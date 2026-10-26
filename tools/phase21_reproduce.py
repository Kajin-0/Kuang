#!/usr/bin/env python3
"""Rebuild the live native melodic performance from portable reviewed sources."""
import argparse,json,shutil,sys,tempfile
from pathlib import Path
frozen=Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir():sys.path.insert(0,str(frozen))
from kuang.house_theme import compose_theme,SOURCE_HASH
from kuang.theme_audit import audit_theme,require_theme
from kuang.production_host import ProductionAdapter
from kuang.schema import load,state_hash,strict_json,ValidationError
from kuang.sample_assets import digest,inventory


def reproduce(root,destination,host,plugin,workspace):
 root=Path(root).resolve();workspace=Path(workspace).resolve();dest=Path(destination)
 if dest.exists() or dest.is_symlink() or not root.is_relative_to(workspace) or not dest.resolve().is_relative_to(workspace) or dest.resolve().is_relative_to(root):raise ValidationError('fresh workspace-local replay outside source required')
 r=strict_json((root/'recipe.json').read_text());keys={'version','source_hash','candidate_hash','raw_A_sha256','raw_B_sha256','end_seconds','composition_receipt_sha256','patch_manifest_sha256','asset_manifest_sha256'}
 if set(r)!=keys or r['version']!='phase21-replay-1' or r['end_seconds']!=160*4*60/126+5:raise ValidationError('strict Phase21 recipe required')
 source=load(root/'source/project.kuang.json');p,receipt=compose_theme(source);audit=audit_theme(source,p,receipt);require_theme(audit)
 if state_hash(source)!=SOURCE_HASH or r['source_hash']!=SOURCE_HASH or r['candidate_hash']!=state_hash(p) or state_hash(load(root/'B/project.kuang.json'))!=state_hash(p):raise ValidationError('composition source/candidate drift')
 if receipt!=strict_json((root/'composition-receipt.json').read_text()) or digest(root/'composition-receipt.json')!=r['composition_receipt_sha256']:raise ValidationError('composition receipt drift')
 assets={t.id:root/'B/native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
 patches={t.id:root/'B/native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')}
 if {t:digest(v/'manifest.json') for t,v in patches.items()}!=r['patch_manifest_sha256'] or {t:digest(v/'asset.json') for t,v in assets.items()}!=r['asset_manifest_sha256']:raise ValidationError('prepared sound identity drift')
 a=ProductionAdapter(host,plugin=plugin,workspace=workspace,scratch=workspace/'.local/phase21/tmp',center_pitch_bend=True);before=inventory(root)
 with tempfile.TemporaryDirectory(dir=a.scratch) as d:
  stage=Path(d)/'publish';stage.mkdir();a.export(p,assets,patches,stage/'native');a.render(stage/'native',stage/'B-reproduced-melodic-native.wav',end_seconds=r['end_seconds'])
  if digest(stage/'B-reproduced-melodic-native.wav')!=r['raw_B_sha256'] or inventory(root)!=before:raise ValidationError('replay PCM or source mismatch')
  dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
  try:
   for f in stage.iterdir():shutil.move(str(f),dest/f.name)
  except BaseException:shutil.rmtree(dest);raise
 return {'PCM_exact':True,'native_editable':True,'rhythm_section_exact':True,'mastering':False,'native':str(dest/'native/session.scraft'),'wav':str(dest/'B-reproduced-melodic-native.wav')}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',default=str(Path(__file__).resolve().parent));ap.add_argument('--out',required=True);ap.add_argument('--workspace',default=str(Path.cwd()));ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);z=ap.parse_args()
 print(json.dumps(reproduce(z.source,z.out,z.soundcraft,z.plugin,z.workspace),indent=2))
