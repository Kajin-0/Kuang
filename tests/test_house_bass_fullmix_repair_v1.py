"""Pure contextual decision checks; not a synthetic music-preference model."""
from copy import deepcopy
import json
import math
from pathlib import Path
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
             "near_mean_power": 100.,
             "offbeat_mean_power": 100./10**(sub/10.)},
            {"hz": [90., 250.],
             "kick_near_0_100ms_vs_offbeat_200_300ms_db": body,
             "near_mean_power": 100.,
             "offbeat_mean_power": 100./10**(body/10.)}
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
    def test_real_native_cross_style_evidence_regression(self):
        # The WAVs and Vital preset states stay private on the producer VPS.
        # Only independently measured fullmix native power receipts are
        # committed. Never reinterpret the negative gain-only control as a
        # source replacement: onset clearance is not established there.
        fixture=Path(__file__).parent/"fixtures"/"house_bass_native_fullmix_crossstyle_20261115.json"
        report=json.loads(fixture.read_text())
        self.assertEqual(report["native_source_contexts"],3)
        for label,case in report["cases"].items():
            with self.subTest(real_native=label):
                result=review_fullmix_bass_rescue(
                    case["baseline_pocket"],case["candidate_pocket"],
                    source_sha256=case["source_sha256"],
                    source_onset_gate=case["source_onset_gate"],
                    candidate_onset_gate=(case["candidate_onset_gate"]
                        if case["candidate_onset_gate"] is not None
                        else {"hard_flags":[]}),
                    candidate_fit=case["candidate_fit"],
                    native_roundtrip_verified=True)
                self.assertEqual(result["status"],case["expected_status"])
                self.assertIsNone(result["automatic_musical_winner"])
                if case["type"]=="verified_native_gain_only_negative_control":
                    self.assertFalse(result["technical_replacement_eligible"])
                else:
                    self.assertTrue(result["technical_replacement_eligible"])
                    self.assertGreaterEqual(min(result["absolute_offbeat_energy_gain_db"]),1)
                    self.assertGreater(min(result["near_kick_energy_change_db"]),-1.5)

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

    def test_slow_attack_review_flag_cannot_be_auto_approved(self):
        r=review(candidate_onset_gate={
            "hard_flags":[],
            "requires_fullmix_context_review":True,
            "review_flags":["bass_slow_attack_requires_fullmix_context_review"]})
        self.assertEqual(r["status"],"DEFER_UNRESOLVED_SOURCE_ARTICULATION_REVIEW")
        self.assertFalse(r["technical_replacement_eligible"])

    def test_missing_native_proof_and_unaligned_source_fail_closed(self):
        with self.assertRaises(ValidationError):
            review(native_roundtrip_verified=False)
        with self.assertRaises(ValidationError):
            review(candidate=pocket(12,6,onsets=12))
        with self.assertRaises(ValidationError):
            review(candidate={"version":POCKET_VERSION,"bands":[]})
        with self.assertRaises(ValidationError):
            review(source_sha256="invalid")

    def test_false_ratio_improvement_by_kick_attenuation_is_rejected(self):
        a=pocket(10,10)
        b=pocket(8,8)
        # Both near and offbeat power are cut; the candidate appears
        # better by ratio alone only because near-kick power collapses.
        for row in b["bands"]:
            row["near_mean_power"] = 30.
            row["offbeat_mean_power"] = 30./10**(8/10.)
        result=review(original=a,candidate=b)
        self.assertEqual(result["status"],"REJECT_NO_ABSOLUTE_OFFBEAT_ENERGY_GAIN")
        self.assertFalse(result["technical_replacement_eligible"])

    def test_kick_energy_cannot_disappear_when_offbeat_gains(self):
        a=pocket(10,10)
        # Offbeat improves 1.5 dB, yet near-kick loses 2.218 dB. The
        # resulting ratio appears better by 3.718 dB; reject this path.
        actual_offbeat = 10. * 10**(1.5/10.)
        ratio = 10*math.log10(60./actual_offbeat)
        b=pocket(ratio,ratio)
        for row in b["bands"]:
            row["near_mean_power"]=60.
            row["offbeat_mean_power"]=actual_offbeat
        result=review(original=a,candidate=b)
        self.assertEqual(result["status"],"REJECT_KICK_NEAR_ENERGY_COLLAPSE")
        self.assertFalse(result["technical_replacement_eligible"])

    def test_inconsistent_pocket_ratio_and_actual_powers_rejected(self):
        changed=pocket(12,6)
        changed["bands"][0]["offbeat_mean_power"]*=4
        with self.assertRaisesRegex(ValidationError, "inconsistent native"):
            review(candidate=changed)

    def test_invalid_silent_or_nan_band_is_rejected(self):
        for change in ("offbeat_mean_power", "near_mean_power",
                       "kick_near_0_100ms_vs_offbeat_200_300ms_db"):
            changed=pocket(12,6)
            changed["bands"][0][change]=float("nan")
            with self.subTest(change=change), self.assertRaises(ValidationError):
                review(candidate=changed)


if __name__ == "__main__":
    unittest.main()
