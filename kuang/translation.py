"""One opt-in kick/bass translation mix over exact Phase 8, schema 0.1."""

from copy import deepcopy

from .depth import note_fingerprints
from .gestures import gesture_house
from .schema import ParameterSpec, ValidationError, state_hash, validate

SOURCE_HASH='22a3d95c5479dbdd312db6aefe803e0e600ba7ecd62350060c2e1880759ca2a7'


def translation_house(source=None):
    source=gesture_house() if source is None else source
    validate(source)
    if state_hash(source)!=SOURCE_HASH:
        raise ValidationError('translation mix requires the exact released Phase 8 song')
    p=deepcopy(source);p.name='Kuang / Pocket with body'
    p.parameters += [ParameterSpec('soundcraft.high_mid_freq','Hz',500,20000,4000,['effect']),
                     ParameterSpec('soundcraft.high_mid_gain','dB',-24,24,0,['effect'])]
    for t in p.tracks:
        if t.id=='track-kick':
            t.instrument.parameters.update({'soundcraft.kick_decay':280,'soundcraft.level':-7})
            eq,comp,sat=t.effects
            eq.parameters.update({'soundcraft.hpf_freq':30,'soundcraft.low_mid_freq':240,
                'soundcraft.low_mid_gain':-3.5,'soundcraft.high_mid_freq':2600,'soundcraft.high_mid_gain':1.5})
            comp.parameters.update({'soundcraft.threshold':-20,'soundcraft.attack':8,
                                    'soundcraft.release':75,'soundcraft.makeup':1})
            sat.parameters.update({'soundcraft.drive':5,'effect.wet':.36,'soundcraft.output':-2})
        elif t.id=='track-bass':
            # Single saw adds even harmonics (130/260 Hz around C2) without
            # another detuned sub oscillator. Static ADSR; existing beat duck
            # and every note/release gap stay unchanged.
            t.instrument.parameters.update({'soundcraft.osc1_wave':0,'soundcraft.osc_mix':0,
                'synth.cutoff_hz':650,'soundcraft.filter_env_amount':.18,
                'soundcraft.amp_decay':160,'soundcraft.amp_sustain':.24,'soundcraft.level':-7})
            eq,comp,sat=t.effects
            eq.parameters.update({'soundcraft.low_mid_freq':180,'soundcraft.low_mid_gain':0})
            comp.parameters.update({'soundcraft.threshold':-25,'soundcraft.attack':12,
                                    'soundcraft.release':95,'soundcraft.makeup':1})
            sat.parameters.update({'soundcraft.drive':7,'effect.wet':.45,
                                   # Calibrated against the same-MIDI native
                                   # stem: the single saw patch is ~5 dB quieter.
                                   'soundcraft.output':1.5,'soundcraft.tone':4000})
        elif t.id=='track-harmony':
            t.effects[0].parameters['soundcraft.low_mid_gain']=-3
            t.controls['mixer.pan']=-.48
        elif t.id=='track-arp':
            t.controls['mixer.pan']=.60
    p.metadata.update(production='translation-mix',translation_source_hash=SOURCE_HASH,
        translation_version='house-translation-v1',translation_notes='All MIDI and all Phase 8 automation exact. Shorter kick, slower transient compression, single-saw harmonic bass, compensated native levels, small stab low-mid cut and upper-part pan separation. No sub boost, tuning-unit fiction, new synth, sampler dependency or master-bus claim. Human preference unknown.')
    validate(p)
    if note_fingerprints(p)!=note_fingerprints(source):raise ValidationError('translation mix changed notes')
    return p
