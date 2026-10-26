"""Actual master summing/DSP, fixed performance, native and frozen portability."""
import json,os,shutil,subprocess,sys,tempfile,unittest,zipfile,wave
from pathlib import Path
from copy import deepcopy
from kuang.schema import load,state_hash
from kuang.record_mix import mixed_record
from kuang.master_bus import attach_terminal,SINK_KEY
from kuang.sample_assets import inventory,digest
from kuang.loudness import measure
from kuang.midi import export_bytes
from kuang.audio import analyze_wav
from kuang.production_audio import _decode
from kuang.transactions import SetParameter,Scope
from tools.phase20_house import adapter,media,END,AUDIO
from tools.phase20_verify import pitch_gate,controls
ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('KUANG_PHASE20_INTEGRATION')=='1','opt in to reviewed native mix/master host, plugin and Phase20 bundle')
class RecordMixIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.root=Path(os.environ['KUANG_PHASE20_RELEASE']);self.host=os.environ['KUANG_SOUNDCRAFT'];self.plugin=os.environ['KUANG_VITALIUM_PLUGIN'];self.a=adapter(self.host,self.plugin)
  scratch=ROOT/'.local/phase20/tests';scratch.mkdir(parents=True,exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.w=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_actual_full_terminal_passthrough_exact_PCM_and_no_main_bypass(self):
  source=load(self.root/'source/phase19-reference.kuang.json');p=attach_terminal(source);assets,patches=media(self.root/'B',p)
  self.a.export(p,assets,patches,self.w/'pass');self.a.render(self.w/'pass',self.w/'pass.wav',end_seconds=END)
  self.assertEqual(digest(self.w/'pass.wav'),digest(self.root/AUDIO['A']))
  native=self.a.inspect(self.w/'pass')['native'];sink=native['busses'][-1]['id']
  self.assertEqual([t['name'] for t in native['tracks'] if t['mixer']['output']=='Main'],['Stereo terminal master'])
  self.assertEqual(sum(t['mixer']['output']=={'Bus':sink} for t in native['tracks']),11)
  shutil.copytree(self.w/'pass',self.w/'muted');self.a.base._run([('mix.mute',{'track':'Stereo terminal master','value':True}),('file.bounce_mix',{'path':str(self.w/'muted.wav'),'format':'wav','bit_depth':24,'dither':False,'start':{'seconds':0},'end':{'seconds':4}})],self.w,source=self.w/'muted/session.scraft',destination=self.w/'muted/session.scraft')
  self.assertFalse(analyze_wav(self.w/'muted.wav')['non_silent'])
 def test_actual_native_pitch_G4_Eb4_C2_chords_and_reload(self):
  r=pitch_gate(self.root,self.w/'pitch',self.host,self.plugin);self.assertEqual(r['native_center_values'],[.5]*4);self.assertTrue(r['saved_reopened_PCM_exact'])
 def test_scoped_native_master_parameter_edit_and_inverse_preserve_everything_else(self):
  p=load(self.root/'B/project.kuang.json');scope=Scope(['phase20-stereo-master'],[],['soundcraft.high_shelf_gain'],None,None)
  self.a.apply(self.root/'B/native',self.w/'edited',[SetParameter('set_parameter','phase20-master-eq','soundcraft.high_shelf_gain',.5)],scope,state_hash(p))
  q=load(self.w/'edited/project.kuang.json');self.a.apply(self.w/'edited',self.w/'restored',[SetParameter('set_parameter','phase20-master-eq','soundcraft.high_shelf_gain',.75)],scope,state_hash(q))
  self.assertEqual(self.a.inspect(self.root/'B/native')['native'],self.a.inspect(self.w/'restored')['native'])
  self.assertEqual(state_hash(p),state_hash(load(self.w/'restored/project.kuang.json')))
 def test_actual_native_parallel_compression_space_and_master_limiter(self):
  r=controls(self.root,self.w/'controls',self.host,self.plugin,os.environ.get('KUANG_EBUR128'))
  self.assertGreater(r['shared_space_on_off']['difference_to_original_rms_ratio'],.02);self.assertGreater(r['native_drum_parallel_compression']['p01_attenuation_below_nominal_db'],.15);self.assertLessEqual(r['limiter_levels']['on']['true_peak_dbtp'],-1)
 def test_entire_MIDI_patches_samples_native_state_and_direct_relocation_PCM(self):
  before=inventory(self.root);s=load(self.root/'source/phase19-reference.kuang.json');p=load(self.root/'B/project.kuang.json');q,r=mixed_record(s)
  self.assertEqual(state_hash(q),state_hash(p));self.assertEqual(r,json.loads((self.root/'B/production.json').read_text()));self.assertEqual(export_bytes(s),export_bytes(p));self.assertEqual((self.root/'B/song.mid').read_bytes(),export_bytes(s));self.assertEqual(sum(len(c.notes) for t in p.tracks for c in t.clips),4596)
  for a,b in zip(s.tracks,p.tracks):self.assertEqual((a.id,a.clips,a.instrument),(b.id,b.clips,b.instrument))
  assets,patches=media(ROOT/'artifacts/phase19-house/B',p)
  for tid,path in assets.items():self.assertEqual(inventory(path),inventory(self.root/'B/native/assets'/tid))
  for tid,path in patches.items():self.assertEqual(inventory(path),inventory(self.root/'B/native/patches'/tid))
  shutil.copytree(self.root/'B/native',self.w/'relocated');plugin=self.w/'plugin/vitalium.vst3';plugin.parent.mkdir();shutil.copytree(self.plugin,plugin);hidden=[]
  try:
   for path in (self.root/'B/native',ROOT/'artifacts/phase19-house/B/native',Path(self.plugin)):
    target=path.with_name(path.name+'-phase20-hidden');self.assertFalse(target.exists());path.rename(target);hidden.append((path,target))
   a=adapter(self.host,plugin);n=a.inspect(self.w/'relocated')['native'];a.save(self.w/'relocated',self.w/'saved');self.assertEqual(n,a.inspect(self.w/'saved')['native']);a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END);self.assertEqual(digest(self.w/'repeat.wav'),digest(self.root/AUDIO['B']))
  finally:
   for path,target in reversed(hidden):target.rename(path)
  self.assertEqual(before,inventory(self.root))
 def test_complete_matched_loudness_PCM_ceiling_stereo_sections_and_shortterm(self):
  m=[measure(p,library=os.environ.get('KUANG_EBUR128')) for p in sorted((self.root/'listening').glob('*.wav'))];self.assertEqual(len(m),2);self.assertAlmostEqual(m[0]['integrated_lufs'],m[1]['integrated_lufs'],delta=.001)
  for x in m:self.assertEqual((x['sample_rate'],x['channels'],x['bits_per_sample'],x['clipped_samples']),(48000,2,24,0));self.assertAlmostEqual(x['duration_seconds'],END,delta=1/48000)
  v=json.loads((self.root/'verification.json').read_text());self.assertLessEqual(v['levels']['B']['true_peak_dbtp'],-1);self.assertTrue(v['source_PCM_exact']);self.assertEqual(v['candidate_preference'],'unreviewed');self.assertFalse(v['professional_quality_claimed'])
  self.assertGreater(v['spatial']['B']['bands']['low_20_120']['mono_energy_retention'],.999);self.assertGreater(v['spatial']['B']['mono_sum']['rms_loss_db'],-.3);self.assertGreater(len(v['shortterm']['B']['rows']),300)
  self.assertEqual(digest(self.root/AUDIO['A']),digest(ROOT/'artifacts/phase19-house/B-Phase19-continuity-native.wav'));self.assertGreater(v['levels']['B']['integrated_lufs'],v['levels']['premaster']['integrated_lufs'])
  tp=json.loads((self.root/'truepeak8x-verification.json').read_text());self.assertEqual(tp['input_sha256'],digest(self.root/AUDIO['B']));self.assertEqual(tp['oversample'],8);self.assertLessEqual(tp['true_peak_dbtp'],-1)
  with wave.open(str(self.root/'B-Phase20-premaster-native.wav'),'rb') as f:
   peaks=[]
   for beat in range(8):
    f.setpos(round(beat*60/126*48000));peaks.append(max(abs(x) for row in _decode(f.readframes(2400),3,2) for x in row))
  self.assertLess(peaks[0]/max(peaks[1:]),2)
 def test_extracted_ZIP_frozen_replay_relative_media_and_relocated_plugin(self):
  before=inventory(self.root)
  with zipfile.ZipFile(self.root/'phase20-house-listening.zip') as z:
   self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'});self.assertEqual(len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')]),2);self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
  clone=self.w/'plugin/vitalium.vst3';clone.parent.mkdir();shutil.copytree(self.plugin,clone);hidden=[]
  try:
   for path in (self.root/'B/native',ROOT/'artifacts/phase19-house/B/native',Path(self.plugin)):
    target=path.with_name(path.name+'-phase20-hidden');self.assertFalse(target.exists());path.rename(target);hidden.append((path,target))
   r=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(clone)],cwd=self.w,capture_output=True,text=True,timeout=420,check=True);self.assertTrue(json.loads(r.stdout)['PCM_exact'])
  finally:
   for path,target in reversed(hidden):target.rename(path)
  self.assertEqual(before,inventory(self.root))
