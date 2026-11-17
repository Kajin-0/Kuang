"""Opt-in House long-form scene development with existing drum instruments.

Uses only the already-selected snare/hat samples and project MIDI pitches.
Never changes kick, bass, chord, source preset, sends or mixer automation.
Not a proxy for human musical preference. Deterministic with source and seed.
"""
from __future__ import annotations

from copy import deepcopy

from .schema import BAR, PPQ, Note, ValidationError, state_hash, validate

VERSION="house-section-drum-scenes-v1"
SIXTEENTH=PPQ//4


def _events(track, section):
    return sorted(((clip, note, clip.start+note.start)
                  for clip in track.clips for note in clip.notes
                  if section.start <= clip.start+note.start < section.start+section.length),
                  key=lambda item:(item[2],item[1].pitch,item[1].id))


def apply_drum_scenes(project, *, seed):
    if type(seed) is not int or not 0<=seed<=2**32-1:
        raise ValidationError("drum scene seed invalid")
    validate(project)
    required={"Groove A","Groove B","Build","Main Drop"}
    sections={s.name:s for s in project.sections}
    if not required <= set(sections) or project.bars<96:
        raise ValidationError("drum scenes need a complete House long-form song")
    if project.metadata.get("house_drum_scenes_version"):
        raise ValidationError("drum scenes already applied")
    tracks={t.id.removeprefix("track-"):t for t in project.tracks}
    if not {"kick","hats","snare","bass","harmony"} <= set(tracks):
        raise ValidationError("missing established house roles")
    snapshot={r:deepcopy(tracks[r]) for r in ("kick","bass","harmony")}
    original=state_hash(project)
    result=deepcopy(project)
    out={t.id.removeprefix("track-"):t for t in result.tracks}
    diagnostics=[]
    for name in ("Groove B","Build","Main Drop","Return"):
        section=sections[name]
        hat=out["hats"]
        hats=_events(hat,section)
        removed=0
        added=0
        emphasized=0
        if name=="Groove B":
            for clip,note,at in list(hats):
                bar=(at-section.start)//BAR
                phase=(at-section.start)%BAR
                if bar%8==7 and 3*PPQ<=phase<4*PPQ:
                    clip.notes.remove(note)
                    removed+=1
        if name=="Main Drop":
            for bar in range(3,section.length//BAR,4):
                at=section.start+bar*BAR+3*PPQ+2*SIXTEENTH
                next_at=section.start+(bar+1)*BAR
                target=next((c for c in hat.clips
                    if c.start<=at<c.start+c.length and
                    c.start+c.length>=next_at),None)
                existing=_events(hat,section)
                if target is None or not existing:
                    continue
                template=existing[0][1]
                if any(abs(now-at)<SIXTEENTH//2 and n.pitch==template.pitch
                       for _,n,now in existing):
                    continue
                duration=min(SIXTEENTH//2,next_at-at)
                if duration<1:
                    continue
                target.notes.append(Note(
                   f"house-scene-hat-{section.start//BAR}-{bar}",
                   at-target.start,duration,template.pitch,
                   max(1,min(127,template.velocity-16)),template.channel))
                added+=1
            for clip,note,at in _events(hat,section):
                if (at-section.start)//BAR%4==0 and (at-section.start)%BAR==2*SIXTEENTH:
                    before=note.velocity
                    note.velocity=min(127,note.velocity+8)
                    emphasized+=int(note.velocity!=before)
        if name=="Build":
            snare=out["snare"]
            events=_events(snare,section)
            if events:
                last_bar=section.start+section.length-BAR
                target=next((c for c in snare.clips
                    if c.start<=last_bar and c.start+c.length>=last_bar+BAR),None)
                if target:
                    template=events[0][1]
                    for offset in (3*PPQ+2*SIXTEENTH,3*PPQ+3*SIXTEENTH):
                        at=last_bar+offset
                        if not any(n.pitch==template.pitch and abs(now-at)<SIXTEENTH//2
                                   for _,n,now in _events(snare,section)):
                            target.notes.append(Note(
                              f"house-scene-snare-{section.start//BAR}-{offset}",
                              at-target.start,SIXTEENTH//2,template.pitch,
                              max(1,min(127,template.velocity-12)),template.channel))
                            added+=1
        diagnostics.append({"section":name,"removed":removed,"added":added,
                            "velocity_accents":emphasized})
    validate(result)
    for role,old in snapshot.items():
        if out[role]!=old:
            raise ValidationError("drum scenes changed protected "+role+" source")
    if state_hash(project)!=original:
        raise ValidationError("drum scenes mutated input")
    result.metadata["house_drum_scenes_version"]=VERSION
    result.metadata["house_drum_scenes_seed"]=str(seed)
    validate(result)
    return result,{"version":VERSION,"source_hash":original,
                   "output_hash":state_hash(result),"changes":diagnostics,
                   "protected_kick_bass_chords":True,
                   "musical_quality":"NOT_EVALUATED"}
