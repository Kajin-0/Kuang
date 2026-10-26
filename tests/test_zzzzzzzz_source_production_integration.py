"""Explicitly optional source-first actual native proof, not listening preference."""
import json,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from kuang.schema import load,state_hash
from kuang.source_production import source_record
from kuang.sample_assets import digest,inventory
from kuang.midi import export_bytes
from kuang.audio import compare_wavs,analyze_wav
from kuang.master_bus import terminal_projection
from tools.phase20_house import adapter,media,END
from tools.phase20_sources import AUDIO
from tools.phase16_pitch import analyze
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('KUANG_PHASE20_SOURCE_INTEGRATION')=='1','optional source-first real-host proof')
class SourceProductionNativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(os.environ['KUANG_PHASE20_SOURCE_RELEASE']);cls.host=os.environ['KUANG_SOUNDCRAFT'];cls.plugin=os.environ['KUANG_VITALIUM_PLUGIN'];cls.a=adapter(cls.host,cls.plugin,master=False)
  cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.local/phase20/tmp');cls.w=Path(cls.temp.name)
  cls.source=load(cls.root/'source/project.kuang.json');cls.p=load(cls.root/'B/project.kuang.json');cls.assets,cls.patches=media(cls.root/'B',cls.p)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_actual_source_rebuild_full_note_identity_and_only_declared_instruments(self):
  p,r=source_record(self.source,{t:self.patches[t] for t in ('track-harmony','track-lead')},kick=self.assets['track-kick'])
  self.assertEqual(state_hash(p),state_hash(self.p));self.assertEqual(r,json.loads((self.root/'B/production.json').read_text()));self.assertEqual(export_bytes(p),export_bytes(self.source));self.assertEqual(p.sections,self.source.sections)
  self.assertEqual(sum(len(c.notes) for t in p.tracks for c in t.clips),4596)
  for a,b in zip(self.source.tracks,p.tracks):
   self.assertEqual((a.id,a.clips),(b.id,b.clips))
   if a.id not in ('track-harmony','track-lead','track-kick'):self.assertEqual(a.instrument,b.instrument)
   if a.id in ('track-bass','track-depth-pad'):self.assertEqual(inventory(self.root/'source/native/patches'/a.id),inventory(self.patches[a.id]))
  self.assertEqual(digest(self.root/AUDIO['A']),digest(ROOT/'artifacts/phase19-house/B-Phase19-continuity-native.wav'))
 def test_real_nine_note_and_Cm9_tuning_in_two_hosts_and_centered_native_MIDI(self):
  report=json.loads((self.root/'source-pitch.json').read_text())
  for voice in ('stab','lead'):
   for host in ('native','independent'):
    for rows in report['voices'][voice][host]['notes'].values():
     for x in rows:self.assertLess(abs(x['fft_cents']),5);self.assertLess(abs(x['period_cents']),5);self.assertGreater(x['period_correlation'],.85)
    self.assertTrue(all(x['nearest_peak_cents']<5 for x in report['voices'][voice][host]['chord']))
   self.assertEqual(report['voices'][voice]['manifest_sha256'],digest(self.patches[{'stab':'track-harmony','lead':'track-lead'}[voice]]/'manifest.json'))
  native=self.a.inspect(self.root/'B/native')['native'];external=[t for t in native['tracks'] if t['instrument'] and t['instrument']['plugin'].startswith('vst3:')]
  self.assertEqual([t['instrument']['params']['1835232641'] for t in external],[.5]*4)
 def test_actual_same_MIDI_modulation_ON_OFF_not_a_preset_label(self):
  controls=Path(os.environ['KUANG_PHASE20_SOURCE_CONTROLS'])
  for voice in ('stab','lead'):
   on=controls/(voice+'-on');off=controls/(voice+'-off');pa=load(on/'project.kuang.json');pb=load(off/'project.kuang.json');self.assertEqual(export_bytes(pa),export_bytes(pb))
   self.a.render(on,self.w/(voice+'-on.wav'));self.a.render(off,self.w/(voice+'-off.wav'))
   d=compare_wavs(self.w/(voice+'-off.wav'),self.w/(voice+'-on.wav'));self.assertGreater(d['difference_to_original_rms_ratio'],.05)
   self.assertEqual(digest(self.w/(voice+'-on.wav')),digest(controls/(voice+'-on.wav')))
 def test_real_full_native_save_reopen_state_and_PCM_exact(self):
  self.a.save(self.root/'B/native',self.w/'saved');self.assertEqual(self.a.inspect(self.root/'B/native')['native'],self.a.inspect(self.w/'saved')['native']);self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END)
  self.assertEqual(digest(self.w/'repeat.wav'),digest(self.root/AUDIO['B']));v=json.loads((self.root/'verification.json').read_text())
  self.assertFalse(v['native_master_processing']);self.assertFalse(v['offline_mastering']);self.assertEqual(v['candidate_preference'],'unreviewed');self.assertEqual(v['levels']['B']['clipped_samples'],0);self.assertGreater(v['spatial']['B']['bands']['low_20_120']['mono_energy_retention'],.999)
 def test_main16_real_source_changes_exact_performance_and_fair_matching(self):
  q=self.root/'groove-preview';a=load(q/'A/project.kuang.json');b=load(q/'B/project.kuang.json');self.assertEqual(export_bytes(a),export_bytes(b));self.assertEqual(sum(len(c.notes) for t in b.tracks for c in t.clips),608)
  for p in (a,b):terminal_projection(p);self.assertEqual(p.tracks[-1].effects,[]);self.assertEqual(p.tracks[-1].controls['mixer.gain_db'],-6)
  d=compare_wavs(q/'A-MAIN16-MATCHED.wav',q/'B-MAIN16-MATCHED.wav');self.assertGreater(d['difference_to_original_rms_ratio'],.1)
  from kuang.loudness import measure
  meter=os.environ.get('KUANG_EBUR128');m=[measure(q/(x+'-MAIN16-MATCHED.wav'),library=meter) for x in ('A','B')];self.assertAlmostEqual(m[0]['integrated_lufs'],m[1]['integrated_lufs'],delta=.001)
  full=[measure(next((self.root/'listening').glob(x+'-*.wav')),library=meter) for x in ('A','B')];self.assertAlmostEqual(full[0]['integrated_lufs'],full[1]['integrated_lufs'],delta=.001)
  self.assertTrue(all(x['clipped_samples']==0 and x['rms']>0 for x in m+full))
 def test_ZIP_portable_frozen_replay_without_original_assets_or_plugin_location(self):
  before=inventory(self.root)
  with zipfile.ZipFile(self.root/'phase20-house-listening.zip') as z:
   self.assertIsNone(z.testzip());manifest=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(manifest)|{'zip-manifest.json'});self.assertEqual(len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')]),2);self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
  clone=self.w/'external/vitalium.vst3';clone.parent.mkdir();shutil.copytree(self.plugin,clone);hidden=[]
  try:
   for path in (self.root/'B/native',ROOT/'artifacts/phase19-house/B/native',Path(self.plugin)):
    target=path.with_name(path.name+'-phase20-source-hidden');self.assertFalse(target.exists());path.rename(target);hidden.append((path,target))
   r=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(clone)],cwd=self.w,capture_output=True,text=True,check=True,timeout=420);self.assertTrue(json.loads(r.stdout)['PCM_exact'])
  finally:
   for path,target in reversed(hidden):target.rename(path)
  self.assertEqual(before,inventory(self.root))
