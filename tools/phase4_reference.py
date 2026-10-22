#!/usr/bin/env python3
"""Reproduce a labeled original/refined house comparison using an installed host.

Run from the checkout. New output paths only. Failed work is removed; all source
files are hashed before/after. No downloads, inference, shell commands or assets.
"""

import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kuang.audio import analyze_wav, compare_wavs
from kuang.create import create
from kuang.production_audio import production_metrics
from kuang.schema import ValidationError, load
from kuang.soundcraft import SoundCraftAdapter


def inventory(roots):
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for root in roots for p in sorted(root.rglob('*')) if p.is_file()}


def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+'\n')


def excerpt(source, destination, start, end, gain=1):
    """PCM slice / attenuation only, explicitly separate from native rendering."""
    with wave.open(str(source), 'rb') as src, wave.open(str(destination), 'wb') as dst:
        params = src.getparams()
        dst.setparams(params)
        src.setpos(start)
        width = src.getsampwidth()
        remaining = end-start
        while remaining:
            data = src.readframes(min(65536, remaining))
            if not data:
                raise ValidationError('truncated reference PCM')
            remaining -= len(data)//(width*src.getnchannels())
            if gain != 1:
                converted = bytearray()
                for offset in range(0,len(data),width):
                    value = int.from_bytes(data[offset:offset+width], 'little', signed=True)
                    converted += round(value*gain).to_bytes(width, 'little', signed=True)
                data = converted
            dst.writeframes(data)


def reference(baseline, destination, executable, preserve=()):
    baseline, destination = Path(baseline).resolve(), Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValidationError('reference output must be a new path')
    roots = [baseline, *(Path(r).resolve() for r in preserve)]
    if any(destination.resolve().is_relative_to(r) for r in roots):
        raise ValidationError('reference output must be outside preserved sources')
    before = inventory(roots)
    source = json.loads((baseline/'report.json').read_text())
    if source['song_spec']['genre'] != 'house':
        raise ValidationError('reference baseline must be house')
    adapter = SoundCraftAdapter(executable, timeout=120)
    adapter.import_project(baseline/'native')
    destination.mkdir(parents=True)
    try:
        original = destination/'A-original'
        original.mkdir()
        for name in ('project.kuang.json','song-spec.json','song.mid'):
            shutil.copyfile(baseline/name, original/name)
        adapter.save(baseline/'native', original/'native')
        a = adapter.render(original/'native', destination/'A-original.wav')
        refined = destination/'B-refined'
        b_create = create(source['prompt'], refined, seed=source['song_spec']['seed'],
                          production='refined', soundcraft=executable, render=True)
        os.link(refined/'preview.wav', destination/'B-refined.wav')
        adapter.save(refined/'native', destination/'B-refined-saved')
        if adapter.inspect(refined/'native')['native'] != adapter.inspect(destination/'B-refined-saved')['native']:
            raise ValidationError('full reference save/reopen mismatch')
        p = load(refined/'project.kuang.json')
        regions = [(s.name.lower(), s.start/p.ppq*60/p.tempo_bpm,
                    (s.start+s.length)/p.ppq*60/p.tempo_bpm) for s in p.sections]
        metrics = {label:production_metrics(destination/filename, regions)
                   for label,filename in (('original','A-original.wav'),('refined','B-refined.wav'))}
        for m in metrics.values():
            if not m['non_silent'] or m['rms'] <= 1e-6 or m['peak'] >= 1 or m['clipped_samples']:
                raise ValidationError('reference audio must be non-silent and unclipped')
        delta = compare_wavs(destination/'A-original.wav', destination/'B-refined.wav')
        if not delta['measurable_change']:
            raise ValidationError('no measurable reference change')
        # Both matched files are attenuated to the quieter full-render RMS.
        # This is an audition aid, not LUFS matching or a native master change.
        matched = destination/'RMS-matched'
        matched.mkdir()
        target = min(m['rms'] for m in metrics.values())
        match_report = {}
        for label, filename in (('original','A-original.wav'),('refined','B-refined.wav')):
            gain = target/metrics[label]['rms']
            excerpt(destination/filename, matched/filename, 0, metrics[label]['frames'], gain)
            match_report[label] = {'gain_db':20*math.log10(gain), 'analysis':analyze_wav(matched/filename)}
        excerpts = destination/'sections'
        excerpts.mkdir()
        for label, filename in (('original','A-original.wav'),('refined','B-refined.wav')):
            for name, m in metrics[label]['sections'].items():
                if name != 'full':
                    excerpt(destination/filename, excerpts/f'{label}-{name}.wav', m['start_frame'], m['end_frame'])
        capability = adapter.capabilities(p)
        write(destination/'pinned-capabilities.json', {'capabilities':capability, 'discovered':adapter._discover(),
              'instrument_parameter_command':'mix.instrument_param (manual native edits; Kuang instrument edits use fresh export)',
              'gaps':['No exposed wavetable or synth LFO', 'Instrument automation rejected by tested native addresses',
                      'Pitch/ratio/Q units have no schema 0.1 mapping', 'No bus/send/master processing in this adapter']})
        after = inventory(roots)
        if after != before:
            raise ValidationError('original source inventory changed')
        # Historical baseline render is retained, and this A render is fresh.
        report = {'complete':True, 'baseline':str(baseline), 'metrics':metrics,
                  'difference':delta, 'rms_matched':match_report,
                  'fresh_original_render':a, 'refined_canonical_hash':b_create['validation']['canonical_hash'],
                  'full_native_save_reopen_equal':True, 'source_before':before, 'source_after':after,
                  'sources_unchanged':True, 'listening_performed':False,
                  'assessment':'Designed arrangement/timbre/balance improvements. Human preference and audibility require listening.',
                  'artifact_sha256':inventory([destination])}
        write(destination/'verification.json', report)
        return report
    except BaseException:
        shutil.rmtree(destination)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--soundcraft', required=True)
    parser.add_argument('--preserve', action='append', default=[])
    args = parser.parse_args()
    result = reference(args.baseline, args.out_dir, args.soundcraft, args.preserve)
    print(json.dumps({'complete':result['complete'], 'report':str(Path(args.out_dir)/'verification.json')}, indent=2))
