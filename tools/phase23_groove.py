#!/usr/bin/env python3
"""ONE melody-free16-bar native candidate, no full-song/shortlist generation."""
import argparse,json,os,shutil,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.chord_bed import compose_bed,audit_bed,REFERENCE_HASH
from kuang.external_synth import bound_project,read_patch
from kuang.master_bus import MasterBusAdapter
from kuang.schema import load,save,state_hash,ValidationError
from kuang.sample_assets import digest,inventory,write
from kuang.midi import export_bytes
from kuang.loudness import measure
from kuang.spatial_audio import spatial_metrics
END=16*4*60/126+5
WAV='Phase23-no-melody-native.wav'

def adapter(host,plugin,workspace=ROOT):
 return MasterBusAdapter(host,plugin=plugin,workspace=workspace,scratch=Path(workspace)/'.local/phase23/tmp',center_pitch_bend=True)

def media(root,p):
 root=Path(root)
 return ({t.id:root/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'},
         {t.id:root/'native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')})

def build(out,patches,host,plugin,meter=None):
 if Path(out).is_symlink():raise ValidationError('symlink output forbidden')
 out=Path(out).resolve();patches=Path(patches).resolve()
 if out.exists() or not out.is_relative_to(ROOT/'.local/phase23') or not patches.is_relative_to(ROOT):raise ValidationError('fresh project-local Phase23 output/patches required')
 src=ROOT/'artifacts/phase22-house/A';before=inventory(src);s=load(src/'project.kuang.json');q,r=compose_bed(s)
 changed={'track-harmony':patches/'stab','track-depth-pad':patches/'pad'}
 for path in changed.values():read_patch(path)
 p=bound_project(q,changed);r.update(candidate_hash=state_hash(p),prepared_patch_manifests={k:digest(v/'manifest.json') for k,v in changed.items()});audit=audit_bed(s,p,r)
 assets,oldpatches=media(src,p);pp={**oldpatches,**changed};a=adapter(host,plugin);out.mkdir();save(s,out/'reference.kuang.json');folder=out/'project';folder.mkdir()
 save(p,folder/'project.kuang.json');(folder/'song.mid').write_bytes(export_bytes(p));write(out/'production-receipt.json',r);write(out/'harmonic-audit.json',audit)
 a.export(p,assets,pp,folder/'native');a.render(folder/'native',out/WAV,end_seconds=END)
 with tempfile.TemporaryDirectory(dir=a.scratch) as d:
  d=Path(d);a.save(folder/'native',d/'saved');a.render(d/'saved',d/'repeat.wav',end_seconds=END)
  if a.inspect(folder/'native')['native']!=a.inspect(d/'saved')['native'] or digest(out/WAV)!=digest(d/'repeat.wav'):raise ValidationError('native state/PCM reopen mismatch')
 levels=measure(out/WAV,library=meter);spatial=spatial_metrics(out/WAV)
 if levels['clipped_samples'] or levels['rms']<=0 or spatial['bands']['low_20_120']['mono_energy_retention']<.999 or spatial['mono_sum']['rms_loss_db']<-.5:raise ValidationError('audio/mono integrity failed')
 # Read an EXISTING baseline only. No new baseline/full-song/alternative render.
 existing=ROOT/'artifacts/phase22-house/listening/A-Phase21-incumbent-MATCHED.wav';ref=measure(existing,library=meter)
 report={'version':'phase23-one-bed-1','reference_hash':REFERENCE_HASH,'candidate_hash':state_hash(p),'bars':16,'bpm':126,'key':'C minor',
         'new_full_mix_compositions':1,'lead_arp_ornamental_air_absent':True,'levels':levels,'spatial':spatial,'native_state_PCM_reopen_exact':True,
         'comparison':{'existing_reference':str(existing.relative_to(ROOT)),'existing_reference_sha256':digest(existing),'levels':ref,
          'reference_gain_db_to_match_candidate':levels['integrated_lufs']-ref['integrated_lufs'],'processing':'No new reference bounce or master; constant player gain only for fair reference comparison'},
         'mastering':False,'human_preference':'unreviewed','professional_quality_claimed':False}
 write(out/'verification.json',report);write(out/'recipe.json',{'version':'phase23-replay-1','reference_hash':REFERENCE_HASH,'score_hash':r['score_hash'],'candidate_hash':state_hash(p),'end_seconds':END,'raw_sha256':digest(out/WAV),'receipt_sha256':digest(out/'production-receipt.json'),
     'patches':{k:digest(v/'manifest.json') for k,v in pp.items()},'assets':{k:digest(v/'asset.json') for k,v in assets.items()}})
 shutil.copytree(ROOT/'artifacts/phase22-house/licenses',out/'licenses')
 if inventory(src)!=before:raise ValidationError('historical reference changed')
 print('ONE candidate rendered; full native state and PCM reopen exact',flush=True);return report

def package(root):
 root=Path(root);target=root/'phase23-no-melody-groove.zip'
 if target.exists() or target.is_symlink():raise ValidationError('fresh package required')
 if not(root/'reproduction').exists():
  shutil.copyfile(ROOT/'docs/PHASE23_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase23_reproduce.py',root/'reproduce.py')
  for p in (ROOT/'kuang').rglob('*'):
   if p.is_file() and p.suffix in ('.py','.lua','.json'):
    out=root/'reproduction/kuang'/p.relative_to(ROOT/'kuang');out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
  shutil.copyfile(ROOT/'LICENSE',root/'reproduction/LICENSE');write(root/'reproduction/source-manifest.json',inventory(root/'reproduction'))
 files=[p for n in ('project','licenses','reproduction') for p in (root/n).rglob('*') if p.is_file()]
 files += [root/n for n in (WAV,'README.md','reproduce.py','reference.kuang.json','recipe.json','production-receipt.json','harmonic-audit.json','verification.json','sound-proof.json','pitch-proof.json')]
 if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files):raise ValidationError('foreign binary/reference content forbidden')
 manifest={str(p.relative_to(root)):digest(p) for p in files}
 with tempfile.TemporaryDirectory(dir=root) as d:
  temp=Path(d)/'pack.zip'
  with zipfile.ZipFile(temp,'x',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(files):z.write(p,str(p.relative_to(root)))
   z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
  with zipfile.ZipFile(temp) as z:
   if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP mismatch')
   waves=[n for n in z.namelist() if n.endswith('.wav')]
   if [n for n in waves if '/' not in n]!=[WAV] or any(n!=WAV and not n.startswith(('project/native/assets/','project/native/Audio Files/','licenses/original-audio/')) for n in waves):raise ValidationError('exactly one new finished mix plus licensed drum assets required')
  if temp.stat().st_size>40_000_000:raise ValidationError('compact single-groove pack exceeds40MB')
  os.link(temp,target)
 return {'bytes':target.stat().st_size,'sha256':digest(target)}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','package'));ap.add_argument('--out-dir',required=True);ap.add_argument('--patches');ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--meter-library');z=ap.parse_args()
 if z.action=='build' and not all((z.patches,z.soundcraft,z.plugin)):ap.error('explicit prepared patches and host/plugin required')
 print(json.dumps(build(z.out_dir,z.patches,z.soundcraft,z.plugin,z.meter_library) if z.action=='build' else package(z.out_dir),indent=2))
