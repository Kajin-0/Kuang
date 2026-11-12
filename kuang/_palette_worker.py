"""Private subprocess for one bounded Vitalium preset audition.

This is invoked only through autonomous_palette's isolated worker boundary.
Third-party patches are never bound to the public original-only VST adapter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
from pathlib import Path

from .schema import ValidationError, strict_json
from .autonomous_palette import PINNED_MODULES, MAX_PRESET_BYTES, _bounded_read, _validate_patch
from .vitalium_patch import chunks, component, component_patch, vstpreset

RATE = 48000
DURATION = {'chord': 3.2, 'pad': 3.8, 'bass': 3.0}


def _events(role, tonic, mode):
    intervals = [0, 3 if mode == 'minor' else 4, 7, 10 if mode == 'minor' else 11]
    root = 36 + tonic if role == 'bass' else 60 + tonic
    events = [(bytes([0xE0, 0, 64]), 0.)]
    if role == 'chord':
        for start, end in ((.2, 1.1), (1.6, 2.2)):
            for step in intervals:
                events.extend(((bytes([0x90, root + step, 86]), start), (bytes([0x80, root + step, 0]), end)))
    elif role == 'pad':
        for step in intervals[:3]:
            events.extend(((bytes([0x90, root + step, 82]), .15), (bytes([0x80, root + step, 0]), 2.25)))
    else:
        for step, start, end in ((0, .15, .55), (0, .75, 1.15), (7, 1.4, 1.8), (0, 2., 2.3)):
            events.extend(((bytes([0x90, root + step, 88]), start), (bytes([0x80, root + step, 0]), end)))
    return sorted(events, key=lambda event: (event[1], event[0][0])), root, intervals


def _features(audio, role, root, intervals):
    import numpy as np

    if audio.shape != (2, round(DURATION[role] * RATE)) or not np.isfinite(audio).all():
        raise ValidationError('invalid or non-finite audio')
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
    if peak < .0001 or rms < .00001:
        raise ValidationError('silent or near-silent audio')
    if peak >= 1 - 1 / 2**23:
        raise ValidationError('audio clips at or above full scale')
    x = audio.astype(np.float64)
    def energy(lo, hi):
        section = x[:, round(lo * RATE):round(hi * RATE)]
        return float(np.sqrt(np.mean(section * section)))
    active = energy(.3, 1.1)
    attack = energy(.15, .35) / max(active, 1e-12)
    tail_start = {'chord': 2.45, 'pad': 2.65, 'bass': 2.5}[role]
    tail = energy(tail_start, DURATION[role]) / max(active, 1e-12)
    # Full-phrase normalized frequency energy, independent of gain.
    nfft = 8192
    window = np.hanning(nfft)
    freq = np.fft.rfftfreq(nfft, 1 / RATE)
    powers = np.zeros(len(freq), dtype=np.float64)
    for pos in np.linspace(round(.2 * RATE), x.shape[1] - nfft, 24, dtype=int):
        spectrum = np.fft.rfft(x[:, pos:pos+nfft] * window, axis=1)
        powers += np.sum(np.abs(spectrum) ** 2, axis=0)
    low = float(np.sum(powers[(freq >= 25) & (freq < 220)]))
    mid = float(np.sum(powers[(freq >= 220) & (freq < 2500)]))
    high = float(np.sum(powers[(freq >= 2500) & (freq < 16000)]))
    total = low + mid + high
    if total <= 0:
        raise ValidationError('no measurable tonal energy')
    m = (x[0] + x[1]) * .5
    s = (x[0] - x[1]) * .5
    stereo = float(np.sum(s*s) / max(np.sum(m*m) + np.sum(s*s), 1e-24))
    # Approximate spectral-peak compatibility; harmonics and octave alternatives are allowed.
    start, end = {'chord': (.3, .9), 'pad': (.65, 1.35), 'bass': (.2, .52)}[role]
    region = x[:, round(start * RATE):round(end * RATE)]
    channel = region[int(np.argmax(np.mean(region*region, axis=1)))]
    spec = np.abs(np.fft.rfft(channel * np.hanning(len(channel)), n=65536))
    f = np.fft.rfftfreq(65536, 1/RATE)
    mask = (f >= 30) & (f <= (2500 if role != 'bass' else 1400))
    index = np.flatnonzero(mask)[int(np.argmax(spec[mask]))]
    peak_hz = float(f[index])
    expected = [440 * 2 ** ((root + step - 69) / 12) for step in (intervals if role == 'chord' else intervals[:3] if role == 'pad' else [0])]
    distance = min(abs(12 * math.log2(peak_hz / (hz * harmonic * 2**octave)))
                   for hz in expected for harmonic in range(1, 7) for octave in (-1, 0, 1))
    if distance > 2.0:
        raise ValidationError('gross spectral pitch mismatch')
    return {'peak': peak, 'rms': rms, 'crest_db': 20 * math.log10(peak/rms),
            'low_fraction': low/total, 'mid_fraction': mid/total, 'high_fraction': high/total,
            'attack_ratio': min(20., attack), 'tail_ratio': min(20., tail), 'stereo_side_fraction': stereo,
            'dominant_peak_hz': peak_hz, 'pitch_distance_semitones': distance,
            'pitch_note': 'dominant spectral peak against expected notes/harmonics/octaves; not transcription'}


def run(plugin_path, expected_hash, source_hash, role, tonic, mode, work):
    import numpy as np
    import pedalboard
    import soundfile as sf

    module = plugin_path / 'Contents/x86_64-linux/vitalium.so'
    if expected_hash not in PINNED_MODULES or hashlib.sha256(_bounded_read(module, 64 * 1024 * 1024)).hexdigest() != expected_hash:
        raise ValidationError('plugin is unpinned or changed after parent verification')
    if not 0 <= tonic <= 11:
        raise ValidationError('invalid audition tonic')
    data = _bounded_read(work/'input.vital', MAX_PRESET_BYTES)
    if hashlib.sha256(data).hexdigest() != source_hash:
        raise ValidationError('staged preset hash differs')
    raw = strict_json(data.decode('utf-8'))
    if type(raw) is not dict:
        raise ValidationError('invalid preset object')
    patch = _validate_patch(data, {'synth_version': raw.get('synth_version'), 'compatibility': 'version_candidate'})
    plugin = pedalboard.load_plugin(str(plugin_path))
    if plugin.name != 'Vitalium' or plugin.version != '1.0.6':
        raise ValidationError('unexpected runtime plugin identity/version')
    plugin.preset_data = vstpreset(component(patch))
    state = chunks(plugin.preset_data)[b'Comp']
    actual = component_patch(state)
    if (actual.get('preset_name') != patch.get('preset_name') or
            (patch.get('author') and actual.get('author') != patch.get('author')) or
            actual.get('settings', {}).get('sample_on') != 0):
        raise ValidationError('preset identity did not survive plugin load or sample was enabled')
    events, root, intervals = _events(role, tonic, mode)
    audio = np.asarray(plugin(events, duration=DURATION[role], sample_rate=RATE, num_channels=2, buffer_size=512))
    features = _features(audio, role, root, intervals)
    sf.write(str(work/'preview.wav'), audio.T, RATE, format='WAV', subtype='PCM_24')
    return {'status': 'accepted', 'features': features,
            'runtime': {'plugin_name': plugin.name, 'plugin_version': plugin.version,
                        'pedalboard_version': pedalboard.__version__, 'readback_preset_name': actual.get('preset_name'),
                        'component_sha256': hashlib.sha256(state).hexdigest(), 'roundtrip': 'identity and sample-off verified; not bit-identical-state claim',
                        'phrase_root_midi': root, 'phrase_mode': mode}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plugin', required=True); parser.add_argument('--plugin-sha', required=True); parser.add_argument('--source-sha', required=True)
    parser.add_argument('--role', required=True, choices=('chord','pad','bass')); parser.add_argument('--tonic', type=int, default=0)
    parser.add_argument('--mode', choices=('major','minor'), default='minor'); parser.add_argument('--work', required=True)
    args = parser.parse_args();work = Path(args.work)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024 * 1024, 4 * 1024 * 1024))
    try:
        result = run(Path(args.plugin), args.plugin_sha, args.source_sha, args.role, args.tonic, args.mode, work)
    except Exception as exc:
        result = {'status': 'rejected', 'reason': f'{type(exc).__name__}: {exc}'[:300]}
    (work/'result.json').write_text(json.dumps(result, allow_nan=False, sort_keys=True)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
