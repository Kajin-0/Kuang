"""Tests for reproducible, safe, private house mastering-preview derivatives."""
import json
import math
import tempfile
import unittest
import wave
from pathlib import Path

from kuang.house_master_preview import (
    _peak_safe_gain, _assert_safe, render_previews,
)
from kuang.loudness import measure
from kuang.mastering import file_hash
from kuang.schema import ValidationError


def sine(path, seconds=2.1):
    with wave.open(str(path),"wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(3)
        wav.setframerate(48000)
        buffer=bytearray()
        for i in range(round(seconds*48000)):
            x=.07*math.sin(2*math.pi*97*i/48000)
            x+=.025*math.sin(2*math.pi*880*i/48000)
            code=round((2**23-1)*x)
            buffer.extend(code.to_bytes(3,"little",signed=True)*2)
        wav.writeframes(buffer)


class HouseMasterPreviewTests(unittest.TestCase):
    def test_bounded_gain_no_clipping_or_fake_limiter(self):
        self.assertAlmostEqual(_peak_safe_gain(-10.),8.3,places=3)
        self.assertEqual(_peak_safe_gain(-35.),12.)
        self.assertEqual(_peak_safe_gain(-1.4),0.)
        with self.assertRaises(ValidationError):
            _peak_safe_gain(float("nan"))
        with self.assertRaises(ValidationError):
            _peak_safe_gain(-.1)

    def test_safety_checks_format_frames_and_true_peak(self):
        first={"sample_rate":48000,"channels":2,"bits_per_sample":24,"frames":120000,
               "integrated_lufs":-24.}
        acceptable={**first,"integrated_lufs":-17.,"clipped_samples":0,
                    "true_peak_dbtp":-1.7}
        _assert_safe(first,acceptable,9.)
        with self.assertRaisesRegex(ValidationError,"clipped"):
            _assert_safe(first,{**acceptable,"true_peak_dbtp":-.4},9.)
        with self.assertRaisesRegex(ValidationError,"format"):
            _assert_safe(first,{**acceptable,"frames":119999},9.)
        with self.assertRaisesRegex(ValidationError,"bounded"):
            _assert_safe(first,acceptable,13.)

    def test_full_real_pcm_preview_two_variants_and_preserved_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original=root/"source"
            original.mkdir()
            (original/"native").mkdir()
            (original/"native/session.scraft").write_bytes(b"example native project")
            sine(original/"preview.wav")
            recorded=measure(original/"preview.wav")
            (original/"report.json").write_text(json.dumps({
                "native_save_reopen_equal":True,"measurement":recorded}))
            original_sha=file_hash(original/"preview.wav")
            out=root/"master"
            result=render_previews(original,out)
            self.assertFalse(result["producer_ready"])
            self.assertEqual(set(result["variants"]),{"gain_only","gentle"})
            self.assertEqual(original_sha,file_hash(original/"preview.wav"))
            for name in ("gain-only.wav","gentle-compression.wav"):
                self.assertTrue((out/name).exists())
                rendered=measure(out/name)
                self.assertEqual(rendered["clipped_samples"],0)
                self.assertLessEqual(rendered["true_peak_dbtp"],-1.1)
                self.assertEqual(rendered["frames"],recorded["frames"])
                self.assertGreater(rendered["integrated_lufs"],recorded["integrated_lufs"]-.2)
            report=json.loads((out/"master-preview-report.json").read_text())
            self.assertIsNone(report["preferred_mode"])
            self.assertFalse(report["producer_ready"])
            self.assertEqual(report["input_sha256"],original_sha)
            with self.assertRaises(ValidationError):
                render_previews(original,out)

    def test_unverified_native_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/"bad"
            source.mkdir()
            sine(source/"preview.wav")
            with self.assertRaises(ValidationError):
                render_previews(source,Path(tmp)/"out")
