"""Authored Phase14 ensemble: foreground chords, mono bass, shared depth.

This is an opt-in full-song production proposal, not a perceptual optimizer.
Kick/drum MIDI and the three-note call stay exact. Narrow voicing lifts and
answer pickups are explicit; static patches and performed FX have distinct roles.
"""
import json
from copy import deepcopy
from dataclasses import asdict

from .external_synth import bound_project
from .production_host import add_send_trim,add_spread,trim_id,graph_contract
from .schema import BAR,Track,Effect,Send,AutomationLane,AutomationPoint,Note,ValidationError,state_hash,validate

VOICES={'track-bass':'bass','track-harmony':'stab','track-lead':'lead','track-depth-pad':'pad'}
DRUMS={'track-kick','track-snare','track-snare.p38','track-hats','track-hats.p46','track-percussion'}
PAN_COMPENSATION_DB=6.020599913279624


def isolate(project,track_ids):
    """Actual MIDI stems keep their reachable shared graph and lane owners."""
    graph_contract(project);ids=set(track_ids)
    midi={t.id for t in project.tracks if t.kind=='midi'}
    if not ids or not ids<=midi:raise ValidationError('explicit existing sounding MIDI stem IDs required')
    byid={t.id:t for t in project.tracks};pending=list(ids)
    while pending:
        for send in byid[pending.pop()].sends:
            if send.target_track_id not in ids:ids.add(send.target_track_id);pending.append(send.target_track_id)
    p=deepcopy(project);p.tracks=[t for t in p.tracks if t.id in ids]
    owners={x for t in p.tracks for x in (t.id,*([t.instrument.id] if t.instrument else []),*(e.id for e in t.effects))}
    p.automation=[a for a in p.automation if a.target_id in owners]
    owned=owners|{c.id for t in p.tracks for c in t.clips}|{n.id for t in p.tracks for c in t.clips for n in c.notes}
    p.locks=[l for l in p.locks if l.target_id in owned]
    graph_contract(p);return p


def build_ensemble(source,patches):
    validate(source)
    if source.locks:raise ValidationError('authored whole-ensemble production requires an unlocked source; scoped edits retain Engine locks')
    if (source.bars,source.tempo_bpm,source.key_tonic,source.key_mode)!=(64,126,0,'minor') or set(patches)!=set(VOICES):
        raise ValidationError('explicit four-voice patch set and full C-minor source required')
    if 'phase14_source_hash' in source.metadata:raise ValidationError('ensemble source already produced')
    p=deepcopy(source);old={n.id:asdict(n) for t in p.tracks for c in t.clips for n in c.notes};added=[]
    byid={t.id:t for t in p.tracks}
    # Answer the second four bars of each drop phrase in a brighter register;
    # keep bass roots, all drum events and every original main-call field.
    for c in byid['track-harmony'].clips:
        for n in c.notes:
            bar=(c.start+n.start)//BAR
            if 32<=bar<48 and bar%8>=4 and n.pitch in (62,63):n.pitch+=12
            if 32<=bar<48:
                n.velocity=min(127,n.velocity+(4 if bar%4==0 else -3 if bar%4==3 else 0))
    for bar,pitches in [(15,(75,74)),(23,(79,77)),(39,(79,82)),(47,(75,74))]:
        t=byid['track-arp'];c=next(c for c in t.clips if c.start<=bar*BAR<c.start+c.length)
        for j,pitch in enumerate(pitches):
            n=Note('phase14-answer-'+str(bar)+'-'+str(j),bar*BAR+2880+j*480-c.start,180,pitch,68-j*7,0)
            if any(x.pitch==pitch and x.channel==n.channel and x.start<n.start+n.duration and n.start<x.start+x.duration for x in c.notes):
                raise ValidationError('authored response collides with source motif')
            c.notes.append(n);added.append({'track':t.id,'clip':c.id,'note':asdict(n)})
    p=bound_project(p,patches);byid={t.id:t for t in p.tracks}
    p.metadata['external_synth_notes']='Phase14 curated original Vitalium voices, numeric overrides and component state. Explicit harmonic updates/pickups in production receipt; original call and drum groove protected. Not official Vital.'
    removed=set()
    # Cohesion comes from real shared returns, replacing stacked individual
    # room/plate/echo/phaser chains. Keep the original spectral EQ identity.
    for tid in ('track-harmony','track-lead','track-arp','track-depth-pad','track-depth-air'):
        t=byid[tid];keep=[e for e in t.effects if e.plugin_ref=='soundcraft:eq_7band']
        removed.update(e.id for e in t.effects if e not in keep);t.effects=keep
    for tid in ('track-snare','track-snare.p38'):
        t=byid[tid];removed.update(e.id for e in t.effects if e.plugin_ref=='soundcraft:room_reverb');t.effects=[e for e in t.effects if e.plugin_ref!='soundcraft:room_reverb']
    t=byid['track-bass'];removed.update(e.id for e in t.effects if e.plugin_ref=='soundcraft:compressor');t.effects=[e for e in t.effects if e.plugin_ref!='soundcraft:compressor']
    for e in t.effects:
        if e.plugin_ref=='soundcraft:saturator':e.parameters.update({'soundcraft.drive':3,'effect.wet':.25,'soundcraft.output':-1})
    p.automation=[a for a in p.automation if a.target_id not in removed]
    # Restore chord fundamentals instead of filtering away Eb3/G3/Bb3.
    eq=byid['track-harmony'].effects[0];eq.parameters.update({'soundcraft.hpf_freq':150,'soundcraft.hpf_slope':0,'soundcraft.low_mid_gain':-1.5})
    eq=byid['track-depth-pad'].effects[0];eq.parameters.update({'soundcraft.hpf_freq':240,'soundcraft.lpf_freq':4800,'soundcraft.low_mid_gain':-2})
    byid['track-harmony'].controls['mixer.pan']=0
    byid['track-depth-pad'].controls['mixer.pan']=-.15
    byid['track-lead'].controls['mixer.pan']=.10
    for tid,value in [('track-harmony',.75),('track-lead',.65),('track-depth-pad',.80)]:add_spread(p,byid[tid],value)
    byid['track-arp'].controls['mixer.pan']=.45
    byid['track-depth-air'].controls.update({'mixer.pan':.60,'mixer.gain_db':-6})
    a=byid['track-arp'].instrument.parameters
    a.update({'soundcraft.amp_attack':2,'soundcraft.amp_decay':180,'soundcraft.amp_sustain':.06,'soundcraft.amp_release':85,
        'soundcraft.filter_decay':150,'soundcraft.osc_mix':.50,'synth.cutoff_hz':2600})
    air=byid['track-depth-air'].instrument.parameters
    air.update({'soundcraft.amp_attack':650,'soundcraft.amp_release':1400,'soundcraft.amp_sustain':.35,'synth.cutoff_hz':3500})

    def bus(tid,name,effects,gain=0):
        t=Track(tid,name,'bus',None,{'mixer.gain_db':gain,'mixer.pan':0,'mixer.mute':0},effects,[],[],True);p.tracks.append(t);byid[tid]=t;return t
    bus('phase14-drum-sum','Producer drum sum',[Effect('phase14-drum-glue','soundcraft:compressor',None,
        {'effect.bypass':0,'effect.wet':.35,'soundcraft.attack':22,'soundcraft.release':110,'soundcraft.threshold':-27,'soundcraft.makeup':0})],PAN_COMPENSATION_DB)
    bus('phase14-short-room','Shared short room',[Effect('phase14-short-reverb','soundcraft:room_reverb',None,
        {'effect.bypass':0,'effect.wet':1,'soundcraft.decay_ms':650,'soundcraft.pre_delay':11,'soundcraft.low_cut':500,'soundcraft.damping':5600,'soundcraft.width':.82})],PAN_COMPENSATION_DB)
    bus('phase14-dark-space','Shared dark plate',[Effect('phase14-dark-reverb','soundcraft:plate_reverb',None,
        {'effect.bypass':0,'effect.wet':1,'soundcraft.decay_ms':2600,'soundcraft.pre_delay':35,'soundcraft.low_cut':650,'soundcraft.damping':4700,'soundcraft.width':.80})],PAN_COMPENSATION_DB-3)
    bus('phase14-echo','Shared dotted echo',[Effect('phase14-echo-effect','soundcraft:mod_delay',None,
        {'effect.bypass':0,'effect.wet':1,'soundcraft.time':357.14285714285717,'soundcraft.feedback':.32,'soundcraft.lpf':5200,'soundcraft.mod_rate':.3,'soundcraft.mod_depth':0})],PAN_COMPENSATION_DB-2)
    for bid in ('phase14-drum-sum','phase14-short-room','phase14-dark-space','phase14-echo'):add_spread(p,byid[bid],1)
    def send(tid,bid,db,label):
        s=Send('phase14-send-'+label,bid,db,0,'post_fader');byid[tid].sends.append(s);return s
    for tid in sorted(DRUMS):
        byid[tid].output_master=False;send(tid,'phase14-drum-sum',0,'sum-'+tid)
    for tid,db in [('track-snare',-13),('track-snare.p38',-20),('track-hats.p46',-24),('track-harmony',-12),('track-lead',-20),('track-arp',-18)]:
        send(tid,'phase14-short-room',db,'short-'+tid)
    for tid,db in [('track-depth-pad',-9),('track-depth-air',-14),('track-lead',-20)]:
        send(tid,'phase14-dark-space',db,'dark-'+tid)

    def lane(tid,param,points,prefix):
        p.automation[:]=[a for a in p.automation if not (a.target_id==tid and a.parameter_id==param)]
        # Points are bar positions, not a new timing unit in canonical state.
        times={round(bar*BAR):value for bar,value in points}
        p.automation.append(AutomationLane(prefix,tid,param,[AutomationPoint(prefix+'-'+str(i),tick,value,'linear') for i,(tick,value) in enumerate(sorted(times.items()))]))
    lane('effect-harmony-eq','soundcraft.hpf_freq',[(0,150),(16,150),(23.8,750),(24,150),(31.7,500),(32,150),(48,150),(64,150)],'phase14-stab-hpf')
    lane('effect-harmony-eq','soundcraft.lpf_freq',[(0,1000),(8,1600),(10,2300),(11.8,3400),(12,1800),(15.8,4200),
        (16,1800),(20,3600),(23.8,8000),(24,1000),(28,1200),(31.7,4000),(32,5600),(35.8,3400),
        (36,6500),(39.8,4200),(40,7000),(43.8,3800),(44,6200),(47.8,4500),(48,2200),(56,1200),(64,1000)],'phase14-stab-tone')
    lane('effect-bass-eq','soundcraft.lpf_freq',[(0,1000),(8,1300),(15.7,1800),(16,1000),(23.8,2300),(24,1000),(31.8,1500),(32,1800),(36,1300),(40,2300),(44,1800),(48,1300),(56,1000),(64,1000)],'phase14-bass-tone')
    lane('effect-depth-pad-eq','soundcraft.lpf_freq',[(0,1800),(16,2800),(24,1700),(28,3300),(31.8,6000),(32,3400),(40,4500),(48,2200),(56,1400),(64,1000)],'phase14-pad-tone')
    # Stable, scheduled return ducking, explicitly not input-triggered sidechain.
    dark=byid['phase14-dark-space'];duck=[]
    for beat in range(256):
        bar=beat/4;v=PAN_COMPENSATION_DB+(-1 if 24<=bar<32 else -3)
        duck.extend([(bar,v-5),(bar+.035,v-5),(bar+.15,v),(bar+.249,v)])
    lane(dark.id,'mixer.gain_db',duck+[(64,PAN_COMPENSATION_DB-12)],'phase14-return-breath')
    for tid in ('track-lead','track-arp'):
        s=send(tid,'phase14-echo',-12,'echo-'+tid);key=add_send_trim(p,byid[tid],s,-60)
        points=[(0,-60),(64,-60)]
        for c in byid[tid].clips:
            for n in c.notes:
                # The main call's F endings, existing Bb/G answers and the new
                # last pickup note receive discrete, tempo-aligned throws.
                if (tid=='track-lead' and n.pitch==65) or (tid=='track-arp' and (n.pitch==67 or n.id.endswith('-1'))):
                    tick=c.start+n.start
                    points.extend([(max(0,tick-24)/BAR,-60),(tick/BAR,0),((tick+380)/BAR,0),((tick+460)/BAR,-60)])
        lane(tid,key,points,'phase14-throw-'+tid)
    p.metadata.update(phase14_source_hash=state_hash(source),phase14_production='Warm articulated chord foreground; mono layered bass; four original Vitalium voices; real shared room/dark plate/dotted echo and summed drum compression. Original call/drum MIDI protected; explicit upper voicing lifts and response pickups.')
    validate(p);graph_contract(p)
    protected={n.id:asdict(n) for t in source.tracks if t.id in DRUMS or t.id in ('track-bass','track-lead') for c in t.clips for n in c.notes}
    after={n.id:asdict(n) for t in p.tracks for c in t.clips for n in c.notes}
    if any(after.get(k)!=v for k,v in protected.items()):raise ValidationError('production changed protected groove/call')
    changed=[{'id':k,'before':v,'after':after[k]} for k,v in old.items() if after[k]!=v]
    return p,{'version':'phase14-production-1','source_hash':state_hash(source),'candidate_hash':state_hash(p),
        'protected_drum_bass_and_main_call_notes_exact':True,'changed_notes':changed,'added_response_notes':added,
        'removed_note_ids':[],'source_song_spec_exact':p.metadata['song_spec']==source.metadata['song_spec'],
        'removed_insert_ids':sorted(removed),'original_source_tracks':[asdict(t) for t in source.tracks],
        'new_graph':{'buses':[t.id for t in p.tracks if t.kind=='bus'],'send_trim_meaning':'native send gain = Send.gain_db + channel-owned dB trim',
                     'sidechain':'scheduled gain on the dark return, not input-triggered'},
        'human_preference':'unreviewed','quality_established':False}
