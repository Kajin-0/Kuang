"""Real tuned VST3 source sounds, full context, portable native editability."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from copy import deepcopy
from kuang.schema import load,dumps
from kuang.sample_assets import digest, inventory
from kuang.sound_palette import performance, sound_palette
from kuang.studio_palette import TRACKS
from kuang.external_synth import bound_project
from kuang.ensemble_production import isolate
from kuang.audio import compare_wavs
from kuang.loudness import measure
from kuang.midi import export_bytes
from tools.phase16_pitch import gate
from tools.phase16_house import adapter, END, AUDIO
ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('KUANG_PHASE16_INTEGRATION')=='1','opt in to actual pitch-centered Vitalium and full Phase16 release')
class StudioIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(os.environ['KUANG_PHASE16_RELEASE']);self.host=os.environ['KUANG_SOUNDCRAFT'];self.plugin=os.environ['KUANG_VITALIUM_PLUGIN']
        scratch=ROOT/'.local/phase16/tests';scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.w=Path(self.temp.name)
        self.a=adapter(self.host,self.plugin)
    def tearDown(self):self.temp.cleanup()

    def test_actual_nine_notes_each_voice_three_windows_poly_chords_both_hosts(self):
        # Fresh actual renders, not a report-only assertion. Patches are copied
        # out by role; gate also saves/reopens and compares full native state.
        patches=self.w/'role-patches';patches.mkdir()
        for tid,voice in TRACKS.items():shutil.copytree(self.root/'B/native/patches'/tid,patches/voice)
        r=gate(self.w/'pitch',self.root/'A/project.kuang.json',patches,self.host,self.plugin,os.environ['KUANG_VITALIUM_HOST_PYTHON'])
        self.assertEqual(set(r),set(TRACKS.values()))
        for voice,value in r.items():
            for host in ('native','independent'):
                for rows in value[host]['notes'].values():
                    for row in rows:
                        self.assertLessEqual(abs(row['fft_cents']),5);self.assertLessEqual(abs(row['period_cents']),5)
                self.assertEqual(len(value[host]['chord']),1 if voice=='bass' else 4)

    def test_full_song_performance_source_PCM_native_reopen_and_matched_levels(self):
        p=load(self.root/'A/project.kuang.json');q=load(self.root/'B/project.kuang.json')
        self.assertEqual(performance(p),performance(q));self.assertEqual(export_bytes(p),export_bytes(q))
        expected,_=sound_palette(p,{t:self.root/'B/native/patches'/t for t in TRACKS})
        self.assertEqual(dumps(q),dumps(expected))
        for t,u in zip(p.tracks,q.tracks):
            if t.id not in TRACKS:self.assertEqual(t,u)
            if t.id!='track-harmony':self.assertEqual(t.effects,u.effects)
            self.assertEqual(t.sends,u.sends)
        self.a.save(self.root/'B/native',self.w/'saved')
        self.assertEqual(self.a.inspect(self.w/'saved')['native'],self.a.inspect(self.root/'B/native')['native'])
        self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END)
        self.assertEqual(digest(self.w/'repeat.wav'),digest(self.root/AUDIO['B']))
        self.assertEqual(digest(self.root/AUDIO['A']),digest(ROOT/'artifacts/phase15-house/B-Phase15-repaired-native.wav'))
        levels=[measure(p,library=os.environ.get('KUANG_EBUR128')) for p in sorted((self.root/'listening').glob('*.wav'))]
        self.assertEqual(len(levels),2);self.assertAlmostEqual(levels[0]['integrated_lufs'],levels[1]['integrated_lufs'],delta=.002)
        for m in levels:self.assertEqual(m['clipped_samples'],0);self.assertLess(m['true_peak_dbtp'],-1)

    def test_same_input_real_timbral_modulation_and_shared_room_are_not_inert(self):
        p=load(self.root/'B/project.kuang.json');patches={t:self.root/'B/native/patches'/t for t in TRACKS}
        off=Path(os.environ['KUANG_PHASE16_MOD_OFF'])
        for tid,voice in TRACKS.items():
            stem=isolate(p,{tid});off_stem=bound_project(stem,{tid:off/voice})
            self.assertEqual(performance(stem),performance(off_stem))
            for label,q,patch in [('on',stem,patches[tid]),('off',off_stem,off/voice)]:
                name=voice+'-'+label;self.a.export(q,{}, {tid:patch},self.w/name)
                self.a.render(self.w/name,self.w/(name+'.wav'),end_seconds=END)
            difference=compare_wavs(self.w/(voice+'-on.wav'),self.w/(voice+'-off.wav'))
            self.assertGreater(difference['difference_to_original_rms_ratio'],.02)
        q=deepcopy(p);next(t for t in q.tracks if t.id=='phase15-shared-room').controls['mixer.mute']=1
        assets={t.id:self.root/'B/native/assets'/t.id for t in q.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
        self.a.export(q,assets,patches,self.w/'room-off');self.a.render(self.w/'room-off',self.w/'room-off.wav',end_seconds=END)
        self.assertGreater(compare_wavs(self.root/AUDIO['B'],self.w/'room-off.wav')['difference_to_original_rms_ratio'],.001)

    def test_ZIP_relative_assets_patch_source_hidden_and_relocated_plugin_replay(self):
        before=inventory(self.root)
        with zipfile.ZipFile(self.root/'phase16-house-listening.zip') as z:
            self.assertIsNone(z.testzip());m=json.loads(z.read('zip-manifest.json'))
            self.assertEqual(set(z.namelist()),set(m)|{'zip-manifest.json'})
            self.assertEqual(len([n for n in z.namelist() if n.endswith('.wav') and n.startswith('listening/')]),2)
            self.assertFalse(any(n.endswith(('.so','.dll','.mp3')) for n in z.namelist()))
            z.extractall(self.w/'download')
        moved=self.w/'external/vitalium.vst3';moved.parent.mkdir();shutil.copytree(self.plugin,moved)
        hidden=[]
        try:
            for path in (self.root/'B/native', ROOT/'.local/phase16/patches-final', Path(self.plugin)):
                if not path.exists():continue
                target=path.with_name(path.name+'-phase16-hidden');self.assertFalse(target.exists());path.rename(target);hidden.append((path,target))
            result=subprocess.run([sys.executable,'-I',str(self.w/'download/reproduce.py'),'--source',str(self.w/'download'),
                  '--out',str(self.w/'replayed'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(moved)],
                  cwd=self.w,capture_output=True,text=True,timeout=240,check=True)
            self.assertTrue(json.loads(result.stdout)['PCM_exact'])
        finally:
            for path,target in reversed(hidden):target.rename(path)
        self.assertEqual(inventory(self.root),before)
