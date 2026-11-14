"""Source-independent, groove-preserving harmony profiles for house templates.

Only major / natural minor are supported. These profiles change chord
*content*, not its rhythm or the recorded bass/drum pocket.
"""
from __future__ import annotations

import re
from .composer import SCALES
from .schema import BAR, ValidationError
from .song import check_prompt, validate_spec

HARMONY_VERSION = "house-harmony-v1"
HARMONY_PROFILES = ("simple", "extended")
_UNSUPPORTED_MODES = re.compile(
    r"\b(phrygian|dorian|mixolydian|lydian|locrian|ionian|aeolian|"
    r"harmonic\s+minor|melodic\s+minor|borrowed\s+chords?|modal\s+house)\b",
    re.I,
)


def select_harmony(prompt: str, groove_profile: str, requested: str = "auto") -> str:
    """Resolve the requested chord vocabulary without misreporting modal support."""
    check_prompt(prompt)
    if requested not in ("auto", *HARMONY_PROFILES):
        raise ValidationError("harmony profile must be auto, simple or extended")
    match = _UNSUPPORTED_MODES.search(prompt)
    if match:
        raise ValidationError(
            f"groove-template does not support explicit {match.group(0)!r} harmony; "
            "only major and natural minor are implemented")
    lower = prompt.lower()
    simple = bool(re.search(r"\b(simple\s+(?:chords?|triads?)|triads?\s+only|"
                            r"plain\s+triads?|no\s+(?:sevenths?|ninths?))\b", lower))
    positive_text = re.sub(r"\b(?:no|without)\s+(?:sevenths?|ninths?)\b", "", lower)
    extended = bool(re.search(r"\b(extended\s+(?:chords?|harmony)|"
                              r"sevenths?|ninths?|jazzy\s+chords?)\b", positive_text))
    if simple and extended:
        raise ValidationError("conflicting simple and extended harmony instructions")
    if requested != "auto":
        if (simple and requested != "simple") or (extended and requested != "extended"):
            raise ValidationError("explicit harmony profile conflicts with prompt")
        return requested
    if simple:
        return "simple"
    if extended:
        return "extended"
    return "extended" if groove_profile == "deep" else "simple"


def _pitch(degree, tonic, scale):
    return (tonic + scale[degree % 7] + 12 * (degree // 7)) % 12


def apply_harmony(project, spec, profile: str):
    """Apply triads or retain authored seventh voicings; return technical evidence.

    The refined composer supplies four-voice diatonic sevenths. Simple mode
    drops the degree-seven pitch class from the chord and optional pad. There
    is no re-quantization, transposition, or edit to the kick/bass note events.
    """
    spec = validate_spec(spec)
    if profile not in HARMONY_PROFILES:
        raise ValidationError("invalid harmony profile")
    scale = SCALES[spec.mode]
    harmony = next((t for t in project.tracks if t.id == "track-harmony"), None)
    if harmony is None:
        raise ValidationError("house template requires a chord track")
    edited_notes = 0
    for track in (t for t in project.tracks if t.id in ("track-harmony", "track-pad")):
        for clip in track.clips:
            notes = []
            for note in clip.notes:
                bar = (clip.start + note.start) // BAR
                degree = spec.progression[(bar // 2) % 4]
                allowed = {_pitch(degree + x, spec.tonic, scale) for x in (0, 2, 4, 6)}
                if note.pitch % 12 not in allowed:
                    raise ValidationError("source chord voicing differs from planned harmony")
                if profile == "simple" and note.pitch % 12 == _pitch(degree + 6, spec.tonic, scale):
                    edited_notes += 1
                    continue
                notes.append(note)
            clip.notes = notes
        if profile == "simple":
            track.name = ("Triad chord stabs" if track.id == "track-harmony"
                          else "Supporting triad pad")
    blocks = []
    functional_bass_ok = True
    bass = next((t for t in project.tracks if t.id == "track-bass"), None)
    if bass is None:
        raise ValidationError("house template requires bass")
    for bar in range(spec.bars):
        degree = spec.progression[(bar // 2) % 4]
        allowed = {_pitch(degree + x, spec.tonic, scale) for x in
                   ((0, 2, 4) if profile == "simple" else (0, 2, 4, 6))}
        chord_events = [n for c in harmony.clips for n in c.notes
                        if bar * BAR <= c.start + n.start < (bar + 1) * BAR]
        if not chord_events or any(n.pitch % 12 not in allowed for n in chord_events):
            raise ValidationError("harmonic profile disagrees with rendered chord pitch classes")
        bass_events = [n for c in bass.clips for n in c.notes
                       if bar * BAR <= c.start + n.start < (bar + 1) * BAR]
        bass_ok = all(n.pitch % 12 in {_pitch(degree + x, spec.tonic, scale)
                                      for x in (0, 4)} for n in bass_events)
        functional_bass_ok &= bass_ok
        blocks.append({
            "bar": bar + 1, "degree": degree,
            "chord_pitch_classes": sorted({n.pitch % 12 for n in chord_events}),
            "expected_pitch_classes": sorted(allowed),
            "chord_event_count": len(chord_events),
            "bass_note_count": len(bass_events),
            "bass_functional": bass_ok,
        })
    if not functional_bass_ok:
        raise ValidationError("bass note function conflicts with planned chord roots/fifths")
    project.metadata["harmony_profile"] = profile
    return {
        "version": HARMONY_VERSION, "profile": profile,
        "tonic": spec.tonic, "mode": spec.mode,
        "seventh_voices_removed": edited_notes,
        "technical_gates": {
            "supported_key_mode": spec.mode in ("major", "minor"),
            "chords_fit_progression": True,
            "bass_root_or_fifth": functional_bass_ok,
            "no_chord_rhythm_requantization": True,
        },
        "perceptual_quality": "NEEDS_LISTENING",
        "bar_summary": blocks,
        "limitations": [
            "Simple mode removes sevenths from authored voicings; extended mode retains "
            "diatonic sevenths; ninth/sus/modal and user-authored chord inversions are not yet implemented.",
            "Harmonic consistency does not certify a pleasant progression, coherent tonal center, "
            "professional mix or original song quality.",
        ],
    }
