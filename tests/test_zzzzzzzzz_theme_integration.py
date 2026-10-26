"""Optional real-host melody/harmony performance, protected pocket and replay."""
import json,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from copy import deepcopy
from pathlib import Path
from kuang.schema import load,state_hash,Section,Clip,Note,BAR
from kuang.house_theme import compose_theme,EDITABLE
from kuang.theme_audit import audit_theme,require_theme
from kuang.sample_assets import digest,inventory
from kuang.midi import export_bytes
from kuang.loudness import measure
from kuang.audio import compare_wavs
from kuang.ensemble_production import isolate,DRUMS
from kuang.pitch_audio import spectrum,hz,cents
from tools.phase20_verify import window
from tools.phase21_house import adapter,media,AUDIO,END
from tools.phase21_pitch import gate
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('KUANG_PHASE21_INTEGRATION')=='1','optional real Phase21 host/palette/record proof')
class HouseThemeNativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(os.environ['KUANG_PHASE21_RELEASE']);cls.host=os.environ['KUANG_SOUNDCRAFT'];cls.plugin=os.environ['KUANG_VITALIUM_PLUGIN'];cls.a=adapter(cls.host,cls.plugin)
  cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.local/phase21/tmp');cls.w=Path(cls.temp.name);cls.s=load(cls.root/'source/project.kuang.json');cls.p=load(cls.root/'B/project.kuang.json');cls.assets,cls.patches=media(cls.root/'B',cls.p)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_exact_approved_pocket_and_palette_with_real_authored_upper_score(self):
  p,r=compose_theme(self.s);self.assertEqual(state_hash(p),state_hash(self.p));self.assertEqual(r,json.loads((self.root/'composition-receipt.json').read_text()));require_theme(audit_theme(self.s,p,r));self.assertNotEqual(export_bytes(p),export_bytes(self.s))
  for a,b in zip(self.s.tracks,p.tracks):
   if a.id not in EDITABLE:self.assertEqual(a,b)
   self.assertEqual(a.instrument,b.instrument);self.assertEqual(a.effects,b.effects);self.assertEqual(a.sends,b.sends);self.assertEqual(a.controls,b.controls)
  for tid,path in {**self.assets,**self.patches}.items():self.assertEqual(inventory(path),inventory(self.root/'source/native'/('assets' if tid in self.assets else 'patches')/tid))
  self.assertEqual(digest(self.root/AUDIO['A']),digest(ROOT/'artifacts/phase20-house/B-Phase20-source-production-native.wav'))
 def test_actual_new_register_and_chord_tuning_in_native_and_independent_hosts(self):
  r=gate(self.w/'new-pitch',self.host,self.plugin,os.environ['KUANG_VITALIUM_HOST_PYTHON']);self.assertEqual(r['native_synthetic_MIDI_pitch_center'],.5);self.assertTrue(r['original_patch_states_unchanged']);self.assertEqual(set(r['native_builtin']),{'arp','air'})
  native=self.a.inspect(self.root/'B/native')['native'];self.assertEqual([t['instrument']['params']['1835232641'] for t in native['tracks'] if t['instrument'] and t['instrument']['plugin'].startswith('vst3:')],[.5]*4)
 def test_real_drum_and_bass_PCM_exact_while_melody_backing_change(self):
  report={}
  for name,p in [('A',self.s),('B',self.p)]:
   for role,ids in [('drums',DRUMS),('bass',{'track-bass','track-sub-pulse'}),('backing',{'track-harmony','track-depth-pad','track-depth-air'}),('melody',{'track-lead','track-arp'})]:
    q=window(isolate(p,ids),32,16);folder=self.w/(name+'-'+role);self.a.export(q,{t.id:self.assets[t.id] for t in q.tracks if t.id in self.assets},{t.id:self.patches[t.id] for t in q.tracks if t.id in self.patches},folder);self.a.render(folder,folder.with_suffix('.wav'));report[name+'-'+role]=folder.with_suffix('.wav')
  for role in ('drums','bass'):self.assertEqual(digest(report['A-'+role]),digest(report['B-'+role]))
  for role in ('backing','melody'):self.assertGreater(compare_wavs(report['A-'+role],report['B-'+role])['difference_to_original_rms_ratio'],.1)
 def test_actual_concurrent_C_pedal_chords_and_existing_F_root(self):
  cases=[('Cm9-C',36,[51,55,58,62]),('Cm11-C',36,[51,53,58,62]),('Abmaj9-C',36,[51,56,58,67]),('Fm9-C',36,[53,56,60,63]),('Fm9-F',41,[53,56,60,63])]
  q=deepcopy(self.p);q.bars=3*len(cases);q.sections=[Section('phase21-root-context','Actual bass plus upper harmony',0,q.bars*BAR)];q.automation=[];q.locks=[];q.tracks=[t for t in q.tracks if t.id in ('track-bass','track-harmony')]
  for t in q.tracks:
   t.effects=[];t.sends=[];t.output_master=True;t.controls={'mixer.gain_db':-24,'mixer.pan':0,'mixer.mute':0};notes=[]
   for i,(_,root,chord) in enumerate(cases):
    for j,n in enumerate([root] if t.id=='track-bass' else chord):notes.append(Note('phase21-context-'+t.id+'-'+str(i)+'-'+str(j),i*3*BAR+480,2880,n,96,0))
   t.clips=[Clip('phase21-context-'+t.id,'No FX, simultaneous original instruments','midi',0,q.bars*BAR,notes,None)]
  self.a.export(q,{}, {t.id:self.patches[t.id] for t in q.tracks},self.w/'root-context');self.a.render(self.w/'root-context',self.w/'root-context.wav')
  for i,(name,root,chord) in enumerate(cases):
   start=(i*12+.5)*60/126;peaks=spectrum(self.w/'root-context.wav',start+.5,start+.9)[2][:150]
   for n in [root,*chord]:self.assertLess(min(abs(cents(x['hz'],hz(n))) for x in peaks),5,(name,n))
  self.a.save(self.w/'root-context',self.w/'root-context-saved');self.a.render(self.w/'root-context-saved',self.w/'root-context-repeat.wav');self.assertEqual(digest(self.w/'root-context.wav'),digest(self.w/'root-context-repeat.wav'))
 def test_entire_native_state_save_reopen_and_full_PCM_exact(self):
  self.a.save(self.root/'B/native',self.w/'saved');self.assertEqual(self.a.inspect(self.root/'B/native')['native'],self.a.inspect(self.w/'saved')['native']);self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END);self.assertEqual(digest(self.w/'repeat.wav'),digest(self.root/AUDIO['B']))
 def test_main16_and_whole_song_actual_PCM_matching_mono_and_form(self):
  meter=os.environ.get('KUANG_EBUR128');full=[measure(next((self.root/'listening').glob(n+'-*.wav')),library=meter) for n in ('A','B')];short=[measure(self.root/'main16'/(n+'-MAIN16-MATCHED.wav'),library=meter) for n in ('A','B')]
  self.assertAlmostEqual(full[0]['integrated_lufs'],full[1]['integrated_lufs'],delta=.001);self.assertAlmostEqual(short[0]['integrated_lufs'],short[1]['integrated_lufs'],delta=.001)
  for x in full+short:self.assertEqual((x['sample_rate'],x['channels'],x['bits_per_sample'],x['clipped_samples']),(48000,2,24,0));self.assertGreater(x['rms'],0)
  self.assertAlmostEqual(full[0]['duration_seconds'],END,delta=1/48000);self.assertAlmostEqual(full[1]['duration_seconds'],END,delta=1/48000)
  self.assertGreater(compare_wavs(self.root/'main16/A-MAIN16-MATCHED.wav',self.root/'main16/B-MAIN16-MATCHED.wav')['difference_to_original_rms_ratio'],.1)
  a=load(self.root/'main16/A/project.kuang.json');b=load(self.root/'main16/B/project.kuang.json')
  for t,u in zip(a.tracks,b.tracks):
   if t.id not in EDITABLE:self.assertEqual(t,u)
  v=json.loads((self.root/'verification.json').read_text());self.assertFalse(v['mastering']);self.assertFalse(v['professional_quality_claimed']);self.assertEqual(v['candidate_preference'],'unreviewed');self.assertGreater(v['spatial_B']['bands']['low_20_120']['mono_energy_retention'],.999)
 def test_ZIP_frozen_replay_without_original_native_or_plugin_location(self):
  before=inventory(self.root)
  with zipfile.ZipFile(self.root/'phase21-house-listening.zip') as z:
   self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'});self.assertEqual(len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')]),2);self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
  clone=self.w/'external/vitalium.vst3';clone.parent.mkdir();shutil.copytree(self.plugin,clone);hidden=[]
  try:
   for p in (self.root/'B/native',ROOT/'artifacts/phase20-house/B/native',Path(self.plugin)):
    target=p.with_name(p.name+'-phase21-hidden');self.assertFalse(target.exists());p.rename(target);hidden.append((p,target))
   r=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(clone)],cwd=self.w,capture_output=True,text=True,timeout=420);self.assertEqual(r.returncode,0,r.stderr[-3000:]);self.assertTrue(json.loads(r.stdout)['PCM_exact'])
  finally:
   for p,target in reversed(hidden):target.rename(p)
  self.assertEqual(before,inventory(self.root))
