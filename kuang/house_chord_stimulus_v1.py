"""Deterministic isolated chord source stimulus for native SoundCraft evaluation.

Adapt a proven house project's *actual* first Groove voicing/velocity/gate to
a private 8bar test session; mute other MIDI roles, hold the tested patch and
effects as-is. Test instrument response, NOT the user's original arrangement.
"""
from __future__ import annotations

from copy import deepcopy

from .schema import BAR,PPQ,Clip,Note,ValidationError,state_hash,validate
from .house_note_envelope_v1 import CHORD_STRUM_SPREAD_TICKS,_note_onsets

VERSION="house-chord-stimulus-v1"
TEST_BARS=8


def chord_stimulus(source, *, section="Groove A"):
    validate(source)
    anchor=next((s for s in source.sections if s.name==section and s.length>=TEST_BARS*BAR),None)
    if anchor is None:raise ValidationError("8bar house Groove for chord source stimulus required")
    harmony=next((t for t in source.tracks if t.id=="track-harmony"),None)
    if harmony is None or harmony.kind!="midi" or harmony.instrument is None:
        raise ValidationError("original actual chord instrument required")
    # Select the earliest complete existing strummed chord with >=3 unique
    # pitches. Same pitches/velocities/gates and inter-note stagger, not an
    # invented "standard" C-major chord or fixed octaves across styles.
    events=[]
    for clip in harmony.clips:
        for n in clip.notes:
            t=clip.start+n.start
            if anchor.start<=t<anchor.start+BAR:
                events.append((t,n.pitch,n.duration,n.velocity,n.channel))
    events.sort()
    if not events:raise ValidationError("source first Groove bar has no chord")
    chosen=None
    for t,pitch,duration,velocity,ch in events:
        notes=[e for e in events if t<=e[0]<=t+CHORD_STRUM_SPREAD_TICKS]
        if len(notes)<3:continue
        keys=[n[1] for n in notes]
        if len(keys)!=len(set(keys)):continue
        chosen=notes
        break
    if chosen is None:
        raise ValidationError("original registered chord voicing too ambiguous for fixed comparison")
    attack=min(n[0] for n in chosen)
    max_gate=max(n[0]-attack+n[2] for n in chosen)
    if max_gate>PPQ*2:
        raise ValidationError("source chord gate too long for controlled isolated stimulus")
    project=deepcopy(source)
    track=next(t for t in project.tracks if t.id=="track-harmony")
    start=anchor.start
    notes=[]
    positions=(BAR,3*BAR,5*BAR,7*BAR)
    for i,offset in enumerate(positions):
        for j,(tick,pitch,gate,vel,ch) in enumerate(chosen):
            notes.append(Note(f"stim-chord-{i}-{j}",
                              offset+tick-attack,gate,pitch,vel,ch))
    track.clips=[Clip("stim-chord-eightbars","Private fixed-register chord audition",
                      "midi",start,TEST_BARS*BAR,notes,None)]
    for t in project.tracks:
        if t.id!="track-harmony" and t.kind=="midi":
            t.controls["mixer.mute"]=1.
        elif t.id=="track-harmony":
            t.controls["mixer.mute"]=0.
    # Frozen song automation may intentionally duck or open filters while
    # the kick/musical backing is muted. This is the actual existing FX/lanes,
    # not a dry preset test; the resulting metrics must say so explicitly.
    validate(project)
    events,_,_=_note_onsets(project,"harmony",section,TEST_BARS)
    if len(events)!=4 or any(e["voices"]!=len(chosen) for e in events):
        raise ValidationError("stimulus grouped chord shape incorrect")
    for before,after in zip(source.tracks,project.tracks):
        if (before.instrument,before.effects,before.sends,before.output_master)!=(
                after.instrument,after.effects,after.sends,after.output_master):
            raise ValidationError("test changed instrument/FX/source identity")
    return project,{
        "version":VERSION,
        "original_canonical_sha256":state_hash(source),
        "stimulus_canonical_sha256":state_hash(project),
        "source_section":section,"source_original_first_chord_tick":attack,
        "source_pitches":[n[1] for n in chosen],
        "source_velocities":[n[3] for n in chosen],
        "source_midi_gate_ticks":[n[2] for n in chosen],
        "source_strum_offsets_ticks":[n[0]-attack for n in chosen],
        "repeated_events":4,"repetition_interval_bars":2,
        "source_midi_preserved_on_disk":True,
        "role_mutes_only":True,"source_instrument_and_fx_unchanged":True,
        "context":"isolated chords through original track/buses/FX/automation, not dry oscillator",
        "musical_quality":"NOT_EVALUATED"
    }
