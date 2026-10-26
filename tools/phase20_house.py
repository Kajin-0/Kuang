#!/usr/bin/env python3
"""Full-song native mix/master and honest equal-LUFS listening delivery."""
import argparse,json,os,shutil,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,save,state_hash,ValidationError
from kuang.record_mix import mixed_record,SOURCE_HASH
from kuang.production_host import ProductionAdapter
from kuang.master_bus import MasterBusAdapter
from kuang.sample_assets import digest,inventory,write
from kuang.midi import export_bytes
from kuang.loudness import measure
from kuang.mastering import match_lufs
from kuang.production_audio import production_metrics
from kuang.lowend_audio import band_metrics
from kuang.spatial_audio import spatial_metrics
from kuang.mix_diagnostics import shortterm_trace

END=160*4*60/126+5
AUDIO={'A':'A-Phase19-original-native.wav','B':'B-Phase20-record-master-native.wav'}
PRE='B-Phase20-premaster-native.wav'


def adapter(host,plugin,*,master=True):
    cls=MasterBusAdapter if master else ProductionAdapter
    return cls(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase20/tmp',center_pitch_bend=True)


def media(root,p):
    return ({t.id:Path(root)/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'},
        {t.id:Path(root)/'native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')})


def build(dest,host,plugin,meter=None):
    dest=Path(dest).resolve()
    if dest.exists() or dest.is_symlink() or not dest.is_relative_to(ROOT/'.local/phase20'):raise ValidationError('new Phase20 staging inside project required')
    src=ROOT/'artifacts/phase19-house/B';before=inventory(src);source=load(src/'project.kuang.json');p,receipt=mixed_record(source);pre,pre_receipt=mixed_record(source,master=False)
    assets,patches=media(src,p);dest.mkdir()
    try:
        (dest/'source').mkdir();save(source,dest/'source/phase19-reference.kuang.json');(dest/'source/phase19-reference.mid').write_bytes(export_bytes(source))
        for name,q,r in [('premaster',pre,pre_receipt),('B',p,receipt)]:
            folder=dest/name;folder.mkdir();save(q,folder/'project.kuang.json');(folder/'song.mid').write_bytes(export_bytes(q));write(folder/'production.json',r)
            a=adapter(host,plugin,master=name=='B');a.export(q,assets,patches,folder/'native')
            a.render(folder/'native',dest/(AUDIO['B'] if name=='B' else PRE),end_seconds=END)
            print('Rendered',name,flush=True)
        shutil.copyfile(src.parent/'B-Phase19-continuity-native.wav',dest/AUDIO['A']);write(dest/'B/source-song-spec.json',json.loads(source.metadata['song_spec']))
        a=adapter(host,plugin)
        with tempfile.TemporaryDirectory(dir=a.scratch) as d:
            d=Path(d);a.save(dest/'B/native',d/'saved');a.render(d/'saved',d/'repeat.wav',end_seconds=END)
            if a.inspect(dest/'B/native')['native']!=a.inspect(d/'saved')['native'] or digest(d/'repeat.wav')!=digest(dest/AUDIO['B']):raise ValidationError('full master native state/PCM reopen failed')
        for tid,path in {**assets,**patches}.items():
            target=dest/'B/native'/('assets' if tid in assets else 'patches')/tid
            if inventory(path)!=inventory(target):raise ValidationError('immutable source media changed')
        levels={k:measure(dest/name,library=meter) for k,name in {**AUDIO,'premaster':PRE}.items()}
        if any(x['clipped_samples'] or x['rms']<=0 for x in levels.values()) or levels['B']['true_peak_dbtp']> -1:raise ValidationError('full-song PCM/true-peak ceiling failed')
        (dest/'listening').mkdir();target=min(levels[k]['integrated_lufs'] for k in AUDIO)
        matching={k:match_lufs(dest/name,dest/'listening'/(k+'-'+('Phase19-original' if k=='A' else 'Phase20-record-master')+'-FULL-LUFS-matched.wav'),target,library=meter) for k,name in AUDIO.items()}
        regions=[(s.name,s.start/p.ppq*60/126,(s.start+s.length)/p.ppq*60/126) for s in p.sections]
        sections={k:production_metrics(dest/name,regions)['sections'] for k,name in {**AUDIO,'premaster':PRE}.items()}
        bands={k:{label:band_metrics(dest/name,first=lo,last=hi,windows=4) for label,lo,hi in regions} for k,name in {**AUDIO,'premaster':PRE}.items()}
        spatial={k:spatial_metrics(dest/name) for k,name in AUDIO.items()}
        if spatial['B']['bands']['low_20_120']['mono_energy_retention']<.999 or spatial['B']['mono_sum']['rms_loss_db']<-.3:raise ValidationError('mono/low-end compatibility failed')
        shortterm={k:shortterm_trace(dest/name,library=meter) for k,name in {**AUDIO,'premaster':PRE}.items()}
        v={'version':'phase20-full-record-verification-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'premaster_hash':state_hash(pre),
            'MIDI_bytes_exact':export_bytes(p)==export_bytes(source),'note_records':4596,'bars':160,'bpm':126,'key':'C minor','sections':9,
            'instruments_patches_samples_exact':True,'native_terminal_master':True,'native_master_save_reopen_state_PCM_exact':True,
            'limiter':'Native maximizer, measured oversampled output ceiling; not advertised as true-peak-aware DSP',
            'ratio':'Native compressor default4:1 with actual parallel blend; no schema ratio/Q fiction',
            'levels':levels,'matching':matching,'sections':sections,'section_bands':bands,'spatial':spatial,'shortterm':shortterm,
            'source_PCM_exact':digest(dest/AUDIO['A'])==digest(src.parent/'B-Phase19-continuity-native.wav'),
            'mastering':'Fully native editable terminal EQ/compressor/maximizer; no offline mastering or rendered-stem replacement',
            'professional_quality_claimed':False,'candidate_preference':'unreviewed','sidechain':'Existing scheduled MIDI-kick gain curves, not an audio-triggered detector route'}
        write(dest/'verification.json',v);write(dest/'recipe.json',{'version':'phase20-replay-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'premaster_hash':state_hash(pre),'raw_A_sha256':digest(dest/AUDIO['A']),'raw_B_sha256':digest(dest/AUDIO['B']),'end_seconds':END,'production_receipt_sha256':digest(dest/'B/production.json'),'patch_manifest_sha256':{k:digest(v/'manifest.json') for k,v in patches.items()}})
        shutil.copytree(src.parent/'licenses',dest/'licenses')
        if inventory(src)!=before:raise ValidationError('source changed')
    except BaseException:shutil.rmtree(dest);raise
    return v


def prepare(root):
    root=Path(root)
    if any((root/n).exists() for n in ('README.md','reproduce.py','reproduction')):raise ValidationError('fresh download preparation required')
    shutil.copyfile(ROOT/'docs/PHASE20_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase20_reproduce.py',root/'reproduce.py')
    frozen=root/'reproduction';(frozen/'kuang').mkdir(parents=True)
    for p in (ROOT/'kuang').rglob('*'):
        if p.is_file() and p.suffix in ('.py','.lua','.json'):
            if p.is_symlink():raise ValidationError('frozen source symlink')
            target=frozen/'kuang'/p.relative_to(ROOT/'kuang');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    shutil.copyfile(ROOT/'LICENSE',frozen/'LICENSE');write(frozen/'source-manifest.json',inventory(frozen))


def package(root):
    root=Path(root);target=root/'phase20-house-listening.zip'
    if target.exists() or target.is_symlink():raise ValidationError('fresh listening ZIP required')
    files=[p for n in ('B','source','listening','licenses','reproduction') for p in (root/n).rglob('*') if p.is_file()]
    files += [root/n for n in ('README.md','reproduce.py','recipe.json','verification.json','controls-verification.json','pitch-verification.json','truepeak8x-verification.json','source-role-analysis.json','role-calibration.json')]
    if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files):raise ValidationError('unlicensed/unsupported bundled media')
    manifest={str(p.relative_to(root)):digest(p) for p in files}
    with tempfile.TemporaryDirectory(dir=root) as d:
        temp=Path(d)/'pack.zip'
        with zipfile.ZipFile(temp,'x',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(files):z.write(p,str(p.relative_to(root)))
            z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
        with zipfile.ZipFile(temp) as z:
            if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP integrity failed')
            if len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')])!=2:raise ValidationError('exactly two complete primary WAVs required')
        if temp.stat().st_size>190_000_000:raise ValidationError('listening ZIP size bound')
        os.link(temp,target)
    return {'bytes':target.stat().st_size,'sha256':digest(target)}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','prepare','package'));ap.add_argument('--out-dir',required=True);ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--meter-library');z=ap.parse_args()
    if z.action=='build' and not(z.soundcraft and z.plugin):ap.error('explicit reviewed host and plugin required')
    result=build(z.out_dir,z.soundcraft,z.plugin,z.meter_library) if z.action=='build' else prepare(z.out_dir) if z.action=='prepare' else package(z.out_dir)
    print(json.dumps(result,indent=2))
