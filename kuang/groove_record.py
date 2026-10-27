"""Opt-in 144-bar development of the approved melody-free Phase23 groove.

No new source or default compiler. The complete original performance/lanes
occupy bars16..32; every other event is a documented original descendant.
"""
import hashlib
import json
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict

from .schema import BAR, PPQ, Clip, Note, Section, AutomationPoint, ValidationError, state_hash, validate
from .chord_bed import PROTECTED, UPPER, REMOVED, CHORDS, THEORY, VOICINGS
from .composition_analysis import event_rows
from .gestures import lane_value
from .master_bus import terminal_projection
from .production_host import trim_id

SOURCE_HASH = '01cd20283cc8fe4e4e43b919d405f07367e6d5327a02b007cd39dcb4afa502b0'
VERSION = 'melody-free-record-1'
FORM = (('intro', 'DJ pocket and chord reveal', 0, 16),
        ('groove', 'Approved groove and opening development', 16, 32),
        ('variation', 'Chord-space conversation', 48, 16),
        ('break', 'Eight-bar harmonic breathing space', 64, 8),
        ('rebuild', 'Kick-led anticipation', 72, 8),
        ('return', 'Recognizable full return and open response', 80, 32),
        ('late', 'Lower pad and guide-tone development', 112, 16),
        ('outro', 'Sixteen-bar DJ withdrawal', 128, 16))
FUNCTIONS = (
 'Clean kick/closed-hat mix-in; clap at4 and a filtered chord hint',
 'Original bass establishes at8; open hats and sparse chord identity',
 'Approved first eight bars: exact notes, devices and performance lanes',
 'Approved second eight bars: exact notes, devices and performance lanes',
 'Repeat the recognizable chord pocket with longer fourth-bar replies',
 'First high point: harmonic filter reveal and a phrase-end echo',
 'Rootless inversion, empty response bars and shifted chord articulation',
 'Same C pedal, softer pad color; two ghost taps prepare the short break',
 'Exactly eight kick-free bars; quiet offbeat hat clock and held chord fragments',
 'Kick/bass recover at72; short chords and filtered anticipation resolve at80',
 'Familiar full pocket returns; original chord attacks over a longer pad sustain',
 'Full groove stays firm while the pad/filtered echo expands its space',
 'Held chord answers, sustained Bb color and a quieter spectral valley',
 'Open guide voicing and brightest harmonic reveal; kick survives the turn',
 'Lower Bb/Eb pad voices support familiar chord rhythm and shared tones',
 'Late harmonic release, not a new melody; final measured ghost-snare handoff',
 'Bass/chords withdraw in stages; pad and filtered tails resolve',
 'Eight unpitched four-floor mix-out bars; hats and percussion finish the meter')
WINDOWS = ((0,16),(32,48),(48,64),(64,72),(72,80),(80,112),(112,128),(128,144))
OPEN = {'Cm9': (55,58,62), 'Cm11': (53,58,63), 'Abmaj9-C': (56,58,63)}
LATE = {**OPEN, 'Cm11': (53,58,67)}


def _value(knots, tick):
    if tick <= knots[0][0]: return knots[0][1]
    for (a,x),(b,y) in zip(knots,knots[1:]):
        if tick <= b: return x+(y-x)*(tick-a)/(b-a)
    return knots[-1][1]


def arrange_groove(source):
    validate(source); terminal_projection(source)
    if source.locks or state_hash(source) != SOURCE_HASH:
        raise ValidationError('exact unlocked human-approved Phase23 source required')
    p=deepcopy(source);p.id='project-phase24-groove-record';p.name='Kuang / Stay in the pocket — extended';p.bars=144
    p.sections=[Section('phase24-'+key,name,first*BAR,length*BAR) for key,name,first,length in FORM]
    old=event_rows(source);by={t.id:t for t in p.tracks};src={t.id:[x for x in old if x['track_id']==t.id] for t in source.tracks}
    origins={};clips={};serial=Counter()
    for t in p.tracks:t.clips=[]
    # Original ownership/IDs/order and all relative note fields survive intact.
    for t in source.tracks:
        for c in t.clips:
            q=deepcopy(c);q.start+=16*BAR;by[t.id].clips.append(q)
            for n in q.notes:
                x=next(x for x in src[t.id] if x['id']==n.id)
                origins[n.id]={'source':x,'reason':'Exact approved16-bar anchor, translated16bars'}
    def put(tid,at,gate,pitch,velocity,origin,reason):
        at=round(at);gate=round(gate)
        window=next(((lo,hi) for lo,hi in WINDOWS if lo*BAR<=at and at+gate<=hi*BAR),None)
        if window is None or gate<=0:raise ValidationError('new event crosses section/anchor boundary')
        key=(tid,window)
        if key not in clips:
            lo,hi=window;c=Clip('phase24-'+tid+'-'+str(lo),FUNCTIONS[lo//8],'midi',lo*BAR,(hi-lo)*BAR,[],None)
            clips[key]=c;by[tid].clips.append(c)
        c=clips[key];serial[tid]+=1;n=Note('phase24-'+tid+'-n'+str(serial[tid]),at-c.start,gate,pitch,velocity,origin['channel'])
        c.notes.append(n);origins[n.id]={'source':deepcopy(origin),'reason':reason}
    def bass_keep(tid,b,x):
        if tid=='track-kick':return not 64<=b<72
        if tid=='track-snare':return 4<=b<140 and not 64<=b<72
        if tid=='track-snare.p38':return 12<=b<136 and not 64<=b<76
        if tid=='track-hats':return not (b<4 or 64<=b<72) or .45*PPQ<=x['absolute_tick']%PPQ<=.65*PPQ
        if tid=='track-hats.p46':return 8<=b<140 and not 64<=b<76
        if tid=='track-percussion':return b>=4 and not 64<=b<72 and (b<140 or b%2==0)
        if tid=='track-bass':
            return (8<=b<136 and not 64<=b<72 and
                    (not 72<=b<76 and b<132 or x['absolute_tick']%BAR//PPQ in (0,2)) and
                    (b not in (79,111,127) or x['absolute_tick']%BAR<3*PPQ))
        return 16<=b<132 and not 64<=b<76
    for b in range(144):
        if 16<=b<32:continue
        for tid in sorted(PROTECTED):
            for x in src[tid]:
                if x['absolute_tick']//BAR!=b%16 or not bass_keep(tid,b,x):continue
                v=x['velocity']-18 if tid=='track-hats' and 64<=b<72 else x['velocity']
                put(tid,b*BAR+x['absolute_tick']%BAR,x['duration'],x['pitch'],v,x,
                    'Timing-aligned approved pocket; section entrance/withdrawal or quiet breakdown hat clock')
    # Four quiet, deliberate handoffs; the kick and original bass clock stay.
    ghost=src['track-snare.p38'][0]
    for b in (63,79,111,127):
        for beat,velocity in ((3.25,44),(3.75,55)):
            at=b*BAR+round(beat*PPQ)+26
            if any(abs(c.start+n.start-at)<90 for c in by['track-snare.p38'].clips for n in c.notes):continue
            put('track-snare.p38',at,ghost['duration'],38,velocity,ghost,'Two quiet licensed-snare ghost taps signal the phrase handoff; no kick dropout')
    for b in range(144):
        if 16<=b<32:continue
        chord=CHORDS[b%16];tones=(LATE if 112<=b<128 else OPEN if 48<=b<64 or 104<=b<112 else VOICINGS)[chord]
        groups=defaultdict(list)
        for x in src['track-harmony']:
            if x['absolute_tick']//BAR==b%16:groups[(x['absolute_tick']%BAR)//16].append(x)
        for j,group in enumerate(groups.values()):
            if b<4 or b>=136 or (4<=b<16 and (b%2 or j!=0)):continue
            if 48<=b<64 and (b%4==1 or b%4==3 and j==0):continue
            if 64<=b<76 and (b%2 or j!=0):continue
            shift=round(.125*PPQ) if 48<=b<64 and b%4==3 else 0
            for i,x in enumerate(sorted(group,key=lambda x:x['pitch'])):
                at=b*BAR+x['absolute_tick']%BAR+shift;gate=x['duration'];v=x['velocity']
                if b<16 or b>=128:v-=10
                if 32<=b<48 and b%4==3 or 96<=b<128 and b%4==1:gate+=round(.30*PPQ)
                if 64<=b<72:gate=round(1.25*PPQ);v-=14
                if 72<=b<80:gate=round(gate*.8);v-=3
                if b>=128 and (b%2 or j!=0):continue
                end=min((b//4+1)*4*BAR,144*BAR)
                gate=min(gate,end-at-round(.20*126/60*PPQ)-8)
                put('track-harmony',at,gate,tones[i],v,x,'Three-voice '+chord+' hook: deliberate space, inversion or held reply; no solo line')
    release=round(2*126/60*PPQ)
    padspans=((4,8),(8,16),(32,48),(48,64),(64,72),(72,80),(80,112),(112,128),(128,136))
    for lo,hi in padspans:
        inner=(58,63) if lo==112 else (63,67)
        for i,n in enumerate(inner):
            origin=min(src['track-depth-pad'],key=lambda x:abs(x['pitch']-n))
            put('track-depth-pad',lo*BAR+.25*PPQ,(hi-lo)*BAR-round(.25*PPQ)-release,n,58-i*2 if lo==112 else 64-i*2,origin,
                'Long shared harmonic inner voice; lower Bb/Eb at112, no ornamental counterline')
        for b in range(lo,hi,4):
            if b>=132:continue
            n={'Cm9':74,'Cm11':77,'Abmaj9-C':72}[CHORDS[b%16]]
            if b==96:n=70
            if b==120:n=67
            origin=min(src['track-depth-pad'],key=lambda x:abs(x['pitch']-n))
            put('track-depth-pad',b*BAR+.25*PPQ,4*BAR-round(.25*PPQ)-release,n,59,origin,
                'Embedded four-bar chord color with2s dry-release clearance; not a top-line')
    for t in p.tracks:
        t.clips.sort(key=lambda c:c.start)
        for c in t.clips:
            if not 16*BAR<=c.start<32*BAR:c.notes.sort(key=lambda n:(n.start,n.pitch,n.id))
    _automation(p,source)
    p.metadata.update(phase24_version=VERSION,phase24_source_hash=SOURCE_HASH,phase24_human_source_verdict='Phase23 audibly better; approved melody-free musical foundation',
        phase24_scope='One144-bar original record; exact16-bar anchor at16..32; no lead/arp/new source or master',phase24_preference='unreviewed')
    validate(p);terminal_projection(p)
    for x in event_rows(p):origins[x['id']].update(actual=x,display_bar=x['absolute_tick']//BAR+1,beat=x['absolute_tick']%BAR/PPQ+1)
    receipt={'version':VERSION,'source_hash':state_hash(source),'candidate_hash':state_hash(p),'anchor_zero_bars':[16,32],
        'note_origins':origins,'sections':[asdict(s) for s in p.sections],'phrases':[{'first_bar':i*8+1,'function':x} for i,x in enumerate(FUNCTIONS)],
        'harmonic_plan':[CHORDS[b%16] for b in range(144)],'instrument_mixer_graph_exact':True,'mastering':False,'human_preference':'unreviewed'}
    return p,receipt


def _automation(p,source):
    # Preserve complete source point identity/value/shape inside the anchor,
    # including its endpoint; repeat other lanes against the same beat clock.
    for a,old in zip(p.automation,source.automation):
        points={}
        for cycle in range(9):
            for x in old.points:
                if x.tick==source.length and cycle!=1:continue
                if x.tick==0 and cycle==2:continue
                q=deepcopy(x);q.tick+=cycle*source.length
                if cycle!=1:q.id='phase24-'+str(cycle)+'-'+q.id
                points[q.tick]=q
        points[p.length]=AutomationPoint('phase24-end-'+a.id,p.length,old.points[-1].value,'linear')
        points[32*BAR+1]=AutomationPoint('phase24-restart-'+a.id,32*BAR+1,old.points[0].value,'linear')
        a.points=sorted(points.values(),key=lambda x:x.tick)
    def edit(owner,key,knots,mode='absolute',calm=False):
        a=next(a for a in p.automation if (a.target_id,a.parameter_id)==(owner,key));old=next(a for a in source.automation if (a.target_id,a.parameter_id)==(owner,key))
        knots=[(round(b*BAR),v) for b,v in knots];points={x.tick:deepcopy(x) for x in a.points}
        for t in {0,p.length,16*BAR-1,32*BAR+1,64*BAR,72*BAR-1,72*BAR}|{x for x,_ in knots}:
            if 16*BAR<=t<=32*BAR:continue
            if t not in points:points[t]=AutomationPoint('phase24-arc-'+a.id+'-'+str(t),t,lane_value(a,t),'linear')
        for t,x in points.items():
            if 16*BAR<=t<=32*BAR:continue
            v=_value(knots,t)
            x.value=(max(q.value for q in old.points)-3 if calm and 64*BAR<=t<72*BAR else x.value)+v if mode=='offset' else v
        a.points=sorted(points.values(),key=lambda x:x.tick)
    edit('effect-harmony-eq','soundcraft.lpf_freq',[(0,1000),(4,1200),(8,1800),(12,2600),(16,2800),(32,3200),(36,4600),(40,3200),(44,5400),(48,2800),(52,3900),(56,2500),(60,4600),(63.75,1500),(64,1200),(68,2000),(71.75,2800),(72,1700),(76,3300),(79.75,6500),(80,4800),(84,6000),(88,3700),(92,6300),(96,4000),(100,6500),(104,4200),(108,7000),(111.75,2500),(112,3000),(116,5200),(120,2800),(124,6200),(128,2400),(132,1500),(136,1000),(144,1000)])
    edit('effect-depth-pad-eq','soundcraft.lpf_freq',[(0,1000),(4,1000),(8,1400),(12,1700),(16,1300),(32,1600),(36,2700),(40,1500),(44,3200),(48,1500),(52,2300),(56,1200),(60,2400),(64,1700),(68,3000),(71.75,2000),(72,1100),(76,1800),(79.75,1000),(80,2500),(84,3600),(88,2000),(92,3800),(96,2300),(100,3500),(104,1800),(108,4000),(112,1600),(116,2800),(120,1500),(124,3100),(128,1400),(132,1000),(136,1000),(144,1000)])
    edit('effect-harmony-eq','soundcraft.hpf_freq',[(0,100),(32,100),(48,100),(63,180),(63.75,320),(64,180),(72,140),(76,200),(79.75,450),(80,100),(112,100),(127,200),(127.75,280),(128,100),(144,100)])
    edit('track-harmony','mixer.gain_db',[(0,-4),(16,0),(32,0),(40,.3),(48,-.8),(64,-1),(72,-3),(76,-1),(80,0),(96,.2),(104,.5),(112,-.6),(120,-.2),(128,-2),(136,-8),(144,-8)],'offset',True)
    edit('track-depth-pad','mixer.gain_db',[(0,-3),(16,0),(32,0),(40,.3),(48,-1),(56,-1.5),(64,-1),(72,-2),(80,.1),(96,.3),(108,.4),(112,-.5),(120,.2),(128,-1),(132,-2),(136,-4),(144,-8)],'offset',True)
    for owner in ('phase17-dark-space','phase17-echo'):
        edit(owner,'mixer.gain_db',[(0,-2),(16,0),(32,0),(48,-.5),(64,0),(72,-1),(80,0),(96,.3),(112,-.5),(128,-1),(136,-3),(144,-6)],'offset',True)
    # Phrase-end sends refer to actual three-note attacks, not empty bar ends.
    a=next(a for a in p.automation if a.target_id=='track-harmony' and a.parameter_id.startswith('route.'))
    kept=[x for x in a.points if 16*BAR<=x.tick<=32*BAR];values={0:-60,p.length:-60,16*BAR-1:-60,32*BAR+1:-60}
    rows=[x for x in event_rows(p) if x['track_id']=='track-harmony']
    for b in (0,8,32,40,48,56,64,72,80,88,96,104,112,120,128):
        group=[x for x in rows if (b+6)*BAR<=x['absolute_tick']<(b+8)*BAR]
        if not group:continue
        at=max(x['absolute_tick'] for x in group)-8;last=[x for x in group if at<=x['absolute_tick']<=at+8]
        end=min(max(x['absolute_tick']+x['duration'] for x in last)+60,(b+8)*BAR-97)
        values.update({max(b*BAR,at-24):-60,at:0,end:0,end+96:-60})
    a.points=sorted(kept+[AutomationPoint('phase24-throw-'+str(i),t,v,'linear') for i,(t,v) in enumerate(sorted(values.items()))],key=lambda x:x.tick)


def anchor_project(source,p):
    """Recover the exact approved source, including point IDs and clip order."""
    q=deepcopy(source);by={t.id:t for t in p.tracks}
    for t in q.tracks:
        ids={c.id for c in t.clips};t.clips=[deepcopy(c) for c in by[t.id].clips if c.id in ids]
        for c in t.clips:c.start-=16*BAR
    for a,b in zip(q.automation,p.automation):
        a.points=[deepcopy(x) for x in b.points if 16*BAR<=x.tick<=32*BAR]
        for x in a.points:x.tick-=16*BAR
    return q


def audit_record(source,p,receipt):
    validate(p);terminal_projection(p)
    if state_hash(source)!=receipt['source_hash'] or state_hash(p)!=receipt['candidate_hash']:raise ValidationError('record receipt drift')
    if p.bars!=144 or p.sections!=[Section('phase24-'+k,n,b*BAR,l*BAR) for k,n,b,l in FORM]:raise ValidationError('exact144-bar authored form required')
    if anchor_project(source,p)!=source:raise ValidationError('approved anchor notes/clips/performance altered')
    if set(t.id for t in p.tracks)!=set(t.id for t in source.tracks) or REMOVED&{t.id for t in p.tracks}:raise ValidationError('no added melody/instrument permitted')
    for a,b in zip(source.tracks,p.tracks):
        x=asdict(a);y=asdict(b);x.pop('clips');y.pop('clips')
        if x!=y:raise ValidationError('approved source/mixer/insert/send graph changed')
    for key in ('parameters','tempo_bpm','key_tonic','key_mode','time_signature','ppq','locks'):
        if getattr(source,key)!=getattr(p,key):raise ValidationError('protected registry/meter changed')
    rows=event_rows(p);old={x['id']:x for x in event_rows(source)};origins=receipt['note_origins']
    if len(rows)!=len(origins) or set(x['id'] for x in rows)!=set(origins):raise ValidationError('complete per-note journal required')
    for x in rows:
        o=origins[x['id']]
        if o['actual']!=x or o['source']!=old.get(o['source']['id']) or not o['reason']:raise ValidationError('invented event/source lineage')
        if x['track_id'] in ('track-bass','track-sub-pulse'):
            for k in ('pitch','velocity','duration','channel'):
                if x[k]!=o['source'][k]:raise ValidationError('bass groove/timbre rewritten')
            if x['absolute_tick']%BAR!=o['source']['absolute_tick']%BAR:raise ValidationError('bass onset moved')
    kicks=Counter(x['absolute_tick']//BAR for x in rows if x['track_id']=='track-kick');gap=longest=0
    for b in range(144):
        gap=gap+1 if not kicks[b] else 0;longest=max(longest,gap)
        played=sorted(x['absolute_tick']%BAR for x in rows if x['track_id']=='track-kick' and x['absolute_tick']//BAR==b)
        if played!=([] if 64<=b<72 else [i*PPQ for i in range(4)]):raise ValidationError('dance-floor kick anchor lost')
    if longest!=8:raise ValidationError('only one eight-bar kick-free break permitted')
    # Independent chord-quality sweep includes conservative measured dry tails.
    events=defaultdict(lambda:{'on':[],'off':[]});budgets={'track-harmony':.20,'track-depth-pad':2.,'track-bass':.03,'track-sub-pulse':.03}
    for x in rows:
        if x['track_id'] not in budgets:continue
        events[x['absolute_tick']]['on'].append(x);end=x['absolute_tick']+x['duration']+round(budgets[x['track_id']]*126/60*PPQ)
        events[min(p.length,end)]['off'].append(x)
    for b in range(145):events[b*BAR]
    times=sorted(events);active={};bad=[];matrix=[]
    for lo,hi in zip(times,times[1:]):
        for x in events[lo]['off']:active.pop(x['id'],None)
        for x in events[lo]['on']:active[x['id']]=x
        chord=CHORDS[lo//BAR%16];root,quality=THEORY[chord];pcs={(root+i)%12 for i in quality}
        if active:
            matrix.append({'start':lo,'end':hi,'chord':chord,'bass':sorted({x['pitch'] for x in active.values() if x['track_id'] in ('track-bass','track-sub-pulse')}),'upper':sorted({x['pitch'] for x in active.values() if x['track_id'] in UPPER})})
        for x in active.values():
            if x['pitch']%12 not in pcs:bad.append({'id':x['id'],'bar':lo//BAR+1,'chord':chord,'pitch':x['pitch']})
    if bad:raise ValidationError('active/releasing chord/bass conflict '+str(bad[:3]))
    strikes=[]
    for x in rows:
        if x['track_id']=='track-depth-pad' and x['duration']<8*PPQ:raise ValidationError('pad cannot hide an ornamental line')
    for x in sorted((x for x in rows if x['track_id']=='track-harmony'),key=lambda x:x['absolute_tick']):
        if not strikes or x['absolute_tick']-strikes[-1][0]['absolute_tick']>8:strikes.append([])
        strikes[-1].append(x)
    if any(len(v)!=3 for v in strikes):raise ValidationError('no disguised monophonic lead permitted')
    phrases=[]
    for b in range(0,144,8):
        group=[x for x in rows if b*BAR<=x['absolute_tick']<(b+8)*BAR]
        shape=sorted((x['track_id'],x['absolute_tick']-b*BAR,x['pitch'],x['duration']) for x in group)
        upper=[x for x in shape if x[0] in UPPER]
        phrases.append({'first_bar':b+1,'function':FUNCTIONS[b//8],'events':len(group),'signature':hashlib.sha256(json.dumps(shape).encode()).hexdigest(),'upper_signature':hashlib.sha256(json.dumps(upper).encode()).hexdigest(),'kick_onsets':sum(kicks[i] for i in range(b,b+8))})
    expected,journal=arrange_groove(source)
    if expected!=p or journal!=receipt:raise ValidationError('undeclared score/performance/provenance edit')
    return {'version':'groove-record-audit-1','source_hash':state_hash(source),'candidate_hash':state_hash(p),'notes':len(rows),'approved_anchor_exact':True,'anchor_source_notes':len(old),'sound_and_signal_graph_exact':True,'bass_event_fields_and_onset_phase_exact':True,'no_lead_arp_or_new_instrument':True,'per_bar_kick_onsets':[kicks[b] for b in range(144)],'longest_kick_free_bars':longest,'phrases':phrases,'unique_eight_bar_shapes':len({x['signature'] for x in phrases}),'unique_upper_shapes':len({x['upper_signature'] for x in phrases}),'harmonic_active_release_intervals':matrix,'unexplained_harmonic_intervals':bad,'release_budgets_seconds':budgets,'human_preference':'unreviewed','scope':'MIDI and conservative dry releases, not transcription of FX tails or a perceptual quality score'}
