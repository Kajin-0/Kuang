"""Opt-in bounded private Vital chord-source gain stabilization tests."""
import json
import math
import unittest
from copy import deepcopy
from kuang.house_role_level import chord_trim, apply_chord_calibration, MAX_TRIM_DB
from kuang.house_template import template
from kuang.schema import ValidationError, state_hash
from kuang.song import rules_plan
from kuang import midi


def selected(bass=.1,chord=.04,verified=True):
    return {"status":"complete","roles":{
       r:{"status":"accepted","runtime_verified":verified,
          "source_sha256":"sha256-"+r,
          "features":{"rms":value}}
       for r,value in (("bass",bass),("chord",chord))}}


class HouseChordLevelTests(unittest.TestCase):
    def test_technical_deadband_and_bounded_gain(self):
        self.assertEqual(chord_trim(selected(.1,.04))[0],0)
        self.assertEqual(chord_trim(selected(.1,.16))[0],-3)
        self.assertEqual(chord_trim(selected(.1,.01))[0],3)
        self.assertEqual(chord_trim(selected(.1,.16))[1]["clamped"],True)

    def test_project_only_modifies_chord_fader_and_duck_gain_points(self):
        spec,_=rules_plan("straight house in C minor 16 bars",41)
        p,_=template(spec,profile="straight",harmony_profile="simple",include_pad=False)
        original_hash=state_hash(p)
        old_midi=midi.export_bytes(p)
        q,e=apply_chord_calibration(p,selected(.1,.16))
        self.assertEqual(e["bounded_db"],-3)
        self.assertEqual(e["source_project_sha256"],original_hash)
        self.assertEqual(midi.export_bytes(q),old_midi)
        self.assertEqual(state_hash(p),original_hash)
        for x,y in zip(p.tracks,q.tracks):
            self.assertEqual(x.id,y.id)
            self.assertEqual(x.instrument,y.instrument)
            self.assertEqual(x.effects,y.effects)
            self.assertEqual(x.clips,y.clips)
            if x.id=="track-harmony":
                self.assertEqual(y.controls["mixer.gain_db"],
                                 x.controls["mixer.gain_db"]-3)
            else:
                self.assertEqual(x.controls,y.controls)
        for x,y in zip(p.automation,q.automation):
            self.assertEqual(x.target_id,y.target_id)
            self.assertEqual([v.tick for v in x.points],[v.tick for v in y.points])
            change=(-3 if x.target_id=="track-harmony"
                        and x.parameter_id=="mixer.gain_db" else 0)
            for m,n in zip(x.points,y.points):
                self.assertAlmostEqual(n.value-m.value,change)

    def test_invalid_audition_provenance_fails_closed(self):
        for entry in (
            selected(0,.1),selected(.1,float("nan")),
            selected(.1,.1,verified=False),{"status":"incomplete","roles":{}},
        ):
            with self.subTest(entry=entry):
                with self.assertRaises(ValidationError):
                    chord_trim(entry)

    def test_noop_is_byte_identical(self):
        spec,_=rules_plan("minimal house in G minor 16 bars",97)
        p,_=template(spec,profile="minimal",harmony_profile="simple",include_pad=False)
        source=state_hash(p)
        q,e=apply_chord_calibration(p,selected(.1,.05))
        self.assertEqual(state_hash(q),source)
        self.assertEqual(e["bounded_db"],0.)
