import unittest
from kuang.house_producer_evidence_policy_v1 import decide_chord_trial
from kuang.schema import ValidationError

class ProducerEvidencePolicy(unittest.TestCase):
    @staticmethod
    def fake():
        rows=[]
        for name,db in [("A-original",None),("B-chords-minus2db",-2.),("C-chords-minus3db",-3.)]:
            rows.append({"variant":name,"native_same_bounce_path":True,"midi_locked":True,
                         "clipped_samples":0,"true_peak_dbtp":-5.2,
                         "matched_lufs":-24.59,"candidate_canonical_hash":name,
                         "source_sha256":"x"*64,"chord_gain_offset_db":db})
        return {"version":"house-chord-cohesion-native-ab-v1","song":"07",
                "source_original_canonical_hash":"hash","candidates":rows}
    def test_explicit_human_preference_wins(self):
        p=self.fake()
        self.assertEqual(decide_chord_trial(p,preferred_variant="A-original")["status"],
                         "USER_APPROVED_FOR_THIS_SONG")
    def test_inconclusive_with_prior_too_loud_feedback_chooses_smaller_trim(self):
        p=self.fake()
        r=decide_chord_trial(p,reported_problem="chords_too_loud")
        self.assertEqual(r["chosen_variant"],"B-chords-minus2db")
        self.assertEqual(r["status"],"PROVISIONAL_AGENT_CHOICE")
        self.assertFalse(r["listening_quality_proven"])
        self.assertFalse(r["promote_to_global_house_default"])
    def test_absent_evidence_preserves_original(self):
        self.assertEqual(decide_chord_trial(self.fake())["chosen_variant"],"A-original")
    def test_rejects_unsafe_or_fabricated_measurements(self):
        for key,bad in (("true_peak_dbtp",0.),("clipped_samples",5),
                        ("matched_lufs",float("nan"))):
            p=self.fake();p["candidates"][1][key]=bad
            with self.assertRaises(ValidationError):decide_chord_trial(p)
        with self.assertRaises(ValidationError):
            decide_chord_trial(self.fake(),preferred_variant="never-rendered")

if __name__=="__main__":unittest.main()
