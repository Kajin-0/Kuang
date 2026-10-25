"""Event-complete symbolic harmony/lineage audits, never a musical quality score.

The interval vocabulary is derived from chord qualities, independently of the
arranger's voiced MIDI tuples. Audio pitch and release/FX tails need separate
native controls; this is not waveform transcription or a dissonance detector.
"""
import hashlib,json
from collections import defaultdict
from dataclasses import asdict
from .schema import BAR,ValidationError,validate,state_hash

KEY={0,2,3,5,7,8,10}
QUALITIES={'Cm9':(0,(0,3,7,10,14)), 'Fm7-C':(5,(0,3,7,10,14)),
 'Fm7':(5,(0,3,7,10)), 'Abmaj9':(8,(0,4,7,11,14)),
 'Ebmaj9':(3,(0,4,7,11,14)), 'Fm9':(5,(0,3,7,10,14)),
 'Bbadd9':(10,(0,4,7,14)), 'Gm7':(7,(0,3,7,10))}
LOW={'track-bass','track-sub-pulse'}
LAYERS={'track-harmony','track-depth-pad','track-depth-air'}

def event_rows(p):
 return [{'track_id':t.id,'clip_id':c.id,'absolute_tick':c.start+n.start,**asdict(n)} for t in p.tracks for c in t.clips for n in c.notes]

def audit_composition(source,candidate,receipt):
 validate(candidate)
 if receipt['source_hash']!=state_hash(source) or receipt['candidate_hash']!=state_hash(candidate):raise ValidationError('composition receipt/hash drift')
 rows=event_rows(candidate);byid={x['id']:x for x in rows};origins=receipt['note_origins']
 if len(byid)!=len(rows) or set(byid)!=set(origins):raise ValidationError('one provenance entry required per actual note')
 original={x['id']:x for x in event_rows(source)}
 for nid,row in byid.items():
  o=origins[nid]
  if o['track_id']!=row['track_id'] or o['destination_tick']!=row['absolute_tick'] or o['display_bar']!=row['absolute_tick']//BAR+1 or o['note']!={k:row[k] for k in ('id','start','duration','pitch','velocity','channel')}:
   raise ValidationError('note provenance does not describe actual event')
  if o['source'] is not None and o['source']!=original.get(o['source']['id']):raise ValidationError('source note origin invented')
 protected=[x for x in event_rows(source) if 32*BAR<=x['absolute_tick']<48*BAR]
 for old in protected:
  if byid.get(old['id'])!=old:raise ValidationError('approved first statement changed')
  new=byid.get('phase18-return-'+old['id'])
  if new is None:raise ValidationError('approved return note missing')
  for key in ('duration','pitch','velocity','channel'):
   if new[key]!=old[key]:raise ValidationError('translated approved performance altered')
  if new['absolute_tick']!=old['absolute_tick']+80*BAR:raise ValidationError('translated approved onset altered')
 # Exact phrases are recognized as intentional returns. Distinct signatures
 # ignore IDs and velocity, so a loudness nudge is not counted as new music.
 phrases=[]
 for first in range(0,candidate.bars,8):
  group=[x for x in rows if first*BAR<=x['absolute_tick']<(first+8)*BAR]
  musical=sorted((x['track_id'],x['absolute_tick']-first*BAR,x['duration'],x['pitch']) for x in group)
  pitches=sorted((x['track_id'],x['absolute_tick']-first*BAR,x['duration'],x['pitch']) for x in group if x['track_id'] not in {'track-kick','track-snare','track-snare.p38','track-hats','track-hats.p46','track-percussion'})
  signature=hashlib.sha256(json.dumps(musical,separators=(',',':')).encode()).hexdigest()
  phrases.append({'first_bar':first+1,'signature_without_velocity':signature,'notes':len(group),'pitched_events':len(pitches),'active_tracks':sorted({x['track_id'] for x in group}),'function':receipt['phrases'][first//8]['function']})
 # Sweep EVERY note-on, note-off and bar boundary; no sparse chord sampling.
 changes=defaultdict(lambda:{'on':[],'off':[]})
 for x in rows:
  if x['track_id'] in LOW|LAYERS|{'track-lead','track-arp'}:
   changes[x['absolute_tick']]['on'].append(x);changes[x['absolute_tick']+x['duration']]['off'].append(x)
 for b in range(candidate.bars+1):changes[b*BAR]
 times=sorted(changes);active={};intervals=[];bad_key=[];bad_harmony=[];bad_bass=[];colors=[]
 plan=receipt['harmonic_plan']
 if len(plan)!=candidate.bars:raise ValidationError('one harmonic plan per bar required')
 for lo,hi in zip(times,times[1:]):
  for x in changes[lo]['off']:active.pop(x['id'],None)
  for x in changes[lo]['on']:active[x['id']]=x
  bar=lo//BAR;ch=plan[bar];root,quality=QUALITIES[ch['name']];pcs={(root+i)%12 for i in quality}
  bass=sorted({x['pitch'] for x in active.values() if x['track_id'] in LOW})
  upper=sorted({x['pitch'] for x in active.values() if x['track_id'] in LAYERS})
  lead=sorted({x['pitch'] for x in active.values() if x['track_id'] in ('track-lead','track-arp')})
  for x in active.values():
   info={'note_id':x['id'],'track':x['track_id'],'pitch':x['pitch'],'start_tick':lo,'end_tick':hi,'bar':bar+1,'chord':ch['name']}
   if x['pitch']%12 not in KEY:bad_key.append(info)
   if x['track_id'] in LAYERS and x['pitch']%12 not in pcs:bad_harmony.append(info)
   if x['track_id'] in LOW and x['pitch']%12 not in pcs:bad_bass.append(info)
   if x['track_id'] in ('track-lead','track-arp') and x['pitch']%12 not in pcs:
    colors.append({**info,'interval_above_chord_root':(x['pitch']-root)%12,'interpretation':'diatonic melodic color/passing tone, not a claimed chord member'})
  if bass or upper or lead:
   intervals.append({'start_tick':lo,'end_tick':hi,'bar':bar+1,'chord':ch['name'],'bass':bass,'upper':upper,'melody':lead,
                     'upper_intervals_above_actual_bass':{str(b):[(u-b)%12 for u in upper] for b in bass}})
 # During B every played bass event must be the declared root, not just in-key.
 wrong_bridge=[x['id'] for x in rows if x['track_id']=='track-bass' and 64*BAR<=x['absolute_tick']<80*BAR and x['pitch']!=plan[x['absolute_tick']//BAR]['root_midi']]
 voice_leading=[]
 for bar in range(65,80):
  old=plan[bar-1]['upper_voicing'];new=plan[bar]['upper_voicing']
  if old!=new:voice_leading.append({'bar':bar+1,'semitones':[b-a for a,b in zip(old,new)]})
 result={'version':'composition-event-audit-1','scope':'All symbolic active-note intervals. Synth release and FX tails are NOT transcribed. Minor seconds/ninths are reported as intervals, not automatically declared bad.',
 'notes':len(rows),'all_note_origins_exact':True,'approved_first_statement_exact':len(protected),'approved_translated_return_exact':len(protected),
 'phrases':phrases,'unique_eight_bar_signatures_without_velocity':len({x['signature_without_velocity'] for x in phrases}),
 'out_of_key_intervals':bad_key,'non_chord_harmonic_layer_intervals':bad_harmony,'non_chord_bass_intervals':bad_bass,
 'bridge_wrong_root_note_ids':wrong_bridge,'bridge_voice_leading':voice_leading,'melodic_color_intervals':colors,'concurrent_intervals':intervals}
 return result
