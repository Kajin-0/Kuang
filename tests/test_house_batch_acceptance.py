"""Repeatable batch QA tests: technical integrity is not music approval."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kuang.house_batch_acceptance import batch_audit, PREVIEW_WARNINGS
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

    def test_batch_size_bounded(self):
        with self.assertRaises(ValidationError):
            batch_audit([])
        with self.assertRaises(ValidationError):
            batch_audit([str(i) for i in range(9)])
        self.assertLess(PREVIEW_WARNINGS["min_integrated_lufs"],0)
