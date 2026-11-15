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
from .house_harmony_interlock import apply_interlock
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



def _reschedule_impact_duck(project):
    """Bounded source-preserving impact duck: bass tail + optional pad only.

    A kick's onset is the timing reference, not a measured envelope detector.
    Deliberately avoid pumping foreground chords: those already have their
    own rhythmic articulation and can turn a bass offbeat into a masked hit.
    Recovery duration is defined in milliseconds, invariant across BPM.
    """
    tracks = {track.id: track for track in project.tracks}
    kick = tracks.get("track-kick")
    if kick is None:
        raise ValidationError("impact duck requires kick MIDI")
    onsets = sorted({c.start + note.start for c in kick.clips for note in c.notes})
    if not onsets:
        raise ValidationError("impact duck requires at least one kick onset")
    for role in ("bass", "harmony", "pad"):
        lane_id = f"production-{role}-duck"
        project.automation = [lane for lane in project.automation if lane.id != lane_id]
        channel = tracks.get(f"track-{role}")
        if channel is None or role == "harmony":
            continue
        depth_db, recovery_ms = ((3., 115.) if role == "bass" else (1.25, 143.))
        recovery = max(1, round(recovery_ms * project.tempo_bpm * PPQ / 60000.))
        baseline = channel.controls["mixer.gain_db"]
        values = [(0, baseline)]
        for at in onsets:
            if at > 0:
                values.append((at - 1, baseline))
            values.extend(((at, baseline - depth_db),
                           (min(at + recovery, project.length), baseline)))
        values.extend(((project.length - PPQ // 2, baseline),
                       (project.length, baseline - 18)))
        # Preserve the usual end fade and exact zero-time kick duck.
        points = sorted(dict(values).items())
        project.automation.append(AutomationLane(lane_id, channel.id,
            "mixer.gain_db", [AutomationPoint(f"{lane_id}-{i}", tick,
                                      value, "linear") for i, (tick,value) in enumerate(points)]))
    return {"bass_depth_db": 3., "bass_recovery_ms": 115.,
            "pad_depth_db": 1.25, "pad_recovery_ms": 143.,
            "dry_harmony_duck_db": 0., "kick_onset_count": len(onsets),
            "source_envelope_detector": False}


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



def _bass_groove_identity(profile: str, seed: int, bar: int):
    """Four musically distinct, bounded bass rhythm families.

    Intentional offbeat roots are retained, but profile and phrase define the
    movement. This is not a musical quality score or a Phase44 transcription.
    Each pattern contains (sixteenth-step, note-gate-kind, diatonic offset).
    """
    if profile not in PROFILES or type(seed) is not int or type(bar) is not int:
        raise ValidationError("invalid groove identity request")
    phrase = (seed + bar // 4) % 3
    if profile == "deep":
        patterns = (
            ((2,3,0),(6,2,0),(10,3,0)),
            ((2,2,0),(7,1,0),(10,3,0),(14,1,7)),
            ((2,3,0),(6,1,0),(10,2,0),(13,1,0)),
        )
    elif profile == "straight":
        patterns = (
            ((2,3,0),(6,2,0),(10,3,0),(14,1,0)),
            ((2,2,0),(6,2,0),(10,2,0),(14,1,7)),
            ((2,3,0),(6,2,0),(11,2,0),(14,1,0)),
        )
    elif profile == "jackin":
        patterns = (
            ((2,2,0),(5,1,4),(9,2,0),(13,1,0)),
            ((2,2,0),(6,1,0),(9,2,4),(14,1,0)),
            ((2,2,0),(5,1,0),(10,2,4),(13,1,0)),
        )
    else:  # Minimal house relies on pauses rather than constant dense bass.
        patterns = (
            ((2,3,0),(10,3,0)),
            ((6,2,0),(14,2,0)),
            ((2,3,0),(10,2,0),(14,1,0)),
        )
    motif = patterns[phrase]
    # A selective bar-end pickup changes an established phrase rather than
    # randomly changing every note and weakening the recognizable motif.
    if profile in ("deep","straight") and bar % 8 == 7 and motif[-1][0] < 13:
        motif += ((14,1,0),)
    return motif


def template(spec: SongSpec, *, profile: str, include_pad: bool = True,
             harmony_profile: str = "extended", impact_pocket: bool = False,
             harmony_interlock: bool = True, groove_identity_v2: bool = False):
    """Build a separate production; preserve established sketch/refined behavior."""
    spec = validate_spec(spec)
    if spec.genre != "house" or spec.arrangement != "song":
        raise ValidationError("groove-template requires house song intent")
    if not {"kick", "snare", "hats", "bass", "harmony"} <= set(spec.instruments):
        raise ValidationError("groove-template requires kick, snare, hats, bass and harmony")
    if (profile not in PROFILES or type(include_pad) is not bool or
        type(impact_pocket) is not bool or type(harmony_interlock) is not bool or
        type(groove_identity_v2) is not bool or (groove_identity_v2 and not impact_pocket)):
        raise ValidationError("invalid groove profile, pad or impact option")

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
                        offset = ((-2, 10, 22, -2)[beat] if impact_pocket else
                                  (12 if profile not in ("jackin", "deep") else 20))
                        add(base + beat * PPQ + PPQ // 2 + offset, 75,
                            46 if beat == 3 and full else 42,
                            65 if beat % 2 else 56)
                    if profile in ("jackin", "deep") and full:
                        for step in (3, 7, 11, 15):
                            add(base + step * step_ticks + 24, 60, 42, 35)
                elif role == "percussion" and full and profile != "minimal":
                    steps = ((1, 3, 5, 7, 9, 11, 13, 15) if impact_pocket else
                             ((1, 7, 13) if profile == "jackin" else (3, 11)))
                    for step in steps:
                        offset = ((-16, 12, 16, -4)[step % 4] if impact_pocket else
                                  (18 if bar % 2 else -8))
                        add(base + step * step_ticks + offset,
                            75 if not impact_pocket else 58, 42,
                            (37 if step % 4 == 1 else 48) if impact_pocket else (40 if step == 3 else 34))
                elif role == "bass" and bass_active:
                    degree = spec.progression[(bar // 2) % 4]
                    root = pitch(degree, 3)
                    if root > 40 + spec.tonic:
                        root -= 12
                    alternate = (bar + spec.seed) % 2 == 1
                    if groove_identity_v2:
                        motif = _bass_groove_identity(profile, spec.seed, bar)
                    elif impact_pocket:
                        # Legacy Phase44-inspired offbeat pocket retained unchanged.
                        motif = ((2, 2, 0), (6, 2, 0), (10, 2, 0))
                        if (profile != 'minimal' or alternate) and (bar % 2 == 0 or profile == 'jackin'):
                            motif += ((13, 1, 7),)
                    else:
                        motif = _bass_pattern(profile, alternate)
                    for step, length, note_degree in motif:
                        note = root if note_degree == 0 else (
                            root + pitch(degree + note_degree, 3) - pitch(degree, 3))
                        if groove_identity_v2:
                            # Longer offbeat body, capped before the next beat.
                            length_tick = {1: 190, 2: 342, 3: 420}[length]
                            velocity = 91 if note_degree == 0 else 77
                            if step >= 13:
                                velocity -= 8
                        else:
                            length_tick = ((326 if length == 2 else 211)
                                           if impact_pocket else length * step_ticks - 52)
                            velocity = ((95, 90, 94, 80)[(2,6,10,13).index(step)]
                                        if impact_pocket else (87 if step in (2, 10) else 77))
                        add(base + step * step_ticks + (0 if impact_pocket else 12), length_tick,
                            note, velocity)
            if notes:
                t.clips.append(Clip(f"house-tpl-clip-{role}-{si}",
                                    t.name + " / " + section.name,
                                    "midi", section.start, section.length, notes, None))

    if impact_pocket:
        # Small low-frequency shaping only, following the user's own Phase44
        # reference. Native source licensing and fader changes happen later.
        kick = tracks['kick']
        for fx in kick.effects:
            if 'soundcraft.low_shelf_gain' in fx.parameters:
                fx.parameters['soundcraft.low_shelf_gain'] = 2.0
                fx.parameters['soundcraft.low_shelf_freq'] = 65.0
            if 'soundcraft.drive' in fx.parameters:
                fx.parameters['soundcraft.drive'] = max(5.0,fx.parameters['soundcraft.drive'])
                if 'effect.wet' in fx.parameters:
                    fx.parameters['effect.wet'] = min(.4,fx.parameters['effect.wet']+.1)
    # Recalculate ducking against the actual newly generated kick onsets.
    # The strong uniform five-dB duck remains the historical non-impact default.
    # Impact mode instead preserves dry chord transients and ducks only the
    # bass tail and (when present) the background pad; independent editable
    # gain lanes preserve the source preset's attack and internal FX behavior.
    impact_duck = _reschedule_impact_duck if impact_pocket else None
    if impact_pocket:
        impact_duck(p)
    else:
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
    interlock_evidence = (apply_interlock(p, profile, spec.seed)
                          if impact_pocket and harmony_interlock else None)

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
    if impact_pocket:
        p.metadata['groove_impact_pocket'] = 'source-preserving-impact-v2'
        if groove_identity_v2:
            p.metadata['groove_identity_version'] = 'style-dependent-bass-pocket-v2'
        p.metadata['ducking_policy'] = 'bass-tail-3db-115ms; pad-1.25db-143ms; harmony-dry-0db'
    p.metadata["groove_profile"] = profile
    if interlock_evidence is not None:
        p.metadata["harmony_interlock_version"] = interlock_evidence["version"]
    p.metadata["groove_gates"] = json.dumps(gates, sort_keys=True)
    validate(p)
    groove_events = {
        role: [(onset - groove.start) for onset in events]
        for role, events in onset_by_role.items()
    }
    receipt = {
        "version": VERSION, "selected_profile": profile,
        "groove_impact_pocket": impact_pocket,
        "impact_ducking_policy": ("source-preserving-impact-v2" if impact_pocket else "legacy"),
        "groove_identity_v2": groove_identity_v2,
        "seed": spec.seed, "full_groove_bars": width,
        "technical_gates": gates, "technical_pass": True,
        "perceptual_quality": "NEEDS_LISTENING",
        "candidate_search": "not implemented",
        "source_selection": "built-in SoundCraft instruments only; no real sample audition",
        "groove_fingerprint_sha256": hashlib.sha256(json.dumps(
            groove_events, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "full_groove_onsets": groove_events,
        "melody_roles": [], "harmony": harmonic_evidence,
        "harmony_interlock": interlock_evidence, "limitations": LIMITATIONS,
        "song_spec": asdict(spec),
    }
    return p, receipt
