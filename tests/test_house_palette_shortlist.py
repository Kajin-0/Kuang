"""Tests for bounded locked-MIDI technical shortlist and safe caching."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kuang.house_palette_shortlist import (
    MAX_ALTERNATIVES, _cached, create_shortlist, evaluate_comparison, plan_candidates,
)
from kuang.sample_assets import digest
import json
from kuang.schema import ValidationError


class TechnicalShortlistTests(unittest.TestCase):
    def _receipt(self, base_lufs=-25., alt_lufs=-27., warnings=None):
        return {"locked_midi_identical":True,
                "unchanged_key_tempo_sections_effects_drums":True,
                "original_premix_meter":{"integrated_lufs":base_lufs},
                "alternative_premix_meter":{
                    "integrated_lufs":alt_lufs,
                    "true_peak_dbtp":-3.,
                    "clipped_samples":0},
                "alternative_context_fit":{"warnings":warnings or []}}

    def test_no_unverified_quality_winner_and_level_reviews(self):
        self.assertEqual(evaluate_comparison(self._receipt()),("TECHNICALLY_ELIGIBLE",[]))
        level=self._receipt(alt_lufs=-30.)
        self.assertEqual(evaluate_comparison(level),
            ("REVIEW",["large_premix_loudness_change_same_locked_midi"]))
        self.assertEqual(evaluate_comparison(self._receipt(
            warnings=["bass_more_active_at_kick_than_after"])),
            ("REVIEW",["bass_more_active_at_kick_than_after"]))

    def test_reject_real_technical_failures_and_fail_closed_invalid_receipts(self):
        flag="full_mix_sub_mono_folddown_loss"
        status,flags=evaluate_comparison(self._receipt(warnings=[flag]))
        self.assertEqual(status,"REJECT")
        self.assertIn(flag,flags)
        status,flags=evaluate_comparison(self._receipt(warnings=[
            "kick_bass_sub_destructive_summation"]))
        self.assertEqual(status,"REJECT")
        bad=self._receipt()
        bad["alternative_premix_meter"]["true_peak_dbtp"]=-.7
        self.assertEqual(evaluate_comparison(bad),("REJECT",["unsafe_true_peak"]))
        bad=self._receipt()
        bad["locked_midi_identical"]=False
        with self.assertRaises(ValidationError):
            evaluate_comparison(bad)

    def test_plan_input_bounded_and_duplicate_donor_rejected(self):
        with self.assertRaises(ValidationError):
            plan_candidates("unknown",[])
        with self.assertRaises(ValidationError):
            plan_candidates("unknown",[("bass","x")]*4)
        self.assertEqual(MAX_ALTERNATIVES,3)
        with tempfile.TemporaryDirectory() as tmp:
            with patch("kuang.house_palette_shortlist.plan_candidates",
                       side_effect=ValidationError("donor verification failed")):
                with self.assertRaisesRegex(ValidationError,"donor"):
                    create_shortlist("x",[("bass","y")],
                        Path(tmp)/"out","fake")

    def test_cached_native_comparison_rejects_hash_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            base=root/"base";base.mkdir()
            (base/"preview.wav").write_bytes(b"source-audio")
            old=root/"cached";(old/"candidate/native").mkdir(parents=True)
            (old/"ab").mkdir()
            native=old/"candidate/native/session.scraft"
            native.write_bytes(b"private-native")
            alt=old/"candidate/candidate.wav"
            alt.write_bytes(b"alternative-wav")
            item={
                "role":"bass",
                "source_canonical_sha256":"source-project-sha",
                "alternate_canonical_sha256":"alternate-project-sha",
                "project_midi_sha256":"original-midi-sha",
                "source_preset_name":"old bass",
                "alternate_preset_name":"new bass",
            }
            receipt={
                "swapped_role":item["role"],
                "source_project_sha256":item["source_canonical_sha256"],
                "alternate_project_sha256":item["alternate_canonical_sha256"],
                "source_midi_sha256":item["project_midi_sha256"],
                "locked_midi_identical":True,
                "unchanged_key_tempo_sections_effects_drums":True,
                "source_name":item["source_preset_name"],
                "alternate_name":item["alternate_preset_name"],
                "subjective_winner":None,
                "technically_eligible":True,
            }
            (old/"source-compare-report.json").write_text(json.dumps(receipt))
            (old/"ab/ab-evidence.json").write_text(json.dumps({
                "source_wav_sha256":{
                    str(base/"preview.wav"):digest(base/"preview.wav"),
                    str(alt):digest(alt),
                }
            }))
            cached,report=_cached(old,item,base)
            self.assertEqual(cached,old)
            self.assertEqual(report,receipt)
            alt.write_bytes(b"tampered-alternative")
            with self.assertRaisesRegex(ValidationError,"drift"):
                _cached(old,item,base)

    def test_batch_evidence_statuses_separate_from_winner(self):
        records=[self._receipt(-25,-26),self._receipt(-25,-31)]
        statuses=[evaluate_comparison(record)[0] for record in records]
        self.assertEqual(statuses,["TECHNICALLY_ELIGIBLE","REVIEW"])
