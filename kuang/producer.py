"""Full-project instrument auditions and an explicit human preference ledger.

This is execution/evidence infrastructure, not an autonomous musical judge or
an AI service. Technical eligibility never promotes a candidate by itself.
"""
import argparse
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from .audio import compare_wavs
from .depth import note_fingerprints
from .groove_audio import stem_sum_error
from .loudness import measure
from .mastering import match_lufs
from .midi import export_bytes
from .sample_assets import digest, inventory, write
from .sampled_instrument import SampledInstrumentAdapter
from .schema import ValidationError, dumps, load, save, state_hash, strict_json


def _subset(p,track_ids):
    q=deepcopy(p);q.tracks=[t for t in q.tracks if t.id in track_ids]
    owners={o for t in q.tracks for o in [t.id,t.instrument.id,*(e.id for e in t.effects)]}
    q.automation=[a for a in q.automation if a.target_id in owners]
    q.locks=[x for x in q.locks if x.target_id in owners or any(x.target_id==c.id for t in q.tracks for c in t.clips)]
    return q


def audition(source, assignments, destination, hypothesis, *, executable=None, library=None, workspace=None):
    if type(hypothesis) is not str or not hypothesis.strip() or len(hypothesis)>4096:
        raise ValidationError('explicit, bounded listening hypothesis required')
    a=SampledInstrumentAdapter(executable,workspace=workspace);base=a.base
    source=a.local(source);dest=a._new(destination,source)
    assets={k:a.local(v) for k,v in assignments.items()}
    if not assets or any(dest.is_relative_to(v) for v in assets.values()):raise ValidationError('output inside audition assets')
    p=load(source/'project.kuang.json')
    if dumps(base.import_project(source/'native'))!=dumps(p):raise ValidationError('baseline canonical/native drift')
    before=inventory(source);asset_before={k:inventory(v) for k,v in assets.items()}
    # The full project, including sparse sections and tails, is the context.
    # This command does not substitute an eight-bar crop as its benchmark.
    end=p.length/p.ppq*60/p.tempo_bpm+5
    with tempfile.TemporaryDirectory(dir=a.scratch,prefix='audition-') as d:
        work=Path(d);stage=work/'publish';stage.mkdir();(stage/'A').mkdir();(stage/'B').mkdir()
        base.save(source/'native',stage/'A/native');save(p,stage/'A/project.kuang.json')
        (stage/'A/song.mid').write_bytes(export_bytes(p))
        base.render(stage/'A/native',stage/'A/raw.wav',end_seconds=end)
        a.export(p,assets,stage/'B/native');q=a.import_project(stage/'B/native')
        save(q,stage/'B/project.kuang.json');(stage/'B/song.mid').write_bytes(export_bytes(q))
        if note_fingerprints(q)!=note_fingerprints(p) or export_bytes(q)!=export_bytes(p) or q.sections!=p.sections:
            raise ValidationError('instrument audition changed musical content')
        for t,u in zip(p.tracks,q.tracks):
            if (t.clips,t.effects,t.controls,t.sends,t.output_master)!=(u.clips,u.effects,u.controls,u.sends,u.output_master):
                raise ValidationError('instrument audition changed mix/routing/notes')
        if q.metadata.get('song_spec')!=p.metadata.get('song_spec') or p.automation!=q.automation:
            raise ValidationError('audition lost source SongSpec/automation')
        a.save(stage/'B/native',stage/'B/reopened-native')
        a.render(stage/'B/native',stage/'B/raw.wav',end_seconds=end)
        a.render(stage/'B/reopened-native',work/'repeated.wav',end_seconds=end)
        if digest(work/'repeated.wav')!=digest(stage/'B/raw.wav'):raise ValidationError('audition PCM does not persist')
        active=[t.id for t in p.tracks if t.id in assets]
        solos=stage/'solos';solos.mkdir()
        old_solo=_subset(p,active);new_solo=_subset(q,active)
        base.export(old_solo,solos/'A-native');base.render(solos/'A-native',solos/'A.wav',end_seconds=end)
        a.export(new_solo,assets,solos/'B-native');a.render(solos/'B-native',solos/'B.wav',end_seconds=end)
        # Same unchanged context independently rendered, so a source swap cannot
        # silently change other instruments under cover of full-mix metrics.
        remainder=_subset(p,[t.id for t in p.tracks if t.id not in assets])
        sums={}
        if remainder.tracks:
            base.export(remainder,solos/'context-native');base.render(solos/'context-native',solos/'context.wav',end_seconds=end)
            sums={k:stem_sum_error(stage/k/'raw.wav',[solos/(k+'.wav'),solos/'context.wav']) for k in ('A','B')}
            if any(v['peak_error_lsb']>12 for v in sums.values()):raise ValidationError('source/context reconstruction differs')
        levels={k:measure(stage/k/'raw.wav',library=library) for k in ('A','B')}
        if any(m['clipped_samples'] or m['true_peak_dbtp']> -1 or m['rms']<1e-6 for m in levels.values()):
            raise ValidationError('audition has inadequate headroom, clipping or silence')
        listen=stage/'listening';listen.mkdir();matching={}
        for view,paths in [('full',{k:stage/k/'raw.wav' for k in ('A','B')}),('instrument',{k:solos/(k+'.wav') for k in ('A','B')})]:
            meters={k:measure(v,library=library) for k,v in paths.items()}
            target=min(v['integrated_lufs'] for v in meters.values())
            matching[view]={k:match_lufs(v,listen/(k+'-'+view+'-LUFS-matched.wav'),target,library=library) for k,v in paths.items()}
        delta=compare_wavs(stage/'A/raw.wav',stage/'B/raw.wav')
        if not delta['measurable_change']:raise ValidationError('sample choice has no actual full-context effect')
        if inventory(source)!=before or any(inventory(v)!=asset_before[k] for k,v in assets.items()):
            raise ValidationError('audition source/library drift')
        evidence={'version':'producer-audition-1','hypothesis':hypothesis,'baseline_hash':state_hash(p),
            'candidate_hash':state_hash(q),'bars':p.bars,'note_fields_exact':True,'midi_bytes_exact':True,
            'song_spec_exact':True,'automation_exact':True,'full_native_reopen_PCM_exact':True,
            'technical_eligible':True,'preference':'unreviewed','quality_improvement_established':False,
            'levels':levels,'matching':matching,'full_context_difference':delta,'independent_context_sum':sums,
            'listening_files':{str(v.relative_to(stage)):digest(v) for v in sorted(listen.glob('*.wav'))},
            'assets':{k:digest(v/'asset.json') for k,v in assets.items()},
            'files':inventory(stage)}
        write(stage/'audition.json',evidence)
        dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
        try:
            for f in stage.iterdir():shutil.move(str(f),dest/f.name)
        except BaseException:shutil.rmtree(dest);raise
    return evidence


def read_audition(root):
    root=Path(root);p=root/'audition.json'
    if p.is_symlink() or not p.is_file() or p.stat().st_size>2**20:raise ValidationError('invalid audition evidence')
    m=strict_json(p.read_text())
    keys={'version','hypothesis','baseline_hash','candidate_hash','bars','note_fields_exact','midi_bytes_exact',
        'song_spec_exact','automation_exact','full_native_reopen_PCM_exact','technical_eligible','preference',
        'quality_improvement_established','levels','matching','full_context_difference','independent_context_sum',
        'listening_files','assets','files'}
    if type(m) is not dict or set(m)!=keys or m['version']!='producer-audition-1' or m['preference']!='unreviewed' or m['quality_improvement_established'] is not False:
        raise ValidationError('unsupported producer audition evidence')
    actual=inventory(root)
    actual={k:v for k,v in actual.items() if not k.startswith('reviews/') and k not in ('audition.json','.review-lock')}
    if actual!=m['files']:raise ValidationError('audition data drift')
    expected={'listening/'+k+'-'+role+'-LUFS-matched.wav' for k in ('A','B') for role in ('full','instrument')}
    if set(m['listening_files'])!=expected or any(actual.get(k)!=v for k,v in m['listening_files'].items()):
        raise ValidationError('wrong audition/listening file identities')
    if (state_hash(load(root/'A/project.kuang.json'))!=m['baseline_hash'] or
        state_hash(load(root/'B/project.kuang.json'))!=m['candidate_hash']):raise ValidationError('audition project identity mismatch')
    return m


def record_review(root, *, audition_sha256, reviewer, decision, reason, listened_files):
    root=Path(root);m=read_audition(root)
    if digest(root/'audition.json')!=audition_sha256:raise ValidationError('stale human review audition identity')
    if type(reviewer) is not str or not reviewer.strip() or len(reviewer)>256 or type(reason) is not str or not reason.strip() or len(reason)>4096:
        raise ValidationError('named reviewer and listening reasons required')
    if decision not in ('preferred','rejected','no_preference') or listened_files!=m['listening_files']:
        raise ValidationError('review must explicitly identify all solo/full-context listening files')
    if m['technical_eligible'] is not True:raise ValidationError('technically ineligible candidate cannot be reviewed for promotion')
    lock=root/'.review-lock'
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as e:raise ValidationError('another producer review writer is active') from e
    try:
        os.close(fd);reviews=root/'reviews';reviews.mkdir(exist_ok=True)
        chain=review_history(root);previous=digest(chain[-1]) if chain else None
        record={'version':'producer-review-1','audition_sha256':audition_sha256,'previous_review_sha256':previous,
            'reviewer':reviewer,'decision':decision,'reason':reason,'listened_files':listened_files,
            'declaration':'Explicit reviewer declaration; software cannot verify that a person listened.'}
        dest=reviews/(f'{len(chain):04d}.json')
        with dest.open('x') as f:json.dump(record,f,indent=2,sort_keys=True);f.write('\n')
    finally:lock.unlink()
    return record


def review_history(root):
    root=Path(root);folder=root/'reviews';paths=sorted(folder.glob('*')) if folder.exists() else []
    previous=None
    for i,path in enumerate(paths):
        if path.name!=f'{i:04d}.json' or path.is_symlink() or path.stat().st_size>16384:raise ValidationError('invalid producer review chain')
        r=strict_json(path.read_text())
        if (type(r) is not dict or set(r)!={'version','audition_sha256','previous_review_sha256','reviewer','decision','reason','listened_files','declaration'} or
            r['version']!='producer-review-1' or r['audition_sha256']!=digest(root/'audition.json') or
            r['previous_review_sha256']!=previous or r['decision'] not in ('preferred','rejected','no_preference') or
            type(r['reviewer']) is not str or not r['reviewer'].strip() or type(r['reason']) is not str or not r['reason'].strip() or
            r['listened_files']!=strict_json((root/'audition.json').read_text())['listening_files']):
            raise ValidationError('producer review receipt drift')
        previous=digest(path)
    return paths


def package_preferred(root, destination):
    root=Path(root);lock=root/'.review-lock'
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as e:raise ValidationError('another producer review/package writer is active') from e
    try:
        os.close(fd)
        return _package_locked(root,destination)
    finally:lock.unlink()


def _package_locked(root, destination):
    root=Path(root);m=read_audition(root);chain=review_history(root)
    if not chain or strict_json(chain[-1].read_text())['decision']!='preferred':
        raise ValidationError('no explicit preferred human review; no production listening ZIP promoted')
    expected={**m['files'],'audition.json':digest(root/'audition.json'),
              **{str(p.relative_to(root)):digest(p) for p in chain}}
    destination=Path(destination)
    if destination.exists() or destination.is_symlink() or destination.resolve().is_relative_to(root.resolve()):
        raise ValidationError('new listening ZIP outside immutable audition required')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent,prefix='.producer-zip-') as d:
        out=Path(d)/'listening.zip'
        with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(root.rglob('*')):
                if p.is_file() and p.name!='.review-lock' and (p.suffix!='.wav' or 'listening' in p.parts):z.write(p,str(p.relative_to(root)))
            # Native Audio Files are WAV too; include the complete editable
            # dependency closure, not just mixes or the original asset manifest.
            present=set(z.namelist())
            for p in sorted(root.rglob('*.wav')):
                name=str(p.relative_to(root))
                if name not in present and ('Audio Files' in p.parts or 'assets' in p.parts):z.write(p,name)
        with zipfile.ZipFile(out) as z:
            if z.testzip():raise ValidationError('producer ZIP failed integrity')
            if any(name not in expected or hashlib.sha256(z.read(name)).hexdigest()!=expected[name] for name in z.namelist()):
                raise ValidationError('producer ZIP input drift during packaging')
        read_audition(root)
        os.link(out,destination)
    return {'zip':str(destination),'sha256':digest(destination),'review_sha256':digest(chain[-1]),
            'human_declared_preference':True,'automated_quality_score':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('audition','review','package'))
    p.add_argument('--source',required=True);p.add_argument('--out');p.add_argument('--workspace');p.add_argument('--soundcraft')
    p.add_argument('--asset',action='append',default=[]);p.add_argument('--hypothesis');p.add_argument('--meter-library')
    p.add_argument('--review-file')
    args=p.parse_args()
    try:
        root=Path(args.workspace or Path.cwd()).resolve()
        def local(x):
            if x is None or Path(x).is_symlink() or not Path(x).resolve().is_relative_to(root):raise ValidationError('producer files must stay within workspace')
            return Path(x).resolve()
        if args.action=='audition':
            pairs=[x.split('=',1) for x in args.asset]
            if any(len(x)!=2 for x in pairs) or len({x[0] for x in pairs})!=len(pairs):raise ValidationError('unique TRACK=ASSET bindings required')
            result=audition(local(args.source),{k:local(v) for k,v in pairs},local(args.out),args.hypothesis,
                executable=args.soundcraft,library=local(args.meter_library) if args.meter_library else None,workspace=root)
        elif args.action=='review':
            request=strict_json(local(args.review_file).read_text())
            if type(request) is not dict or set(request)!={'audition_sha256','reviewer','decision','reason','listened_files'}:
                raise ValidationError('exact human review fields required')
            result=record_review(local(args.source),**request)
        else:result=package_preferred(local(args.source),local(args.out))
        print(json.dumps(result,indent=2,allow_nan=False))
    except (ValidationError,OSError) as e:p.exit(2,str(e)+'\n')


if __name__=='__main__':main()
