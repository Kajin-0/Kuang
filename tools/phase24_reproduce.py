#!/usr/bin/env python3
"""Reproduce ONE approved-source record from frozen MIT code and live media."""
import argparse,json,shutil,sys,tempfile
from pathlib import Path
frozen=Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir():sys.path.insert(0,str(frozen))
from kuang.groove_record import arrange_groove,audit_record,SOURCE_HASH
from kuang.schema import load,state_hash,strict_json,ValidationError
from kuang.master_bus import MasterBusAdapter
from kuang.sample_assets import digest,inventory

def reproduce(root,out,host,plugin,workspace):
 if Path(root).is_symlink() or Path(out).is_symlink():raise ValidationError('symlink source/destination forbidden')
 root=Path(root).resolve();out=Path(out).resolve();workspace=Path(workspace).resolve()
 if out.exists() or out.is_relative_to(root) or not root.is_relative_to(workspace) or not out.is_relative_to(workspace):raise ValidationError('new workspace-local output outside source required')
 r=strict_json((root/'recipe.json').read_text())
 if set(r)!={'version','source_hash','candidate_hash','end_seconds','raw_sha256','receipt_sha256','patches','assets'} or r['version']!='phase24-replay-1' or r['source_hash']!=SOURCE_HASH or r['end_seconds']!=144*4*60/126+5:raise ValidationError('strict one-record recipe required')
 s=load(root/'approved-source.kuang.json');p,receipt=arrange_groove(s);audit_record(s,p,receipt)
 if state_hash(p)!=r['candidate_hash'] or p!=load(root/'project/project.kuang.json') or receipt!=strict_json((root/'composition-receipt.json').read_text()) or digest(root/'composition-receipt.json')!=r['receipt_sha256']:raise ValidationError('score/receipt drift')
 assets={t.id:root/'project/native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
 patches={t.id:root/'project/native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')}
 if {k:digest(v/'asset.json') for k,v in assets.items()}!=r['assets'] or {k:digest(v/'manifest.json') for k,v in patches.items()}!=r['patches']:raise ValidationError('media drift')
 a=MasterBusAdapter(host,plugin=plugin,workspace=workspace,scratch=workspace/'.local/phase24/tmp',center_pitch_bend=True);before=inventory(root)
 with tempfile.TemporaryDirectory(dir=a.scratch) as d:
  d=Path(d);a.export(p,assets,patches,d/'native');a.render(d/'native',d/'Phase24-reproduced.wav',end_seconds=r['end_seconds'])
  if digest(d/'Phase24-reproduced.wav')!=r['raw_sha256'] or inventory(root)!=before:raise ValidationError('replay PCM/source changed')
  out.parent.mkdir(parents=True,exist_ok=True);out.mkdir()
  try:
   for f in d.iterdir():shutil.move(str(f),out/f.name)
  except BaseException:shutil.rmtree(out);raise
 return {'PCM_exact':True,'native_editable':True,'bars':144,'lead_and_arp_absent':True,'single_candidate':True,'human_preference':'unreviewed'}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',default=str(Path(__file__).resolve().parent));ap.add_argument('--out',required=True);ap.add_argument('--workspace',default=str(Path.cwd()));ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);z=ap.parse_args();print(json.dumps(reproduce(z.source,z.out,z.soundcraft,z.plugin,z.workspace),indent=2))
