#!/usr/bin/env python3
"""Reproduce the portable live native Phase20 master, no downloads."""
import argparse,json,shutil,sys,tempfile
from pathlib import Path
frozen=Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir():sys.path.insert(0,str(frozen))
from kuang.record_mix import mixed_record,SOURCE_HASH
from kuang.master_bus import MasterBusAdapter
from kuang.schema import load,state_hash,strict_json,ValidationError
from kuang.sample_assets import digest,inventory


def reproduce(root,destination,host,plugin,workspace):
    root=Path(root).resolve();workspace=Path(workspace).resolve();dest=Path(destination)
    if dest.exists() or dest.is_symlink() or not root.is_relative_to(workspace) or not dest.resolve().is_relative_to(workspace) or dest.resolve().is_relative_to(root):raise ValidationError('new workspace-local replay destination outside the source required')
    r=strict_json((root/'recipe.json').read_text())
    if set(r)!={'version','source_hash','candidate_hash','premaster_hash','raw_A_sha256','raw_B_sha256','end_seconds','production_receipt_sha256','patch_manifest_sha256'} or r['version']!='phase20-replay-1':raise ValidationError('strict Phase20 replay recipe required')
    old=load(root/'source/phase19-reference.kuang.json');p,receipt=mixed_record(old);pre,_=mixed_record(old,master=False)
    if state_hash(old)!=SOURCE_HASH or r['source_hash']!=SOURCE_HASH or state_hash(p)!=r['candidate_hash'] or state_hash(pre)!=r['premaster_hash'] or state_hash(load(root/'B/project.kuang.json'))!=r['candidate_hash']:raise ValidationError('mix source/candidate drift')
    if receipt!=strict_json((root/'B/production.json').read_text()) or digest(root/'B/production.json')!=r['production_receipt_sha256']:raise ValidationError('mix provenance drift')
    a=MasterBusAdapter(host,plugin=plugin,workspace=workspace,scratch=workspace/'.local/phase20/tmp',center_pitch_bend=True);before=inventory(root)
    assets={t.id:root/'B/native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
    patches={t.id:root/'B/native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')}
    if {tid:digest(path/'manifest.json') for tid,path in patches.items()}!=r['patch_manifest_sha256']:raise ValidationError('immutable patch identity drift')
    with tempfile.TemporaryDirectory(dir=a.scratch) as d:
        stage=Path(d)/'publish';stage.mkdir();a.export(p,assets,patches,stage/'native');a.render(stage/'native',stage/'B-reproduced-native-master.wav',end_seconds=r['end_seconds'])
        if digest(stage/'B-reproduced-native-master.wav')!=r['raw_B_sha256'] or inventory(root)!=before:raise ValidationError('replayed PCM/source mismatch')
        dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
        try:
            for f in stage.iterdir():shutil.move(str(f),dest/f.name)
        except BaseException:shutil.rmtree(dest);raise
    return {'PCM_exact':True,'native_master_editable':True,'native':str(dest/'native/session.scraft'),'wav':str(dest/'B-reproduced-native-master.wav')}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',default=str(Path(__file__).resolve().parent));ap.add_argument('--out',required=True);ap.add_argument('--workspace',default=str(Path.cwd()));ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);z=ap.parse_args()
    print(json.dumps(reproduce(z.source,z.out,z.soundcraft,z.plugin,z.workspace),indent=2))
