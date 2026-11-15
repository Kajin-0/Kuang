"""Regression gates for opt-in musical-plan enrichment of the existing house engine."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kuang.create import create
from kuang.house_musical_plan import FAMILIES, VERSION, enrich_house_spec
from kuang.schema import ValidationError, load
from kuang.song import rules_plan, validate_spec


class HouseMusicalPlanTests(unittest.TestCase):
    def test_all_house_styles_modes_reproduce_and_vary_without_mutating_spec(self):
        keys = {"major": "C major", "minor": "D minor"}
        for profile in ("deep", "straight", "jackin", "minimal"):
            for mode, key in keys.items():
                with self.subTest(profile=profile, mode=mode):
                    seen = set()
                    for seed in range(1, 17):
                        spec, _ = rules_plan(f"{profile} house in {key}, 16 bars", seed)
                        original = tuple(spec.progression)
                        p, evidence = enrich_house_spec(spec, f"{profile} house in {key}, 16 bars", profile)
                        again, second = enrich_house_spec(spec, f"{profile} house in {key}, 16 bars", profile)
                        self.assertEqual(p.progression, again.progression)
                        self.assertEqual(evidence, second)
                        self.assertEqual(tuple(spec.progression), original)
                        self.assertEqual((p.tonic, p.mode, p.bpm, p.bars, p.seed),
                                         (spec.tonic, spec.mode, spec.bpm, spec.bars, spec.seed))
                        self.assertEqual(p.instruments, spec.instruments)
                        self.assertEqual(evidence["version"], VERSION)
                        self.assertEqual(evidence["perceptual_quality"], "NEEDS_LISTENING")
                        self.assertIn((evidence["family"], tuple(p.progression)), FAMILIES[(profile, mode)])
                        validate_spec(p)
                        seen.add(tuple(p.progression))
                    self.assertGreaterEqual(len(seen), 3)

    def test_explicit_roman_progression_remains_authoritative(self):
        for profile, prompt in (
            ("straight", "straight house in C major, 16 bars I-V-vi-IV"),
            ("deep", "deep house in D minor, 16 bars i-VI-III-VII"),
            ("minimal", "minimal house in F major, 16 bars I-IV-I-V"),
        ):
            with self.subTest(profile=profile):
                spec, _ = rules_plan(prompt, 41)
                planned, receipt = enrich_house_spec(spec, prompt, profile)
                self.assertEqual(planned.progression, spec.progression)
                self.assertEqual(receipt["selection"], "explicit_roman")
                self.assertEqual(receipt["family"], "user_explicit")

    def test_rejects_non_house_or_unsupported_profile(self):
        s, _ = rules_plan("ambient in D minor 16 bars", 13)
        with self.assertRaises(ValidationError):
            enrich_house_spec(s, "ambient in D minor 16 bars", "deep")
        h, _ = rules_plan("house in C major 16 bars", 7)
        with self.assertRaises(ValidationError):
            enrich_house_spec(h, "house in C major 16 bars", "techno")

    def test_opt_in_symbolic_project_has_shared_spec_and_traceable_plan(self):
        prompt = "warm deep house in E major, 16 bars, no lead"
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
                result = create(prompt, parent / "planned", seed=67,
                                production="groove-template", musical_plan_v2=True)
                baseline = create(prompt, parent / "legacy", seed=67,
                                  production="groove-template")
                repeated = create(prompt, parent / "repeat", seed=67,
                                  production="groove-template", musical_plan_v2=True)
            saved = json.loads((parent / "planned/song-spec.json").read_text())
            music = json.loads((parent / "planned/musical-plan-evidence.json").read_text())
            groove = json.loads((parent / "planned/groove-evidence.json").read_text())
            project = load(parent / "planned/project.kuang.json")
            self.assertEqual(saved["progression"], music["progression_degrees"])
            self.assertEqual(saved, groove["song_spec"])
            self.assertEqual(result["musical_plan"], music)
            self.assertEqual(project.metadata["musical_plan_version"], VERSION)
            self.assertEqual(music["perceptual_quality"], "NEEDS_LISTENING")
            self.assertTrue((parent / "planned/song.mid").is_file())
            self.assertEqual((parent / "planned/song.mid").read_bytes(),
                             (parent / "repeat/song.mid").read_bytes())
            self.assertEqual((parent / "planned/musical-plan-evidence.json").read_bytes(),
                             (parent / "repeat/musical-plan-evidence.json").read_bytes())
            self.assertNotIn("musical_plan", baseline)
            self.assertFalse((parent / "legacy/musical-plan-evidence.json").exists())
            self.assertTrue(result["validation"]["canonical"])
            self.assertFalse(result["validation"]["audio_verified"])

    def test_full_song_arranger_still_consumes_original_song_spec(self):
        prompt = "deep house in D minor 124 bpm full-length instrumental"
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
                r = create(prompt, Path(temp) / "full", seed=73,
                           production="groove-template",
                           full_song_bars=96, musical_plan_v2=True)
            self.assertEqual(r["actual_project_bars"], 96)
            self.assertEqual(r["song_spec"]["bars"], 32)
            self.assertEqual(r["song_spec"]["progression"],
                             r["musical_plan"]["progression_degrees"])
            self.assertIsNotNone(r["arrangement"])

    def test_default_unchanged_and_option_fails_closed(self):
        prompt = "straight house in A minor 125 bpm 16 bars"
        with tempfile.TemporaryDirectory() as temp:
            a, b, bad = (Path(temp) / name for name in ("default", "explicit-false", "invalid"))
            with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
                create(prompt, a, seed=41, production="groove-template")
                create(prompt, b, seed=41, production="groove-template",
                       musical_plan_v2=False)
                with self.assertRaisesRegex(ValidationError, "requires groove-template"):
                    create(prompt, bad, seed=41, production="refined",
                           musical_plan_v2=True)
            self.assertEqual((a / "project.kuang.json").read_bytes(),
                             (b / "project.kuang.json").read_bytes())
            self.assertEqual((a / "song.mid").read_bytes(),
                             (b / "song.mid").read_bytes())
            self.assertFalse(bad.exists())


if __name__ == "__main__":
    unittest.main()
