"""Deterministic diatonic sketches from validated SongSpec, with explicit host voices."""

import json
import random
from dataclasses import asdict

from .schema import (BAR, PPQ, AutomationLane, AutomationPoint, Clip, Effect, Instrument,
                     Note, ParameterSpec, Project, Section, Track, standard_parameters, validate)
from .song import ROLES, validate_spec

COMPOSER = "song-composer-v1"
SCALES = {"minor": (0, 2, 3, 5, 7, 8, 10), "major": (0, 2, 4, 5, 7, 9, 11)}


def compose(spec):
    spec = validate_spec(spec)
    rng = random.Random(spec.seed)
    scale = SCALES[spec.mode]

    def pitch(degree, octave):
        return 12 * octave + spec.tonic + scale[degree % 7] + 12 * (degree // 7)

    width = spec.bars // 4
    names = ("Arrival", "Expansion", "Suspension", "Dissolve") if spec.arrangement == "evolving" else ("Intro", "Main", "Break", "Finale")
    sections = [Section(f"section-{i}", name, i * width * BAR, width * BAR) for i, name in enumerate(names)]
    registry = standard_parameters() + [
        ParameterSpec("soundcraft.amp_attack", "ms", 0.5, 5000, 5, ["instrument"]),
        ParameterSpec("soundcraft.amp_decay", "ms", 1, 5000, 200, ["instrument"]),
        ParameterSpec("soundcraft.amp_sustain", "normalized", 0, 1, 0.7, ["instrument"]),
        ParameterSpec("soundcraft.amp_release", "ms", 1, 10000, 300, ["instrument"]),
        ParameterSpec("soundcraft.kick_decay", "ms", 50, 2000, 450, ["instrument"]),
        ParameterSpec("soundcraft.hat_decay", "ms", 20, 500, 80, ["instrument"]),
        ParameterSpec("soundcraft.hpf_on", "boolean", 0, 1, 0, ["effect"]),
        ParameterSpec("soundcraft.hpf_freq", "Hz", 10, 2000, 80, ["effect"]),
        ParameterSpec("soundcraft.low_mid_gain", "dB", -24, 24, 0, ["effect"]),
        ParameterSpec("soundcraft.size", "normalized", 0, 1, 0.5, ["effect"]),
        ParameterSpec("soundcraft.damping", "Hz", 1000, 20000, 6000, ["effect"]),
        ParameterSpec("soundcraft.pre_delay", "ms", 0, 250, 10, ["effect"]),
    ]
    tracks, automation = [], []
    energy = {"low": 0, "medium": 1, "high": 2}[spec.energy]
    # Seed changes the motif and rhythm as well as dynamics. All melodic notes stay diatonic.
    motif = rng.choice(((0, 2, 4, 2), (4, 2, 1, 0), (0, 4, 2, 1)))
    if spec.mood == "dark":
        motif = tuple(reversed(sorted(motif)))
    elif spec.mood == "uplifting":
        motif = tuple(sorted(motif))
    elif spec.mood == "dreamy":
        motif = (motif[0], motif[2], motif[1], motif[3])
    for role in ROLES:
        if role not in spec.instruments:
            continue
        drum = role in ("kick", "snare", "hats")
        label = {
            "kick": "Four on floor" if spec.genre == "house" else "Half-time kick",
            "snare": "Backbeat clap" if spec.genre == "house" else "Half-time snare",
            "hats": "Offbeat hats" if spec.genre == "house" else "Rolling hats",
            "bass": "808-style sub" if spec.genre == "trap" else "Offbeat bass" if spec.genre == "house" else "Low drone",
            "harmony": "Chord stabs" if spec.genre == "house" else "Spacious pad",
            "arp": "Pulse arpeggio" if spec.genre != "ambient" else "Sparse droplets",
            "lead": "Haunting motif" if spec.mood == "dark" else "Rising motif" if spec.mood == "uplifting" else "Floating motif",
        }[role]
        clips = []
        for si, section in enumerate(sections):
            if spec.arrangement == "song":
                if si == 0 and role in ("snare", "bass", "lead"):
                    continue
                if si == 2 and role in ("kick", "snare", "hats", "bass"):
                    continue
            elif si in (0, 3) and role in ("kick", "snare", "hats", "arp"):
                continue
            notes = []

            def add(tick, duration, note, velocity):
                notes.append(Note(f"note-{role}-{si}-{len(notes):04d}", tick, duration, note,
                                  max(1, min(120, velocity + rng.randint(-4, 4))), 9 if drum else 0))

            for local in range(width):
                bar = si * width + local
                base = local * BAR
                # Ambient harmony breathes for two bars; dance harmony changes each bar.
                degree = spec.progression[(bar // (2 if spec.genre == "ambient" else 1)) % 4]
                triad = [pitch(degree + d, 4) for d in (0, 2, 4)]
                # Invert into a compact register while preserving chord classes.
                triad = sorted(60 + (p - spec.tonic - 60) % 12 + spec.tonic for p in triad)
                bass = pitch(degree, 2)
                if bass > 47:
                    bass -= 12
                if role == "kick":
                    if spec.genre == "house":
                        hits = (0, 4, 8, 12)
                    elif spec.genre == "ambient":
                        hits = (0,)
                    else:
                        hits = (0, 6, 11) if (bar + spec.seed) % 2 == 0 else (0, 7, 14)
                    if energy == 0:
                        hits = hits[:2]
                    for step in hits:
                        add(base + step * PPQ // 4, PPQ // 8, 36, 108 if step == 0 else 95)
                elif role == "snare":
                    for step in ((4, 12) if spec.genre == "house" else (8,)):
                        add(base + step * PPQ // 4, PPQ // 6, 39 if spec.genre == "house" else 38, 94)
                    if spec.genre == "trap" and energy == 2 and local == width - 1:
                        add(base + 15 * PPQ // 4, PPQ // 8, 38, 52)
                elif role == "hats":
                    steps = range(2, 16, 4) if spec.genre == "house" else range(0, 16, 4 if energy == 0 else 2)
                    for step in steps:
                        add(base + step * PPQ // 4, PPQ // 10, 42, 66 if step % 4 == 0 else 49)
                    if energy == 2 and spec.genre == "trap" and bar % 2:
                        for step in (13, 15):
                            add(base + step * PPQ // 4, PPQ // 12, 42, 44)
                elif role == "bass":
                    if spec.genre == "ambient":
                        add(base, BAR - 120, bass, 64)
                    elif spec.genre == "house":
                        for step in range(2, 16, 4):
                            add(base + step * PPQ // 4, PPQ // 3, bass + (12 if step == 14 and energy == 2 else 0), 83)
                    else:
                        hits = ((0, 5), (6, 4), (11, 3), (14, 2)) if (bar + spec.seed) % 2 == 0 else ((0, 6), (7, 6), (14, 2))
                        if energy == 0:
                            hits = ((0, 10), (12, 4))
                        for step, length in hits:
                            add(base + step * PPQ // 4, length * PPQ // 4 - 30, bass, 93)
                elif role == "harmony":
                    if spec.genre == "house":
                        for step in ((2, 6, 10, 14) if energy else (2, 10)):
                            for n in triad:
                                add(base + step * PPQ // 4, PPQ // 3, n, 64)
                    else:
                        for n in triad:
                            add(base, BAR - 120, n, 55 if spec.genre == "ambient" else 49)
                elif role == "arp":
                    spacing = 2 * PPQ if spec.genre == "ambient" else PPQ if energy == 0 else PPQ // 2
                    for step in range(BAR // spacing):
                        add(base + step * spacing, spacing // 2, triad[(step + bar + spec.seed) % 3] + 12, 54)
                elif role == "lead":
                    if spec.genre == "ambient":
                        add(base + PPQ, PPQ * 2, pitch(degree + motif[bar % 4], 5), 58)
                    elif spec.genre == "house":
                        for step in range(2 if energy == 0 else 4):
                            add(base + step * PPQ, PPQ // 2, pitch(degree + motif[step], 5), 75)
                    else:
                        for step, offset in enumerate((0, 6, 10) if energy else (0, 10)):
                            add(base + offset * PPQ // 4, PPQ // 2 if step else PPQ,
                                pitch(degree + motif[(bar + step) % 4], 5), 70)
            clips.append(Clip(f"clip-{role}-{si}", f"{label} / {section.name}", "midi", section.start, section.length, notes, None))
        cutoff = {"dark": 1100, "warm": 2100, "bright": 4200}[spec.palette]
        params = ({"soundcraft.kick_decay": 650 if spec.genre == "trap" else 230,
                   "soundcraft.hat_decay": 45 if spec.genre == "trap" else 90} if drum else
                  {"synth.cutoff_hz": 220 if role == "bass" else cutoff,
                   "synth.resonance": 0.08,
                   "soundcraft.amp_attack": 650 if role == "harmony" and spec.genre != "house" else 5,
                   "soundcraft.amp_decay": 180 if spec.genre == "house" else 500,
                   "soundcraft.amp_sustain": 0.8 if role in ("bass", "harmony") and spec.genre != "house" else 0.25,
                   "soundcraft.amp_release": 900 if role == "harmony" else 100 if role == "bass" else 300})
        instrument = Instrument(f"instrument-{role}", "plugin", "soundcraft:" + ("drum_synth" if drum else "subtractive_synth"), None, None, params)
        effects = []
        if role in ("bass", "harmony", "lead", "arp"):
            effects.append(Effect(f"effect-{role}-eq", "soundcraft:eq_7band", None,
                                  {"soundcraft.hpf_on": 1, "soundcraft.hpf_freq": 28 if role == "bass" else 180,
                                   "soundcraft.low_mid_gain": -2, "effect.bypass": 0}))
        if role in ("harmony", "lead", "arp") and spec.space != "dry":
            effects.append(Effect(f"effect-{role}-reverb", "soundcraft:room_reverb", None,
                                  {"effect.wet": 0.32 if spec.space == "wide" else 0.12, "effect.bypass": 0,
                                   "soundcraft.size": 0.85 if spec.space == "wide" else 0.4,
                                   "soundcraft.damping": 3500 if spec.palette == "dark" else 7000,
                                   "soundcraft.pre_delay": 28 if spec.space == "wide" else 8}))
        gain = {"kick": -10, "snare": -16, "hats": -23, "bass": -15, "harmony": -24, "arp": -25, "lead": -22}[role]
        if spec.genre == "ambient" and role == "harmony":
            gain = -18
        pan = {"harmony": -0.16, "arp": 0.24, "lead": 0.12, "hats": 0.15}.get(role, 0)
        tracks.append(Track(f"track-{role}", label, "midi", instrument,
                            {"mixer.gain_db": gain, "mixer.pan": pan, "mixer.mute": 0}, effects, clips, [], True))
        if role == "harmony":
            points = [(0, gain - 8), (width * BAR, gain), (2 * width * BAR, gain - 4),
                      (3 * width * BAR, gain), (spec.bars * BAR, gain - 12)]
            if spec.automation == "pulse":
                points = [(bar * BAR + beat * PPQ + offset, gain + delta)
                          for bar in range(spec.bars) for beat in range(4) for offset, delta in ((0, -7), (PPQ // 2, 0))]
                points.append((spec.bars * BAR, gain - 12))
            automation.append(AutomationLane("automation-harmony-gain", "track-harmony", "mixer.gain_db",
                              [AutomationPoint(f"point-harmony-{i}", tick, value, "linear") for i, (tick, value) in enumerate(points)]))
    project = Project("0.1", "project-kuang-song", f"Kuang {spec.genre} sketch", spec.bpm, spec.tonic, spec.mode,
                      [4, 4], PPQ, spec.bars, sections, registry, tracks, automation, [],
                      {"composer": COMPOSER, "seed": str(spec.seed),
                       "song_spec": json.dumps(asdict(spec), sort_keys=True, separators=(",", ":"))})
    validate(project)
    return project
