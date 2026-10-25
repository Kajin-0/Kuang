"""Independent 160-bar record arrangement from the human-approved Phase17 B.

Original patches, mixer/insert/send graph and SongSpec are immutable. Musical
changes are explicit note descendants or authored phrases in a composition
receipt, not a revision-1 transaction or a claim of automatic musical quality.
"""
import hashlib
import json
from copy import deepcopy
from dataclasses import asdict
from .schema import BAR, PPQ, Clip, Note, Section, AutomationLane, AutomationPoint, ValidationError, state_hash, validate
from .gestures import lane_value
from .production_host import graph_contract, trim_id
from .ensemble_production import PAN_COMPENSATION_DB

SOURCE_HASH='35669355d63ac231ca31d04364941380596762b7cc0cb34a4c7e2cb27651e690'
VERSION='house-record-composition-1'
FORM=(('intro','DJ introduction',0,16),('establish','Pocket and hook reveal',16,16),
      ('statement','Main statement A',32,32),('bridge','Harmonic conversation B',64,16),
      ('breakdown','Space and suspended answer',80,16),('rebuild','Rhythmic rebuild',96,16),
      ('return','Final return A prime',112,32),('outro','DJ resolution and mix out',144,16))
# Each entry is one eight-bar musical purpose, not a random mutation counter.
PHRASES=(
 'Kick/closed-hat exchange; first filtered Cm9 reply in bar7',
 'Clap handoff and two short bass teasers; no foreground lead',
 'Bass pocket establishes; two-note hook question leaves room for answer',
 'Complete hook teaser, displaced chord reply and one-beat turn into A',
 'Original approved first eight-bar statement, exact absolute note fields',
 'Original approved second eight-bar statement, exact absolute note fields',
 'Bass answers with F roots; new G-F-Eb melodic resolution and altered stabs',
 'Peak A: delayed answer, longer chord replies and a two-hit transition',
 'Abmaj9-Ebmaj9-Fm9-Bbadd9; eight-bar response rather than the A hook',
 'Same harmonic journey, new response contour and anticipatory chord rhythm',
 'Kick-free Abmaj9 to Fm9; augmented hook and two-bar harmonic breathing',
 'Ebmaj9 to Gm7, descending answer and an exposed one-bar rest',
 'Offbeat bass and chord rhythm recover before the kick returns',
 'Four-on-floor rebuild, filter opening, D-Eb-F pickup, last-beat vacuum',
 'Approved original first eight bars return with exact translated note fields',
 'Approved original second eight bars return with exact translated note fields',
 'Payoff: F-G-Eb answer, alternating bass pickup and chord articulation',
 'Final syncopated hook answer, sustained Cm9 resolution and transition fill',
 'Bass/stab withdrawal, last quiet hook fragment and closing filters',
 'Eight clean unpitched mix-out bars; hat/shaker handoff and natural tails')
DRUMS={'track-kick','track-snare','track-snare.p38','track-hats','track-hats.p46','track-percussion'}
# Root notes and four explicitly voiced upper tones. No blanket transposition.
CHORDS={
 'Cm9':(36,(51,55,58,62)),
 'Fm7-C':(36,(53,56,60,63)), # approved C pedal/inversion, not an unrelated root
 'Fm7':(41,(53,56,60,63)),
 'Abmaj9':(32,(55,58,60,63)),
 'Ebmaj9':(39,(55,58,62,65)),
 'Fm9':(41,(56,60,63,67)),
 'Bbadd9':(34,(58,60,62,65)),
 'Gm7':(31,(55,58,62,65))}
BRIDGE=('Abmaj9','Abmaj9','Ebmaj9','Ebmaj9','Fm9','Fm9','Bbadd9','Bbadd9')
MAP=(0,8,8,16,32,40,32,40,32,40,24,24,16,16,32,40,32,40,48,56)


def harmony_at(bar):
    if not 0<=bar<160:raise ValidationError('record bar outside 0..159')
    if 64<=bar<80:return BRIDGE[(bar-64)%8]
    if 80<=bar<96:return ('Abmaj9','Fm9','Ebmaj9','Gm7')[(bar-80)//4]
    if 48<=bar<64 or 128<=bar<144:return 'Fm7' if bar%4==3 else 'Cm9'
    return 'Fm7-C' if bar%4==3 else 'Cm9'


def _events(project,tid):
    return [(c.start+n.start,n,c) for t in project.tracks if t.id==tid for c in t.clips for n in c.notes]


def compose_record(source):
    validate(source)
    if state_hash(source)!=SOURCE_HASH or source.locks:
        raise ValidationError('exact unlocked human-approved Phase17 B required')
    p=deepcopy(source);p.id='project-phase18-house-record';p.name='Kuang / Return to the room — extended house';p.bars=160
    p.sections=[Section('phase18-section-'+key,name,start*BAR,length*BAR) for key,name,start,length in FORM]
    byid={t.id:t for t in p.tracks};original={t.id:t for t in source.tracks}
    events={t.id:_events(source,t.id) for t in source.tracks};origins={};clipmap={}
    for t in p.tracks:t.clips=[]
    def origin(tid,n,at,source_event,reason):
        old=None
        if source_event:
            x,m,c=source_event;old={'track_id':tid,'clip_id':c.id,'absolute_tick':x,**asdict(m)}
        origins[n.id]={'track_id':tid,'destination_tick':at,'display_bar':at//BAR+1,
                       'beat':(at%BAR)/PPQ+1,'reason':reason,'source':old,'note':asdict(n)}
    def clip(tid,first):
        key=(tid,first)
        if key not in clipmap:
            c=Clip('phase18-clip-'+tid+'-'+str(first),PHRASES[first//8],'midi',first*BAR,8*BAR,[],None)
            clipmap[key]=c;byid[tid].clips.append(c)
        return clipmap[key]
    def put(tid,bar,tick,length,pitch,velocity,reason,src=None):
        c=clip(tid,bar//8*8);at=bar*BAR+round(tick);length=round(length)
        if length<=0 or at+length>c.start+c.length:raise ValidationError('authored note crosses its explicit phrase clip')
        n=Note('phase18-'+tid+'-'+str(bar//8)+'-'+str(len(c.notes)),at-c.start,length,pitch,velocity,src[1].channel if src else (9 if tid in DRUMS else 0))
        c.notes.append(n);origin(tid,n,at,src,reason);return n
    def source_bar(tid,bar):
        return [x for x in events[tid] if (32+bar%16)*BAR<=x[0]<(33+bar%16)*BAR]
    def copybar(tid,bar,keep=lambda x:True,reason='Approved pocket descendant',pitch=None,velocity=0):
        for x,n,c in source_bar(tid,bar):
            if keep(n):put(tid,bar,x%BAR,n.duration,n.pitch if pitch is None else pitch,max(1,min(120,n.velocity+velocity)),reason,(x,n,c))
    # Two recognizable statements: original IDs/clip ownership at32..48; later
    # return uses new identities with exact translated source performances.
    for dest in (32,112):
        for tid,t in original.items():
            for c in t.clips:
                if 32*BAR<=c.start and c.start+c.length<=48*BAR:
                    q=deepcopy(c);q.start+=(dest-32)*BAR
                    if dest!=32:q.id='phase18-return-'+c.id
                    for old,n in zip(c.notes,q.notes):
                        if dest!=32:n.id='phase18-return-'+old.id
                        origin(tid,n,q.start+n.start,(c.start+old.start,old,c),'Exact approved statement' if dest==32 else 'Exact translated approved return')
                    byid[tid].clips.append(q)
    protected=lambda b:32<=b<48 or 112<=b<128
    # Groove is inherited by role: no uniform timing noise or new kick offsets.
    for bar in range(160):
        if protected(bar):continue
        phrase=bar//8;local=bar%8;bridge=64<=bar<80;breaking=80<=bar<96
        # Straight kick anchor, deliberate last-beat turnarounds and a truly
        # kick-free breakdown. Rebuild recovers rhythm before its final silence.
        kick=not breaking and not (96<=bar<104)
        if kick:
            copybar('track-kick',bar,lambda n:not(bar in (31,79,111) and n.start%BAR>=3*PPQ),reason='Steady original kick; documented pre-boundary dropout')
        if not breaking:
            copybar('track-snare',bar,lambda n:(bar>=8 and not (96<=bar<100) and not (bar in (31,79,111) and n.start%BAR>=3*PPQ)),velocity=-6 if bridge or bar>=152 else 0)
            copybar('track-snare.p38',bar,lambda n:bar>=16 and bar<152 and local in (1,5),velocity=-4 if bridge else 0)
            copybar('track-hats',bar,lambda n:(bar>=2 and (bar>=8 or (n.start%BAR)//240 in (2,10)) and
                not (96<=bar<100 and (n.start%BAR)//240 not in (2,10)) and
                not (bridge and (n.start%BAR)//240 not in (2,10)) and
                not (bar in (31,79,111) and n.start%BAR>=3*PPQ)),velocity=-5 if bridge else 0)
            copybar('track-hats.p46',bar,lambda n:bar>=8 and not (bridge or 96<=bar<104 or bar>=156) and not(bar in (31,79,111) and n.start%BAR>=3*PPQ))
            copybar('track-percussion',bar,lambda n:bar>=4 and (not bridge or local>=4) and not (96<=bar<100) and not(bar in (31,79,111) and n.start%BAR>=3*PPQ),velocity=-7 if bridge else 0)
        elif bar in (90,91):
            copybar('track-hats',bar,lambda n:(n.start%BAR)//240 in (2,10),velocity=-18,reason='Two bars of quiet timekeeping inside the breakdown')
        # Authored small fills: different sites, lengths and accents, not a
        # snare roll at every repeated four-bar boundary.
        fills={15:((3.25,44),(3.75,57)),31:((2.5,48),(2.75,62)),55:((3.25,43),),
               63:((2.75,48),(3.5,61)),79:((2.5,46),(2.75,57)),103:((3.5,48),),
               107:((2.75,45),(3.5,54)),111:((2,51),(2.5,65)),135:((3.25,46),(3.75,58)),
               143:((2.5,44),(3.5,59)),151:((3.5,44),),159:((2.75,38),)}
        for beat,vel in fills.get(bar,()):
            put('track-snare.p38',bar,beat*PPQ+26,70,38,vel,'Authored quiet ghost-snare transition; steady kick retained except documented gaps')
        # Hat/shaker handoffs are rhythmic variations within unchanged timbres.
        if bar in (7,23,51,59,75,131,139,155):
            put('track-hats',bar,PPQ+PPQ//4+40,60,42,37,'Single shuffled closed-hat answer between the established offbeats')
        if bar in (6,22,50,58,74,130,138,154):
            put('track-percussion',bar,2*PPQ+PPQ//2+46,60,44,43,'Shaker answer to preceding hat accent')
        if breaking:continue
        chord=harmony_at(bar);root,voicing=CHORDS[chord]
        # Offbeat bass/root hierarchy. The approved C-pedal turnarounds are
        # retained in A; B has explicitly paired roots and never an unrelated C.
        if bar<12 or bar>=152:continue
        if bar<16:
            if bar in (12,14):copybar('track-bass',bar,lambda n:(n.start%BAR)//240 in (2,10),velocity=-14,reason='Short filtered bass teaser')
            continue
        if bridge:
            patterns=((.5,300,96),(2.5,260,88)) if local%2==0 else ((.5,300,96),(1.75,150,65),(3.5,160,83))
            for beat,duration,vel in patterns:put('track-bass',bar,beat*PPQ+(38 if beat%1==.75 else 12),duration,root,vel,'Bridge bass explicitly follows '+chord)
        elif 96<=bar<104:
            copybar('track-bass',bar,lambda n:(n.start%BAR)//240 in ((2,) if bar<100 else (2,10)),velocity=-8,reason='Syncopated bass rebuild before kick return')
        else:
            def basskeep(n):return not(bar in (31,111) and n.start%BAR>=3*PPQ) and not(bar>=148 and (n.start%BAR)//240 not in (2,10))
            for x,n,c in source_bar('track-bass',bar):
                if not basskeep(n):continue
                pitch=n.pitch
                if chord=='Fm7':pitch=root if n.pitch!=31 else 36 # fifth C approaches next C root
                elif (48<=bar<64 or 128<=bar<144) and bar%8 in (1,5) and (n.start%BAR)//240==7:pitch=43
                put('track-bass',bar,x%BAR,n.duration,pitch,n.velocity,'Bass descendant with declared root/fifth response' if pitch!=n.pitch else 'Approved bass articulation',(x,n,c))
        if bar>=16 and bar<144 and not (bridge or 96<=bar<104):
            # Match pulse to sounding bass, including its existing turnaround.
            for x,n,c in source_bar('track-sub-pulse',bar):
                if bar in (31,111) and x%BAR>=3*PPQ:continue
                pitch=root if chord=='Fm7' else n.pitch
                if chord=='Fm7' and x%BAR>=3.5*PPQ:pitch=36
                put('track-sub-pulse',bar,x%BAR,n.duration,pitch,n.velocity,'Quiet pulse follows declared bass harmony',(x,n,c))
    # Explicitly voiced stabs and a breathing pad, with eight-bar melodic
    # responses. Silence and articulation, not just entrances, create the form.
    for bar in range(160):
        if protected(bar):continue
        chord=harmony_at(bar);root,voicing=CHORDS[chord];local=bar%8
        def stabs(beats,duration=175,velocity=68):
            template=source_bar('track-harmony',32)[:4]
            for beat in beats:
                for i,pitch in enumerate(voicing):
                    src=template[i];put('track-harmony',bar,beat*PPQ+36+i*4,duration,pitch,velocity-i*2,'Voiced '+chord+' chord response',src)
        if bar<16:
            if bar in (6,10,14):stabs((2.75,),150,57 if bar<8 else 63)
        elif bar<32:
            stabs((.75,2.75) if local in (0,4) else (1.75,) if local in (3,7) else (.75,),160,65)
        elif 48<=bar<64 or 128<=bar<144:
            stabs((.75,2.75) if local in (0,2,4) else (1.75,) if local in (3,7) else (.75,),230 if local in (3,7) else 175,70)
        elif 64<=bar<80:
            stabs((.75,2.5) if local%2==0 else (2.75,) if bar<72 else (1.75,),250,64)
        elif 80<=bar<96:
            if local in (0,4):stabs((.5,),PPQ,57)
        elif 96<=bar<112:
            stabs((2.75,) if bar<100 else (.75,2.75),125 if bar>=108 else 160,62 if bar<104 else 68)
        elif 144<=bar<152 and local in (0,4):stabs((.75,),210,63 if local==0 else 54)
        # Sustained pads use chord-specific upper voices, not a global pitch
        # offset. No low root is stacked with the bass; release gap at changes.
        pad_start=(16<=bar<32 and local in (0,4)) or (48<=bar<80 and bar%2==0) or (80<=bar<96 and bar%4==0) or (100<=bar<112 and local in (0,4)) or (128<=bar<144 and bar%2==0)
        if pad_start:
            if chord=='Cm9':tones=(63,70,74)
            elif chord in ('Fm7','Fm7-C'):tones=(65,68,72)
            elif chord=='Abmaj9':tones=(68,72,79)
            elif chord=='Ebmaj9':tones=(63,70,74)
            elif chord=='Fm9':tones=(65,72,79)
            elif chord=='Bbadd9':tones=(62,65,72)
            else:tones=(67,70,77)
            bars=3 if bar==92 else 4 if 80<=bar<96 else 2
            # Never hold a MIDI note across a scheduled chord change.
            until=next((x for x in range(1,bars) if harmony_at(bar+x)!=chord),bars)
            duration=until*BAR-PPQ;start=PPQ//2
            for i,pitch in enumerate(tones):put('track-depth-pad',bar,start,duration,pitch,70-i*2 if 80<=bar<96 else 73-i*2,'Sustained '+chord+' upper voicing with release space')
        if (48<=bar<64 or 128<=bar<144) and local in (3,5):
            # Air is a quiet upper chord reply, not a second lead melody.
            for i,pitch in enumerate({'Cm9':(75,79),'Fm7':(75,84),'Fm7-C':(75,84),'Abmaj9':(75,79),'Ebmaj9':(74,79),'Fm9':(75,79),'Bbadd9':(74,82),'Gm7':(74,82)}[chord]):
                put('track-depth-air',bar,PPQ//2,2*PPQ,pitch,65-i*2,'Air partials from '+chord+' upper tones')
        elif 80<=bar<96 and bar%4==2:
            for i,pitch in enumerate({'Cm9':(75,79),'Fm7':(75,84),'Fm7-C':(75,84),'Abmaj9':(75,79),'Ebmaj9':(74,79),'Fm9':(75,79),'Bbadd9':(74,82),'Gm7':(74,82)}[chord]):
                put('track-depth-air',bar,PPQ,2*PPQ,pitch,59-i*2,'Distant breakdown answer using chord tones')
    def line(tid,bar,notes,reason):
        for beat,pitch,duration,velocity in notes:put(tid,bar,beat*PPQ,duration,pitch,velocity,reason)
    hook=((0,67,290,88),(.78125,63,155,72),(1.5,65,310,83))
    for bar in (18,22):line('track-lead',bar,hook[:2],'Two-note question teasing the approved hook')
    for bar in (26,30,48,52,56,60,128,132):line('track-lead',bar,hook,'Recognizable G-Eb-F call')
    for bar in (50,54):line('track-lead',bar,((.5,67,260,85),(1.5,65,240,77),(2.75,63,300,73)),'G-F-Eb answering contour')
    for bar in (130,134):line('track-lead',bar,((.5,65,230,79),(1.5,67,300,84),(2.75,63,280,73)),'Payoff F-G-Eb answer, distinct from first-peak G-F-Eb')
    for bar in (58,62):line('track-lead',bar,((.5,65,260,79),(1.75,63,220,73),(2.75,67,260,83)),'F-Eb-G delayed answer; returns to the fifth')
    for bar in (136,140):line('track-lead',bar,tuple((beat+.5,pitch,duration,velocity) for beat,pitch,duration,velocity in hook),'Final hook displaced by an eighth note')
    for bar in (138,142):line('track-lead',bar,((.25,65,230,79),(1.5,67,300,84),(2.75,63,280,73)),'Final F-G-Eb answer')
    response=[((.5,67,420,80),(2,63,360,73)),((1.5,60,520,71),),((.5,70,350,81),(2,67,330,77)),((1.5,65,500,73),),
              ((.5,68,350,79),(2,67,320,76)),((1.5,65,480,73),),((.5,65,350,77),(2,62,400,73)),((1,60,480,71),)]
    for i,notes in enumerate(response):line('track-lead',64+i,notes,'Eight-bar B response over '+harmony_at(64+i))
    response2=[((1,63,330,75),(2.5,67,420,79)),((1.5,70,420,76),),((1,67,350,79),(2.5,65,360,73)),((1.5,63,480,72),),
               ((1,65,350,77),(2.5,68,380,79)),((1.5,67,420,74),),((1,62,420,75),),((.5,65,600,74),)]
    for i,notes in enumerate(response2):line('track-lead',72+i,notes,'Second B response changes contour and phrasing over '+harmony_at(72+i))
    # Augmented familiar contour, then a related descending response: sixteen
    # bars with harmonic breathing, not the same drum loop minus its kick.
    line('track-lead',80,((.5,67,PPQ,76),),'Augmented opening of the hook over Abmaj9')
    line('track-lead',81,((.5,63,PPQ,70),),'Augmented hook descent')
    line('track-lead',82,((.5,65,PPQ,73),),'Hook thirteenth over Abmaj9; rests leave a plate tail')
    for bar,pitch in ((88,67),(89,65),(90,63),(92,62)):
        line('track-lead',bar,((.5,pitch,PPQ,72),),'Descending breakdown answer; D resolves as Gm7 fifth')
    line('track-lead',110,((2,62,300,72),),'Rebuild D pickup')
    line('track-lead',111,((0,63,300,74),(1.5,65,300,80)),'Eb-F pickup, then a full beat of silence before G at112')
    line('track-lead',144,((.5,67,240,62),),'One quiet farewell fragment; no lead in the mix-out')
    for bar in (19,23,27,29,49,53,57,61,129,133,137,141):
        line('track-arp',bar,((1.7875,70,210,70),(2.5125,67,210,76)),'Original Bb-G response in the space between lead calls')
    # Remove the last beat of all pitched rebuild material, not only the kick.
    # Record any shortened/removed authored events, never silently truncate.
    vacuum=111*BAR+3*PPQ;removed=[]
    for t in p.tracks:
        if t.kind!='midi':continue
        for c in t.clips:
            kept=[]
            for n in c.notes:
                at=c.start+n.start
                if vacuum<=at<112*BAR:
                    removed.append(n.id);origins.pop(n.id);continue
                if at<vacuum<at+n.duration and at>=110*BAR:
                    n.duration=vacuum-at;origins[n.id]['note']=asdict(n);origins[n.id]['reason']+='; explicit pre-drop note-off'
                kept.append(n)
            c.notes=kept
        t.clips=[c for c in t.clips if c.notes];t.clips.sort(key=lambda c:c.start)
        for c in t.clips:c.notes.sort(key=lambda n:(n.start,n.pitch,n.id)) if c.id.startswith('phase18-clip-') else None
    _automation(p,source)
    p.metadata.update(phase17_human_preference='approved: user hears clearly better sound/production',
       phase18_human_preference='unreviewed',phase18_source_hash=SOURCE_HASH,phase18_composition_version=VERSION,
       phase18_arrangement_spec=json.dumps({'bars':160,'form':FORM,'phrases':PHRASES},sort_keys=True),
       phase18_notes='Independent extended record composition. Exact approved statement at bars33-48; translated return at113-128. New bridge/root-aware harmony, breakdown, answers, fills and performed filter/send curves. Original SongSpec is source provenance, not a160-bar SongSpec. No quality claim before listening.')
    graph_contract(p)
    for a,b in zip(source.tracks,p.tracks):
        aa=asdict(a);bb=asdict(b);aa.pop('clips');bb.pop('clips')
        if aa!=bb:raise ValidationError('record arrangement changed approved instrument/mixer/FX/send graph')
    receipt={'version':VERSION,'source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'not_transaction_receipt':True,
       'bars':160,'source_bars':64,'sections':[asdict(s) for s in p.sections],
       'phrases':[{'first_bar':i*8+1,'bars':8,'function':text} for i,text in enumerate(PHRASES)],
       'harmonic_plan':[{'bar':b+1,'name':harmony_at(b),'root_midi':CHORDS[harmony_at(b)][0],'upper_voicing':list(CHORDS[harmony_at(b)][1])} for b in range(160)],
       'note_origins':origins,'pre_drop_removed_note_ids':removed,'automation_source_windows':list(MAP),
       'original_SongSpec_exact':p.metadata['song_spec']==source.metadata['song_spec'],'patch_and_signal_graph_exact':True,
       'MIDI_bytes_exact':False,'human_preference':'unreviewed'}
    return p,receipt


def _automation(p,source):
    """Map actual eight-bar performances, then re-key kick/throw-dependent lanes."""
    p.automation=[]
    def lane(owner,key,values,label):
        points=dict(values);p.automation=[a for a in p.automation if (a.target_id,a.parameter_id)!=(owner,key)]
        p.automation.append(AutomationLane('phase18-'+label,owner,key,[AutomationPoint('phase18-'+label+'-'+str(i),tick,value,'linear') for i,(tick,value) in enumerate(sorted(points.items()))]))
    for old in source.automation:
        if old.parameter_id.startswith('route.') or old.target_id in ('phase17-dark-space','phase17-echo'):continue
        values={}
        for i,start in enumerate(MAP):
            lo=start*BAR;hi=lo+8*BAR;dest=i*8*BAR
            values[dest]=lane_value(old,lo)
            for x in old.points:
                if lo<x.tick<hi:values[dest+x.tick-lo]=x.value
            values[dest+8*BAR-1]=lane_value(old,hi-1)
        values[160*BAR]=lane_value(old,64*BAR)
        lane(old.target_id,old.parameter_id,values.items(),old.id)
    # Phrase-specific tone performance. Preserve approved32..48 and112..128
    # mappings; foreground stays out of the DJ bookends.
    for tid in ('track-harmony','track-lead','track-arp','track-depth-pad','track-depth-air'):
        t=next(t for t in p.tracks if t.id==tid);eq=next(e for e in t.effects if e.plugin_ref=='soundcraft:eq_7band')
        a=next(a for a in p.automation if a.target_id==eq.id and a.parameter_id=='soundcraft.lpf_freq')
        values={x.tick:x.value for x in a.points}
        spans=[(0,16,1100,4800),(16,32,4200,10000),(48,64,6500,12500),
               (64,80,3800,6200),(80,96,1900,4200),(96,112,1000,14000),
               (128,144,7000,12500),(144,160,5500,1000)]
        scale=.40 if tid=='track-depth-pad' else .65 if tid=='track-depth-air' else 1
        for lo,hi,start,end in spans:
            values={k:v for k,v in values.items() if not lo*BAR<=k<hi*BAR}
            for b,v in ((lo,start),(lo+4,start*.85+end*.15),(hi-4,start*.25+end*.75),(hi-1/16,end)):
                values[round(b*BAR)]=max(1000,min(20000,v*scale))
        lane(eq.id,'soundcraft.lpf_freq',values.items(),'tone-'+tid)
        if 'soundcraft.hpf_freq' in eq.parameters and tid in ('track-harmony','track-lead','track-arp'):
            a=next(a for a in p.automation if a.target_id==eq.id and a.parameter_id=='soundcraft.hpf_freq')
            values={x.tick:x.value for x in a.points if not 96*BAR<=x.tick<112*BAR}
            values.update({96*BAR:eq.parameters['soundcraft.hpf_freq'],104*BAR:380,110*BAR:700,112*BAR-1:900})
            lane(eq.id,'soundcraft.hpf_freq',values.items(),'build-highpass-'+tid)
    byid={t.id:t for t in p.tracks}
    for tid in ('track-harmony','track-lead','track-arp'):
        t=byid[tid];s=next(s for s in t.sends if s.target_track_id=='phase17-echo');values={0:-60,160*BAR:-60}
        for first in range(0,160,2):
            ev=[(c.start+n.start,n.duration) for c in t.clips for n in c.notes if first*BAR<=c.start+n.start<(first+2)*BAR]
            if not ev:continue
            at,duration=max(ev);end=min(at+duration+60,160*BAR-97)
            for tick,v in ((max(0,at-24),-60),(at,0),(end,0),(end+96,-60)):values[tick]=v
        lane(tid,trim_id(s),values.items(),'throws-'+tid)
    kicks=sorted({c.start+n.start for c in byid['track-kick'].clips for n in c.notes})
    def ticks(ms):return round(ms/1000*126/60*p.ppq)
    for tid,depth in (('phase17-dark-space',6),('phase17-echo',4)):
        times={0,p.length}
        for b in (16,32,64,80,96,104,112,144,152):times.update((b*BAR-1,b*BAR))
        for k in kicks:times.update(max(0,min(p.length,x)) for x in (k-1,k,k+ticks(25),k+ticks(75),k+ticks(165)))
        values=[]
        for at in sorted(times):
            bar=at/BAR;section=1 if 80<=bar<96 else -2 if 32<=bar<64 or 112<=bar<144 else -4 if bar>=144 else -1
            distance=[at-k for k in kicks if 0<=at-k<=ticks(165)];delta=0
            if distance:
                d=min(distance);delta=-depth if d<=ticks(25) else -depth*(ticks(165)-d)/(ticks(165)-ticks(25))
            values.append((at,PAN_COMPENSATION_DB+section+delta))
        lane(tid,'mixer.gain_db',values,'breathing-'+tid)
