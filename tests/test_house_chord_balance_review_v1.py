import unittest
from kuang.house_chord_balance_review_v1 import chord_gain_candidate
from kuang.house_template import template
from kuang.song import rules_plan
from kuang.schema import ValidationError,dumps
from kuang import midi

class ChordBalanceReviewV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s,_=rules_plan("minimal house in C minor 32 bars 127 bpm",23)
        cls.source,_=template(s,profile="minimal",impact_pocket=True,groove_identity_v2=True)
    def test_reversible_trim_keeps_midi_and_all_other_roles(self):
        original=dumps(self.source)
        for db in (-2.,-3.):
            p,r=chord_gain_candidate(self.source,db)
            self.assertEqual(midi.export_bytes(p),midi.export_bytes(self.source))
            self.assertEqual(r["chord_fader_offset_db"],db)
            self.assertIsNone(r["human_preference"])
            source=next(t for t in self.source.tracks if t.id=="track-harmony")
            after=next(t for t in p.tracks if t.id=="track-harmony")
            self.assertAlmostEqual(after.controls["mixer.gain_db"],source.controls["mixer.gain_db"]+db)
            self.assertEqual(source.instrument,after.instrument)
            self.assertEqual(source.effects,after.effects)
        self.assertEqual(original,dumps(self.source))
    def test_arbitrary_or_positive_gain_is_forbidden(self):
        for db in (3.,-10.,-1.,float("nan"),None,"-2"):
            with self.assertRaises(ValidationError):
                chord_gain_candidate(self.source,db)

if __name__=="__main__":unittest.main()
