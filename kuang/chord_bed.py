"""One melody-free house bed on the sealed Phase21 main-peak pocket.

Original editable synth designs and restrained chord performance; no default
composer change, new schema, borrowed preset or automatic quality ranking.
"""
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
from .schema import BAR,PPQ,Clip,Note,ValidationError,state_hash,validate
from .master_bus import terminal_projection
from .composition_analysis import event_rows
from .studio_palette import studio_patch

REFERENCE_HASH='ec7c372bd16dbc140a5990913442497c829943b2e45177c41fcfdd6d04405d55'
VERSION='melody-free-chord-bed-1'
REMOVED={'track-lead','track-arp','track-depth-air'}
UPPER={'track-harmony','track-depth-pad'}
PROTECTED={'track-kick','track-snare','track-snare.p38','track-hats','track-hats.p46','track-percussion','track-bass','track-sub-pulse'}
CHORDS=('Cm9',)*4+('Cm11',)*4+('Abmaj9-C',)*4+('Cm9',)*4
VOICINGS={'Cm9':(51,58,62),'Cm11':(53,58,63),'Abmaj9-C':(51,56,58)}
THEORY={'Cm9':(0,(0,3,7,10,14)),'Cm11':(0,(0,3,7,10,14,17)),
        'Abmaj9-C':(8,(0,4,7,11,14))}


def bed_patch(voice,*,modulation=True,volume_db=None):
    """Verified Vitalium INTERNAL units; real worker must restore/read back.

    Time knobs are fourth roots of seconds, cutoff is MIDI-note units. LFO
    enum3 is8/1, enum4 is4/1, Sync mode1, verified on actual1.0.6 parameter text.
    No pitch destination, broad detune, oscillator stack or internal reverb.
    """
    if voice not in ('stab','pad') or type(modulation) is not bool:raise ValidationError('one known chord-bed voice required')
    gain={'stab':-6.2615209492101425,'pad':-1.2647295761}[voice] if volume_db is None else volume_db
    p=studio_patch(voice,modulation=False,volume_db=gain);s=p['settings']
    s.update(osc_1_on=1,osc_2_on=1,osc_3_on=0,osc_1_transpose=0,osc_2_transpose=0,
        osc_1_tune=0,osc_2_tune=0,osc_1_unison_voices=1,osc_2_unison_voices=1,
        osc_1_unison_detune=0,osc_2_unison_detune=0,osc_1_stereo_spread=0,osc_2_stereo_spread=0,
        osc_1_random_phase=0,osc_2_random_phase=0,osc_1_phase=.25,osc_2_phase=.32,
        osc_1_distortion_type=0,osc_2_distortion_type=0,osc_1_distortion_amount=0,osc_2_distortion_amount=0,
        filter_1_resonance=.06,filter_1_drive=1.12,filter_1_keytrack=.4,
        lfo_1_sync=1,lfo_1_sync_type=1,lfo_1_stereo=.08,
        chorus_on=0,reverb_on=0,delay_on=0,distortion_on=0,polyphony=12,legato=0)
    def env(i,a,d,hold,r):
        s.update({f'env_{i}_attack':a**.25,f'env_{i}_decay':d**.25,
                  f'env_{i}_sustain':hold,f'env_{i}_release':r**.25})
    if voice=='stab':
        env(1,.007,.32,.36,.17);env(2,.003,.24,.10,.12)
        s.update(osc_1_wave_frame=150,osc_1_level=.63,osc_1_pan=-.20,
            osc_2_wave_frame=220,osc_2_level=.22,osc_2_pan=.20,
            filter_1_cutoff=92,lfo_1_tempo=4,velocity_track=.35,
            modulation_1_amount=.12,modulation_2_amount=.06,modulation_3_amount=.025)
        links=[('env_2','filter_1_cutoff'),('velocity','filter_1_cutoff'),('lfo_1','osc_1_wave_frame')]
    else:
        env(1,.75,2.8,.70,1.8);env(2,1.2,5.0,.25,1.6)
        s.update(osc_1_wave_frame=130,osc_1_level=.42,osc_1_pan=-.32,
            osc_2_wave_frame=190,osc_2_level=.31,osc_2_pan=.32,
            filter_1_cutoff=84,filter_1_resonance=.04,filter_1_keytrack=.35,
            lfo_1_tempo=3,velocity_track=.25,modulation_1_amount=.06,
            modulation_2_amount=.035,modulation_3_amount=.08)
        links=[('lfo_1','osc_2_wave_frame'),('lfo_1','filter_1_cutoff'),('env_2','filter_1_cutoff')]
    s['modulations']=[{'source':a,'destination':b} for a,b in links] if modulation else []
    p['comments']='Phase23 '+voice+': original Fourier body, two single tuned oscillators, role envelopes and verified slow sync timbral motion; no lead, factory content or added reverb.'
    return p


def compose_bed(reference):
    validate(reference);terminal_projection(reference)
    if reference.locks or state_hash(reference)!=REFERENCE_HASH:raise ValidationError('exact unlocked Phase21 main16 required')
    p=deepcopy(reference);p.id='project-phase23-chord-bed';p.name='Kuang / In the pocket — no melody'
    old=event_rows(reference);by={t.id:t for t in p.tracks};removed=[x for x in old if x['track_id'] in UPPER|REMOVED]
    removed_owners={x for t in p.tracks if t.id in REMOVED for x in (t.id,t.instrument.id,*(e.id for e in t.effects))}
    p.tracks=[t for t in p.tracks if t.id not in REMOVED];p.automation=[a for a in p.automation if a.target_id not in removed_owners]
    serial=defaultdict(int);authored={}
    for tid in sorted(UPPER):by[tid].clips=[Clip('phase23-'+tid,'One restrained harmonic performance','midi',0,16*BAR,[],None)]
    def add(tid,at,gate,pitch,vel,reason):
        serial[tid]+=1;n=Note('phase23-'+tid+'-'+str(serial[tid]),round(at),round(gate),pitch,vel,0);c=by[tid].clips[0];c.notes.append(n)
        src=min((x for x in old if x['track_id']==tid),key=lambda x:(abs(x['absolute_tick']-n.start),abs(x['pitch']-pitch),x['id']))
        authored[n.id]={'track_id':tid,'clip_id':c.id,'absolute_tick':n.start,**asdict(n),'source':src,'reason':reason}
    pattern=(((.75,.30,78),(2.75,.42,74)),((1.75,.72,76),),
             ((.75,.28,77),(3.0,.24,72)),((.75,.65,75),(2.5,.40,74)))
    for b in range(16):
        for beat,gate,vel in pattern[b%4]:
            if b>=8 and b%4==3:gate+=.10
            for i,n in enumerate(VOICINGS[CHORDS[b]]):add('track-harmony',(b*4+beat)*PPQ+i*4,gate*PPQ,n,vel-i*3,
                'Three-voice rhythmic chord hook; exact rootless guide voicing, short/held articulation, no single-note answer')
    # Two held common inner voices and one embedded chord color; no solo top
    # line or ornamental part. A2s budget exceeds the actual1.8s pad release.
    release=2*126/60*PPQ
    for n,v in ((63,64),(67,62)):add('track-depth-pad',.25*PPQ,16*BAR-.25*PPQ-release,n,v,'Common Eb/G harmonic inner voice; sustained source body, not a lead')
    for b,n in ((0,74),(4,77),(8,72),(12,74)):add('track-depth-pad',(b*4+.25)*PPQ,4*BAR-.25*PPQ-release,n,59,
        'Embedded four-bar extended-chord color, release-aware handoff inside the sustained polyphonic pad')
    for tid in UPPER:by[tid].clips[0].notes.sort(key=lambda n:(n.start,n.pitch,n.id))
    # Reuse existing actual inserts/lanes, without changing any shared return
    # or protected rhythm strip. Less chorus smearing, supported body register.
    for tid,mix,depth,rate,spread in [('track-harmony',.12,.16,.17,.6),('track-depth-pad',.18,.18,.09,.7)]:
        t=by[tid];e=next(e for e in t.effects if e.plugin_ref=='soundcraft:chorus')
        e.parameters.update({'effect.wet':mix,'soundcraft.depth':depth,'soundcraft.rate':rate,'soundcraft.spread':spread})
    eq=next(e for e in by['track-depth-pad'].effects if e.plugin_ref=='soundcraft:eq_7band');eq.parameters['soundcraft.hpf_freq']=180;eq.parameters['soundcraft.low_mid_gain']=0
    by['track-depth-pad'].controls['mixer.stereo_spread']=.65
    from .schema import AutomationPoint
    for tid,values in [('track-harmony',[2800,4200,3000,5000,3200]),('track-depth-pad',[1300,2400,1700,3100,1600])]:
        fx=next(e for e in by[tid].effects if e.plugin_ref=='soundcraft:eq_7band');fx.parameters['soundcraft.lpf_freq']=values[0]
        lane=next(a for a in p.automation if a.target_id==fx.id and a.parameter_id=='soundcraft.lpf_freq')
        lane.points=[AutomationPoint('phase23-'+tid+'-tone-'+str(i),i*4*BAR,v,'linear') for i,v in enumerate(values)]
    lane=next(a for a in p.automation if a.target_id=='track-depth-pad' and a.parameter_id=='mixer.gain_db')
    offsets=(-.6,.3,-.4,.5,-.5)
    for point in lane.points:
        phase=min(point.tick/(4*BAR),3.999999999);i=int(phase);offset=offsets[i]+(offsets[i+1]-offsets[i])*(phase-i);point.value+=offset
    by['track-depth-pad'].controls['mixer.gain_db']=lane.points[0].value
    p.metadata.update(phase23_profile=VERSION,phase23_reference_hash=REFERENCE_HASH,phase23_scope='One16-bar chord/pad groove; lead/arp/ornamental air deleted; drums,bass,sub and shared routing/returns exact',phase23_preference='unreviewed')
    validate(p);terminal_projection(p)
    oldby={x['id']:x for x in old};origins={x['id']:authored.get(x['id'],{**x,'source':oldby.get(x['id']),'reason':'Exact protected Phase21 event'}) for x in event_rows(p)}
    return p,{'version':VERSION,'reference_hash':REFERENCE_HASH,'score_hash':state_hash(p),'candidate_hash':state_hash(p),
        'removed_tracks':sorted(REMOVED),'removed_notes':removed,'note_origins':origins,
        'harmonic_plan':[{'bar':i+1,'chord':c,'voicing':list(VOICINGS[c])} for i,c in enumerate(CHORDS)],
        'source_notes':len(old),'candidate_notes':len(origins),'authored_notes':len(authored),
        'human_preference':'unreviewed','mastering':False,'full_song':False}


def audit_bed(reference,p,receipt):
    """Every sounding/releasing harmonic interval, exact pocket and role absence."""
    validate(reference);validate(p);terminal_projection(p)
    if receipt['reference_hash']!=state_hash(reference) or receipt['candidate_hash']!=state_hash(p):raise ValidationError('bed receipt drift')
    expected,_=compose_bed(reference);view=deepcopy(p)
    # Binding may change ONLY the two declared instrument states and its
    # three provenance strings. The reviewed score/FX/lane edit stays exact.
    for t in view.tracks:
        if t.id in UPPER:t.instrument=deepcopy(next(x.instrument for x in expected.tracks if x.id==t.id))
    for key in ('external_synth_source_hash','external_synth_backend','external_synth_notes'):
        if key in expected.metadata:view.metadata[key]=expected.metadata[key]
        else:view.metadata.pop(key,None)
    if state_hash(expected)!=receipt['score_hash'] or view!=expected:raise ValidationError('outside reviewed chord-bed edit scope')
    old={x['id']:x for x in event_rows(reference)};rows=event_rows(p);now={x['id']:x for x in rows};origins=receipt['note_origins']
    if set(now)!=set(origins):raise ValidationError('complete note lineage required')
    for x in rows:
        r=origins[x['id']]
        if any(r.get(k)!=v for k,v in x.items()) or r.get('source')!=old.get(r.get('source',{}).get('id')) or not r.get('reason'):raise ValidationError('invented note ancestry')
    removed={x['id']:x for x in receipt['removed_notes']}
    if set(removed)!=set(old)-set(now) or any(x!=old[k] for k,x in removed.items()):raise ValidationError('removed-note inventory drift')
    if set(t.id for t in p.tracks)!=(set(t.id for t in reference.tracks)-REMOVED):raise ValidationError('lead/arp/air absent and no new instrument required')
    by={t.id:t for t in p.tracks}
    for t in reference.tracks:
        if t.id in PROTECTED or t.kind=='bus':
            if by[t.id]!=t:raise ValidationError('protected groove or shared bus changed')
    owners={x for t in reference.tracks if t.id in PROTECTED or t.kind=='bus' for x in (t.id,*([t.instrument.id] if t.instrument else []),*(e.id for e in t.effects))}
    if [a for a in p.automation if a.target_id in owners]!=[a for a in reference.automation if a.target_id in owners]:raise ValidationError('protected expression changed')
    for key in ('sections','parameters','tempo_bpm','key_tonic','key_mode','time_signature','ppq','bars','locks'):
        if getattr(reference,key)!=getattr(p,key):raise ValidationError('form/registry changed')
    plan=receipt['harmonic_plan']
    if len(plan)!=16 or [x['chord'] for x in plan]!=list(CHORDS):raise ValidationError('declared gentle pedal harmony required')
    pcs=[{(THEORY[h][0]+i)%12 for i in THEORY[h][1]} for h in CHORDS]
    events=defaultdict(lambda:{'on':[],'off':[]})
    for x in rows:
        if x['track_id'] in UPPER|{'track-bass','track-sub-pulse'}:
            release={'track-harmony':.20,'track-depth-pad':2.0,'track-bass':.03,'track-sub-pulse':.03}[x['track_id']]
            events[x['absolute_tick']]['on'].append(x);events[min(16*BAR,x['absolute_tick']+x['duration']+round(release*126/60*PPQ))]['off'].append(x)
    for b in range(17):events[b*BAR]
    active={};bad=[];matrix=[];times=sorted(events)
    for lo,hi in zip(times,times[1:]):
        for x in events[lo]['off']:active.pop(x['id'],None)
        for x in events[lo]['on']:active[x['id']]=x
        for x in active.values():
            if x['pitch']%12 not in pcs[lo//BAR]:bad.append({'id':x['id'],'pitch':x['pitch'],'bar':lo//BAR+1,'chord':CHORDS[lo//BAR]})
        if active:matrix.append({'start':lo,'end':hi,'bar':lo//BAR+1,'bass':[x['pitch'] for x in active.values() if x['track_id'] in ('track-bass','track-sub-pulse')],'harmonic':[x['pitch'] for x in active.values() if x['track_id'] in UPPER]})
    # No invented top-line in a renamed role: every short chord attack is a
    # compact3-note group; the pad has only long overlapping ensemble notes.
    strikes=defaultdict(list)
    for x in rows:
        if x['track_id']=='track-harmony':strikes[(x['absolute_tick']//PPQ,(x['absolute_tick']%PPQ)//16)].append(x)
    if any(len(xs)!=3 or max(x['absolute_tick'] for x in xs)-min(x['absolute_tick'] for x in xs)>8 for xs in strikes.values()):raise ValidationError('chord hook may not hide a single-note lead')
    if any(x['duration']<8*PPQ for x in rows if x['track_id']=='track-depth-pad'):raise ValidationError('pad may not hide ornamental notes')
    if bad:raise ValidationError('incompatible active/releasing harmony: '+str(bad[:3]))
    return {'version':'melody-free-bed-audit-1','protected_tracks_exact':sorted(PROTECTED),'shared_bus_and_rhythm_expression_exact':True,
        'lead_arp_air_tracks_and_notes_absent':True,'only_harmonic_MIDI_roles':sorted(UPPER),'all_note_lineage_exact':True,
        'active_and_release_intervals':matrix,'unexplained_harmonic_intervals':bad,'notes':len(rows),'chord_strikes':len(strikes),
        'release_budgets_seconds':{'stab':.20,'pad':2.0,'bass_sub':.03},'human_preference':'unreviewed',
        'scope':'MIDI plus conservative actual dry-envelope releases; reverb tails and perceived richness require listening'}
