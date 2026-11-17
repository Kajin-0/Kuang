import unittest
from kuang.house_v3_space_review import review_chord_space
from kuang.schema import ValidationError

class ChordSceneReviewTests(unittest.TestCase):
    def data(self,attack,tail,dry,wet):
        return {"source_midi_unchanged":True,
           "kick_bass_stem_byte_exact":True,"eligible_isolated_onsets":16,
           "attack_change_db":attack,"tail_change_db":tail,
           "chord_to_kick_bass_presence_2k_8k_dry_db":dry,
           "chord_to_kick_bass_presence_2k_8k_wet_db":wet}
    def test_deep_detects_large_tail_even_when_attack_safe(self):
        report=review_chord_space(self.data(.072,6.98,34.463,35.209))
        self.assertTrue(report["requires_source_aware_review"])
        self.assertEqual(report["warnings"],["LARGE_WET_TAIL_GAIN_REVIEW_SOURCE_ARTICULATION"])
        self.assertFalse(report["automatic_global_send_promotion"])
    def test_minimal_relatively_restrained(self):
        report=review_chord_space(self.data(.496,.711,-1.177,-.132))
        self.assertEqual(report["warnings"],[])
        self.assertIsNone(report["automatic_musical_winner"])
    def test_missing_provenance_and_untrusted_metric_fail(self):
        data=self.data(.2,2.,-2.,-1.)
        data["kick_bass_stem_byte_exact"]=False
        with self.assertRaises(ValidationError):review_chord_space(data)
        data["kick_bass_stem_byte_exact"]=True
        data["attack_change_db"]=float("nan")
        with self.assertRaises(ValidationError):review_chord_space(data)
if __name__=="__main__":unittest.main()
