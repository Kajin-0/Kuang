"""Synthetic, rights-clean regression tests for external reference analysis."""
import json
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from kuang.schema import ValidationError
from tools.house_reference_collection import (
    CATALOG, analyze_reference, audit_collection, catalog_sources,
)


def wav(path, *, seconds=0.65, rate=48000, channels=1, hz=60, amplitude=0.4):
    frames = round(seconds * rate)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        pcm = bytearray()
        for i in range(frames):
            # Gentle decay and safe PCM level, no external samples or downloads.
            value = round(32767 * amplitude * math.exp(-2 * i / max(1, frames)) *
                          math.sin(2 * math.pi * hz * i / rate))
            pcm.extend(struct.pack("<h", value) * channels)
        stream.writeframes(pcm)


class HouseReferenceCollectionTests(unittest.TestCase):
    def test_catalog_distinguishes_rights_and_correlation(self):
        sources = catalog_sources()
        self.assertEqual(sum(sources[k]["claimed_file_count"] for k in
                         ("musicradar-vintage-house-techno-371", "musicradar-deep-house-267",
                          "musicradar-house-338")), 976)
        for source in sources.values():
            self.assertFalse(source["rights"]["audio_redistribution"])
            self.assertFalse(source["rights"]["ai_training_authorized"])
            self.assertTrue(source["independence_note"])
        self.assertTrue(CATALOG.is_file())

    def test_mono_kick_spectrum_not_claimed_fundamental_or_lufs(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "kick.wav"
            wav(p, hz=60)
            out = analyze_reference(p, role="kick", loudness=True)
            self.assertEqual(out["format"]["sample_rate"], 48000)
            self.assertEqual(out["format"]["channels"], 1)
            self.assertGreater(out["peak_dbfs"], -14)
            self.assertEqual(out["clipped_samples"], 0)
            spectrum = out["spectrum"]
            self.assertIsNotNone(spectrum)
            self.assertFalse(spectrum["dominant_bin_is_kick_fundamental"])
            self.assertLess(abs(spectrum["dominant_30_150_hz_bin"] - 60), spectrum["bin_spacing_hz"])
            self.assertGreater(spectrum["band_power_fraction"]["kick_40_80"], 0.65)
            self.assertNotIn("integrated_lufs", out["loudness"])

    def test_loop_loudness_is_non_certified(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "loop.wav"
            wav(p, seconds=1.2, channels=2, hz=110)
            out = analyze_reference(p, role="drum_loop", loudness=True)
            self.assertIsInstance(out["loudness"]["integrated_lufs"], float)
            self.assertLess(out["loudness"]["true_peak_dbtp"], 0)
            self.assertFalse(out["loudness"]["certified"])

    def test_short_sample_abstains_spectral_and_lufs(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "short.wav"
            wav(p, seconds=0.02, hz=1000)
            out = analyze_reference(p, role="drum_loop", loudness=True)
            self.assertIsNone(out["spectrum"])
            self.assertEqual(out["loudness"]["status"], "not_meaningful_for_role_or_short_duration")

    def test_full_collection_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs = root / "wav"
            inputs.mkdir()
            wav(inputs / "a.wav", rate=44100)
            wav(inputs / "b.WAV", rate=48000, hz=80)
            output = root / "report.json"
            kwargs = dict(source_id="musicradar-deep-house-267", role="kick", group_id="kit1")
            result = audit_collection(inputs, output, **kwargs)
            self.assertEqual(result["summary"]["files_found"], 2)
            self.assertEqual(result["summary"]["measured"], 2)
            self.assertEqual(result["summary"]["rejected"], 0)
            self.assertFalse(result["independent_observations_established"])
            self.assertEqual(json.loads(output.read_text())["source_id"], kwargs["source_id"])
            self.assertEqual(len(result["files"][0]["sha256"]), 64)
            with self.assertRaises(ValidationError):
                audit_collection(inputs, output, **kwargs)
            with self.assertRaises(ValidationError):
                audit_collection(inputs, inputs / "inside.json", **kwargs)
            with self.assertRaises(ValidationError):
                audit_collection(inputs, root / "too-many.json", limit=1, **kwargs)

    def test_invalid_and_symlink_sources_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / "bad.wav"
            p.write_bytes(b"not a WAV file")
            with self.assertRaises((ValidationError, EOFError, wave.Error)):
                analyze_reference(p, role="kick")
            with self.assertRaises(ValidationError):
                analyze_reference(p, role="invented")
            target = root / "outside.wav"
            wav(target)
            source = root / "inputs"
            source.mkdir()
            (source / "linked.wav").symlink_to(target)
            with self.assertRaises(ValidationError):
                audit_collection(source, root / "linked.json",
                                 source_id="musicradar-house-338", role="mixed")


if __name__ == "__main__":
    unittest.main()
