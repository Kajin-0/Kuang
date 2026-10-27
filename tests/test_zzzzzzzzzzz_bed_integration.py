"""Opt-in real checks for the one melody-free groove, no new variants."""
import json,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from kuang.chord_bed import compose_bed,audit_bed,bed_patch,PROTECTED,REMOVED
from kuang.external_synth import bound_project,read_patch
from kuang.schema import load,state_hash
from kuang.sample_assets import digest,inventory
from kuang.loudness import measure
from tools.phase22_shortlist import stem
from tools.phase23_groove import adapter,media,END,WAV
from tools.phase23_verify import pitch
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('KUANG_PHASE23_INTEGRATION')=='1','optional real single-groove source/pocket/portable proof')
class ChordBedNativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(os.environ['KUANG_PHASE23_RELEASE']);cls.host=os.environ['KUANG_SOUNDCRAFT'];cls.plugin=os.environ['KUANG_VITALIUM_PLUGIN'];cls.a=adapter(cls.host,cls.plugin);cls.ref=load(cls.root/'reference.kuang.json');cls.p=load(cls.root/'project/project.kuang.json');cls.assets,cls.patches=media(cls.root/'project',cls.p);cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.local/phase23/tmp');cls.w=Path(cls.temp.name)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_actual_absence_exact_source_rhythm_native_graph_and_two_new_patch_states(self):
  q,r=compose_bed(self.ref);changed={t:self.patches[t] for t in ('track-harmony','track-depth-pad')};p=bound_project(q,changed);r.update(candidate_hash=state_hash(p),prepared_patch_manifests={k:digest(v/'manifest.json') for k,v in changed.items()});self.assertEqual(p,self.p);self.assertEqual(r,json.loads((self.root/'production-receipt.json').read_text()));audit_bed(self.ref,p,r)
  self.assertFalse(REMOVED&{t.id for t in p.tracks});original=ROOT/'artifacts/phase22-house/A/native'
  for tid,path in {**self.assets,'track-bass':self.patches['track-bass']}.items():self.assertEqual(inventory(path),inventory(original/('assets' if tid in self.assets else 'patches')/tid))
  for tid,voice in [('track-harmony','stab'),('track-depth-pad','pad')]:
   read_patch(self.patches[tid]);self.assertEqual(json.loads((self.patches[tid]/'patch.vital').read_text()),bed_patch(voice));self.assertNotEqual(digest(self.patches[tid]/'component.bin'),digest(original/'patches'/tid/'component.bin'))
  native=self.a.inspect(self.root/'project/native')['native'];self.assertEqual([t['instrument']['params']['1835232641'] for t in native['tracks'] if t['instrument'] and t['instrument']['plugin'].startswith('vst3:')],[.5]*3)
 def test_played_new_source_notes_chords_and_C2_in_both_real_hosts(self):
  before=inventory(self.root);r=pitch(self.root,self.w/'tuning',self.host,self.plugin,os.environ['KUANG_VITALIUM_HOST_PYTHON']);self.assertEqual(r['native_pitch_center'],.5);self.assertEqual(set(r['voices']),{'stab','pad','bass'});self.assertEqual(before,inventory(self.root))
 def test_approved_rhythm_PCM_exact_and_real_source_filter_controls(self):
  paths=[]
  for name,p in [('reference',self.ref),('candidate',self.p)]:
   q=stem(p,PROTECTED);folder=self.w/name;self.a.export(q,{t.id:self.assets[t.id] for t in q.tracks if t.id in self.assets},{t.id:self.patches[t.id] for t in q.tracks if t.id in self.patches},folder);wav=self.w/(name+'.wav');self.a.render(folder,wav,end_seconds=END);paths.append(wav)
  self.assertEqual(digest(paths[0]),digest(paths[1]));s=json.loads((self.root/'sound-proof.json').read_text());self.assertTrue(s['rhythm_section_PCM_exact']);self.assertGreater(s['native_slow_filter_on_off']['difference_to_original_rms_ratio'],.01)
  for x in s['same_input_source_timbres'].values():self.assertGreater(x['equal_LUFS_source_difference']['difference_to_source_RMS'],.10)
 def test_single_full_mix_PCM_format_reopen_and_complete_unchanged_state(self):
  self.a.save(self.root/'project/native',self.w/'saved');self.assertEqual(self.a.inspect(self.root/'project/native')['native'],self.a.inspect(self.w/'saved')['native']);self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END);self.assertEqual(digest(self.root/WAV),digest(self.w/'repeat.wav'))
  m=measure(self.root/WAV,library=os.environ.get('KUANG_EBUR128'));self.assertEqual((m['sample_rate'],m['channels'],m['bits_per_sample'],m['clipped_samples']),(48000,2,24,0));self.assertGreater(m['rms'],0);self.assertAlmostEqual(m['duration_seconds'],END,delta=1/48000)
  self.assertEqual([p.name for p in self.root.glob('*.wav')],[WAV]);v=json.loads((self.root/'verification.json').read_text());self.assertFalse(v['mastering']);self.assertFalse(v['professional_quality_claimed']);self.assertEqual(v['human_preference'],'unreviewed');self.assertGreater(v['spatial']['bands']['low_20_120']['mono_energy_retention'],.999)
 def test_ZIP_one_mix_and_relocated_replay_with_original_paths_hidden(self):
  before=inventory(self.root)
  with zipfile.ZipFile(self.root/'phase23-no-melody-groove.zip') as z:
   self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'});self.assertEqual([n for n in z.namelist() if n==WAV],[WAV]);self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
  clone=self.w/'external/vitalium.vst3';clone.parent.mkdir();shutil.copytree(self.plugin,clone);hidden=[]
  try:
   for p in (self.root/'project/native',ROOT/'artifacts/phase22-house/A/native',Path(self.plugin)):
    target=p.with_name(p.name+'-phase23-hidden');self.assertFalse(target.exists());p.rename(target);hidden.append((p,target))
   r=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(clone)],cwd=self.w,capture_output=True,text=True,timeout=240);self.assertEqual(r.returncode,0,r.stderr[-3000:]);self.assertTrue(json.loads(r.stdout)['PCM_exact'])
  finally:
   for p,target in reversed(hidden):target.rename(p)
  self.assertEqual(before,inventory(self.root))
