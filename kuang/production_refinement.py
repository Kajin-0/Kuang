"""Scoped Phase25 source/space refinement; the approved record stays intact.

Original editable Fourier designs, explicit transition repairs and existing
native lanes. No new instrument, musical section, master chain or quality score.
"""
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict

from .schema import BAR,PPQ,ValidationError,validate,state_hash
from .chord_bed import bed_patch,PROTECTED,UPPER,REMOVED,CHORDS,THEORY
from .composition_analysis import event_rows
from .master_bus import terminal_projection

SOURCE_HASH='279ddbc10d2692d27ef97d54b914c85b62f2a20bb6a1309a7bc4dbc2c933a6d1'
VERSION='source-space-refinement-1'
EXTRA_GHOSTS={f'phase24-track-snare.p38-n{i}' for i in (62,63,64,65)}
SHIFT_BARS={51,55,59,63}
# Actual same-MIDI pre-insert calibration. The pad reaches the reviewed synth
# output ceiling0dB; its remaining2.284dB is explicit native EQ input makeup.
# This restores the OLD input level, not an overall listening/master boost.
PATCH_GAINS={'stab':-3.419572565695212,'pad':0.0}
INPUT_TRIMS={'stab':0.0,'pad':2.2836950749501597}


def refined_patch(voice,*,modulation=True,volume_db=None):
    """Actual1.0.6 internal units. False bypasses ONLY slow LFO routing.

    Waveforms remain original reviewed Fourier tables. No pitch destination,
    detune, unison pile, internal reverb or sample/factory content. LFO2 shape
    is the vertical inverse of LFO1, not a claimed oscillator pitch LFO.
    """
    if voice not in PATCH_GAINS or type(modulation) is not bool:raise ValidationError('one known refinement voice and explicit motion bool required')
    p=bed_patch(voice,volume_db=PATCH_GAINS[voice] if volume_db is None else volume_db);s=p['settings']
    def env(i,a,d,hold,r):
        s.update({f'env_{i}_attack':a**.25,f'env_{i}_decay':d**.25,f'env_{i}_sustain':hold,f'env_{i}_release':r**.25})
    if voice=='stab':
        env(1,.005,.28,.34,.14);env(2,.002,.18,.06,.10)
        s.update(osc_1_wave_frame=206,osc_1_level=.60,osc_1_pan=-.08,
            osc_2_wave_frame=96,osc_2_level=.18,osc_2_pan=.08,
            filter_1_cutoff=96,filter_1_drive=1.18,velocity_track=.40)
        routes=[('env_2','filter_1_cutoff',.115),('velocity','filter_1_cutoff',.09),('lfo_1','osc_1_wave_frame',.075)]
    else:
        env(1,.60,2.5,.68,1.65);env(2,1.6,4.0,.20,1.6)
        s.update(osc_1_wave_frame=170,osc_1_level=.40,osc_1_pan=-.45,
            osc_2_wave_frame=210,osc_2_level=.24,osc_2_pan=.45,
            filter_1_cutoff=93,filter_1_resonance=.035,lfo_2_sync=1,
            lfo_2_sync_type=1,lfo_2_tempo=3,lfo_2_stereo=.13)
        s['lfos'].append({'name':'Kuang counter-phase triangle','num_points':3,
            'points':[0,0,.5,1,1,0],'powers':[0,0,0],'smooth':True})
        routes=[('lfo_1','osc_1_wave_frame',.09),('lfo_2','osc_2_wave_frame',.08),
                ('lfo_2','filter_1_cutoff',.04),('env_2','filter_1_cutoff',.055),('velocity','filter_1_cutoff',.04)]
    for i in range(1,9):s[f'modulation_{i}_amount']=0
    routes=[x for x in routes if modulation or not x[0].startswith('lfo_')]
    s['modulations']=[{'source':a,'destination':b} for a,b,_ in routes]
    for i,(_,_,amount) in enumerate(routes,1):s[f'modulation_{i}_amount']=amount
    p['comments']='Phase25 original '+voice+': complementary Fourier registers, shaped strike/body and genuine timbral motion; no pitch modulation, factory content or added layer.'
    return p


def _curve(knots,bar):
    if bar<=knots[0][0]:return knots[0][1]
    for (a,x),(b,y) in zip(knots,knots[1:]):
        if bar<=b:return x+(y-x)*(bar-a)/(b-a)
    return knots[-1][1]


def refine_record(source):
    validate(source);terminal_projection(source)
    if source.locks or state_hash(source)!=SOURCE_HASH:raise ValidationError('exact unlocked Phase24 record required')
    p=deepcopy(source);p.id='project-phase25-production';p.name='Kuang / Stay in the pocket — source and space'
    before={x['id']:x for x in event_rows(source)};edits=[]
    for t in p.tracks:
        for c in t.clips:
            kept=[]
            for n in c.notes:
                x=before[n.id];b=x['absolute_tick']//BAR
                if n.id in EXTRA_GHOSTS:
                    if t.id!='track-snare.p38' or b not in (63,79,111,127) or x['absolute_tick']%BAR!=round(3.25*PPQ)+26:raise ValidationError('extra ghost identity drift')
                    edits.append({'action':'remove','before':x,'reason':'Remove only the Phase24-added post-clap tap; preserve the approved source ghost at3.777beats'})
                    continue
                if t.id=='track-harmony' and b in SHIFT_BARS:
                    n.start-=round(.125*PPQ)
                    edits.append({'action':'move','before':x,'after_tick':c.start+n.start,'delta_ticks':-120,'reason':'Restore original2.5beat chord pocket rather than the Phase24-only59.5ms delay; preserve source hand-strum'})
                kept.append(n)
            c.notes=kept
    if sum(e['action']=='remove' for e in edits)!=4 or sum(e['action']=='move' for e in edits)!=12:raise ValidationError('reviewed4ghost/12voice repair scope drift')
    by={t.id:t for t in p.tracks}
    chord=next(e for e in by['track-harmony'].effects if e.plugin_ref=='soundcraft:eq_7band')
    chord.parameters.update({'soundcraft.hpf_freq':140,'soundcraft.low_mid_freq':330,'soundcraft.low_mid_gain':-1.25})
    pad=next(e for e in by['track-depth-pad'].effects if e.plugin_ref=='soundcraft:eq_7band')
    pad.parameters.update({'soundcraft.hpf_freq':220,'soundcraft.low_mid_gain':-1.75,'soundcraft.input_gain':INPUT_TRIMS['pad']})
    dark=by['phase17-dark-space']
    next(e for e in dark.effects if e.plugin_ref=='soundcraft:eq_7band').parameters.update({'soundcraft.hpf_freq':600,'soundcraft.lpf_freq':8000})
    next(e for e in dark.effects if e.plugin_ref=='soundcraft:plate_reverb').parameters.update({'soundcraft.low_cut':600,'soundcraft.pre_delay':42})
    automation_edits=[]
    for lane in p.automation:
        if lane.target_id=='effect-harmony-eq' and lane.parameter_id=='soundcraft.hpf_freq':
            for x in lane.points:x.value=max(140,x.value)
        elif lane.target_id=='effect-depth-pad-eq' and lane.parameter_id=='soundcraft.lpf_freq':
            knots=[(0,1.05),(8,1.1),(16,1),(32,1),(36,1.5),(44,1.65),(48,1.3),(60,1.55),(64,1.3),(68,1.4),(72,1.15),(76,1.3),(79.75,1.1),(80,1.5),(84,1.7),(92,1.65),(96,1.5),(108,1.8),(112,1.35),(124,1.55),(128,1.2),(136,1),(144,1)]
            for x in lane.points:
                if not 16*BAR<=x.tick<=32*BAR:x.value*=_curve(knots,x.tick/BAR)
        elif lane.target_id=='phase17-dark-space' and lane.parameter_id=='mixer.gain_db':
            # Pad input already ducks. Halve only the EXTRA wet-return duck;
            # preserve recovered levels and leave the kick-free break calm.
            peaks=defaultdict(lambda:-90.)
            for x in lane.points:peaks[x.tick//PPQ]=max(peaks[x.tick//PPQ],x.value)
            for x in lane.points:
                if not 64*BAR<=x.tick<72*BAR:x.value+=(peaks[x.tick//PPQ]-x.value)*.5
        elif lane.target_id=='track-harmony' and lane.parameter_id.startswith('route.'):
            for x in lane.points:
                if x.tick//BAR in (55,63):
                    old=asdict(x);x.tick-=120;automation_edits.append({'before':old,'after':asdict(x),'reason':'Echo gate follows repaired chord attack and release'})
            lane.points.sort(key=lambda x:x.tick)
    p.metadata.update(phase25_version=VERSION,phase25_source_hash=SOURCE_HASH,
        phase25_scope='Four added ghosts removed,12 chord voice onsets restored; original anchor MIDI, other notes and rhythm sources exact. Two upper synth patches/role EQ/depth performance, no new master.',phase25_preference='unreviewed')
    validate(p);terminal_projection(p)
    return p,{'version':VERSION,'source_hash':SOURCE_HASH,'score_hash':state_hash(p),'candidate_hash':state_hash(p),
        'note_edits':edits,'automation_timing_edits':automation_edits,'source_notes':len(before),'candidate_notes':len(event_rows(p)),
        'anchor_MIDI_exact':True,'anchor_upper_audio_exact':False,'rhythm_source_states_exact':True,
        'mastering':False,'human_preference':'unreviewed','scope':'Fresh production project, not a revision-1 transaction receipt'}


def audit_refinement(source,p,receipt):
    validate(p);terminal_projection(p)
    if receipt['source_hash']!=state_hash(source) or receipt['candidate_hash']!=state_hash(p):raise ValidationError('refinement receipt drift')
    q,r=refine_record(source);view=deepcopy(p)
    for t in view.tracks:
        if t.id in UPPER:t.instrument=deepcopy(next(x.instrument for x in q.tracks if x.id==t.id))
    for k in ('external_synth_source_hash','external_synth_backend','external_synth_notes'):
        if k in q.metadata:view.metadata[k]=q.metadata[k]
        else:view.metadata.pop(k,None)
    if view!=q or receipt['score_hash']!=state_hash(q) or receipt['note_edits']!=r['note_edits'] or receipt['automation_timing_edits']!=r['automation_timing_edits']:raise ValidationError('outside reviewed production scope')
    old=event_rows(source);now=event_rows(p);a={x['id']:x for x in old};b={x['id']:x for x in now}
    if set(a)-set(b)!=EXTRA_GHOSTS or set(b)-set(a):raise ValidationError('unapproved note removal/addition')
    for x in now:
        prior=a[x['id']];moved=x['track_id']=='track-harmony' and prior['absolute_tick']//BAR in SHIFT_BARS
        for k,v in prior.items():
            expected=v-120 if moved and k in ('start','absolute_tick') else v
            if x[k]!=expected:raise ValidationError('unauthorized note field edit')
    anchor=[x for x in old if 16*BAR<=x['absolute_tick']<32*BAR]
    if anchor!=[x for x in now if 16*BAR<=x['absolute_tick']<32*BAR]:raise ValidationError('approved anchor MIDI changed')
    for x,y in zip(source.tracks,p.tracks):
        if x.id in PROTECTED-{'track-snare.p38'} and x!=y:raise ValidationError('protected rhythm channel changed')
    for key in ('sections','bars','parameters','tempo_bpm','key_tonic','key_mode','ppq','time_signature','locks'):
        if getattr(source,key)!=getattr(p,key):raise ValidationError('song form/registry changed')
    if REMOVED&{t.id for t in p.tracks}:raise ValidationError('no lead/arp permitted')
    # Existing harmonic membership plus measured dry-release budgets remain
    # valid because only chord onsets move earlier by.125beat, inside same bar.
    changes=defaultdict(lambda:{'on':[],'off':[]});budgets={'track-harmony':.20,'track-depth-pad':2.,'track-bass':.03,'track-sub-pulse':.03}
    for x in now:
        if x['track_id'] in budgets:
            changes[x['absolute_tick']]['on'].append(x);changes[min(p.length,x['absolute_tick']+x['duration']+round(budgets[x['track_id']]*126/60*PPQ))]['off'].append(x)
    for bar in range(145):changes[bar*BAR]
    active={};bad=[];intervals=0;times=sorted(changes)
    for lo,hi in zip(times,times[1:]):
        for x in changes[lo]['off']:active.pop(x['id'],None)
        for x in changes[lo]['on']:active[x['id']]=x
        root,quality=THEORY[CHORDS[lo//BAR%16]];pcs={(root+i)%12 for i in quality}
        intervals+=bool(active)
        for x in active.values():
            if x['pitch']%12 not in pcs:bad.append(x['id'])
    if bad:raise ValidationError('active/releasing harmonic conflict')
    return {'version':'production-refinement-audit-1','source_hash':state_hash(source),'candidate_hash':state_hash(p),'notes':len(now),
        'removed_extra_ghosts':sorted(EXTRA_GHOSTS),'repaired_chord_voice_onsets':12,'retained_note_ids_order_other_fields_exact':True,'anchor_MIDI_exact':len(anchor),
        'anchor_upper_audio_exact':False,'seven_unchanged_rhythm_channels_exact':True,'bass_omissions_intentionally_retained':True,
        'harmonic_active_release_intervals':intervals,'unexplained_harmonic_intervals':bad,'structure_and_no_lead_exact':True,
        'human_preference':'unreviewed','mastering':False,'scope':'Musical/event integrity, not a professional-quality or rhythm-preference score'}
