"""Independent event-complete audit of the new theme and protected pocket.

Chord qualities are constructed from roots/intervals, not the composer's voiced
MIDI tuples. MIDI-active intervals do not transcribe synth/reverb release tails
or establish whether the listener likes a composition.
"""
from collections import Counter,defaultdict
from dataclasses import asdict
from .schema import BAR,PPQ,ValidationError,state_hash,validate
from .composition_analysis import event_rows
from .flow_audit import groove_facts

THEORY={'Cm9':(0,(0,3,7,10,14)),'Cm11':(0,(0,3,7,10,14,17)),
        'Abmaj9-C':(8,(0,4,7,11,14)),'Fm9-C':(5,(0,3,7,10,14)),
        'Fm11-C':(5,(0,3,7,10,14,17))}
SCALE={0,2,3,5,7,8,10}
PROTECTED={'track-kick','track-snare','track-snare.p38','track-hats','track-hats.p46','track-percussion','track-bass','track-sub-pulse'}
UPPER={'track-harmony','track-depth-pad','track-depth-air'}


def audit_theme(source,candidate,receipt):
    validate(source);validate(candidate)
    if receipt['source_hash']!=state_hash(source) or receipt['candidate_hash']!=state_hash(candidate):raise ValidationError('theme receipt/hash drift')
    old={x['id']:x for x in event_rows(source)};rows=event_rows(candidate);origins=receipt['note_origins'];new={x['id']:x for x in rows}
    if len(new)!=len(rows) or set(new)!=set(origins):raise ValidationError('complete unique note lineage required')
    for x in rows:
        o=origins[x['id']]
        if any(o[k]!=v for k,v in x.items()) or not o['reason'] or o['source']!=old.get(o['source']['id']):raise ValidationError('invented/incomplete source lineage')
        if x['id'] in old and x!=old[x['id']]:raise ValidationError('surviving source IDs must retain exact fields')
    removed={x['id']:x for x in receipt['removed_notes']}
    if set(removed)!=(set(old)-set(new)) or any(x!=old[k] for k,x in removed.items()):raise ValidationError('removed-note inventory mismatch')
    for a,b in zip(source.tracks,candidate.tracks):
        if a.id in PROTECTED and a!=b:raise ValidationError('approved rhythm section changed')
        x=asdict(a);y=asdict(b);x.pop('clips');y.pop('clips')
        if x!=y:raise ValidationError('sound palette/mix graph changed')
    if source.sections!=candidate.sections or source.automation!=candidate.automation or source.parameters!=candidate.parameters:raise ValidationError('form/expression/registry changed')
    plan=receipt['harmonic_plan']
    if len(plan)!=candidate.bars:raise ValidationError('complete harmonic plan required')
    changes=defaultdict(lambda:{'on':[],'off':[]})
    for x in rows:
        if x['track_id'] not in PROTECTED-{'track-bass','track-sub-pulse'}:
            changes[x['absolute_tick']]['on'].append(x);changes[x['absolute_tick']+x['duration']]['off'].append(x)
    for b in range(candidate.bars+1):changes[b*BAR]
    active={};intervals=[];bad_key=[];bad_upper=[];bad_low=[];melodic_colors=[];times=sorted(changes)
    for lo,hi in zip(times,times[1:]):
        for x in changes[lo]['off']:active.pop(x['id'],None)
        for x in changes[lo]['on']:active[x['id']]=x
        b=lo//BAR;h=plan[b];root,quality=THEORY[h['name']];pcs={(root+i)%12 for i in quality}
        if h['pitch_classes']!=sorted(pcs):raise ValidationError('chord label/quality mismatch')
        lows=sorted({x['pitch'] for x in active.values() if x['track_id'] in ('track-bass','track-sub-pulse')});uppers=sorted({x['pitch'] for x in active.values() if x['track_id'] in UPPER})
        for x in active.values():
            info={'id':x['id'],'track':x['track_id'],'pitch':x['pitch'],'start':lo,'end':hi,'bar':b+1,'harmony':h['name']}
            if x['pitch']%12 not in SCALE:bad_key.append(info)
            if x['pitch']%12 not in pcs:
                if x['track_id'] in UPPER:bad_upper.append(info)
                elif x['track_id'] in ('track-bass','track-sub-pulse'):bad_low.append(info)
                else:melodic_colors.append({**info,'interpretation':'Short diatonic melodic11th/suspension, not claimed chord membership','note_gate_beats':x['duration']/PPQ})
        if active:intervals.append({'start':lo,'end':hi,'bar':b+1,'harmony':h['name'],'bass':lows,'upper':uppers,
            'melody':sorted({x['pitch'] for x in active.values() if x['track_id'] in ('track-lead','track-arp')}),
            'upper_intervals_above_actual_bass':{str(n):[(u-n)%12 for u in uppers] for n in lows}})
    # New melodic colors must be brief F-over-C gestures, never arbitrary
    # out-of-chord held notes excused by a key label. Old break is reported.
    illegal_colors=[x for x in melodic_colors if x['id'].startswith('phase21-') and not(x['pitch']%12==5 and x['harmony']=='Cm9' and x['note_gate_beats']<=.5)]
    voice_leading=[]
    for a,b in zip(plan,plan[1:]):
        if a['stab_voicing']!=b['stab_voicing']:
            voice_leading.append({'bar':b['bar'],'from':a['name'],'to':b['name'],'semitones':[y-x for x,y in zip(a['stab_voicing'],b['stab_voicing'])]})
    # Describe the actual melodic development, rather than rewarding more notes.
    phrases=[]
    for first in range(16,144,8):
        if first==80:continue
        group=[x for x in rows if x['track_id']=='track-lead' and first*BAR<=x['absolute_tick']<(first+8)*BAR]
        phrases.append({'first_bar':first+1,'notes':len(group),'pitch_sequence':[x['pitch'] for x in sorted(group,key=lambda x:x['absolute_tick'])],
                        'pitch_range':([min(x['pitch'] for x in group),max(x['pitch'] for x in group)] if group else []),
                        'silent_beats':32-sum(x['duration'] for x in group)/PPQ})
    pocket=groove_facts(candidate)
    source_kicks=[x for x in event_rows(source) if x['track_id']=='track-kick']
    candidate_kicks=[x for x in rows if x['track_id']=='track-kick']
    return {'version':'theme-performance-audit-1','all_note_lineage_exact':True,'all_removed_notes_accounted':True,
        'protected_tracks_exact':sorted(PROTECTED),'palette_graph_sections_lanes_registry_exact':True,
        'source_notes':len(old),'candidate_notes':len(rows),'authored_notes':receipt['authored_notes'],
        'out_of_key_intervals':bad_key,'non_chord_upper_intervals':bad_upper,'non_chord_low_intervals':bad_low,
        'unexplained_new_melodic_colors':illegal_colors,'all_melodic_colors':melodic_colors,
        'concurrent_intervals':intervals,'voice_leading':voice_leading,'phrases':phrases,
        'kick_counts_exact':source_kicks==candidate_kicks,
        'per_bar_kick':[{'bar':b+1,'ticks_within_bar':x['kick_ticks_within_bar']} for b,x in enumerate(pocket['per_bar'])],
        'longest_kick_free_bars':pocket['longest_kick_free_bars'],
        'limitations':'Exact MIDI-active harmony/lineage; synth release and reverb tails need separate native listening/controls, and this is not a preference score'}


def require_theme(audit):
    for key in ('out_of_key_intervals','non_chord_upper_intervals','non_chord_low_intervals','unexplained_new_melodic_colors'):
        if audit[key]:raise ValidationError('theme musical integrity failed: '+key+' '+str(audit[key][:3]))
    if audit['longest_kick_free_bars']>8 or not audit['kick_counts_exact']:raise ValidationError('dance-floor continuity changed')
