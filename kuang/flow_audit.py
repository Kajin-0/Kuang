"""Event-level continuity and editorial-delta audit, not a taste score."""
from copy import deepcopy
from dataclasses import asdict
from .schema import BAR,PPQ,ValidationError,state_hash
from .composition_analysis import event_rows,audit_composition
from .harmonic_audit import context


def groove_facts(p):
 rows=event_rows(p);bars=[];signature=[];danceable=[];longest=run=0;longest_start=None;run_start=0
 for bar in range(p.bars):
  ev=[x for x in rows if bar*BAR<=x['absolute_tick']<(bar+1)*BAR]
  kick=sorted(x['absolute_tick']-bar*BAR for x in ev if x['track_id']=='track-kick')
  lead=[x for x in ev if x['track_id']=='track-lead']
  complete=all(any(x['absolute_tick']-bar*BAR==tick and x['pitch']==pitch and x['duration']==duration for x in lead) for tick,pitch,duration in ((0,67,290),(750,63,155),(1440,65,310)))
  if complete:signature.append(bar)
  bass=[x for x in ev if x['track_id']=='track-bass'];clap=[x for x in ev if x['track_id']=='track-snare']
  if kick==[0,PPQ,2*PPQ,3*PPQ] and len(bass)>=2 and len(clap)>=2:danceable.append(bar)
  if not kick:
   if run==0:run_start=bar
   run+=1
   if run>longest:longest=run;longest_start=run_start
  else:run=0
  bars.append({'zero_bar':bar,'display_bar':bar+1,'kick_count':len(kick),'kick_ticks_within_bar':kick,'four_floor_exact':kick==[0,PPQ,2*PPQ,3*PPQ],
   'bass_count':len(bass),'bass_pitches':[x['pitch'] for x in bass],'clap_count':len(clap),'hat_count':sum(x['track_id'] in ('track-hats','track-hats.p46') for x in ev),'complete_signature':complete})
 return {'per_bar':bars,'longest_kick_free_bars':longest,'longest_kick_free_start_zero_bar':longest_start,'first_complete_signature_zero_bar':min(signature) if signature else None,
 'complete_signature_zero_bars':signature,'first_established_bass_drums_zero_bar':min(danceable) if danceable else None,
 'lead_pitch_vocabulary':sorted({x['pitch'] for x in rows if x['track_id']=='track-lead'}),'steady_four_floor_88_112':all(x['four_floor_exact'] for x in bars[88:112]),
 'scope':'Actual MIDI onsets and duration-matched G-Eb-F pattern. Presence is not a claim of perceived prominence; native audio/filters checked separately.'}


def audit_flow(source,candidate,receipt):
 # Independently replay the entire note journal. Missing provenance, an
 # unexplained update/removal and collateral timing/clip changes fail closed.
 before={x['id']:x for x in event_rows(source)};actual={x['id']:x for x in event_rows(candidate)};replayed=deepcopy(before)
 for e in receipt['edits']:
  if not e['reason']:raise ValidationError('editorial reason required')
  if e['action'] in ('remove','update'):
   old=e['before']
   if replayed.get(old['id'])!=old:raise ValidationError('editorial journal precondition failed')
   if e['action']=='remove':del replayed[old['id']]
   else:
    if e['after']['id']!=old['id']:raise ValidationError('update cannot rename a retained note')
    replayed[old['id']]=e['after']
  elif e['action']=='add':
   new=e['after']
   if new['id'] in replayed or before.get(e['source']['id'])!=e['source']:raise ValidationError('invalid added-note lineage')
   replayed[new['id']]=new
  else:raise ValidationError('unknown editorial journal action')
 if actual!=replayed:raise ValidationError('editorial journal does not reproduce the complete note state')
 for a,b in zip(source.tracks,candidate.tracks):
  aa=asdict(a);bb=asdict(b);aa.pop('clips');bb.pop('clips')
  if aa!=bb:raise ValidationError('editorial audit detected changed instrument/mixer graph')
 if receipt['automation_before']!=[asdict(a) for a in source.automation] or receipt['automation_after']!=[asdict(a) for a in candidate.automation]:raise ValidationError('automation journal mismatch')
 harmonic=audit_composition(source,candidate,receipt)
 # Phase18's old 'all bridge bass must equal chord root' heuristic is not
 # applicable to this intentionally inherited C-pedal pocket with chord-tone
 # G/Bb/Eb pickups. Check its explicit anchors/colors instead of calling a
 # valid inversion/passing chord tone a wrong-key error.
 roots=[]
 for bar in range(64,80):
  bass=sorted([x for x in actual.values() if x['track_id']=='track-bass' and bar*BAR<=x['absolute_tick']<(bar+1)*BAR],key=lambda x:x['absolute_tick'])
  roots.append({'bar':bar+1,'first_bass':bass[0]['pitch'] if bass else None,'pitches':[x['pitch'] for x in bass],
    'C_anchor':bool(bass and bass[0]['pitch']==36),'color_all_C':all(x['pitch']==36 for x in bass) if 68<=bar<72 else None})
 failures=[x for x in roots if not x['C_anchor'] or x['color_all_C'] is False]
 src=groove_facts(source);dst=groove_facts(candidate)
 transitions=[]
 for b in (16,32,64,68,72,80,88,96,112,144,152):
  transitions.append({'zero_bar':b,'display_bar':b+1,'notes':[x for x in actual.values() if (b-1)*BAR<=x['absolute_tick']<(b+1)*BAR]})
 return {'version':'club-continuity-audit-1','source_facts':src,'candidate_facts':dst,'note_journal_exact':True,
  'retained_note_ids':sum(k in actual for k in before),'unchanged_note_records':sum(actual.get(k)==x for k,x in before.items()),
  'removed_note_records':sum(e['action']=='remove' for e in receipt['edits']),'updated_note_records':sum(e['action']=='update' for e in receipt['edits']),'added_note_records':sum(e['action']=='add' for e in receipt['edits']),
  'source_note_count':len(before),'candidate_note_count':len(actual),'harmonic':harmonic,'bridge_anchor_matrix':roots,'bridge_anchor_failures':failures,
  'transition_note_windows':transitions,'measured_pitch_offset_context':context(candidate),
  'interpretation':'Restraint and continuity, not a required novelty/signature-count score. Symbolic note activity does not transcribe ADSR/reverb tails or establish listener preference.'}


def require_flow(a):
 f=a['candidate_facts'];h=a['harmonic']
 if f['longest_kick_free_bars']>8 or not f['steady_four_floor_88_112'] or f['first_complete_signature_zero_bar'] is None or f['first_complete_signature_zero_bar']>24 or f['first_established_bass_drums_zero_bar']>=16:raise ValidationError('club continuity gate failed')
 if a['bridge_anchor_failures'] or any(h[x] for x in ('out_of_key_intervals','non_chord_harmonic_layer_intervals','non_chord_bass_intervals')):raise ValidationError('editorial harmony gate failed')
