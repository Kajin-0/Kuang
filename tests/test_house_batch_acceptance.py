"""Repeatable batch QA tests: technical integrity is not music approval."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kuang.house_batch_acceptance import (
    batch_audit, PREVIEW_WARNINGS, _drum_sources, _native_bass_rescue_status,
    audit_autonomous_attempts)
from kuang.schema import ValidationError


class BatchAuditTests(unittest.TestCase):
    def test_distinct_source_families_and_no_artificial_quality_winner(self):
        def fake(path,spectral=True):
            name=Path(path).name
            return {"candidate":name,"groove_fingerprint":name+"-groove",
                    "instrument_preset_names":{"bass":name+"bass","chord":name+"chord"},
                    "drum_source_ids":{"kick":name+"drum"},
                    "render_integrity":"PASS",
                    "near_finished_preview_readiness":"NOT_READY",
                    "mix_level_warnings":["near_finished_preview_loudness_low"]}
        with tempfile.TemporaryDirectory() as tmp,patch(
             "kuang.house_batch_acceptance.inspect_candidate",side_effect=fake):
            a,b,c=[Path(tmp)/name for name in ("deep","jackin","minimal")]
            out=Path(tmp)/"batch.json"
            report=batch_audit([a,b,c],output=out)
            self.assertTrue(report["all_native_integrity_pass"])
            self.assertFalse(report["producer_ready"])
            self.assertEqual(report["near_finished_preview_ready_count"],0)
            self.assertEqual(report["distinct_sources_and_grooves"],
                             {"groove_fingerprint":3,"instrument_preset_names":3,
                              "drum_source_ids":3})
            self.assertTrue(out.is_file())
            with self.assertRaises(ValidationError):
                batch_audit([a,b,c],output=out)
            with self.assertRaises(ValidationError):
                batch_audit([a,a],output=Path(tmp)/"dupe.json")

    def test_real_drum_receipt_contains_extra_groove_metadata(self):
        actual={"groove_impact_pocket":{"kick_relative_gain_delta_db":8.0},
                "kick":{"source_id":"house.kick.tight-01"},
                "snare":{"source_id":"house.snare.snap-01"},
                "hats":{"source_id":"house.hat.closed-06"},
                "open_hat":{"source_id":"house.hat.open-01"}}
        self.assertEqual(set(_drum_sources(actual)),{"kick","snare","hats","open_hat"})
        with self.assertRaises(ValidationError):
            _drum_sources({"groove_impact_pocket":{}})

    def test_fails_closed_on_unresolved_bass_and_unproven_replacement(self):
        initial={"bass_onset_rescue_requested":True,
                 "bass_onset_baseline_gate":{"hard_flags":["weak_attack"]},
                 "bass_onset_rescued":False,"comparisons":[]}
        with self.assertRaisesRegex(ValidationError,"unresolved"):
            _native_bass_rescue_status(initial)
        initial["bass_onset_rescued"]=True
        with self.assertRaisesRegex(ValidationError,"missing actual"):
            _native_bass_rescue_status(initial)
        initial["comparisons"]=[{"role":"bass","chosen":True,
            "native_fullmix_bass_repair":{"status":"TECHNICAL_REPAIR_ELIGIBLE",
                                         "technical_replacement_eligible":True},
            "native_note_onset_gate":{"hard_flags":[]}}]
        self.assertEqual(_native_bass_rescue_status(initial),
                         "TECHNICAL_REPAIR_VERIFIED")
        initial["comparisons"][0]["native_fullmix_bass_repair"]["technical_replacement_eligible"]=False
        with self.assertRaises(ValidationError):
            _native_bass_rescue_status(initial)

    def test_batch_retains_actual_failed_attempts_in_denominator(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"results.json"
            attempts={
                "deep_41":{"seed":41,"style":"deep","status":"FAIL_CLOSED",
                           "stderr_tail":"bass native onset fault had no safe verified source rescue"},
                "jackin_83":{"seed":83,"style":"jackin","status":"FAIL_CLOSED",
                           "stderr_tail":"bass native onset fault had no safe verified source rescue"},
                "minimal_97":{"seed":97,"style":"minimal","status":"PASS_NATIVE_TECHNICAL"},
            }
            p.write_text(json.dumps({"complete":True,"defaults_modified":False,
                                    "cases":attempts}))
            proof={"seed":97,"genre":"minimal",
                   "autonomous_bass_repair_status":"TECHNICAL_REPAIR_VERIFIED",
                   "bass_source_sha256":"a"*64,"groove_fingerprint":"unique",
                   "drum_source_ids":{"kick":"test"},
                   "mix_level_warnings":["near_finished_preview_loudness_low"]}
            with patch("kuang.house_batch_acceptance.inspect_candidate",
                       return_value=proof) as mock:
                report=audit_autonomous_attempts(p)
            mock.assert_called_once()
            self.assertEqual(report["attempted"],3)
            self.assertEqual(report["completed"],1)
            self.assertEqual(report["failed_closed"],2)
            self.assertEqual(report["technical_yield"],.3333)
            self.assertEqual(report["outcome"],"GENERALIZATION_TECHNICAL_GATE_FAIL")
            self.assertFalse(report["production_default_promotion"])
            self.assertEqual(report["distinct_successful_bass_sources"],1)
            self.assertEqual(report["artistic_quality"],"NOT_EVALUATED")
            attempts["minimal_97"]["status"]="RUNNING"
            p.write_text(json.dumps({"complete":True,"defaults_modified":False,"cases":attempts}))
            with self.assertRaises(ValidationError):
                audit_autonomous_attempts(p)

    def test_batch_size_bounded(self):
        with self.assertRaises(ValidationError):
            batch_audit([])
        with self.assertRaises(ValidationError):
            batch_audit([str(i) for i in range(9)])
        self.assertLess(PREVIEW_WARNINGS["min_integrated_lufs"],0)
