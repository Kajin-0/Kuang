"""Bounded native source-comparison policy tests; no aesthetic success claims."""
import unittest
from kuang.house_pad_context import compare_native_pad
from kuang.schema import ValidationError

def bands(body,mid):
    return {"band_rms_dbfs":{"body_120_500":body,"mid_500_2000":mid}}

class PadNativeContextTests(unittest.TestCase):
    S1="a"*64
    S2="b"*64
    def assess(self,bass,old,new):
        return compare_native_pad(bass,old,new,baseline_source_sha=self.S1,candidate_source_sha=self.S2)

    def test_c_real_native_case_provisional_eligibility(self):
        r=self.assess(bands(-47.2,-56.4),bands(-35.5,-44.8),bands(-47.5,-50.1))
        self.assertTrue(r["technical_replacement_eligible"])
        self.assertGreater(r["pad_tilt_reduction_db"],6.)
        self.assertEqual(r["perceptual_quality"],"NOT_ESTABLISHED")
        self.assertIsNone(r["mix_winner"])
        self.assertEqual(r,self.assess(bands(-47.2,-56.4),bands(-35.5,-44.8),bands(-47.5,-50.1)))

    def test_quieting_only_not_sufficient(self):
        # A simple -12 dB fader cut preserves the source's spectral tilt.
        r=self.assess(bands(-47,-54),bands(-35,-44),bands(-47,-56))
        self.assertFalse(r["technical_replacement_eligible"])
        self.assertFalse(r["candidate_preserves_midrange_and_reduces_overlap"])

    def test_low_mid_clean_baseline_is_not_replaced(self):
        r=self.assess(bands(-47,-60),bands(-45,-44),bands(-65,-50))
        self.assertFalse(r["severe_original_lower_mid_overlap"])
        self.assertFalse(r["technical_replacement_eligible"])

    def test_alternate_too_quiet_is_not_selected(self):
        r=self.assess(bands(-47,-60),bands(-34,-45),bands(-57,-70))
        self.assertFalse(r["technical_replacement_eligible"])

    def test_alternate_still_overcrowds_bass(self):
        r=self.assess(bands(-47,-60),bands(-34,-45),bands(-40,-48))
        self.assertFalse(r["technical_replacement_eligible"])

    def test_rejects_invalid_source_or_spectrum(self):
        with self.assertRaises(ValidationError):
            compare_native_pad(bands(-47,-60),bands(-34,-45),bands(-48,-50),
                               baseline_source_sha=self.S1,candidate_source_sha=self.S1)
        with self.assertRaises(ValidationError):
            self.assess(bands(-47,-60),bands(float('nan'),-45),bands(-48,-50))
        with self.assertRaises(ValidationError):
            self.assess(bands(-47,-60),bands(-34,-45),{"band_rms_dbfs":{}})

if __name__=="__main__":
    unittest.main()
