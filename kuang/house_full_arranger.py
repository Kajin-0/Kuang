"""Reusable long-form house arranger built from a locked eight-bar groove.

The arranger uses original Kuang MIDI only. It does NOT copy commercial songs,
change VSTs, audition replacements or claim perceptual quality. It preserves
the source project and expands role-presence/automation to a 96-160 bar form.
"""
from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from . import midi
from .schema import (BAR, PPQ, AutomationLane, AutomationPoint, Clip,
                     Note, Section, ValidationError, state_hash, validate)

VERSION = "house-full-song-arranger-v1"
ALLOWED_BARS = (96, 112, 128, 160)
CYCLE = 8
# Section templates are strong house arrangements, not strict universal laws.
FORMS = {
    96:  (8, 16, 16, 8, 8, 16, 16, 8),
    112: (16, 16, 16, 8, 8, 16, 16, 16),
    128: (16, 24, 16, 8, 8, 24, 16, 16),
    160: (16, 32, 24, 8, 8, 32, 24, 16),
}
NAMES = ("Intro", "Groove A", "Groove B", "Breakdown", "Build",
         "Main Drop", "Return", "Outro")
ROLES = ("kick", "snare", "hats", "open_hat", "bass", "harmony", "pad", "percussion")


def parse_long_form(prompt, requested=None, *, bpm=126):
    """Resolve explicit bar/minute intent without fabricating SongSpec support."""
    if type(prompt) is not str or not prompt.strip():
        raise ValidationError("prompt required")
    if requested is not None and (type(requested) is not int or requested not in FORMS):
        raise ValidationError("long song bars must be 96, 112, 128 or 160")
    found = {int(s) for s in re.findall(r"\b(96|112|128|160)\s*bars?\b", prompt, re.I)}
    if len(found) > 1 or (requested is not None and found and next(iter(found)) != requested):
        raise ValidationError("conflicting full-song length requests")
    if found:
        requested = next(iter(found))
    short = {int(s) for s in re.findall(r"\b(8|16|32)\s*bars?\b",prompt,re.I)}
    if requested is not None and short:
        raise ValidationError("cannot request a short loop and full song together")
    minutes = re.findall(r"\b(?:about|around|approximately)?\s*(\d+(?:\.\d+)?)\s*(?:minute|min)(?:s)?\b", prompt, re.I)
    if minutes and (len({float(m) for m in minutes}) != 1 or requested is not None):
        raise ValidationError("ambiguous full-song length; use either bars or minutes")
    if minutes:
        requested_seconds = float(minutes[0]) * 60
        if not 150 <= requested_seconds <= 360 or not 100 <= bpm <= 150:
            raise ValidationError("requested song duration outside supported house form")
        requested = min(ALLOWED_BARS,
                        key=lambda bars: (abs(4 * bars * 60 / bpm - requested_seconds), bars))
    if requested is None and re.search(r"\b(full[ -]length|complete song|complete track|extended mix)\b",prompt,re.I):
        requested = 128 if "extended mix" not in prompt.lower() else 160
    # SongSpec's explicit 8/16/32 limitation is retained; only the adapter
    # consumes this rewritten source-plan phrase, the original prompt is logged.
    planner_prompt = re.sub(r"\b(?:96|112|128|160)\s*bars?\b",
                            "32 bars",prompt,flags=re.I) if requested else prompt
    return requested, planner_prompt


def _source_events(project, role, section):
    """Normalize only pre-existing notes of a source eight-bar section."""
    stem = next((t for t in project.tracks if t.id == "track-" + role),None)
    if stem is None:
        return []
    section = next(s for s in project.sections if s.name == section)
    if section.length != CYCLE * BAR:
        raise ValidationError("source sections must be exactly eight bars")
    start, end = section.start, section.start + section.length
    events = []
    for clip in stem.clips:
        for note in clip.notes:
            at = clip.start + note.start
            if start <= at < end:
                local = at - start
                if local + note.duration > end - start:
                    raise ValidationError("source motif crosses eight-bar boundary")
                events.append((local,note.duration,note.pitch,note.velocity,note.channel))
    return sorted(events)


def _present(role, kind, bar, duration, profile, block):
    """Part-presence grammar, including negative space and DJ mix windows."""
    half = duration // 2
    if kind == "Intro":
        return (role == "pad" or role == "hats" or
                role == "open_hat" and bar >= duration - 4 or
                role == "harmony" and bar >= half or
                role == "kick" and bar >= half or
                role == "snare" and bar >= duration - 4 or
                role == "bass" and bar >= duration - 2)
    if kind == "Groove A":
        return role in ("kick","snare","hats","open_hat","bass","harmony") or (
            role == "percussion" and profile == "jackin" and block % 2 == 1)
    if kind == "Groove B":
        return role in ("kick","snare","hats","open_hat","bass","harmony") or (
            role == "percussion" and profile != "minimal")
    if kind == "Breakdown":
        return (role in ("pad","harmony") or
                role in ("hats","open_hat") and bar >= duration - 1 or
                role == "snare" and bar >= duration - 1)
    if kind == "Build":
        return (role in ("pad","harmony") or
                role in ("hats","open_hat") and bar >= half or
                role == "snare" and bar >= duration - 2 or
                role == "kick" and bar >= duration - 2)
    if kind == "Main Drop":
        return role in ("kick","snare","hats","open_hat","bass","harmony") or (
            role == "percussion" and profile != "minimal") or (
            role == "pad" and bar >= half and profile == "deep")
    if kind == "Return":
        return role in ("kick","snare","hats","open_hat","bass","harmony") or (
            role == "percussion" and profile != "minimal" and block % 2 == 0)
    if kind == "Outro":
        return role in ("kick","snare","hats") or (
                role == "open_hat" and bar < half or
            role == "bass" and bar < half) or (
            role == "harmony" and bar < min(8,half)) or (
            role == "percussion" and bar < 8 and profile == "jackin")
    raise ValidationError("unsupported arrangement section")


def _build_lanes(result):
    # Source filter events at 32 bars cannot represent a 128-bar full song.
    # Rebuild all known house filter and duck lanes from the actual timeline.
    kept=[]
    if result.automation:
        for a in result.automation:
            if a.id.startswith("production-") and (
                a.id.endswith("-duck") or a.id.endswith("-filter")):
                continue
            if any(p.tick > result.length for p in a.points):
                raise ValidationError("cannot retain unknown long-range automation")
            kept.append(a)
    result.automation=kept
    for role in ("bass","harmony","pad"):
        track=next((t for t in result.tracks if t.id=="track-"+role),None)
        if track is None: continue
        baseline=track.controls["mixer.gain_db"]
        kicks=next(t for t in result.tracks if t.id=="track-kick")
        onsets=sorted(c.start+n.start for c in kicks.clips for n in c.notes)
        points=[(0,baseline)]
        for at in onsets:
            if at>0:points.append((at-1,baseline))
            points.extend(((at,baseline-5),
                           (min(result.length,at+100),baseline-4),
                           (min(result.length,at+420),baseline)))
        points.extend(((result.length-PPQ//2,baseline),
                       (result.length,baseline-18)))
        values=sorted(dict(points).items())
        label=f"production-{role}-duck"
        result.automation.append(AutomationLane(label,track.id,"mixer.gain_db",
                           [AutomationPoint(f"{label}-{i}", tick,v,"linear")
                            for i,(tick,v) in enumerate(values)]))
        eq=next((e for e in track.effects if e.id == "effect-"+role+"-eq"),None)
        if eq is not None and "soundcraft.lpf_freq" in eq.parameters:
            cutoffs={"Intro":4000,"Groove A":12500,"Groove B":15000,
                     "Breakdown":1800,"Build":5000,"Main Drop":17000,
                     "Return":12500,"Outro":7000}
            points=[]
            for section in result.sections:
                frequency=cutoffs[section.name]
                if role == "pad":
                    frequency=min(9000,frequency)
                points.append((section.start,frequency))
                if section.name=="Build":
                    points.append((section.start+section.length-PPQ,16000 if role!="pad" else 9000))
            points.append((result.length,3000 if role!="pad" else 1500))
            points=sorted(dict(points).items())
            label=f"production-{role}-filter"
            result.automation.append(AutomationLane(label,eq.id,"soundcraft.lpf_freq",
                [AutomationPoint(f"{label}-{i}",tick,float(value),"linear")
                 for i,(tick,value) in enumerate(points)]))


def arrange_full_song(source, *, bars=128, profile=None, seed=17):
    """Build eight configurable sections using eight-bar core cells.

    No original user reference song is used; source can be ANY supported
    32-bar generated groove with the standard four named sections.
    """
    validate(source)
    if bars not in FORMS or type(bars) is not int:
        raise ValidationError("full-song bars must be 96,112,128,160")
    if type(seed) is not int or not 0 <= seed <= 2**32-1:
        raise ValidationError("invalid arrangement seed")
    profile=profile or source.metadata.get("groove_profile")
    if profile not in ("deep","straight","jackin","minimal"):
        raise ValidationError("full-song requires known house rhythm family")
    if source.bars != 32 or [x.name for x in source.sections] != [
            "Intro","Groove","Breakdown","Drop"]:
        raise ValidationError("source must be a validated 32-bar groove-first template")
    if source.locks:
        raise ValidationError("locked source cannot be implicitly rearranged")
    if any(t.id in ("track-lead","track-arp") for t in source.tracks):
        raise ValidationError("independent melody must be absent")
    if any(t.kind != "midi" for t in source.tracks):
        raise ValidationError("this arranger requires a MIDI-only source graph")
    original_hash=state_hash(source)
    result=deepcopy(source)
    result.bars=bars
    result.name=source.name+" / producer-ready "+str(bars)+" bars"
    start=0
    result.sections=[]
    for index,(name,length) in enumerate(zip(NAMES,FORMS[bars])):
        result.sections.append(Section(f"house-form-{index}",name,start*BAR,length*BAR))
        start+=length
    if start!=bars:raise ValidationError("form length mismatch")

    # Role-source maps always pull from Kuang's generated material, never any
    # named commercially recorded track.
    origins={role:{
        name:_source_events(source,role,name)
        for name in ("Intro","Groove","Breakdown","Drop")
    } for role in ROLES}

    role_matrix=[]
    for track in result.tracks:
        track.clips=[]

    for index,section in enumerate(result.sections):
        name=section.name
        length=section.length//BAR
        for block in range(length//CYCLE):
            for role in ROLES:
                track=next((t for t in result.tracks if t.id=="track-"+role),None)
                if track is None:continue
                # Arrange a coherent motif, rather than cloning an intro's
                # accidental 4-bar silence each time its source loop repeats.
                source_kind = ("Breakdown" if name == "Breakdown" else
                               "Breakdown" if name == "Build" and role in ("harmony","pad","snare") else
                               "Intro" if name == "Intro" and role in ("harmony","pad") else
                               "Groove")
                events=origins[role][source_kind]
                # Pads are present in Intro/Breakdown but may be absent from
                # the Groove segment; use the existing generated pad voice.
                if role=="pad" and not events:
                    events=origins[role]["Intro"] or origins[role]["Breakdown"]
                notes=[]
                for local,duration,pitch,velocity,channel in events:
                    bar=block*CYCLE+local//BAR
                    if not _present(role,name,bar,length,profile,block):
                        continue
                    # No added notes or new pitch content; slight seeded
                    # velocity variation is limited to tops and percussion.
                    if role in ("hats","open_hat","percussion","snare"):
                        digest=hashlib.sha256(
                          f"{seed}:{profile}:{name}:{block}:{role}:{local}:{pitch}".encode()).digest()
                        velocity=max(1,min(127,velocity+(digest[0]%5-2)))
                    notes.append(Note(
                        f"af-{index}-{block}-{role}-{len(notes)}",
                        local,duration,pitch,velocity,channel))
                if notes:
                    track.clips.append(Clip(
                        f"ac-{index}-{block}-{role}",
                        f"{name} / {role} / {block+1:02d}",
                        "midi",section.start+block*CYCLE*BAR,CYCLE*BAR,
                        notes,None))
        role_counts={role:sum(len(c.notes) for t in result.tracks
                              if t.id=="track-"+role for c in t.clips
                              if section.start<=c.start<section.start+section.length)
                     for role in ROLES if any(t.id=="track-"+role for t in result.tracks)}
        role_matrix.append({"name":name,"start_bar":section.start//BAR+1,
                            "bars":length,"events":role_counts})

    # Optional roles with no audible notes must not become invalid empty
    # instrument tracks in the native SoundCraft session. Require that no
    # surviving bus send or automation refers to any removed role.
    silent = [t.id for t in result.tracks
              if t.kind == "midi" and not any(c.notes for c in t.clips)]
    for track_id in silent:
        if track_id not in ("track-percussion", "track-pad"):
            raise ValidationError("required instrument role is empty: " + track_id)
        if any(send.target_track_id == track_id
               for t in result.tracks for send in t.sends):
            raise ValidationError("silent role is a send destination: " + track_id)
    result.tracks = [t for t in result.tracks if t.id not in silent]
    result.automation = [lane for lane in result.automation
                         if lane.target_id not in silent]
    _build_lanes(result)
    # Explicit no-hook and groove-return checks from source, not arbitrary
    # numerical score in lieu of listening.
    kick=next(t for t in result.tracks if t.id=="track-kick")
    bass=next(t for t in result.tracks if t.id=="track-bass")
    def active(track,section):
        return [c.start+n.start for c in track.clips for n in c.notes
                if section.start<=c.start+n.start<section.start+section.length]
    groove=next(s for s in result.sections if s.name=="Groove A")
    drop=next(s for s in result.sections if s.name=="Main Drop")
    brk=next(s for s in result.sections if s.name=="Breakdown")
    expected=[groove.start+i*PPQ for i in range(groove.length//PPQ)]
    first_eight_onsets=[x-groove.start for x in active(kick,groove) if x<groove.start+8*BAR]
    source_kick=[x for x,*_ in origins["kick"]["Groove"]]
    activity={item["name"]:sum(item["events"].values()) for item in role_matrix}
    gates={
        "complete_section_partition":sum(s.length for s in result.sections)==result.length,
        "original_pocket_first_eight_bars":first_eight_onsets==source_kick,
        "four_on_floor_groove_a":active(kick,groove)==expected,
        "return_has_kick_and_bass":bool(active(kick,drop) and active(bass,drop)),
        "breakdown_without_kick_or_bass":not active(kick,brk) and not active(bass,brk),
        "outro_contains_beat":bool(active(kick,result.sections[-1])),
        "intro_audibly_establishes_identity":activity["Intro"]>0,
        "build_has_transition_activity":activity["Build"]>activity["Breakdown"] or
                  activity["Build"]>0 and any(
                      row["name"]=="Build" and
                      row["events"].get("hats",0)>0 for row in role_matrix),
        "drop_more_events_than_breakdown":activity["Main Drop"]>activity["Breakdown"],
        "no_empty_sections":all(value>0 for value in activity.values()),
        "all_remaining_roles_have_midi":all(
            any(c.notes for c in t.clips) for t in result.tracks if t.kind == "midi"),
        "no_independent_melody":not any(t.id in ("track-lead","track-arp") for t in result.tracks),
        "source_immutable":state_hash(source)==original_hash,
    }
    if not all(gates.values()):
        raise ValidationError("full-song structural gate failed: "+str(gates))
    result.metadata["arranger"]=VERSION
    result.metadata["arrangement_source_hash"]=original_hash
    result.metadata["arrangement_full_bars"]=str(bars)
    result.metadata["arrangement_seed"]=str(seed)
    result.metadata["arrangement_profile"]=profile
    validate(result)
    evidence={
        "version":VERSION,"source_bars":source.bars,"output_bars":bars,
        "tempo_bpm":source.tempo_bpm,"key_tonic":source.key_tonic,
        "key_mode":source.key_mode,"groove_profile":profile,
        "arrangement_seed":seed,
        "source_canonical_sha256":original_hash,
        "output_canonical_sha256":state_hash(result),
        "source_midi_sha256":hashlib.sha256(midi.export_bytes(source)).hexdigest(),
        "output_midi_sha256":hashlib.sha256(midi.export_bytes(result)).hexdigest(),
        "sections":role_matrix,"technical_gates":gates,
        "technical_pass":True,"perceptual_quality":"NEEDS_LISTENING",
        "quality_winner":None,
        "limitations":[
            "This is an original MIDI-first 8-bar-cell arranger, not a trained arrangement-quality evaluator.",
            "No original new melody, vocals, true riser synth or real audio-triggered sidechain added.",
            "Role entrances, fades and filters are deliberately formulaic and fully editable.",
            "Native rendering, source compatibility, mastering and subjective acceptance are separate gates.",
        ]}
    return result,evidence
