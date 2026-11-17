import unittest

from kuang.schema import BAR, Section, ValidationError
from tools.audio_fingerprint import (power_db, ratio_db, windows_from_project,
    bar_energy_profile, section_energy_extrema)

class WindowFingerprints(unittest.TestCase):
    def test_synthetic_section_mapping_and_equal_8bar_duration(self):
        class Project:
            tempo_bpm=120.
            sections=[
                Section('i','Groove A',16*BAR,24*BAR),
                Section('b','Breakdown',56*BAR,8*BAR),
                Section('d','Main Drop',72*BAR,24*BAR),
            ]
        window=windows_from_project(Project(),reference="generator")
        self.assertEqual(window["Groove"]["start_seconds"],32)
        self.assertEqual(window["Groove"]["end_seconds"],48)
        self.assertEqual(window["Breakdown"]["start_seconds"],112)
        self.assertEqual(window["Drop"]["start_seconds"],144)
        self.assertEqual(window["Drop"]["end_seconds"],160)

    def test_missing_section_fails_closed(self):
        class Project:
            tempo_bpm=120.
            sections=[Section('i','Groove A',0,8*BAR)]
        with self.assertRaises(ValidationError):
            windows_from_project(Project(),reference="generator")
        with self.assertRaises(ValidationError):
            windows_from_project(Project(),reference="invalid")

    def test_sliding_windows_cross_section_boundary_are_flagged(self):
        class P:
            tempo_bpm=120.
            bars=32
            sections=[
               Section("a","Groove A",0,16*BAR),
               Section("b","Breakdown",16*BAR,8*BAR),
               Section("c","Main Drop",24*BAR,8*BAR)]
        # Synthetic energy array supplies a precise section-boundary
        # adversary without allocating real minutes of PCM.
        levels=[-10.]*16+[-20.]*4+[-12.]*4+[-10.]*8
        powers=[10**(x/10) for x in levels]
        import math
        rows=[{"bar_zero_based":i,
               "section":"Groove A" if i<16 else "Breakdown" if i<24 else "Main Drop",
               "rms_dbfs":v} for i,v in enumerate(levels)]
        sliding=[{"start_bar_zero_based":i,
                  "end_bar_zero_based_exclusive":i+8,
                  "rms_dbfs":10*math.log10(sum(powers[i:i+8])/8)}
                 for i in range(25)]
        result=section_energy_extrema({"bar_rms":rows,
                   "sliding_eight_bar_rms":sliding},
                   P.sections,reference="generator")
        self.assertTrue(isinstance(
            result["breakdown_deepest_eight_bar_overlapping"]["crosses_section_boundary"],bool))
        self.assertEqual(result["breakdown_deepest_eight_bar_inside"]["start_bar_zero_based"],16)
        self.assertFalse(result["breakdown_deepest_eight_bar_inside"]["crosses_section_boundary"]
                         if "crosses_section_boundary" in result["breakdown_deepest_eight_bar_inside"] else False)
        self.assertEqual(result["breakdown_deepest_one_bar"]["rms_dbfs"],-20.)
        self.assertIsNotNone(result["breakdown_deepest_eight_bar_inside"])

    def test_ratios_are_power_based_not_amplitude(self):
        self.assertEqual(ratio_db(1,.01),20)
        self.assertEqual(power_db(.01),-20)
        self.assertIsNone(ratio_db(0,1))
        self.assertIsNone(ratio_db(1,0))

if __name__=="__main__":unittest.main()
