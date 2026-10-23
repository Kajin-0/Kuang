"""Event timing and envelope diagnostics, never a musical quality score."""
import math
import wave

from .production_audio import _decode
from .schema import BAR, PPQ, ValidationError


def event_map(p):
    ms = 60000/(p.tempo_bpm*p.ppq)
    result = {}
    for t in p.tracks:
        events = []
        for c in t.clips:
            for n in c.notes:
                tick = c.start+n.start
                nearest = round(tick/(PPQ//4))*(PPQ//4)
                events.append({'id': n.id, 'clip': c.id, 'tick': tick,
                    'bar': tick//BAR+1, 'pitch': n.pitch, 'velocity': n.velocity,
                    'duration_ms': n.duration*ms, 'sixteenth_offset_ms': (tick-nearest)*ms})
        result[t.id] = {'events': sorted(events, key=lambda x: (x['tick'], x['pitch'], x['id'])),
            'notes': len(events), 'velocity_mean': sum(e['velocity'] for e in events)/len(events) if events else None,
            'offsets_ms': sorted({round(e['sixteenth_offset_ms'], 6) for e in events})}
    return result


def note_windows(path, project, track_id, *, pitch=None):
    """Window energies relative to actual authored onsets, including late hits.

    Multiple sounding voices can overlap: this is a stem measurement, not
    inferred isolated voice gain reduction or a perceptual transient score.
    """
    track = next((t for t in project.tracks if t.id == track_id), None)
    if track is None:
        raise ValidationError('unknown timing diagnostic track')
    with wave.open(str(path), 'rb') as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (2, 3, 48000):
            raise ValidationError('onset diagnostics require stereo 48k24 PCM')
        duration = w.getnframes()/48000
        rows = []
        for c in track.clips:
            for n in c.notes:
                if pitch is not None and n.pitch != pitch:
                    continue
                at = (c.start+n.start)*60/(project.tempo_bpm*project.ppq)
                energies = {}
                for name, a, b in (('attack_0_20ms', 0, .02), ('body_20_100ms', .02, .1),
                                   ('tail_100_220ms', .1, .22)):
                    if at+b > duration:
                        continue
                    w.setpos(round((at+a)*48000))
                    frames = list(_decode(w.readframes(round((b-a)*48000)), 3, 2))
                    energies[name] = sum(l*l+r*r for l, r in frames)/(2*len(frames))
                rows.append({'id': n.id, 'at_seconds': at, 'energy': energies})
    average = {key: sum(r['energy'][key] for r in rows if key in r['energy'])/
               sum(key in r['energy'] for r in rows) for key in rows[0]['energy']} if rows else {}
    return {'method': 'actual MIDI onset, stereo mean-square windows; overlapping stem voices retained',
            'events': rows, 'mean_energy': average,
            'attack_to_tail_db': 10*math.log10(average['attack_0_20ms']/average['tail_100_220ms'])
                if average.get('attack_0_20ms', 0) and average.get('tail_100_220ms', 0) else None}


def gain_fit_residual(original, changed):
    """Least-squares scalar fit: distinguish waveform shape from pure gain.

    This does not align/warp or measure quality. Both inputs must already have
    identical sample origin, length and format. PCM quantization is retained.
    """
    with wave.open(str(original), 'rb') as a, wave.open(str(changed), 'rb') as b:
        def fmt(w):
            return (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes(), w.getcomptype())
        if fmt(a) != fmt(b) or fmt(a)[:3] != (2, 3, 48000) or a.getnframes() == 0:
            raise ValidationError('scalar fit needs aligned stereo 48k24 PCM')
        aa = bb = ab = 0.
        while left := a.readframes(32768):
            right = b.readframes(32768)
            for x, y in zip(_decode(left, 3, 2), _decode(right, 3, 2)):
                aa += x[0]*x[0]+x[1]*x[1]
                bb += y[0]*y[0]+y[1]*y[1]
                ab += x[0]*y[0]+x[1]*y[1]
        if not aa or not bb:
            raise ValidationError('scalar fit needs two non-silent inputs')
    return {'method': 'aligned least-squares scalar only; no time shift or perceptual score',
            'best_scalar': ab/aa, 'residual_to_changed_rms_ratio': math.sqrt(max(0, bb-ab*ab/aa)/bb)}
