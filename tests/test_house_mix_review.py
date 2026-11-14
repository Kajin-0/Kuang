"""Native-free tests for rigorous loudness-matched house mix A/B packaging."""
import math
import tempfile
import unittest
import wave
from pathlib import Path

from kuang.house_mix_review import prepare_ab
from kuang.schema import ValidationError


def make_wav(path,amplitude,frequency=211,seconds=1):
    with wave.open(str(path),"wb") as w:
        w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000)
        payload=bytearray()
        for i in range(seconds*48000):
            v=round(amplitude*(2**23)*math.sin(2*math.pi*i*frequency/48000))
            payload.extend(v.to_bytes(3,"little",signed=True)*2)
        w.writeframes(payload)


class MixReviewTests(unittest.TestCase):
    def test_real_attentuation_only_matching_preserves_sources_and_no_winner(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            a=root/"a.wav";b=root/"b.wav";out=root/"ab"
            make_wav(a,.03)
            make_wav(b,.08,frequency=311)
            aa=a.read_bytes();bb=b.read_bytes()
            data=prepare_ab(a,b,out)
            self.assertEqual(data["perceptual_quality"],"NEEDS_LISTENING")
            self.assertLess(data["candidate_gain_db"],0)
            self.assertLess(data["original_gain_db"],0)
            self.assertEqual(a.read_bytes(),aa)
            self.assertEqual(b.read_bytes(),bb)
            self.assertTrue((out/"ab-evidence.json").is_file())
            self.assertTrue((out/"original-matched.wav").is_file())
            self.assertTrue((out/"candidate-matched.wav").is_file())
            with self.assertRaises(ValidationError):
                prepare_ab(a,b,out)

    def test_mismatch_format_and_identical_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            a=root/"a.wav";b=root/"b.wav"
            make_wav(a,.05)
            make_wav(b,.05,frequency=211,seconds=2)
            with self.assertRaisesRegex(ValidationError,"equal"):
                prepare_ab(a,b,root/"bad")
            with self.assertRaises(ValidationError):
                prepare_ab(a,a,root/"same")
