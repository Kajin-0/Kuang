"""Phase19 editorial restraint on Phase18; no instrument or mixer novelty.

This is an independent opt-in arrangement editor. Retained IDs/order survive;
every removal, revoicing and added descendant has an explicit source record.
"""
import json
from copy import deepcopy
from dataclasses import asdict
from .schema import BAR,PPQ,Clip,Note,Section,AutomationLane,AutomationPoint,ValidationError,validate,state_hash
from .gestures import lane_value
from .production_host import graph_contract,trim_id
from .ensemble_production import PAN_COMPENSATION_DB
from .composition_analysis import event_rows,audit_composition
from .house_composition import CHORDS,harmony_at as phase18_harmony

SOURCE_HASH='185d3617f729aeeb2e48d668965f4a84a9aaf051a5a1bcbbe9c811a43561c1f1'
VERSION='club-flow-editorial-1'
FORM=(('intro','DJ pocket and early identity',0,16),('theme','Established signature',16,16),
 ('peak','First sustained high point',32,32),('color','Same-song pedal color',64,16),
 ('break','Eight-bar breathing space',80,8),('recover','Kick and theme recover',88,8),
 ('rise','Continuous rhythmic rise',96,16),('return','Signature payoff',112,32),
 ('outro','DJ withdrawal and mix out',144,16))
FUNCTIONS=(
 'Eight clean four-floor bars; familiar filtered chord hint',
 'Bass pocket arrives at8; G then G-Eb tease at12/14',
 'Complete approved G-Eb-F calls and Bb-G replies from16',
 'Repeat the same theme; percussion/filters supply development',
 'Approved608-note pocket, first half unchanged',
 'Approved608-note pocket, second half unchanged',
 'Same signature calls over retained bass/stab articulation',
 'Same call continues; familiar percussion fill announces color',
 'C pedal, four bars of familiar Fm9/C color, no rotating roots',
 'Cm9 restores; offbeat open hats hand back the familiar energy',
 'Only eight kick-free bars; familiar augmented hook and quiet hat clock',
 'Kick/clap/hats and the signature recover at88, before96',
 'Full pocket continues; no new countertheme or missing kick',
 'Open filters over firm four-floor; brief harmonic space before112',
 'Approved translated608-note return, first half unchanged',
 'Approved translated608-note return, second half unchanged',
 'Familiar G-Eb-F payoff; existing Bb-G answers stay in their gaps',
 'Keep identity through the last peak; use touch/FX rather than a new riff',
 'Existing quiet farewell and harmonic/bass withdrawal retained',
 'Existing clean eight-bar drum mix-out retained')


def harmony_at(bar):
 if not 0<=bar<160:raise ValidationError('club-flow bar outside160-bar score')
 if 64<=bar<80:return 'Fm7-C' if 68<=bar<72 else 'Cm9'
 if 80<=bar<112:return 'Cm9'
 return phase18_harmony(bar)


def refine_flow(source):
 validate(source)
 if state_hash(source)!=SOURCE_HASH or source.locks:raise ValidationError('exact unlocked Phase18 reference required')
 p=deepcopy(source);p.id='project-phase19-club-flow';p.name='Kuang / Return to the pocket — club continuity'
 p.sections=[Section('phase19-'+key,name,start*BAR,bars*BAR) for key,name,start,bars in FORM]
 oldrows=event_rows(source);oldbyid={x['id']:x for x in oldrows};byid={t.id:t for t in p.tracks}
 rows={t.id:[x for x in oldrows if x['track_id']==t.id] for t in source.tracks}
 changes=[];origins={x['id']:{'track_id':x['track_id'],'destination_tick':x['absolute_tick'],'display_bar':x['absolute_tick']//BAR+1,'beat':x['absolute_tick']%BAR/PPQ+1,'reason':'Retained Phase18 event','source':deepcopy(x),'note':{k:x[k] for k in ('id','start','duration','pitch','velocity','channel')}} for x in oldrows}
 serial=0
 def remove(tid,first,last,reason):
  for c in byid[tid].clips:
   kept=[]
   for n in c.notes:
    at=c.start+n.start
    if first*BAR<=at<last*BAR:
     if at+n.duration>last*BAR:raise ValidationError('editorial removal crosses declared boundary')
     changes.append({'action':'remove','before':deepcopy(oldbyid[n.id]),'reason':reason});origins.pop(n.id);continue
    if at<first*BAR<at+n.duration:raise ValidationError('editorial scope crosses a held note')
    kept.append(n)
   c.notes=kept
 def add(tid,src,dest,reason,pitch=None,velocity=None):
  nonlocal serial
  serial+=1;at=round(dest);n=Note('phase19-note-'+str(serial),0,src['duration'],src['pitch'] if pitch is None else pitch,src['velocity'] if velocity is None else velocity,src['channel'])
  c=next((c for c in byid[tid].clips if c.start<=at and at+n.duration<=c.start+c.length),None)
  if c is None:
   start=at//(8*BAR)*8*BAR;c=Clip('phase19-clip-'+tid+'-'+str(start//BAR),FUNCTIONS[start//(8*BAR)],'midi',start,8*BAR,[],None);byid[tid].clips.append(c)
  n.start=at-c.start;c.notes.append(n)
  origins[n.id]={'track_id':tid,'destination_tick':at,'display_bar':at//BAR+1,'beat':at%BAR/PPQ+1,'reason':reason,'source':deepcopy(src),'note':asdict(n)}
  changes.append({'action':'add','after':{'track_id':tid,'clip_id':c.id,'absolute_tick':at,**asdict(n)},'source':deepcopy(src),'reason':reason})
 def copy(tid,first,bars,dest,reason,keep=lambda x,b:True,repitch=lambda x,b:x['pitch'],trim=0):
  for x in rows[tid]:
   if not first*BAR<=x['absolute_tick']<(first+bars)*BAR:continue
   at=x['absolute_tick']+(dest-first)*BAR;b=at//BAR
   if keep(x,b):add(tid,x,at,reason,repitch(x,b),max(1,min(120,x['velocity']+trim)))
 def core(tid,first,bars,reason,keep=lambda x,b:True,repitch=lambda x,b:x['pitch'],trim=0):
  for dest in range(first,first+bars,16):copy(tid,32,min(16,first+bars-dest),dest,reason,keep,repitch,trim)
 def revoice(tid,first,last,tones,reason):
  # Chord groups are explicit simultaneous source events (4-tick hand spread),
  # not parsed IDs or a blind transpose of unrelated voices.
  entries=sorted([(c.start+n.start,c,n) for c in byid[tid].clips for n in c.notes if first*BAR<=c.start+n.start<last*BAR],key=lambda x:(x[0],x[2].pitch))
  groups=[]
  for item in entries:
   if not groups or item[0]-groups[-1][0][0]>16:groups.append([])
   groups[-1].append(item)
  for group in groups:
   desired=tones(group[0][0]//BAR)
   if len(group)!=len(desired):raise ValidationError('explicit chord voice count mismatch')
   for (_,c,n),pitch in zip(sorted(group,key=lambda x:x[2].pitch),desired):
    if n.pitch==pitch:continue
    before=deepcopy(oldbyid[n.id]);n.pitch=pitch;origins[n.id]['note']=asdict(n);origins[n.id]['reason']=reason
    changes.append({'action':'update','before':before,'after':{'track_id':tid,'clip_id':c.id,'absolute_tick':c.start+n.start,**asdict(n)},'reason':reason})
 # Establish the rhythm section in the second intro half; keep first8 mixable.
 remove('track-bass',8,16,'Replace isolated teasers with an established pocket')
 core('track-bass',8,8,'Earlier danceable bass pocket',keep=lambda x,b:b>=12 or x['absolute_tick']%BAR//240 in (2,10))
 remove('track-lead',0,32,'Earlier complete identity instead of prolonged partial previews')
 g=next(x for x in rows['track-lead'] if x['absolute_tick']==32*BAR)
 add('track-lead',g,12*BAR,'One quiet G identity hint',velocity=g['velocity']-14)
 for x in [x for x in rows['track-lead'] if 32*BAR<=x['absolute_tick']<32*BAR+PPQ]:add('track-lead',x,x['absolute_tick']-18*BAR,'Quiet two-note G-Eb intro question',velocity=x['velocity']-10)
 core('track-lead',16,16,'Complete approved signature establishes at16')
 remove('track-arp',16,32,'Keep the established original call/response pairing')
 core('track-arp',16,16,'Familiar Bb-G response to the main signature')
 # Restraint at both developed high points: keep the voice, not a countertheme.
 for first in (48,128):
  remove('track-lead',first,first+16,'Remove competing answer/eighth-displacement, retain signature identity')
  core('track-lead',first,16,'Same G-Eb-F signature; existing bass/stab/FX articulation develops it')
 # Bridge stays on the C pedal with ONE short neighboring color.
 remove('track-bass',64,80,'Remove rotating Ab/Eb/F/Bb bass roots')
 core('track-bass',64,16,'Approved interlocking bass rhythm on the same C pedal',repitch=lambda x,b:36 if 68<=b<72 else x['pitch'])
 revoice('track-harmony',64,80,lambda b:CHORDS[harmony_at(b)][1],'Gentle Cm9-Fm9/C-Cm9 color; original chord rhythm/articulation retained')
 revoice('track-depth-pad',64,80,lambda b:(63,68,79) if 68<=b<72 else (63,70,74),'Same-song upper-voice color over the C pedal')
 remove('track-lead',64,80,'Remove two independent eight-bar bridge melodies')
 core('track-lead',64,16,'Bridge reframes the signature every four bars',keep=lambda x,b:b%4==0,trim=-6)
 core('track-arp',64,16,'Familiar sparse response instead of new bridge melody',keep=lambda x,b:b%4==1,trim=-5)
 core('track-hats.p46',72,8,'Offbeat open-hat handoff reconnects bridge to the pocket',trim=-4)
 # Eight-bar breakdown, not a24-bar kick-free breakdown+rebuild sequence.
 revoice('track-harmony',80,88,lambda b:CHORDS['Cm9'][1],'Breakdown keeps the home harmony and familiar augmented hook')
 revoice('track-depth-pad',80,88,lambda b:(63,70,74),'Home Cm9 pad rather than another harmonic departure')
 hat=next(x for x in rows['track-hats'] if x['absolute_tick']==32*BAR+492)
 for b in range(80,88):
  for beat in range(4):add('track-hats',hat,b*BAR+beat*PPQ+492,'Quiet offbeat timekeeping through the eight-bar break',velocity=44 if beat%2==0 else 48)
 # Actual kick onsets, not labels. Keep all four beats through88..112.
 core('track-kick',88,16,'Firm kick returns at88 and continues through the rebuild')
 last=next(x for x in rows['track-kick'] if x['absolute_tick']==32*BAR+3*PPQ)
 add('track-kick',last,111*BAR+3*PPQ,'Retain downbeat certainty across the one-beat harmonic gap')
 core('track-snare',88,12,'Restore familiar backbeat alongside the kick')
 for tid in ('track-hats','track-hats.p46'):
  remove(tid,88,104,'Restore the established offbeat hat pocket')
  core(tid,88,16,'Same hat articulation/accents through the rebuild')
 core('track-percussion',88,12,'Shuffled timekeeping returns with the kick')
 remove('track-bass',88,112,'Replace prolonged weak/absent bass rebuild with the same pocket')
 core('track-bass',88,24,'Firm familiar bass returns before96',keep=lambda x,b:(b>=92 or x['absolute_tick']%BAR//240 in (2,10)) and not(b==111 and x['absolute_tick']%BAR>=3*PPQ))
 remove('track-harmony',88,112,'Restore the original chord articulation before the final peak')
 core('track-harmony',88,24,'Home Cm9 original stab rhythm; no new countertheme',keep=lambda x,b:b>=92 or x['absolute_tick']%BAR<2*PPQ,repitch=lambda x,b:(51,55,58,62)[CHORDS['Fm7-C'][1].index(x['pitch'])] if x['pitch'] in (53,56,60,63) else x['pitch'])
 # The voicing expression above uses original ordered four-voice descendants:
 # source Cm9 pitches remain, source Fm7/C voices map by their source voice.
 revoice('track-depth-pad',88,112,lambda b:(63,70,74),'Home pad supports the restored pocket instead of Eb/Gm departures')
 remove('track-lead',88,112,'Remove descending breakdown countertheme and D-Eb-F rebuild pickup')
 core('track-lead',88,24,'Signature returns with the kick, with space between four-bar calls',keep=lambda x,b:b%4==0,trim=-5)
 core('track-arp',88,24,'Original response on alternate bars of the recovered groove',keep=lambda x,b:b%4==1,trim=-4)
 for t in p.tracks:
  t.clips=[c for c in t.clips if c.notes];t.clips.sort(key=lambda c:c.start)
 _automation(p,source)
 p.metadata.update(phase18_human_verdict='potential, but awkward/amateur/confusing dance-floor flow; not approved club song',
  phase19_source_hash=SOURCE_HASH,phase19_arranger_version=VERSION,phase19_preference='unreviewed',
  phase19_notes='Editorial restraint: complete signature16, bass pocket8, C-pedal bridge with one four-bar Fm9/C color, only8kick-free bars80..88, actual four-floor88..112, original signature at high points; same instruments and mixer graph.',
  phase19_form=json.dumps(FORM),phase19_functions=json.dumps(FUNCTIONS))
 graph_contract(p)
 for old,new in zip(source.tracks,p.tracks):
  a=asdict(old);b=asdict(new);a.pop('clips');b.pop('clips')
  if a!=b:raise ValidationError('editorial flow changed the approved sound/mixer graph')
 # Final per-note facts are recomputed from actual objects, not inferred counts.
 actual=event_rows(p)
 for x in actual:
  o=origins[x['id']];o.update(destination_tick=x['absolute_tick'],display_bar=x['absolute_tick']//BAR+1,beat=x['absolute_tick']%BAR/PPQ+1,note={k:x[k] for k in ('id','start','duration','pitch','velocity','channel')})
 receipt={'version':VERSION,'source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'not_transaction_receipt':True,'MIDI_bytes_exact':False,
  'sections':[asdict(s) for s in p.sections],'phrases':[{'first_bar':i*8+1,'bars':8,'function':x} for i,x in enumerate(FUNCTIONS)],
  'harmonic_plan':[{'bar':b+1,'name':harmony_at(b),'root_midi':CHORDS[harmony_at(b)][0],'upper_voicing':list(CHORDS[harmony_at(b)][1])} for b in range(160)],
  'note_origins':origins,'edits':changes,'automation_before':[asdict(a) for a in source.automation],
  'automation_after':[asdict(a) for a in p.automation],'sound_graph_exact':True,'human_preference':'unreviewed'}
 return p,receipt


def _automation(p,source):
 """Keep the approved base graph; compress only the editorial performance arc."""
 def replace(owner,key,first,last,points,label):
  a=next(x for x in p.automation if x.target_id==owner and x.parameter_id==key)
  old=deepcopy(a);kept=[x for x in a.points if not first*BAR<=x.tick<last*BAR]
  values=dict(points)
  # Preserve the value/shape immediately before and after the explicit window.
  if first>0:values.setdefault(first*BAR-1,lane_value(old,first*BAR-1))
  values.setdefault(last*BAR,lane_value(old,last*BAR))
  kept=[x for x in kept if x.tick not in values]
  kept += [AutomationPoint('phase19-'+label+'-'+str(i),round(t),v,'linear') for i,(t,v) in enumerate(sorted(values.items()))]
  a.points=sorted(kept,key=lambda x:x.tick)
 # Audible early identity, eight-bar break and a rhythm-supported rise. The
 # original32..48 and112..128 performances remain outside these edit windows.
 for tid in ('track-harmony','track-lead','track-arp','track-depth-pad','track-depth-air'):
  t=next(t for t in p.tracks if t.id==tid);eq=next(e for e in t.effects if e.plugin_ref=='soundcraft:eq_7band')
  scale=.4 if tid=='track-depth-pad' else .65 if tid=='track-depth-air' else 1
  replace(eq.id,'soundcraft.lpf_freq',0,32,[(round(b*BAR),max(1000,v*scale)) for b,v in ((0,1100),(8,2600),(12,4000),(16,6500),(24,8000),(31.75,9500))],'early-tone-'+tid)
  replace(eq.id,'soundcraft.lpf_freq',64,112,[(round(b*BAR),max(1000,v*scale)) for b,v in ((64,5000),(68,4000),(72,5500),(79.75,6500),(80,2400),(84,3000),(87.9,4200),(88,5000),(96,6500),(104,7500),(110,9500),(111.75,11000))],'arc-tone-'+tid)
  if tid in ('track-harmony','track-lead','track-arp'):
   resting=eq.parameters['soundcraft.hpf_freq']
   replace(eq.id,'soundcraft.hpf_freq',64,112,[(round(b*BAR),v) for b,v in ((64,resting),(80,resting),(88,resting),(96,resting),(104,max(resting,210)),(110,350),(111.75,500))],'arc-hpf-'+tid)
 for tid in ('track-harmony','track-depth-pad','track-depth-air'):
  a=next(x for x in source.automation if x.target_id==tid and x.parameter_id=='mixer.gain_db')
  pts=[(88*BAR+x.tick-32*BAR,x.value) for x in a.points if 32*BAR<=x.tick<40*BAR]
  replace(tid,'mixer.gain_db',88,96,pts,'recovered-pump-'+tid)
 # Re-key sends to actual edited notes, with fewer throws outside protected peaks.
 for tid in ('track-harmony','track-lead','track-arp'):
  t=next(t for t in p.tracks if t.id==tid);s=next(s for s in t.sends if s.target_track_id=='phase17-echo');key=trim_id(s)
  for lo,hi in ((0,32),(48,112),(128,160)):
   points={lo*BAR:-60,hi*BAR:-60}
   for b in range(lo,hi,4):
    events=[(c.start+n.start,n.duration) for c in t.clips for n in c.notes if b*BAR<=c.start+n.start<(b+4)*BAR]
    if not events:continue
    at,duration=max(events);end=min(at+duration+60,hi*BAR-97)
    points.update({max(lo*BAR,at-24):-60,at:0,end:0,end+96:-60})
   replace(tid,key,lo,hi,points.items(),'throws-'+tid+'-'+str(lo))
 kicks=sorted({c.start+n.start for t in p.tracks if t.id=='track-kick' for c in t.clips for n in c.notes})
 def ticks(ms):return round(ms/1000*p.tempo_bpm/60*p.ppq)
 for tid,depth in (('phase17-dark-space',6),('phase17-echo',4)):
  a=next(a for a in p.automation if a.target_id==tid and a.parameter_id=='mixer.gain_db');times={0,p.length}
  for bar in (16,32,64,68,72,80,88,96,104,112,144,152):times.update((bar*BAR-1,bar*BAR))
  for k in kicks:times.update(max(0,min(p.length,x)) for x in (k-1,k,k+ticks(25),k+ticks(75),k+ticks(165)))
  points=[]
  for at in sorted(times):
   b=at/BAR;level=1 if 80<=b<88 else -2 if 16<=b<64 or 112<=b<144 else -4 if b>=144 else -1
   distances=[at-k for k in kicks if 0<=at-k<=ticks(165)];duck=0
   if distances:
    d=min(distances);duck=-depth if d<=ticks(25) else -depth*(ticks(165)-d)/(ticks(165)-ticks(25))
   points.append(AutomationPoint('phase19-breathe-'+tid+'-'+str(len(points)),at,PAN_COMPENSATION_DB+level+duck,'linear'))
  a.points=points
