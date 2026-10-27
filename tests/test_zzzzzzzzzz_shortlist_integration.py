"""Optional actual four-way composition/pocket/tuning/portable-native proof."""
import json,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from copy import deepcopy
from pathlib import Path
from kuang.schema import load,state_hash,Section,Clip,Note,BAR
from kuang.house_shortlist import main_reference,compose_candidate,DRUMS,LOW
from kuang.shortlist_audit import audit_shortlist,require_shortlist
from kuang.sample_assets import digest,inventory,write
from kuang.loudness import measure
from kuang.audio import compare_wavs
from kuang.pitch_audio import spectrum,hz,cents
from kuang.production_host import ProductionAdapter
from kuang.master_bus import SINK_KEY
from tools.phase22_shortlist import adapter,media,stem,OPTIONS,DIRECTIONS,END
from tools.phase22_pitch import gate
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('KUANG_PHASE22_INTEGRATION')=='1','optional real Phase22 four-way composer/palette proof')
class HouseShortlistNativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(os.environ['KUANG_PHASE22_RELEASE']);cls.host=os.environ['KUANG_SOUNDCRAFT'];cls.plugin=os.environ['KUANG_VITALIUM_PLUGIN'];cls.a=adapter(cls.host,cls.plugin)
  cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.local/phase22/tmp');cls.w=Path(cls.temp.name);cls.ps={n:load(cls.root/n/'project.kuang.json') for n in OPTIONS};cls.assets,cls.patches=media(cls.root/'A',cls.ps['A'])
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_exact_incumbent_and_authored_scores_with_original_palette_and_expression(self):
  source=load(ROOT/'artifacts/phase21-house/B/project.kuang.json');self.assertEqual(state_hash(main_reference(source)),state_hash(self.ps['A']));self.assertEqual(self.ps['A'],load(ROOT/'artifacts/phase21-house/main16/B/project.kuang.json'))
  for n,kind in DIRECTIONS.items():
   p,r=compose_candidate(self.ps['A'],kind);self.assertEqual(p,self.ps[n]);self.assertEqual(r,json.loads((self.root/n/'composition-receipt.json').read_text()));require_shortlist(audit_shortlist(self.ps['A'],p,r))
  for n,p in self.ps.items():
   for tid,path in {**self.assets,**self.patches}.items():self.assertEqual(inventory(path),inventory(self.root/n/'native'/('assets' if tid in self.assets else 'patches')/tid))
   native=self.a.inspect(self.root/n/'native')['native'];self.assertEqual([t['instrument']['params']['1835232641'] for t in native['tracks'] if t['instrument'] and t['instrument']['plugin'].startswith('vst3:')],[.5]*4)
 def test_actual_all_new_notes_G4_Eb4_C2_chord_partials_and_independent_host(self):
  r=gate(self.w/'pitch',self.host,self.plugin,os.environ['KUANG_VITALIUM_HOST_PYTHON']);self.assertEqual(r['native_pitch_center'],.5);self.assertTrue(r['original_patch_states_unchanged']);self.assertEqual(set(r['voices']),{'bass','lead','stab','pad'});self.assertEqual(set(r['builtins']),{'arp','air'})
 def test_real_all_four_drum_PCM_and_hypnotic_bass_PCM_exact(self):
  report={}
  for name,p in self.ps.items():
   for role,ids in [('drums',DRUMS),('low',LOW),('upper',{'track-harmony','track-lead','track-depth-pad','track-arp','track-depth-air'})]:
    q=stem(p,ids);folder=self.w/(name+'-'+role);self.a.export(q,{t.id:self.assets[t.id] for t in q.tracks if t.id in self.assets},{t.id:self.patches[t.id] for t in q.tracks if t.id in self.patches},folder);wav=folder.with_suffix('.wav');self.a.render(folder,wav,end_seconds=END);report[name+'-'+role]=wav
  for name in 'BCD':self.assertEqual(digest(report['A-drums']),digest(report[name+'-drums']))
  self.assertEqual(digest(report['A-low']),digest(report['D-low']))
  for name in 'BC':self.assertGreater(compare_wavs(report['A-low'],report[name+'-low'])['difference_to_original_rms_ratio'],.1)
  for name in 'BCD':self.assertGreater(compare_wavs(report['A-upper'],report[name+'-upper'])['difference_to_original_rms_ratio'],.1)
 def test_actual_concurrent_moving_roots_and_guide_voicings(self):
  cases=[(36,[51,58,62]),(41,[56,60,63]),(32,[55,58,60]),(39,[55,58,62]),(34,[56,60,63])]
  q=deepcopy(self.ps['A']);q.metadata.pop(SINK_KEY);q.bars=3*len(cases);q.sections=[Section('phase22-chord-root','Actual simultaneous roots and guides',0,q.bars*BAR)];q.automation=[];q.locks=[];q.tracks=[t for t in q.tracks if t.id in ('track-bass','track-harmony')]
  for t in q.tracks:
   t.effects=[];t.sends=[];t.output_master=True;t.controls={'mixer.gain_db':-24,'mixer.pan':0,'mixer.mute':0};t.clips=[Clip('phase22-context-'+t.id,'Dry actual root/guide context','midi',0,q.bars*BAR,
    [Note('phase22-context-'+t.id+'-'+str(i)+'-'+str(j),i*3*BAR+480,2880,n,96,0) for i,(root,chord) in enumerate(cases) for j,n in enumerate([root] if t.id=='track-bass' else chord)],None)]
  a=ProductionAdapter(self.host,plugin=self.plugin,workspace=ROOT,scratch=ROOT/'.local/phase22/tmp',center_pitch_bend=True);a.export(q,{}, {t.id:self.patches[t.id] for t in q.tracks},self.w/'chords');a.render(self.w/'chords',self.w/'chords.wav')
  for i,(root,chord) in enumerate(cases):
   at=(i*12+.5)*60/126;peaks=spectrum(self.w/'chords.wav',at+.5,at+.9)[2][:150]
   for n in [root,*chord]:self.assertLess(min(abs(cents(x['hz'],hz(n))) for x in peaks),5,(root,chord,n))
  a.save(self.w/'chords',self.w/'chords-saved');a.render(self.w/'chords-saved',self.w/'chords-repeat.wav');self.assertEqual(digest(self.w/'chords.wav'),digest(self.w/'chords-repeat.wav'))
 def test_native_save_reopen_full_state_and_all_four_PCM_exact(self):
  for n in OPTIONS:
   self.a.save(self.root/n/'native',self.w/(n+'-saved'));self.assertEqual(self.a.inspect(self.root/n/'native')['native'],self.a.inspect(self.w/(n+'-saved'))['native']);wav=self.w/(n+'-repeat.wav');self.a.render(self.w/(n+'-saved'),wav,end_seconds=END);self.assertEqual(digest(wav),digest(self.root/'raw'/(n+'-'+OPTIONS[n]+'-native.wav')))
 def test_real_matched_full_mix_non_silence_no_clips_mono_and_distinct_audio(self):
  meter=os.environ.get('KUANG_EBUR128');levels=[measure(self.root/'listening'/(n+'-'+title+'-MATCHED.wav'),library=meter) for n,title in OPTIONS.items()]
  self.assertLess(max(x['integrated_lufs'] for x in levels)-min(x['integrated_lufs'] for x in levels),.001)
  for x in levels:self.assertEqual((x['sample_rate'],x['channels'],x['bits_per_sample'],x['clipped_samples']),(48000,2,24,0));self.assertGreater(x['rms'],0);self.assertAlmostEqual(x['duration_seconds'],END,delta=1/48000)
  v=json.loads((self.root/'verification.json').read_text());self.assertTrue(v['A_is_exact_existing_Phase21_main16_PCM']);self.assertFalse(v['mastering']);self.assertFalse(v['new_full_song']);self.assertFalse(v['professional_quality_claimed']);self.assertEqual(v['human_preference'],'unreviewed')
  for n,x in v['results'].items():self.assertGreater(x['spatial']['bands']['low_20_120']['mono_energy_retention'],.999)
  self.assertTrue(all(x['difference_to_original_rms_ratio']>.05 for x in v['pairwise_PCM_differences'].values()))
 def test_ZIP_four_way_frozen_replay_with_all_original_paths_hidden(self):
  before=inventory(self.root)
  with zipfile.ZipFile(self.root/'phase22-composer-shortlist.zip') as z:
   self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'});self.assertEqual(len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')]),4);self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()));z.extractall(self.w/'download')
  clone=self.w/'external/vitalium.vst3';clone.parent.mkdir();shutil.copytree(self.plugin,clone);hidden=[]
  try:
   for p in [*(self.root/n/'native' for n in OPTIONS),ROOT/'artifacts/phase21-house/B/native',ROOT/'artifacts/phase21-house/main16/B/native',Path(self.plugin)]:
    target=p.with_name(p.name+'-phase22-hidden');self.assertFalse(target.exists());p.rename(target);hidden.append((p,target))
   r=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(clone)],cwd=self.w,capture_output=True,text=True,timeout=420);self.assertEqual(r.returncode,0,r.stderr[-3000:]);self.assertTrue(json.loads(r.stdout)['all_four_PCM_exact'])
  finally:
   for p,target in reversed(hidden):target.rename(p)
  self.assertEqual(before,inventory(self.root))
