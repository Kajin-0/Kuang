"""House bass rhythmic compatibility metrics, opt-in and key independent.

This is a rhythmic *fingerprint*, not a perceptual groove model. Four-to-floor
kick defines meter; bass anticipations and offbeat accents are measured without
rewarding arbitrarily many bass notes, maximum velocity, or low-end clipping.
"""
from __future__ import annotations
from .schema import BAR,PPQ,ValidationError,validate

VERSION="house-bass-syncopation-fingerprint-v1"

def inspect_bass_pocket(project,*,section=None,bars=8):
    validate(project)
    if type(bars) is not int or not 2<=bars<=16:
        raise ValidationError("bounded complete bar count required")
    if section is None:
        names=("Groove A","Groove","Melodic development","First groove")
        active=next((s for name in names for s in project.sections if s.name==name and s.length>=bars*BAR),None)
    else:
        active=next((s for s in project.sections if s.name==section and s.length>=bars*BAR),None)
    if active is None:raise ValidationError("requested active groove section unavailable")
    bass=next((t for t in project.tracks if t.id=="track-bass"),None)
    kick=next((t for t in project.tracks if t.id=="track-kick"),None)
    if bass is None or kick is None:raise ValidationError("missing core rhythm roles")
    start=active.start;end=start+bars*BAR
    def notes(track):
        return sorted((c.start+n.start,n.duration,n.velocity,n.pitch) for c in track.clips for n in c.notes
                      if start<=c.start+n.start<end)
    bass_notes=notes(bass);kick_notes=notes(kick)
    if len(bass_notes)<bars:raise ValidationError("source bass insufficient for active groove review")
    beat=PPQ
    off=[(t,d,v,p) for t,d,v,p in bass_notes if (t-start)%beat not in (0,)]
    kick_grid={t for t,d,v,p in kick_notes}
    expected={start+bar*BAR+beat_index*beat for bar in range(bars) for beat_index in range(4)}
    kick_coverage=len(expected&kick_grid)/len(expected)
    on=[n for n in bass_notes if (n[0]-start)%beat==0]
    # A true *anticipation* is an off-grid onset that crosses an approaching
    # quarter-note beat, not just a conventional eighth-note offbeat.
    anticipations=[n for n in off if (n[0]-start)%beat>=beat//2 and
                   n[0]+n[1] > start+(((n[0]-start)//beat)+1)*beat]
    # Bass notes near the kick are not inherently wrong, but are logged.
    overlap=[n for n in bass_notes if min((abs(n[0]-k) for k in kick_grid),default=beat)<PPQ//8]
    velocities=[n[2] for n in bass_notes]
    return {
        "version":VERSION,"section":active.name,"bars":bars,
        "kick_quarter_coverage":round(kick_coverage,4),
        "bass_onsets":len(bass_notes),
        "bass_onsets_per_bar":round(len(bass_notes)/bars,3),
        "bass_offbeat_onset_fraction":round(len(off)/len(bass_notes),4),
        "bass_anticipation_fraction":round(len(anticipations)/len(bass_notes),4),
        "bass_near_kick_onset_fraction":round(len(overlap)/len(bass_notes),4),
        "bass_mean_gate_ms":round(sum(n[1] for n in bass_notes)/len(bass_notes)
                         /PPQ*60000/project.tempo_bpm,2),
        "bass_mean_velocity":round(sum(velocities)/len(velocities),2),
        "bass_velocity_range":max(velocities)-min(velocities),
        "bass_eighth_positions":sorted({round(((t-start)%BAR)/(PPQ/2),3) for t,d,v,p in bass_notes}),
        "perceptual_groove_quality":"NOT_EVALUATED",
        "limitation":"Offbeat onset ratio is not a validated syncopation index. Melody, accents, rests and meter expectations matter."
    }


def propose_phrase_pickups(project,*,section="Groove A",bars=16,interval_bars=4):
    """Opt-in late-sixteenth anticipation on existing pickup notes.

    No notes, pitches, samples, roles or velocities are added. Moving an
    existing step-14 eighth pickup to step-15 creates a stronger anticipatory
    accent before the next downbeat. This is a hypothesis for A/B, not a
    guaranteed syncopation or groove improvement.
    """
    from copy import deepcopy
    from . import midi
    from .schema import state_hash
    validate(project)
    if type(bars) is not int or bars<8 or bars>16 or type(interval_bars) is not int or interval_bars not in (4,8):
        raise ValidationError("bounded phrase pickup policy required")
    s=next((x for x in project.sections if x.name==section and x.length>=bars*BAR),None)
    if s is None:raise ValidationError("active section missing")
    source_hash=state_hash(project)
    out=deepcopy(project)
    kick=next(t for t in out.tracks if t.id=="track-kick")
    bass=next(t for t in out.tracks if t.id=="track-bass")
    kick_before=deepcopy(kick)
    events=[]
    for bar in range(0,bars,interval_bars):
        target_bar=bar+interval_bars-1
        base=s.start+target_bar*BAR
        hits=[(c,n) for c in bass.clips for n in c.notes
              if c.start+n.start-base==14*(PPQ//4) and n.duration<=PPQ//4]
        if len(hits)!=1:continue
        clip,note=hits[0]
        # Move to the final sixteenth of the 4/8-bar phrase; protect next
        # downbeat (no overlapping bass note on same voice).
        new_time=base+15*(PPQ//4)
        if new_time+note.duration>base+BAR:
            continue
        if any(c.start+x.start==new_time for c in bass.clips for x in c.notes):
            continue
        old_time=clip.start+note.start
        note.start=new_time-clip.start
        events.append({"bar_1based":s.start//BAR+target_bar+1,
                       "old_tick":old_time,"new_tick":new_time,
                       "note_pitch":note.pitch,"duration":note.duration})
    validate(out)
    if kick!=kick_before:raise ValidationError("kick changed in bass pickup proposal")
    for old,new in zip(project.tracks,out.tracks):
        if old.id!="track-bass" and old!=new:
            raise ValidationError("non-bass song role altered")
    if any(o.instrument!=n.instrument or o.controls!=n.controls or
           o.effects!=n.effects or o.sends!=n.sends for o,n in zip(project.tracks,out.tracks)):
        raise ValidationError("source or native FX changed")
    return out,{
        "version":"house-bass-phrase-anticipation-audition-v1",
        "source_sha256":source_hash,
        "section":section,"requested_bars":bars,"interval_bars":interval_bars,
        "changed_existing_notes":len(events),"note_movements":events,
        "note_count_unchanged":True,"kick_midi_unchanged":True,
        "candidate_only":True,"perceptual_quality":"NEEDS_LISTENING"
    }
