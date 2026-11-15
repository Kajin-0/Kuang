"""Tests for optional triad vs seventh voicings in the groove-first engine."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kuang.create import create
from kuang.house_harmony import apply_harmony, select_harmony
from kuang.house_template import template
from kuang.schema import BAR, ValidationError, dumps, load, validate
from kuang.song import rules_plan


def events(project, role):
    track = next(t for t in project.tracks if t.id == "track-" + role)
    return [(c.start + n.start, n.duration, n.pitch, n.velocity, n.channel)
            for c in track.clips for n in c.notes]


class HarmonyProfileTests(unittest.TestCase):
    def test_selection_and_modes_fail_closed(self):
        self.assertEqual(select_harmony("minimal house", "minimal"), "simple")
        self.assertEqual(select_harmony("deep house", "deep"), "extended")
        self.assertEqual(select_harmony("house with simple triads", "deep"), "simple")
        self.assertEqual(select_harmony("house with no sevenths", "deep"), "simple")
        self.assertEqual(select_harmony("house with seventh chords", "straight"), "extended")
        self.assertEqual(select_harmony("house", "straight", "extended"), "extended")
        for phrase in ("A Phrygian house", "D Dorian house",
                       "G Mixolydian house", "modal house", "house with borrowed chords"):
            with self.subTest(phrase=phrase):
                with self.assertRaisesRegex(ValidationError, "does not support"):
                    select_harmony(phrase, "deep")
        with self.assertRaisesRegex(ValidationError, "conflicting"):
            select_harmony("house with simple chords and sevenths", "straight")
        with self.assertRaisesRegex(ValidationError, "conflicts"):
            select_harmony("house with simple triads", "straight", "extended")
        with self.assertRaises(ValidationError):
            select_harmony("house", "deep", "modal")

    def test_simple_and_extended_share_identical_kick_bass_percussion(self):
        for key in ("C major", "D minor", "F# major"):
            for profile in ("straight", "deep", "jackin", "minimal"):
                with self.subTest(key=key, profile=profile):
                    spec, _ = rules_plan(f"house in {key}, 16 bars", 17)
                    simple, sr = template(spec, profile=profile, harmony_profile="simple")
                    ext, er = template(spec, profile=profile, harmony_profile="extended")
                    validate(simple); validate(ext)
                    self.assertEqual(sr["groove_fingerprint_sha256"], er["groove_fingerprint_sha256"])
                    self.assertEqual(sr["full_groove_onsets"], er["full_groove_onsets"])
                    for role in ("kick", "snare", "hats", "percussion", "bass"):
                        self.assertEqual(events(simple, role), events(ext, role))
                    self.assertEqual(sr["harmony"]["profile"], "simple")
                    self.assertEqual(er["harmony"]["profile"], "extended")
                    self.assertGreater(sr["harmony"]["seventh_voices_removed"], 0)
                    self.assertEqual(er["harmony"]["seventh_voices_removed"], 0)
                    self.assertTrue(all(sr["harmony"]["technical_gates"].values()))
                    self.assertTrue(all(er["harmony"]["technical_gates"].values()))
                    self.assertEqual(sr["harmony"]["perceptual_quality"], "NEEDS_LISTENING")
                    a = events(simple, "harmony")
                    b = events(ext, "harmony")
                    self.assertLess(len(a), len(b))
                    # Filtering a seventh must not invent new onset, pitch or velocities.
                    self.assertTrue(set(a) < set(b))

    def test_simple_retains_exact_chord_rhythm_and_triad_pitch_classes(self):
        spec, _ = rules_plan("house in C minor, 32 bars", 8)
        p, evidence = template(spec, profile="deep", harmony_profile="simple")
        self.assertEqual(p.metadata["harmony_profile"], "simple")
        self.assertEqual(len(evidence["harmony"]["bar_summary"]), 32)
        for block in evidence["harmony"]["bar_summary"]:
            self.assertEqual(set(block["chord_pitch_classes"]),
                             set(block["expected_pitch_classes"]))
            self.assertTrue(block["bass_functional"])

    def test_pads_follow_chord_profile_and_are_optional(self):
        spec, _ = rules_plan("deep house in D minor, 32 bars", 17)
        simple, _ = template(spec, profile="deep", harmony_profile="simple")
        extended, _ = template(spec, profile="deep", harmony_profile="extended")
        self.assertLess(len(events(simple, "pad")), len(events(extended, "pad")))
        without, evidence = template(spec, profile="deep", include_pad=False,
                                     harmony_profile="simple")
        self.assertNotIn("track-pad", {t.id for t in without.tracks})
        self.assertEqual(evidence["harmony"]["profile"], "simple")

    def test_project_is_deterministic_and_source_spec_not_mutated(self):
        spec, _ = rules_plan("house in G minor, 16 bars", 21)
        snapshot = json.dumps(spec.__dict__, sort_keys=True)
        a, ae = template(spec, profile="jackin", harmony_profile="simple")
        b, be = template(spec, profile="jackin", harmony_profile="simple")
        self.assertEqual(dumps(a), dumps(b))
        self.assertEqual(ae, be)
        self.assertEqual(json.dumps(spec.__dict__, sort_keys=True), snapshot)

    def test_validation_rejects_corrupted_bass_function(self):
        spec, _ = rules_plan("house in C major, 16 bars", 7)
        p, _ = template(spec, profile="straight")
        bass = next(t for t in p.tracks if t.id == "track-bass")
        bass.clips[0].notes[0].pitch += 1
        with self.assertRaisesRegex(ValidationError, "bass note function"):
            apply_harmony(p, spec, "extended")


class HarmonyCreateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_harmony_profile_option_and_reports(self):
        with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
            r = create("deep house in C minor, no lead, 16 bars, simple triads",
                       self.root / "simple", production="groove-template", seed=11)
            p = load(self.root / "simple/project.kuang.json")
        self.assertEqual(p.metadata["harmony_profile"], "simple")
        self.assertEqual(r["groove"]["harmony"]["profile"], "simple")
        receipt = json.loads((self.root / "simple/groove-evidence.json").read_text())
        self.assertEqual(receipt["harmony"]["profile"], "simple")
        self.assertFalse(r["validation"]["audio_verified"])

    def test_modal_prompt_rejected_and_does_not_publish(self):
        with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
            for i, phrase in enumerate(("house in A Phrygian", "G Dorian deep house")):
                with self.subTest(phrase=phrase):
                    output = self.root / f"unsupported-{i}"
                    with self.assertRaisesRegex(ValidationError, "does not support"):
                        create(phrase, output, production="groove-template")
                    self.assertFalse(output.exists())

    def test_mismatch_profile_rejected_and_legacy_stable(self):
        with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
            with self.assertRaisesRegex(ValidationError, "only valid"):
                create("house", self.root / "a", production="refined",
                       harmony_profile="simple")
            with self.assertRaisesRegex(ValidationError, "conflicts"):
                create("house with seventh chords", self.root / "b",
                       production="groove-template", harmony_profile="simple")
            baseline = create("house in C major, 8 bars", self.root / "sketch")
        self.assertEqual(baseline["engine"]["production"], "sketch")
        self.assertNotIn("harmony", baseline["groove"] if baseline["groove"] else {})
