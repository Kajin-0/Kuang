#!/usr/bin/env python3
"""Full-song CC0 drum-palette experiment; never an automatic preference claim."""
import argparse
import json
import math
import os
import shutil
import sys
import tempfile
import wave
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kuang.audio import analyze_wav, compare_wavs
from kuang.drum_palette import note_inventory
from kuang.groove_audio import low_end_interaction, stem_sum_error
from kuang.lowend_audio import band_metrics
from kuang.loudness import measure
from kuang.mastering import match_lufs
from kuang.midi import export_bytes
from kuang.octalsamples import COMMIT, catalog, inspect_pack, import_sound
from kuang.producer import _subset
from kuang.production_audio import _decode
from kuang.record_palette import KITS, PITCHES, PLAN, sampled_house, split_house
from kuang.sample_assets import digest, inventory, write
from kuang.sampled_instrument import SampledInstrumentAdapter
from kuang.schema import ValidationError, dumps, load, save, state_hash
from kuang.spatial_audio import spatial_metrics


def adapter(executable):
    a = SampledInstrumentAdapter(executable, workspace=ROOT)
    a.scratch = ROOT/'.local/phase13/tmp'
    a.scratch.mkdir(parents=True, exist_ok=True)
    return a


def new_path(path, parent):
    p = Path(path).absolute()
    if p.is_symlink() or not p.resolve().is_relative_to(parent.resolve()) or p.exists():
        raise ValidationError('new project-local Phase13 destination required')
    return p.resolve()


def prepare_library(pack,destination,converter_library):
    """Explicit offline source import; no download/npm or automatic discovery."""
    from kuang.sample_conversion import SincConverter
    dest=new_path(destination,ROOT/'.local/phase13');pack=Path(pack).resolve()
    if not pack.is_relative_to(ROOT) or dest.is_relative_to(pack):raise ValidationError('source/output must be separate within Kuang')
    inspect_pack(pack);converter=SincConverter(converter_library)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent,prefix='.library-') as d:
        stage=Path(d)/'publish';stage.mkdir();records={}
        for sounds in KITS.values():
            for tid,key in sounds.items():
                label=key+'-p'+str(PITCHES[tid])
                if label not in records:
                    mode='gate' if tid in ('track-hats.p46','track-snare.p38') else 'one_shot'
                    records[label]=import_sound(pack,key,PITCHES[tid],stage/label,converter,playback=mode,conversion_gain_db=-12)
                    records[label]['asset']=label
        write(stage/'conversions.json',records);dest.mkdir()
        try:
            for p in stage.iterdir():shutil.move(str(p),dest/p.name)
        except BaseException:shutil.rmtree(dest);raise
    return {'library':str(dest),'assets':len(records),'commit':COMMIT}


def window_rms(path, first=32*4*60/126, last=40*4*60/126):
    with wave.open(str(path), 'rb') as w:
        a, b = round(first*w.getframerate()), round(last*w.getframerate())
        if not 0 <= a < b <= w.getnframes():raise ValidationError('invalid diagnostic window')
        w.setpos(a);v=list(_decode(w.readframes(b-a),w.getsampwidth(),2))
        power=sum(l*l+r*r for l,r in v)/(2*len(v))
        return 10*math.log10(power) if power else None


def build(destination, source, library, selection, pack, executable, meter=None):
    dest = new_path(destination, ROOT/'.local/phase13')
    source, library, pack = (Path(p).resolve() for p in (source,library,pack))
    if not all(p.is_relative_to(ROOT) for p in (source,library,pack)):
        raise ValidationError('all source/asset paths must stay within Kuang')
    if any(dest.is_relative_to(p) or p.is_relative_to(dest) for p in (source,library,pack)):
        raise ValidationError('publication must be separate from every source/library')
    audit = inspect_pack(pack)
    p=load(source/'project.kuang.json')
    if state_hash(p) != 'dad1db280f798fdf07ab4b0243bcc6e528f680b30f32b8a5e92104a94ce640b1':
        raise ValidationError('exact full Phase10 D incumbent required')
    before = inventory(source)
    chosen=selection['chosen_kit'];sounds=KITS[chosen]
    assets={tid:library/(key+'-p'+str(PITCHES[tid])) for tid,key in sounds.items()}
    q, production=sampled_house(p,assets,selection['levels'])
    a=adapter(executable);base=a.base;end=64*4*60/126+5
    if dumps(base.import_project(source/'native'))!=dumps(p):raise ValidationError('source canonical/native drift')
    with tempfile.TemporaryDirectory(dir=a.scratch,prefix='release-') as d:
        work=Path(d);stage=work/'publish';stage.mkdir();(stage/'A').mkdir();(stage/'B').mkdir()
        base.save(source/'native',stage/'A/native');save(p,stage/'A/project.kuang.json');(stage/'A/song.mid').write_bytes(export_bytes(p))
        shutil.copyfile(source/'source-song-spec.json',stage/'A/source-song-spec.json')
        base.render(stage/'A/native',stage/'A-phase10-original-native.wav',end_seconds=end)
        if digest(stage/'A-phase10-original-native.wav')!=digest(source/'D-phase10-combined-native.wav'):
            raise ValidationError('full Phase10 A PCM identity failed')
        a.export(q,assets,stage/'B/native');save(q,stage/'B/project.kuang.json');(stage/'B/song.mid').write_bytes(export_bytes(q))
        shutil.copyfile(source/'source-song-spec.json',stage/'B/source-song-spec.json')
        a.save(stage/'B/native',work/'reopened')
        if a.inspect(stage/'B/native')['native']!=a.inspect(work/'reopened')['native']:
            raise ValidationError('full native state did not reopen')
        a.render(stage/'B/native',stage/'B-phase13-drum-palette-native.wav',end_seconds=end)
        a.render(work/'reopened',work/'repeated-B.wav',end_seconds=end)
        if digest(work/'repeated-B.wav')!=digest(stage/'B-phase13-drum-palette-native.wav'):
            raise ValidationError('full native reopened PCM differs')
        print('Full native A/B and reopen PCM verified',flush=True)
        stems=stage/'internal-controls';stems.mkdir();music_ids=[t.id for t in p.tracks if t.id not in PLAN]
        base.export(_subset(p,music_ids),stems/'unchanged-music-native')
        base.render(stems/'unchanged-music-native',stems/'unchanged-music.wav',end_seconds=end)
        groups={};sums={}
        for label,project,backend in [('A',p,base),('B',q,a)]:
            group_paths=[]
            for group,ids in [('kick',['track-kick']),('other-drums',[t.id for t in project.tracks if t.id in PITCHES and t.id!='track-kick'])]:
                folder=stems/(label+'-'+group+'-native');part=_subset(project,ids)
                if label=='A':backend.export(part,folder)
                else:backend.export(part,{tid:assets[tid] for tid in ids},folder)
                out=stems/(label+'-'+group+'.wav');backend.render(folder,out,end_seconds=end);group_paths.append(out)
            raw=stage/('A-phase10-original-native.wav' if label=='A' else 'B-phase13-drum-palette-native.wav')
            sums[label]=stem_sum_error(raw,[*group_paths,stems/'unchanged-music.wav'])
            if sums[label]['peak_error_lsb']>2:raise ValidationError('independent three-stem reconstruction exceeds 2 LSB')
        bass=_subset(p,['track-bass']);base.export(bass,stems/'bass-native');base.render(stems/'bass-native',stems/'bass.wav',end_seconds=end)
        levels={label:measure(stage/name,library=meter) for label,name in [('A','A-phase10-original-native.wav'),('B','B-phase13-drum-palette-native.wav')]}
        if any(x['clipped_samples'] or x['true_peak_dbtp']> -1 or x['rms']<1e-6 for x in levels.values()):
            raise ValidationError('full song clipping/headroom/silence failure')
        listening=stage/'listening';listening.mkdir();target=min(x['integrated_lufs'] for x in levels.values())
        matching={label:match_lufs(stage/raw,listening/name,target,library=meter) for label,raw,name in [
            ('A','A-phase10-original-native.wav','A-Phase10-original-full-LUFS-matched.wav'),
            ('B','B-phase13-drum-palette-native.wav','B-Phase13-sampled-drums-full-LUFS-matched.wav')]}
        # Internal stems remain diagnostics. The user receives a complete record A/B.
        bands={label:band_metrics(stage/name,first=32*4*60/126,last=40*4*60/126,windows=16) for label,name in [('A','A-phase10-original-native.wav'),('B','B-phase13-drum-palette-native.wav')]}
        kick_bass={label:low_end_interaction(stems/(label+'-kick.wav'),stems/'bass.wav') for label in ('A','B')}
        spatial={label:spatial_metrics(stage/name) for label,name in [('A','A-phase10-original-native.wav'),('B','B-phase13-drum-palette-native.wav')]}
        difference=compare_wavs(listening/'A-Phase10-original-full-LUFS-matched.wav',listening/'B-Phase13-sampled-drums-full-LUFS-matched.wav')
        if not difference['measurable_change'] or difference['difference_to_original_rms_ratio']<.1:
            raise ValidationError('full-context source experiment has no substantial waveform change')
        licenses=stage/'licenses';licenses.mkdir();(licenses/'original-audio').mkdir()
        for name in ('LICENSE','LICENSES.md','manifest.json'):
            shutil.copyfile(pack/name,licenses/('octal-'+name))
        shutil.copyfile(ROOT/'LICENSE',licenses/'Kuang-MIT.txt')
        original_sources={}
        for tid,key in sounds.items():
            s=catalog()['samples'][key];original=pack/s['path'];out=licenses/'original-audio'/(key+'.wav');shutil.copyfile(original,out)
            original_sources[tid]={'key':key,'path':str(out.relative_to(stage)),'sha256':digest(out),'source_commit':COMMIT,'source_original':s}
        write(stage/'selection.json',selection);write(stage/'production.json',production)
        recipe={'version':'phase13-palette-1','source_hash':state_hash(p),'candidate_hash':state_hash(q),
            'source': 'A/project.kuang.json','levels':selection['levels'],
            'assets':{tid:'B/native/assets/'+tid for tid in PITCHES},'original_sources':original_sources,
            'native_pcm_sha256':digest(stage/'B-phase13-drum-palette-native.wav'),
            'render_end_seconds':end,'hidden_postprocessing':False,'mastering':'none; listening copies use constant attenuation only'}
        write(stage/'recipe.json',recipe)
        shutil.copyfile(ROOT/'tools/phase13_reproduce.py',stage/'reproduce.py')
        reproduction=stage/'reproduction';(reproduction/'kuang').mkdir(parents=True)
        for path in (ROOT/'kuang').rglob('*'):
            if path.is_file() and path.suffix in ('.py','.lua','.json'):
                if path.is_symlink():raise ValidationError('reproduction source symlinks unsupported')
                target=reproduction/'kuang'/path.relative_to(ROOT/'kuang');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        shutil.copyfile(ROOT/'LICENSE',reproduction/'LICENSE')
        write(reproduction/'source-manifest.json',inventory(reproduction))
        report={'source_hash':state_hash(p),'candidate_hash':state_hash(q),'bars':64,'tempo_bpm':126,'key':'C minor',
            'source_notes':1536,'all_original_note_fields_exact':note_inventory(p)==note_inventory(q),
            'source_song_spec_exact':p.metadata['song_spec']==q.metadata['song_spec'],'six_sections_exact':p.sections==q.sections,
            'non_drum_tracks_exact':True,'source_audit':audit,'live_sample_instruments':6,
            'full_native_save_reopen_exact':True,'repeated_full_PCM_exact':True,'baseline_A_PCM_exact':True,
            'independent_reconstruction':sums,'levels':levels,'matching':matching,'drop_bands':bands,
            'kick_bass':kick_bass,'spatial':spatial,'matched_full_context_difference':difference,
            'human_preference':'unreviewed','professional_quality_established':False,'incumbent_retained':'Phase10 D',
            'routing':'original inserts/master outputs; no general send/bus or parallel compressor claim',
            'source_unchanged':inventory(source)==before,'source_drum_edits':production}
        if not report['source_unchanged']:raise ValidationError('historical source drift')
        write(stage/'verification.json',report)
        text=(ROOT/'docs/PHASE13_LISTENING_README.md').read_text()
        (stage/'README.md').write_text(text)
        write(stage/'artifact-sha256.json',inventory(stage))
        dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
        try:
            for f in stage.iterdir():shutil.move(str(f),dest/f.name)
        except BaseException:shutil.rmtree(dest);raise
    package(dest)
    return report


def package(root):
    root=Path(root);out=root/'phase13-house-listening.zip'
    if out.exists():raise ValidationError('new listening ZIP required')
    # Explicitly authorized UNREVIEWED comparison, not a forged preferred review
    # or a replacement for producer.package_preferred's promotion gate.
    selected=[]
    for folder in ('A','B','listening','licenses','reproduction'):
        selected.extend(p for p in (root/folder).rglob('*') if p.is_file())
    selected.extend(root/name for name in ('README.md','recipe.json','reproduce.py','production.json','selection.json','verification.json'))
    if any(p.is_symlink() for p in selected):raise ValidationError('ZIP symlinks unsupported')
    expected={str(p.relative_to(root)):digest(p) for p in selected}
    with tempfile.TemporaryDirectory(dir=root,prefix='.zip-') as d:
        zpath=Path(d)/'listening.zip'
        with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(selected):z.write(p,str(p.relative_to(root)))
            z.writestr('zip-manifest.json',json.dumps(expected,indent=2,sort_keys=True)+'\n')
        with zipfile.ZipFile(zpath) as z:
            if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in expected.items()):
                raise ValidationError('listening ZIP identity/integrity failure')
        os.link(zpath,out)
    return {'zip':str(out),'sha256':digest(out),'bytes':out.stat().st_size,'human_preference':'unreviewed'}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out-dir',required=True);ap.add_argument('--symbolic',action='store_true')
    ap.add_argument('--prepare-library',action='store_true');ap.add_argument('--converter-library')
    ap.add_argument('--source',default=str(ROOT/'artifacts/phase10-house'))
    ap.add_argument('--library');ap.add_argument('--selection');ap.add_argument('--pack');ap.add_argument('--soundcraft');ap.add_argument('--meter-library')
    args=ap.parse_args()
    if args.prepare_library:
        if args.symbolic or not args.pack or not args.converter_library:ap.error('library preparation requires --pack and explicit --converter-library')
        print(json.dumps(prepare_library(args.pack,args.out_dir,args.converter_library),indent=2))
    elif args.symbolic:
        dest=new_path(args.out_dir,ROOT/'.local/phase13');dest.mkdir(parents=True)
        from kuang.atmosphere import atmosphere_house
        p,r=split_house(atmosphere_house());save(p,dest/'project.kuang.json');(dest/'song.mid').write_bytes(export_bytes(p));write(dest/'split.json',r)
    else:
        if not all((args.library,args.selection,args.pack,args.soundcraft)):ap.error('render requires --library, --selection, --pack and --soundcraft')
        build(args.out_dir,args.source,args.library,json.loads(Path(args.selection).read_text()),args.pack,args.soundcraft,args.meter_library)
