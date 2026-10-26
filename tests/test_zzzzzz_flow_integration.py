"""Real editorial-flow native render, pitch, meter and portable state gates."""
import json,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from dataclasses import asdict
from kuang.schema import load,dumps
from kuang.club_flow import refine_flow
from kuang.flow_audit import audit_flow,require_flow
from kuang.sample_assets import inventory,digest
from kuang.loudness import measure
from kuang.midi import export_bytes
from tools.phase19_house import adapter,media,END,AUDIO
from tools.phase19_verify import pitch_gate,pulse_gate
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('KUANG_PHASE19_INTEGRATION')=='1','opt in to reviewed native host and complete Phase19 bundle')
class FlowIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.root=Path(os.environ['KUANG_PHASE19_RELEASE']);self.host=os.environ['KUANG_SOUNDCRAFT'];self.plugin=os.environ['KUANG_VITALIUM_PLUGIN']
  scratch=ROOT/'.local/phase19/tests';scratch.mkdir(parents=True,exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.w=Path(self.tmp.name);self.a=adapter(self.host,self.plugin)
 def tearDown(self):self.tmp.cleanup()
 def test_actual_signature_C2_and_home_color_chords_pitch_and_reload(self):
  r=pitch_gate(self.root,self.w/'pitch',self.host,self.plugin);self.assertEqual(r['native_synthetic_MIDI_input_1835232641'],.5);self.assertTrue(r['saved_reopened_PCM_exact']);self.assertEqual(len(r['chords']),4)
 def test_actual_kick_onsets_96_recovered_beats_compared_to_reference(self):
  r=pulse_gate(self.root,self.w/'pulse',self.host,self.plugin);self.assertEqual(r['records']['A']['audible_kick_attacks_88_112'],31);self.assertEqual(r['records']['B']['audible_kick_attacks_88_112'],96)
 def test_full_note_journal_exact_graph_state_and_PCM_after_reopen(self):
  before=inventory(self.root);old=load(self.root/'source/phase18-reference.kuang.json');p=load(self.root/'B/project.kuang.json');q,r=refine_flow(old)
  self.assertEqual(dumps(q),dumps(p));self.assertEqual(r,json.loads((self.root/'composition-receipt.json').read_text()));require_flow(audit_flow(old,p,r))
  for a,b in zip(old.tracks,p.tracks):
   aa=asdict(a);bb=asdict(b);aa.pop('clips');bb.pop('clips');self.assertEqual(aa,bb)
  self.assertEqual((self.root/'B/song.mid').read_bytes(),export_bytes(p));self.assertNotEqual(export_bytes(p),export_bytes(old))
  assets,patches=media(ROOT/'artifacts/phase18-house/B',p)
  for tid,path in assets.items():self.assertEqual(inventory(path),inventory(self.root/'B/native/assets'/tid))
  for tid,path in patches.items():self.assertEqual(inventory(path),inventory(self.root/'B/native/patches'/tid))
  n=self.a.inspect(self.root/'B/native')['native'];self.assertEqual((len(n['tracks']),len(n['busses']),len(n['markers'])),(17,4,9))
  self.a.save(self.root/'B/native',self.w/'saved');self.assertEqual(n,self.a.inspect(self.w/'saved')['native'])
  self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END);self.assertEqual(digest(self.w/'repeat.wav'),digest(self.root/AUDIO['B']));self.assertEqual(inventory(self.root),before)
 def test_full_equal_length_level_matched_PCM_nonclip_stereo_and_flow(self):
  m=[measure(p,library=os.environ.get('KUANG_EBUR128')) for p in sorted((self.root/'listening').glob('*.wav'))];self.assertEqual(len(m),2)
  self.assertAlmostEqual(m[0]['integrated_lufs'],m[1]['integrated_lufs'],delta=.01);self.assertEqual(m[0]['frames'],m[1]['frames'])
  for x in m:self.assertEqual((x['sample_rate'],x['bits_per_sample'],x['channels']),(48000,24,2));self.assertEqual(x['clipped_samples'],0);self.assertGreater(x['rms'],0);self.assertAlmostEqual(x['duration_seconds'],END,delta=1/48000)
  v=json.loads((self.root/'verification.json').read_text());self.assertEqual(v['candidate_preference'],'unreviewed');self.assertTrue(v['A_PCM_exact'])
  f=v['flow_facts']['B'];self.assertEqual(f['longest_kick_free_bars'],8);self.assertTrue(f['steady_four_floor_88_112']);self.assertEqual(f['first_complete_signature_zero_bar'],16)
  self.assertGreater(v['spatial_B']['bands']['low_20_120']['mono_energy_retention'],.9999);self.assertGreater(v['spatial_B']['bands']['high_over_500']['side_to_mid_power_ratio'],.03)
  self.assertGreater(v['spatial_B']['mono_sum']['rms_loss_db'],-.25);self.assertEqual(v['spatial_B']['last_250ms']['peak'],0)
  self.assertEqual(digest(self.root/AUDIO['A']),digest(ROOT/'artifacts/phase18-house/B-Phase18-extended-native.wav'))
 def test_zip_frozen_replay_with_original_source_media_and_plugin_hidden(self):
  before=inventory(self.root)
  with zipfile.ZipFile(self.root/'phase19-house-listening.zip') as z:
   self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'});self.assertEqual(len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')]),2)
   self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
  clone=self.w/'plugin/vitalium.vst3';clone.parent.mkdir();shutil.copytree(self.plugin,clone);hidden=[]
  try:
   for path in (self.root/'B/native',ROOT/'artifacts/phase18-house/B/native',Path(self.plugin)):
    target=path.with_name(path.name+'-phase19-hidden');self.assertFalse(target.exists());path.rename(target);hidden.append((path,target))
   result=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(clone)],cwd=self.w,capture_output=True,text=True,timeout=360,check=True)
   self.assertTrue(json.loads(result.stdout)['PCM_exact'])
  finally:
   for path,target in reversed(hidden):target.rename(path)
  self.assertEqual(inventory(self.root),before)
