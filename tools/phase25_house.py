#!/usr/bin/env python3
"""One source-first144-bar production refinement and honest full-song A/B."""
import argparse,json,shutil,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.production_refinement import refine_record,audit_refinement,refined_patch,SOURCE_HASH
from kuang.external_synth import bound_project,read_patch
from kuang.schema import load,save,state_hash,ValidationError
from kuang.master_bus import MasterBusAdapter
from kuang.midi import export_bytes
from kuang.sample_assets import digest,inventory,write
from kuang.loudness import measure
from kuang.mastering import match_lufs
from kuang.production_audio import production_metrics
from kuang.spatial_audio import spatial_metrics
from kuang.lowend_audio import band_metrics
END=144*4*60/126+5
RAW='B-Phase25-production-native.wav'
LISTEN={'A':'A-Phase24-reference-MATCHED.wav','B':'B-Phase25-production-MATCHED.wav'}

def adapter(host,plugin,workspace=ROOT):
 return MasterBusAdapter(host,plugin=plugin,workspace=workspace,scratch=Path(workspace)/'.local/phase25/tmp',center_pitch_bend=True)

def media(root,p):
 root=Path(root)
 return ({t.id:root/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'},
         {t.id:root/'native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')})

def build(out,patches,host,plugin,host_python,meter=None):
 if Path(out).is_symlink():raise ValidationError('symlink output forbidden')
 out=Path(out).resolve();patches=Path(patches).resolve()
 if out.exists() or not out.is_relative_to(ROOT/'.local/phase25') or not patches.is_relative_to(ROOT):raise ValidationError('fresh project-local Phase25 stage/patches required')
 src=ROOT/'artifacts/phase24-house';before=inventory(src);s=load(src/'project/project.kuang.json');q,r=refine_record(s)
 changed={'track-harmony':patches/'stab','track-depth-pad':patches/'pad'}
 for tid,path in changed.items():
  read_patch(path);voice='stab' if tid=='track-harmony' else 'pad'
  if json.loads((path/'patch.vital').read_text())!=refined_patch(voice):raise ValidationError('reviewed calibrated source recipe required')
 p=bound_project(q,changed);r.update(candidate_hash=state_hash(p),prepared_patch_manifests={k:digest(v/'manifest.json') for k,v in changed.items()});audit=audit_refinement(s,p,r)
 a=adapter(host,plugin);assets,pp=media(src/'project',p);pp.update(changed);out.mkdir();folder=out/'project';folder.mkdir()
 save(s,out/'phase24-source.kuang.json');save(p,folder/'project.kuang.json');(folder/'song.mid').write_bytes(export_bytes(p))
 write(out/'production-receipt.json',r);write(out/'scope-audit.json',audit);shutil.copyfile(ROOT/'.local/phase25/gain-calibration.json',out/'gain-calibration.json')
 a.export(p,assets,pp,folder/'native');print('Native source/space production exported',flush=True)
 from tools.phase25_verify import pitch,source_controls
 tuning=pitch(out,ROOT/'.local/phase25/pitch',host,plugin,host_python);write(out/'pitch-proof.json',tuning)
 causal=source_controls(out,host,plugin,meter);write(out/'source-proof.json',causal)
 print('Actual tuning and equal-level source/motion gates pass before full render',flush=True)
 a.render(folder/'native',out/RAW,end_seconds=END);print('ONE revised full record rendered',flush=True)
 with tempfile.TemporaryDirectory(dir=a.scratch) as d:
  d=Path(d);a.save(folder/'native',d/'saved');a.render(d/'saved',d/'repeat.wav',end_seconds=END)
  if a.inspect(folder/'native')['native']!=a.inspect(d/'saved')['native'] or digest(out/RAW)!=digest(d/'repeat.wav'):raise ValidationError('full native state/PCM reopen changed')
 original=src/'Phase24-melody-free-extended-native.wav';levels={'A':measure(original,library=meter),'B':measure(out/RAW,library=meter)}
 if any(x['clipped_samples'] or x['true_peak_dbtp']>-1 or x['rms']<=0 for x in levels.values()):raise ValidationError('raw native non-silence/headroom gate failed')
 if levels['A']['frames']!=levels['B']['frames']:raise ValidationError('full A/B time drift')
 (out/'listening').mkdir();target=min(x['integrated_lufs'] for x in levels.values())-.1
 matching={k:match_lufs(path,out/'listening'/LISTEN[k],target,library=meter) for k,path in [('A',original),('B',out/RAW)]}
 spatial=spatial_metrics(out/RAW)
 if spatial['mono_sum']['rms_loss_db']<-.5 or spatial['bands']['low_20_120']['mono_energy_retention']<.999:raise ValidationError('mono integrity failed')
 regions=[('phrase-'+str(b+1),b*4*60/126,(b+8)*4*60/126) for b in range(0,144,8)]
 performance=production_metrics(out/RAW,regions);bands={label:band_metrics(out/RAW,first=b*4*60/126,last=(b+8)*4*60/126,windows=6) for label,b in [('anchor',16),('return',80),('late',112)]}
 for tid,path in assets.items():
  if inventory(path)!=inventory(folder/'native/assets'/tid):raise ValidationError('licensed sample changed')
 if inventory(src/'project/native/patches/track-bass')!=inventory(folder/'native/patches/track-bass'):raise ValidationError('approved bass source changed')
 report={'version':'phase25-source-production-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'new_candidates':1,'bars':144,'bpm':126,'key':'C minor',
  'raw_reference_path':str(original.relative_to(ROOT)),'raw_reference_sha256':digest(original),'raw_levels':levels,'matching':matching,'spatial':spatial,'phrase_audio':performance,'selected_bands':bands,
  'native_state_PCM_save_reopen_exact':True,'anchor_MIDI_exact':True,'anchor_upper_audio_exact':False,'mastering':False,'human_preference':'unreviewed','professional_quality_claimed':False}
 write(out/'verification.json',report);write(out/'recipe.json',{'version':'phase25-replay-1','source_hash':SOURCE_HASH,'score_hash':r['score_hash'],'candidate_hash':state_hash(p),'end_seconds':END,'raw_sha256':digest(out/RAW),'receipt_sha256':digest(out/'production-receipt.json'),
  'patches':{k:digest(v/'manifest.json') for k,v in pp.items()},'assets':{k:digest(v/'asset.json') for k,v in assets.items()},
  'audition_gain_db':matching['B']['gain_db'],'audition_sha256':digest(out/'listening'/LISTEN['B'])})
 shutil.copytree(src/'licenses',out/'licenses')
 if inventory(src)!=before:raise ValidationError('historical Phase24 changed')
 print('Full equal-LUFS A/B and source preservation verified; no master',flush=True);return report

def package(root):
 root=Path(root);target=root/'phase25-house-listening.zip'
 if target.exists() or target.is_symlink():raise ValidationError('fresh package required')
 if not(root/'reproduction').exists():
  shutil.copyfile(ROOT/'docs/PHASE25_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase25_reproduce.py',root/'reproduce.py')
  for p in (ROOT/'kuang').rglob('*'):
   if p.is_file() and p.suffix in ('.py','.lua','.json'):
    out=root/'reproduction/kuang'/p.relative_to(ROOT/'kuang');out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
  shutil.copyfile(ROOT/'LICENSE',root/'reproduction/LICENSE');write(root/'reproduction/source-manifest.json',inventory(root/'reproduction'))
 files=[p for n in ('project','licenses','reproduction','listening') for p in (root/n).rglob('*') if p.is_file()]
 files += [root/n for n in ('README.md','reproduce.py','phase24-source.kuang.json','recipe.json','production-receipt.json','scope-audit.json','verification.json','source-proof.json','pitch-proof.json','rhythm-proof.json','master-gate.json','gain-calibration.json')]
 if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files):raise ValidationError('foreign binary/reference content forbidden')
 manifest={str(p.relative_to(root)):digest(p) for p in files}
 with tempfile.TemporaryDirectory(dir=root) as d:
  temp=Path(d)/'pack.zip'
  with zipfile.ZipFile(temp,'x',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(files):z.write(p,str(p.relative_to(root)))
   z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
  with zipfile.ZipFile(temp) as z:
   if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP integrity failed')
   if sorted(n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav'))!=sorted('listening/'+n for n in LISTEN.values()):raise ValidationError('exactly TWO full A/B listening files required')
   if any(n.endswith('.wav') and not n.startswith(('listening/','project/native/assets/','project/native/Audio Files/','licenses/original-audio/')) for n in z.namelist()):raise ValidationError('unexpected raw/control audio in ZIP')
  shutil.move(temp,target)
 return {'bytes':target.stat().st_size,'sha256':digest(target)}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','package'));ap.add_argument('--out-dir',required=True);ap.add_argument('--patches');ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--host-python');ap.add_argument('--meter-library');z=ap.parse_args()
 if z.action=='build' and not all((z.patches,z.soundcraft,z.plugin,z.host_python)):ap.error('explicit prepared sources and pinned host/plugin required')
 print(json.dumps(build(z.out_dir,z.patches,z.soundcraft,z.plugin,z.host_python,z.meter_library) if z.action=='build' else package(z.out_dir),indent=2))
