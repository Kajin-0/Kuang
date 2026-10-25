#!/usr/bin/env python3
"""Portable pitch-centered native replay, explicit separately installed Vitalium.

No network, independent host, factory content or external sample library needed.
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
frozen = Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir(): sys.path.insert(0,str(frozen))
from kuang.production_host import ProductionAdapter
from kuang.sound_palette import sound_palette, SOURCE_HASH
from kuang.studio_palette import TRACKS
from kuang.schema import load, state_hash, strict_json, ValidationError
from kuang.sample_assets import digest, inventory


def reproduce(root, destination, executable, plugin, workspace):
    root = Path(root).resolve(); workspace = Path(workspace).resolve(); destination = Path(destination)
    if destination.exists() or destination.is_symlink() or not root.is_relative_to(workspace) or not destination.resolve().is_relative_to(workspace):
        raise ValidationError('new replay destination inside explicit workspace required')
    recipe = strict_json((root/'recipe.json').read_text())
    if set(recipe) != {'version','source_hash','candidate_hash','raw_A_sha256','raw_B_sha256','end_seconds','patch_manifest_sha256'} or recipe['version'] != 'phase16-replay-1':
        raise ValidationError('strict sound-palette replay recipe required')
    old = load(root/'A/project.kuang.json')
    patches = {t:root/'B/native/patches'/t for t in TRACKS}
    if recipe['source_hash'] != SOURCE_HASH or state_hash(old) != SOURCE_HASH or {t:digest(p/'manifest.json') for t,p in patches.items()} != recipe['patch_manifest_sha256']:
        raise ValidationError('source/patch recipe drift')
    p, _ = sound_palette(old,patches)
    if state_hash(p) != recipe['candidate_hash'] or state_hash(load(root/'B/project.kuang.json')) != recipe['candidate_hash']:
        raise ValidationError('candidate drift')
    a = ProductionAdapter(executable,plugin=plugin,workspace=workspace,scratch=workspace/'.local/phase16/tmp',center_pitch_bend=True)
    assets = {t.id:root/'B/native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref == 'soundcraft:sampler'}
    before = inventory(root)
    with tempfile.TemporaryDirectory(dir=a.scratch) as d:
        stage = Path(d)/'publish';stage.mkdir()
        a.export(p,assets,patches,stage/'native');a.render(stage/'native',stage/'B-reproduced.wav',end_seconds=recipe['end_seconds'])
        if digest(stage/'B-reproduced.wav') != recipe['raw_B_sha256'] or inventory(root) != before:
            raise ValidationError('replayed PCM or source differs')
        destination.parent.mkdir(parents=True,exist_ok=True);destination.mkdir()
        try:
            for item in stage.iterdir():shutil.move(str(item),destination/item.name)
        except BaseException:shutil.rmtree(destination);raise
    return {'PCM_exact':True,'native':str(destination/'native/session.scraft'),'wav':str(destination/'B-reproduced.wav')}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',default=str(Path(__file__).resolve().parent));ap.add_argument('--out',required=True)
    ap.add_argument('--workspace',default=str(Path.cwd()));ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True)
    z = ap.parse_args();print(json.dumps(reproduce(z.source,z.out,z.soundcraft,z.plugin,z.workspace),indent=2))
