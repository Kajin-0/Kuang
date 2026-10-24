"""Real audio correctness: actual notes/voicing, not just native field equality."""
import json,math,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from kuang.production_host import ProductionAdapter
from kuang.schema import load,dumps
from kuang.pitch_audio import note_pitch,spectrum,hz,cents
from kuang.sample_assets import digest,inventory
from kuang.midi import export_bytes
from kuang.audio import compare_wavs
from tools.phase15_pitch import gate,held,ON,WINDOWS
from tools.phase15_house import adapter,END
ROOT=Path(__file__).resolve().parents[1];SCRATCH=ROOT/'.local/phase15/tests'

@unittest.skipUnless(os.environ.get('KUANG_PHASE15_INTEGRATION')=='1','opt in to actual reviewed host, tuning probes and full repair')
class MusicalRepairIntegrationTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=SCRATCH);self.w=Path(self.tmp.name)
        self.root=Path(os.environ['KUANG_PHASE15_RELEASE']);self.host=os.environ['KUANG_SOUNDCRAFT'];self.plugin=os.environ['KUANG_VITALIUM_PLUGIN']
    def tearDown(self):self.tmp.cleanup()
    def test_actual_multiregister_native_pitch_defect_and_center_repair_reload(self):
        gate(self.w/'gates',self.host,self.plugin)
        a=ProductionAdapter(self.host,plugin=self.plugin,workspace=ROOT,scratch=ROOT/'.local/phase15/tmp',center_pitch_bend=True)
        legacy=adapter(self.host,self.plugin);source=load(ROOT/'artifacts/phase14-house/B/project.kuang.json')
        for role,tid,n in [('lead','track-lead',67),('lead','track-lead',65),('lead','track-lead',63),('bass','track-bass',36)]:
            p=held(source,tid,[n]);name=role+str(n);patch=ROOT/'artifacts/phase14-house/B/native/patches'/tid
            legacy.export(p,{}, {tid:patch},self.w/name);legacy.render(self.w/name,self.w/(name+'.wav'))
            r=note_pitch(self.w/(name+'.wav'),n,ON+.5,ON+.9)
            self.assertAlmostEqual(r['fft_cents'],-200,delta=3);self.assertAlmostEqual(r['period_cents'],-200,delta=4)
        good=self.w/'gates/lead-67';bad=json.loads((self.w/'lead67/session.scraft').read_text());goodn=a.inspect(good)['native']
        bad['tracks'][0]['instrument']['params']['1835232641']=.5;self.assertEqual(bad,goodn)
        self.assertEqual((good/'song.mid').read_bytes(),(self.w/'lead67/song.mid').read_bytes())
        a.save(good,self.w/'saved');a.render(self.w/'saved',self.w/'repeat.wav');self.assertEqual(digest(self.w/'repeat.wav'),digest(self.w/'gates/lead-67.wav'))
        self.assertEqual(goodn,a.inspect(self.w/'saved')['native'])
    def test_actual_chord_roots_original_wrong_and_corrected(self):
        src=load(ROOT/'artifacts/phase14-house/B/project.kuang.json');old=load(ROOT/'artifacts/phase13-house/B/project.kuang.json');notes=[51,55,58,62]
        for label,p,center in [('A',old,False),('bad',src,False),('fixed',src,True)]:
            a=ProductionAdapter(self.host,plugin=self.plugin,workspace=ROOT,scratch=ROOT/'.local/phase15/tmp',center_pitch_bend=center)
            q=held(p,'track-harmony',notes);patch={} if label=='A' else {'track-harmony':ROOT/'artifacts/phase14-house/B/native/patches/track-harmony'}
            a.export(q,{},patch,self.w/label);a.render(self.w/label,self.w/(label+'.wav'))
            peaks=spectrum(self.w/(label+'.wav'),ON+.5,ON+.9)[2][:48]
            expected=notes if label!='bad' else [n-2 for n in notes]
            for n in expected:self.assertLess(min(abs(cents(p['hz'],hz(n))) for p in peaks),20)
        self.assertEqual(notes,[51,55,58,62])  # no corrective MIDI transpose
    def test_full_song_preservation_native_reload_zip_relative_replay(self):
        root=self.root;before=inventory(root);p=load(root/'A/project.kuang.json');q=load(root/'B/project.kuang.json');a=adapter(self.host)
        self.assertEqual(export_bytes(p),export_bytes(q));self.assertEqual(p.sections,q.sections);self.assertEqual(p.automation,q.automation)
        for t,u in zip(p.tracks,q.tracks):self.assertEqual((t.clips,t.instrument,t.effects,t.controls),(u.clips,u.instrument,u.effects,u.controls))
        a.save(root/'B/native',self.w/'saved');self.assertEqual(a.inspect(self.w/'saved')['native'],a.inspect(root/'B/native')['native'])
        a.render(self.w/'saved',self.w/'repeated.wav',end_seconds=END);self.assertEqual(digest(self.w/'repeated.wav'),digest(root/'B-Phase15-repaired-native.wav'))
        with zipfile.ZipFile(root/'phase15-house-listening.zip') as z:
            self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'));self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'})
            self.assertFalse(any(k.endswith(('.so','.dll','.vstpreset')) for k in z.namelist()));z.extractall(self.w/'download')
        hiding=[]
        try:
            for path in (root/'B/native',ROOT/'artifacts/phase13-house/B/native'):
                target=path.with_name(path.name+'-hidden-phase15');self.assertFalse(target.exists());path.rename(target);hiding.append((path,target))
            result=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),'--out',str(self.w/'replay'),
                '--workspace',str(ROOT),'--soundcraft',self.host],cwd=self.w,capture_output=True,text=True,timeout=240,check=True)
            self.assertTrue(json.loads(result.stdout)['PCM_exact'])
        finally:
            for path,target in reversed(hiding):target.rename(path)
        self.assertEqual(inventory(root),before)
    def test_actual_shared_room_and_summed_compression_on_off(self):
        p=load(self.root/'B/project.kuang.json');a=adapter(self.host);assets={t.id:self.root/'B/native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
        for mode in ('room','compressor'):
            q=deepcopy(p)
            if mode=='room':next(t for t in q.tracks if t.id=='phase15-shared-room').controls['mixer.mute']=1
            else:next(t for t in q.tracks if t.id=='phase15-drum-sum').effects[0].parameters['effect.bypass']=1
            a.export(q,assets,{},self.w/mode);a.render(self.w/mode,self.w/(mode+'.wav'),end_seconds=END)
            self.assertGreater(compare_wavs(self.root/'B-Phase15-repaired-native.wav',self.w/(mode+'.wav'))['difference_to_original_rms_ratio'],.001)
        r=json.loads((self.root/'verification.json').read_text());self.assertTrue(r['source_notes_MIDI_exact']);self.assertEqual(r['notes'],1536)
        self.assertEqual(r['harmony']['A'],r['harmony']['B'])
        for v in r['levels'].values():self.assertEqual(v['clipped_samples'],0);self.assertLess(v['true_peak_dbtp'],-1)
        self.assertAlmostEqual(*[m['measurement']['integrated_lufs'] for m in r['matching'].values()],delta=.002)
