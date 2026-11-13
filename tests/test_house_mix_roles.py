"""Focused mix-role calibration tests; no copyrighted source assets or native host required."""
import math
import tempfile
import unittest
import wave
from pathlib import Path

from kuang.house_mix_roles import (_rms_region, _role_solo, _window,
                                   apply_offsets, role_offsets)
from kuang.house_template import template
from kuang.schema import ValidationError, dumps
from kuang.song import rules_plan
from kuang import midi


class HouseMixRoleTests(unittest.TestCase):
    def setUp(self):
        self.spec, _ = rules_plan("deep house in C minor, 16 bars", 17)
        self.project, _ = template(self.spec,profile="deep",harmony_profile="simple")

    def test_window_uses_groove_not_intro_or_breakdown(self):
        window = _window(self.project)
        self.assertEqual(window["name"], "Groove")
        self.assertGreater(window["start_seconds"], 0)
        self.assertGreater(window["end_seconds"], window["start_seconds"])

    def test_solo_mutes_every_other_instrument_without_touching_notes(self):
        src = dumps(self.project)
        for role, tids in {"kick":{"track-kick"},"bass":{"track-bass"},
                           "chords":{"track-harmony"}}.items():
            solo = _role_solo(self.project,role)
            for t in solo.tracks:
                if t.kind == "midi":
                    self.assertEqual(t.controls["mixer.mute"],int(t.id not in tids))
            self.assertEqual(midi.export_bytes(solo),midi.export_bytes(self.project))
        self.assertEqual(src,dumps(self.project))
        with self.assertRaises(ValidationError):
            _role_solo(self.project,"future")

    def test_offsets_are_bounded_and_relative_to_actual_kick(self):
        inputs = {"kick":{"rms_dbfs":-20.},"bass":{"rms_dbfs":-30.},
                  "chords":{"rms_dbfs":-24.}}
        gains, evidence = role_offsets(inputs)
        self.assertEqual(gains,{"kick":0.,"bass":4.,"chords":-3.})
        self.assertTrue(evidence["bass"]["clamped"])
        self.assertTrue(evidence["bass"]["within_3db_heuristic"])
        self.assertEqual(evidence["bass"]["residual_vs_heuristic_db"],-3.)
        self.assertFalse(evidence["chords"]["clamped"])
        self.assertTrue(evidence["chords"]["within_3db_heuristic"])
        self.assertEqual(evidence["bass"]["observed_vs_kick_db"],-10.)

    def test_adjustments_preserve_notes_effects_and_duck_envelopes(self):
        p = self.project
        baseline = midi.export_bytes(p)
        q = apply_offsets(p,{"kick":0.,"bass":3.,"chords":-2.})
        self.assertEqual(midi.export_bytes(q),baseline)
        self.assertEqual(p.sections,q.sections)
        for role,delta in (("bass",3),("harmony",-2)):
            a = next(t for t in p.tracks if t.id=="track-"+role)
            b = next(t for t in q.tracks if t.id=="track-"+role)
            self.assertAlmostEqual(b.controls["mixer.gain_db"]-a.controls["mixer.gain_db"],delta)
            original = next(x for x in p.automation if x.id==f"production-{role}-duck")
            changed = next(x for x in q.automation if x.id==f"production-{role}-duck")
            self.assertEqual([x.tick for x in original.points],[x.tick for x in changed.points])
            self.assertTrue(all(abs(y.value-x.value-delta)<1e-8
                                for x,y in zip(original.points,changed.points)))

    def test_fail_closed_for_unknowns_silence_and_unbounded_gains(self):
        inputs = {"kick":{"rms_dbfs":-20.},"bass":{"rms_dbfs":-30.},
                  "chords":{"rms_dbfs":-24.}}
        with self.assertRaises(ValidationError):
            role_offsets({**inputs,"pad":{"rms_dbfs":-25.}})
        with self.assertRaises(ValidationError):
            role_offsets({**inputs,"bass":{"rms_dbfs":float("nan")}})
        with self.assertRaises(ValidationError):
            apply_offsets(self.project,{"kick":0.,"bass":7.,"chords":0.})

    def test_regional_pcm_rms_ignores_intro(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"stem.wav"
            with wave.open(str(path),"wb") as w:
                w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000)
                for magnitude in (100,10000):
                    payload=b"".join(int(magnitude).to_bytes(3,"little",signed=True)*2
                                     for _ in range(4800))
                    w.writeframes(payload)
            w0={"start_seconds":0,"end_seconds":.1}
            w1={"start_seconds":.1,"end_seconds":.2}
            a=_rms_region(path,w0);b=_rms_region(path,w1)
            self.assertAlmostEqual(b["rms_dbfs"]-a["rms_dbfs"],40,delta=.01)
            self.assertEqual(a["wav_sha256"],b["wav_sha256"])
