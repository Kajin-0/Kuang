import hashlib
import json
import math
import tempfile
import unittest
import wave
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from kuang.audio import analyze_wav
from kuang.loudness import KBlocks,TruePeak,k_coefficients,measure
from kuang.mastering import apply_master,attenuate,file_hash,match_lufs,validate_recipe
from kuang.schema import ValidationError
from loudness_vectors import RECIPES,write_vector

SCRATCH=Path(__file__).resolve().parents[1]/'.local/phase9'


class LoudnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SCRATCH.mkdir(parents=True,exist_ok=True);cls.temp=tempfile.TemporaryDirectory(dir=SCRATCH)
        cls.addClassCleanup(cls.temp.cleanup);cls.root=Path(cls.temp.name)
        cls.golden=json.loads((Path(__file__).parent/'fixtures/loudness-golden.json').read_text())
        cls.measured={}
        for name in RECIPES:
            p=cls.root/(name+'.wav');write_vector(p,name);cls.measured[name]=measure(p)

    def test_independent_libebur128_golden_loudness_and_true_peak_vectors(self):
        for name,m in self.measured.items():
            with self.subTest(vector=name):
                golden=self.golden['vectors'][name]
                self.assertEqual(file_hash(self.root/(name+'.wav')),golden['input_sha256'])
                for key,tolerance in (('integrated_lufs',.01),('true_peak_dbtp',.01)):
                    if golden[key] is None:self.assertIsNone(m[key])
                    else:self.assertAlmostEqual(m[key],golden[key],delta=tolerance)

    def test_ebu_described_steady_stereo_and_mono_calibration(self):
        self.assertAlmostEqual(self.measured['stereo-1k']['integrated_lufs'],-23,delta=.1)
        self.assertAlmostEqual(self.measured['mono-1k']['integrated_lufs'],-26.0103,delta=.1)
        self.assertAlmostEqual(self.measured['stereo-1k']['integrated_lufs']-self.measured['mono-1k']['integrated_lufs'],10*math.log10(2),places=9)

    def test_ebu_described_intersample_and_overfull_analytic_peaks(self):
        for name in ('tp15','tp16-intersample','tp17','tp18'):
            self.assertAlmostEqual(self.measured[name]['true_peak_dbtp'],20*math.log10(.5),delta=.4)
        m=self.measured['tp16-intersample']
        self.assertGreater(m['true_peak_dbtp']-m['sample_peak_dbfs'],2.9)
        self.assertGreater(self.measured['tp19-overfull']['true_peak_dbtp'],2.8)
        self.assertLess(self.measured['tp19-overfull']['sample_peak_dbfs'],0)

    def test_silence_absolute_relative_gating_and_complete_block_rules(self):
        for name in ('silence','quiet-absolute-gate','short-block'):
            self.assertIsNone(self.measured[name]['integrated_lufs'])
        self.assertEqual(self.measured['stereo-1k']['complete_blocks'],9)
        m=self.measured['relative-gate']
        self.assertLess(m['relative_pass_blocks'],m['absolute_pass_blocks'])
        self.assertGreater(m['integrated_lufs'],-22)
        self.assertLess(m['relative_gate_lufs'],m['integrated_lufs']-8)

    def test_eight_x_fir_and_boundary_drain_not_linear_interpolation(self):
        path=self.root/'tp16-intersample.wav';m=measure(path,oversample=8)
        self.assertEqual(m['oversample'],8);self.assertEqual(m['fir_taps'],97)
        self.assertAlmostEqual(m['true_peak_dbtp'],self.measured['tp16-intersample']['true_peak_dbtp'],delta=.05)
        p=TruePeak(1,4);p.add([.8]);self.assertGreaterEqual(p.finish(),.8)
        # Constant input reconstructs with near-unity DC; phase 0 is cardinal.
        p=TruePeak(1,4)
        for _ in range(30):p.add([.1])
        self.assertAlmostEqual(sum(c for _,c in p.phases[0]),1,places=10)
        self.assertTrue(all(abs(sum(c for _,c in phase)-1)<.002 for phase in p.phases))

    def test_published_48k_k_weighting_coefficients(self):
        shelf,high=k_coefficients(48000)
        for a,b in zip(shelf,(1.53512485958697,-2.69169618940638,1.19839281085285,-1.69065929318241,.73248077421585)):
            self.assertAlmostEqual(a,b,places=12)
        self.assertEqual(high[:3],(1,-2,1))
        self.assertAlmostEqual(high[3],-1.99004745483398,places=12)

    def test_invalid_formats_factors_rates_and_explicit_missing_reference_fail_closed(self):
        for factor in (1,2,16,4.0,True):
            with self.assertRaises(ValidationError):measure(self.root/'stereo-1k.wav',oversample=factor)
        for rate in (0,48000.0,4000,300000):
            with self.assertRaises(ValidationError):k_coefficients(rate)
        with self.assertRaises(ValidationError):measure(self.root/'stereo-1k.wav',library=self.root/'missing.so')
        with self.assertRaises(ValidationError):measure(self.root/'stereo-1k.wav',library='/bin/true',oversample=8)
        p=self.root/'three-channel.wav'
        with wave.open(str(p),'wb') as w:w.setparams((3,3,48000,0,'NONE','not compressed'));w.writeframes(b'\0'*4800*9)
        with self.assertRaises(ValidationError):measure(p)

    def test_lufs_match_is_measured_constant_attenuation_and_no_clobber(self):
        source=self.root/'stereo-1k.wav';before=file_hash(source);dest=self.root/'matched.wav'
        r=match_lufs(source,dest,-27)
        self.assertLessEqual(r['gain_db'],0);self.assertLess(abs(r['error_lu']),.001)
        self.assertEqual(file_hash(source),before)
        m=analyze_wav(dest);original=analyze_wav(source)
        self.assertAlmostEqual(m['rms_dbfs']-original['rms_dbfs'],r['gain_db'],places=4)
        with self.assertRaises(ValidationError):match_lufs(source,dest,-27)
        with self.assertRaises(ValidationError):match_lufs(source,self.root/'boost.wav',-10)
        with self.assertRaises(ValidationError):match_lufs(self.root/'silence.wav',self.root/'silent-match.wav',-27)

    def test_frozen_master_recipe_exact_repeat_linked_compression_and_input_preservation(self):
        source=self.root/'stereo-1k.wav';before=file_hash(source)
        recipe={'version':'gentle-master-1','input_sha256':before,'threshold_dbfs':-30,
                'ratio':1.3,'attack_ms':15,'release_ms':150,'gain_db':0,'ceiling_dbtp':-1.2}
        a,b=self.root/'master-a.wav',self.root/'master-b.wav'
        r=apply_master(source,a,recipe);apply_master(source,b,recipe)
        self.assertEqual(file_hash(a),file_hash(b));self.assertEqual(file_hash(source),before)
        self.assertGreater(r['maximum_reduction_db'],1);self.assertLess(r['maximum_reduction_db'],3)
        self.assertFalse(r['native_editable']);self.assertLess(r['rms_gain_db'],0)
        m=analyze_wav(a);self.assertEqual(m['frames'],analyze_wav(source)['frames']);self.assertEqual(m['clipped_samples'],0)
        with self.assertRaises(ValidationError):apply_master(source,a,recipe)

    def test_master_recipe_injection_bounds_and_wrong_source_hash_fail_closed(self):
        source=self.root/'stereo-1k.wav'
        base={'version':'gentle-master-1','input_sha256':file_hash(source),'threshold_dbfs':-20,
              'ratio':1.3,'attack_ms':15,'release_ms':150,'gain_db':0,'ceiling_dbtp':-1.2}
        for key,value in (('exec','bad'),('ratio',8),('attack_ms',0),('gain_db',13),('gain_db',float('nan')),('ceiling_dbtp',0)):
            r={**base,key:value}
            with self.assertRaises(ValidationError):validate_recipe(r)
        dest=self.root/'wrong-input.wav'
        with self.assertRaises(ValidationError):apply_master(source,dest,{**base,'input_sha256':'0'*64})
        self.assertFalse(dest.exists())
        import os
        original_link=os.link
        def race(source,target):
            Path(target).write_bytes(b'other writer')
            return original_link(source,target)
        racing=self.root/'racing.wav'
        with patch('kuang.mastering.os.link',side_effect=race):
            with self.assertRaises(FileExistsError):apply_master(source,racing,base)
        self.assertEqual(racing.read_bytes(),b'other writer')
        self.assertFalse(any(p.name.startswith(('.kuang-master-','.kuang-gain-')) for p in self.root.iterdir()))
