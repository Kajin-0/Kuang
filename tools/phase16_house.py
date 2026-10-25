#!/usr/bin/env python3
"""Pitch-correct sound-only full-song experiment; no arrangement changes."""
import argparse
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kuang.sound_palette import sound_palette, SOURCE_HASH, performance
from kuang.studio_palette import TRACKS
from kuang.production_host import ProductionAdapter
from kuang.schema import load, save, state_hash, ValidationError
from kuang.sample_assets import inventory, digest, write
from kuang.midi import export_bytes
from kuang.mastering import match_lufs
from kuang.loudness import measure
from kuang.spatial_audio import spatial_metrics
from kuang.lowend_audio import band_metrics
from kuang.production_audio import production_metrics
from kuang.audio import compare_wavs

END = 64*4*60/126+5
AUDIO = {'A': 'A-Phase15-approved-native.wav', 'B': 'B-Phase16-palette-native.wav'}


def adapter(host, plugin=None):
    return ProductionAdapter(host, plugin=plugin, workspace=ROOT,
                             scratch=ROOT/'.local/phase16/tmp', center_pitch_bend=bool(plugin))


def build(destination, source, patches, pitch_report, host, plugin, library=None):
    dest = Path(destination).resolve(); source = Path(source).resolve(); folder = Path(patches).resolve()
    if dest.exists() or dest.is_symlink() or not dest.is_relative_to(ROOT/'.local/phase16'):
        raise ValidationError('new project-local Phase16 stage required')
    old = load(source/'project.kuang.json')
    if state_hash(old) != SOURCE_HASH:
        raise ValidationError('approved Phase15 source drift')
    pitch = json.loads(Path(pitch_report).read_text())
    if pitch['version'] != 'phase16-actual-tuning-1' or set(pitch['voices']) != set(TRACKS.values()):
        raise ValidationError('all four actual pitch gates required')
    assignments = {t: folder/v for t,v in TRACKS.items()}
    # Each final patch must be exactly the patch actually calibrated in the
    # native and independent host, including its output calibration.
    for tid, voice in TRACKS.items():
        if digest(assignments[tid]/'manifest.json') != pitch['voices'][voice]['manifest_sha256']:
            raise ValidationError('uncalibrated final patch '+voice)
    before = inventory(source); before_patches = inventory(folder)
    a = adapter(host, plugin); legacy = adapter(host)
    assets = {t.id:source/'native/assets'/t.id for t in old.tracks if t.instrument and t.instrument.plugin_ref == 'soundcraft:sampler'}
    dest.mkdir(parents=True)
    try:
        (dest/'A').mkdir(); save(old, dest/'A/project.kuang.json')
        (dest/'A/song.mid').write_bytes(export_bytes(old))
        legacy.save(source/'native', dest/'A/native')
        legacy.render(dest/'A/native', dest/AUDIO['A'], end_seconds=END)
        reference = source.parent/'B-Phase15-repaired-native.wav'
        if digest(dest/AUDIO['A']) != digest(reference):
            raise ValidationError('untouched A native PCM drift')
        write(dest/'A/source-song-spec.json', json.loads(old.metadata['song_spec']))
        (dest/'internal-stages').mkdir(); stages = {}; selected = {}
        for i, (tid, voice) in enumerate(TRACKS.items()):
            selected[tid] = assignments[tid]
            q, plan = sound_palette(old, selected)
            final = len(selected) == len(assignments)
            bundle = dest/'B/native' if final else dest/'internal-stages'/voice/'native'
            wav = dest/AUDIO['B'] if final else dest/'internal-stages'/(str(i+1)+'-'+voice+'-full.wav')
            a.export(q, assets, selected, bundle)
            a.render(bundle, wav, end_seconds=END)
            level = measure(wav, library=library)
            spatial = spatial_metrics(wav)
            if level['clipped_samples'] or level['true_peak_dbtp'] > -1 or spatial['mono_sum']['clipped']:
                raise ValidationError('context headroom/mono failure '+voice)
            if spatial['bands']['low_20_120']['mono_energy_retention'] < .995:
                raise ValidationError('low-end stereo leakage '+voice)
            stages[voice] = {'voice_added': tid, 'all_previous_notes_exact': performance(q) == performance(old),
                             'levels': level, 'spatial': spatial, 'raw_sha256': digest(wav),
                             'integrity_gate': 'pass; not a listening preference verdict'}
            print('full64bar stage', voice, 'pass', level['integrated_lufs'], flush=True)
        save(q, dest/'B/project.kuang.json'); (dest/'B/song.mid').write_bytes(export_bytes(q))
        write(dest/'B/source-song-spec.json', json.loads(old.metadata['song_spec']))
        with tempfile.TemporaryDirectory(dir=a.scratch, prefix='final-reopen-') as d:
            d = Path(d); a.save(dest/'B/native', d/'native')
            a.render(d/'native', d/'repeat.wav', end_seconds=END)
            if digest(d/'repeat.wav') != digest(dest/AUDIO['B']) or a.inspect(d/'native')['native'] != a.inspect(dest/'B/native')['native']:
                raise ValidationError('full palette native state/PCM reopen drift')
        levels = {k: measure(dest/name, library=library) for k,name in AUDIO.items()}
        (dest/'listening').mkdir(); target = min(v['integrated_lufs'] for v in levels.values())
        matching = {k: match_lufs(dest/name, dest/'listening'/(k+'-'+('Phase15-approved' if k=='A' else 'Phase16-palette')+'-full-LUFS-matched.wav'), target, library=library) for k,name in AUDIO.items()}
        regions = [(s.name,s.start/q.ppq*60/q.tempo_bpm,(s.start+s.length)/q.ppq*60/q.tempo_bpm) for s in q.sections]
        report = {'version':'phase16-verification-1', 'source_hash':SOURCE_HASH, 'candidate_hash':state_hash(q),
                  'source_A_PCM_exact':True, 'note_count':1536, 'full_performance_and_MIDI_exact':True,
                  'native_state_and_PCM_reopen_exact':True, 'stages':stages, 'levels':levels, 'matching':matching,
                  'spatial':{k:spatial_metrics(dest/n) for k,n in AUDIO.items()},
                  'drop_bands':{k:band_metrics(dest/n,first=32*4*60/126,last=40*4*60/126) for k,n in AUDIO.items()},
                  'sections':{k:production_metrics(dest/n,regions)['sections'] for k,n in AUDIO.items()},
                  'full_difference':compare_wavs(dest/AUDIO['A'],dest/AUDIO['B']),
                  'human_preference':'unreviewed', 'professional_quality_claimed':False,
                  'mastering':'none; native raw plus constant-attenuation listening copies'}
        write(dest/'verification.json', report); write(dest/'production.json', plan)
        write(dest/'pitch-verification.json', pitch)
        write(dest/'recipe.json', {'version':'phase16-replay-1', 'source_hash':SOURCE_HASH, 'candidate_hash':state_hash(q),
              'raw_A_sha256':digest(dest/AUDIO['A']), 'raw_B_sha256':digest(dest/AUDIO['B']), 'end_seconds':END,
              'patch_manifest_sha256':{t:digest(v/'manifest.json') for t,v in assignments.items()}})
        shutil.copytree(source.parent/'licenses', dest/'licenses')
        write(dest/'licenses/Phase16-original-and-external.json', {
            'bundled':'Kuang original Fourier waves, patches and replay code MIT; inherited six sample assets have individual CC0/Unlicense provenance in this folder.',
            'not_bundled':{'Vitalium1.0.6':'GPL-3.0-or-later https://github.com/DISTRHO/DISTRHO-Ports/tree/2021-03-15/ports/vitalium',
                           'Pedalboard0.9.26':'GPL-3.0 https://github.com/spotify/pedalboard',
                           'official_Vital':'Not downloaded, installed, tested or bundled; account Basic route https://account.vital.audio/basic'},
            'excluded':'All downloaded tutorial/bank presets, embedded third-party wavetables, factory assets, plugin binaries, Suno/reference audio'})
        if inventory(source) != before or inventory(folder) != before_patches:
            raise ValidationError('source files changed during production')
    except BaseException:
        shutil.rmtree(dest); raise
    return report


def prepare_download(root):
    root = Path(root)
    if any((root/n).exists() for n in ('README.md','reproduce.py','reproduction')):
        raise ValidationError('download source already exists')
    shutil.copyfile(ROOT/'docs/PHASE16_LISTENING_README.md', root/'README.md')
    shutil.copyfile(ROOT/'tools/phase16_reproduce.py', root/'reproduce.py')
    frozen = root/'reproduction'; (frozen/'kuang').mkdir(parents=True)
    for p in (ROOT/'kuang').rglob('*'):
        if p.is_file() and p.suffix in ('.py','.lua','.json'):
            if p.is_symlink(): raise ValidationError('frozen source symlink')
            target = frozen/'kuang'/p.relative_to(ROOT/'kuang'); target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,target)
    shutil.copyfile(ROOT/'LICENSE',frozen/'LICENSE'); write(frozen/'source-manifest.json',inventory(frozen))


def package(root):
    root = Path(root); target = root/'phase16-house-listening.zip'
    if target.exists() or target.is_symlink(): raise ValidationError('new listening ZIP required')
    files = [p for name in ('A','B','listening','licenses','reproduction') for p in (root/name).rglob('*') if p.is_file()]
    files += [root/n for n in ('README.md','reproduce.py','recipe.json','production.json','verification.json','pitch-verification.json','sound-design.json')]
    if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files): raise ValidationError('unexpected bundled content')
    manifest = {str(p.relative_to(root)):digest(p) for p in files}
    with tempfile.TemporaryDirectory(dir=root) as d:
        zpath = Path(d)/'pack.zip'
        with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(files): z.write(p,str(p.relative_to(root)))
            z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
        with zipfile.ZipFile(zpath) as z:
            if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):
                raise ValidationError('listening ZIP integrity failed')
        if zpath.stat().st_size > 180_000_000: raise ValidationError('listening ZIP size budget')
        os.link(zpath,target)
    return {'bytes':target.stat().st_size,'sha256':digest(target)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=('build','package'))
    ap.add_argument('--out-dir',required=True)
    for flag in ('source','patches','pitch-report','soundcraft','plugin','meter-library'): ap.add_argument('--'+flag)
    z = ap.parse_args()
    if z.action == 'package': result = package(z.out_dir)
    else:
        if not all((z.source,z.patches,z.pitch_report,z.soundcraft,z.plugin)): ap.error('build requires explicit source/patches/pitch-report/soundcraft/plugin')
        result = build(z.out_dir,z.source,z.patches,z.pitch_report,z.soundcraft,z.plugin,z.meter_library)
    print(json.dumps(result,indent=2,allow_nan=False))
