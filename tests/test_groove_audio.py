import math
import tempfile
import unittest
import wave
from pathlib import Path

from kuang.groove_audio import low_end_interaction,stem_sum_error,transient_metrics
from kuang.schema import ValidationError


class GrooveAudioTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def wav(self,name,values,width=3,rate=48000,channels=2):
        p=self.root/name
        with wave.open(str(p),'wb') as s:
            s.setparams((channels,width,rate,0,'NONE','PCM'))
            s.writeframes(b''.join(v.to_bytes(width,'little',signed=True) for v in values))
        return p

    def test_grid_transient_windows_have_known_energy(self):
        p=self.wav('dc.wav',[1<<21]*96000)
        r=transient_metrics(p,120,2)
        for w in r['windows'].values():self.assertEqual(w['median_rms'],.25)
        with self.assertRaises(ValidationError):transient_metrics(p,120,10)
        with self.assertRaises(ValidationError):transient_metrics(p,float('nan'),2)

    def test_identical_and_inverted_low_band_stems_have_expected_interference(self):
        values=[round((1<<20)*math.sin(2*math.pi*64*i/48000)) for i in range(48000) for _ in range(2)]
        a=self.wav('a.wav',values);b=self.wav('b.wav',[-v for v in values])
        same=low_end_interaction(a,a);opposite=low_end_interaction(a,b)
        self.assertAlmostEqual(same['correlation'],1)
        self.assertAlmostEqual(same['interference_db'],10*math.log10(2))
        self.assertAlmostEqual(opposite['correlation'],-1)
        self.assertAlmostEqual(opposite['summed_to_independent_energy_ratio'],0)

    def test_independent_stem_sum_exact_and_quantization_error_all_widths(self):
        for width in (2,3,4):
            a=self.wav('a.wav',[100,-100]*10,width)
            b=self.wav('b.wav',[200,-200]*10,width)
            mix=self.wav('mix.wav',[300,-300]*10,width)
            self.assertEqual(stem_sum_error(mix,[a,b])['peak_error_lsb'],0)
            mix=self.wav('mix.wav',[302,-302]*10,width)
            self.assertEqual(stem_sum_error(mix,[a,b])['peak_error_lsb'],2)

    def test_wrong_formats_missing_stems_and_truncated_audio_fail(self):
        a=self.wav('a.wav',[100,-100]*100)
        b=self.wav('b.wav',[100,-100]*100,rate=44100)
        with self.assertRaises(ValidationError):low_end_interaction(a,b)
        with self.assertRaises(ValidationError):stem_sum_error(a,[b])
        with self.assertRaises(ValidationError):stem_sum_error(a,[])
        b=self.wav('b.wav',[100,-100]*100);b.write_bytes(b.read_bytes()[:-4])
        with self.assertRaises(ValidationError):stem_sum_error(a,[b])
