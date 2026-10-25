#!/usr/bin/env python3
"""Full-song mix polish from the exact human-approved Phase16 B."""
import argparse,json,os,shutil,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.mix_polish import polished_mix,SOURCE_HASH
from kuang.production_host import ProductionAdapter
from kuang.schema import load,save,state_hash,ValidationError
from kuang.midi import export_bytes
from kuang.sample_assets import digest,inventory,write
from kuang.loudness import measure
from kuang.mastering import match_lufs
from kuang.spatial_audio import spatial_metrics
from kuang.production_audio import production_metrics
from kuang.lowend_audio import band_metrics
from kuang.audio import compare_wavs

END=64*4*60/126+5
AUDIO={'A':'A-Phase16-approved-native.wav','B':'B-Phase17-mix-native.wav'}

def adapter(host,plugin):
    return ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase17/tmp',center_pitch_bend=True)

def assets_and_patches(root,p):
    root=Path(root)
    return ({t.id:root/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'},
            {t.id:root/'native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')})

def build(destination,host,plugin,meter=None):
    dest=Path(destination).resolve()
    if dest.exists() or dest.is_symlink() or not dest.is_relative_to(ROOT/'.local/phase17'):
        raise ValidationError('new project-local Phase17 staging required')
    source=ROOT/'artifacts/phase16-house/B';before=inventory(source);old=load(source/'project.kuang.json')
    p,plan=polished_mix(old);assets,patches=assets_and_patches(source,p);a=adapter(host,plugin)
    dest.mkdir(parents=True)
    try:
        for label,q in [('A',old),('B',p)]:
            (dest/label).mkdir();save(q,dest/label/'project.kuang.json')
            (dest/label/'song.mid').write_bytes(export_bytes(q));write(dest/label/'source-song-spec.json',json.loads(old.metadata['song_spec']))
        a.save(source/'native',dest/'A/native');a.render(dest/'A/native',dest/AUDIO['A'],end_seconds=END)
        if digest(dest/AUDIO['A'])!=digest(source.parent/'B-Phase16-palette-native.wav'):
            raise ValidationError('approved Phase16 PCM drift')
        # Fresh export; the first prototype is retained separately for comparison.
        a.export(p,assets,patches,dest/'B/native');a.render(dest/'B/native',dest/AUDIO['B'],end_seconds=END)
        prototype=ROOT/'.local/phase17/prototype/B-phase17-prototype-native.wav'
        # The initial prototype precedes measured role calibration and rejection
        # of an inert extra bass-duck experiment; it remains preserved separately.
        with tempfile.TemporaryDirectory(dir=a.scratch) as d:
            d=Path(d);a.save(dest/'B/native',d/'reopened');a.render(d/'reopened',d/'repeat.wav',end_seconds=END)
            if digest(d/'repeat.wav')!=digest(dest/AUDIO['B']) or a.inspect(d/'reopened')['native']!=a.inspect(dest/'B/native')['native']:
                raise ValidationError('full native/PCM reopen differs')
        for tid,path in patches.items():
            if inventory(path)!=inventory(dest/'B/native/patches'/tid):raise ValidationError('approved patch bytes altered')
        levels={k:measure(dest/v,library=meter) for k,v in AUDIO.items()}
        if any(x['clipped_samples'] or x['true_peak_dbtp']>-1 for x in levels.values()):raise ValidationError('mix headroom failure')
        (dest/'listening').mkdir();target=min(x['integrated_lufs'] for x in levels.values())
        matches={k:match_lufs(dest/v,dest/'listening'/(k+'-'+('Phase16-approved' if k=='A' else 'Phase17-mix')+'-full-LUFS-matched.wav'),target,library=meter) for k,v in AUDIO.items()}
        regions=[(s.name,s.start/p.ppq*60/p.tempo_bpm,(s.start+s.length)/p.ppq*60/p.tempo_bpm) for s in p.sections]
        spatial={k:spatial_metrics(dest/v) for k,v in AUDIO.items()}
        if spatial['B']['bands']['low_20_120']['mono_energy_retention']<.9999 or spatial['B']['mono_sum']['rms_loss_db']<-.25:
            raise ValidationError('mono compatibility gate failed')
        write(dest/'production.json',plan)
        report={'version':'phase17-verification-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),
            'incumbent':'Phase16 B: human approved','candidate_preference':'unreviewed','professional_quality_claimed':False,
            'performance':{'bars':64,'bpm':126,'key':'C minor','sections':6,'note_records':1536,'MIDI_bytes_exact':export_bytes(old)==export_bytes(p),'instruments_and_patches_exact':True},
            'A_PCM_exact':True,'native_state_and_PCM_reopen_exact':True,'levels':levels,'matching':matches,'spatial':spatial,
            'sections':{k:production_metrics(dest/v,regions)['sections'] for k,v in AUDIO.items()},
            'section_bands':{k:{name:band_metrics(dest/v,first=lo,last=hi,windows=4) for name,lo,hi in regions} for k,v in AUDIO.items()},
            'full_difference':compare_wavs(dest/AUDIO['A'],dest/AUDIO['B']),
            'sidechain':'scheduled MIDI-kick attenuation; no audio-triggered routing claim','mastering':'none; raw native and constant attenuation listening copies only'}
        write(dest/'verification.json',report)
        write(dest/'recipe.json',{'version':'phase17-replay-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),
            'raw_A_sha256':digest(dest/AUDIO['A']),'raw_B_sha256':digest(dest/AUDIO['B']),'end_seconds':END,
            'patch_manifest_sha256':{t:digest(v/'manifest.json') for t,v in patches.items()}})
        shutil.copytree(source.parent/'licenses',dest/'licenses')
        if inventory(source)!=before:raise ValidationError('incumbent source changed')
    except BaseException:shutil.rmtree(dest);raise
    return report

def prepare_download(root):
    root=Path(root)
    if any((root/n).exists() for n in ('README.md','reproduce.py','reproduction')):raise ValidationError('fresh download inputs required')
    shutil.copyfile(ROOT/'docs/PHASE17_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase17_reproduce.py',root/'reproduce.py')
    frozen=root/'reproduction';(frozen/'kuang').mkdir(parents=True)
    for p in (ROOT/'kuang').rglob('*'):
        if p.is_file() and p.suffix in ('.py','.lua','.json'):
            if p.is_symlink():raise ValidationError('frozen source symlink')
            out=frozen/'kuang'/p.relative_to(ROOT/'kuang');out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
    shutil.copyfile(ROOT/'LICENSE',frozen/'LICENSE');write(frozen/'source-manifest.json',inventory(frozen))

def package(root):
    root=Path(root);target=root/'phase17-house-listening.zip'
    if target.exists() or target.is_symlink():raise ValidationError('new listening ZIP required')
    files=[p for name in ('A','B','listening','licenses','reproduction') for p in (root/name).rglob('*') if p.is_file()]
    files += [root/n for n in ('README.md','reproduce.py','recipe.json','production.json','verification.json','controls.json','pitch-verification.json')]
    if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files):raise ValidationError('unsupported bundled media/binary')
    manifest={str(p.relative_to(root)):digest(p) for p in files}
    with tempfile.TemporaryDirectory(dir=root) as d:
        zpath=Path(d)/'pack.zip'
        with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(files):z.write(p,str(p.relative_to(root)))
            z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
        with zipfile.ZipFile(zpath) as z:
            if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP integrity failure')
        if zpath.stat().st_size>180_000_000:raise ValidationError('listening ZIP size limit')
        os.link(zpath,target)
    return {'bytes':target.stat().st_size,'sha256':digest(target)}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','package'));ap.add_argument('--out-dir',required=True)
    ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--meter-library');z=ap.parse_args()
    if z.action=='build' and not (z.soundcraft and z.plugin):ap.error('explicit reviewed host and plugin required')
    print(json.dumps(build(z.out_dir,z.soundcraft,z.plugin,z.meter_library) if z.action=='build' else package(z.out_dir),indent=2))
