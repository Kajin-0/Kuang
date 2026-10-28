"""Opt-in functional development of the Phase25 record, with its pocket intact."""
from copy import deepcopy
from dataclasses import asdict
from collections import defaultdict
from .schema import BAR,PPQ,Clip,Note,ValidationError,state_hash,validate
from .composition_analysis import event_rows
from .chord_bed import CHORDS,THEORY
from .master_bus import terminal_projection
SOURCE_HASH='a6109969c1d6d914adf4f5a2bce807858555ee7ba879b0bb6c8aa9a8f6f7e494'
VOICES={'i':(55,60,63),'iv':(56,60,65),'Vsus':(55,60,65),'V':(55,59,65)}
PCS={'i':{0,2,3,7,10},'iv':{5,7,8,0,3},'Vsus':{7,0,2,5},'V':{7,11,2,5}}
PADS={'i':(58,62,67),'iv':(60,63,68),'Vsus':(62,67),'V':(62,67)}

def function(bar):
 if 16<=bar<32:return CHORDS[bar%16]
 if bar<32 or bar>=128:return 'i'
 phase=(bar-32)%16
 return 'i' if phase<8 else 'iv' if phase<12 else 'Vsus' if phase<14 else 'V'

def compose_direction(source):
 validate(source);terminal_projection(source)
 if source.locks or state_hash(source)!=SOURCE_HASH:raise ValidationError('exact unlocked Phase25 source required')
 p=deepcopy(source);p.id='project-phase26-direction';p.name='Kuang / Stay in the pocket — home and return'
 origins={x['id']:x for x in event_rows(source)};journal=[]
 def record(action,before,after,reason):journal.append({'action':action,'before':before,'after':after,'reason':reason})
 for t in p.tracks:
  if t.id=='track-depth-pad':continue
  for c in t.clips:
   groups=defaultdict(list)
   for n in c.notes:groups[(c.start+n.start)//BAR,((c.start+n.start)%BAR)//16].append(n)
   for (bar,_),notes in groups.items():
    if 16<=bar<32:continue
    f=function(bar)
    if t.id=='track-harmony':
     for n,pitch in zip(sorted(notes,key=lambda n:n.pitch),VOICES[f]):n.pitch=pitch
    elif t.id in ('track-bass','track-sub-pulse'):
     for n in notes:
      if f=='iv':n.pitch+=5
      elif f in ('Vsus','V'):
       n.pitch+=7
       if n.pitch%12==10:n.pitch+=2 if f=='Vsus' else 1
   keep=[]
   for n in c.notes:
    at=c.start+n.start;bar=at//BAR;old=origins[n.id]
    remove=(t.id=='track-harmony' and bar<12 or t.id=='track-hats.p46' and bar<12 or t.id=='track-hats' and bar<4 and at%PPQ<PPQ//2)
    if remove:record('remove',old,None,'Intro hierarchy: kick/offbeat clock, then backbeat, bass at8, upper reveal at12');continue
    keep.append(n)
    if n.pitch!=old['pitch']:record('pitch',old,n.pitch,'Bass-supported '+function(bar)+'; retain onset, gate, accent, ID and strum')
   c.notes=keep
 # Replace only non-anchor sustained upper notes. Two dominant pad tones are
 # common to sus, dominant and tonic9, avoiding a held B/C collision.
 pad=next(t for t in p.tracks if t.id=='track-depth-pad');oldpad=[x for x in origins.values() if x['track_id']==pad.id]
 kept=[]
 for c in pad.clips:
  if 16*BAR<=c.start<32*BAR:kept.append(c)
  else:
   for n in c.notes:record('replace-pad',origins[n.id],None,'Rearticulate sustained backing at functional boundaries; preserve approved anchor')
 pad.clips=kept
 spans=[(12,16,'i')]
 for start in range(32,128,16):spans.extend([(start,start+8,'i'),(start+8,start+12,'iv'),(start+12,start+16,'Vsus')])
 spans.append((128,132,'i'))
 for lo,hi,f in spans:
  # 2s dry-release clearance before each harmonic boundary. Dominant pad
  # contains only D/G; no leading tone is held through the tonic arrival.
  gate=(hi-lo)*BAR-PPQ//4-round(2*126/60*PPQ)
  notes=[]
  for i,pitch in enumerate(PADS[f]):
   n=Note(f'phase26-pad-{lo}-{i}',PPQ//4,gate,pitch,58 if lo<16 else 62-i*2,0);notes.append(n)
   nearest=min(oldpad,key=lambda x:abs(x['pitch']-pitch))
   record('pad',nearest,{'clip_start':lo*BAR,**asdict(n)},'Shared-tone '+f+' sustain; explicit2s dry release, common D/G over V and resolution')
  pad.clips.append(Clip('phase26-pad-'+str(lo),'Functional '+f+' bed','midi',lo*BAR,(hi-lo)*BAR,notes,None))
 pad.clips.sort(key=lambda c:c.start)
 # Existing continuous lane identities and anchor points remain intact.
 for a in p.automation:
  for x in a.points:
   if x.tick>=16*BAR:continue
   bar=x.tick/BAR
   if a.target_id=='track-kick' and a.parameter_id=='mixer.gain_db':x.value-=2*(1-bar/16)
   if a.target_id in ('track-harmony','track-depth-pad') and a.parameter_id=='mixer.gain_db':x.value-=max(0,(16-bar)*.75)
   if a.target_id=='effect-harmony-eq' and a.parameter_id=='soundcraft.lpf_freq':x.value=min(x.value,1000+max(0,bar-12)*450)
   if a.target_id=='effect-depth-pad-eq' and a.parameter_id=='soundcraft.lpf_freq':x.value=min(x.value,1000+max(0,bar-12)*150)
 p.metadata.update(phase26_source_hash=SOURCE_HASH,phase26_version='functional-direction-1',phase26_preference='unreviewed')
 validate(p);terminal_projection(p)
 return p,{'version':'functional-direction-1','source_hash':state_hash(source),'candidate_hash':state_hash(p),'events':journal,'harmony':[function(b) for b in range(144)],'human_preference':'unreviewed','mastering':False}

def audit_direction(source,p,receipt):
 q,r=compose_direction(source)
 if p!=q or receipt!=r:raise ValidationError('undeclared composition or receipt drift')
 a=event_rows(source);b=event_rows(p)
 anchor=lambda rows:[x for x in rows if 16*BAR<=x['absolute_tick']<32*BAR]
 if anchor(a)!=anchor(b):raise ValidationError('anchor MIDI drift')
 for x,y in zip(source.tracks,p.tracks):
  u,v=asdict(x),asdict(y);u.pop('clips');v.pop('clips')
  if u!=v:raise ValidationError('sound or graph drift')
 for x,y in zip(source.automation,p.automation):
  if [asdict(z) for z in x.points if z.tick>=16*BAR]!=[asdict(z) for z in y.points if z.tick>=16*BAR]:raise ValidationError('later performance drift')
 old={x['id']:x for x in a};bad=[]
 for x in b:
  bar=x['absolute_tick']//BAR;f=function(bar)
  if x['track_id'] in ('track-bass','track-sub-pulse'):
   if {k:v for k,v in x.items() if k!='pitch'}!={k:v for k,v in old[x['id']].items() if k!='pitch'}:raise ValidationError('bass pocket drift')
  if x['track_id'] in ('track-bass','track-sub-pulse','track-harmony','track-depth-pad'):
   root,quality=THEORY[f] if f in THEORY else (0,PCS[f]);pcs={(root+i)%12 for i in quality}
   if x['pitch']%12 not in pcs:bad.append(x['id'])
 if bad:raise ValidationError('functional chord membership '+str(bad[:3]))
 # Dry release sweep, including harmony changes and the B-natural resolution.
 ev=defaultdict(lambda:[[],[]]);tails={'track-depth-pad':2.,'track-harmony':.20,'track-bass':.03,'track-sub-pulse':.03}
 for x in b:
  if x['track_id'] in tails:
   ev[x['absolute_tick']][0].append(x);ev[min(p.length,x['absolute_tick']+x['duration']+round(tails[x['track_id']]*126/60*PPQ))][1].append(x)
 for bar in range(145):ev[bar*BAR]
 active={};windows=0
 for tick in sorted(ev)[:-1]:
  for x in ev[tick][1]:active.pop(x['id'],None)
  for x in ev[tick][0]:active[x['id']]=x
  f=function(tick//BAR);root,quality=THEORY[f] if f in THEORY else (0,PCS[f]);pcs={(root+i)%12 for i in quality}
  if any(x['pitch']%12 not in pcs for x in active.values()):raise ValidationError('sounding/releasing functional clash at '+str(tick/BAR))
  windows+=1
 return {'notes':len(b),'anchor_notes_exact':len(anchor(b)),'sound_graph_exact':True,'bass_pitch_only':True,'release_intervals':windows,'harmonic_errors':bad,'harmonic_plan':receipt['harmony'],'cadence_landings':[48,64,80,96,112,128],'human_preference':'unreviewed','FX_tail_consonance_certified':False}
