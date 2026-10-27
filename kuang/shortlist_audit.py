"""Independent harmonic and exact-edit checks for the 16-bar shortlist.

Every MIDI onset/offset is audited; release budgets additionally check the
unchanged dry pad's voice handoffs. This is not transcription of FX tails or a
measure of musical preference. Chord pitches are derived from intervals.
"""
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
from .schema import BAR,PPQ,ValidationError,validate,state_hash
from .composition_analysis import event_rows
from .master_bus import terminal_projection

THEORY={'Cm9':(0,(0,3,7,10,14)),'Fm9':(5,(0,3,7,10,14)),
        'Abmaj9':(8,(0,4,7,11,14)),'Ebmaj9':(3,(0,4,7,11,14)),
        'Bb9sus4':(10,(0,5,7,10,14)),'Cm11':(0,(0,3,7,10,14,17)),
        'Fm11-C':(5,(0,3,7,10,14,17))}
SCALE={0,2,3,5,7,8,10}
DRUMS={'track-kick','track-snare','track-snare.p38','track-hats','track-hats.p46','track-percussion'}
LOW={'track-bass','track-sub-pulse'}
UPPER={'track-harmony','track-lead','track-depth-pad','track-arp','track-depth-air'}


def audit_shortlist(reference,candidate,receipt):
    validate(reference);validate(candidate);terminal_projection(candidate)
    if receipt['source_hash']!=state_hash(reference) or receipt['candidate_hash']!=state_hash(candidate):raise ValidationError('shortlist receipt/hash drift')
    direction=receipt['direction']
    if direction not in ('soulful','progressive','hypnotic') or candidate.bars!=16:raise ValidationError('declared16-bar shortlist only')
    old={x['id']:x for x in event_rows(reference)};new={x['id']:x for x in event_rows(candidate)};origins=receipt['note_origins']
    if set(new)!=set(origins):raise ValidationError('complete note ancestry required')
    edits={x['before']['id']:x for x in receipt['pitch_edits']}
    for nid,x in new.items():
        o=origins[nid]
        if (not isinstance(o.get('source'),dict) or any(o.get(k)!=v for k,v in x.items()) or not o.get('reason') or
            o['source']!=old.get(o['source'].get('id'))):raise ValidationError('invented note provenance')
        if nid in old:
            permitted={**old[nid],'pitch':x['pitch']}
            if x!=permitted or (x['pitch']!=old[nid]['pitch'] and (x['track_id'] not in LOW or direction=='hypnotic')):raise ValidationError('surviving event changed outside authorized pitch')
            if x!=old[nid] and (nid not in edits or edits[nid]['before']!=old[nid] or edits[nid]['after']!=x):raise ValidationError('pitch edit not journaled')
    if set(edits)!={n for n,x in new.items() if n in old and x!=old[n]}:raise ValidationError('extra pitch edit claims')
    removed={x['id']:x for x in receipt['removed_notes']}
    if set(removed)!=set(old)-set(new) or any(x!=old[n] for n,x in removed.items()):raise ValidationError('removed upper-note inventory drift')
    if [t.id for t in reference.tracks]!=[t.id for t in candidate.tracks]:raise ValidationError('track identity/order drift')
    for a,b in zip(reference.tracks,candidate.tracks):
        x=asdict(a);y=asdict(b);x.pop('clips');y.pop('clips')
        if x!=y or(a.id not in UPPER|LOW and a!=b):raise ValidationError('palette, drums or graph changed')
        if a.id in LOW:
            x=deepcopy(b)
            for c in x.clips:
                for n in c.notes:n.pitch=old[n.id]['pitch']
            if x!=a or(direction=='hypnotic' and a!=b):raise ValidationError('bass/sub rhythm or protected pedal changed')
    for key in ('sections','automation','parameters','tempo_bpm','key_tonic','key_mode','time_signature','ppq','bars','locks'):
        if getattr(reference,key)!=getattr(candidate,key):raise ValidationError('form, registry or native expression changed')
    plan=receipt['harmonic_plan']
    if len(plan)!=16 or any(x['bar']!=i+1 or x['chord'] not in THEORY for i,x in enumerate(plan)):raise ValidationError('complete declared chord sequence required')
    pcs=[{(THEORY[x['chord']][0]+i)%12 for i in THEORY[x['chord']][1]} for x in plan]
    failures=[];events=defaultdict(lambda:{'on':[],'off':[]})
    for x in new.values():
        if x['track_id'] in LOW|UPPER:
            events[x['absolute_tick']]['on'].append(x);events[x['absolute_tick']+x['duration']]['off'].append(x)
    for b in range(17):events[b*BAR]
    active={};matrix=[]
    for lo,hi in zip(sorted(events),sorted(events)[1:]):
        for x in events[lo]['off']:active.pop(x['id'],None)
        for x in events[lo]['on']:active[x['id']]=x
        b=lo//BAR
        for x in active.values():
            if x['pitch']%12 not in SCALE or x['pitch']%12 not in pcs[b]:failures.append({'id':x['id'],'bar':b+1,'pitch':x['pitch'],'chord':plan[b]['chord']})
        if active:matrix.append({'tick':lo,'end':hi,'bar':b+1,'chord':plan[b]['chord'],'voices':{tid:sorted(x['pitch'] for x in active.values() if x['track_id']==tid) for tid in sorted(LOW|UPPER)}})
    # A source passing fifth/seventh is reinterpreted FUNCTIONALLY under major
    # neighbors. Roots and paired pulses must support the declared harmony.
    root_errors=[]
    for x in new.values():
        if x['track_id'] not in LOW:continue
        b=x['absolute_tick']//BAR;h=plan[b]['chord'];root,quality=THEORY[h]
        if direction!='hypnotic':
            src=old[x['id']]['pitch'];function={36:0,34:(11 if h in ('Abmaj9','Ebmaj9') else 10),31:7,39:(5 if h=='Bb9sus4' else 4 if h in ('Abmaj9','Ebmaj9') else 3)}[src]
            if x['pitch']%12!=(root+function)%12 or not 29<=x['pitch']<=44:root_errors.append(x['id'])
    # Actual overlapping low notes must be unison/octave or short consonant
    # root/fifth/third/seventh pickups, never two independently chosen roots.
    low_matrix=[]
    for row in matrix:
        bass=row['voices']['track-bass'];sub=row['voices']['track-sub-pulse']
        if bass and sub:low_matrix.append({'tick':row['tick'],'bass':bass,'sub':sub,'intervals':[(s-b)%12 for b in bass for s in sub]})
    leading=[]
    for i in range(1,16):
        a=plan[i-1]['stab_voicing'];b=plan[i]['stab_voicing']
        if a!=b:leading.append({'bar':i+1,'from':a,'to':b,'semitones':[y-x for x,y in zip(a,b)]})
    release_errors=[];pad=[x for x in new.values() if x['track_id']=='track-depth-pad'];release=round(1.65*126/60*PPQ)
    for x in pad:
        lo=x['absolute_tick'];hi=min(16*BAR,lo+x['duration']+release)
        for b in range(lo//BAR,(hi-1)//BAR+1):
            if x['pitch']%12 not in pcs[b]:release_errors.append(x['id'])
    air_errors=[];air_release=round(2.4*126/60*PPQ)  # Native2200ms, plus margin.
    for x in new.values():
        if x['track_id']!='track-depth-air':continue
        lo=x['absolute_tick'];hi=min(16*BAR,lo+x['duration']+air_release)
        for b in range(lo//BAR,(hi-1)//BAR+1):
            if x['pitch']%12 not in pcs[b]:air_errors.append(x['id'])
    phrase=[]
    for first in (0,4,8,12):
        xs=sorted((x for x in new.values() if x['track_id']=='track-lead' and first*BAR<=x['absolute_tick']<(first+4)*BAR),key=lambda x:x['absolute_tick'])
        phrase.append({'first_bar':first+1,'pitches':[x['pitch'] for x in xs],'gates_beats':[x['duration']/PPQ for x in xs],'rests_beats':16-sum(x['duration'] for x in xs)/PPQ})
    return {'version':'house-shortlist-audit-1','direction':direction,'drum_tracks_exact':True,'low_rhythm_exact':True,'hypnotic_low_tracks_exact':direction=='hypnotic',
            'palette_graph_expression_exact':True,'complete_lineage':True,'source_notes':len(old),'candidate_notes':len(new),'declared_pitch_edits':len(edits),
            'harmonic_plan':plan,'active_interval_matrix':matrix,'non_chord_or_key_intervals':failures,'bass_function_errors':root_errors,
            'bass_pulse_overlap':low_matrix,'stab_voice_leading':leading,'pad_release_handoff_errors':release_errors,'air_release_handoff_errors':air_errors,'four_bar_themes':phrase,
            'scope':'MIDI-active plus dry pad/air release budgets only; FX tails and artistic preference require listening',
            'human_preference':'unreviewed','new_full_song':False,'mastering':False}


def require_shortlist(report):
    if any(report[k] for k in ('non_chord_or_key_intervals','bass_function_errors','pad_release_handoff_errors','air_release_handoff_errors')):raise ValidationError('shortlist harmonic/pitch/release gate failed')
    return report
