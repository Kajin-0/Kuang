#!/usr/bin/env python3
"""Portable Phase15 replay: SoundCraft only, original MIDI/built-ins/samplers."""
import argparse,json,shutil,sys,tempfile
from pathlib import Path
frozen=Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir():sys.path.insert(0,str(frozen))
from kuang.production_host import ProductionAdapter
from kuang.musical_repair import repaired_house
from kuang.schema import load,state_hash,ValidationError,strict_json
from kuang.sample_assets import digest,inventory

def reproduce(root,destination,executable,workspace):
    root=Path(root).resolve();workspace=Path(workspace).resolve();destination=Path(destination)
    if destination.exists() or destination.is_symlink() or not root.is_relative_to(workspace) or not destination.resolve().is_relative_to(workspace):raise ValidationError('new replay destination inside explicit workspace required')
    r=strict_json((root/'recipe.json').read_text())
    if set(r)!={'version','source_hash','candidate_hash','raw_B_sha256','end_seconds'} or r['version']!='phase15-replay-1':raise ValidationError('strict repair recipe required')
    old=load(root/'A/project.kuang.json');p,_=repaired_house(old)
    if state_hash(old)!=r['source_hash'] or state_hash(p)!=r['candidate_hash']:raise ValidationError('repair source/candidate drift')
    a=ProductionAdapter(executable,workspace=workspace,scratch=workspace/'.local/phase15/tmp')
    assets={t.id:root/'B/native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'};before=inventory(root)
    with tempfile.TemporaryDirectory(dir=a.scratch) as d:
        stage=Path(d)/'publish';stage.mkdir();a.export(p,assets,{},stage/'native');a.render(stage/'native',stage/'B-reproduced.wav',end_seconds=r['end_seconds'])
        if digest(stage/'B-reproduced.wav')!=r['raw_B_sha256'] or inventory(root)!=before:raise ValidationError('replayed PCM/source differs')
        destination.parent.mkdir(parents=True,exist_ok=True);destination.mkdir()
        try:
            for item in stage.iterdir():shutil.move(str(item),destination/item.name)
        except BaseException:shutil.rmtree(destination);raise
    return {'PCM_exact':True,'native':str(destination/'native/session.scraft'),'wav':str(destination/'B-reproduced.wav')}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',default=str(Path(__file__).resolve().parent));ap.add_argument('--out',required=True);ap.add_argument('--workspace',default=str(Path.cwd()));ap.add_argument('--soundcraft',required=True);a=ap.parse_args();print(json.dumps(reproduce(a.source,a.out,a.soundcraft,a.workspace),indent=2))
