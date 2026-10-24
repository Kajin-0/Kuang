#!/usr/bin/env python3
"""Reproduce the live Phase13 candidate from the extracted portable assets.

Requires the MIT Kuang checkout/wheel and separately installed SoundCraft.
No download, sample conversion, library path or plugin binary is needed.
"""
import argparse
import json
import shutil
import tempfile
import sys
from pathlib import Path

# The listening ZIP carries only Kuang's own MIT source, never host/plugin
# binaries. This makes its actual downloaded recipe runnable with python -I.
frozen=Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir():sys.path.insert(0,str(frozen))

from kuang.record_palette import sampled_house
from kuang.sample_assets import digest
from kuang.sampled_instrument import SampledInstrumentAdapter
from kuang.schema import ValidationError,load,state_hash,strict_json


def reproduce(root,destination,executable,workspace):
    root,destination,workspace=map(lambda p:Path(p).resolve(),(root,destination,workspace))
    if not root.is_relative_to(workspace) or not destination.is_relative_to(workspace) or destination.exists():
        raise ValidationError('new reproduction destination within explicit workspace required')
    r=strict_json((root/'recipe.json').read_text())
    if type(r) is not dict or set(r)!={'version','source_hash','candidate_hash','source','levels','assets','original_sources','native_pcm_sha256','render_end_seconds','hidden_postprocessing','mastering'}:
        raise ValidationError('exact versioned reproduction recipe required')
    source_path=(root/r['source']).resolve()
    if not source_path.is_relative_to(root):raise ValidationError('unsafe reproduction source path')
    source=load(source_path)
    if r['version']!='phase13-palette-1' or state_hash(source)!=r['source_hash']:
        raise ValidationError('reproduction source/recipe identity differs')
    assets={tid:root/name for tid,name in r['assets'].items()}
    if any(not p.resolve().is_relative_to(root) for p in assets.values()):raise ValidationError('unsafe reproduction asset path')
    candidate,_=sampled_house(source,assets,r['levels'])
    if state_hash(candidate)!=r['candidate_hash']:raise ValidationError('reproduction candidate identity differs')
    a=SampledInstrumentAdapter(executable,workspace=workspace);a.scratch=workspace/'.local/phase13/tmp';a.scratch.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.scratch,prefix='replay-') as d:
        stage=Path(d)/'publish';stage.mkdir()
        a.export(candidate,assets,stage/'native')
        a.render(stage/'native',stage/'B-reproduced.wav',end_seconds=r['render_end_seconds'])
        if digest(stage/'B-reproduced.wav')!=r['native_pcm_sha256']:raise ValidationError('reproduced full PCM differs')
        destination.parent.mkdir(parents=True,exist_ok=True);destination.mkdir()
        try:
            for p in stage.iterdir():shutil.move(str(p),destination/p.name)
        except BaseException:shutil.rmtree(destination);raise
    return {'native':str(destination/'native/session.scraft'),'wav':str(destination/'B-reproduced.wav'),'PCM_exact':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',default=str(Path(__file__).resolve().parent))
    p.add_argument('--out',required=True);p.add_argument('--soundcraft',required=True);p.add_argument('--workspace',default=str(Path.cwd()))
    a=p.parse_args();print(json.dumps(reproduce(a.source,a.out,a.soundcraft,a.workspace),indent=2))
