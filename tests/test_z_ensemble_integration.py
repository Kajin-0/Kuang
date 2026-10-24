"""Optional real mixed-plugin/CC0-sampler/shared-return full-song lifecycle."""
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path
from kuang.audio import compare_wavs
from kuang.ensemble_production import DRUMS,VOICES,isolate,build_ensemble
from kuang.production_host import ProductionAdapter,trim_id,native_pan
from kuang.external_synth import read_patch
from kuang.sample_assets import digest,inventory,write
from kuang.schema import load,save,dumps,state_hash,ValidationError
from kuang.transactions import Scope,SetParameter,receipt_from_dict,replay
from kuang.loudness import measure
from tools.phase14_house import package,END

ROOT=Path(__file__).resolve().parents[1];SCRATCH=ROOT/'.local/phase14/tests'


@unittest.skipUnless(os.environ.get('KUANG_PHASE14_INTEGRATION')=='1','opt in to reviewed SoundCraft/Vitalium and complete Phase14 release')
class EnsembleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(os.environ['KUANG_PHASE14_RELEASE']);self.p=load(self.root/'B/project.kuang.json')
        self.a=ProductionAdapter(os.environ['KUANG_SOUNDCRAFT'],plugin=os.environ['KUANG_VITALIUM_PLUGIN'],workspace=ROOT)
        SCRATCH.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=SCRATCH);self.work=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_all_note_fields_routes_state_markers_and_native_PCM_reopen(self):
        a=self.a;p=self.p;before=inventory(self.root);s=load(self.root/'A/project.kuang.json');n=a.inspect(self.root/'B/native')['native']
        self.assertEqual(len(n['tracks']),17);self.assertEqual(len(n['markers']),6);self.assertEqual(len(n['busses']),4)
        self.assertEqual((p.bars,p.tempo_bpm,p.key_tonic,p.key_mode),(64,126,0,'minor'));self.assertEqual(p.sections,s.sections)
        self.assertEqual(p.metadata['song_spec'],s.metadata['song_spec'])
        self.assertEqual(digest(self.root/'A-Phase13-original-native.wav'),digest(ROOT/'artifacts/phase13-house/B-phase13-drum-palette-native.wav'))
        for t,h in zip(p.tracks,n['tracks']):
            self.assertEqual(h['name'],t.name);self.assertEqual(h['mixer']['output'],'Main' if t.output_master else 'None')
            for x,y in zip(h['mixer']['pan'],native_pan(t)):self.assertAlmostEqual(x,y,delta=1e-6)
            if t.kind=='bus':self.assertEqual(h['kind'],'Aux');continue
            got=Counter((v['start'],v['length'],v['pitch'],v['velocity'],v['channel'],v['release_velocity']) for c in h['playlists'][0]['clips'] for v in c['content']['Midi']['sequence']['notes'])
            want=Counter((c.start+v.start,v.duration,v.pitch,v.velocity,v.channel,0) for c in t.clips for v in c.notes)
            self.assertEqual(got,want)
            if t.id in DRUMS|{'track-bass','track-lead'}:self.assertEqual(t.clips,next(x for x in s.tracks if x.id==t.id).clips)
            if t.id in VOICES:
                path=self.root/'B/native/patches'/t.id
                self.assertEqual(base64.b64decode(h['instrument']['state']),(path/'component.bin').read_bytes())
                _,rows=read_patch(path);self.assertEqual(len(rows),771)
                for row in rows:self.assertAlmostEqual(h['instrument']['params'][row['native_id']],t.instrument.parameters[row['canonical_id']]*row['scale'],delta=2e-5)
        a.save(self.root/'B/native',self.work/'saved');self.assertEqual(a.inspect(self.work/'saved')['native'],n)
        a.render(self.work/'saved',self.work/'repeat.wav',end_seconds=END)
        self.assertEqual(digest(self.work/'repeat.wav'),digest(self.root/'B-Phase14-ensemble-native.wav'));self.assertEqual(inventory(self.root),before)
    def test_causal_controls_actual_audio_stereo_levels_and_reconstruction(self):
        root=Path(os.environ['KUANG_PHASE14_CONTROLS']);r=json.loads((root/'verification.json').read_text());v=json.loads((self.root/'verification.json').read_text())
        self.assertLessEqual(r['independent_reconstruction']['peak_error_lsb'],32)
        for key in ('no-shared-space','no-drum-glue','static-stab-filter'):
            actual=compare_wavs(self.root/'B-Phase14-ensemble-native.wav',root/(key+'.wav'))
            self.assertEqual(actual,r['same_input_effect_controls'][key]);self.assertGreater(actual['difference_to_original_rms_ratio'],.002)
        self.assertTrue(any(x['gain_db']<-.05 for x in r['drum_compressor_envelope']))
        mod=r['pad_modulation_control'];self.assertTrue(mod['same_MIDI_clips']);self.assertTrue(mod['same_effects_and_mixer'])
        self.assertGreater(compare_wavs(root/'pad.wav',root/'pad-mod-off.wav')['difference_to_original_rms_ratio'],.01)
        for m in v['levels'].values():
            self.assertEqual((m['sample_rate'],m['channels'],m['bits_per_sample'],m['frames']),(48000,2,24,6091429))
            self.assertEqual(m['clipped_samples'],0);self.assertLess(m['true_peak_dbtp'],-1)
        for s in v['spatial'].values():
            self.assertGreater(s['bands']['low_20_120']['mono_energy_retention'],.98);self.assertFalse(s['mono_sum']['clipped'])
        self.assertGreater(v['spatial']['B']['bands']['high_over_500']['side_to_mid_power_ratio'],v['spatial']['A']['bands']['high_over_500']['side_to_mid_power_ratio'])
        levels=[measure(path,library=os.environ.get('KUANG_EBUR128'))['integrated_lufs'] for path in sorted((self.root/'listening').glob('*.wav'))]
        self.assertAlmostEqual(*levels,delta=.002);self.assertEqual(v['human_preference'],'unreviewed');self.assertFalse(v['professional_quality_established'])
    def test_edit_sampler_external_bus_effect_pan_and_exact_inverse(self):
        path=self.root/'B/native/patches/track-bass';_,rows=read_patch(path);key=next(x['canonical_id'] for x in rows if x['name']=='Filter 1 Cutoff')
        ops=[SetParameter('set_parameter','phase14-drum-glue','soundcraft.threshold',-25),
             SetParameter('set_parameter','instrument-hats.p46','sample.release_ms',60),
             SetParameter('set_parameter','instrument-bass',key,.65),SetParameter('set_parameter','track-harmony','mixer.pan',.1)]
        scope=Scope(['phase14-drum-sum','track-hats.p46','track-bass','track-harmony'],[],[o.parameter_id for o in ops],None,None)
        self.a.apply(self.root/'B/native',self.work/'edited',ops,scope,state_hash(self.p))
        q=load(self.work/'edited/project.kuang.json');receipt=receipt_from_dict(json.loads((self.work/'edited/receipt.json').read_text()))
        self.assertEqual(dumps(replay(q,receipt,undo=True)),dumps(self.p));self.assertEqual(dumps(replay(self.p,receipt,undo=False)),dumps(q))
        self.assertTrue(json.loads((self.work/'edited/report.json').read_text())['exact_unrelated_native_state'])
        with self.assertRaises(ValidationError):self.a.apply(self.root/'B/native',self.work/'wrong-scope',ops,Scope(['track-bass'],[],[key],None,None),state_hash(self.p))
        self.assertFalse((self.work/'wrong-scope').exists())
    def test_native_send_trim_edit_and_base_overridden_by_lane_rejection(self):
        p=isolate(self.p,['track-lead']);t=p.tracks[0];s=next(s for s in t.sends if s.target_track_id=='phase14-echo');key=trim_id(s)
        with self.assertRaises(ValidationError):self.a.apply(self.root/'B/native',self.work/'overridden',[SetParameter('set_parameter',t.id,key,0)],Scope([t.id],[],[key],None,None),state_hash(self.p))
        p.automation=[a for a in p.automation if not(a.target_id==t.id and a.parameter_id==key)]
        self.a.export(p,{}, {t.id:self.root/'B/native/patches'/t.id},self.work/'static')
        n=self.a.inspect(self.work/'static')['native']
        self.a.apply(self.work/'static',self.work/'throw',[SetParameter('set_parameter',t.id,key,0)],Scope([t.id],[],[key],None,None),state_hash(p))
        expected=deepcopy(n);expected['tracks'][0]['mixer']['sends'][2]['level_db']=-12
        self.assertEqual(self.a.inspect(self.work/'throw')['native'],expected)
        self.a.render(self.work/'static',self.work/'dry.wav');self.a.render(self.work/'throw',self.work/'wet.wav')
        self.assertGreater(compare_wavs(self.work/'dry.wav',self.work/'wet.wav')['difference_to_original_rms_ratio'],.01)
    def test_portable_ZIP_frozen_replay_with_original_paths_hidden(self):
        zpath=self.root/'phase14-house-listening.zip';before=inventory(self.root)
        with zipfile.ZipFile(zpath) as z:
            self.assertIsNone(z.testzip());manifest=json.loads(z.read('zip-manifest.json'))
            self.assertEqual(set(z.namelist()),set(manifest)|{'zip-manifest.json'})
            self.assertTrue(all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in manifest.items()))
            self.assertEqual(len([k for k in z.namelist() if k.startswith('listening/') and k.endswith('.wav')]),2)
            self.assertFalse(any(k.endswith(('.so','.dll','.deb')) for k in z.namelist()));z.extractall(self.work/'download')
        self.assertLess(zpath.stat().st_size,180_000_000)
        moved=self.work/'external/Vitalium.vst3';moved.parent.mkdir();shutil.copytree(Path(os.environ['KUANG_VITALIUM_PLUGIN']),moved)
        hiding=[]
        try:
            for path in (self.root/'B/native',ROOT/'.local/phase14/patches-balanced',ROOT/'artifacts/phase13-house/B/native'):
                if path.exists():
                    target=path.with_name(path.name+'-hidden-phase14');self.assertFalse(target.exists());path.rename(target);hiding.append((path,target))
            run=subprocess.run([sys.executable,'-I',str(self.work/'download/reproduce.py'),'--source',str(self.work/'download'),
                '--out',str(self.work/'reproduced'),'--workspace',str(ROOT),'--soundcraft',os.environ['KUANG_SOUNDCRAFT'],'--plugin',str(moved)],
                cwd=self.work,capture_output=True,text=True,timeout=240,check=True)
            self.assertTrue(json.loads(run.stdout)['PCM_exact'])
        finally:
            for path,target in reversed(hiding):target.rename(path)
        self.assertEqual(inventory(self.root),before)
    def test_fail_closed_drift_noclobber_and_unsupported_note_operation(self):
        before=inventory(self.root)
        with self.assertRaises(ValidationError):self.a.save(self.root/'B/native',self.root/'B/native')
        with self.assertRaises(ValidationError):package(self.root)
        with self.assertRaises(ValidationError):self.a.apply(self.root/'B/native',self.work/'bad-op',[object()],Scope([],[],[],None,None),state_hash(self.p))
        shutil.copytree(self.root/'B/native',self.work/'drift');path=self.work/'drift/Audio Files';media=next(path.glob('*'))
        with media.open('ab') as f:f.write(b'drift')
        with self.assertRaises(ValidationError):self.a.save(self.work/'drift',self.work/'invalid')
        self.assertFalse((self.work/'invalid').exists());self.assertEqual(inventory(self.root),before)
        # Shared routing is also a free built-in-only path. No VST/sampler
        # asset is needed for this separate positive capability gate.
        from kuang.atmosphere import atmosphere_house
        from kuang.gestures import crop
        from kuang.schema import Track,Send
        from kuang.production_host import add_spread
        q=crop(atmosphere_house(),32,1,['track-harmony']);q.automation=[];q.tracks[0].effects=[]
        q.tracks[0].controls['mixer.gain_db']=-18  # headroom after removing the original shaping chain
        dry=deepcopy(q);bus=Track('independent-bus','Independent room','bus',None,
            {'mixer.gain_db':6.020599913279624,'mixer.pan':0,'mixer.mute':0},
            deepcopy(next(t for t in self.p.tracks if t.id=='phase14-short-room').effects),[],[],True)
        q.tracks.append(bus);add_spread(q,bus,1);q.tracks[0].sends=[Send('independent-send',bus.id,-12,0,'post_fader')]
        a=ProductionAdapter(os.environ['KUANG_SOUNDCRAFT'],workspace=ROOT)
        self.assertIsNone(a.capabilities()['external_plugin']);a.export(q,{}, {},self.work/'builtin-wet')
        a.export(dry,{}, {},self.work/'builtin-dry');a.render(self.work/'builtin-wet',self.work/'builtin-wet.wav')
        a.render(self.work/'builtin-dry',self.work/'builtin-dry.wav')
        self.assertGreater(compare_wavs(self.work/'builtin-dry.wav',self.work/'builtin-wet.wav')['difference_to_original_rms_ratio'],.002)
