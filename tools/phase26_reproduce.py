"""Reproduce the live Phase26 arrangement and scalar-matched audition."""
import argparse,json,sys,tempfile,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'reproduction'))
from kuang.groove_direction import compose_direction,audit_direction,SOURCE_HASH
from kuang.schema import load,state_hash,ValidationError
from kuang.sample_assets import digest,inventory
from kuang.master_bus import MasterBusAdapter
from kuang.mastering import attenuate

def replay(root,out,workspace,host,plugin):
 root=Path(root).resolve();out=Path(out).resolve();workspace=Path(workspace).resolve()
 if out.exists() or out.is_relative_to(root) or not out.is_relative_to(workspace) or not root.is_relative_to(workspace):raise ValidationError('fresh project-local output outside source required')
 r=json.loads((root/'recipe.json').read_text())
 if set(r)!={'version','candidate_hash','source_hash','raw_sha256','audition_sha256','audition_gain_db','end_seconds'} or r['version']!='phase26-replay-1' or r['source_hash']!=SOURCE_HASH or r['end_seconds']!=144*4*60/126+5 or not isinstance(r['audition_gain_db'],(int,float)) or not -60<=r['audition_gain_db']<=0:raise ValidationError('strict Phase26 recipe required')
 s=load(root/'phase25-source.kuang.json');p,j=compose_direction(s);audit_direction(s,p,j)
 if state_hash(p)!=r['candidate_hash'] or p!=load(root/'project/project.kuang.json') or j!=json.loads((root/'composition-receipt.json').read_text()):raise ValidationError('source/composition drift')
 assets={t.id:root/'project/native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'};patches={t.id:root/'project/native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')}
 a=MasterBusAdapter(host,plugin=plugin,workspace=workspace,scratch=workspace/'.local/phase26/tmp',center_pitch_bend=True);before=inventory(root)
 with tempfile.TemporaryDirectory(dir=a.scratch) as d:
  d=Path(d);a.export(p,assets,patches,d/'native');a.render(d/'native',d/'raw.wav',end_seconds=r['end_seconds'])
  if digest(d/'raw.wav')!=r['raw_sha256']:raise ValidationError('raw replay drift')
  attenuate(d/'raw.wav',d/'matched.wav',r['audition_gain_db'])
  if digest(d/'matched.wav')!=r['audition_sha256'] or inventory(root)!=before:raise ValidationError('matched/source drift')
  out.mkdir(parents=True)
  for f in d.iterdir():shutil.move(f,out/f.name)
 return {'raw_and_matched_PCM_exact':True,'native_editable':True}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True);ap.add_argument('--workspace',required=True);ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);z=ap.parse_args();print(json.dumps(replay(z.source,z.out,z.workspace,z.soundcraft,z.plugin)))
