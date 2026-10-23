"""Phase 10: separately testable pad space and quiet mono sine pulse.

Every original Phase 9 note/clip remains exact. Existing lane/point identities
remain; only explicitly selected wet values change. Ordinary schema 0.1.
"""

import json
from copy import deepcopy

from .depth import PAD_IDS,note_fingerprints
from .schema import (BAR,PPQ,AutomationLane,AutomationPoint,Clip,Effect,Note,ParameterSpec,Track,
                     ValidationError,state_hash,validate)
from .translation import translation_house

SOURCE_HASH='209b21e6b58283237ebaf3f29e56e7af6d2d0f6b8f267bff855663267e7c17ef'
PULSE_ID='track-sub-pulse'


def _space(p):
    changed=[]
    for t in p.tracks:
        if t.id in PAD_IDS:
            air=t.id==PAD_IDS[1]
            t.controls['mixer.pan']=.78 if air else -.72
            t.instrument.parameters.update({'soundcraft.amp_attack':620 if air else 320,
                'soundcraft.amp_decay':1000 if air else 850,'soundcraft.amp_sustain':.24 if air else .42,
                'soundcraft.amp_release':2200 if air else 1900,
                'soundcraft.filter_attack':1100 if air else 650,
                'soundcraft.filter_decay':1400 if air else 1500,
                'soundcraft.filter_release':2200 if air else 1900,
                # Native stem-calibrated compensation for the more recessed
                # sustain/wet blend; faders and their read lanes stay exact.
                'soundcraft.level':-3.5 if air else -7})
            for e in t.effects:
                if e.plugin_ref=='soundcraft:chorus':
                    e.parameters.update({'effect.wet':.34 if air else .32,'soundcraft.depth':.30 if air else .28})
                elif e.plugin_ref=='soundcraft:phaser':
                    e.parameters.update({'effect.wet':.06,'soundcraft.depth':.14})
                elif e.plugin_ref=='soundcraft:plate_reverb':
                    e.parameters.update({'soundcraft.decay_ms':3600 if air else 3800,
                        'soundcraft.width':.95,'soundcraft.low_cut':700 if air else 600,
                        'effect.wet':.31})
                    changed.append(e.id)
            delay=Effect('effect-space-'+('air' if air else 'pad')+'-echo','soundcraft:mod_delay',None,
                {'effect.bypass':0,'effect.wet':.10 if air else .12,
                 'soundcraft.time':60000/126*(.75 if air else 1),
                 'soundcraft.feedback':.26 if air else .30,'soundcraft.mod_rate':.2,
                 'soundcraft.mod_depth':0,'soundcraft.lpf':4500})
            t.effects.insert(len(t.effects)-1,delay)
            values=[(0,.10 if air else .12),(20,.14),(24,.20 if air else .22),
                (30,.22),(31.9,.16),(32,.07 if air else .08),(40,.10),(48,.12),(56,.08),(64,.08)]
            label='space-'+('air' if air else 'pad')+'-echo'
            p.automation.append(AutomationLane(label,delay.id,'effect.wet',[
                AutomationPoint(label+'-'+str(i),round(bar*BAR),v,'linear') for i,(bar,v) in enumerate(values)]))
        elif t.id in ('track-lead','track-arp'):
            for e in t.effects:
                if e.plugin_ref=='soundcraft:mod_delay':
                    e.parameters['soundcraft.feedback']=.48
                    e.parameters['effect.wet']=.06
                    changed.append(e.id)
                elif e.plugin_ref.endswith('reverb'):
                    e.parameters.update({'soundcraft.decay_ms':3600 if t.id=='track-lead' else 3400,
                        'soundcraft.width':.9,'effect.wet':.135})
                    changed.append(e.id)
        elif t.id=='track-harmony':t.controls['mixer.pan']=-.60
    # Preserve every original lane/point ID and tick; modify only mapped wet
    # values. Effect slots may shift, but adapter addresses follow effect IDs.
    for lane in p.automation:
        if lane.target_id not in changed or lane.parameter_id!='effect.wet':continue
        for point in lane.points:
            if lane.target_id in ('effect-lead-delay','effect-arp-delay'):
                point.value=min(.62,point.value+(.025 if point.value<.1 else .04))
            elif lane.target_id.startswith('effect-depth-') and lane.target_id.endswith('-plate') and lane.target_id!='effect-depth-lead-plate':
                point.value=min(.68,point.value+.06*(1-point.value))
            else:point.value=min(.68,point.value+.035*(1-point.value))


def _pulse(p):
    p.parameters += [ParameterSpec('soundcraft.type','normalized',0,1,0,['effect']),
                     ParameterSpec('soundcraft.freq','Hz',20,20000,1000,['effect'])]
    bass=next(t for t in p.tracks if t.id=='track-bass')
    inst=deepcopy(bass.instrument);inst.id='instrument-sub-pulse'
    inst.parameters.update({'soundcraft.osc1_wave':2/3,'soundcraft.osc2_wave':2/3,
        'soundcraft.osc_mix':0,'synth.cutoff_hz':120,'synth.resonance':0,
        'soundcraft.filter_env_amount':0,'soundcraft.amp_attack':8,'soundcraft.amp_decay':110,
        'soundcraft.amp_sustain':0,'soundcraft.amp_release':24,
        'soundcraft.filter_attack':8,'soundcraft.filter_decay':110,'soundcraft.filter_sustain':0,
        'soundcraft.filter_release':24,'soundcraft.velocity':.25,'soundcraft.level':-4})
    eq=Effect('effect-sub-pulse-eq','soundcraft:eq_7band',None,
        {'effect.bypass':0,'soundcraft.hpf_on':1,'soundcraft.hpf_freq':30,'soundcraft.hpf_slope':1/3,
         'soundcraft.lpf_on':0})
    lowpass=Effect('effect-sub-pulse-lowpass','soundcraft:eq_1band',None,
        {'effect.bypass':0,'soundcraft.type':4/6,'soundcraft.freq':140})
    t=Track(PULSE_ID,'Quiet late-offbeat sine pulse','midi',inst,
            {'mixer.gain_db':-18,'mixer.pan':0,'mixer.mute':0},[eq,lowpass],[],[],True)
    events=sorted((c.start+n.start,n.pitch) for c in bass.clips for n in c.notes)
    for bar in [*range(8,16),*range(32,48)]:
        notes=[]
        for beat in range(4):
            at=bar*BAR+beat*PPQ+3*PPQ//5+16
            # Use the actual most recent bass root in this beat, not an
            # invented sub-octave. Reset/phase controls are not exposed.
            pitches=[(tick,pitch) for tick,pitch in events if bar*BAR<=tick<=at]
            pitch=max(pitches)[1] if pitches else next(pitch for tick,pitch in events if tick>=bar*BAR)
            # Native on/off probes found a ~1.30 dB local cancellation at the
            # Bb1 turnaround. Leave that existing bass note alone; prune only
            # this optional new pulse, retaining C2/G1 support elsewhere.
            if pitch==34:continue
            notes.append(Note(f'pulse-note-{bar:02d}-{beat}',beat*PPQ+3*PPQ//5+16,180,pitch,72,0))
        t.clips.append(Clip(f'pulse-clip-{bar:02d}','Sine pulse / bar '+str(bar+1),'midi',bar*BAR,BAR,notes,None))
    p.tracks.append(t)
    # Programmed ghost duck, with no claim of kick-input routing. Notes begin
    # ~294 ms after the kick and release before the next beat (~69 ms gap).
    values=[(beat*PPQ+offset,-18+delta) for beat in range(256)
            for offset,delta in ((0,-16),(120,-16),(420,-3),(560,0),(900,0))]+[(p.length,-34)]
    p.automation.append(AutomationLane('pulse-programmed-duck',PULSE_ID,'mixer.gain_db',[
        AutomationPoint('pulse-duck-'+str(i),tick,v,'linear') for i,(tick,v) in enumerate(values)]))


def atmosphere_house(source=None,*,space=True,pulse=True):
    if type(space) is not bool or type(pulse) is not bool:raise ValidationError('space/pulse must be booleans')
    source=translation_house() if source is None else source;validate(source)
    if state_hash(source)!=SOURCE_HASH:raise ValidationError('Phase 10 requires the exact released Phase 9 native source')
    p=deepcopy(source)
    if space:_space(p)
    if pulse:_pulse(p)
    if not space and not pulse:return p
    p.name='Kuang / Pocket in a wider room'+(' / sine pulse' if pulse else '')
    p.metadata.update(production='space-and-pulse',atmosphere_source_hash=SOURCE_HASH,
        atmosphere_version='house-atmosphere-v1',atmosphere_variants=json.dumps({'space':space,'pulse':pulse},sort_keys=True),
        atmosphere_notes='Original notes/clip IDs exact; original automation identities/times retained, selected FX wet values edited. Distinct static pad ADSR, native delayed/reverberant tails and separate pans. Optional quiet mono sine, synth filter120Hz plus actual EQ1 LPF140Hz, EQ7 HPF30Hz. Programmed duck, no phase-reset/triggered-sidechain or oscillator-LFO claim. Human preference unknown.')
    validate(p)
    fingerprints=note_fingerprints(p)
    if any(fingerprints[k]!=v for k,v in note_fingerprints(source).items()):raise ValidationError('original MIDI changed')
    return p
