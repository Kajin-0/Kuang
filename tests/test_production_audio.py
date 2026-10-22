import math
import tempfile
import unittest
import wave
from pathlib import Path

from kuang.production_audio import production_metrics
from kuang.schema import ValidationError


class ProductionAudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def tone(self, hz, *, phase=1, channels=2, frames=8192):
        path = self.root/f'{hz}-{phase}-{channels}-{frames}.wav'
        with wave.open(str(path), 'wb') as stream:
            stream.setparams((channels, 2, 16384, 0, 'NONE', 'uncompressed'))
            data = bytearray()
            for i in range(frames):
                value = round(8192*math.sin(2*math.pi*hz*i/16384))
                data += value.to_bytes(2, 'little', signed=True)
                if channels == 2:
                    data += (value*phase).to_bytes(2, 'little', signed=True)
            stream.writeframes(data)
        return path

    def test_known_tones_have_correct_band_power_rms_and_crest(self):
        for hz, band in ((64, 'sub_20_120'), (256, 'body_120_500'), (1024, 'mid_500_2000'), (4096, 'presence_2000_8000')):
            with self.subTest(hz=hz):
                r = production_metrics(self.tone(hz))
                self.assertGreater(r['spectrum']['band_power_fraction'][band], .999)
                self.assertAlmostEqual(r['rms'], .25/math.sqrt(2), places=4)
                self.assertAlmostEqual(r['crest_db'], 20*math.log10(math.sqrt(2)), places=3)
                self.assertAlmostEqual(sum(r['spectrum']['band_power_fraction'].values()), 1)

    def test_stereo_correlation_and_side_energy_for_mono_and_opposite_phase(self):
        mono = production_metrics(self.tone(1024))['sections']['full']
        opposite = production_metrics(self.tone(1024, phase=-1))['sections']['full']
        self.assertAlmostEqual(mono['stereo_correlation'], 1)
        self.assertEqual(mono['side_rms'], 0)
        self.assertAlmostEqual(opposite['stereo_correlation'], -1)
        self.assertAlmostEqual(opposite['side_rms'], opposite['rms'])

    def test_sections_use_exact_frame_bounds_and_invalid_regions_fail(self):
        p = self.tone(1024)
        r = production_metrics(p, [('intro', 0, .125), ('drop', .25, .5)])
        self.assertEqual(r['sections']['intro']['end_frame'], 2048)
        self.assertEqual(r['sections']['drop']['start_frame'], 4096)
        self.assertAlmostEqual(r['sections']['intro']['rms'], r['sections']['drop']['rms'])
        for regions in ([('bad', -1, .5)], [('bad', 0, 100)], [('full', 0, .25)], [('bad', 0, float('nan'))]):
            with self.assertRaises(ValidationError):
                production_metrics(p, regions)

    def test_silence_short_and_mono_have_explicit_results_or_errors(self):
        silent = production_metrics(self.tone(0))
        self.assertEqual(silent['spectrum']['band_power_fraction']['sub_20_120'], 0)
        self.assertIsNone(silent['crest_db'])
        for p in (self.tone(1024, frames=1024), self.tone(1024, channels=1)):
            with self.assertRaises(ValidationError):
                production_metrics(p)
