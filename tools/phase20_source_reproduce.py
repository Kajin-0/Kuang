#!/usr/bin/env python3
"""Reproduce the portable live source-production mix, no downloads/mastering."""
import argparse,json,shutil,sys,tempfile
from pathlib import Path
frozen=Path(__file__).resolve().parent/'reproduction'
if (frozen/'kuang').is_dir():sys.path.insert(0,str(frozen))
from kuang.source_production import source_record
from kuang.record_mix import SOURCE_HASH
from kuang.production_host import ProductionAdapter
from kuang.schema import load,state_hash,strict_json,ValidationError
from kuang.sample_assets import digest,inventory


def reproduce(root,destination,host,plugin,workspace):
    root=Path(root).resolve();workspace=Path(workspace).resolve();dest=Path(destination)
    if dest.exists() or dest.is_symlink() or not root.is_relative_to(workspace) or not dest.resolve().is_relative_to(workspace) or dest.resolve().is_relative_to(root):
        raise ValidationError('new workspace-local replay destination outside the source required')
    r=strict_json((root/'recipe.json').read_text())
    expected={'version','source_hash','candidate_hash','raw_A_sha256','raw_B_sha256','end_seconds','production_receipt_sha256','changed_patch_tracks','changed_sample_tracks','patch_manifest_sha256','asset_manifest_sha256'}
    if set(r)!=expected or r['version']!='phase20-source-replay-1' or r['changed_patch_tracks']!=['track-harmony','track-lead'] or r['changed_sample_tracks']!=['track-kick'] or r['end_seconds']!=160*4*60/126+5:
        raise ValidationError('strict selected source-production recipe required')
    old=load(root/'source/project.kuang.json');candidate=load(root/'B/project.kuang.json')
    patches={t.id:root/'B/native/patches'/t.id for t in candidate.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')}
    assets={t.id:root/'B/native/assets'/t.id for t in candidate.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
    if {tid:digest(path/'manifest.json') for tid,path in patches.items()}!=r['patch_manifest_sha256'] or {tid:digest(path/'asset.json') for tid,path in assets.items()}!=r['asset_manifest_sha256']:
        raise ValidationError('portable patch/sample identity drift')
    p,receipt=source_record(old,{t:patches[t] for t in r['changed_patch_tracks']},kick=assets['track-kick'])
    if state_hash(old)!=SOURCE_HASH or r['source_hash']!=SOURCE_HASH or state_hash(p)!=r['candidate_hash'] or state_hash(candidate)!=r['candidate_hash']:
        raise ValidationError('source/candidate drift')
    if receipt!=strict_json((root/'B/production.json').read_text()) or digest(root/'B/production.json')!=r['production_receipt_sha256']:
        raise ValidationError('source-production provenance drift')
    a=ProductionAdapter(host,plugin=plugin,workspace=workspace,scratch=workspace/'.local/phase20/tmp',center_pitch_bend=True);before=inventory(root)
    with tempfile.TemporaryDirectory(dir=a.scratch) as d:
        stage=Path(d)/'publish';stage.mkdir();a.export(p,assets,patches,stage/'native');a.render(stage/'native',stage/'B-reproduced-source-native.wav',end_seconds=r['end_seconds'])
        if digest(stage/'B-reproduced-source-native.wav')!=r['raw_B_sha256'] or inventory(root)!=before:
            raise ValidationError('replayed source PCM/source mismatch')
        dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
        try:
            for f in stage.iterdir():shutil.move(str(f),dest/f.name)
        except BaseException:shutil.rmtree(dest);raise
    return {'PCM_exact':True,'live_instruments_and_native_FX_editable':True,'mastering':False,'native':str(dest/'native/session.scraft'),'wav':str(dest/'B-reproduced-source-native.wav')}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',default=str(Path(__file__).resolve().parent));ap.add_argument('--out',required=True);ap.add_argument('--workspace',default=str(Path.cwd()));ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);z=ap.parse_args()
    print(json.dumps(reproduce(z.source,z.out,z.soundcraft,z.plugin,z.workspace),indent=2))
