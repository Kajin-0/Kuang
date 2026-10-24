"""Conservative Phase15 rollback: incumbent pitches/sounds, real shared paths.

The rejected Phase14 palette/voicings are not an input to this transformation.
No note, existing instrument, insert, fader, pan or automation is rewritten.
Only declared post-fader routes, two auxes and provenance are added.
"""
from copy import deepcopy
from dataclasses import asdict
from .schema import Track,Effect,Send,ValidationError,validate,state_hash
from .ensemble_production import DRUMS,PAN_COMPENSATION_DB
from .production_host import add_spread,graph_contract


def repaired_house(source):
    validate(source)
    if source.locks or (source.bars,source.tempo_bpm,source.key_tonic,source.key_mode)!=(64,126,0,'minor'):
        raise ValidationError('unlocked full 64-bar incumbent at 126BPM C minor required')
    if len(source.tracks)!=13 or any(t.kind!='midi' or t.sends or not t.output_master or t.instrument.plugin_ref.startswith('vst3:') for t in source.tracks):
        raise ValidationError('unrouted Phase13 built-in/sampler incumbent required, not rejected Phase14')
    if not DRUMS<={t.id for t in source.tracks}:raise ValidationError('original six drum roles required')
    p=deepcopy(source)
    drum=Track('phase15-drum-sum','Repair drum sum','bus',None,
        {'mixer.gain_db':PAN_COMPENSATION_DB,'mixer.pan':0,'mixer.mute':0},
        [Effect('phase15-drum-glue','soundcraft:compressor',None,{'effect.bypass':0,'effect.wet':.25,
            'soundcraft.attack':22,'soundcraft.release':110,'soundcraft.threshold':-27,'soundcraft.makeup':0})],[],[],True)
    room=Track('phase15-shared-room','Repair shared room','bus',None,
        {'mixer.gain_db':PAN_COMPENSATION_DB,'mixer.pan':0,'mixer.mute':0},
        [Effect('phase15-room-effect','soundcraft:room_reverb',None,{'effect.bypass':0,'effect.wet':1,
            'soundcraft.decay_ms':800,'soundcraft.pre_delay':15,'soundcraft.low_cut':550,
            'soundcraft.damping':5000,'soundcraft.width':.8})],[],[],True)
    p.tracks.extend([drum,room]);add_spread(p,drum,1);add_spread(p,room,1)
    for t in p.tracks[:13]:
        if t.id in DRUMS:
            t.output_master=False;t.sends.append(Send('phase15-sum-'+t.id,drum.id,0,0,'post_fader'))
    for tid,gain in [('track-snare',-18),('track-harmony',-22),('track-lead',-24),('track-depth-pad',-26)]:
        next(t for t in p.tracks if t.id==tid).sends.append(Send('phase15-room-'+tid,room.id,gain,0,'post_fader'))
    p.metadata.update(phase15_source_hash=state_hash(source),phase15_production='Musical rollback to every Phase13 note and original source sound. No Phase14 Vitalium voices, octave lifts, pickups, filter edits or pad redesign. One true summed drum compressor and a quiet shared short room; original per-track effects and automation retained.',
        phase14_human_verdict='rejected: strange/incoherent tuning; Phase13 remains incumbent',phase15_human_preference='unreviewed')
    graph_contract(p)
    return p,{'version':'musical-repair-1','source_hash':state_hash(source),'candidate_hash':state_hash(p),
        'original_tracks_before_routing':[asdict(t) for t in source.tracks],
        'all_original_note_fields_exact':True,'all_original_instruments_inserts_mixer_lanes_exact':True,
        'original_1536_note_ids_exact':True,'added_notes':[],'removed_notes':[],'voicing_changes':[],
        'phase14_palette_used':False,'phase14_human_rejected':True,'human_preference':'unreviewed',
        'quality_upgrade_claimed':False,'incumbent':'Phase13 B','routing':'six post-fader sources, direct Main off, actual stereo compressor aux; four quiet sends to an actual shared room'}


def zero_pitch_bend_operations(project,patches):
    """Explicit opt-in workaround, not MIDI transposition or a legacy default.

    Disables bend expression on selected reviewed Vitalium instances only.
    Caller must apply the returned typed edits through Engine/native scopes.
    Actual audio calibration remains required; no generic VST tuning promise.
    """
    from .external_synth import read_patch,PLUGIN_ID
    from .transactions import SetParameter
    validate(project);ops=[]
    if not patches:raise ValidationError('explicit reviewed external patch targets required')
    for tid,path in patches.items():
        t=next((t for t in project.tracks if t.id==tid),None)
        if t is None or t.instrument is None or t.instrument.plugin_ref!=PLUGIN_ID:raise ValidationError('reviewed Vitalium instance required')
        _,rows=read_patch(path);r=[r for r in rows if r['name']=='Pitch Bend Range']
        if len(r)!=1 or r[0]['steps']!=49 or r[0]['scale']!=48:raise ValidationError('pitch bend control contract changed')
        key=r[0]['canonical_id'];spec=next((s for s in project.parameters if s.id==key),None)
        if spec is None or (spec.unit,spec.minimum,spec.maximum,spec.targets)!=('normalized',0,1,['instrument']) or key not in t.instrument.parameters:raise ValidationError('pitch bend normalized registry mismatch')
        ops.append(SetParameter('set_parameter',t.instrument.id,key,0))
    return ops
