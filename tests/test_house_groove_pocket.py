"""Diagnostic geometry and reproducibility checks, not subjective music gates."""
from __future__ import annotations

import math
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace

from kuang.house_groove_pocket import VERSION, evaluate_pocket
from kuang.schema import ValidationError


def mock_project():
    bpm=120.
    beats=[i*960 for i in range(6)]
    c=SimpleNamespace(start=0,notes=[SimpleNamespace(start=t) for t in beats])
    k=SimpleNamespace(id="track-kick",clips=[c])
    sec=SimpleNamespace(name="Groove",start=0,length=6*960)
    return SimpleNamespace(tracks=[k],sections=[sec],ppq=960,tempo_bpm=bpm)


def generate(path, *, variable=False):
    rate=48000
    with wave.open(str(path),"wb") as w:
        w.setnchannels(2);w.setsampwidth(3);w.setframerate(rate)
        block=bytearray()
        for i in range(rate*3):
            phase=i/rate
            within=phase % .5
            gain=3. if variable and .2 <= within < .3 else 1.
            sample=gain*(.08*math.sin(2*math.pi*60*phase)
                         +.04*math.sin(2*math.pi*150*phase))
            x=round(sample*8388608.)
            block.extend(x.to_bytes(3,"little",signed=True)*2)
        w.writeframes(block)


class PocketDiagnosticsTests(unittest.TestCase):
    def test_constant_tone_has_near_equal_kick_and_offbeat_energy(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"flat.wav";generate(p)
            first=evaluate_pocket(mock_project(),p)
            second=evaluate_pocket(mock_project(),p)
            self.assertEqual(first,second)
            self.assertEqual(first["version"],VERSION)
            self.assertEqual(first["kick_onsets_used"],6)
            self.assertEqual(first["perceptual_quality"],"NOT_EVALUATED")
            for band in first["bands"]:
                self.assertLess(abs(band["kick_near_0_100ms_vs_offbeat_200_300ms_db"]),.1)

    def test_source_with_bigger_offbeat_energy_has_negative_ratio(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"offbeat.wav";generate(p,variable=True)
            out=evaluate_pocket(mock_project(),p)
            for band in out["bands"]:
                self.assertLess(band["kick_near_0_100ms_vs_offbeat_200_300ms_db"],-5)

    def test_missing_wav_and_invalid_section_fail(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValidationError):
                evaluate_pocket(mock_project(),Path(d)/"missing.wav")
            p=Path(d)/"flat.wav";generate(p)
            with self.assertRaises(ValidationError):
                evaluate_pocket(mock_project(),p,section="not-a-section")
            with self.assertRaises(ValidationError):
                evaluate_pocket(mock_project(),p,max_events=200)


if __name__=="__main__":
    unittest.main()
