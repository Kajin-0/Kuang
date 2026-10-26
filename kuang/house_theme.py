"""Independent Phase21 melodic/harmonic performance on the approved pocket.

Drums, bass, sub pulse, prepared sounds and the entire native mix graph are
immutable. Authored upper harmony develops around the existing low voices.
No mastering, swing reapplication, new tracks or automatic quality score.
"""
from copy import deepcopy
from dataclasses import asdict
from collections import defaultdict
from .schema import BAR,PPQ,Clip,Note,ValidationError,validate,state_hash
from .composition_analysis import event_rows
from .production_host import graph_contract

SOURCE_HASH='eabf2314fbcbd6099a6c93de3ccfd323a645c6c7b9ded294c8aeaadb70227230'
VERSION='house-melodic-theme-1'
EDITABLE={'track-harmony','track-lead','track-arp','track-depth-pad','track-depth-air'}
LOW={'track-bass','track-sub-pulse'}
QUALITIES={'Cm9':{0,2,3,7,10},'Cm11':{0,2,3,5,7,10},
           'Abmaj9-C':{0,3,7,8,10},'Fm9-C':{0,3,5,7,8},'Fm11-C':{0,3,5,7,8,10}}
STABS={'Cm9':(51,55,58,62),'Cm11':(51,53,58,62),
       'Abmaj9-C':(51,56,58,67),'Fm9-C':(53,56,60,63),'Fm11-C':(53,56,60,63)}
COLORS={'Cm9':(70,74),'Cm11':(70,77),'Abmaj9-C':(70,72),
        'Fm9-C':(68,72),'Fm11-C':(68,72)}
# Original G-Eb-F question becomes a connected eight-bar arch. Tuples are
# pitch, quarter-beat position, gate, velocity; no random timing/accents.
THEME=(
 ((67,0,.302,90),(63,.78125,.16146,72),(65,1.5,.45,83)),
 ((70,.5125,.22,77),(67,1.29167,.28,75),(72,2.5125,.50,84)),
 ((67,0,.30,87),(74,1.29167,.25,79),(72,2.5125,.50,82)),
 ((70,.79167,.25,77),(67,1.5125,.60,83)),
 ((67,0,.30,86),(70,.78125,.18,74),(72,1.5,.50,84)),
 ((75,.5125,.42,85),(72,1.79167,.30,80),(70,2.5125,.30,76)),
 ((67,0,.302,88),(63,.78125,.16146,72),(65,1.5,.323,83)),
 ((74,.79167,.25,79),(72,1.5125,.72,84)))
STRIKES=( ((.7875,.18,0),(2.7875,.22,-2)), ((1.7875,.44,-2),),
          ((.7875,.20,-1),(3.2875,.42,-3)), ((.5125,.40,-3),(2.2875,.32,-1)),
          ((.7875,.20,0),(2.7875,.26,-3)), ((1.2875,.34,-2),(3.2875,.18,-5)),
          ((.7875,.20,1),(2.7875,.48,-2)), ((1.2875,.52,-2),))


def musical_scope(bar):
    return 16<=bar<80 or 88<=bar<144


def harmonic_plan(source):
    """C-pedal related upper harmony; honor actual existing F/Bb low notes."""
    rows=event_rows(source);low=defaultdict(set)
    for x in rows:
        if x['track_id'] in LOW:low[x['absolute_tick']//BAR].add(x['pitch']%12)
    cycle=('Cm9','Cm9','Cm11','Cm11','Abmaj9-C','Abmaj9-C','Cm9','Cm9',
           'Cm9','Cm9','Abmaj9-C','Abmaj9-C','Fm9-C','Fm9-C','Cm11','Cm9')
    plan=[]
    for b in range(source.bars):
        name=cycle[b%16] if musical_scope(b) else 'Cm9'
        if 5 in low[b]:name='Fm11-C' if 10 in low[b] else 'Fm9-C'
        plan.append({'bar':b+1,'zero_bar':b,'name':name,'bass_pedal':'Existing exact C/F/G/Bb performance, no root edits',
                     'actual_low_pitch_classes':sorted(low[b]),'pitch_classes':sorted(QUALITIES[name]),
                     'stab_voicing':list(STABS[name]),'color_voicing':list(COLORS[name]),
                     'interpretation':'Related upper harmony over preserved bass; C is third of Ab or fifth of F, not a new unrelated root cycle'})
    return plan


def compose_theme(source):
    validate(source);graph_contract(source)
    if source.locks or state_hash(source)!=SOURCE_HASH:
        raise ValidationError('exact unlocked Phase20 source required; groove and palette must be protected')
    p=deepcopy(source);p.id='project-phase21-harmonic-theme';p.name='Kuang / A room to return to — melodic house'
    before=event_rows(source);byid={t.id:t for t in p.tracks};orig={t.id:t for t in source.tracks}
    rows={tid:[x for x in before if x['track_id']==tid] for tid in sorted(EDITABLE)}
    plan=harmonic_plan(source);authored=[];serial=defaultdict(int);removed=[]
    # Remove just the scoped upper performance. Keep DJ bookends and the short
    # breakdown; partial clip data outside the scope remains exact.
    for tid in sorted(EDITABLE):
        for c in byid[tid].clips:
            kept=[]
            for n in c.notes:
                at=c.start+n.start
                if musical_scope(at//BAR):removed.append({'track_id':tid,'clip_id':c.id,'absolute_tick':at,**asdict(n)})
                else:kept.append(n)
            c.notes=kept
        byid[tid].clips=[c for c in byid[tid].clips if c.notes]
    def source_for(tid,at,pitch):
        pool=rows[tid]
        if not pool:raise ValidationError('authored role has no original source')
        return min(pool,key=lambda x:(abs(x['absolute_tick']-at),abs(x['pitch']-pitch),x['id']))
    def add(tid,at,duration,pitch,velocity,reason,*,span=8):
        at=round(at);duration=round(duration);start=at//(span*BAR)*(span*BAR)
        # Eight-bar recovered section starts at88, so all spans align naturally.
        c=next((c for c in byid[tid].clips if c.id=='phase21-clip-'+tid+'-'+str(start//BAR)),None)
        if c is None:
            c=Clip('phase21-clip-'+tid+'-'+str(start//BAR),'Authored harmony/theme '+str(start//BAR+1),'midi',start,span*BAR,[],None);byid[tid].clips.append(c)
        if not start<=at<at+duration<=start+span*BAR:raise ValidationError('authored note exceeds phrase boundary')
        serial[tid]+=1;n=Note('phase21-'+tid+'-'+str(serial[tid]),at-start,duration,pitch,velocity,0);c.notes.append(n)
        authored.append({'track_id':tid,'clip_id':c.id,'absolute_tick':at,**asdict(n),
                         'reason':reason,'source':deepcopy(source_for(tid,at,pitch))})
    tick=lambda beats:round(beats*PPQ)
    # The complete theme belongs at established peaks; contrasting sections
    # use the SAME phrase's question/cadence fragments, not another melody.
    for b in range(16,144):
        if not musical_scope(b):continue
        h=plan[b]['name'];phase=b%8;full=16<=b<64 or 104<=b<144
        if full or phase in (0,3,4,7):
            phrase=THEME[phase]
            for i,(pitch,beat,gate,vel) in enumerate(phrase):
                if h.startswith('Fm') and pitch%12 in (2,10):pitch=75 if pitch%12==2 else 68
                if h.startswith('Ab') and pitch%12 in (2,5):pitch=75 if pitch%12==2 else 67
                # A-prime develops the final cadence, not an unrelated riff.
                if b%16==15 and i==len(phrase)-1:gate=.90
                if not full:vel-=8
                add('track-lead',b*BAR+tick(beat),tick(gate),pitch,vel,
                    'Original G-Eb-F ancestry; connected question/answer contour and rest, harmony-aware phrase member')
        # A quieter upper response now inhabits the lead's cadence gaps.
        if phase in (3,7):
            notes=(75,79) if h.startswith('Ab') else (75,72) if h.startswith('Fm') else (79,74)
            for i,pitch in enumerate(notes):add('track-arp',b*BAR+tick(2.7875+i*.725),tick(.16),pitch,59-i*3,
                'Upper two-note counterline in the new lead rest; reduced density and velocity, not a competing foreground loop')
        for beat,gate,accent in STRIKES[phase]:
            for voice,pitch in enumerate(STABS[h]):
                add('track-harmony',b*BAR+tick(beat)+voice*4,tick(gate),pitch,72-voice*3+accent,
                    'Voice-led rootless/pedal chord; short/held articulation and space between melodic gestures')
    # Richer background is a played harmonic bed, not a fader/reverb increase.
    # Common Eb/G remain across upper changes. Color voices stop early enough
    # for the original1.45s release, while the constant shared tones connect it.
    for first in range(16,144,8):
        if not musical_scope(first):continue
        if not any(first*BAR<=x['absolute_tick']<(first+8)*BAR for x in rows['track-depth-pad']):continue
        release=tick(1.65*source.tempo_bpm/60)
        for pitch,vel in ((63,67),(67,63)):
            add('track-depth-pad',first*BAR+tick(.5),8*BAR-tick(.5)-release,pitch,vel,
                'Common Eb/G support sustains the eight-bar question/answer with original moving pad, unchanged level')
        for b in range(first,first+8,2):
            # Existing F-bass bars can change inside a two-bar pair. Split
            # colors there rather than sustaining a mismatched upper voice.
            chunks=[(b,1),(b+1,1)] if plan[b]['name']!=plan[b+1]['name'] else [(b,2)]
            for start,bars in chunks:
                colors=COLORS[plan[start]['name']];duration=bars*BAR-tick(.5)-release
                # One-bar colors cannot accommodate the original slow envelope
                # and long release. Use compatible held Eb/G only for that bar.
                if duration<tick(.75):continue
                for voice,pitch in enumerate(colors):add('track-depth-pad',start*BAR+tick(.5),duration,pitch,69-voice*3,
                    'Upper color voice; related harmony, long articulation and release-aware handoff, no pad gain increase')
    # Preserve air texture timing/gates exactly; replace only pitches outside
    # the new explicit harmony, choosing the nearest consonant register member.
    for x in rows['track-depth-air']:
        b=x['absolute_tick']//BAR
        if not musical_scope(b):continue
        pcs=QUALITIES[plan[b]['name']];pitch=min((n for n in range(67,84) if n%12 in pcs),key=lambda n:(abs(n-x['pitch']),n))
        add('track-depth-air',x['absolute_tick'],x['duration'],pitch,x['velocity'],
            'Original air note timing/gate/velocity retained; nearest compatible upper harmony')
    for t in p.tracks:
        if t.id in EDITABLE:
            t.clips.sort(key=lambda c:(c.start,c.id))
            for c in t.clips:c.notes.sort(key=lambda n:(n.start,n.pitch,n.id))
    p.metadata.update(phase21_profile=VERSION,phase21_source_hash=SOURCE_HASH,
        phase21_scope='Upper melodic/harmonic performance only; drums,bass,subpulse,instruments,FX,mixer,routes and automation exact',
        phase21_preference='unreviewed',phase21_music='C-pedal related voice-led colors; recognizable G-Eb-F develops into a16-bar question/answer; sustained background with release-aware color voices')
    validate(p);graph_contract(p)
    for a,b in zip(source.tracks,p.tracks):
        if a.id not in EDITABLE and a!=b:raise ValidationError('protected groove track changed')
        aa=asdict(a);bb=asdict(b);aa.pop('clips');bb.pop('clips')
        if aa!=bb:raise ValidationError('palette or native mix graph changed')
    if source.sections!=p.sections or source.automation!=p.automation or source.parameters!=p.parameters:
        raise ValidationError('form, expression lanes or registry changed')
    after=event_rows(p);oldby={x['id']:x for x in before};authby={x['id']:x for x in authored}
    origins={}
    for x in after:
        if x['id'] in authby:origins[x['id']]=authby[x['id']]
        else:origins[x['id']]={**deepcopy(x),'reason':'Unchanged Phase20 performance','source':deepcopy(oldby[x['id']])}
    return p,{'version':VERSION,'source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),
              'MIDI_bytes_exact':False,'protected_drum_bass_subpulse_tracks_exact':True,'palette_mix_graph_and_automation_exact':True,
              'harmonic_plan':plan,'removed_notes':removed,'note_origins':origins,
              'source_notes':len(before),'candidate_notes':len(after),'authored_notes':len(authored),
              'retained_notes':len(after)-len(authored),'human_preference':'unreviewed','professional_quality_claimed':False,
              'scope':'Intentionally new upper MIDI. No drum/bass rewrite, new instrument, gain/master/FX changes or uniform swing.'}
