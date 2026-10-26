"""Opt-in house mix/master recipe; immutable music and prepared instruments.

No loudness target or perceptual score. Source processing is separate from the
terminal master. Physical units use the existing strict registry; compressor
ratio stays at the verified native4:1 default because schema0.1 has no ratio
unit. Parallel wet blends are actual DSP controls, not invented ratio units.
"""
from copy import deepcopy
from dataclasses import asdict
import math

from .schema import ParameterSpec,Effect,AutomationLane,AutomationPoint,ValidationError,state_hash,validate
from .midi import export_bytes
from .master_bus import attach_terminal,terminal_projection,SINK_KEY
from .production_host import graph_contract

SOURCE_HASH='94bdf147880f2b062213a370e889a55df23839d80679f5da4ae68084e91c9600'
VERSION='house-record-mix-1'
BALANCE={'track-arp': -4.673478770096194, 'track-bass': 1.025768953677743, 'track-depth-air': 0.0, 'track-depth-pad': -1.8936892960781964, 'track-harmony': -0.49147533997314286, 'track-kick': 0.0, 'track-lead': -7.7383501276143685}


def register(p,key,unit,lo,hi,default):
    wanted=ParameterSpec(key,unit,lo,hi,default,['effect']);old=next((s for s in p.parameters if s.id==key),None)
    if old is None:p.parameters.append(wanted)
    elif old!=wanted:raise ValidationError('mix registry collision '+key)


def _extra_registry(p):
    for row in [('input_gain','dB',-24,24,0),('low_shelf_freq','Hz',20,1000,100),('low_shelf_gain','dB',-24,24,0),
        ('mid_freq','Hz',100,8000,1000),('mid_gain','dB',-24,24,0),('high_shelf_freq','Hz',1000,20000,8000),
        ('knee','dB',0,24,6),('sc_hpf_on','boolean',0,1,0),('sc_hpf_freq','Hz',20,500,100),
        ('lookahead','ms',0,10,0),('ceiling','dB',-30,0,-.3)]:
        key,unit,lo,hi,default=row;old=next((s for s in p.parameters if s.id=='soundcraft.'+key),None)
        if old is None:register(p,'soundcraft.'+key,unit,lo,hi,default)
        elif old.unit!=unit or not old.minimum<=lo<=hi<=old.maximum:raise ValidationError('incompatible physical mix registry '+key)


def mixed_record(source,*,balance=None,master=True):
    validate(source);graph_contract(source)
    if source.locks or state_hash(source)!=SOURCE_HASH or type(master) is not bool:raise ValidationError('exact unlocked Phase19 source and explicit master bool required')
    offsets=deepcopy(BALANCE)
    if balance is not None:
        if type(balance) is not dict or set(balance)!=set(offsets):raise ValidationError('complete role calibration required')
        if any(type(v) not in (int,float) or not math.isfinite(v) or not -12<=v<=12 for v in balance.values()):raise ValidationError('bounded finite role calibration required')
        offsets.update(balance)
    p=deepcopy(source);p.id='project-phase20-house-record'
    _extra_registry(p);by={t.id:t for t in p.tracks};fx={e.id:e for t in p.tracks for e in t.effects};edits=[]
    def settings(eid,reason,**kw):
        e=fx[eid];before=deepcopy(e.parameters)
        for key,v in kw.items():e.parameters['effect.wet' if key=='wet' else 'soundcraft.'+key]=v
        edits.append({'effect':eid,'before':before,'after':deepcopy(e.parameters),'reason':reason})
    settings('effect-kick-compression','Control the short kick spike before bus density; retain the source sample',attack=4,release=85,threshold=-22,makeup=0,wet=.8)
    settings('effect-bass-eq','Restore audible bass body without a sub boost',low_shelf_freq=80,low_shelf_gain=-1,low_mid_freq=180,low_mid_gain=1,mid_freq=350,mid_gain=1)
    settings('effect-bass-compression','Let the original note attack/body breathe instead of aggressive serial attenuation',attack=18,release=110,threshold=-21,makeup=0,wet=.7)
    settings('effect-harmony-eq','Recover lower chord fundamentals; preserve performed filter timing',hpf_freq=100,low_mid_gain=.5)
    settings('effect-harmony-compression','Retain stab articulation with less full-wet4:1 compression',attack=18,release=110,threshold=-22,makeup=0,wet=.35)
    for role in ('lead','arp'):
        settings('effect-'+role+'-compression','Preserve the note front instead of0.2ms full-wet compression',attack=8,release=95,threshold=-22,makeup=0,wet=.4)
        settings('effect-'+role+'-eq','Keep body below the foreground presence range',hpf_freq=210 if role=='lead' else 240)
    settings('effect-depth-pad-eq','Retain pad level while allowing voiced low-mid texture',hpf_freq=240,low_mid_gain=-1)
    settings('phase15-drum-glue','Real summed parallel compression for drum body, not a new duplicate dry path',threshold=-30,attack=12,release=120,makeup=2,wet=.5,sc_hpf_on=1,sc_hpf_freq=80)
    drum_sat=Effect('phase20-drum-color','soundcraft:saturator',None,
        {'effect.bypass':0,'effect.wet':.15,'soundcraft.drive':2,'soundcraft.output':-1,'soundcraft.tone':9000})
    by['phase15-drum-sum'].effects.append(drum_sat)
    settings('phase17-dark-eq','Retain midrange in the stereo depth path, filter low bass',hpf_freq=450,lpf_freq=6000)
    settings('phase17-dark-plate','Sustained darker depth, separated from dry attacks',decay_ms=2700,low_cut=450,damping=6000)
    settings('phase15-room-effect','One coherent room behind the foreground',decay_ms=780,low_cut=500,damping=7000)
    send_changes=[]
    boosts={'phase15-room-track-snare':2,'phase15-room-track-harmony':5,'phase15-room-track-lead':8,
        'phase17-send-dark-track-depth-pad':6,'phase17-send-dark-track-depth-air':4,'phase17-send-dark-track-lead':11,
        'phase17-send-echo-track-harmony':4,'phase17-send-echo-track-lead':6,'phase17-send-echo-track-arp':3}
    for t in p.tracks:
        for s in t.sends:
            if s.id in boosts:
                before=s.gain_db;s.gain_db+=boosts[s.id];send_changes.append({'send':s.id,'before_db':before,'after_db':s.gain_db,'reason':'Depth/phrase tail behind the unchanged foreground; original MIDI throw gates retained'})
    # Change resting HPF values AND existing lanes; never hide an overridden edit.
    for lane in p.automation:
        if lane.parameter_id=='soundcraft.hpf_freq' and lane.target_id in ('effect-harmony-eq','effect-lead-eq','effect-arp-eq'):
            floor=fx[lane.target_id].parameters['soundcraft.hpf_freq'];oldfloor=next(e.parameters['soundcraft.hpf_freq'] for t in source.tracks for e in t.effects if e.id==lane.target_id)
            for x in lane.points:x.value=max(floor,x.value-(oldfloor-floor))
    for tid,offset in offsets.items():
        by[tid].controls['mixer.gain_db']+=offset
        for lane in p.automation:
            if lane.target_id==tid and lane.parameter_id=='mixer.gain_db':
                for x in lane.points:x.value+=offset
    # Explicit -3dB output staging without changing compressor detector input:
    # direct synth faders and the drum-sum output move together. Drum MIDI
    # source faders stay put; their room send is reduced to match the synth
    # sends. Wet inputs therefore move -3dB too, rather than being attenuated
    # twice by an additional return-fader change.
    staged={t.id for t in p.tracks if t.kind=='midi' and t.output_master}|{'phase15-drum-sum'}
    for t in p.tracks:
        if t.id in staged:t.controls['mixer.gain_db']-=3
        for s in t.sends:
            if s.id=='phase15-room-track-snare':
                before=s.gain_db;s.gain_db-=3;send_changes.append({'send':s.id,'before_db':before,'after_db':s.gain_db,'reason':'Match the explicit -3dB output staging of synth-fed room inputs'})
    for lane in p.automation:
        if lane.target_id in staged and lane.parameter_id=='mixer.gain_db':
            for x in lane.points:x.value-=3
    # Actual first-hit detector startup is not a MIDI accent. The native
    # per-kick limiter trial did not remove it and was pruned. Start the fader
    # at its corrected value (not only an automation point, which could smooth
    # from the wrong initial gain), hold20ms and restore the source level by
    #120ms. Every later note/velocity remains exact.
    kick=by['track-kick'];resting=kick.controls['mixer.gain_db'];kick.controls['mixer.gain_db']=resting-12
    tick=lambda ms:round(ms/1000*p.tempo_bpm/60*p.ppq)
    startup=AutomationLane('phase20-kick-startup',kick.id,'mixer.gain_db',[
        AutomationPoint('phase20-kick-start',0,resting-12,'linear'),
        AutomationPoint('phase20-kick-hold',tick(20),resting-12,'linear'),
        AutomationPoint('phase20-kick-restored',tick(120),resting,'linear'),
        AutomationPoint('phase20-kick-end',p.length,resting,'linear')])
    p.automation.append(startup)
    if master:
        chain=[Effect('phase20-master-eq','soundcraft:eq_7band',None,{'effect.bypass':0,'soundcraft.input_gain':0,'soundcraft.low_shelf_freq':90,'soundcraft.low_shelf_gain':-.5,'soundcraft.high_shelf_freq':8000,'soundcraft.high_shelf_gain':.75}),
            Effect('phase20-master-glue','soundcraft:compressor',None,{'effect.bypass':0,'effect.wet':.3,'soundcraft.threshold':-23,'soundcraft.attack':30,'soundcraft.release':150,'soundcraft.makeup':0,'soundcraft.knee':4}),
            Effect('phase20-master-limiter','soundcraft:maximizer',None,{'effect.bypass':0,'soundcraft.threshold':-10,'soundcraft.ceiling':-1.8,'soundcraft.release':110})]
        p=attach_terminal(p,chain,identity='phase20-stereo-master')
    p.metadata.update(phase20_source_hash=SOURCE_HASH,phase20_recipe=VERSION,phase20_preference='unreviewed',
        phase20_scope='Sound/role balance, filtering, real drum-sum parallel dynamics, shared depth and terminal native master; every source note/patch/sample exact. No loudness target or input-triggered sidechain.')
    if export_bytes(p)!=export_bytes(source) or p.sections!=source.sections:raise ValidationError('record mix changed the music')
    for a,b in zip(source.tracks,p.tracks):
        if (a.id,a.instrument,a.clips)!=(b.id,b.instrument,b.clips):raise ValidationError('record mix changed note or instrument identity')
    terminal_projection(p) if master else graph_contract(p)
    return p,{'version':VERSION,'source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'MIDI_bytes_exact':True,
        'note_ids_fields_clips_sections_instruments_exact':True,'all_source_tracks_exact_order':True,
        'effect_changes':edits,'send_changes':send_changes,'role_calibration_db':offsets,
        'added_effects':[asdict(drum_sat)],'startup_gain_correction':asdict(startup),'output_staging_db':-3,'output_staged_track_ids':sorted(staged),'native_master':master,'native_limiter_true_peak_aware_claimed':False,
        'master_effects':[asdict(e) for e in p.tracks[-1].effects] if master else [],
        'tracks_before':[asdict(t) for t in source.tracks],'automation_before':[asdict(a) for a in source.automation],
        'automation_after':[asdict(a) for a in p.automation],'human_preference':'unreviewed'}
