"""Opt-in sound-only production. Exact approved Phase15 performance is sealed.

No new notes, clips, voicings, song sections or arrangement. Deliberate changes
are limited to selected original patches and their documented sound/mix path.
"""
from copy import deepcopy
from dataclasses import asdict
from .external_synth import bound_project
from .midi import export_bytes
from .production_host import add_spread, graph_contract
from .schema import ValidationError, state_hash, validate
from .studio_palette import TRACKS

SOURCE_HASH = '3183aaf4c60ef2552560b1bd96083d8f3c483b6908d02faffe9db75d1fc63f48'
# Post-insert calibration against the same eight-bar drop. Constant offsets
# move every gain-lane point together, preserving its exact duck/release shape.
MIX_TRIMS = {'track-bass': -3.1077318064, 'track-harmony': -9.3041289158,
             'track-lead': -.6116083569, 'track-depth-pad': 0.}


def performance(p):
    """Complete musical fields, including clip ownership/order and note IDs."""
    return {'tempo_bpm': p.tempo_bpm, 'bars': p.bars, 'ppq': p.ppq,
            'key': [p.key_tonic, p.key_mode], 'sections': [asdict(s) for s in p.sections],
            'tracks': [{'id': t.id, 'kind': t.kind, 'clips': [asdict(c) for c in t.clips]}
                       for t in p.tracks], 'song_spec': p.metadata['song_spec']}


def sound_palette(source, patches):
    validate(source)
    if state_hash(source) != SOURCE_HASH or source.locks:
        raise ValidationError('exact unlocked approved Phase15 B required')
    if type(patches) is not dict or not patches or not set(patches) <= set(TRACKS):
        raise ValidationError('explicit existing studio voice assignments required')
    p = bound_project(source, patches)
    byid = {t.id: t for t in p.tracks}
    # Keep the two proven shared auxes and all sample drums exact. The original
    # per-track sweeps/echo throws/duck lanes also stay intact. Wider positions
    # preserve actual stereo inputs instead of collapsing both channels to one.
    pans = {'track-harmony': (-.12, .70), 'track-lead': (.12, .55),
            'track-depth-pad': (-.12, .80)}
    for tid in patches:
        if tid in pans:
            center, spread = pans[tid]
            byid[tid].controls['mixer.pan'] = center
            add_spread(p, byid[tid], spread)
        trim = MIX_TRIMS[tid]
        byid[tid].controls['mixer.gain_db'] += trim
        for lane in p.automation:
            if lane.target_id == tid and lane.parameter_id == 'mixer.gain_db':
                for point in lane.points: point.value += trim
    if 'track-harmony' in patches:
        # Keep the struck chord fundamentals instead of high-passing their
        # body away. Existing 400..1000Hz tension peaks and timestamps stay.
        eq = next(e for e in byid['track-harmony'].effects if e.id == 'effect-harmony-eq')
        eq.parameters.update({'soundcraft.hpf_freq':150, 'soundcraft.hpf_slope':0,
                              'soundcraft.low_mid_gain':-1.5})
        compressor = next(e for e in byid['track-harmony'].effects if e.id == 'effect-harmony-compression')
        compressor.parameters.update({'soundcraft.attack':8,'soundcraft.threshold':-28,'soundcraft.makeup':0})
        for lane in p.automation:
            if lane.target_id == eq.id and lane.parameter_id == 'soundcraft.hpf_freq':
                for point in lane.points:
                    if point.value == 280: point.value = 150
    p.metadata['phase16_source_hash'] = SOURCE_HASH
    p.metadata['phase16_palette'] = 'Original pitch-centered Vitalium sound-only experiment; exact Phase15 music; no factory content; human preference unreviewed.'
    validate(p); graph_contract(p)
    if performance(p) != performance(source) or export_bytes(p) != export_bytes(source):
        raise ValidationError('sound-only proposal changed approved musical performance')
    # No timestamps, interpolation, lane IDs or ownership changes. Only the
    # explicitly declared gain offsets and stab HPF floor may change values.
    allowed = deepcopy(source.automation)
    for lane in allowed:
        if lane.target_id in patches and lane.parameter_id == 'mixer.gain_db':
            for point in lane.points: point.value += MIX_TRIMS[lane.target_id]
        if 'track-harmony' in patches and lane.target_id == 'effect-harmony-eq' and lane.parameter_id == 'soundcraft.hpf_freq':
            for point in lane.points:
                if point.value == 280: point.value = 150
    if p.automation != allowed:
        raise ValidationError('sound-only proposal altered undeclared automation')
    changes = []
    for t, u in zip(source.tracks, p.tracks):
        if asdict(t) != asdict(u):
            changes.append({'track': t.id, 'instrument_before': asdict(t.instrument),
                            'instrument_after': asdict(u.instrument),
                            'controls_before': t.controls, 'controls_after': u.controls,
                            'effects_before': [asdict(e) for e in t.effects], 'effects_after':[asdict(e) for e in u.effects],
                            'effects_exact': t.effects == u.effects, 'routing_exact': t.sends == u.sends and t.output_master == u.output_master})
    return p, {'version': 'phase16-sound-only-1', 'source_hash': SOURCE_HASH,
               'candidate_hash': state_hash(p), 'exact_performance_and_MIDI': True,
               'note_count': sum(len(c.notes) for t in p.tracks for c in t.clips),
               'automation_changes':[{'before':asdict(a),'after':asdict(b)} for a,b in zip(source.automation,p.automation) if a!=b],
               'mix_trims_db':{t:MIX_TRIMS[t] for t in patches}, 'changes': changes,
               'human_quality_gate': 'unreviewed; numeric acceptance is musical integrity only'}
