import unittest
from kuang.house_chord_stimulus_v1 import chord_stimulus
from kuang.house_full_arranger import arrange_full_song
from kuang.house_template import template
from kuang.song import rules_plan
from kuang.schema import ValidationError,dumps, BAR
from kuang.house_note_envelope_v1 import _note_onsets


class ChordStimulusV1Tests(unittest.TestCase):
    def source(self,profile):
        p,_=rules_plan(f"{profile} house in C minor, 32 bars, 124 bpm",71)
        short,_=template(p,profile=profile,impact_pocket=True,groove_identity_v2=True)
        full,_=arrange_full_song(short,profile=profile,bars=128,seed=71)
        return full

    def test_extracted_real_voicing_and_phrasing_is_deterministic(self):
        for profile in ("straight","jackin","minimal","deep"):
            with self.subTest(profile=profile):
                source=self.source(profile)
                frozen=dumps(source)
                a,receipt=chord_stimulus(source)
                b,again=chord_stimulus(source)
                self.assertEqual(dumps(source),frozen)
                self.assertEqual(dumps(a),dumps(b))
                self.assertEqual(receipt,again)
                self.assertEqual(receipt["repeated_events"],4)
                self.assertGreaterEqual(len(receipt["source_pitches"]),3)
                groups,_,_=_note_onsets(a,"harmony","Groove A",8)
                self.assertEqual(len(groups),4)
                self.assertEqual(len(set(receipt["source_pitches"])),len(receipt["source_pitches"]))
                for t in a.tracks:
                    if t.kind=="midi":
                        self.assertEqual(t.controls["mixer.mute"],
                                         0 if t.id=="track-harmony" else 1)

    def test_no_source_chord_fails_closed(self):
        src=self.source("jackin")
        track=next(t for t in src.tracks if t.id=="track-harmony")
        track.clips=[]
        with self.assertRaises(ValidationError):
            chord_stimulus(src)

if __name__=="__main__":
    unittest.main()
