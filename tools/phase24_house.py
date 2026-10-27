#!/usr/bin/env python3
"""Build ONE native144-bar record from approved Phase23; no alternate mixes."""
import argparse,json,shutil,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.groove_record import arrange_groove,audit_record,anchor_project,SOURCE_HASH,FORM
from kuang.schema import load,save,state_hash,ValidationError
from kuang.master_bus import MasterBusAdapter
from kuang.midi import export_bytes
from kuang.sample_assets import digest,inventory,write
from kuang.loudness import measure
from kuang.production_audio import production_metrics
from kuang.spatial_audio import spatial_metrics
from kuang.lowend_audio import band_metrics

END=144*4*60/126+5
WAV='Phase24-melody-free-extended-native.wav'

def adapter(host,plugin,workspace=ROOT):
 return MasterBusAdapter(host,plugin=plugin,workspace=workspace,scratch=Path(workspace)/'.local/phase24/tmp',center_pitch_bend=True)

def media(root,p):
 root=Path(root)
 return ({t.id:root/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'},
         {t.id:root/'native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')})

def build(out,host,plugin,meter=None):
 if Path(out).is_symlink():raise ValidationError('symlink output forbidden')
 out=Path(out).resolve()
 if out.exists() or not out.is_relative_to(ROOT/'.local/phase24'):raise ValidationError('fresh Phase24 stage required')
 src=ROOT/'artifacts/phase23-house';before=inventory(src);s=load(src/'project/project.kuang.json');p,r=arrange_groove(s);audit=audit_record(s,p,r)
 a=adapter(host,plugin);assets,patches=media(src/'project',p);out.mkdir();folder=out/'project';folder.mkdir()
 save(s,out/'approved-source.kuang.json');save(p,folder/'project.kuang.json');(folder/'song.mid').write_bytes(export_bytes(p))
 write(out/'composition-receipt.json',r);write(out/'record-audit.json',audit)
 write(folder/'source-song-spec.json',json.loads(s.metadata['song_spec']))
 a.export(p,assets,patches,folder/'native');print('Actual native144-bar project exported',flush=True)
 a.render(folder/'native',out/WAV,end_seconds=END);print('ONE full record rendered',flush=True)
 with tempfile.TemporaryDirectory(dir=a.scratch) as d:
  d=Path(d);a.save(folder/'native',d/'saved');a.render(d/'saved',d/'repeat.wav',end_seconds=END)
  if a.inspect(folder/'native')['native']!=a.inspect(d/'saved')['native'] or digest(out/WAV)!=digest(d/'repeat.wav'):raise ValidationError('full native state/PCM reopen changed')
  anchor=anchor_project(s,p)
  a.export(anchor,assets,patches,d/'anchor');a.render(d/'anchor',d/'anchor.wav',end_seconds=16*4*60/126+5)
  if digest(d/'anchor.wav')!=digest(src/'Phase23-no-melody-native.wav'):raise ValidationError('fresh anchor PCM differs from approved recording')
 print('Native reopen exact; fresh anchor PCM equals approved Phase23',flush=True)
 for tid,path in {**assets,**patches}.items():
  target=folder/'native'/('assets' if tid in assets else 'patches')/tid
  if inventory(path)!=inventory(target):raise ValidationError('approved media/patch changed '+tid)
 levels=measure(out/WAV,library=meter);spatial=spatial_metrics(out/WAV)
 if levels['clipped_samples'] or levels['true_peak_dbtp']>-1 or levels['rms']<=0 or spatial['mono_sum']['rms_loss_db']<-.5 or spatial['bands']['low_20_120']['mono_energy_retention']<.999:raise ValidationError('audio/mono/headroom integrity failed')
 regions=[('phrase-'+str(b+1),b*4*60/126,(b+8)*4*60/126) for b in range(0,144,8)]
 performance=production_metrics(out/WAV,regions);bands={key:band_metrics(out/WAV,first=b*4*60/126,last=(b+n)*4*60/126,windows=6) for key,_,b,n in FORM}
 if any(x['rms']<=0 for x in performance['sections'].values()):raise ValidationError('silent eight-bar region')
 report={'version':'phase24-one-record-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'source_human_approved':True,'new_finished_recordings':1,
  'bars':144,'bpm':126,'key':'C minor','levels':levels,'spatial':spatial,'phrase_audio':performance,'section_bands':bands,
  'approved_anchor_MIDI_patch_lanes_and_fresh_PCM_exact':True,'anchor_PCM_scope':'Exact reset render of anchor projection; whole-song incoming FX/history are intentionally not asserted byte-equal to a fresh16-bar render',
  'native_state_PCM_save_reopen_exact':True,'all_patch_sample_assets_exact':True,'mastering':False,'human_preference':'unreviewed','professional_quality_claimed':False}
 write(out/'verification.json',report);write(out/'recipe.json',{'version':'phase24-replay-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'end_seconds':END,'raw_sha256':digest(out/WAV),'receipt_sha256':digest(out/'composition-receipt.json'),
  'patches':{k:digest(v/'manifest.json') for k,v in patches.items()},'assets':{k:digest(v/'asset.json') for k,v in assets.items()}})
 shutil.copytree(src/'licenses',out/'licenses')
 if inventory(src)!=before:raise ValidationError('approved Phase23 release changed')
 print('Real audio/section diagnostics complete; source preserved',flush=True);return report

def package(root):
 root=Path(root);target=root/'phase24-melody-free-house.zip'
 if target.exists() or target.is_symlink():raise ValidationError('fresh package required')
 if not(root/'reproduction').exists():
  shutil.copyfile(ROOT/'docs/PHASE24_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase24_reproduce.py',root/'reproduce.py')
  for p in (ROOT/'kuang').rglob('*'):
   if p.is_file() and p.suffix in ('.py','.lua','.json'):
    out=root/'reproduction/kuang'/p.relative_to(ROOT/'kuang');out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
  shutil.copyfile(ROOT/'LICENSE',root/'reproduction/LICENSE');write(root/'reproduction/source-manifest.json',inventory(root/'reproduction'))
 files=[p for n in ('project','licenses','reproduction') for p in (root/n).rglob('*') if p.is_file()]
 files += [root/n for n in (WAV,'README.md','reproduce.py','approved-source.kuang.json','recipe.json','composition-receipt.json','record-audit.json','verification.json','pitch-proof.json','performance-proof.json')]
 if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files):raise ValidationError('foreign binary/reference content forbidden')
 manifest={str(p.relative_to(root)):digest(p) for p in files}
 with tempfile.TemporaryDirectory(dir=root) as d:
  temp=Path(d)/'pack.zip'
  with zipfile.ZipFile(temp,'x',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(files):z.write(p,str(p.relative_to(root)))
   z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
  with zipfile.ZipFile(temp) as z:
   if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP integrity failed')
   if [n for n in z.namelist() if '/' not in n and n.endswith('.wav')]!=[WAV]:raise ValidationError('exactly ONE finished record required')
   if any(n.endswith('.wav') and n!=WAV and not n.startswith(('project/native/assets/','project/native/Audio Files/','licenses/original-audio/')) for n in z.namelist()):raise ValidationError('unexpected listening/control recording in ZIP')
  shutil.move(temp,target)
 return {'bytes':target.stat().st_size,'sha256':digest(target)}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','package'));ap.add_argument('--out-dir',required=True);ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--meter-library');z=ap.parse_args()
 if z.action=='build' and not(z.soundcraft and z.plugin):ap.error('explicit pinned host/plugin required')
 print(json.dumps(build(z.out_dir,z.soundcraft,z.plugin,z.meter_library) if z.action=='build' else package(z.out_dir),indent=2))
