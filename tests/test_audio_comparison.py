import tempfile
import unittest
import wave
from pathlib import Path

from kuang.audio import compare_wavs
from kuang.schema import ValidationError


class AudioComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def wav(self, name, values, *, width=3, channels=2, rate=48000):
        path = self.root/name
        with wave.open(str(path), "wb") as s:
            s.setnchannels(channels); s.setsampwidth(width); s.setframerate(rate)
            s.writeframes(b''.join(v.to_bytes(width, "little", signed=True) for v in values))
        return path

    def test_exact_pcm_is_zero_difference_in_all_integer_widths(self):
        for width in (2, 3, 4):
            a = self.wav(f"a{width}.wav", [100, -100]*10, width=width)
            b = self.wav(f"b{width}.wav", [100, -100]*10, width=width)
            r = compare_wavs(a, b)
            self.assertEqual(r["changed_samples"], 0)
            self.assertEqual(r["difference_rms"], 0)
            self.assertIsNone(r["difference_rms_dbfs"])
            self.assertFalse(r["measurable_change"])

    def test_sample_delta_rms_peak_fraction_and_ratio_are_measured(self):
        a = self.wav("a.wav", [100000, -100000]*10)
        b = self.wav("b.wav", [200000, -200000]*10)
        r = compare_wavs(a, b)
        self.assertTrue(r["measurable_change"])
        self.assertEqual(r["changed_fraction"], 1)
        self.assertAlmostEqual(r["difference_rms"], 100000/(2**23))
        self.assertEqual(r["difference_to_original_rms_ratio"], 1)
        self.assertEqual(r["offset_frames"], 0)

    def test_tiny_quantization_only_change_is_not_enough(self):
        a = self.wav("a.wav", [100000, -100000]*10)
        b = self.wav("b.wav", [100001, -100001]*10)
        r = compare_wavs(a, b)
        self.assertGreater(r["changed_samples"], 0)
        self.assertFalse(r["measurable_change"])

    def test_format_frame_count_rate_and_compression_must_match(self):
        a = self.wav("a.wav", [100, -100]*10)
        for i, options in enumerate(({"width": 2}, {"channels": 1}, {"rate": 44100})):
            b = self.wav(f"b{i}.wav", [100, -100]*10, **options)
            with self.assertRaises(ValidationError): compare_wavs(a, b)
        with self.assertRaises(ValidationError): compare_wavs(a, self.wav("short.wav", [100, -100]))

    def test_silence_has_no_relative_difference_reference(self):
        a = self.wav("a.wav", [0, 0]*10)
        b = self.wav("b.wav", [100000, -100000]*10)
        r = compare_wavs(a, b)
        self.assertIsNone(r["difference_to_original_rms_ratio"])
        self.assertFalse(r["measurable_change"])

    def test_truncated_or_empty_wavs_fail(self):
        a = self.wav("a.wav", [100000, -100000]*10)
        b = self.wav("b.wav", [100000, -100000]*10)
        b.write_bytes(b.read_bytes()[:-4])
        with self.assertRaises(ValidationError): compare_wavs(a, b)
        with self.assertRaises(ValidationError): compare_wavs(a, self.wav("empty.wav", []))
