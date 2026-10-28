#!/usr/bin/env python3
"""Build the single Phase26 functional house arrangement with real native proof."""
import argparse,json,shutil,sys,tempfile,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.groove_direction import compose_direction,audit_direction,SOURCE_HASH
from kuang.schema import load,save,state_hash,ValidationError
from kuang.master_bus import MasterBusAdapter
from kuang.sample_assets import digest,inventory,write
from kuang.midi import export_bytes
from kuang.loudness import measure
from kuang.mastering import match_lufs
from kuang.production_audio import production_metrics
from kuang.spatial_audio import spatial_metrics
from kuang.gestures import crop
END=144*4*60/126+5
RAW='B-Phase26-direction-native.wav'
LISTEN={'A':'A-Phase25-reference-MATCHED.wav','B':'B-Phase26-direction-MATCHED.wav'}
def adapter(host,plugin,workspace=ROOT):return MasterBusAdapter(host,plugin=plugin,workspace=workspace,scratch=Path(workspace)/'.local/phase26/tmp',center_pitch_bend=True)
def media(root,p):
 return ({t.id:Path(root)/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}, {t.id:Path(root)/'native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')})
def build(out,host,plugin,host_python,meter):
 out=Path(out)
 if out.exists() or out.is_symlink() or not out.resolve().is_relative_to(ROOT/'.local/phase26'):raise ValidationError('fresh Phase26 staging required')
 src=ROOT/'artifacts/phase25-house';before=inventory(src);s=load(src/'project/project.kuang.json');p,r=compose_direction(s);audit=audit_direction(s,p,r)
 out.mkdir();(out/'project').mkdir();save(s,out/'phase25-source.kuang.json');save(p,out/'project/project.kuang.json');(out/'project/song.mid').write_bytes(export_bytes(p));write(out/'composition-receipt.json',r);write(out/'harmony-audit.json',audit)
 a=adapter(host,plugin);assets,patches=media(src/'project',p);a.export(p,assets,patches,out/'project/native');print('Functional record native export complete',flush=True)
 from tools.phase26_pitch import pitch
 write(out/'pitch-proof.json',pitch(out,ROOT/'.local/phase26/pitch',host,plugin,host_python));print('Two-host actual tuning/chord gate passed',flush=True)
 with tempfile.TemporaryDirectory(dir=a.scratch) as temp:
  temp=Path(temp);hashes=[]
  for label,score in [('A',s),('B',p)]:
   q=crop(score,16,16,[t.id for t in score.tracks]);a.export(q,assets,patches,temp/label);a.render(temp/label,temp/(label+'.wav'),end_seconds=16*4*60/126+5);hashes.append(digest(temp/(label+'.wav')))
  if hashes[0]!=hashes[1]:raise ValidationError('full reset anchor PCM changed')
  a.render(out/'project/native',out/RAW,end_seconds=END);a.save(out/'project/native',temp/'saved');a.render(temp/'saved',temp/'repeat.wav',end_seconds=END)
  if digest(out/RAW)!=digest(temp/'repeat.wav') or a.inspect(out/'project/native')['native']!=a.inspect(temp/'saved')['native']:raise ValidationError('native state/PCM reload drift')
 original=src/'B-Phase25-production-native.wav';levels={k:measure(f,library=meter) for k,f in [('A',original),('B',out/RAW)]}
 if any(x['clipped_samples'] or x['rms']==0 or x['true_peak_dbtp']>-1 for x in levels.values()):raise ValidationError('audio integrity failed')
 (out/'listening').mkdir();target=min(x['integrated_lufs'] for x in levels.values())-.1;matched={k:match_lufs(f,out/'listening'/LISTEN[k],target,library=meter) for k,f in [('A',original),('B',out/RAW)]}
 spatial=spatial_metrics(out/RAW)
 if spatial['mono_sum']['rms_loss_db']<-.5:raise ValidationError('mono loss')
 regions=[('intro-'+str(b),b*4*60/126,(b+4)*4*60/126) for b in range(0,16,4)]+[('anchor',16*4*60/126,32*4*60/126),('return',80*4*60/126,96*4*60/126)]
 performance={k:production_metrics(f,regions) for k,f in [('A',original),('B',out/RAW)]}
 report={'version':'phase26-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'raw_levels':levels,'matching':matched,'spatial':spatial,'performance':performance,'full_reset_anchor_PCM_exact':True,'native_state_PCM_reopen_exact':True,'human_preference':'unreviewed','mastering':False}
 write(out/'verification.json',report);write(out/'recipe.json',{'version':'phase26-replay-1','candidate_hash':state_hash(p),'source_hash':SOURCE_HASH,'raw_sha256':digest(out/RAW),'audition_sha256':digest(out/'listening'/LISTEN['B']),'audition_gain_db':matched['B']['gain_db'],'end_seconds':END})
 shutil.copytree(src/'licenses',out/'licenses')
 if inventory(src)!=before:raise ValidationError('source modified')
 print('Full144-bar A/B, exact anchor and native reload passed',flush=True)
def package(root):
 root=Path(root);target=root/'phase26-house-listening.zip'
 if target.exists():raise ValidationError('no clobber')
 shutil.copyfile(ROOT/'docs/PHASE26_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase26_reproduce.py',root/'reproduce.py')
 shutil.copytree(ROOT/'kuang',root/'reproduction/kuang',ignore=shutil.ignore_patterns('__pycache__'));shutil.copyfile(ROOT/'LICENSE',root/'reproduction/LICENSE')
 files=[p for p in root.rglob('*') if p.is_file() and p.name!=RAW and 'proof' not in p.relative_to(root).parts]
 manifest={str(p.relative_to(root)):digest(p) for p in files}
 with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED) as z:
  for f in files:z.write(f,f.relative_to(root))
  z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True))
 with zipfile.ZipFile(target) as z:
  if z.testzip() or any(hashlib.sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP corruption')
 return {'bytes':target.stat().st_size,'sha256':digest(target)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build','package']);ap.add_argument('--out-dir',required=True);ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--host-python');ap.add_argument('--meter');z=ap.parse_args();print(build(z.out_dir,z.soundcraft,z.plugin,z.host_python,z.meter) if z.action=='build' else package(z.out_dir))
