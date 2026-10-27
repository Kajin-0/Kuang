"""Three original 16-bar compositions on a sealed, human-preferred pocket.

Opt-in only. No source/patch/FX changes, default composer changes or quality
ranking. The two moving-root sketches change LOW PITCH ONLY, including the
original passing-note functions and matching pulse. The pedal sketch doesn't.
"""
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
from .schema import BAR,PPQ,Clip,Note,ValidationError,validate,state_hash
from .gestures import crop
from .master_bus import attach_terminal,terminal_projection
from .composition_analysis import event_rows

SOURCE_HASH='44f96f794035a4cc730ff2318d0ef473ee7a1ad8350ea4258258c529f8bbc620'
REFERENCE_HASH='ec7c372bd16dbc140a5990913442497c829943b2e45177c41fcfdd6d04405d55'
VERSION='house-composer-shortlist-1'
UPPER={'track-harmony','track-lead','track-depth-pad','track-arp','track-depth-air'}
LOW={'track-bass','track-sub-pulse'}
DRUMS={'track-kick','track-snare','track-snare.p38','track-hats','track-hats.p46','track-percussion'}
# Original C-root note functions: root, minor seventh, fifth pickup, third.
# Major/suspended neighbors need their OWN chord tones, not blind transposes.
ROOT_MAP={
 'Cm9':{36:36,34:34,31:31,39:39},
 'Fm9':{36:41,34:39,31:36,39:44},
 'Abmaj9':{36:32,34:31,31:39,39:36},
 'Ebmaj9':{36:39,34:38,31:34,39:43},
 'Bb9sus4':{36:34,34:32,31:29,39:39}}
STABS={'Cm9':(51,58,62),'Fm9':(56,60,63),'Abmaj9':(55,58,60),
       'Ebmaj9':(55,58,62),'Bb9sus4':(56,60,63),
       'Cm11':(53,58,63),'Fm11-C':(56,60,63)}
PLANS={
 'soulful':('Cm9',)*2+('Fm9',)*2+('Abmaj9',)*2+('Cm9',)*2+
            ('Cm9',)*2+('Abmaj9',)*2+('Fm9',)*2+('Cm9',)*2,
 'progressive':('Cm9',)*4+('Abmaj9',)*4+('Ebmaj9',)*4+('Bb9sus4',)*2+('Cm9',)*2,
 'hypnotic':('Cm9',)*4+('Cm11',)*4+('Fm11-C',)*4+('Cm9',)*4}
# These are independently authored phrases, not transposed copies. Each tuple:
# MIDI pitch, beat within bar, gate in quarter beats, played velocity.
LEADS={
 'soulful':(
  ((67,1.5,.50,81),(70,2.75,.28,75)),
  ((67,.25,.70,79),(62,1.75,.22,68),(63,2.5,.55,76)),
  ((65,.75,.55,80),(68,2,.35,77)),
  ((72,.5,.65,83),(68,1.75,.45,76),(67,2.75,.30,70)),
  ((75,1.25,.60,82),(72,2.5,.40,76)),
  ((70,.5,.50,76),(67,1.75,.65,80)),
  ((63,.75,.25,72),(67,1.5,.55,79),(70,2.75,.30,76)),
  ((74,.25,.35,77),(72,1.5,1.00,82)),
  ((67,1.5,.45,80),(70,2.5,.30,75),(72,3,.25,77)),
  ((70,.5,.60,79),(67,2,.60,77)),
  ((75,.75,.50,84),(72,2.25,.45,79)),
  ((70,.5,.45,76),(67,1.75,.75,80)),
  ((68,1.25,.45,79),(72,2.5,.50,82)),
  ((67,.5,.45,75),(65,1.75,.70,79)),
  ((70,.75,.35,77),(67,1.75,.50,80),(63,2.75,.30,73)),
  ((62,.5,.35,72),(60,1.5,1.20,80))),
 'progressive':(
  ((67,.75,1.00,82),(70,2.5,.55,78)),
  ((72,.5,1.25,83),),
  ((74,1.25,.50,81),(75,2.5,.55,85)),
  ((74,.5,.50,78),(72,1.75,.85,82)),
  ((72,.75,.70,81),(75,2,.65,85)),
  ((79,.5,.90,86),(75,2.25,.60,81)),
  ((72,.75,.50,78),(70,1.75,.50,76)),
  ((67,.5,1.20,81),),
  ((70,.75,.65,80),(74,2.25,.50,82)),
  ((75,.5,.75,84),(79,2,.75,87)),
  ((77,.75,.40,79),(75,1.5,.55,81),(74,2.5,.45,78)),
  ((70,.5,1.25,80),),
  ((72,.75,.65,82),(75,2.25,.50,84)),
  ((77,.5,.75,85),(75,2,.50,79)),
  ((74,.75,.40,79),(70,1.5,.45,77),(67,2.5,.40,78)),
  ((63,.5,.60,77),(72,1.75,1.20,84))),
 'hypnotic':(
  ((72,.75,.25,82),(67,2.25,.40,77)),
  ((70,1.5,.60,79),),
  (),((72,.75,.25,82),(74,2.25,.30,76),(70,3,.22,74)),
  ((72,.75,.25,80),(65,2.25,.40,77)),
  ((70,1.5,.60,78),),
  (),((77,1.5,.50,81),(74,2.5,.30,76)),
  ((72,.75,.25,80),(68,2.25,.40,78)),
  ((70,1.5,.60,78),),
  (),((72,.75,.25,82),(67,2.25,.50,79)),
  ((72,.75,.25,83),(67,2.25,.40,78)),
  ((70,1.5,.60,79),),
  ((74,2.25,.30,76),),((72,.75,.30,82),(67,2.25,.65,79))) }


def main_reference(source):
    """Exactly the existing Phase21 B main16 capture, including its common trim."""
    validate(source)
    if source.locks or state_hash(source)!=SOURCE_HASH:raise ValidationError('unlocked sealed Phase21 B source required')
    q=crop(source,32,16,[t.id for t in source.tracks])
    q.tracks=[t for t in q.tracks if t.kind=='bus' or any(c.notes for c in t.clips)]
    owners={x for t in q.tracks for x in (t.id,*([t.instrument.id] if t.instrument else []),*(e.id for e in t.effects))}
    q.automation=[a for a in q.automation if a.target_id in owners]
    for lane in q.automation:
        if lane.parameter_id=='mixer.gain_db':next(t for t in q.tracks if t.id==lane.target_id).controls['mixer.gain_db']=lane.points[0].value
    q=attach_terminal(q);q.tracks[-1].controls['mixer.gain_db']=-6
    validate(q);terminal_projection(q);return q


def compose_candidate(reference,direction):
    validate(reference);terminal_projection(reference)
    if direction not in PLANS or reference.locks or state_hash(reference)!=REFERENCE_HASH:
        raise ValidationError('one declared direction and exact unlocked Phase21 main16 required')
    p=deepcopy(reference);p.id='project-phase22-'+direction;p.name='Kuang / '+{'soulful':'Amber conversation','progressive':'The long way home','hypnotic':'Afterimage'}[direction]
    old=event_rows(reference);oldby={x['id']:x for x in old};tracks={t.id:t for t in p.tracks};plan=PLANS[direction]
    removed=[x for x in old if x['track_id'] in UPPER];changed=[];authored={};serial=defaultdict(int)
    for tid in sorted(UPPER):tracks[tid].clips=[Clip('phase22-'+direction+'-'+tid,'Original '+direction+' performance','midi',0,16*BAR,[],None)]
    if direction!='hypnotic':
        for tid in sorted(LOW):
            for c in tracks[tid].clips:
                for n in c.notes:
                    before=oldby[n.id];n.pitch=ROOT_MAP[plan[(c.start+n.start)//BAR]][n.pitch]
                    if n.pitch!=before['pitch']:changed.append({'before':before,'after':{**before,'pitch':n.pitch},'reason':'Chord-root/guide-tone pitch only; original root, seventh, fifth pickup or third function, with paired sub root'})
    def add(tid,b,beat,gate,pitch,velocity,reason):
        serial[tid]+=1;at=round((4*b+beat)*PPQ);duration=round(gate*PPQ)
        n=Note('phase22-'+direction+'-'+tid+'-'+str(serial[tid]),at,duration,pitch,velocity,0);tracks[tid].clips[0].notes.append(n)
        pool=[x for x in old if x['track_id']==tid];ancestor=min(pool,key=lambda x:(abs(x['absolute_tick']-at),abs(x['pitch']-pitch),x['id']))
        authored[n.id]={'track_id':tid,'clip_id':tracks[tid].clips[0].id,'absolute_tick':at,**asdict(n),
                        'reason':reason,'source':ancestor,'ancestry':'Original new composition; source event identifies instrument-role lineage, not a copied melody'}
    # Shared score gestures are played on existing devices; all base envelopes,
    # modulation, faders and native expression lanes remain untouched.
    for b,phrase in enumerate(LEADS[direction]):
        for pitch,beat,gate,vel in phrase:add('track-lead',b,beat,gate,pitch,vel,'Original '+direction+' theme; purposeful rest/contour and phrase answer')
        if direction=='soulful':
            hits=(((.75,.32,80),(2.75,.24,75)),((1.25,.65,77),),((.75,.28,78),(2.25,.52,75)),((1.75,.70,78),))[b%4]
        elif direction=='progressive':hits=(((.75,.30,72),(2.75,.28,70)),((1.75,.65,73),))[b%2]
        else:hits=(((1.75,.38,72),),(),((.75,.28,71),(2.75,.25,67)),((1.25,.52,73),))[b%4]
        voices=STABS[plan[b]] if direction!='hypnotic' else STABS[plan[b]][:2]
        for beat,gate,vel in hits:
            for i,pitch in enumerate(voices):add('track-harmony',b,beat+i/240,gate,pitch,vel-3*i,'Connected guide voices and played top-note rhythm; complementary to lead, not full-chord doubling')
    # Ensemble writing: only the needed pad voices, with separate held inner
    # voice and moving top line. Reserve the actual original pad's release.
    release=1.65*126/60
    if direction=='hypnotic':
        add('track-depth-pad',0,.25,64-.25-release,63,65,'Common Eb inner voice across the pedal; background remains through lead rests')
        for b,mid,top in ((0,67,74),(4,65,77),(8,68,72),(12,67,74)):
            for pitch,vel in ((mid,66),(top,63)):add('track-depth-pad',b,.25,16-.25-release,pitch,vel,'Independent contrary-moving pad lines; release-aware four-bar suspension/resolution')
    else:
        # Eb is shared by every chosen chord. Distribute other harmonic
        # functions across stabs/pad/lead instead of stacking identical blocks.
        add('track-depth-pad',0,.25,64-.25-release,63,62,'Shared Eb ensemble inner voice, original pad envelope and level')
        pairs={'Cm9':(67,74),'Fm9':(67,72),'Abmaj9':(67,72),'Ebmaj9':(67,74),'Bb9sus4':(65,72)}
        # Two-bar breathing; the second half's top voice changes inversions.
        for b in range(0,16,2):
            notes=pairs[plan[b]]
            for i,pitch in enumerate(notes):add('track-depth-pad',b,.25,8-.25-release,pitch,64-i*3+(2 if b>=8 else 0),'Release-aware color/upper voice, sustained background between keyboard/lead phrases')
    # Air is a single complementary fifth/seventh, not whole duplicated chords.
    air={'Cm9':79,'Fm9':79,'Abmaj9':79,'Ebmaj9':79,'Bb9sus4':77,'Cm11':77,'Fm11-C':79}
    for b in (3,7,11,15):
        pitch=77 if direction=='progressive' and b==11 else air[plan[b]]
        # Original air release is2200ms: F is shared by Ebmaj9 and Bb9sus4,
        # so the upper ninth becomes a fifth without an incompatible G tail.
        add('track-depth-air',b,.25,1.7,pitch,60,'Quiet breathing upper fifth/ninth; phrase handoff with original airy source')
    counter={'soulful':((1,74),(5,75),(9,74),(13,72)),
             'progressive':((3,79),(7,75),(11,79),(15,79)),
             'hypnotic':((2,79),(6,77),(10,79),(14,79))}
    for b,pitch in counter[direction]:add('track-arp',b,3.0,.16,pitch,55,'Single upper response in the principal lead rest, not a second busy melody')
    for tid in sorted(UPPER):tracks[tid].clips[0].notes.sort(key=lambda n:(n.start,n.pitch,n.id))
    p.metadata.update(phase22_profile=VERSION,phase22_direction=direction,phase22_reference_hash=REFERENCE_HASH,
        phase22_full_source_hash=SOURCE_HASH,phase22_scope='Only upper MIDI plus declared root pitches in soulful/progressive; no drum/timing/source/mix changes',phase22_preference='unreviewed')
    validate(p);terminal_projection(p)
    for a,b in zip(reference.tracks,p.tracks):
        aa=asdict(a);bb=asdict(b);aa.pop('clips');bb.pop('clips')
        if aa!=bb:raise ValidationError('sound/mix changes forbidden')
        if a.id not in UPPER|LOW and a!=b:raise ValidationError('protected drum/bus changed')
        if direction=='hypnotic' and a.id in LOW and a!=b:raise ValidationError('pedal low voices must be exact')
    origins={}
    for x in event_rows(p):
        origins[x['id']]=authored.get(x['id'],{**x,'source':oldby[x['id']] if x['id'] in oldby else None,'reason':'Exact incumbent event or declared bass pitch-only harmonic edit'})
    receipt={'version':VERSION,'direction':direction,'source_hash':REFERENCE_HASH,'candidate_hash':state_hash(p),'full_source_hash':SOURCE_HASH,
             'source_window':{'zero_first_bar':32,'bars':16,'fresh_DSP_reset':True,'common_capture_trim_db':-6},
             'harmonic_plan':[{'bar':b+1,'chord':h,'stab_voicing':list(STABS[h] if direction!='hypnotic' else STABS[h][:2])} for b,h in enumerate(plan)],
             'removed_notes':removed,'pitch_edits':changed,'note_origins':origins,'source_notes':len(old),'candidate_notes':len(origins),
             'authored_notes':len(authored),'drums_exact':True,'bass_rhythm_exact':True,'patches_and_mix_exact':True,
             'new_full_song':False,'mastering':False,'human_preference':'unreviewed','professional_quality_claimed':False}
    return p,receipt
