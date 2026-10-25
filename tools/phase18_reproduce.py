#!/usr/bin/env python3
"""Recompose and render the portable Phase18 live native record, no downloads."""
import argparse,json,shutil,sys,tempfile
from pathlib import Path
frozen=Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir():sys.path.insert(0,str(frozen))
from kuang.house_composition import compose_record,SOURCE_HASH
from kuang.composition_analysis import audit_composition
from kuang.production_host import ProductionAdapter
from kuang.schema import load,state_hash,strict_json,ValidationError
from kuang.sample_assets import digest,inventory

def reproduce(root,destination,host,plugin,workspace):
 root=Path(root).resolve();workspace=Path(workspace).resolve();dest=Path(destination)
 if dest.exists() or dest.is_symlink() or not root.is_relative_to(workspace) or not dest.resolve().is_relative_to(workspace):raise ValidationError('new workspace-local replay destination required')
 r=strict_json((root/'recipe.json').read_text())
 if set(r)!={'version','source_hash','candidate_hash','raw_A_sha256','raw_B_sha256','end_seconds','patch_manifest_sha256','composition_receipt_sha256'} or r['version']!='phase18-replay-1':raise ValidationError('strict Phase18 replay recipe required')
 old=load(root/'source/phase17-approved.kuang.json');p,receipt=compose_record(old)
 if state_hash(old)!=SOURCE_HASH or r['source_hash']!=SOURCE_HASH or state_hash(p)!=r['candidate_hash'] or state_hash(load(root/'B/project.kuang.json'))!=r['candidate_hash']:raise ValidationError('composition source/candidate drift')
 if receipt!=strict_json((root/'composition-receipt.json').read_text()) or digest(root/'composition-receipt.json')!=r['composition_receipt_sha256']:raise ValidationError('composition provenance drift')
 a=ProductionAdapter(host,plugin=plugin,workspace=workspace,scratch=workspace/'.local/phase18/tmp',center_pitch_bend=True);before=inventory(root)
 assets={t.id:root/'B/native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
 patches={t.id:root/'B/native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')}
 if {t:digest(v/'manifest.json') for t,v in patches.items()}!=r['patch_manifest_sha256']:raise ValidationError('approved patch identity drift')
 with tempfile.TemporaryDirectory(dir=a.scratch) as d:
  stage=Path(d)/'publish';stage.mkdir();a.export(p,assets,patches,stage/'native');a.render(stage/'native',stage/'B-reproduced.wav',end_seconds=r['end_seconds'])
  if digest(stage/'B-reproduced.wav')!=r['raw_B_sha256'] or inventory(root)!=before:raise ValidationError('replayed PCM/source mismatch')
  dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
  try:
   for f in stage.iterdir():shutil.move(str(f),dest/f.name)
  except BaseException:shutil.rmtree(dest);raise
 return {'PCM_exact':True,'native':str(dest/'native/session.scraft'),'wav':str(dest/'B-reproduced.wav')}
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',default=str(Path(__file__).resolve().parent));ap.add_argument('--out',required=True);ap.add_argument('--workspace',default=str(Path.cwd()));ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);z=ap.parse_args()
 print(json.dumps(reproduce(z.source,z.out,z.soundcraft,z.plugin,z.workspace),indent=2))
