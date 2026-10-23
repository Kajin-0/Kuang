"""Opt-in, authored production gestures over the exact released Phase 7 song.

Ordinary schema 0.1 notes, inserts and linear native lanes; no new engine,
sidechain routing, synth LFO, schema or transaction semantics.
"""

import json
from copy import deepcopy
from dataclasses import asdict

from .house_song import arrange_house
from .schema import (BAR, PPQ, AutomationLane, AutomationPoint, ParameterSpec,
                     Section, ValidationError, state_hash, validate)

SOURCE_HASH = '6e22ce487c5fd3453b8d26d4e8387e1238284248fa7335a9dfc3528e68e3f88a'
GESTURE_VERSION = 'house-gestures-v1'
HARMONICS = ('track-harmony', 'track-lead', 'track-arp')
PADS = ('track-depth-pad', 'track-depth-air')


def lane_value(lane, tick):
    """Evaluate the validated continuous canonical lane, including endpoints."""
    if tick <= lane.points[0].tick:
        return lane.points[0].value
    for a, b in zip(lane.points, lane.points[1:]):
        if tick <= b.tick:
            return a.value if a.shape == 'step' else a.value + (b.value-a.value)*(tick-a.tick)/(b.tick-a.tick)
    return lane.points[-1].value


def curve(project, label, owner, parameter, points):
    project.automation = [a for a in project.automation
                          if (a.target_id, a.parameter_id) != (owner, parameter)]
    values = sorted(dict(points).items())
    project.automation.append(AutomationLane('gesture-'+label, owner, parameter,
        [AutomationPoint(f'gesture-{label}-{i}', tick, value, 'linear')
         for i, (tick, value) in enumerate(values)]))


def gesture_house(source=None):
    source = arrange_house() if source is None else source
    validate(source)
    if state_hash(source) != SOURCE_HASH:
        raise ValidationError('gestures require the unchanged released Phase 7 song')
    p = deepcopy(source)
    p.name = 'Kuang / Pocket into motion'
    # Static normalized Choice selectors map to integer 3: 24 dB/oct. Never
    # interpolate a selector, or claim the cutoff taper changes canonical Hz.
    p.parameters += [ParameterSpec('soundcraft.'+s, 'normalized', 0, 1, 1/3, ['effect'])
                     for s in ('hpf_slope', 'lpf_slope')]

    def bars(label, owner, param, points):
        curve(p, label, owner, param, [(round(b*BAR), v) for b, v in points])

    deviations = []
    for t in p.tracks:
        role = t.id.removeprefix('track-')
        if role in ('snare', 'hats', 'percussion'):
            # One beat of air before bar 33. Preserve ALL kick/bass/hook notes,
            # including their IDs, timings and velocities throughout the song.
            for c in t.clips:
                kept = []
                for n in c.notes:
                    if 32*BAR-PPQ <= c.start+n.start < 32*BAR:
                        deviations.append({'track':t.id, 'clip':c.id, 'removed':asdict(n),
                                           'absolute_tick':c.start+n.start,
                                           'reason':'one-beat percussion pause before main drop'})
                    else:
                        kept.append(n)
                c.notes = kept
        if t.id in HARMONICS or role in ('hats', 'percussion', 'snare'):
            eq = t.effects[0]
            eq.parameters['soundcraft.lpf_slope'] = 1
            eq.parameters['soundcraft.lpf_freq'] = 1000
            # Intro opens from genuinely closed, build deliberately closes then
            # opens again. Reset on beat one uses a 12-tick (~6 ms) ramp to
            # avoid a mathematical jump while retaining the musical impact.
            bars(role+'-lpf', eq.id, 'soundcraft.lpf_freq', [
                (0,1000),(2,1400),(4,3000),(7.9,12000),(8,14000),
                (16,1600),(18,2200),(20,4000),(23.75,12000),
                (24,1100),(28,1600),(30,2800),(31.75,1100),
                ((32*BAR-12)/BAR,1100),(32,14000),
                (36,10000),(39.75,2400),(40,14000),(44,10000),
                (47.75,2400),(48,12000),(56,6500),(60,3000),(64,1000)])
            if t.id in HARMONICS or role == 'snare':
                base = 220 if role == 'snare' else 280
                eq.parameters['soundcraft.hpf_slope'] = 1
                bars(role+'-hpf', eq.id, 'soundcraft.hpf_freq', [
                    (0,base),(16,base),(18,400),(20,600),(23.75,1000),
                    (24,base),(28,base),(30,500),(31.75,1000),
                    ((32*BAR-12)/BAR,1000),(32,base),(48,base),(56,base),(64,base)])
        if t.id in ('track-lead', 'track-arp'):
            delay = next(e for e in t.effects if e.plugin_ref == 'soundcraft:mod_delay')
            delay.parameters.update({'effect.wet':.035,'soundcraft.feedback':.46,
                'soundcraft.time':60000/126*(.75 if role == 'lead' else .5),
                'soundcraft.mod_depth':0,'soundcraft.lpf':6500})
            points = {0:.035, p.length:.035}
            # Last note of each two-bar call/response, rather than empty last
            # beats. Hold wet through echoes, then fade. Mix is not a send:
            # some dry attack is exchanged for echoes on these selected notes.
            for first in range(0,64,2):
                events = [(c.start+n.start,n.duration) for c in t.clips for n in c.notes
                          if first*BAR <= c.start+n.start < (first+2)*BAR]
                if not events:
                    continue
                at, duration = max(events)
                wet = .58 if 24*BAR <= at < 32*BAR else .48
                for tick, value in ((max(0,at-96),.035),(at,wet),
                        (at+duration+PPQ,wet),(at+duration+2*PPQ,.035)):
                    if tick <= p.length:
                        points[tick] = value
            curve(p, role+'-throw', delay.id, 'effect.wet', points.items())
            for reverb in (e for e in t.effects if e.plugin_ref.endswith('reverb')):
                reverb.parameters.update({'soundcraft.decay_ms':3200,'soundcraft.low_cut':500,
                    'soundcraft.pre_delay':48,'soundcraft.width':.8})
                reverb.parameters['effect.wet'] = .10
                bars(role+'-space', reverb.id, 'effect.wet', [(0,.10),(20,.16),(23.75,.40),
                    (24,.58),(28,.62),(31.5,.66),(31.95,.50),(32,.10),
                    (46,.10),(47.8,.34),(48,.14),(56,.10),(64,.10)])
        if t.id in PADS:
            verb = t.effects[-1]
            verb.parameters.update({'soundcraft.decay_ms':3400,'soundcraft.pre_delay':42,
                                     'soundcraft.low_cut':650,'soundcraft.width':.80})
            verb.parameters['effect.wet'] = .25
            bars(role+'-space', verb.id, 'effect.wet', [(0,.25),(20,.30),(23.75,.42),
                (24,.60),(28,.64),(31.5,.64),(31.95,.48),(32,.22),(48,.25),(56,.22),(64,.22)])
        if t.id in PADS or t.id == 'track-harmony':
            base = t.controls['mixer.gain_db']
            points = []
            for beat in range(256):
                bar = beat//4
                # Let the breakdown breathe freely; the drop's first kick
                # visibly/audibly re-engages the programmed duck envelope.
                depth = 0 if 24 <= bar < 32 else 11 if t.id in PADS else 7
                points += [(beat*PPQ+offset,base+delta*depth)
                    for offset,delta in ((0,-1),(90,-1),(240,-.72),(480,-.25),(680,0),(PPQ-20,0))]
            curve(p, role+'-pump', t.id, 'mixer.gain_db', points+[(p.length,base)])
    p.metadata.update(production='house-production-gestures',gesture_version=GESTURE_VERSION,
        gesture_source_hash=SOURCE_HASH,gesture_note_deviations=json.dumps(deviations,sort_keys=True),
        gesture_notes='Native EQ7 HPF/LPF, note-aligned tempo delay throws, breakdown reverb, programmed tempo-synced gain ducking (NOT input-triggered sidechain). Kick, bass, main lead and original drop MIDI retained. Static synth ADSR; no oscillator LFO. Listening preference unknown.')
    validate(p)
    return p


def control(project, kind):
    """Same-input counterfactuals. Removes only the named gesture, no MIDI edits."""
    q = deepcopy(project)
    if kind not in ('hpf','lpf','delay','reverb','duck','modulation'):
        raise ValidationError('unknown gesture control')
    targets = set()
    swept = {(a.target_id,a.parameter_id) for a in q.automation if a.id.startswith('gesture-')}
    for t in q.tracks:
        if kind == 'duck' and t.id in (*PADS,'track-harmony'):
            targets.add((t.id,'mixer.gain_db'))
        for e in t.effects:
            if kind in ('hpf','lpf') and e.plugin_ref == 'soundcraft:eq_7band':
                param = 'soundcraft.'+kind+'_freq'
                # Only open an authored sweep. Fixed hat/percussion highpasses
                # must stay fixed, otherwise their low-frequency spill could
                # falsely inflate the measured effect of HPF automation.
                if (e.id,param) not in swept:continue
                e.parameters[param] = 10 if kind == 'hpf' else 20000
                targets.add((e.id,param))
            elif ((kind=='delay' and e.plugin_ref=='soundcraft:mod_delay') or
                  (kind=='reverb' and e.plugin_ref.endswith('reverb')) or
                  (kind=='modulation' and e.plugin_ref in ('soundcraft:chorus','soundcraft:phaser','soundcraft:flanger'))):
                e.parameters['effect.wet'] = 0
                targets.add((e.id,'effect.wet'))
    q.automation = [a for a in q.automation if (a.target_id,a.parameter_id) not in targets]
    validate(q)
    return q


def crop(project, first, bars, track_ids):
    """Fresh native audition window, same-input controls with exact boundary values.

    Retain sounding notes by explicit clipping at the window; record that this
    is a DSP-reset diagnostic, not an identical slice of a running full bounce.
    """
    if type(first) is not int or type(bars) is not int or first<0 or bars<1 or first+bars>project.bars:
        raise ValidationError('invalid gesture audition window')
    if not track_ids or len(set(track_ids))!=len(track_ids) or not set(track_ids)<=set(t.id for t in project.tracks):
        raise ValidationError('invalid audition tracks')
    q=deepcopy(project);start,end=first*BAR,(first+bars)*BAR
    q.bars=bars;q.sections=[Section('gesture-audition-section','Gesture audition',0,bars*BAR)]
    q.tracks=[t for t in q.tracks if t.id in track_ids]
    owners={t.id for t in q.tracks}|{e.id for t in q.tracks for e in t.effects}
    for t in q.tracks:
        clips=[]
        for c in t.clips:
            lo,hi=max(start,c.start),min(end,c.start+c.length)
            if hi<=lo:continue
            notes=[]
            for n in c.notes:
                a,b=max(lo,c.start+n.start),min(hi,c.start+n.start+n.duration)
                if b>a:n.start=a-lo;n.duration=b-a;notes.append(n)
            c.start=lo-start;c.length=hi-lo;c.notes=notes
            if notes:clips.append(c)
        t.clips=clips
    q.automation=[a for a in q.automation if a.target_id in owners]
    for lane in q.automation:
        a,b=lane_value(lane,start),lane_value(lane,end)
        points=[AutomationPoint(x.id,x.tick-start,x.value,x.shape) for x in lane.points if start<x.tick<end]
        lane.points=[AutomationPoint(lane.id+'-crop-start',0,a,'linear'),*points,
                     AutomationPoint(lane.id+'-crop-end',bars*BAR,b,'linear')]
    q.metadata['gesture_diagnostic_window']=json.dumps({'first_bar':first+1,'bars':bars,
        'native_dsp_reset':True,'boundary_notes_explicitly_clipped':True})
    validate(q)
    return q
