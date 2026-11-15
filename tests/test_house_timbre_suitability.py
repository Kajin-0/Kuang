"""Only feature validation and interpretable review flags, not music ratings."""
import copy
import unittest

from kuang.house_timbre_suitability import review_sources, source_names
from kuang.schema import ValidationError


class RoleTimbreReviewTests(unittest.TestCase):
    SOURCE = {
        "bass": {"low_fraction": .84, "mid_fraction": .155,"high_fraction": .005,
                 "stereo_side_fraction": .69,"tail_ratio": .09,"rms": .08},
        "chord": {"low_fraction": .001, "mid_fraction": .995,"high_fraction": .004,
                  "stereo_side_fraction": .35,"tail_ratio": .58,"rms": .04},
        "pad": {"low_fraction": .28, "mid_fraction": .718,"high_fraction": .002,
                "stereo_side_fraction": .37,"tail_ratio": .45,"rms": .20}
    }

    def test_review_flags_are_explicit_and_do_not_reject_or_rank(self):
        values=copy.deepcopy(self.SOURCE)
        receipt=review_sources(values)
        self.assertEqual(values,self.SOURCE)
        self.assertFalse(receipt["verified_suitability"])
        self.assertIsNone(receipt["winner"])
        self.assertIn("loud_low_pad_requires_kick_bass_context_review",
                      receipt["roles"]["pad"]["review_flags"])
        self.assertIn("bass_stereo_requires_sub_band_mono_measurement",
                      receipt["roles"]["bass"]["review_flags"])
        self.assertIn("long_chord_tail_may_mask_adjacent_rhythmic_parts",
                      receipt["roles"]["chord"]["review_flags"])
        self.assertEqual(receipt,review_sources(values))

    def test_clean_pad_has_no_review_flags(self):
        role={"pad":dict(self.SOURCE["pad"],
                         low_fraction=.0013,mid_fraction=.99838,high_fraction=.00032,
                         rms=.09)}
        receipt=review_sources(role)
        self.assertEqual(receipt["roles"]["pad"]["review_flags"],[])
        self.assertIsNone(receipt["winner"])

    def test_fails_closed_on_bad_observations(self):
        for attr,bad in [("low_fraction",float('nan')),("rms",1.2),
                         ("tail_ratio",-1),("stereo_side_fraction",float('inf'))]:
            v={"bass":dict(self.SOURCE["bass"],**{attr:bad})}
            with self.subTest(attr=attr),self.assertRaises(ValidationError):
                review_sources(v)
        with self.assertRaises(ValidationError):
            source_names({"roles":{},"status":"incomplete"})


if __name__=="__main__":
    unittest.main()
