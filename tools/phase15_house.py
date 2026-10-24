#!/usr/bin/env python3
"""Safe full-song repair from Phase13; no rejected Phase14 voices or notes."""
import argparse,json,os,shutil,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.production_host import ProductionAdapter
from kuang.sampled_instrument import SampledInstrumentAdapter
from kuang.musical_repair import repaired_house
from kuang.schema import load,save,state_hash,ValidationError
from kuang.sample_assets import inventory,digest,write
from kuang.midi import export_bytes
from kuang.mastering import match_lufs
from kuang.loudness import measure
from kuang.spatial_audio import spatial_metrics
from kuang.audio import compare_wavs
from kuang.harmonic_audit import context
from kuang.ensemble_production import VOICES
END=64*4*60/126+5
SOURCE='fe30aebffc6118ccebf4bdfb0884beb0bc2972e3b5f4a175bfd8d8dd4f9e4ca9'


def adapter(executable,plugin=None):return ProductionAdapter(executable,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase15/tmp')


def build(destination,executable,meter=None):
    dest=Path(destination).resolve()
    if dest.exists() or not dest.is_relative_to(ROOT/'.local/phase15'):raise ValidationError('new project-local Phase15 staging required')
    source=ROOT/'artifacts/phase13-house/B';old=load(source/'project.kuang.json')
    if state_hash(old)!=SOURCE:raise ValidationError('exact Phase13 incumbent required')
    p,plan=repaired_house(old);a=adapter(executable);before=inventory(source)
    assets={t.id:source/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
    legacy=SampledInstrumentAdapter(executable,workspace=ROOT);legacy.scratch=a.scratch
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent,prefix='.build-') as d:
        r=Path(d)/'publish';r.mkdir()
        for label,q in [('A',old),('B',p)]:
            (r/label).mkdir();save(q,r/label/'project.kuang.json');(r/label/'song.mid').write_bytes(export_bytes(q));write(r/label/'source-song-spec.json',json.loads(old.metadata['song_spec']))
        legacy.save(source/'native',r/'A/native');legacy.render(r/'A/native',r/'A-Phase13-incumbent-native.wav',end_seconds=END)
        if digest(r/'A-Phase13-incumbent-native.wav')!=digest(source.parent/'B-phase13-drum-palette-native.wav'):raise ValidationError('incumbent PCM drift')
        a.export(p,assets,{},r/'B/native');a.render(r/'B/native',r/'B-Phase15-repaired-native.wav',end_seconds=END)
        a.save(r/'B/native',Path(d)/'reopened');a.render(Path(d)/'reopened',Path(d)/'repeat.wav',end_seconds=END)
        if digest(Path(d)/'repeat.wav')!=digest(r/'B-Phase15-repaired-native.wav'):raise ValidationError('repair reopened PCM drift')
        levels={k:measure(r/name,library=meter) for k,name in [('A','A-Phase13-incumbent-native.wav'),('B','B-Phase15-repaired-native.wav')]}
        if any(x['clipped_samples'] or x['true_peak_dbtp']>-1 for x in levels.values()):raise ValidationError('repair headroom failure')
        (r/'listening').mkdir();target=min(x['integrated_lufs'] for x in levels.values())
        matching={k:match_lufs(r/raw,r/'listening'/name,target,library=meter) for k,raw,name in [
            ('A','A-Phase13-incumbent-native.wav','A-Phase13-incumbent-full-LUFS-matched.wav'),('B','B-Phase15-repaired-native.wav','B-Phase15-repaired-full-LUFS-matched.wav')]}
        controls=r/'internal-controls';controls.mkdir();bypass=__import__('copy').deepcopy(p)
        for t in bypass.tracks:
            if t.kind=='bus':t.controls['mixer.mute']=1 if t.id=='phase15-shared-room' else 0
            if t.id=='phase15-drum-sum':t.effects[0].parameters['effect.bypass']=1
        a.export(bypass,assets,{},controls/'bypass-native');a.render(controls/'bypass-native',controls/'bypass.wav',end_seconds=END)
        delta=compare_wavs(controls/'bypass.wav',r/'B-Phase15-repaired-native.wav')
        if delta['difference_to_original_rms_ratio']<.002:raise ValidationError('shared processing is inert')
        report={'version':'phase15-repair-1','source_hash':SOURCE,'candidate_hash':state_hash(p),'notes':1536,'source_notes_MIDI_exact':export_bytes(old)==export_bytes(p),
            'full_native_and_PCM_reopen_exact':True,'A_PCM_exact':True,'levels':levels,'matching':matching,'actual_routing_on_off':delta,
            'spatial':{k:spatial_metrics(r/raw) for k,raw in [('A','A-Phase13-incumbent-native.wav'),('B','B-Phase15-repaired-native.wav')]},
            'harmony':{'A':context(old),'B':context(p)},'human_preference':'unreviewed','phase14_B_human_rejected':True,'incumbent':'Phase13 B','professional_quality_claimed':False}
        # Bus strips carry no MIDI track, so exported MIDI must remain identical.
        if not report['source_notes_MIDI_exact'] or report['harmony']['A']!=report['harmony']['B']:raise ValidationError('repair changed harmony or MIDI')
        write(r/'production.json',plan);write(r/'verification.json',report)
        write(r/'recipe.json',{'version':'phase15-replay-1','source_hash':SOURCE,'candidate_hash':state_hash(p),'raw_B_sha256':digest(r/'B-Phase15-repaired-native.wav'),'end_seconds':END})
        shutil.copytree(source.parent/'licenses',r/'licenses');shutil.copyfile(ROOT/'LICENSE',r/'licenses/Kuang-MIT.txt')
        if inventory(source)!=before:raise ValidationError('incumbent source changed')
        shutil.move(str(r),dest)
    return report


def package(root):
    root=Path(root);out=root/'phase15-house-listening.zip'
    if out.exists():raise ValidationError('new repair ZIP required')
    files=[p for folder in ('A','B','listening','licenses','reproduction') for p in (root/folder).rglob('*') if p.is_file()]
    files += [root/n for n in ('README.md','recipe.json','reproduce.py','production.json','verification.json','pitch-verification.json')]
    manifest={str(p.relative_to(root)):digest(p) for p in files}
    if any(p.is_symlink() for p in files):raise ValidationError('ZIP symlinks unsupported')
    with tempfile.TemporaryDirectory(dir=root) as d:
        zpath=Path(d)/'listening.zip'
        with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(files):z.write(p,str(p.relative_to(root)))
            z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
        with zipfile.ZipFile(zpath) as z:
            if z.testzip():raise ValidationError('ZIP CRC failure')
        os.link(zpath,out)
    return {'bytes':out.stat().st_size,'sha256':digest(out)}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','package'));ap.add_argument('--out-dir',required=True);ap.add_argument('--soundcraft');ap.add_argument('--meter-library');a=ap.parse_args()
    print(json.dumps(build(a.out_dir,a.soundcraft,a.meter_library) if a.action=='build' else package(a.out_dir),indent=2))
