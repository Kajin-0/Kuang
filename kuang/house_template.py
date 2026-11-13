"""Opt-in groove-first house template: a deterministic, editable MIDI foundation.

This is a curated rhythmic starting point, not an automatic quality judgment.
No third-party samples, plugins, patches or full-length audio are generated here.
"""
from __future__ import annotations

import hashlib
import json
import random
from copy import deepcopy
from dataclasses import asdict

from .composer import SCALES, compose
from .house_harmony import apply_harmony
from .production import refine_house
from .schema import (
    BAR, PPQ, AutomationLane, AutomationPoint, Clip, Note,
    ValidationError, validate,
)
from .song import SongSpec, validate_spec

VERSION = "house-groove-template-v1"
PROFILES = ("straight", "deep", "jackin", "minimal")
ROLES = ("kick", "snare", "hats", "percussion", "bass")
LIMITATIONS = [
    "Curated MIDI house archetypes, not a human-approved or professionally mastered song.",
    "Built-in SoundCraft drum/synth devices, not selected real sampled drums or Vital presets.",
    "No standalone lead, arp, vocals, or independent melody; optional supporting pad.",
    "Original template supports only 8/16/32 bars, constant 4/4 and diatonic major/minor.",
    "Simple triads or diatonic sevenths only; no true modal, suspended or ninth-chord support.",
    "Programmed ducking uses actual kick MIDI onsets, not audio-triggered compression.",
    "No per-role audio-calibrated mastering or learned perceptual gate yet.",
]


def select_profile(prompt: str, seed: int, requested: str = "auto") -> str:
    """Choose a recognizable style family, not independent random drum events."""
    if requested not in ("auto", *PROFILES):
        raise ValidationError("groove profile must be auto, straight, deep, jackin or minimal")
    if requested != "auto":
        return requested
    lower = prompt.lower()
    if "minimal" in lower or "stripped" in lower:
        return "minimal"
    if "jackin" in lower or "funky" in lower or "disco house" in lower:
        return "jackin"
    if "deep house" in lower or "deep-house" in lower:
        return "deep"
    # For generic house, vary between two proven foundations.
    return ("straight", "deep")[seed % 2]


def _bass_pattern(profile: str, alternate: bool):
    """Sixteenth-step start, length, diatonic pitch offset (0=root, 4=fifth, 7=octave)."""
    if profile == "straight":
        return ((2, 2, 0), (6, 2, 0), (10, 2, 0), (14, 1, 0)) if not alternate else (
            (2, 2, 0), (6, 2, 0), (10, 2, 0), (14, 1, 7))
    if profile == "deep":
        return ((2, 2, 0), (6, 1, 0), (10, 2, 0)) if not alternate else (
            (2, 2, 0), (7, 1, 0), (10, 2, 0), (14, 1, 7))
    if profile == "jackin":
        return ((0, 1, 0), (3, 1, 0), (6, 1, 4), (10, 2, 0), (14, 1, 0)) if not alternate else (
            (2, 2, 0), (5, 1, 0), (9, 1, 4), (12, 2, 0), (15, 1, 7))
    return ((2, 2, 0), (10, 2, 0)) if not alternate else (
        (6, 2, 0), (14, 2, 0))


def template(spec: SongSpec, *, profile: str, include_pad: bool = True,
             harmony_profile: str = "extended"):
    """Build a separate production; preserve established sketch/refined behavior."""
    spec = validate_spec(spec)
    if spec.genre != "house" or spec.arrangement != "song":
        raise ValidationError("groove-template requires house song intent")
    if not {"kick", "snare", "hats", "bass", "harmony"} <= set(spec.instruments):
        raise ValidationError("groove-template requires kick, snare, hats, bass and harmony")
    if profile not in PROFILES or type(include_pad) is not bool:
        raise ValidationError("invalid groove profile or pad option")

    # Explicitly omit the failed/future melody engine, rather than merely muting it.
    spec = deepcopy(spec)
    spec.instruments = [r for r in spec.instruments if r not in ("lead", "arp")]
    p = refine_house(spec, compose(spec), include_pad=include_pad, kick_aligned_ducking=True)
    p.name = f"Kuang {profile} house template"
    rng = random.Random(spec.seed)
    tracks = {t.id.removeprefix("track-"): t for t in p.tracks}
    perc = deepcopy(tracks["hats"])
    perc.id = "track-percussion"
    perc.name = "Light auxiliary hat percussion"
    perc.instrument.id = "instrument-percussion"
    for fx in perc.effects:
        fx.id = "house-template-" + fx.id + "-percussion"
    perc.controls["mixer.gain_db"] = -9
    perc.controls["mixer.pan"] = -.25
    perc.clips = []
    p.tracks.append(perc)
    tracks["percussion"] = perc

    scale = SCALES[spec.mode]
    width = spec.bars // 4
    step_ticks = PPQ // 4

    def pitch(degree: int, octave: int) -> int:
        return 12 * octave + spec.tonic + scale[degree % 7] + 12 * (degree // 7)

    for role in ROLES:
        t = tracks[role]
        t.clips = []
        t.name = {
            "kick": "Four-to-floor kick",
            "snare": "Backbeat clap and restrained ghosts",
            "hats": "Offbeat hats",
            "percussion": "Light shuffled ticks",
            "bass": "Syncopated bass pocket",
        }[role]
        for si, section in enumerate(p.sections):
            notes = []

            def add(tick, length, note, velocity):
                tick = int(tick)
                if tick < 0 or tick >= section.length:
                    return
                duration = max(1, min(int(length), section.length - tick))
                velocity = max(1, min(120, int(velocity) + rng.randint(-2, 2)))
                notes.append(Note(f"house-tpl-{role}-{si}-{len(notes):04d}",
                                  tick, duration, note, velocity, 9 if role != "bass" else 0))

            for local in range(width):
                bar = si * width + local
                base = local * BAR
                intro = si == 0
                break_section = si == 2
                full = si in (1, 3)
                kick_active = not break_section
                bass_active = full or intro and local >= max(1, width // 2)
                hats_active = full or intro and local >= max(1, width // 2) or (
                    break_section and local == width - 1)
                clap_active = full or intro and local == width - 1 or (
                    break_section and local == width - 1)
                # The last beat before the drop can withdraw the kick.
                last_drop_bar = si == 3 and local == width - 1
                if role == "kick" and kick_active:
                    for beat in range(3 if last_drop_bar else 4):
                        add(base + beat * PPQ, 125, 36,
                            112 if beat in (0, 2) else 106)
                elif role == "snare" and clap_active:
                    for beat in (1, 3):
                        add(base + beat * PPQ + 14, 105, 39,
                            91 if beat == 1 else 87)
                    if full and profile in ("jackin", "deep") and bar % 2:
                        add(base + 11 * step_ticks + 25, 70, 38, 38)
                elif role == "hats" and hats_active:
                    for beat in range(4):
                        offset = 12 if profile not in ("jackin", "deep") else 20
                        add(base + beat * PPQ + PPQ // 2 + offset, 75,
                            46 if beat == 3 and full else 42,
                            65 if beat % 2 else 56)
                    if profile in ("jackin", "deep") and full:
                        for step in (3, 7, 11, 15):
                            add(base + step * step_ticks + 24, 60, 42, 35)
                elif role == "percussion" and full and profile != "minimal":
                    for step in ((1, 7, 13) if profile == "jackin" else (3, 11)):
                        add(base + step * step_ticks + (18 if bar % 2 else -8),
                            75, 42, 40 if step == 3 else 34)
                elif role == "bass" and bass_active:
                    degree = spec.progression[(bar // 2) % 4]
                    root = pitch(degree, 3)
                    if root > 40 + spec.tonic:
                        root -= 12
                    alternate = (bar + spec.seed) % 2 == 1
                    for step, length, note_degree in _bass_pattern(profile, alternate):
                        note = root if note_degree == 0 else (
                            root + pitch(degree + note_degree, 3) - pitch(degree, 3))
                        add(base + step * step_ticks + 12, length * step_ticks - 52,
                            note, 87 if step in (2, 10) else 77)
            if notes:
                t.clips.append(Clip(f"house-tpl-clip-{role}-{si}",
                                    t.name + " / " + section.name,
                                    "midi", section.start, section.length, notes, None))

    # Recalculate scheduled pumping after the new kick grid, rather than
    # retaining envelopes computed from the old refined-composer kick.
    kick_onsets = sorted({c.start + n.start for c in tracks["kick"].clips for n in c.notes})
    for role in ("bass", "harmony", "pad"):
        if role not in tracks:
            continue
        lane_id = f"production-{role}-duck"
        p.automation = [lane for lane in p.automation if lane.id != lane_id]
        baseline = tracks[role].controls["mixer.gain_db"]
        values = [(0, baseline)]
        for onset in kick_onsets:
            if onset > 0:
                values.append((onset - 1, baseline))
            values.extend(((onset, baseline - 5),
                           (min(onset + 100, spec.bars * BAR), baseline - 4),
                           (min(onset + 420, spec.bars * BAR), baseline)))
        values.extend(((spec.bars * BAR - PPQ // 2, baseline),
                       (spec.bars * BAR, baseline - 18)))
        ticks = sorted(dict(values).items())
        p.automation.append(AutomationLane(lane_id, tracks[role].id, "mixer.gain_db",
            [AutomationPoint(f"{lane_id}-{i}", tick, value, "linear")
             for i, (tick, value) in enumerate(ticks)]))

    # Adjust chord vocabulary without touching the approved kick/bass rhythm.
    harmonic_evidence = apply_harmony(p, spec, harmony_profile)

    # Machine-checkable G1 structural gates, **not** a listening approval.
    groove = p.sections[1]
    onset_by_role = {
        role: sorted(c.start + n.start for c in tracks[role].clips for n in c.notes
                     if groove.start <= c.start + n.start < groove.start + groove.length)
        for role in ROLES
    }
    expected_kicks = [groove.start + bar * BAR + beat * PPQ
                      for bar in range(width) for beat in range(4)]
    expected_backbeats = [groove.start + bar * BAR + beat * PPQ + 14
                          for bar in range(width) for beat in (1, 3)]
    gates = {
        "four_on_floor_full_groove": onset_by_role["kick"] == expected_kicks,
        "backbeat_full_groove": expected_backbeats == [
            x for x in onset_by_role["snare"] if x in expected_backbeats],
        "bass_present": bool(onset_by_role["bass"]),
        "hats_present": bool(onset_by_role["hats"]),
        "no_standalone_melody": not any(t.id in ("track-lead", "track-arp") for t in p.tracks),
        "role_separation": len({t.id for t in p.tracks}) == len(p.tracks),
    }
    if not all(gates.values()):
        raise ValidationError("groove-template structural gate failed")
    p.metadata["composer"] = VERSION
    p.metadata["groove_profile"] = profile
    p.metadata["groove_gates"] = json.dumps(gates, sort_keys=True)
    validate(p)
    groove_events = {
        role: [(onset - groove.start) for onset in events]
        for role, events in onset_by_role.items()
    }
    receipt = {
        "version": VERSION, "selected_profile": profile,
        "seed": spec.seed, "full_groove_bars": width,
        "technical_gates": gates, "technical_pass": True,
        "perceptual_quality": "NEEDS_LISTENING",
        "candidate_search": "not implemented",
        "source_selection": "built-in SoundCraft instruments only; no real sample audition",
        "groove_fingerprint_sha256": hashlib.sha256(json.dumps(
            groove_events, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "full_groove_onsets": groove_events,
        "melody_roles": [], "harmony": harmonic_evidence, "limitations": LIMITATIONS,
        "song_spec": asdict(spec),
    }
    return p, receipt
