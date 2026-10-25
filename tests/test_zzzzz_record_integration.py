"""Actual full extended-record graph, tuning, performance and portable replay."""
import os,json,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from dataclasses import asdict
from kuang.schema import load,dumps
from kuang.house_composition import compose_record
from kuang.composition_analysis import audit_composition,event_rows
from kuang.midi import export_bytes
from kuang.sample_assets import inventory,digest
from kuang.loudness import measure
from tools.phase18_house import adapter,media,END,AUDIO,assert_audit
from tools.phase18_verify import pitch_gate,gestures
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('KUANG_PHASE18_INTEGRATION')=='1','opt in to actual pinned host and complete Phase18 bundle')
class RecordIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.root=Path(os.environ['KUANG_PHASE18_RELEASE']);self.host=os.environ['KUANG_SOUNDCRAFT'];self.plugin=os.environ['KUANG_VITALIUM_PLUGIN']
  scratch=ROOT/'.local/phase18/tests';scratch.mkdir(parents=True,exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.w=Path(self.tmp.name);self.a=adapter(self.host,self.plugin)
 def tearDown(self):self.tmp.cleanup()
 def test_actual_all_new_pitches_six_poly_voicings_and_reloaded_PCM(self):
  r=pitch_gate(self.root,self.w/'pitch',self.host,self.plugin)
  self.assertGreaterEqual(len(r['chords']),6);self.assertEqual(r['native_synthetic_MIDI_input_1835232641'],.5)
  self.assertTrue(all(x['native_state_and_PCM_reload_exact'] for x in r['cases'].values()))
 def test_actual_new_filter_performance_and_pre_return_gap(self):
  r=gestures(self.root,self.w/'gestures',self.host,self.plugin)
  self.assertLess(r['early_rebuild_2_8k_power_performed_over_static'],.9);self.assertLess(r['gap_over_return_power'],.4)
  self.assertGreater(r['different_PCM_phrase_windows'],18)
 def test_complete_note_lineage_instruments_graph_native_state_and_PCM_reopen(self):
  before=inventory(self.root);old=load(self.root/'source/phase17-approved.kuang.json');p=load(self.root/'B/project.kuang.json');expected,r=compose_record(old)
  self.assertEqual(dumps(expected),dumps(p));self.assertEqual(r,json.loads((self.root/'composition-receipt.json').read_text()));assert_audit(audit_composition(old,p,r))
  for x,y in zip(old.tracks,p.tracks):
   a=asdict(x);b=asdict(y);a.pop('clips');b.pop('clips');self.assertEqual(a,b)
  self.assertNotEqual(export_bytes(old),export_bytes(p));self.assertEqual((self.root/'B/song.mid').read_bytes(),export_bytes(p))
  source=ROOT/'artifacts/phase17-house/B';assets,patches=media(source,p)
  for tid,path in assets.items():self.assertEqual(inventory(path),inventory(self.root/'B/native/assets'/tid))
  for tid,path in patches.items():self.assertEqual(inventory(path),inventory(self.root/'B/native/patches'/tid))
  n=self.a.inspect(self.root/'B/native')['native'];self.assertEqual((len(n['tracks']),len(n['busses']),len(n['markers'])),(17,4,8))
  self.a.save(self.root/'B/native',self.w/'saved');self.assertEqual(n,self.a.inspect(self.w/'saved')['native'])
  self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END);self.assertEqual(digest(self.w/'repeat.wav'),digest(self.root/AUDIO['B']))
  self.assertEqual(inventory(self.root),before)
 def test_real_complete_different_duration_loudness_matched_audio_and_sections(self):
  m=[measure(x,library=os.environ.get('KUANG_EBUR128')) for x in sorted((self.root/'listening').glob('*.wav'))]
  self.assertEqual(len(m),2);self.assertAlmostEqual(m[0]['integrated_lufs'],m[1]['integrated_lufs'],delta=.01)
  self.assertAlmostEqual(m[0]['duration_seconds'],64*4*60/126+5,delta=1/48000);self.assertAlmostEqual(m[1]['duration_seconds'],END,delta=1/48000)
  for x in m:self.assertEqual((x['sample_rate'],x['bits_per_sample'],x['channels']),(48000,24,2));self.assertEqual(x['clipped_samples'],0);self.assertGreater(x['rms'],0)
  v=json.loads((self.root/'verification.json').read_text());self.assertTrue(v['A_PCM_exact']);self.assertEqual(v['candidate_preference'],'unreviewed')
  self.assertLess(v['sections_B']['Space and suspended answer']['rms'],v['sections_B']['Final return A prime']['rms']*.6)
  self.assertGreater(v['spatial_B']['bands']['high_over_500']['side_to_mid_power_ratio'],.03);self.assertGreater(v['spatial_B']['bands']['low_20_120']['mono_energy_retention'],.9999)
  self.assertGreater(v['spatial_B']['mono_sum']['rms_loss_db'],-.25);self.assertEqual(v['spatial_B']['last_250ms']['peak'],0)
  self.assertEqual(digest(self.root/AUDIO['A']),digest(ROOT/'artifacts/phase17-house/B-Phase17-mix-native.wav'))
 def test_zip_portable_full_record_replay_original_media_and_plugin_hidden(self):
  before=inventory(self.root)
  with zipfile.ZipFile(self.root/'phase18-house-listening.zip') as z:
   self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'})
   self.assertEqual(len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')]),2)
   self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
  moved=self.w/'external/vitalium.vst3';moved.parent.mkdir();shutil.copytree(self.plugin,moved);hidden=[]
  try:
   for path in (self.root/'B/native',Path(self.plugin)):
    target=path.with_name(path.name+'-phase18-hidden');self.assertFalse(target.exists());path.rename(target);hidden.append((path,target))
   result=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--workspace',str(ROOT),'--out',str(self.w/'replay'),'--soundcraft',self.host,'--plugin',str(moved)],cwd=self.w,capture_output=True,text=True,timeout=360,check=True)
   self.assertTrue(json.loads(result.stdout)['PCM_exact'])
  finally:
   for path,target in reversed(hidden):target.rename(path)
  self.assertEqual(inventory(self.root),before)
