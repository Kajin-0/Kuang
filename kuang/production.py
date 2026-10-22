"""Opt-in, deterministic house production; ordinary schema 0.1 objects only.

SongSpec remains musical intent. This profile expands it into editable notes,
devices and lanes, without altering the sketch composer or transaction engine.
Normalized oscillator selectors are 0=saw, 1/3=square, 2/3=sine, 1=triangle.
"""

import random
from copy import deepcopy

from .composer import SCALES
from .schema import (BAR, PPQ, AutomationLane, AutomationPoint, Clip, Effect,
                     Instrument, Note, ParameterSpec, Track, ValidationError, validate)
from .song import validate_spec

REFINED_COMPOSER = "house-refined-v1"
REFINED_LIMITATIONS = [
    "Deterministic house production template; subjective quality awaits human listening.",
    "Constant tempo, 4/4, 8/16/32 bars, diatonic seventh voicings; no vocals or external assets.",
    "Two-oscillator subtractive synthesis, amp/filter envelopes; no wavetable or exposed synth LFO.",
    "Filter movement uses native EQ automation; chorus/delay provide their own modulation.",
    "Beat gain envelopes are programmed ducking, not audio-triggered sidechain compression.",
    "No master bus processing, LUFS/true-peak certification or automatic host edit reconciliation.",
]


def refine_house(spec, sketch):
    """Return a new production, preserving the input and its original SongSpec."""
    spec = validate_spec(spec)
    if spec.genre != "house" or spec.arrangement != "song":
        raise ValidationError("refined production supports house with song arrangement only")
    project = deepcopy(sketch)
    project.name = "Kuang refined house"
    rng = random.Random(spec.seed)
    width = spec.bars // 4
    scale = SCALES[spec.mode]
    for section, name in zip(project.sections, ("Intro", "Groove", "Breakdown", "Drop")):
        section.name = name
    definitions = [
        ("osc1_wave", "normalized", 0, 1, 0, "instrument"),
        ("osc2_wave", "normalized", 0, 1, 0, "instrument"),
        ("osc_mix", "normalized", 0, 1, .5, "instrument"),
        ("filter_env_amount", "normalized", -1, 1, .3, "instrument"),
        ("filter_attack", "ms", .5, 5000, 5, "instrument"),
        ("filter_decay", "ms", 1, 5000, 300, "instrument"),
        ("filter_sustain", "normalized", 0, 1, .3, "instrument"),
        ("filter_release", "ms", 1, 10000, 300, "instrument"),
        ("velocity", "normalized", 0, 1, .7, "instrument"),
        ("level", "dB", -48, 6, -6, "instrument"),
        ("snare_decay", "ms", 50, 1000, 220, "instrument"),
        ("snare_snappy", "normalized", 0, 1, .6, "instrument"),
        ("open_hat_decay", "ms", 100, 3000, 600, "instrument"),
        ("low_mid_freq", "Hz", 20, 2000, 250, "effect"),
        ("high_shelf_gain", "dB", -24, 24, 0, "effect"),
        ("lpf_on", "boolean", 0, 1, 0, "effect"),
        ("lpf_freq", "Hz", 1000, 20000, 18000, "effect"),
        ("threshold", "dB", -60, 0, -20, "effect"),
        ("attack", "ms", .01, 300, 10, "effect"),
        ("release", "ms", 5, 3000, 100, "effect"),
        ("makeup", "dB", 0, 40, 0, "effect"),
        ("drive", "dB", 0, 36, 6, "effect"),
        ("output", "dB", -24, 12, 0, "effect"),
        ("tone", "Hz", 1000, 20000, 20000, "effect"),
        ("time", "ms", 1, 2000, 250, "effect"),
        ("feedback", "normalized", -.99, .99, .3, "effect"),
        ("mod_rate", "Hz", .01, 10, .5, "effect"),
        ("mod_depth", "normalized", 0, 1, 0, "effect"),
        ("lpf", "Hz", 500, 20000, 12000, "effect"),
        ("rate", "Hz", .051, 5, .8, "effect"),
        ("depth", "normalized", 0, 1, .5, "effect"),
        ("spread", "normalized", 0, 1, 1, "effect"),
        ("decay_ms", "ms", 101, 20000, 1200, "effect"),
        ("low_cut", "Hz", 20, 1000, 20, "effect"),
        ("width", "normalized", 0, 1, 1, "effect"),
    ]
    project.parameters += [ParameterSpec("soundcraft."+n, u, lo, hi, default, [kind])
                           for n, u, lo, hi, default, kind in definitions]
    project.automation = []

    def pitch(degree, octave):
        return octave * 12 + spec.tonic + scale[degree % 7] + 12 * (degree // 7)

    # One harmonic phrase lasts eight beats, giving the melody room to answer.
    roots = [spec.progression[(bar // 2) % 4] for bar in range(spec.bars)]
    voicings, previous = [], (48+spec.tonic, 55+spec.tonic, 59+spec.tonic, 64+spec.tonic)
    for root in roots:
        pcs = [(pitch(root+d, 4) % 12) for d in (0, 2, 4, 6)]
        candidates = []
        for rotation in range(4):
            ordered = pcs[rotation:] + pcs[:rotation]
            for bottom in range(48+spec.tonic, 61+spec.tonic):
                if bottom % 12 != ordered[0]:
                    continue
                chord = [bottom]
                for pc in ordered[1:]:
                    chord.append(chord[-1]+1+(pc-chord[-1]-1) % 12)
                candidates.append(tuple(chord))
        voice = min(candidates, key=lambda c: (sum(abs(a-b) for a, b in zip(c, previous)), c))
        voicings.append(voice)
        previous = voice

    def lane(label, target, parameter, points):
        # Last write wins only for deliberately shared section/beat boundaries.
        ordered = sorted(dict(points).items())
        project.automation.append(AutomationLane("production-"+label, target, parameter,
            [AutomationPoint(f"production-{label}-{i}", tick, value, "linear")
             for i, (tick, value) in enumerate(ordered)]))

    def effect(role, label, plugin, **params):
        return Effect(f"effect-{role}-{label}", "soundcraft:"+plugin, None,
                      {"effect.bypass": 0, **{"soundcraft."+k: v for k, v in params.items()}})

    def space(role, wet, decay):
        fx = effect(role, "reverb", "plate_reverb", decay_ms=decay, pre_delay=24,
                    damping=6500, low_cut=350, width=1)
        fx.parameters["effect.wet"] = wet
        return fx

    # A separate pad is derived only when the requested harmony role exists.
    harmony = next(t for t in project.tracks if t.id == "track-harmony")
    pad = Track("track-pad", "Breathing seventh pad", "midi", deepcopy(harmony.instrument),
                deepcopy(harmony.controls), [], [], [], True)
    pad.instrument.id = "instrument-pad"
    project.tracks.append(pad)
    # Calibrated from isolated native renders, not from nominal MIDI velocities:
    # this host's drum kick is much hotter than its hats and polyphonic synth.
    base_gains = {"kick": -7, "snare": -6, "hats": -2, "bass": -6,
                  "harmony": 0, "arp": 0, "lead": 2, "pad": 0}
    motif = rng.choice(((0, 2, 4, 6), (4, 2, 6, 4), (2, 4, 6, 2)))
    for track in project.tracks:
        role = track.id.removeprefix("track-")
        drum = role in ("kick", "snare", "hats")
        track.clips = []
        track.name = {"kick": "Rounded house kick", "snare": "Clap and ghost fills", "hats": "Swung hats",
                      "bass": "Envelope bass", "harmony": "Seventh stabs", "arp": "Answer pluck",
                      "lead": "Call motif", "pad": "Breathing seventh pad"}[role]
        for si, section in enumerate(project.sections):
            notes = []

            def add(tick, duration, note, velocity, swing=False):
                if swing and (tick // (PPQ//4)) % 2:
                    tick += 30  # 53.1% sixteenth swing; kick remains on grid.
                if tick >= section.length:
                    return
                notes.append(Note(f"refined-{role}-{si}-{len(notes):04d}", tick,
                                  min(duration, section.length-tick), note,
                                  max(1, min(120, velocity+rng.randint(-3, 3))), 9 if drum else 0))

            for local in range(width):
                bar = si*width+local
                base = local*BAR
                build = si == 2 and local >= width//2
                full = si in (1, 3)
                last = local == width-1
                root, chord = roots[bar], voicings[bar]
                if role == "kick" and (full or (si == 0 and local >= width//2)):
                    for beat in range(4 if not last or si == 1 else 3):
                        add(base+beat*PPQ, 120, 36, 111 if beat == 0 else 103)
                elif role == "snare":
                    if full:
                        for beat in (1, 3):
                            add(base+beat*PPQ+9, 120, 39, 92)
                        if bar % 2:
                            add(base+11*PPQ//4, 90, 38, 35, True)
                    if (last and si in (0, 1)) or build:
                        spacing = PPQ//4 if last and si == 2 else PPQ//2
                        for tick in range(3*PPQ, BAR-60, spacing):
                            add(base+tick, 80, 38, 38+int(35*(tick-3*PPQ)/PPQ), True)
                elif role == "hats" and si != 2:
                    for beat in range(4):
                        add(base+beat*PPQ+PPQ//2+12, 80, 46 if full and beat % 2 else 42, 64 if beat % 2 else 53)
                        if full and spec.energy != "low":
                            add(base+beat*PPQ+PPQ//4, 65, 42, 33, True)
                    if last and full:
                        for step in (15,):
                            add(base+step*PPQ//4, 65, 42, 39, True)
                elif role == "bass" and full:
                    bass = pitch(root, 3)
                    if bass > 40+spec.tonic:
                        bass -= 12
                    pattern = ((2, 2, 0), (6, 1, 0), (9, 1, 4), (10, 2, 0), (14, 1, 7)) if bar % 2 else ((2, 2, 0), (6, 2, 0), (10, 2, 0), (14, 1, 0))
                    for step, length, degree in pattern:
                        n = bass if degree == 0 else bass + pitch(root+degree, 3)-pitch(root, 3)
                        add(base+step*PPQ//4+12, length*PPQ//4-55, n, 90 if step in (2, 10) else 76, True)
                elif role == "harmony":
                    steps = (2, 7, 10) if full and bar % 2 == 0 else (2, 10) if full else (0,)
                    for step in steps:
                        for voice, note in enumerate(chord):
                            add(base+step*PPQ//4+voice*5, 300 if full else PPQ*2, note, 59 if full else 48, True)
                elif role == "pad" and (si in (0, 2) or (si == 3 and local >= width//2)):
                    for note in chord:
                        add(base+24, BAR-120, note, 45)
                elif role == "lead" and full:
                    # Calls leave the second bar largely open for the answering pluck.
                    events = ((0, motif[0], 600), (3, motif[1], 280), (6, motif[2], 720)) if not bar % 2 else ((12, motif[3], 600),)
                    if si == 3 and last:
                        events = ((0, 4, 420), (4, 2, 420), (8, 0, PPQ))
                    for step, degree, duration in events:
                        add(base+step*PPQ//4, duration, pitch(root+degree, 6), 76, True)
                elif role == "arp" and (full or build):
                    steps = (1, 5, 9, 13) if bar % 2 else (9, 13)
                    if build:
                        steps = (0, 4, 8, 10, 12, 14)
                    for i, step in enumerate(steps):
                        add(base+step*PPQ//4, 160, chord[(i+(1 if si == 3 else 0)) % 4]+12, 62 if bar % 2 else 48, True)
            if notes:
                track.clips.append(Clip(f"refined-clip-{role}-{si}", track.name+" / "+section.name,
                                        "midi", section.start, section.length, notes, None))
        gain = base_gains[role]
        track.controls = {"mixer.gain_db": gain, "mixer.pan": {"hats": .18, "harmony": -.22,
                          "arp": .3, "lead": -.08}.get(role, 0), "mixer.mute": 0}
        inst = track.instrument
        if drum:
            inst.parameters = {"soundcraft.level": -6, "soundcraft.kick_decay": 240,
                               "soundcraft.hat_decay": 48, "soundcraft.open_hat_decay": 160,
                               "soundcraft.snare_decay": 135, "soundcraft.snare_snappy": .72}
        else:
            cutoff = {"bass": 280, "harmony": 1900, "arp": 2600, "lead": 3400, "pad": 1100}[role]
            if spec.palette == "dark":
                cutoff *= .7
            inst.parameters = {"synth.cutoff_hz": cutoff, "synth.resonance": .12 if role == "bass" else .18,
                "soundcraft.osc1_wave": 2/3 if role == "bass" else 1 if role == "pad" else 0,
                "soundcraft.osc2_wave": 0 if role in ("bass", "pad") else 1/3,
                "soundcraft.osc_mix": .18 if role == "bass" else .32,
                "soundcraft.filter_env_amount": .2 if role == "bass" else .42 if role != "pad" else .1,
                "soundcraft.amp_attack": 260 if role == "pad" else 3,
                "soundcraft.amp_decay": 150 if role == "bass" else 210,
                "soundcraft.amp_sustain": .5 if role == "bass" else .55 if role == "pad" else .12,
                "soundcraft.amp_release": 650 if role == "pad" else 65 if role == "bass" else 140,
                "soundcraft.filter_attack": 350 if role == "pad" else 1.5,
                "soundcraft.filter_decay": 180 if role == "bass" else 260,
                "soundcraft.filter_sustain": .25 if role == "pad" else .05,
                "soundcraft.filter_release": 450 if role == "pad" else 130,
                "soundcraft.velocity": .78, "soundcraft.level": -8 if role == "bass" else -6}
        eq = effect(role, "eq", "eq_7band", hpf_on=1,
                    hpf_freq={"kick": 28, "bass": 30, "snare": 190, "hats": 650}.get(role, 230),
                    low_mid_freq=320, low_mid_gain=-2.5 if role != "bass" else -1.5,
                    high_shelf_gain=-2 if role in ("hats", "lead") else 0, lpf_on=1, lpf_freq=18000)
        track.effects = [eq]
        if role in ("kick", "bass", "harmony"):
            sat = effect(role, "saturation", "saturator", drive=3, output=-2, tone=6500)
            sat.parameters["effect.wet"] = .22
            track.effects.append(sat)
        if role in ("kick", "snare", "bass"):
            track.effects.append(effect(role, "compression", "compressor", threshold=-22 if role != "bass" else -25,
                                        attack=18 if role == "kick" else 8, release=95, makeup=1))
        if role in ("harmony", "pad"):
            chorus = effect(role, "chorus", "chorus", rate=.32, depth=.22, spread=1)
            chorus.parameters["effect.wet"] = .18 if role == "harmony" else .3
            track.effects.append(chorus)
        if role in ("arp", "lead") and spec.space != "dry":
            delay = effect(role, "delay", "mod_delay", time=60000/spec.bpm*.75, feedback=.24,
                           mod_rate=.23, mod_depth=.035, lpf=5800)
            delay.parameters["effect.wet"] = .16
            track.effects.append(delay)
            lane(role+"-throw", delay.id, "effect.wet", [(0, .1), (width*BAR, .12),
                (2*width*BAR-PPQ, .34), (2*width*BAR, .2), (3*width*BAR-PPQ, .32),
                (3*width*BAR, .12), (project.length-PPQ, .28), (project.length, .2)])
        if role in ("harmony", "pad", "arp", "lead", "snare") and spec.space != "dry":
            track.effects.append(space(role, .2 if role == "pad" else .055 if role == "snare" else .1,
                                       1900 if role == "pad" else 1050))
        if not drum:
            lane(role+"-filter", eq.id, "soundcraft.lpf_freq", [(0, 1600), (width*BAR-PPQ, 4200),
                (width*BAR, 12500), (2*width*BAR-PPQ, 9000), (2*width*BAR, 1200),
                (3*width*BAR-PPQ, 6000), (3*width*BAR-120, 16000),
                (3*width*BAR, 13500), (project.length-PPQ, 9500), (project.length, 2000)])
        if role in ("bass", "harmony", "pad"):
            points = []
            for bar in range(spec.bars):
                for beat in range(4):
                    tick = bar*BAR+beat*PPQ
                    duck = 0 if width*2 <= bar < width*3 else 1
                    points += [(tick, gain-5*duck), (tick+100, gain-4*duck), (tick+420, gain), (tick+PPQ-1, gain)]
            points += [(project.length-PPQ//2, gain), (project.length, gain-18)]
            lane(role+"-duck", track.id, "mixer.gain_db", points)
        if role == "arp":
            lane("arp-pan", track.id, "mixer.pan", [(0, -.3), (width*BAR, .3),
                (2*width*BAR, -.4), (3*width*BAR, .4), (project.length, -.2)])
    project.metadata.update(composer=REFINED_COMPOSER, production="refined",
                            production_notes="Diatonic seventh voicings, call/response, sixteenth swing, envelopes, insert FX, programmed ducking; no exposed synth LFO or wavetable.")
    validate(project)
    return project
