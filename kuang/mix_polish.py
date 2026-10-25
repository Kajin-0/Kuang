"""Phase17 mix-only proposal on the human-approved Phase16 performance/palette.

All synthesis and sample state is immutable. Real one-level aux returns replace
stacked individual spaces. Ducking is scheduled from MIDI kick onsets, never
represented as an external-audio sidechain. No mastering or waveform edits.
"""
from copy import deepcopy
from dataclasses import asdict
from .schema import (BAR, Track, Effect, Send, AutomationLane, AutomationPoint,
                     ValidationError, validate, state_hash)
from .production_host import add_spread, add_send_trim, graph_contract
from .ensemble_production import PAN_COMPENSATION_DB
from .sound_palette import performance
from .midi import export_bytes

SOURCE_HASH = '8c4378bc22acd41aedf10d63503ed6af7043a28f36d554879b9f2b38e1df38b8'
SPACE_TRACKS = ('track-harmony','track-lead','track-arp','track-depth-pad','track-depth-air')


def polished_mix(source):
    validate(source)
    if state_hash(source) != SOURCE_HASH or source.locks:
        raise ValidationError('exact unlocked human-approved Phase16 B required')
    p=deepcopy(source);byid={t.id:t for t in p.tracks};removed=set()
    for tid in SPACE_TRACKS:
        t=byid[tid]
        removed.update(e.id for e in t.effects if e.plugin_ref in
                       ('soundcraft:plate_reverb','soundcraft:room_reverb','soundcraft:mod_delay','soundcraft:phaser'))
        t.effects=[e for e in t.effects if e.id not in removed]
    p.automation=[a for a in p.automation if a.target_id not in removed]
    # Keep foreground EQ/transient identity and the approved patch files.
    for tid,amount in [('track-depth-pad',-3.3548529739),('track-depth-air',-2),
                       ('track-harmony',.3399790963),('track-lead',.2755680453)]:
        byid[tid].controls['mixer.gain_db']+=amount
        for a in p.automation:
            if a.target_id==tid and a.parameter_id=='mixer.gain_db':
                for x in a.points:x.value+=amount
    for tid,wet,depth,rate in [('track-harmony',.25,.25,.22),('track-depth-pad',.40,.30,.17)]:
        e=next(e for e in byid[tid].effects if e.plugin_ref=='soundcraft:chorus')
        e.parameters.update({'effect.wet':wet,'soundcraft.depth':depth,'soundcraft.rate':rate})
    add_spread(p,byid['track-harmony'],.85);add_spread(p,byid['track-lead'],.65)
    # Existing actual drum sum, with conservative parallel blend and a slower
    # attack to retain the sampled kick's leading transient. Ratio stays4.
    byid['phase15-drum-sum'].effects[0].parameters.update({'effect.wet':.35,
        'soundcraft.attack':28,'soundcraft.release':125,'soundcraft.threshold':-25})
    room=byid['phase15-shared-room'];room.effects[0].parameters.update({
        'soundcraft.decay_ms':650,'soundcraft.pre_delay':14,'soundcraft.low_cut':650,
        'soundcraft.damping':6000,'soundcraft.width':.85})
    for t in p.tracks:
        for s in t.sends:
            if s.target_track_id==room.id:
                s.gain_db={'track-snare':-18,'track-harmony':-17,'track-lead':-22,'track-depth-pad':-90}[t.id]
    # Pad's old short-room path is removed explicitly; dark bed has its own return.
    byid['track-depth-pad'].sends=[s for s in byid['track-depth-pad'].sends if s.target_track_id!=room.id]

    def eq(eid,hpf,lpf):
        return Effect(eid,'soundcraft:eq_7band',None,{'effect.bypass':0,
            'soundcraft.hpf_on':1,'soundcraft.hpf_freq':hpf,'soundcraft.hpf_slope':1/3,
            'soundcraft.lpf_on':1,'soundcraft.lpf_freq':lpf,'soundcraft.lpf_slope':1/3})
    def bus(tid,name,fx):
        t=Track(tid,name,'bus',None,{'mixer.gain_db':PAN_COMPENSATION_DB,'mixer.pan':0,'mixer.mute':0},fx,[],[],True)
        p.tracks.append(t);byid[tid]=t;add_spread(p,t,1);return t
    dark=bus('phase17-dark-space','Polish dark plate',[
        eq('phase17-dark-eq',650,4800),Effect('phase17-dark-chorus','soundcraft:chorus',None,
        {'effect.bypass':0,'effect.wet':.50,'soundcraft.rate':.11,'soundcraft.depth':.24,'soundcraft.spread':1}),
        Effect('phase17-dark-plate','soundcraft:plate_reverb',None,{'effect.bypass':0,'effect.wet':1,
        'soundcraft.decay_ms':2400,'soundcraft.pre_delay':32,'soundcraft.low_cut':650,
        'soundcraft.damping':4800,'soundcraft.width':1})])
    echo=bus('phase17-echo','Polish phrase echo',[
        eq('phase17-echo-eq',550,4800),Effect('phase17-echo-delay','soundcraft:mod_delay',None,
        {'effect.bypass':0,'effect.wet':1,'soundcraft.time':60/126*750,'soundcraft.feedback':.28,
         'soundcraft.lpf':4800,'soundcraft.mod_depth':0,'soundcraft.mod_rate':.2}),
        Effect('phase17-echo-chorus','soundcraft:chorus',None,{'effect.bypass':0,'effect.wet':.35,
         'soundcraft.rate':.23,'soundcraft.depth':.15,'soundcraft.spread':1})])
    def send(tid,bid,db,label):
        s=Send('phase17-send-'+label,bid,db,0,'post_fader');byid[tid].sends.append(s);return s
    for tid,db in [('track-depth-pad',-9),('track-depth-air',-15),('track-lead',-26)]:
        send(tid,dark.id,db,'dark-'+tid)
    send('track-arp',room.id,-24,'room-arp')
    def lane(tid,key,points,name):
        p.automation=[a for a in p.automation if not (a.target_id==tid and a.parameter_id==key)]
        values={round(t):v for t,v in points}
        p.automation.append(AutomationLane(name,tid,key,[AutomationPoint(name+'-'+str(i),tick,v,'linear')
            for i,(tick,v) in enumerate(sorted(values.items()))]))
    throws={}
    for tid,db in [('track-harmony',-12),('track-lead',-15),('track-arp',-22)]:
        s=send(tid,echo.id,db,'echo-'+tid);key=add_send_trim(p,byid[tid],s,-60)
        events={}
        for c in byid[tid].clips:
            for n in c.notes:
                at=c.start+n.start;group=at//(2*BAR)
                if group not in events or at>events[group][0]:events[group]=(at,n.duration)
        points=[(0,-60),(64*BAR,-60)];throws[tid]=[]
        for at,duration in sorted(events.values()):
            end=min(at+duration+60,64*BAR-97)
            if end<=at:continue
            points.extend([(max(0,at-24),-60),(at,0),(end,0),(end+96,-60)])
            throws[tid].append({'onset_tick':at,'close_tick':end+96})
        lane(tid,key,points,'phase17-throws-'+tid)
    kick=sorted({c.start+n.start for c in byid['track-kick'].clips for n in c.notes})
    # Durations are specified in ticks derived from milliseconds at source BPM.
    def ticks(ms):return round(ms/1000*126/60*p.ppq)
    def duck(at,depth,hold_ms=25,release_ms=165):
        distance=[at-k for k in kick if 0<=at-k<=ticks(release_ms)]
        if not distance:return 0.
        d=min(distance)
        return -depth if d<=ticks(hold_ms) else -depth*(ticks(release_ms)-d)/(ticks(release_ms)-ticks(hold_ms))
    # Returns breathe with the actual kick pattern, including its dropouts.
    for t,depth in [(dark,6),(echo,4)]:
        times={0,64*BAR}
        # A kick-free breakdown still needs its own space level. These explicit
        # boundaries prevent section gains from disappearing with the triggers.
        for bar in (24,32,48):times.update((bar*BAR-1,bar*BAR))
        for k in kick:times.update(max(0,min(64*BAR,x)) for x in (k-1,k,k+ticks(25),k+ticks(75),k+ticks(165)))
        points=[]
        for at in sorted(times):
            bar=at/BAR;section=1 if 24<=bar<32 else -2 if 32<=bar<48 else -1
            points.append((at,PAN_COMPENSATION_DB+section+duck(at,depth)))
        lane(t.id,'mixer.gain_db',points,'phase17-breathe-'+t.id)
    p.metadata.update(phase17_source_hash=SOURCE_HASH,phase16_human_preference='approved: audible qualitative step-change',
        phase17_human_preference='unreviewed',phase17_processing='Shared dark plate and filtered phrase echo; short room cohesion; scheduled MIDI-kick return attenuation, not audio-triggered sidechain. Incumbent bass dynamics retained; original synth/sample state and MIDI exact.')
    graph_contract(p)
    if export_bytes(p)!=export_bytes(source) or any(t.instrument!=u.instrument or t.clips!=u.clips for t,u in zip(source.tracks,p.tracks)):
        raise ValidationError('mix polish altered approved notes or instrument state')
    # New aux strips carry no musical clips; compare existing source performance.
    check=deepcopy(p);check.tracks=check.tracks[:len(source.tracks)]
    if performance(check)!=performance(source):raise ValidationError('mix polish changed musical structure')
    return p,{'version':'phase17-mix-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),
        'source_notes_and_instruments_exact':True,'MIDI_bytes_exact':True,'added_notes':[],
        'removed_insert_ids':sorted(removed),'throw_windows':throws,'kick_onsets':kick,
        'ducking':'scheduled from immutable MIDI kick onsets, not audio-triggered sidechain',
        'bass_dynamics':'incumbent gain curve exact; rejected130ms extra duck occupied silent gaps (relative PCM RMS .0001596)',
        'new_auxes':[dark.id,echo.id],'human_preference':'unreviewed','incumbent':'Phase16 B',
        'tracks_before':[asdict(t) for t in source.tracks],
        'automation_before':[asdict(a) for a in source.automation]}
