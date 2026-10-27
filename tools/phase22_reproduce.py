#!/usr/bin/env python3
"""Portable frozen replay of the four editable16-bar compositions."""
import argparse,json,shutil,sys,tempfile
from pathlib import Path
frozen=Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir():sys.path.insert(0,str(frozen))
from kuang.house_shortlist import compose_candidate,SOURCE_HASH,REFERENCE_HASH
from kuang.shortlist_audit import audit_shortlist,require_shortlist
from kuang.master_bus import MasterBusAdapter
from kuang.schema import load,strict_json,state_hash,ValidationError
from kuang.sample_assets import digest,inventory

def reproduce(root,destination,host,plugin,workspace):
 if Path(destination).is_symlink() or Path(root).is_symlink():raise ValidationError('symlink replay source/destination prohibited')
 root=Path(root).resolve();workspace=Path(workspace).resolve();dest=Path(destination).resolve()
 if dest.exists() or dest.is_relative_to(root) or not root.is_relative_to(workspace) or not dest.is_relative_to(workspace):raise ValidationError('fresh workspace-local replay outside source required')
 r=strict_json((root/'recipe.json').read_text())
 if set(r)!={'version','source_hash','reference_hash','end_seconds','projects','asset_manifests','patch_manifests'} or r['version']!='phase22-replay-1' or r['source_hash']!=SOURCE_HASH or r['reference_hash']!=REFERENCE_HASH or r['end_seconds']!=16*4*60/126+5 or set(r['projects'])!=set('ABCD'):raise ValidationError('strict16-bar shortlist recipe required')
 source=load(root/'A/project.kuang.json')
 if state_hash(source)!=REFERENCE_HASH:raise ValidationError('reference drift')
 projects={'A':source}
 for label,kind in [('B','soulful'),('C','progressive'),('D','hypnotic')]:
  p,receipt=compose_candidate(source,kind);require_shortlist(audit_shortlist(source,p,receipt));projects[label]=p
  if receipt!=strict_json((root/label/'composition-receipt.json').read_text()) or digest(root/label/'composition-receipt.json')!=r['projects'][label]['receipt_sha256']:raise ValidationError('composition lineage drift')
 for label,p in projects.items():
  if set(r['projects'][label])!={'hash','raw_sha256','receipt_sha256'} or state_hash(p)!=r['projects'][label]['hash'] or state_hash(load(root/label/'project.kuang.json'))!=state_hash(p):raise ValidationError('candidate score drift')
 assets={t.id:root/'A/native/assets'/t.id for t in source.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
 patches={t.id:root/'A/native/patches'/t.id for t in source.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')}
 if {k:digest(v/'asset.json') for k,v in assets.items()}!=r['asset_manifests'] or {k:digest(v/'manifest.json') for k,v in patches.items()}!=r['patch_manifests']:raise ValidationError('prepared media drift')
 a=MasterBusAdapter(host,plugin=plugin,workspace=workspace,scratch=workspace/'.local/phase22/tmp',center_pitch_bend=True);before=inventory(root)
 with tempfile.TemporaryDirectory(dir=a.scratch) as d:
  stage=Path(d)/'publish';stage.mkdir()
  for label,p in projects.items():
   a.export(p,assets,patches,stage/label/'native');wav=stage/(label+'-reproduced.wav');a.render(stage/label/'native',wav,end_seconds=r['end_seconds'])
   if digest(wav)!=r['projects'][label]['raw_sha256']:raise ValidationError('replay PCM mismatch '+label)
  if inventory(root)!=before:raise ValidationError('replay source changed')
  dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
  try:
   for p in stage.iterdir():shutil.move(str(p),dest/p.name)
  except BaseException:shutil.rmtree(dest);raise
 return {'all_four_PCM_exact':True,'native_editable':True,'new_full_song':False,'mastering':False,'human_preference':'unreviewed'}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',default=str(Path(__file__).resolve().parent));ap.add_argument('--out',required=True);ap.add_argument('--workspace',default=str(Path.cwd()));ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);z=ap.parse_args()
 print(json.dumps(reproduce(z.source,z.out,z.soundcraft,z.plugin,z.workspace),indent=2))
