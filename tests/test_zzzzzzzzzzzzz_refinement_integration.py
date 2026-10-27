"""Actual source refinement, bounded master gate and complete native replay."""
import json,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from kuang.schema import load,state_hash
from kuang.production_refinement import refine_record,audit_refinement,refined_patch
from kuang.external_synth import bound_project
from kuang.sample_assets import digest,inventory
from kuang.mastering import attenuate
from kuang.loudness import measure
from tools.phase25_house import adapter,media,END,RAW,LISTEN
from tools.phase25_verify import pitch,source_controls,rhythm_qa,master_probe
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('KUANG_PHASE25_INTEGRATION')=='1','optional real source-refined144-bar production')
class ProductionRefinementNativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(os.environ['KUANG_PHASE25_RELEASE']);cls.host=os.environ['KUANG_SOUNDCRAFT'];cls.plugin=os.environ['KUANG_VITALIUM_PLUGIN'];cls.meter=os.environ['KUANG_EBUR128'];cls.a=adapter(cls.host,cls.plugin);cls.s=load(cls.root/'phase24-source.kuang.json');cls.p=load(cls.root/'project/project.kuang.json');cls.assets,cls.patches=media(cls.root/'project',cls.p);cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.local/phase25/tmp');cls.w=Path(cls.temp.name)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_actual_source_states_scoped_MIDI_live_graph_and_neutral_pitch(self):
  q,r=refine_record(self.s);changed={k:self.patches[k] for k in ('track-harmony','track-depth-pad')};p=bound_project(q,changed);r.update(candidate_hash=state_hash(p),prepared_patch_manifests={k:digest(v/'manifest.json') for k,v in changed.items()});self.assertEqual(p,self.p);self.assertEqual(r,json.loads((self.root/'production-receipt.json').read_text()));a=audit_refinement(self.s,p,r);self.assertEqual(a['anchor_MIDI_exact'],501);self.assertFalse(a['anchor_upper_audio_exact'])
  old=ROOT/'artifacts/phase24-house/project/native'
  for tid,path in {**self.assets,'track-bass':self.patches['track-bass']}.items():self.assertEqual(inventory(path),inventory(old/('assets' if tid in self.assets else 'patches')/tid))
  for tid,voice in [('track-harmony','stab'),('track-depth-pad','pad')]:self.assertEqual(json.loads((self.patches[tid]/'patch.vital').read_text()),refined_patch(voice));self.assertNotEqual(digest(self.patches[tid]/'component.bin'),digest(old/'patches'/tid/'component.bin'))
  native=self.a.inspect(self.root/'project/native')['native'];self.assertEqual([t['instrument']['params']['1835232641'] for t in native['tracks'] if t['instrument'] and t['instrument']['plugin'].startswith('vst3:')],[.5]*3);self.assertEqual(len(native['markers']),8);self.assertFalse(self.p.tracks[-1].effects)
 def test_new_patch_actual_notes_polyphony_and_reopen_both_hosts(self):
  before=inventory(self.root);r=pitch(self.root,self.w/'pitch',self.host,self.plugin,os.environ['KUANG_VITALIUM_HOST_PYTHON']);self.assertEqual(r['native_pitch_center'],.5);self.assertEqual(before,inventory(self.root))
 def test_sources_motion_return_duck_and_true_bus_FX_same_input_gates(self):
  before=inventory(self.root);r=source_controls(self.root,self.host,self.plugin,self.meter);self.assertTrue(r['anchor_rhythm_PCM_exact'])
  for x in r['voices'].values():self.assertGreater(x['same_new_MIDI_source_swap_equal_LUFS']['difference_to_source_RMS'],.10);self.assertGreater(x['LFO_routes_on_off_same_input']['difference_to_original_rms_ratio'],.02);self.assertLess(abs(x['preinsert_error_LU']),.01)
  gate=master_probe(self.root,self.host,self.plugin,self.meter);self.assertTrue(gate['actual_terminal_routes_and_processing']);self.assertFalse(gate['applied_to_final_record']);self.assertEqual(before,inventory(self.root))
 def test_rhythm_before_after_native_windows_preserve_prefix_and_source_ghosts(self):
  before=inventory(self.root);r=rhythm_qa(self.root,self.host,self.plugin);self.assertEqual(r['extra_ghosts_removed'],4);self.assertTrue(r['source_ghost_3_777_retained']);self.assertTrue(r['bass_omissions_retained'])
  for x in r['windows'].values():self.assertTrue(x['unaffected_first_bar_PCM_exact']);self.assertTrue(x['actual_PCM_difference']['measurable_change'])
  self.assertEqual(before,inventory(self.root))
 def test_full_raw_native_reopen_PCM_and_exact_constant_gain_A_B_matching(self):
  self.a.save(self.root/'project/native',self.w/'saved');self.assertEqual(self.a.inspect(self.root/'project/native')['native'],self.a.inspect(self.w/'saved')['native']);self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END);self.assertEqual(digest(self.root/RAW),digest(self.w/'repeat.wav'))
  v=json.loads((self.root/'verification.json').read_text());values=[]
  for label,path in [('A',ROOT/v['raw_reference_path']),('B',self.root/RAW)]:
   m=measure(self.root/'listening'/LISTEN[label],library=self.meter);self.assertEqual((m['sample_rate'],m['channels'],m['bits_per_sample'],m['clipped_samples']),(48000,2,24,0));self.assertAlmostEqual(m['duration_seconds'],END,delta=1/48000);values.append(m['integrated_lufs']);gain=v['matching'][label]['gain_db'];self.assertLessEqual(gain,0);attenuate(path,self.w/(label+'-gain.wav'),gain);self.assertEqual(digest(self.w/(label+'-gain.wav')),digest(self.root/'listening'/LISTEN[label]))
  self.assertLess(abs(values[0]-values[1]),.001);self.assertFalse(v['mastering']);self.assertEqual(v['human_preference'],'unreviewed')
 def test_ZIP_two_complete_auditions_and_relocated_raw_matched_replay_exact(self):
  before=inventory(self.root)
  with zipfile.ZipFile(self.root/'phase25-house-listening.zip') as z:
   self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'});self.assertEqual(sorted(n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')),sorted('listening/'+v for v in LISTEN.values()));self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
  clone=self.w/'external/vitalium.vst3';clone.parent.mkdir();shutil.copytree(self.plugin,clone);hidden=[]
  try:
   for p in (self.root/'project/native',ROOT/'artifacts/phase24-house/project/native',Path(self.plugin)):
    dest=p.with_name(p.name+'-phase25-hidden');self.assertFalse(dest.exists());p.rename(dest);hidden.append((p,dest))
   r=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(clone)],cwd=self.w,capture_output=True,text=True,timeout=600);self.assertEqual(r.returncode,0,r.stderr[-4000:]);result=json.loads(r.stdout);self.assertTrue(result['raw_PCM_exact']);self.assertTrue(result['matched_PCM_exact'])
  finally:
   for p,dest in reversed(hidden):dest.rename(p)
  self.assertEqual(before,inventory(self.root))
