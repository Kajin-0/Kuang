import unittest
from copy import deepcopy
from kuang.house_pad_level import recommend_trim,apply_trim,VERSION
from kuang.house_template import template
from kuang.song import rules_plan
from kuang.schema import ValidationError,dumps
from kuang import midi

def levels(spec):
    return {"version":"house-native-section-levels-v1",
            "sections":{k:{"start_seconds":float(i),"end_seconds":float(i+1),
                "window_100ms":{"p95_rms_dbfs":v[0]},
                "window_400ms":{"p95_rms_dbfs":v[1]},
                "sample_peak_dbfs":v[2]}
                for i,(k,v) in enumerate(spec.items())}}

class PadLevelTests(unittest.TestCase):
    def test_c_actual_windows_require_bounded_large_trim(self):
        p=levels({"Intro":(-21.731,-22.706,-11.119),
                  "Breakdown":(-21.53,-22.425,-10.332),
                  "Drop":(-23.138,-22.747,-11.473)})
        h=levels({"Intro":(-32.692,-34.191,-17.374),
                  "Breakdown":(-33.085,-34.436,-20.609),
                  "Drop":(-31.985,-34.187,-19.983)})
        value,receipt=recommend_trim(p,h,["Intro","Breakdown","Drop"])
        self.assertEqual(value,-12.)
        self.assertGreater(receipt["requested_attenuation_db"],12.)
        self.assertTrue(receipt["bounded_at_12db"])
        self.assertEqual(receipt["perceptual_quality"],"NEEDS_LISTENING")
    def test_deep_and_jackin_stay_unchanged(self):
        pairs=[
            ({"Intro":(-30.043,-31.075,-18.852),
              "Breakdown":(-31.635,-31.816,-19.93),
              "Drop":(-30.744,-28.876,-18.338)},
             {"Intro":(-24.71,-24.733,-11.128),
              "Breakdown":(-23.871,-23.73,-10.386),
              "Drop":(-24.217,-27.503,-10.162)}),
            ({"Intro":(-25.25,-24.84,-14.225),
              "Breakdown":(-24.893,-24.74,-13.038),
              "Drop":(-27.69,-26.718,-14.41)},
             {"Intro":(-24.074,-24.736,-11.758),
              "Breakdown":(-23.984,-23.645,-11.513),
              "Drop":(-23.944,-26.38,-11.097)})]
        for a,b in pairs:
            self.assertEqual(recommend_trim(levels(a),levels(b),list(a))[0],0.)
    def test_only_pad_active_sections_count(self):
        from kuang.house_pad_native_level import _active_sections
        spec,_=rules_plan("minimal house in F# minor 16 bars",29)
        p,_=template(spec,profile="minimal",impact_pocket=True,groove_identity_v2=True)
        sections,active=_active_sections(p)
        self.assertEqual(set(active),{"Intro","Breakdown","Drop"})
        self.assertNotIn("Groove",active)
        self.assertEqual(len(sections),4)

    def test_invalid_misaligned_and_missing_stems_rejected(self):
        p=levels({"Intro":(-20,-20,-11)})
        h=levels({"Intro":(-32,-34,-20)})
        with self.assertRaises(ValidationError):
            recommend_trim(p,h,["Outro"])
        with self.assertRaises(ValidationError):
            recommend_trim(p,h,["Intro","Intro"])
        moved=deepcopy(h);moved["sections"]["Intro"]["end_seconds"]=2
        with self.assertRaises(ValidationError):
            recommend_trim(p,moved,["Intro"])
    def test_apply_pad_trim_preserves_original_midi_source_and_other_tracks(self):
        spec,_=rules_plan("minimal house in F# minor 16 bars",29)
        original,_=template(spec,profile="minimal",impact_pocket=True,groove_identity_v2=True)
        before=dumps(original)
        edited=apply_trim(original,-12.)
        self.assertEqual(before,dumps(original))
        self.assertEqual(midi.export_bytes(original),midi.export_bytes(edited))
        old=next(t for t in original.tracks if t.id=="track-pad")
        new=next(t for t in edited.tracks if t.id=="track-pad")
        self.assertEqual(new.controls["mixer.gain_db"],old.controls["mixer.gain_db"]-12)
        a=[x for x in original.automation if x.target_id=="track-pad" and x.parameter_id=="mixer.gain_db"]
        b=[x for x in edited.automation if x.target_id=="track-pad" and x.parameter_id=="mixer.gain_db"]
        self.assertTrue(a and b)
        self.assertEqual([round(y.value-x.value,6) for lane_a,lane_b in zip(a,b) for x,y in zip(lane_a.points,lane_b.points)],[-12.]*sum(len(x.points) for x in a))
        self.assertEqual(dumps(original),dumps(apply_trim(original,0.)))
        with self.assertRaises(ValidationError):
            apply_trim(original,-20.)
if __name__=="__main__":
    unittest.main()
