import unittest
from kuang.house_context_palette_v2 import (VERSION,chord_intent,review_source,
                                              assess_alternative)
from kuang.house_template import template
from kuang.song import rules_plan
from kuang.schema import ValidationError

class ContextPaletteV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s,_=rules_plan("straight house in F minor, 120 bpm",67)
        cls.project,_=template(s,profile="straight",groove_identity_v2=True,impact_pocket=True)
        cls.stems={"kick":{"rms_dbfs":-29.64},"bass":{"rms_dbfs":-36.06},
                   "harmony":{"rms_dbfs":-64.07}}
        cls.chord_sha="1"*64
    def review(self,**kwargs):
        config={"prompt":"straight house with wide sustained chords","profile":"straight",
                "stems":self.stems,"source_verified":True,"source_sha256":self.chord_sha,
                "source_name":"private verified preset","runner_up_count":2}
        config.update(kwargs)
        return review_source(self.project,**config)
    def test_prompt_intent_explicit_does_not_assume_all_chords_should_be_loud(self):
        self.assertEqual(chord_intent("jackin house, short piano house stabs","jackin"),"percussive_stabs")
        self.assertEqual(chord_intent("minimal house with spacey sustained chords","minimal"),"prominent_sustained")
        self.assertEqual(chord_intent("minimal house with a sub and sparse hats","minimal"),"unspecified")
    def test_real_reference_song01_flags_role_contradiction_without_auto_swap(self):
        r=self.review()
        self.assertEqual(r["version"],VERSION)
        self.assertEqual(r["action"],"AUDITION_VERIFIED_CHORD_ALTERNATIVES")
        self.assertEqual(r["max_candidates"],2)
        self.assertFalse(r["source_replaced"])
        self.assertAlmostEqual(r["chord_minus_kick_rms_db"],-34.43)
    def test_short_stabs_are_preserved_even_if_quiet(self):
        r=self.review(prompt="jackin house, short piano house stabs",profile="jackin")
        self.assertEqual(r["action"],"RETAIN_WITH_ARTICULATION_REVIEW")
        self.assertEqual(r["max_candidates"],0)
    def test_healthy_stems_and_bounded_candidates(self):
        stems={**self.stems,"harmony":{"rms_dbfs":-45}}
        self.assertEqual(self.review(stems=stems)["action"],"KEEP_SOURCE")
        self.assertEqual(self.review(runner_up_count=0)["max_candidates"],0)
    def test_native_fullmix_eligibility_not_aesthetic_choice(self):
        review=self.review()
        a=dict(integrated_lufs=-27.6,true_peak_dbtp=-5.6,clipped_samples=0,
               presence_1k_4k_rel_30_250_db=-15.671,
               lowmid_250_1k_rel_30_250_db=-12.014,side_mid_db=-37.874)
        b=dict(integrated_lufs=-24.12,true_peak_dbtp=-5.637,clipped_samples=0,
               presence_1k_4k_rel_30_250_db=-6.889,
               lowmid_250_1k_rel_30_250_db=-4.148,side_mid_db=-22.214)
        p=assess_alternative(review,candidate_sha256="2"*64,candidate_source_verified=True,
                             original_mix=a,candidate_mix=b)
        self.assertEqual(p["technical_status"],"ELIGIBLE_FOR_GAIN_MATCHED_LISTENING")
        self.assertTrue(p["large_source_level_difference"])
        self.assertFalse(p["automatic_winner_selected"])
        self.assertEqual(p["native_mix_delta"]["presence_1k_4k_rel_30_250_db"],8.782)
        for changed in ({**b,"true_peak_dbtp":.1},{**b,"clipped_samples":5}):
            bad=assess_alternative(review,candidate_sha256="2"*64,candidate_source_verified=True,
                                   original_mix=a,candidate_mix=changed)
            self.assertEqual(bad["technical_status"],"REJECT_NATIVE_AUDIO_SAFETY")
    def test_unverified_or_incomplete_native_data_fail_closed(self):
        with self.assertRaises(ValidationError):self.review(source_verified=False)
        with self.assertRaises(ValidationError):self.review(stems={"kick":{"rms_dbfs":0}})
        with self.assertRaises(ValidationError):self.review(source_sha256="short")

if __name__=="__main__":unittest.main()
