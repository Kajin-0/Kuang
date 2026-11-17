"""Source integrity and evidence policy tests; human groove preference untested."""
import copy
import unittest
from unittest.mock import patch
from kuang.house_bass_audio_gate_v1 import (
    bass_gain_trial, review_native_bass_trials, VERSION,
)
from kuang.house_groove_pocket import VERSION as POCKET_VERSION
from kuang.schema import ValidationError, state_hash
from kuang.house_template import template
from kuang.song import rules_plan


def _source():
    s, _ = rules_plan("jackin house in G minor, 16 bars, 126 bpm", 83)
    p, _ = template(s, profile="jackin", impact_pocket=True,
                    groove_identity_v2=True, phrase_stable_chords_v2=True)
    return p


def _pocket(sub, body):
    return {"version": POCKET_VERSION, "kick_onsets_used": 16, "bands": [
        {"hz": [25.0, 90.0], "kick_near_0_100ms_vs_offbeat_200_300ms_db": sub},
        {"hz": [90.0, 250.0], "kick_near_0_100ms_vs_offbeat_200_300ms_db": body},
    ]}


def _meter(lufs=-25., peak=-5., clips=0):
    return {"integrated_lufs": lufs, "true_peak_dbtp": peak,
            "clipped_samples": clips, "duration_seconds": 42.}


class AudioBassGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = _source()
        cls.trial, _ = bass_gain_trial(cls.original, gain_db=3.)

    def test_trial_changes_only_bass_gain_and_does_not_mutate_original(self):
        before = state_hash(self.original)
        q, receipt = bass_gain_trial(self.original, gain_db=3.)
        self.assertEqual(q, self.trial)
        self.assertEqual(state_hash(self.original), before)
        self.assertEqual(receipt["version"], VERSION)
        self.assertFalse(receipt["default_enabled"])
        for a, b in zip(self.original.tracks, q.tracks):
            if a.id != "track-bass":
                self.assertEqual(a, b)
            else:
                self.assertEqual(b.controls["mixer.gain_db"],
                                 a.controls["mixer.gain_db"] + 3.)
                x = copy.deepcopy(b)
                x.controls["mixer.gain_db"] -= 3.
                self.assertEqual(a, x)
        for a, b in zip(self.original.automation, q.automation):
            offset = 3. if a.target_id == "track-bass" and a.parameter_id == "mixer.gain_db" else 0.
            self.assertEqual([v.tick for v in a.points], [v.tick for v in b.points])
            self.assertEqual([v.value + offset for v in a.points],
                             [v.value for v in b.points])

    def test_trial_rejects_invalid_gain(self):
        for bad in (0, -1, 6.1, float("nan"), "3", True):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                bass_gain_trial(self.original, gain_db=bad)

    def test_reviewer_shortlists_conditional_not_automatically(self):
        with patch("kuang.house_bass_audio_gate_v1.measure",
                   side_effect=[_meter(), _meter(-24., peak=-4.)]), \
             patch("kuang.house_bass_audio_gate_v1.evaluate_pocket",
                   side_effect=[_pocket(10, 7), _pocket(8, 6)]):
            out = review_native_bass_trials(
                self.original, "baseline.wav",
                [(3., self.trial, "candidate.wav", True)])
        self.assertEqual(out["minimum_conditional_gain_db"], 3.)
        self.assertEqual(out["candidate_status"], "SPECTRAL_SHORTLIST_ONLY")
        self.assertTrue(out["tested"][0]["conditional_spectral_gate"])
        self.assertIsNone(out["winner"])
        self.assertFalse(out["automatic_gain_change"])
        self.assertEqual(out["phase_aware_stem_review"], "NOT_YET_MEASURED")

    def test_rejects_candidate_with_unrelated_chord_edit(self):
        bad = copy.deepcopy(self.trial)
        chords = next(t for t in bad.tracks if t.id == "track-harmony")
        chords.controls["mixer.gain_db"] -= 1
        with patch("kuang.house_bass_audio_gate_v1.measure",
                   return_value=_meter()), \
             patch("kuang.house_bass_audio_gate_v1.evaluate_pocket",
                   return_value=_pocket(10, 7)):
            with self.assertRaises(ValidationError):
                review_native_bass_trials(
                    self.original, "a.wav", [(3., bad, "b.wav", True)])

    def test_rejects_unverified_or_duplicate_trials(self):
        with patch("kuang.house_bass_audio_gate_v1.measure",
                   return_value=_meter()), \
             patch("kuang.house_bass_audio_gate_v1.evaluate_pocket",
                   return_value=_pocket(10, 7)):
            with self.assertRaises(ValidationError):
                review_native_bass_trials(
                    self.original, "a.wav", [(3., self.trial, "b.wav", False)])
            with self.assertRaises(ValidationError):
                review_native_bass_trials(
                    self.original, "a.wav",
                    [(3., self.trial, "b.wav", True),
                     (3., self.trial, "c.wav", True)])

    def test_safety_and_minimum_gain_gate(self):
        q6, _ = bass_gain_trial(self.original, gain_db=6.)
        with patch("kuang.house_bass_audio_gate_v1.measure",
                   side_effect=[_meter(), _meter(-24., peak=-.1), _meter(-23., peak=-3)]), \
             patch("kuang.house_bass_audio_gate_v1.evaluate_pocket",
                   side_effect=[_pocket(10, 7), _pocket(6, 4), _pocket(8, 6)]):
            out = review_native_bass_trials(
                self.original, "base.wav",
                [(3., self.trial, "three.wav", True),
                 (6., q6, "six.wav", True)])
        self.assertFalse(out["tested"][0]["peak_and_clipping_safe"])
        self.assertFalse(out["tested"][0]["conditional_spectral_gate"])
        self.assertEqual(out["minimum_conditional_gain_db"], 6.)

    def test_reviewer_does_not_choose_if_no_band_improvement(self):
        with patch("kuang.house_bass_audio_gate_v1.measure",
                   side_effect=[_meter(), _meter(-24)]), \
             patch("kuang.house_bass_audio_gate_v1.evaluate_pocket",
                   side_effect=[_pocket(10, 7), _pocket(9.9, 6.9)]):
            out = review_native_bass_trials(
                self.original, "base.wav",
                [(3., self.trial, "b.wav", True)])
        self.assertEqual(out["candidate_status"], "NO_SPECTRAL_PASS")
        self.assertIsNone(out["minimum_conditional_gain_db"])


if __name__ == "__main__":
    unittest.main()
