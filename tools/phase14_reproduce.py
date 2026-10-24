#!/usr/bin/env python3
"""Rebuild editable Phase14 graph and exact native PCM from portable originals.

Requires separately installed reviewed SoundCraft, Vitalium and bubblewrap.
No plugin binary, factory content, converter, external source library or
Pedalboard is needed to replay these original prepared presets.
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
frozen=Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir():sys.path.insert(0,str(frozen))
from kuang.production_host import ProductionAdapter
from kuang.ensemble_production import build_ensemble,VOICES
from kuang.sample_assets import digest,inventory
from kuang.schema import ValidationError,load,state_hash,strict_json


def reproduce(root,destination,executable,plugin,workspace):
    workspace=Path(workspace).resolve();root=Path(root).resolve();dest=Path(destination)
    if dest.exists() or dest.is_symlink() or not root.is_relative_to(workspace) or not dest.resolve().is_relative_to(workspace):
        raise ValidationError('new reproduction destination inside explicit workspace required')
    dest=dest.resolve();r=strict_json((root/'recipe.json').read_text())
    if type(r) is not dict or set(r)!={'version','source_hash','candidate_hash','raw_A_sha256','raw_B_sha256','render_end_seconds','host','patches'} or r['version']!='phase14-recipe-1':
        raise ValidationError('exact Phase14 recipe required')
    a=ProductionAdapter(executable,plugin=plugin,workspace=workspace)
    if a.capabilities()!=r['host']:raise ValidationError('reproduction host/plugin capability drift')
    original=load(root/'A/project.kuang.json');expected=load(root/'B/project.kuang.json')
    patches={tid:root/'B/native/patches'/tid for tid in VOICES}
    if state_hash(original)!=r['source_hash'] or any(digest(path/'manifest.json')!=r['patches'][tid] for tid,path in patches.items()):
        raise ValidationError('reproduction source/patch identity differs')
    p,_=build_ensemble(original,patches)
    if state_hash(p)!=r['candidate_hash'] or state_hash(expected)!=state_hash(p):raise ValidationError('reproduction proposal differs')
    assets={t.id:root/'B/native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
    before=inventory(root)
    with tempfile.TemporaryDirectory(dir=a.scratch,prefix='reproduce-') as d:
        stage=Path(d)/'publish';stage.mkdir();a.export(p,assets,patches,stage/'native')
        a.render(stage/'native',stage/'B-reproduced.wav',end_seconds=r['render_end_seconds'])
        if digest(stage/'B-reproduced.wav')!=r['raw_B_sha256'] or inventory(root)!=before:raise ValidationError('reproduced PCM/source differs')
        dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
        try:
            for item in stage.iterdir():shutil.move(str(item),dest/item.name)
        except BaseException:shutil.rmtree(dest);raise
    return {'PCM_exact':True,'native':str(dest/'native/session.scraft'),'wav':str(dest/'B-reproduced.wav')}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',default=str(Path(__file__).resolve().parent))
    ap.add_argument('--out',required=True);ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);ap.add_argument('--workspace',default=str(Path.cwd()))
    args=ap.parse_args();print(json.dumps(reproduce(args.source,args.out,args.soundcraft,args.plugin,args.workspace),indent=2))
