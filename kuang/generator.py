"""Seeded symbolic arrangement; an orchestration fixture, not a quality claim."""

import random

from .schema import (BAR, PPQ, AutomationLane, AutomationPoint, Clip, Effect,
                     Instrument, Project, Section, Track, Note, standard_parameters, validate)


def generate(seed: int = 7) -> Project:
    rng = random.Random(seed)
    sections = [Section(f"section-{name}", name.replace("-", " ").title(), start * BAR, length * BAR)
                for name, start, length in [("intro", 0, 4), ("verse", 4, 8), ("hook-a", 12, 8),
                                            ("break", 20, 4), ("hook-b", 24, 8)]]
    names = [("kick", "Kick", 0, -9, 0), ("snare", "Snare / Clap", 0, -13, 0),
             ("hats", "Hats", 0, -18, 0.16), ("bass", "808 / Bass", 38, -12, 0),
             ("chords", "Chords", 89, -18, -0.18), ("pad", "Pad", 91, -21, 0.2),
             ("arp", "Arp", 81, -20, -0.25), ("lead", "Lead", 80, -17, 0.1)]
    tracks = []
    # Am - F - C - G, two bars per chord. All pitched notes use A natural minor.
    roots = [45, 41, 48, 43]
    chords = [[57, 60, 64], [53, 57, 60], [55, 60, 64], [55, 59, 62]]
    melody = [76, 72, 69, 72, 74, 71, 67, 69]
    for index, (slug, name, program, gain, pan) in enumerate(names):
        instrument = Instrument(f"instrument-{slug}", "midi", None, None,
                                None if index < 3 else program, {})
        clips = []
        channel = 9 if index < 3 else index - 3
        for section in sections:
            short = section.id.removeprefix("section-")
            start_bar, count = section.start // BAR, section.length // BAR
            if short == "intro" and slug in ("snare", "bass", "lead"):
                continue
            if short == "break" and slug in ("kick", "snare", "hats", "bass", "lead"):
                continue
            if short == "verse" and slug == "lead":
                continue
            notes = []

            def add(tick, duration, pitch, velocity):
                notes.append(Note(f"note-{slug}-{short}-{len(notes):04d}", tick, duration, pitch,
                                  max(1, min(127, velocity + rng.randint(-5, 5))), channel))

            for local_bar in range(count):
                bar = start_bar + local_bar
                base = local_bar * BAR
                root = roots[(bar // 2) % 4]
                chord = chords[(bar // 2) % 4]
                if slug == "kick":
                    hits = [0, 1.5, 2.75] if bar % 2 == 0 else [0, 2, 3.5]
                    if short == "intro":
                        hits = [0, 2]
                    for beat in hits:
                        add(base + int(beat * PPQ), PPQ // 8, 36, 112 if beat == 0 else 98)
                elif slug == "snare":
                    for beat in (1, 3):
                        add(base + beat * PPQ, PPQ // 6, 38, 106)
                        add(base + beat * PPQ + 12, PPQ // 8, 39, 72)
                    if local_bar == count - 1:
                        add(base + 15 * PPQ // 4, PPQ // 8, 38, 62)
                elif slug == "hats":
                    for step in range(8 if short != "intro" else 4):
                        spacing = PPQ // 2 if short != "intro" else PPQ
                        add(base + step * spacing, PPQ // 10, 42, 80 if step % 2 == 0 else 58)
                    if short.startswith("hook") and bar % 2:
                        for step in (13, 15):
                            add(base + step * PPQ // 4, PPQ // 10, 42, 54)
                        add(base + 3 * PPQ + PPQ // 2, PPQ // 4, 46, 67)
                elif slug == "bass":
                    for beat, duration, pitch in [(0, 1.25, root - 12), (1.5, 0.75, root - 12),
                                                  (2.75, 0.5, root - 12), (3.5, 0.375, root)]:
                        add(base + int(beat * PPQ), int(duration * PPQ), pitch, 103)
                elif slug == "chords":
                    for beat in (0, 2):
                        for pitch in chord:
                            add(base + beat * PPQ, int(1.6 * PPQ), pitch, 75)
                elif slug == "pad":
                    for pitch in chord:
                        add(base, BAR - PPQ // 8, pitch + 12, 52)
                elif slug == "arp":
                    spacing = PPQ if short in ("intro", "break") else PPQ // 2
                    for step in range(BAR // spacing):
                        add(base + step * spacing, spacing * 3 // 4,
                            chord[[0, 1, 2, 1][step % 4]] + 12, 67)
                elif slug == "lead":
                    for step in range(4):
                        add(base + step * PPQ + (PPQ // 4 if step % 2 else 0),
                            PPQ // 2 if step < 3 else PPQ * 2 // 3,
                            melody[(bar * 2 + step) % len(melody)], 89)
            clips.append(Clip(f"clip-{slug}-{short}", f"{name} — {section.name}", "midi",
                              section.start, section.length, notes, None))
        effects = [Effect("effect-pad-reverb", "reaper:ReaVerbate", None, {"effect.wet": 0.18, "effect.bypass": 0})] if slug == "pad" else []
        tracks.append(Track(f"track-{slug}", name, "midi", instrument,
                            {"mixer.gain_db": gain, "mixer.pan": pan, "mixer.mute": 0}, effects, clips, [], True))
    automation = [AutomationLane("automation-pad-gain", "track-pad", "mixer.gain_db", [
        AutomationPoint("point-pad-intro", 0, -30, "linear"),
        AutomationPoint("point-pad-verse", 4 * BAR, -21, "linear"),
        AutomationPoint("point-pad-break", 20 * BAR, -25, "linear"),
        AutomationPoint("point-pad-hook", 24 * BAR, -21, "linear"),
        AutomationPoint("point-pad-end", 32 * BAR, -32, "linear"),
    ])]
    project = Project("0.1", "project-kuang-demo", "Kuang Phase 0 — symbolic demo", 124, 9, "minor",
                      [4, 4], PPQ, 32, sections, standard_parameters(), tracks, automation, [],
                      {"seed": str(seed), "engine": "seeded-symbolic-v1", "audio_status": "not rendered"})
    validate(project)
    return project
