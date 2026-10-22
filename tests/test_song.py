import json
import unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from kuang.composer import SCALES, compose
from kuang.schema import BAR, ValidationError, decode, dumps
from kuang.song import SongSpec, rules_plan, spec_schema, validate_spec
from kuang.soundcraft import SoundCraftAdapter

PROMPTS = (
    "dark atmospheric trap, 140 bpm, A minor, heavy 808, spacious pads, haunting lead",
    "uplifting house, 126 bpm, C major, driving bass, bright chord stabs",
    "ambient cinematic, 72 bpm, D minor, gentle spacious pads",
)


def content(project):
    return [(t.id, [(c.start + n.start, n.duration, n.pitch, n.channel) for c in t.clips for n in c.notes]) for t in project.tracks]


class SongTests(unittest.TestCase):
    def test_three_styles_have_distinct_notes_rhythms_harmony_and_instrumentation(self):
        specs = [rules_plan(p)[0] for p in PROMPTS]
        projects = [compose(s) for s in specs]
        self.assertEqual([p.tempo_bpm for p in projects], [140, 126, 72])
        self.assertEqual([len(p.tracks) for p in projects], [6, 7, 4])
        self.assertEqual(len({json.dumps(content(p)) for p in projects}), 3)
        self.assertEqual(len({tuple(s.progression) for s in specs}), 3)
        self.assertEqual(len({json.dumps([asdict(t.instrument) for t in p.tracks], sort_keys=True) for p in projects}), 3)
        trap, house = projects[:2]
        snare = lambda p: next(t for t in p.tracks if t.id == "track-snare").clips[0].notes
        self.assertIn(1920, [n.start % BAR for n in snare(trap)])
        self.assertEqual({n.start % BAR for n in snare(house)}, {960, 2880})
        self.assertEqual({n.start % BAR for c in house.tracks[0].clips for n in c.notes}, {0, 960, 1920, 2880})

    def test_seed_reproduces_bytes_and_changes_content_beyond_velocity(self):
        for prompt in PROMPTS:
            a = compose(rules_plan(prompt, 7)[0])
            self.assertEqual(dumps(a), dumps(compose(rules_plan(prompt, 7)[0])))
            self.assertNotEqual(content(a), content(compose(rules_plan(prompt, 8)[0])))

    def test_all_pitched_notes_are_in_key_and_harmony_and_bass_follow_progression(self):
        for prompt in PROMPTS:
            spec = rules_plan(prompt)[0]
            p = compose(spec)
            allowed = {(spec.tonic + n) % 12 for n in SCALES[spec.mode]}
            for track in p.tracks:
                for clip in track.clips:
                    for n in clip.notes:
                        if n.channel == 9:
                            continue
                        self.assertIn(n.pitch % 12, allowed)
                        bar = (clip.start + n.start) // BAR
                        degree = spec.progression[(bar // (2 if spec.genre == "ambient" else 1)) % 4]
                        if track.id == "track-bass":
                            self.assertEqual(n.pitch % 12, (spec.tonic + SCALES[spec.mode][degree]) % 12)
                        if track.id == "track-harmony":
                            chord = {(spec.tonic + SCALES[spec.mode][(degree+d) % 7]) % 12 for d in (0, 2, 4)}
                            self.assertIn(n.pitch % 12, chord)

    def test_transposition_changes_pitch_classes_and_preserves_drums(self):
        a = compose(rules_plan("trap A minor")[0])
        b = compose(rules_plan("trap B minor")[0])
        for ta, tb in zip(a.tracks, b.tracks):
            for ca, cb in zip(ta.clips, tb.clips):
                for na, nb in zip(ca.notes, cb.notes):
                    self.assertEqual((na.start, na.duration, na.velocity, na.id), (nb.start, nb.duration, nb.velocity, nb.id))
                    self.assertEqual(nb.pitch % 12, (na.pitch + (0 if na.channel == 9 else 2)) % 12)

    def test_options_affect_music_fx_and_sections(self):
        a = compose(rules_plan("house high energy spacious C major")[0])
        b = compose(rules_plan("house low energy dry C major no drums no lead")[0])
        self.assertNotEqual(content(a), content(b))
        self.assertTrue(any(t.effects[-1].plugin_ref == "soundcraft:room_reverb" for t in a.tracks if t.effects))
        self.assertFalse(any(e.plugin_ref == "soundcraft:room_reverb" for t in b.tracks for e in t.effects))
        self.assertEqual({t.id for t in b.tracks}, {"track-bass", "track-harmony", "track-arp"})
        for bars in (8, 16, 32):
            p = compose(rules_plan(f"ambient {bars} bars")[0])
            self.assertEqual(p.sections[-1].start+p.sections[-1].length, bars*BAR)
            self.assertEqual(p.sections[0].name, "Arrival")

    def test_parser_accidentals_progression_and_explicit_limits(self):
        s, messages = rules_plan("house Bb major 128 bpm 8 bars I-V-vi-IV with vocals in 7/8")
        self.assertEqual((s.tonic, s.mode, s.bpm, s.bars, s.progression), (10, "major", 128, 8, [0, 4, 5, 3]))
        self.assertTrue(any("vocals" in m for m in messages))
        self.assertTrue(any("4/4" in m for m in messages))
        self.assertEqual(rules_plan("ambient F# minor")[0].tonic, 6)
        self.assertTrue(any("unspecified/unsupported" in m for m in rules_plan("jazz quartet")[1]))

    def test_ambient_energy_changes_note_density_beyond_metadata_and_velocity(self):
        projects = [compose(rules_plan(f"ambient {energy} energy")[0]) for energy in ("low", "medium", "high")]
        counts = [sum(len(c.notes) for t in p.tracks for c in t.clips) for p in projects]
        self.assertLess(counts[0], counts[1])
        self.assertLess(counts[1], counts[2])
        self.assertEqual(len({json.dumps(content(p)) for p in projects}), 3)

    def test_strict_schema_corruptions_ranges_and_injection(self):
        original = asdict(rules_plan(PROMPTS[0])[0])
        for key, value in (("genre", "jazz"), ("bpm", 201), ("bpm", True), ("tonic", -1),
                           ("seed", -1), ("seed", 2**32), ("bars", 9), ("progression", [0, 7, 3, 4]),
                           ("progression", [0]), ("instruments", ["bass", "harmony", "harmony"]),
                           ("instruments", ["bass", "shell"]), ("instruments", ["lead"]),
                           ("automation", "exec"), ("space", "../../etc")):
            with self.subTest(key=key, value=value):
                bad = deepcopy(original); bad[key] = value
                with self.assertRaises(ValidationError):
                    validate_spec(decode(SongSpec, bad))
        for bad in ({**original, "command": "touch /tmp/injected"}, {k:v for k,v in original.items() if k != "seed"}):
            with self.assertRaises(ValidationError): decode(SongSpec, bad)
        for prompt in ("", "x"*4001, "trap\x00", "trap 220 bpm", "trap 12 bars", "trap 120.5 bpm", "trap 120 bpm 130 bpm", "trap A minor C major"):
            with self.subTest(prompt=prompt[:30]):
                with self.assertRaises(ValidationError): rules_plan(prompt)

    def test_every_profile_matches_recorded_host_capabilities(self):
        adapter = SoundCraftAdapter("/bin/true")
        adapter._discovery = json.loads((Path(__file__).parent/"fixtures/soundcraft-contract.json").read_text())
        for prompt in PROMPTS:
            for bars in (8, 16, 32):
                spec = rules_plan(prompt)[0]; spec.bars = bars
                self.assertEqual(adapter.capabilities(compose(spec))["unsupported"], [])
        schema = spec_schema()
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["properties"]), set(asdict(rules_plan(PROMPTS[0])[0])))
