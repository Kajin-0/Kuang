"""Actual Phase17 native signal graph, controls, pitch and portable full song."""
import json,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from kuang.schema import load,dumps
from kuang.mix_polish import polished_mix
from kuang.sound_palette import performance
from kuang.midi import export_bytes
from kuang.sample_assets import digest,inventory
from kuang.loudness import measure
from tools.phase17_house import adapter,END,AUDIO
from tools.phase17_verify import pitch_gate,controls
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('KUANG_PHASE17_INTEGRATION')=='1','opt in to actual reviewed host and complete Phase17 bundle')
class MixIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(os.environ['KUANG_PHASE17_RELEASE']);self.host=os.environ['KUANG_SOUNDCRAFT'];self.plugin=os.environ['KUANG_VITALIUM_PLUGIN']
        scratch=ROOT/'.local/phase17/tests';scratch.mkdir(parents=True,exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.w=Path(self.tmp.name);self.a=adapter(self.host,self.plugin)
    def tearDown(self):self.tmp.cleanup()
    def test_actual_centred_G4_Eb4_C2_and_poly_Cm9_after_native_reload(self):
        r=pitch_gate(self.root,self.w/'pitch',self.host,self.plugin)
        self.assertEqual(r['native_input_1835232641'],.5);self.assertTrue(r['saved_reopened_PCM_exact'])
    def test_actual_aux_on_off_echo_trails_closed_send_and_gain_duck(self):
        r=controls(self.root,self.w/'controls',self.host,self.plugin)
        self.assertLess(r['echo']['closed_send_RMS_ratio'],.003)
        self.assertLess(r['return_duck']['attenuated_window_power_ratio'],1)
        self.assertAlmostEqual(r['return_duck']['recovered_body_power_ratio'],1,delta=.01)
    def test_full_performance_patch_sample_state_mixer_graph_and_PCM_exact(self):
        before=inventory(self.root);p=load(self.root/'A/project.kuang.json');q=load(self.root/'B/project.kuang.json');expected,_=polished_mix(p)
        self.assertEqual(dumps(q),dumps(expected));self.assertEqual(export_bytes(p),export_bytes(q))
        for t,u in zip(p.tracks,q.tracks):self.assertEqual((t.instrument,t.clips),(u.instrument,u.clips))
        for t in p.tracks:
            if t.instrument and t.instrument.plugin_ref.startswith('vst3:'):
                self.assertEqual(inventory(self.root/'A/native/patches'/t.id),inventory(self.root/'B/native/patches'/t.id))
            if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler':
                self.assertEqual(inventory(self.root/'A/native/assets'/t.id),inventory(self.root/'B/native/assets'/t.id))
        native=self.a.inspect(self.root/'B/native')['native'];self.assertEqual(len(native['tracks']),17);self.assertEqual(len(native['busses']),4);self.assertEqual(len(native['markers']),6)
        self.a.save(self.root/'B/native',self.w/'saved');self.assertEqual(native,self.a.inspect(self.w/'saved')['native'])
        self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END);self.assertEqual(digest(self.w/'repeat.wav'),digest(self.root/AUDIO['B']))
        self.assertEqual(digest(self.root/AUDIO['A']),digest(ROOT/'artifacts/phase16-house/B-Phase16-palette-native.wav'))
        m=[measure(x,library=os.environ.get('KUANG_EBUR128')) for x in sorted((self.root/'listening').glob('*.wav'))]
        self.assertEqual(len(m),2);self.assertAlmostEqual(m[0]['integrated_lufs'],m[1]['integrated_lufs'],delta=.01)
        for x in m:self.assertEqual((x['sample_rate'],x['channels'],x['bits_per_sample']),(48000,2,24));self.assertEqual(x['clipped_samples'],0)
        v=json.loads((self.root/'verification.json').read_text());self.assertGreater(v['spatial']['B']['bands']['high_over_500']['side_to_mid_power_ratio'],.07)
        self.assertGreater(v['spatial']['B']['bands']['low_20_120']['mono_energy_retention'],.9999)
        self.assertGreater(v['spatial']['B']['mono_sum']['rms_loss_db'],-.25);self.assertEqual(v['candidate_preference'],'unreviewed')
        self.assertEqual(inventory(self.root),before)
    def test_zip_extracted_replay_relative_media_and_relocated_plugin(self):
        before=inventory(self.root)
        with zipfile.ZipFile(self.root/'phase17-house-listening.zip') as z:
            self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'})
            self.assertEqual(len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')]),2)
            self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
        moved=self.w/'external/vitalium.vst3';moved.parent.mkdir();shutil.copytree(self.plugin,moved)
        hidden=[]
        try:
            for path in (self.root/'B/native',Path(self.plugin)):
                target=path.with_name(path.name+'-phase17-hidden');self.assertFalse(target.exists());path.rename(target);hidden.append((path,target))
            result=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),
                '--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(moved)],cwd=self.w,capture_output=True,text=True,timeout=240,check=True)
            self.assertTrue(json.loads(result.stdout)['PCM_exact'])
        finally:
            for path,target in reversed(hidden):target.rename(path)
        self.assertEqual(inventory(self.root),before)
