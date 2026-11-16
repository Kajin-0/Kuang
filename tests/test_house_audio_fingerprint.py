import unittest

from kuang.schema import BAR, Section, ValidationError
from tools.audio_fingerprint import power_db, ratio_db, windows_from_project

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

    def test_ratios_are_power_based_not_amplitude(self):
        self.assertEqual(ratio_db(1,.01),20)
        self.assertEqual(power_db(.01),-20)
        self.assertIsNone(ratio_db(0,1))
        self.assertIsNone(ratio_db(1,0))

if __name__=="__main__":unittest.main()
