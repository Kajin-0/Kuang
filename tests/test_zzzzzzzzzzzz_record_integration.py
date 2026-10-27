"""Opt-in real native144-bar song, actual source/FX/pitch and portable replay."""
import json,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from kuang.schema import load,state_hash
from kuang.groove_record import arrange_groove,audit_record,anchor_project,FORM
from kuang.sample_assets import digest,inventory
from kuang.loudness import measure
from tools.phase24_house import adapter,media,END,WAV
from tools.phase24_verify import pitch,controls
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('KUANG_PHASE24_INTEGRATION')=='1','optional real single144-bar record proof')
class GrooveRecordNativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(os.environ['KUANG_PHASE24_RELEASE']);cls.host=os.environ['KUANG_SOUNDCRAFT'];cls.plugin=os.environ['KUANG_VITALIUM_PLUGIN'];cls.a=adapter(cls.host,cls.plugin);cls.s=load(cls.root/'approved-source.kuang.json');cls.p=load(cls.root/'project/project.kuang.json');cls.assets,cls.patches=media(cls.root/'project',cls.p);cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.local/phase24/tmp');cls.w=Path(cls.temp.name)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_full_score_exact_anchor_sources_signal_graph_and_native_markers(self):
  p,r=arrange_groove(self.s);self.assertEqual(p,self.p);self.assertEqual(r,json.loads((self.root/'composition-receipt.json').read_text()));a=audit_record(self.s,p,r);self.assertEqual(a['longest_kick_free_bars'],8)
  original=ROOT/'artifacts/phase23-house/project/native'
  for tid,path in {**self.assets,**self.patches}.items():self.assertEqual(inventory(path),inventory(original/('assets' if tid in self.assets else 'patches')/tid))
  native=self.a.inspect(self.root/'project/native')['native'];self.assertEqual([t['instrument']['params']['1835232641'] for t in native['tracks'] if t['instrument'] and t['instrument']['plugin'].startswith('vst3:')],[.5]*3)
  self.assertEqual([(m['name'],m['start'],m['end']) for m in native['markers']],[(name,round(b*4*60/126*48000),round((b+n)*4*60/126*48000)) for _,name,b,n in FORM])
  q=anchor_project(self.s,p);self.a.export(q,self.assets,self.patches,self.w/'anchor');self.a.render(self.w/'anchor',self.w/'anchor.wav',end_seconds=16*4*60/126+5);self.assertEqual(digest(self.w/'anchor.wav'),digest(ROOT/'artifacts/phase23-house/Phase23-no-melody-native.wav'))
 def test_actual_new_upper_registers_chords_and_C2_both_hosts(self):
  before=inventory(self.root);r=pitch(self.root,self.w/'pitch',self.host,self.plugin,os.environ['KUANG_VITALIUM_HOST_PYTHON']);self.assertEqual(r['native_pitch_center'],.5);self.assertEqual(before,inventory(self.root))
 def test_same_input_native_filter_plate_and_echo_controls_no_prefix_leak(self):
  before=inventory(self.root);r=controls(self.root,self.host,self.plugin);self.assertEqual(before,inventory(self.root));self.assertTrue(r['controls']['echo']['closed_six_bar_prefix_PCM_exact'])
  for v in r['controls'].values():self.assertTrue(v['same_input_notes_exact']);self.assertGreater(v['aligned_PCM_difference']['difference_to_original_rms_ratio'],.001)
 def test_full_native_state_and_144_bar_PCM_reopen_format_and_integrity(self):
  self.a.save(self.root/'project/native',self.w/'saved');self.assertEqual(self.a.inspect(self.root/'project/native')['native'],self.a.inspect(self.w/'saved')['native']);self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END);self.assertEqual(digest(self.root/WAV),digest(self.w/'repeat.wav'))
  m=measure(self.root/WAV,library=os.environ.get('KUANG_EBUR128'));self.assertEqual((m['sample_rate'],m['channels'],m['bits_per_sample'],m['clipped_samples']),(48000,2,24,0));self.assertGreater(m['rms'],0);self.assertAlmostEqual(m['duration_seconds'],END,delta=1/48000)
  v=json.loads((self.root/'verification.json').read_text());self.assertGreater(v['spatial']['bands']['low_20_120']['mono_energy_retention'],.999);self.assertFalse(v['mastering']);self.assertEqual(v['human_preference'],'unreviewed');self.assertEqual([p.name for p in self.root.glob('*.wav')],[WAV])
 def test_ZIP_single_record_extracted_replay_original_paths_hidden_PCM_exact(self):
  before=inventory(self.root)
  with zipfile.ZipFile(self.root/'phase24-melody-free-house.zip') as z:
   self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'});self.assertEqual([n for n in z.namelist() if '/' not in n and n.endswith('.wav')],[WAV]);self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
  clone=self.w/'external/vitalium.vst3';clone.parent.mkdir();shutil.copytree(self.plugin,clone);hidden=[]
  try:
   for p in (self.root/'project/native',ROOT/'artifacts/phase23-house/project/native',Path(self.plugin)):
    target=p.with_name(p.name+'-phase24-hidden');self.assertFalse(target.exists());p.rename(target);hidden.append((p,target))
   r=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(clone)],cwd=self.w,capture_output=True,text=True,timeout=600);self.assertEqual(r.returncode,0,r.stderr[-4000:]);self.assertTrue(json.loads(r.stdout)['PCM_exact'])
  finally:
   for p,target in reversed(hidden):target.rename(p)
  self.assertEqual(before,inventory(self.root))
