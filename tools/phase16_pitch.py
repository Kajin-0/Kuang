#!/usr/bin/env python3
"""Actual multi-register dry tuning gate, centered native MIDI and independent VST3."""
import argparse
import json
import sys
from pathlib import Path
from copy import deepcopy
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kuang.production_host import ProductionAdapter
from kuang.external_synth import bound_project
from kuang.schema import BAR, Clip, Note, Section, load, save, ValidationError
from kuang.studio_palette import TRACKS
from kuang.pitch_audio import note_pitch, spectrum, hz, cents
from kuang.sample_assets import write, digest
from tools.phase15_pitch import held, ON, WINDOWS

NOTES = (36, 43, 51, 55, 58, 62, 63, 65, 67)
CHORD = (51, 55, 58, 62)
SPACING = 3 * 4 * 60 / 126


def calibration(source, tid):
    q = held(source, tid, [36])
    q.bars = 30
    q.sections = [Section('studio-pitch-section', 'Isolated notes then Cm9', 0, 30*BAR)]
    notes = [Note('studio-pitch-'+str(n), i*3*BAR+480, 2880, n, 96, 0)
             for i, n in enumerate(NOTES)]
    notes += [Note('studio-chord-'+str(n), 27*BAR+480, 2880, n, 96, 0) for n in CHORD]
    q.tracks[0].clips = [Clip('studio-calibration', 'No overlapping held notes; final chord',
                              'midi', 0, 30*BAR, notes, None)]
    return q


def analyze(path, *, monophonic=False):
    result = {}
    for i, n in enumerate(NOTES):
        result[str(n)] = [note_pitch(path, n, i*SPACING+ON+u, i*SPACING+ON+v)
                          for u, v in WINDOWS]
        for row in result[str(n)]:
            if abs(row['fft_cents']) > 5 or abs(row['period_cents']) > 5 or row['period_correlation'] < .85:
                raise ValidationError('studio tuning failed '+str(n)+' '+str(row))
    peaks = spectrum(path, 9*SPACING+ON+.5, 9*SPACING+ON+.9)[2][:100]
    # Mono bass intentionally uses last-note priority; do not call it a
    # polyphonic instrument merely because four note-ons were submitted.
    expected = CHORD[-1:] if monophonic else CHORD
    chord = [{'midi': n, 'nearest_peak_cents': min(abs(cents(x['hz'], hz(n))) for x in peaks)} for n in expected]
    if any(x['nearest_peak_cents'] > 5 for x in chord):
        raise ValidationError('actual Cm9 partials failed '+str(chord))
    return {'notes': result, 'chord': chord, 'chord_mode': 'mono last-note priority' if monophonic else 'four actual simultaneous voices'}


def gate(destination, source, patch_folder, executable, plugin, host_python):
    out = Path(destination).resolve()
    if out.exists() or not out.is_relative_to(ROOT/'.local/phase16'):
        raise ValidationError('new project-local Phase16 pitch destination required')
    out.mkdir()
    a = ProductionAdapter(executable, plugin=plugin, workspace=ROOT,
                          scratch=ROOT/'.local/phase16/tmp', center_pitch_bend=True)
    original = load(source)
    patches = {tid: Path(patch_folder)/voice for tid, voice in TRACKS.items()}
    p = bound_project(original, patches)
    report = {}
    for tid, voice in TRACKS.items():
        q = calibration(p, tid)
        save(q, out/(voice+'.kuang.json'))
        a.export(q, {}, {tid: patches[tid]}, out/voice)
        wav = out/(voice+'-native.wav')
        a.render(out/voice, wav)
        measured = analyze(wav, monophonic=voice == 'bass')
        a.save(out/voice, out/(voice+'-reopened'))
        repeated = out/(voice+'-repeated.wav')
        a.render(out/(voice+'-reopened'), repeated)
        if digest(wav) != digest(repeated) or a.inspect(out/voice)['native'] != a.inspect(out/(voice+'-reopened'))['native']:
            raise ValidationError('studio patch native reload not exact')
        report[voice] = {'native': measured, 'native_state_and_PCM_reload_exact': True,
                         'manifest_sha256': digest(patches[tid]/'manifest.json')}
        print(voice, 'native pitch and chord pass', flush=True)
    # Optional GPL host is isolated in its separately installed interpreter.
    request = out/'independent-request.json'
    write(request, {'plugin': str(a.external.plugin), 'patches': {v: str(patches[t]) for t, v in TRACKS.items()}, 'out': str(out)})
    a.external.call([str(Path(host_python).absolute()), str(ROOT/'tools/phase16_independent.py'), str(request)], ROOT)
    for voice in TRACKS.values():
        report[voice]['independent'] = analyze(out/(voice+'-independent.wav'), monophonic=voice == 'bass')
    write(out/'verification.json', {'version': 'phase16-actual-tuning-1', 'voices': report,
          'notes': list(NOTES), 'fft_and_period_max_cents': 5, 'minimum_period_correlation': .85,
          'native_pitch_center': a.capabilities()['midi_pitch_initialization'],
          'independent_host': 'Pedalboard0.9.26/Vitalium1.0.6', 'no_transposed_MIDI': True})
    return report

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    for flag in ('out-dir', 'source', 'patches', 'soundcraft', 'plugin', 'host-python'):
        ap.add_argument('--'+flag, required=True)
    z = ap.parse_args()
    gate(z.out_dir, z.source, z.patches, z.soundcraft, z.plugin, z.host_python)
