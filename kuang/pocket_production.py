"""Eight-bar, factorial producer experiment over the frozen Phase 10 drop.

No new synth, routing fiction, random humanization or default composer change.
Changes are ordinary scoped transactions; the release sidecars carry labels.
"""
from copy import deepcopy
from dataclasses import asdict

from .atmosphere import atmosphere_house
from .gestures import crop
from .schema import BAR, PPQ, ValidationError, state_hash, validate
from .transactions import (AddAutomationPoints, DeleteAutomationPoints, Engine,
                           Scope, SetParameter, UpdateNote)

SOURCE_HASH = 'dad1db280f798fdf07ab4b0243bcc6e528f680b30f32b8a5e92104a94ce640b1'
FIRST_BAR = 32
BARS = 8
GROOVE_TRACKS = ('track-snare', 'track-hats', 'track-percussion', 'track-bass', 'track-harmony')
# Calibrated from independent, same-MIDI A/C native eight-bar stem RMS.
# These are explicit native post-FX fader trims, including every existing gain
# breakpoint. They preserve the prior sound hierarchy, not a louder C mix.
SOUND_TRIMS = {'track-kick': .75, 'track-bass': 1.5, 'track-snare': .3,
               'track-hats': 1.3, 'track-harmony': -2.9}

# Each entry has a single musical purpose. All controls already exist in A;
# no new insert or automation, selector, unit or preset is introduced.
SOUND_BY_TRACK = {
    'track-kick': {'instrument': {'soundcraft.kick_decay': 225},
                   'effect-kick-compression': {'soundcraft.attack': 12, 'soundcraft.release': 65},
                   'effect-kick-eq': {'soundcraft.high_mid_freq': 2200, 'soundcraft.high_mid_gain': 2}},
    'track-bass': {'instrument': {'soundcraft.amp_decay': 125, 'soundcraft.amp_sustain': .18,
                                  'soundcraft.amp_release': 22, 'synth.cutoff_hz': 780,
                                  'soundcraft.filter_env_amount': .23}},
    'track-snare': {'instrument': {'soundcraft.snare_decay': 85},
                    'effect-snare-room': {'soundcraft.decay_ms': 380, 'soundcraft.pre_delay': 8,
                                           'effect.wet': .065}},
    'track-hats': {'instrument': {'soundcraft.hat_decay': 40, 'soundcraft.open_hat_decay': 155}},
    'track-harmony': {'instrument': {'soundcraft.amp_attack': 2.5, 'soundcraft.amp_decay': 110,
                                     'soundcraft.amp_sustain': 0, 'soundcraft.amp_release': 45,
                                     'soundcraft.filter_decay': 95, 'soundcraft.filter_env_amount': .28,
                                     'synth.cutoff_hz': 1800},
                      'effect-harmony-room': {'soundcraft.decay_ms': 600, 'effect.wet': .13},
                      'effect-harmony-chorus': {'effect.wet': .10},
                      'effect-harmony-compression': {'soundcraft.attack': 4, 'soundcraft.threshold': -27,
                                                     'soundcraft.makeup': 1}},
}


def baseline(source=None):
    source = atmosphere_house() if source is None else source
    validate(source)
    if state_hash(source) != SOURCE_HASH:
        raise ValidationError('Phase 12 requires the exact released Phase 10 D, not Phase 11')
    return crop(source, FIRST_BAR, BARS, [t.id for t in source.tracks])


def groove_operations(p):
    """Authored role timing, not a global shuffle or a random perturbation."""
    operations = []
    for t in p.tracks:
        if t.id not in GROOVE_TRACKS:
            continue
        for c in t.clips:
            for original in c.notes:
                n = deepcopy(original)
                at = c.start+n.start
                bar, within = divmod(at, BAR)
                step = within//(PPQ//4)
                grid = step*(PPQ//4)
                if t.id == 'track-snare':
                    if n.pitch == 39:
                        # Backbeats stay 18 ticks (~9 ms) behind the kick.
                        n.velocity = 107 if step == 4 else 103 if bar in (3, 7) else 96
                    else:
                        n.start += grid+56-within
                        n.velocity = 34 if bar in (3, 7) else 30
                elif t.id == 'track-hats':
                    if n.pitch == 46:
                        n.start += grid+8-within
                        n.velocity = 82 if step == 6 else 75 if bar not in (3, 7) else 80
                    elif step in (2, 10):
                        n.start += grid+10-within
                        n.velocity = 68 if step == 2 else 62
                    else:
                        # Quiet last-sixteenth hats answer the offbeat accents.
                        n.start += grid+60-within
                        n.velocity = 34 if step < 12 else 41
                elif t.id == 'track-percussion':
                    n.start += grid+60-within
                    n.velocity = {1: 30, 7: 46, 9: 27, 15: 40}[step]
                    if bar in (3, 7) and step == 15:
                        n.velocity = 48
                elif t.id == 'track-bass':
                    # Long offbeat body, short weak syncopations, an uncluttered
                    # pickup. The existing root/answer pitches remain exact.
                    duration, velocity, delay = {
                        2: (330, 105, 8), 5: (115, 74, 48), 7: (90, 53, 60),
                        10: (285, 97, 8), 14: (165, 85, 8), 15: (85, 62, 48),
                    }[step]
                    n.start += grid+delay-within
                    n.duration, n.velocity = duration, velocity
                    if step == 2 and bar in (3, 7):
                        n.velocity = 99
                elif t.id == 'track-harmony':
                    # Preserve the voiced chord and its 4-tick upward roll.
                    roll = (within-36) % (PPQ//4)
                    n.start += grid+12+roll-within
                    response = step == 11
                    n.duration = 110 if response else 150 if bar % 4 in (0, 2) else 120
                    voice = roll//4
                    n.velocity = (58 if response else 74 if bar % 4 in (0, 2) else 66)-2*voice
                if n != original:
                    operations.append(UpdateNote('update_note', c.id, n))
    return operations


def sound_operations(p):
    operations = []
    for t in p.tracks:
        for owner, parameters in SOUND_BY_TRACK.get(t.id, {}).items():
            device = t.instrument if owner == 'instrument' else next((e for e in t.effects if e.id == owner), None)
            if device is None:
                raise ValidationError('missing existing production device: '+owner)
            for key, value in parameters.items():
                if key not in device.parameters:
                    raise ValidationError('missing existing production control: '+key)
                operations.append(SetParameter('set_parameter', device.id, key, value))
        if t.id in SOUND_TRIMS:
            trim = SOUND_TRIMS[t.id]
            operations.append(SetParameter('set_parameter', t.id, 'mixer.gain_db',
                                           t.controls['mixer.gain_db']+trim))
            for lane in p.automation:
                if (lane.target_id, lane.parameter_id) != (t.id, 'mixer.gain_db'):
                    continue
                points = deepcopy(lane.points)
                for point in points:
                    point.value += trim
                operations += [DeleteAutomationPoints('delete_automation_points', lane.id,
                                                       [v.id for v in lane.points]),
                               AddAutomationPoints('add_automation_points', lane.id, points)]
    return operations


def apply_stage(p, operations, *, groove):
    tracks = list(GROOVE_TRACKS) if groove else list(SOUND_BY_TRACK)
    parameters = [] if groove else sorted({o.parameter_id for o in operations if isinstance(o, SetParameter)})
    e = Engine(p)
    clips = [c.id for t in p.tracks if t.id in tracks for c in t.clips]
    receipt = e.apply(operations, Scope(tracks, clips, parameters, 0, p.length) if groove
                      else Scope(tracks, [], parameters, None, None), state_hash(p))
    return e.project, receipt


def experiment(source=None):
    """Return A/B/C/D and exact reversible receipts; source is never mutated."""
    a = baseline(source)
    b, rb = apply_stage(a, groove_operations(a), groove=True)
    c, rc = apply_stage(a, sound_operations(a), groove=False)
    d, rd = apply_stage(b, sound_operations(b), groove=False)
    return {'A': a, 'B': b, 'C': c, 'D': d}, {
        'B-from-A': asdict(rb), 'C-from-A': asdict(rc), 'D-from-B': asdict(rd)}


def note_changes(before, after):
    """Every note change with canonical IDs and unrounded millisecond deltas."""
    result = []
    for t, u in zip(before.tracks, after.tracks):
        for c, d in zip(t.clips, u.clips):
            for n, m in zip(c.notes, d.notes):
                if n != m:
                    result.append({'track': t.id, 'clip': c.id, 'before': asdict(n), 'after': asdict(m),
                        'absolute_before_tick': c.start+n.start, 'absolute_after_tick': d.start+m.start,
                        'onset_delta_ms': (m.start-n.start)*60000/(before.tempo_bpm*before.ppq)})
    return result
