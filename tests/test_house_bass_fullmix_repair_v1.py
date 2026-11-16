"""Pure contextual decision checks; not a synthetic music-preference model."""
from copy import deepcopy
import unittest

from kuang.house_bass_fullmix_repair_v1 import (
    review_fullmix_bass_rescue, VERSION)
from kuang.house_groove_pocket import VERSION as POCKET_VERSION
from kuang.schema import ValidationError


def pocket(sub, body, *, onsets=16):
    return {
        "version": POCKET_VERSION, "section": "Groove",
        "tempo_bpm": 122., "kick_onsets_used": onsets,
        "bands": [
            {"hz": [25., 90.],
             "kick_near_0_100ms_vs_offbeat_200_300ms_db": sub,
             "near_mean_power": 100., "offbeat_mean_power": 20.},
            {"hz": [90., 250.],
             "kick_near_0_100ms_vs_offbeat_200_300ms_db": body,
             "near_mean_power": 100., "offbeat_mean_power": 20.}
        ]
    }


def review(original=None, candidate=None, **kwargs):
    options = {
        "source_sha256": "a"*64,
        "source_onset_gate": {"hard_flags": ["bass_onset_attack_severely_masked_by_kick"]},
        "candidate_onset_gate": {"hard_flags": []},
        "candidate_fit": {"warnings": []},
        "native_roundtrip_verified": True,
    }
    options.update(kwargs)
    return review_fullmix_bass_rescue(
        pocket(24.496,16.513) if original is None else original,
        pocket(12.061,6.288) if candidate is None else candidate,
        **options)


class NativeBassFullmixRepairTests(unittest.TestCase):
    def test_actual_rescue_profile_is_eligible_but_not_quality_judgment(self):
        result = review()
        self.assertEqual(result["version"], VERSION)
        self.assertEqual(result["relative_offbeat_gain_db"], [12.435,10.225])
        self.assertTrue(result["technical_replacement_eligible"])
        self.assertIsNone(result["automatic_musical_winner"])
        self.assertEqual(result["perceptual_quality"], "NOT_EVALUATED")

    def test_cannot_swap_a_source_with_no_initial_hard_fault(self):
        with self.assertRaises(ValidationError):
            review(source_onset_gate={"hard_flags": []})

    def test_known_producer_rejection_overrides_good_metrics(self):
        r = review(source_sha256="6e4e2259440015123c1f5670b2991674638c00f0ed198119dd20f3fb97cd918c")
        self.assertFalse(r["technical_replacement_eligible"])
        self.assertEqual(r["status"], "REJECT_PRODUCER_SOURCE_VETO")

    def test_no_auto_swap_for_meager_gain_or_worse_body(self):
        for after in (pocket(23.9,16.3), pocket(15,16), pocket(30,5)):
            with self.subTest(after=after["bands"]):
                r = review(candidate=after)
                self.assertEqual(r["status"], "REJECT_NO_MEANINGFUL_FULLMIX_OFFBEAT_REPAIR")

    def test_cannot_replace_with_active_hard_fault_or_phase_problem(self):
        self.assertEqual(review(candidate_onset_gate={"hard_flags": ["silent_bass"]})["status"],
                         "REJECT_CANDIDATE_HARD_ONSET_FAULT")
        self.assertEqual(review(candidate_fit={"warnings":["full_mix_sub_mono_folddown_loss"]})["status"],
                         "REJECT_NATIVE_SUB_OR_MONO_FAULT")

    def test_missing_native_proof_and_unaligned_source_fail_closed(self):
        with self.assertRaises(ValidationError):
            review(native_roundtrip_verified=False)
        with self.assertRaises(ValidationError):
            review(candidate=pocket(12,6,onsets=12))
        with self.assertRaises(ValidationError):
            review(candidate={"version":POCKET_VERSION,"bands":[]})
        with self.assertRaises(ValidationError):
            review(source_sha256="invalid")

    def test_invalid_silent_or_nan_band_is_rejected(self):
        for change in ("offbeat_mean_power", "near_mean_power",
                       "kick_near_0_100ms_vs_offbeat_200_300ms_db"):
            changed=pocket(12,6)
            changed["bands"][0][change]=float("nan")
            with self.subTest(change=change), self.assertRaises(ValidationError):
                review(candidate=changed)


if __name__ == "__main__":
    unittest.main()
