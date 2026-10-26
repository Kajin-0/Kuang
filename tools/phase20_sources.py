#!/usr/bin/env python3
"""Source-first native groove/full-record experiment; no master processing."""
import argparse,json,shutil,sys,tempfile,zipfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,save,state_hash,ValidationError
from kuang.source_production import source_record
from kuang.record_mix import SOURCE_HASH
from kuang.sample_assets import digest,inventory,write
from kuang.midi import export_bytes
from kuang.loudness import measure
from kuang.mastering import match_lufs
from kuang.production_audio import production_metrics
from kuang.lowend_audio import band_metrics
from kuang.spatial_audio import spatial_metrics
from kuang.audio import compare_wavs
from tools.phase20_house import adapter,media,END

AUDIO={'A':'A-Phase19-original-native.wav','B':'B-Phase20-source-production-native.wav'}


def build(destination,patch_folder,kick,host,plugin,meter=None):
    """Only the selected, actually tested pair of new voices; keep the bass/pad."""
    dest=Path(destination).resolve();patch_folder=Path(patch_folder).resolve();kick=Path(kick).resolve()
    if dest.exists() or dest.is_symlink() or not dest.is_relative_to(ROOT/'.local/phase20'):
        raise ValidationError('fresh Phase20 project-local staging required')
    src=ROOT/'artifacts/phase19-house/B';source=load(src/'project.kuang.json');before=inventory(src)
    patches_new={'track-harmony':patch_folder/'stab-body','track-lead':patch_folder/'lead-body'}
    p,receipt=source_record(source,patches_new,kick=kick);assets,patches=media(src,source)
    assets['track-kick']=kick;patches.update(patches_new)
    a=adapter(host,plugin,master=False);dest.mkdir()
    # Failed render/staging is retained privately for diagnosis, never published.
    for name,q in [('source',source),('B',p)]:
        folder=dest/name;folder.mkdir();save(q,folder/'project.kuang.json');(folder/'song.mid').write_bytes(export_bytes(q))
    write(dest/'B/production.json',receipt);write(dest/'B/source-song-spec.json',json.loads(source.metadata['song_spec']))
    shutil.copytree(src/'native',dest/'source/native');a.inspect(dest/'source/native')
    a.export(p,assets,patches,dest/'B/native');a.render(dest/'B/native',dest/AUDIO['B'],end_seconds=END)
    shutil.copyfile(src.parent/'B-Phase19-continuity-native.wav',dest/AUDIO['A']);print('Full source-first song rendered, no master',flush=True)
    with tempfile.TemporaryDirectory(dir=a.scratch) as d:
        d=Path(d);a.save(dest/'B/native',d/'saved');a.render(d/'saved',d/'repeat.wav',end_seconds=END)
        if a.inspect(dest/'B/native')['native']!=a.inspect(d/'saved')['native'] or digest(d/'repeat.wav')!=digest(dest/AUDIO['B']):
            raise ValidationError('source production native full state/PCM reopen failed')
    levels={k:measure(dest/n,library=meter) for k,n in AUDIO.items()}
    if any(v['clipped_samples'] or v['rms']<=0 for v in levels.values()) or levels['B']['true_peak_dbtp']>-.5:
        raise ValidationError('source mix clipping/headroom failed; do not rescue with mastering')
    (dest/'listening').mkdir();target=min(v['integrated_lufs'] for v in levels.values())
    matching={k:match_lufs(dest/n,dest/'listening'/(k+'-'+('Phase19-original' if k=='A' else 'Phase20-source-production')+'-FULL-MATCHED.wav'),target,library=meter) for k,n in AUDIO.items()}
    regions=[(s.name,s.start/p.ppq*60/126,(s.start+s.length)/p.ppq*60/126) for s in p.sections]
    sections={k:production_metrics(dest/n,regions)['sections'] for k,n in AUDIO.items()}
    bands={k:{label:band_metrics(dest/n,first=lo,last=hi,windows=4) for label,lo,hi in regions} for k,n in AUDIO.items()}
    spatial={k:spatial_metrics(dest/n) for k,n in AUDIO.items()}
    if spatial['B']['bands']['low_20_120']['mono_energy_retention']<.999 or spatial['B']['mono_sum']['rms_loss_db']<-.5:
        raise ValidationError('source production mono compatibility failed')
    if inventory(src)!=before:raise ValidationError('source project changed')
    v={'version':'phase20-source-first-verification-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),
       'notes':sum(len(c.notes) for t in p.tracks for c in t.clips),'bars':160,'bpm':126,'key':'C minor','sections':9,
       'MIDI_bytes_exact':export_bytes(p)==export_bytes(source),'source_PCM_exact':digest(dest/AUDIO['A'])==digest(src.parent/'B-Phase19-continuity-native.wav'),
       'native_save_reopen_state_PCM_exact':True,'native_master_processing':False,'offline_mastering':False,
       'changed_sources':['track-kick','track-harmony','track-lead'],'approved_bass_and_pad_patch_exact':True,
       'levels':levels,'matching':matching,'section_audio':sections,'section_bands':bands,'spatial':spatial,
       'candidate_preference':'unreviewed','professional_quality_claimed':False,
       'sidechain':'Scheduled MIDI-kick attenuation retained, not an audio-triggered external detector',
       'gate':'Substantial same-input source/role PCM change and tuning/integrity; human listening decides preference, not loudness or spectral scores'}
    write(dest/'verification.json',v)
    write(dest/'recipe.json',{'version':'phase20-source-replay-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),
       'raw_A_sha256':digest(dest/AUDIO['A']),'raw_B_sha256':digest(dest/AUDIO['B']),'end_seconds':END,
       'production_receipt_sha256':digest(dest/'B/production.json'),
       'changed_patch_tracks':sorted(patches_new),'changed_sample_tracks':['track-kick'],
       'patch_manifest_sha256':{t:digest(path/'manifest.json') for t,path in patches.items()},
       'asset_manifest_sha256':{t:digest(path/'asset.json') for t,path in assets.items()}})
    shutil.copytree(src.parent/'licenses',dest/'licenses');write(dest/'licenses/phase20-replacement-kick.json',json.loads((kick/'asset.json').read_text())['provenance'])
    return v


def prepare(root,groove_root):
    root=Path(root);groove_root=Path(groove_root)
    if (root/'reproduction').exists() or (root/'groove-preview').exists():raise ValidationError('fresh source download preparation required')
    shutil.copyfile(ROOT/'docs/PHASE20_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase20_source_reproduce.py',root/'reproduce.py')
    frozen=root/'reproduction';(frozen/'kuang').mkdir(parents=True)
    for p in (ROOT/'kuang').rglob('*'):
        if p.is_file() and p.suffix in ('.py','.lua','.json'):
            if p.is_symlink():raise ValidationError('frozen source symlink')
            target=frozen/'kuang'/p.relative_to(ROOT/'kuang');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    shutil.copyfile(ROOT/'LICENSE',frozen/'LICENSE');write(frozen/'source-manifest.json',inventory(frozen))
    preview=root/'groove-preview';preview.mkdir()
    for letter,case in [('A','A-original'),('B','E-tight-original-bass')]:
        folder=preview/letter;folder.mkdir();q=load(groove_root/case/'project.kuang.json');save(q,folder/'project.kuang.json');(folder/'song.mid').write_bytes(export_bytes(q));shutil.copytree(groove_root/case/'native',folder/'native')
        shutil.copyfile(groove_root/'matched'/(case+'-16bar-MATCHED.wav'),preview/(letter+'-MAIN16-MATCHED.wav'))
    write(preview/'verification.json',json.loads((groove_root/'verification.json').read_text()))
    (preview/'README.txt').write_text('Same source bars32-48,608 original MIDI events, native16-bar DSP reset plus5s tail. Both have an identical transparent -6dB capture trim, no terminal EQ/compressor/limiter. Constant attenuation only for matched audition. Not an identical slice of running full-song effect tails. A=Phase19; B=selected new kick/stab/lead, incumbent bass and pad. Human preference pending.\n')


def package(root):
    root=Path(root);target=root/'phase20-house-listening.zip'
    if target.exists():raise ValidationError('fresh ZIP required')
    files=[p for n in ('B','source','listening','groove-preview','licenses','reproduction') for p in (root/n).rglob('*') if p.is_file()]
    files += [root/n for n in ('README.md','reproduce.py','recipe.json','verification.json','source-controls.json','source-pitch.json')]
    if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files):raise ValidationError('unlicensed/unsupported bundled file')
    manifest={str(p.relative_to(root)):digest(p) for p in files}
    with tempfile.TemporaryDirectory(dir=root) as d:
        temp=Path(d)/'pack.zip'
        with zipfile.ZipFile(temp,'x',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(files):z.write(p,str(p.relative_to(root)))
            z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
        with zipfile.ZipFile(temp) as z:
            if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP integrity failed')
            if len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')])!=2:raise ValidationError('two primary complete listening WAVs required')
        if temp.stat().st_size>200_000_000:raise ValidationError('source listening ZIP exceeds200MB bound')
        os.link(temp,target)
    return {'bytes':target.stat().st_size,'sha256':digest(target)}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','prepare','package'));ap.add_argument('--out-dir',required=True);ap.add_argument('--patches');ap.add_argument('--kick');ap.add_argument('--groove-root');ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--meter-library');z=ap.parse_args()
    if z.action=='build' and not all((z.patches,z.kick,z.soundcraft,z.plugin)):ap.error('explicit prepared patches, licensed kick, host and plugin required')
    if z.action=='prepare' and not z.groove_root:ap.error('verified main16-bar prototypes required')
    result=build(z.out_dir,z.patches,z.kick,z.soundcraft,z.plugin,z.meter_library) if z.action=='build' else prepare(z.out_dir,z.groove_root) if z.action=='prepare' else package(z.out_dir)
    print(json.dumps(result,indent=2))
