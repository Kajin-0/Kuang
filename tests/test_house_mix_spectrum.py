"""No-host FFT band energy tests, including sampled kick/bass-like tones."""
import math
import tempfile
import unittest
import wave
from pathlib import Path

from kuang.house_mix_spectrum import band_rms, role_spectral_diagnostics
from kuang.schema import ValidationError


def tone(path,frequency,*,amp=.1,rate=48000,seconds=.5):
    with wave.open(str(path),"wb") as w:
        w.setframerate(rate);w.setnchannels(2);w.setsampwidth(3)
        block=bytearray()
        for n in range(round(seconds*rate)):
            v=int(amp*(2**23-1)*math.sin(2*math.pi*frequency*n/rate))
            block.extend(v.to_bytes(3,"little",signed=True)*2)
        w.writeframes(block)


class BandRmsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()

    def test_known_tones_have_correct_bands_and_absolute_levels(self):
        bands={70:"sub_20_120",220:"body_120_500",
               1000:"mid_500_2000",4000:"presence_2000_8000",
               12000:"air_8000_nyquist"}
        for f,expected in bands.items():
            with self.subTest(freq=f):
                p=self.root/f"{f}.wav"
                tone(p,f)
                result=band_rms(p,{"start_seconds":.05,"end_seconds":.45},windows=8)
                self.assertGreater(result["band_power_fraction"][expected],.96)
                # 0.1 sine wave has ~ -23.01 dBFS RMS, frequency bins leak
                # a little, and 20 Hz HP-like diagnostic excludes DC.
                self.assertAlmostEqual(result["band_rms_dbfs"][expected],
                                       20*math.log10(.1/math.sqrt(2)),delta=.4)

    def test_real_band_deltas_are_not_global_rms_equivalence(self):
        names={"kick":70,"bass":100,"chords":400}
        results={}
        for role,f in names.items():
            p=self.root/(role+".wav")
            tone(p,f)
            results[role]=band_rms(p,{"start_seconds":0,"end_seconds":.5},windows=8)
        summary=role_spectral_diagnostics(results)
        self.assertEqual(summary["quality_improvement_established"],False)
        self.assertGreater(summary["chord_sub_fraction"],0)
        self.assertIn("chords_vs_bass_body_120_500_db",summary)
        self.assertIn("bass_vs_kick_sub_20_120_db",summary)

    def test_fail_closed_on_invalid_regions_and_sources(self):
        p=self.root/"a.wav";tone(p,100)
        for region in ({"start_seconds":1,"end_seconds":2},
                       {"start_seconds":.5,"end_seconds":0},
                       {"start_seconds":float("nan"),"end_seconds":.5}):
            with self.subTest(region=region):
                with self.assertRaises(ValidationError):
                    band_rms(p,region)
        with self.assertRaises(ValidationError):
            band_rms(p,{"start_seconds":0,"end_seconds":.5},windows=100)
        with self.assertRaises(ValidationError):
            role_spectral_diagnostics({"kick":{}})
