"""Opt-in sonic layers over the fingerprinted Phase 5 pocket, schema 0.1.

No rewritten groove, new DSP, assets or synth-LFO claim. Envelopes are static
per instrument; movement is native insert modulation and continuous EQ lanes.
"""

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict

from .groove import house_loop
from .schema import (BAR, PPQ, AutomationLane, AutomationPoint, Clip, Effect,
                     Note, ParameterSpec, Track, ValidationError, state_hash, validate)

DEPTH_VERSION = "house-depth-experiment-v1"
SOURCE_HASH = "3fe734a568b0d715890a382159fcacea58a1c770b8b50d0dda8bbeb3e6c0d311"
PAD_IDS = ("track-depth-pad", "track-depth-air")


def note_fingerprints(project):
    """Include clip identity/placement and every note field, in original order."""
    return {t.id: hashlib.sha256(json.dumps([asdict(c) for c in t.clips],
                 sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            for t in project.tracks}


def depth_house(source=None):
    """Extend only the exact released seed-29 Phase 5 project; reject drift."""
    source = house_loop() if source is None else source
    validate(source)
    if state_hash(source) != SOURCE_HASH:
        raise ValidationError("depth experiment requires the unchanged Phase 5 seed-29 source")
    p = deepcopy(source)
    p.name = "Kuang house pocket / depth experiment"
    p.parameters.append(ParameterSpec("soundcraft.center", "Hz", 100, 4000, 800, ["effect"]))

    def fx(role, label, plugin, wet=None, **values):
        params = {"effect.bypass": 0, **{"soundcraft."+k: v for k, v in values.items()}}
        if wet is not None:
            params["effect.wet"] = wet
        return Effect(f"effect-depth-{role}-{label}", "soundcraft:"+plugin, None, params)

    def lane(label, owner, parameter, points):
        p.automation.append(AutomationLane("depth-"+label, owner, parameter,
            [AutomationPoint(f"depth-{label}-{i}", tick, value, "linear")
             for i, (tick, value) in enumerate(sorted(dict(points).items()))]))

    # Keep every original insert and lane. Two deliberate reverb changes give
    # the unchanged stabs and call some audible space without washing the bass.
    harmony = next(t for t in p.tracks if t.id == "track-harmony")
    room = next(e for e in harmony.effects if e.plugin_ref == "soundcraft:room_reverb")
    room.parameters.update({"effect.wet": .22, "soundcraft.decay_ms": 1250,
                            "soundcraft.pre_delay": 22})
    lead = next(t for t in p.tracks if t.id == "track-lead")
    lead.effects.append(fx("lead", "plate", "plate_reverb", .20,
        decay_ms=1450, pre_delay=28, damping=7200, low_cut=500, width=1))

    for role, pan, gain in (("pad", -.58, 4), ("air", .62, 2)):
        air = role == "air"
        inst = deepcopy(harmony.instrument)
        inst.id = "instrument-depth-"+role
        inst.parameters.update({
            "soundcraft.osc1_wave": 0 if air else 1,
            "soundcraft.osc2_wave": 1 if air else 0,
            "soundcraft.osc_mix": .24 if air else .34,
            "synth.cutoff_hz": 8500 if air else 3400,
            "synth.resonance": .12 if air else .16,
            "soundcraft.filter_env_amount": .16 if air else .24,
            "soundcraft.amp_attack": 260 if air else 650,
            "soundcraft.amp_decay": 600 if air else 950,
            "soundcraft.amp_sustain": .38 if air else .70,
            "soundcraft.amp_release": 650 if air else 1000,
            "soundcraft.filter_attack": 450 if air else 1100,
            "soundcraft.filter_decay": 1200 if air else 1600,
            "soundcraft.filter_sustain": .42 if air else .55,
            "soundcraft.filter_release": 650 if air else 1000,
            "soundcraft.velocity": .45, "soundcraft.level": -6})
        t = Track("track-depth-"+role, "Air ninth texture" if air else "Slow rootless ninth pad",
                  "midi", inst, {"mixer.gain_db": gain, "mixer.pan": pan, "mixer.mute": 0},
                  [], [], [], True)
        for phrase, section in enumerate(p.sections):
            notes = []
            if air:
                # Sparse upper answers, never another fast hook. D/G/Bb over
                # Cm9 and Eb/G/C over Fm9; the ninth is a deliberate colour.
                cells = [(BAR+PPQ*3//2, PPQ*2, (74,79,82)),
                         (3*BAR+PPQ//2, PPQ*5//2, (75,79,84))]
                if phrase == 0:
                    cells = cells[1:]
                voices = 3 if phrase in (2,3) else 2
            else:
                # Rootless Cm9 -> Fm9. No pad fundamental competes with C2/F2.
                cm = (63,70,74) if phrase in (0,2) else (63,67,70,74)
                fm = (63,68,79) if phrase in (0,2) else (63,67,68,72)
                cells = [(PPQ//2, 7*PPQ, cm), (2*BAR+PPQ//4, 3*PPQ, cm),
                         (3*BAR, 3*PPQ, fm)]
                voices = 4
            for start, duration, chord in cells:
                for voice, pitch in enumerate(chord[:voices]):
                    notes.append(Note(f"depth-{role}-{phrase}-{len(notes):03d}", start,
                                      duration, pitch, (68 if air else 76)-2*voice+phrase, 0))
            t.clips.append(Clip(f"depth-clip-{role}-{phrase}", t.name+" / "+section.name,
                                "midi", section.start, section.length, notes, None))
        eq = fx(role, "eq", "eq_7band", hpf_on=1, hpf_freq=1000 if air else 400,
                low_mid_freq=450, low_mid_gain=-2, lpf_on=1, lpf_freq=14000 if air else 6500)
        chorus = fx(role, "chorus", "chorus", .44 if air else .40,
                    rate=.63 if air else .32, depth=.58 if air else .65, spread=1)
        t.effects = [eq, chorus]
        if not air:
            t.effects.append(fx(role, "phaser", "phaser", .38, rate=.126,
                                depth=.72, center=950, feedback=.28))
        t.effects.append(fx(role, "plate", "plate_reverb", .24 if air else .28,
            decay_ms=1300 if air else 1800, pre_delay=32 if air else 38,
            damping=9000 if air else 6500, low_cut=650 if air else 500, width=1))
        p.tracks.append(t)
        points = []
        for phrase in range(4):
            base = phrase*4*BAR
            low, high = (2400, 14000) if air else (1200, 6500)
            # Repeated opening/closing gestures with phrase-dependent height;
            # these automate the insert LPF, not the synth oscillator/filter.
            peak = high*(.75 if phrase == 0 else .9 if phrase == 2 else 1)
            points += [(base, low), (base+BAR+2*PPQ, peak),
                       (base+2*BAR, low*1.5), (base+3*BAR+2*PPQ, peak*.8),
                       (base+4*BAR, low)]
        lane(role+"-filter", eq.id, "soundcraft.lpf_freq", points)
        # Gentle beat breathing leaves the original bass duck envelope intact.
        lane(role+"-breath", t.id, "mixer.gain_db", [(beat*PPQ+offset, gain+delta)
             for beat in range(64) for offset, delta in ((0,-3),(PPQ//3,-1),(PPQ*2//3,0),(PPQ-1,0))]
             +[(p.length, gain-3)])
    p.metadata.update(production="depth-experiment", depth_version=DEPTH_VERSION,
        depth_source_hash=SOURCE_HASH, depth_note_fingerprints=json.dumps(note_fingerprints(source),sort_keys=True),
        depth_notes="Exact Phase 5 MIDI retained. Added rootless ninth pad/air with distinct static ADSR; native chorus/phaser and automated insert LPF. No synth LFO/ADSR automation or listening-quality claim.")
    validate(p)
    assert all(note_fingerprints(p)[key] == value for key,value in note_fingerprints(source).items())
    return p
