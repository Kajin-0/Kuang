"""One authored 16-bar house pocket, expanded into ordinary editable objects.

An experiment, not a club-quality claim. Keeps previous composers byte-stable.
No assets, inference, external instrument or new schema/transaction semantics.
"""

import random
from copy import deepcopy

from .composer import compose
from .production import refine_house
from .schema import (BAR, PPQ, AutomationLane, AutomationPoint, Clip, Effect,
                     Note, validate)
from .song import rules_plan

GROOVE_VERSION = "house-pocket-experiment-v1"


def house_loop(seed=29):
    spec, _ = rules_plan("house, 126 bpm, C minor, 16 bars, high energy", seed)
    spec.progression = [0,0,0,3]  # Authored four-bar Cm/Cm/Cm/Fm cell, retained in provenance.
    p = refine_house(spec, compose(spec))
    p.name = "Kuang house pocket experiment"
    # Reuse the existing device registry; construct a new project rather than
    # revising any prior artifact or reinterpreting existing note identities.
    p.tracks = [t for t in p.tracks if t.id != "track-pad"]
    perc = deepcopy(next(t for t in p.tracks if t.id == "track-hats"))
    perc.id, perc.instrument.id = "track-percussion", "instrument-percussion"
    p.tracks.append(perc)
    p.automation = []
    for s, name in zip(p.sections, ("Pocket", "Answer", "Lift", "Return")):
        s.name = name
    rng = random.Random(spec.seed)
    gains = {"kick": -3, "snare": 3, "hats": 4, "bass": -6,
             "harmony": 7, "lead": 7, "arp": 4, "percussion": -1}

    def lane(label, target, parameter, values):
        p.automation.append(AutomationLane("pocket-"+label, target, parameter,
            [AutomationPoint(f"pocket-{label}-{i}", tick, value, "linear")
             for i, (tick, value) in enumerate(sorted(dict(values).items()))]))

    def fx(role, label, plugin, wet=None, **values):
        params = {"effect.bypass": 0, **{"soundcraft."+k:v for k,v in values.items()}}
        if wet is not None:
            params["effect.wet"] = wet
        return Effect(f"effect-{role}-{label}", "soundcraft:"+plugin, None, params)

    for t in p.tracks:
        role = t.id.removeprefix("track-")
        drum = role in ("kick", "snare", "hats", "percussion")
        t.name = {"kick":"Pocket kick", "snare":"Late clap", "hats":"Choked offbeat hats",
                  "percussion":"Quiet shuffled ticks", "bass":"Short mono bass",
                  "harmony":"Rootless Cm9 stabs", "lead":"Three-note call", "arp":"Two-note answer"}[role]
        t.controls = {"mixer.gain_db":gains[role], "mixer.pan":{
            "hats":.28, "percussion":-.38, "harmony":-.26, "lead":.12, "arp":.36}.get(role,0), "mixer.mute":0}
        t.clips = []
        for phrase, section in enumerate(p.sections):
            notes = []

            def add(tick, duration, pitch, velocity):
                notes.append(Note(f"pocket-{role}-{phrase}-{len(notes):04d}", tick, duration, pitch,
                                  max(1,min(120,velocity+rng.randint(-2,2))), 9 if drum else 0))

            for bar in range(4):
                base = bar*BAR
                # Notes and articulations repeat as a recognizable two-bar cell.
                # Phrase variants are authored; randomization only shades velocity.
                if role == "kick":
                    for beat in range(4):
                        add(base+beat*PPQ,120,36,112 if beat in (0,2) else 109)
                elif role == "snare":
                    for beat in (1,3):
                        add(base+beat*PPQ+18,100,39,101 if beat == 1 else 96)
                    if bar in (1,3):
                        add(base+11*PPQ//4+38,80,38,40)
                    if bar == 3 and phrase in (1,3):
                        add(base+15*PPQ//4+26,70,38,52)
                elif role == "hats":
                    for beat in range(4):
                        # Closed hats after an open hat choke that voice natively.
                        add(base+beat*PPQ+PPQ//2+12,80,46 if beat in (1,3) else 42,80 if beat in (1,3) else 65)
                        if beat in (0,2) or phrase == 2:
                            add(base+beat*PPQ+3*PPQ//4+40,65,42,40)
                    if bar == 3:
                        add(base+13*PPQ//4+40,60,42,34)
                elif role == "percussion":
                    for step, vel in ((1,38),(7,53),(9,32),(15,47)):
                        if not (phrase == 0 and bar == 0 and step == 9):
                            add(base+step*PPQ//4+46,60,44,vel)
                elif role == "bass":
                    cell = [(2,300,36,101),(5,180,36,82),(10,270,36,94),(14,210,34 if bar == 2 else 36,87)]
                    if bar % 2:
                        cell.insert(2,(7,105,36,61))
                    if bar == 3:
                        cell[-1] = (14,150,31,85)
                        if phrase in (1,3):
                            cell.append((15,100,39,68))
                    for step, length, note, vel in cell:
                        # Sixteenth pickups end before the next kick, including
                        # the release. The main offbeat holds a short round body.
                        delay = 38 if step % 2 else 12
                        add(base+step*PPQ//4+delay,length,note,vel)
                elif role == "harmony":
                    chord = (51,55,58,62) if bar != 3 else (53,56,60,63)
                    for step in ((3,11) if bar in (0,2) else (3,)):
                        for voice, note in enumerate(chord):
                            add(base+step*PPQ//4+36+voice*4,175,note,70-voice*2)
                elif role == "lead" and bar in (0,2):
                    # G–Eb–F: one compact hook, not an octave-running lead.
                    for step,length,note,vel in ((0,290,67,88),(3,155,63,72),(6,310,65,83)):
                        add(base+step*PPQ//4+(30 if step%2 else 0),length,note,vel)
                    if phrase == 3 and bar == 2:
                        add(base+14*PPQ//4,180,63,66)
                elif role == "arp" and bar in (1,3):
                    for step,note,vel in ((7,70,71),(10,67,78)):
                        add(base+step*PPQ//4+(36 if step%2 else 12),210,note,vel)
            t.clips.append(Clip(f"pocket-clip-{role}-{phrase}",t.name+" / "+section.name,
                                "midi",section.start,section.length,notes,None))
        if drum:
            t.instrument.parameters = {"soundcraft.level":-6,"soundcraft.kick_decay":400,
                "soundcraft.hat_decay":55 if role != "percussion" else 26,
                "soundcraft.open_hat_decay":210,"soundcraft.snare_decay":110,"soundcraft.snare_snappy":.68}
        else:
            params = t.instrument.parameters
            params.update({"soundcraft.osc1_wave":1/3 if role in ("bass","lead") else 0,
                "soundcraft.osc2_wave":1,"soundcraft.osc_mix":0 if role == "bass" else .22,
                "synth.cutoff_hz":340 if role == "bass" else 1500 if role == "lead" else 2200,
                "synth.resonance":.1 if role == "bass" else .16,
                "soundcraft.filter_env_amount":.22 if role == "bass" else .18,
                "soundcraft.amp_attack":1.5 if role == "bass" else 8 if role == "harmony" else 5,
                "soundcraft.amp_decay":135 if role == "bass" else 145,
                "soundcraft.amp_sustain":.28 if role == "bass" else .04,
                "soundcraft.amp_release":28 if role == "bass" else 75,
                "soundcraft.filter_attack":1,"soundcraft.filter_decay":125,
                "soundcraft.filter_sustain":.03,"soundcraft.filter_release":60,
                "soundcraft.velocity":.8,"soundcraft.level":-6})
        eq = fx(role,"eq","eq_7band",hpf_on=1,
                hpf_freq={"kick":28,"bass":32,"snare":220,"hats":1200,"percussion":1800}.get(role,280),
                low_mid_freq=300,low_mid_gain=-2 if role != "bass" else -1,
                high_shelf_gain=1 if role == "hats" else 0,lpf_on=1,
                lpf_freq=14000 if drum else 1300 if role == "bass" else 9000)
        t.effects = [eq]
        if role in ("kick","bass"):
            t.effects += [fx(role,"compression","compressor",threshold=-24,
                             attack=.25 if role == "kick" else 8,release=60 if role == "kick" else 85,makeup=3 if role == "kick" else 2),
                          fx(role,"saturation","saturator",wet=.32,drive=3,output=-1.5,tone=7000)]
        if role == "harmony":
            t.effects += [fx(role,"chorus","chorus",wet=.15,rate=.38,depth=.19,spread=1)]
        if role in ("lead","arp"):
            delay = fx(role,"delay","mod_delay",wet=.13,time=60000/126*.75,feedback=.22,
                       mod_rate=.27,mod_depth=.018,lpf=4500)
            t.effects.append(delay)
            points = [(0,.13)]
            for phrase in range(4):
                tick=(phrase+1)*4*BAR
                points += [(tick-PPQ,.13),(tick-PPQ//2,.26),(tick,.13)]
            lane(role+"-throw",delay.id,"effect.wet",points)
        if role in ("harmony","snare","arp"):
            t.effects.append(fx(role,"room","room_reverb",wet=.04 if role == "snare" else .08,
                                decay_ms=550,pre_delay=12,low_cut=450,damping=6500,width=1))
        if role in ("harmony","lead","arp"):
            # Short isolated stabs had peaks above the kick despite low average
            # energy. Control those attacks locally, without flattening the mix.
            t.effects.append(fx(role,"compression","compressor",threshold=-32,attack=.2,release=80,makeup=2))
        if role in ("bass","harmony"):
            gain=gains[role]
            lane(role+"-duck",t.id,"mixer.gain_db",[(bar*BAR+beat*PPQ+offset,gain+delta)
                 for bar in range(16) for beat in range(4)
                 for offset,delta in ((0,-8 if role == "bass" else -4),(120,-6 if role == "bass" else -3),(360,0),(PPQ-1,0))]
                 +[(p.length,gain+(-8 if role == "bass" else -4))])
        if role in ("harmony","lead","arp"):
            lane(role+"-tone",eq.id,"soundcraft.lpf_freq",[(0,5200),(4*BAR,6800),
                (8*BAR,5800),(11*BAR,7800),(12*BAR,6500),(15*BAR,5800),(p.length,5200)])
    p.metadata.update(composer=GROOVE_VERSION,production="groove-experiment",ai_plan="false",
        production_notes="One C-minor house pocket, 126 BPM. Continuous kick, short mono bass, G-Eb-F call, Bb-G answer, controlled four-bar variants. Built-ins only; listening quality unknown.")
    validate(p)
    return p
