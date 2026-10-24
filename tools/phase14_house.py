#!/usr/bin/env python3
"""Full-song authored ensemble and strict mixed-instrument production graph."""
import argparse
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.ensemble_production import build_ensemble,VOICES,isolate
from kuang.production_host import ProductionAdapter
from kuang.sampled_instrument import SampledInstrumentAdapter
from kuang.sample_assets import write,digest,inventory
from kuang.schema import load,save,state_hash,ValidationError,dumps
from kuang.midi import export_bytes
from kuang.mastering import match_lufs
from kuang.loudness import measure
from kuang.spatial_audio import spatial_metrics
from kuang.lowend_audio import band_metrics
from kuang.production_audio import production_metrics
from kuang.audio import compare_wavs

SOURCE_HASH='fe30aebffc6118ccebf4bdfb0884beb0bc2972e3b5f4a175bfd8d8dd4f9e4ca9'
END=64*4*60/126+5


def new_path(path):
    path=Path(path)
    if path.is_symlink() or path.exists():raise ValidationError('new Phase14 destination required')
    p=path.resolve()
    if not p.is_relative_to(ROOT/'.local/phase14'):raise ValidationError('stage Phase14 inside .local/phase14 before verified publication')
    return p


def adapter(executable,plugin):return ProductionAdapter(executable,plugin=plugin,workspace=ROOT)


def build(destination,source,patch_folder,plugin,executable,library=None):
    dest=new_path(destination);a=adapter(executable,plugin);source=a.local(source);patch_folder=a.local(patch_folder)
    if dest.is_relative_to(source) or dest.is_relative_to(patch_folder):raise ValidationError('production output intersects source')
    original=load(source/'project.kuang.json')
    if state_hash(original)!=SOURCE_HASH:raise ValidationError('exact Phase13 B full-song incumbent required')
    before=inventory(source);patch_before=inventory(patch_folder)
    patches={k:patch_folder/v for k,v in VOICES.items()};p,plan=build_ensemble(original,patches)
    assets={t.id:source/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
    legacy=SampledInstrumentAdapter(executable,workspace=ROOT);legacy.scratch=a.scratch
    if dumps(legacy.import_project(source/'native'))!=dumps(original):raise ValidationError('baseline canonical/native drift')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent,prefix='.build-') as directory:
        stage=Path(directory)/'publish';stage.mkdir();(stage/'A').mkdir();(stage/'B').mkdir()
        legacy.save(source/'native',stage/'A/native');save(original,stage/'A/project.kuang.json')
        (stage/'A/song.mid').write_bytes(export_bytes(original))
        legacy.render(stage/'A/native',stage/'A-Phase13-original-native.wav',end_seconds=END)
        if digest(stage/'A-Phase13-original-native.wav')!=digest(source.parent/'B-phase13-drum-palette-native.wav'):
            raise ValidationError('baseline PCM no longer identical')
        a.export(p,assets,patches,stage/'B/native');save(p,stage/'B/project.kuang.json');(stage/'B/song.mid').write_bytes(export_bytes(p))
        for label in ('A','B'):write(stage/label/'source-song-spec.json',json.loads(original.metadata['song_spec']))
        a.render(stage/'B/native',stage/'B-Phase14-ensemble-native.wav',end_seconds=END)
        levels={k:measure(stage/name,library=library) for k,name in [('A','A-Phase13-original-native.wav'),('B','B-Phase14-ensemble-native.wav')]}
        if any(m['clipped_samples'] or m['true_peak_dbtp']> -1 for m in levels.values()):raise ValidationError('production headroom failure')
        (stage/'listening').mkdir();target=min(m['integrated_lufs'] for m in levels.values())
        matches={k:match_lufs(stage/name,stage/'listening'/(k+'-'+('Phase13-original' if k=='A' else 'Phase14-ensemble')+'-full-LUFS-matched.wav'),target,library=library)
                 for k,name in [('A','A-Phase13-original-native.wav'),('B','B-Phase14-ensemble-native.wav')]}
        regions=[(s.name,s.start/p.ppq*60/p.tempo_bpm,(s.start+s.length)/p.ppq*60/p.tempo_bpm) for s in p.sections]
        report={'version':'phase14-verification-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),
            'source_baseline_PCM_exact':True,'canonical_schema':'0.1','note_count_A':1536,'note_count_B':1544,
            'levels':levels,'level_matching':matches,'full_mix_difference':compare_wavs(stage/'A-Phase13-original-native.wav',stage/'B-Phase14-ensemble-native.wav'),
            'spatial':{k:spatial_metrics(stage/name) for k,name in [('A','A-Phase13-original-native.wav'),('B','B-Phase14-ensemble-native.wav')]},
            'drop_bands':{k:band_metrics(stage/name,first=32*4*60/126,last=40*4*60/126,windows=16) for k,name in [('A','A-Phase13-original-native.wav'),('B','B-Phase14-ensemble-native.wav')]},
            'sections':{k:production_metrics(stage/name,regions)['sections'] for k,name in [('A','A-Phase13-original-native.wav'),('B','B-Phase14-ensemble-native.wav')]},
            'human_preference':'unreviewed','professional_quality_established':False,'mastering':'none; raw native mixes and constant-attenuation listening copies only'}
        write(stage/'production.json',plan);write(stage/'verification.json',report)
        write(stage/'recipe.json',{'version':'phase14-recipe-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),
            'raw_A_sha256':digest(stage/'A-Phase13-original-native.wav'),'raw_B_sha256':digest(stage/'B-Phase14-ensemble-native.wav'),
            'render_end_seconds':END,'host':a.capabilities(),'patches':{k:digest(v/'manifest.json') for k,v in patches.items()}})
        shutil.copytree(source.parent/'licenses',stage/'licenses')
        shutil.copyfile(ROOT/'LICENSE',stage/'licenses/Kuang-MIT.txt')
        write(stage/'licenses/external-components.json',{'not_bundled':{'DISTRHO Vitalium 1.0.6':'GPL-3.0-or-later; https://github.com/DISTRHO/DISTRHO-Ports/tree/2021-03-15/ports/vitalium',
            'SoundCraft 0.11.0':'MIT OR Apache-2.0; https://github.com/storytold/soundcraft/releases/tag/v0.11.0',
            'Pedalboard 0.9.26':'GPL-3.0; optional original-patch preparation only; https://github.com/spotify/pedalboard'},
            'bundled_content':'Original Kuang Fourier wavetables, patches and code MIT; six inherited original octal samples CC0 with per-file provenance. No factory preset/plugin binary/reference recording.'})
        prepare_download(stage)
        if inventory(source)!=before or inventory(patch_folder)!=patch_before:raise ValidationError('production source/patch drift')
        dest.mkdir()
        try:
            for item in stage.iterdir():shutil.move(str(item),dest/item.name)
        except BaseException:shutil.rmtree(dest);raise
    return report


def prepare_download(root):
    """Own MIT replay code plus clear listening instructions, no binaries."""
    root=Path(root)
    if any((root/name).exists() for name in ('README.md','reproduce.py','reproduction')):raise ValidationError('download recipe already exists')
    shutil.copyfile(ROOT/'docs/PHASE14_LISTENING_README.md',root/'README.md')
    shutil.copyfile(ROOT/'tools/phase14_reproduce.py',root/'reproduce.py')
    frozen=root/'reproduction';(frozen/'kuang').mkdir(parents=True)
    for path in (ROOT/'kuang').rglob('*'):
        if path.is_file() and path.suffix in ('.py','.lua','.json'):
            if path.is_symlink():raise ValidationError('replay source symlink unsupported')
            target=frozen/'kuang'/path.relative_to(ROOT/'kuang');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    shutil.copyfile(ROOT/'LICENSE',frozen/'LICENSE');write(frozen/'source-manifest.json',inventory(frozen))


def package(root):
    root=Path(root);out=root/'phase14-house-listening.zip'
    if out.exists() or out.is_symlink():raise ValidationError('new Phase14 listening ZIP required')
    selected=[]
    for folder in ('A','B','listening','licenses','reproduction'):
        selected.extend(p for p in (root/folder).rglob('*') if p.is_file())
    selected.extend(root/name for name in ('README.md','recipe.json','reproduce.py','production.json','verification.json'))
    if any(p.is_symlink() for p in selected):raise ValidationError('ZIP symlinks unsupported')
    expected={str(p.relative_to(root)):digest(p) for p in selected}
    with tempfile.TemporaryDirectory(dir=root,prefix='.zip-') as d:
        zpath=Path(d)/'listening.zip'
        with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(selected):z.write(p,str(p.relative_to(root)))
            z.writestr('zip-manifest.json',json.dumps(expected,sort_keys=True,indent=2)+'\n')
        with zipfile.ZipFile(zpath) as z:
            if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in expected.items()):raise ValidationError('ZIP integrity failure')
        if zpath.stat().st_size>180_000_000:raise ValidationError('listening ZIP exceeds 180MB budget')
        os.link(zpath,out)
    return {'bytes':out.stat().st_size,'sha256':digest(out),'human_preference':'unreviewed'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','package'))
    ap.add_argument('--out-dir',required=True);ap.add_argument('--source',default=str(ROOT/'artifacts/phase13-house/B'))
    ap.add_argument('--patches');ap.add_argument('--plugin');ap.add_argument('--soundcraft');ap.add_argument('--meter-library')
    args=ap.parse_args()
    if args.action=='package':result=package(args.out_dir)
    else:
        if not all((args.patches,args.plugin,args.soundcraft)):ap.error('build requires explicit --patches, --plugin, --soundcraft')
        result=build(args.out_dir,args.source,args.patches,args.plugin,args.soundcraft,args.meter_library)
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__':main()
