#!/usr/bin/env python3
"""An authored melodic/harmonic performance on the exact Phase20 rhythm section."""
import argparse,json,os,shutil,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.house_theme import compose_theme,SOURCE_HASH
from kuang.theme_audit import audit_theme,require_theme
from kuang.schema import load,save,state_hash,ValidationError
from kuang.production_host import ProductionAdapter
from kuang.midi import export_bytes
from kuang.sample_assets import digest,inventory,write
from kuang.loudness import measure
from kuang.mastering import match_lufs
from kuang.production_audio import production_metrics
from kuang.spatial_audio import spatial_metrics
from kuang.master_bus import attach_terminal
from tools.phase20_verify import window
END=160*4*60/126+5
AUDIO={'A':'A-Phase20-source-reference-native.wav','B':'B-Phase21-melodic-house-native.wav'}


def adapter(host,plugin):
 return ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase21/tmp',center_pitch_bend=True)


def media(root,p):
 root=Path(root)
 return ({t.id:root/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'},
         {t.id:root/'native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')})


def build(destination,host,plugin,meter=None):
 dest=Path(destination).resolve()
 if dest.exists() or dest.is_symlink() or not dest.is_relative_to(ROOT/'.local/phase21'):raise ValidationError('fresh project-local Phase21 staging required')
 src=ROOT/'artifacts/phase20-house/B';s=load(src/'project.kuang.json');before=inventory(src);p,receipt=compose_theme(s);audit=audit_theme(s,p,receipt);require_theme(audit)
 assets,patches=media(src,p);a=adapter(host,plugin);dest.mkdir()
 # Keep failed experiments private for diagnosis; publication is a separate gate.
 for name,q in [('source',s),('B',p)]:
  folder=dest/name;folder.mkdir();save(q,folder/'project.kuang.json');(folder/'song.mid').write_bytes(export_bytes(q))
 shutil.copytree(src/'native',dest/'source/native');write(dest/'B/source-song-spec.json',json.loads(s.metadata['song_spec']))
 write(dest/'composition-receipt.json',receipt);write(dest/'theme-audit.json',audit)
 shutil.copyfile(src.parent/'B-Phase20-source-production-native.wav',dest/AUDIO['A'])
 a.export(p,assets,patches,dest/'B/native');a.render(dest/'B/native',dest/AUDIO['B'],end_seconds=END);print('Full160-bar new melodic/harmonic performance rendered',flush=True)
 with tempfile.TemporaryDirectory(dir=a.scratch) as d:
  d=Path(d);a.save(dest/'B/native',d/'saved');a.render(d/'saved',d/'repeat.wav',end_seconds=END)
  if a.inspect(dest/'B/native')['native']!=a.inspect(d/'saved')['native'] or digest(d/'repeat.wav')!=digest(dest/AUDIO['B']):raise ValidationError('new composition native state/PCM reopen failed')
 for tid,path in {**assets,**patches}.items():
  target=dest/'B/native'/('assets' if tid in assets else 'patches')/tid
  if inventory(path)!=inventory(target):raise ValidationError('approved instrument asset changed')
 levels={k:measure(dest/name,library=meter) for k,name in AUDIO.items()}
 if any(x['clipped_samples'] or x['rms']<=0 or x['true_peak_dbtp']>-.5 for x in levels.values()):raise ValidationError('native composition PCM integrity/headroom failed')
 (dest/'listening').mkdir();target=min(x['integrated_lufs'] for x in levels.values())
 matching={k:match_lufs(dest/name,dest/'listening'/(k+'-'+('Phase20-reference' if k=='A' else 'Phase21-theme')+'-FULL-MATCHED.wav'),target,library=meter) for k,name in AUDIO.items()}
 regions=[(x.name,x.start/p.ppq*60/126,(x.start+x.length)/p.ppq*60/126) for x in p.sections]
 sections={k:production_metrics(dest/name,regions)['sections'] for k,name in AUDIO.items()};spatial=spatial_metrics(dest/AUDIO['B'])
 if spatial['bands']['low_20_120']['mono_energy_retention']<.999 or spatial['mono_sum']['rms_loss_db']<-.5:raise ValidationError('low-end/mono compatibility failed')
 if inventory(src)!=before:raise ValidationError('incumbent Phase20 source changed')
 report={'version':'phase21-melodic-performance-verification-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'source_notes':len(receipt['removed_notes'])+receipt['retained_notes'],'candidate_notes':receipt['candidate_notes'],
  'music':{'bars':160,'bpm':126,'key':'C minor','sections':9,'MIDI_bytes_exact':False,'all_drum_bass_subpulse_tracks_exact':True,'prepared_instruments_samples_graph_FX_mixer_lanes_exact':True},
  'A_PCM_exact':digest(dest/AUDIO['A'])==digest(src.parent/'B-Phase20-source-production-native.wav'),'native_state_and_PCM_reopen_exact':True,
  'levels':levels,'matching':matching,'sections':sections,'spatial_B':spatial,'mastering':False,'professional_quality_claimed':False,'candidate_preference':'unreviewed',
  'comparison':'Same exact rhythm section/palette/mix; deliberately new melody, harmony, pad performance and counterline. Integrated level matching is an audition control, never a quality score.'}
 write(dest/'verification.json',report)
 write(dest/'recipe.json',{'version':'phase21-replay-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'raw_A_sha256':digest(dest/AUDIO['A']),'raw_B_sha256':digest(dest/AUDIO['B']),'end_seconds':END,
  'composition_receipt_sha256':digest(dest/'composition-receipt.json'),'patch_manifest_sha256':{t:digest(v/'manifest.json') for t,v in patches.items()},'asset_manifest_sha256':{t:digest(v/'asset.json') for t,v in assets.items()}})
 shutil.copytree(src.parent/'licenses',dest/'licenses');return report


def prepare(root,prototype):
 root=Path(root);prototype=Path(prototype)
 if (root/'reproduction').exists():raise ValidationError('fresh download preparation required')
 shutil.copyfile(ROOT/'docs/PHASE21_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase21_reproduce.py',root/'reproduce.py')
 frozen=root/'reproduction';(frozen/'kuang').mkdir(parents=True)
 for p in (ROOT/'kuang').rglob('*'):
  if p.is_file() and p.suffix in ('.py','.lua','.json'):
   if p.is_symlink():raise ValidationError('source symlink')
   target=frozen/'kuang'/p.relative_to(ROOT/'kuang');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 shutil.copyfile(ROOT/'LICENSE',frozen/'LICENSE');write(frozen/'source-manifest.json',inventory(frozen))
 preview=root/'main16';preview.mkdir()
 for n,path in [('A',root/'source/project.kuang.json'),('B',root/'B/project.kuang.json')]:
  q=attach_terminal(window(load(path),32,16));q.tracks[-1].controls['mixer.gain_db']=-6
  if state_hash(q)!=state_hash(load(prototype/n/'project.kuang.json')):raise ValidationError('main16 prototype no longer describes the selected score')
  shutil.copytree(prototype/n,preview/n);shutil.copyfile(prototype/'matched'/(n+'-MAIN16-MATCHED.wav'),preview/(n+'-MAIN16-MATCHED.wav'))
 shutil.copyfile(prototype/'verification.json',preview/'verification.json')
 (preview/'README.txt').write_text('Source bars32-48; identical drums,bass,subpulse and instruments/mix. Upper melody/harmony/pad MIDI intentionally differs. Fresh native DSP reset, common transparent -6dB capture trim, no terminal FX. Matched only by constant attenuation. This is not an exact slice of running full-song release/FX tails.\n')


def package(root):
 root=Path(root);target=root/'phase21-house-listening.zip'
 if target.exists() or target.is_symlink():raise ValidationError('fresh ZIP required')
 files=[p for n in ('B','source','listening','main16','licenses','reproduction') for p in (root/n).rglob('*') if p.is_file()]
 files += [root/n for n in ('README.md','reproduce.py','recipe.json','verification.json','composition-receipt.json','theme-audit.json','pitch-verification.json','context-verification.json')]
 if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files):raise ValidationError('unsupported bundled media/binary')
 manifest={str(p.relative_to(root)):digest(p) for p in files}
 with tempfile.TemporaryDirectory(dir=root) as d:
  temp=Path(d)/'pack.zip'
  with zipfile.ZipFile(temp,'x',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(files):z.write(p,str(p.relative_to(root)))
   z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
  with zipfile.ZipFile(temp) as z:
   if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP integrity failed')
   if len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')])!=2:raise ValidationError('two complete primary songs required')
  if temp.stat().st_size>200_000_000:raise ValidationError('listening ZIP exceeds200MB')
  os.link(temp,target)
 return {'bytes':target.stat().st_size,'sha256':digest(target)}


if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','prepare','package'));ap.add_argument('--out-dir',required=True);ap.add_argument('--prototype');ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--meter-library');z=ap.parse_args()
 if z.action=='build' and not(z.soundcraft and z.plugin):ap.error('reviewed host/plugin required')
 if z.action=='prepare' and not z.prototype:ap.error('verified main16 prototype required')
 result=build(z.out_dir,z.soundcraft,z.plugin,z.meter_library) if z.action=='build' else prepare(z.out_dir,z.prototype) if z.action=='prepare' else package(z.out_dir)
 print(json.dumps(result,indent=2))
