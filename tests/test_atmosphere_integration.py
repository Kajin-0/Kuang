"""Independent full native repeat and real controls; no host/library download."""
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.atmosphere import PULSE_ID,atmosphere_house
from kuang.atmosphere_audio import pulse_windows,sample_steps,sub_power
from kuang.audio import compare_wavs
from kuang.gestures import crop
from kuang.loudness import measure
from kuang.mastering import file_hash
from kuang.schema import dumps,load,save,state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.spatial_audio import spatial_metrics
from kuang.transactions import Scope,SetParameter,receipt_from_dict,replay
from kuang.translation import translation_house
from tools.phase10_house import ROOT,SCRATCH,build,inventory,package


@unittest.skipUnless(os.environ.get('KUANG_SOUNDCRAFT_INTEGRATION')=='1','opt in to real SoundCraft space/pulse proof')
class AtmosphereIntegrationTests(unittest.TestCase):
    def test_full_native_repeat_controls_source_preservation_and_portable_master(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);selected=os.environ.get('KUANG_SOUNDCRAFT_ARTIFACTS')
        temp=tempfile.TemporaryDirectory(dir=SCRATCH) if not selected else None
        root=Path(selected+'-phase10' if selected else temp.name)
        if root.exists() and any(root.iterdir()):raise RuntimeError('new/empty Phase 10 host proof required')
        root.mkdir(parents=True,exist_ok=True)
        try:
            a=SoundCraftAdapter(timeout=240);end=64*4*60/126+5
            supplied=os.environ.get('KUANG_PHASE10_RELEASE')
            if supplied:
                release=Path(supplied).resolve()
            else:
                source=root/'source';source.mkdir();old=translation_house();save(old,source/'project.kuang.json')
                a.export(old,source/'native');a.render(source/'native',source/'B-phase9-premaster.wav',end_seconds=end)
                release=root/'release';build(release,source=source,executable=str(a.executable),library=os.environ.get('KUANG_EBUR128'))
                package(release)
            before=inventory([release]);r=json.loads((release/'verification.json').read_text());p=load(release/'project.kuang.json')
            self.assertEqual(dumps(p),dumps(atmosphere_house()))
            self.assertTrue(r['original_notes_exact']);self.assertFalse(r['human_listening']);self.assertFalse(r['master_native_editable'])
            a.export(p,root/'independent-native');a.save(root/'independent-native',root/'reopened-native')
            native=a.inspect(root/'independent-native')['native']
            self.assertEqual(native,a.inspect(root/'reopened-native')['native'])
            self.assertEqual(native,a.inspect(release/'native')['native'])
            self.assertEqual(dumps(a.import_project(root/'reopened-native')),dumps(p))
            self.assertEqual(len(native['markers']),6)
            for marker,section in zip(native['markers'],p.sections):
                self.assertEqual((marker['name'],marker['start'],marker['end']),
                    (section.name,round(section.start*48000*60/(960*126)),round((section.start+section.length)*48000*60/(960*126))))
            for t,h in zip(p.tracks,native['tracks']):
                actual=[(n['start'],n['length'],n['pitch'],n['velocity'],n['channel'],n['release_velocity'])
                        for c in h['playlists'][0]['clips'] for n in c['content']['Midi']['sequence']['notes']]
                expected=[(c.start+n.start,n.duration,n.pitch,n.velocity,n.channel,0) for c in t.clips for n in c.notes]
                self.assertEqual(Counter(actual),Counter(expected))
                inserts=[e for e in h['mixer']['inserts'] if e]
                self.assertEqual([x['plugin'] for x in inserts],[e.plugin_ref.split(':')[1] for e in t.effects])
                for e,n in zip(t.effects,inserts):
                    for key,value in e.parameters.items():
                        if key=='effect.bypass':self.assertEqual(n['bypass'],bool(value));continue
                        param=key.removeprefix('soundcraft.');unit=next(x.unit for x in p.parameters if x.id==key)
                        if key=='effect.wet':param='mix';value*=100
                        elif param=='decay_ms':param='decay';value/=1000
                        elif param.endswith('_slope'):value*=3
                        elif param=='type':value*=6
                        elif unit=='normalized':value*=100
                        self.assertAlmostEqual(n['params'][param],value,delta=.002)
                if t.id in ('track-kick','track-bass',PULSE_ID):self.assertEqual(h['mixer']['pan'],[0,0])
                if t.id==PULSE_ID:
                    self.assertEqual(h['instrument']['params']['osc1_wave'],2)
                    self.assertEqual(h['instrument']['params']['osc2_wave'],2)
                    self.assertEqual(h['instrument']['params']['osc_mix'],0)
                    self.assertEqual(inserts[-1]['params']['type'],4);self.assertEqual(inserts[-1]['params']['freq'],140)
                for lane in (x for x in p.automation if x.target_id in {t.id,*(e.id for e in t.effects)}):
                    if lane.target_id==t.id:
                        addresses=['Volume'] if lane.parameter_id=='mixer.gain_db' else [{'Pan':0},{'Pan':1}];factor=1
                    else:
                        slot=next(i for i,e in enumerate(t.effects) if e.id==lane.target_id)
                        param='mix' if lane.parameter_id=='effect.wet' else lane.parameter_id.removeprefix('soundcraft.')
                        addresses=[{'Plugin':{'slot':slot,'param':param}}];factor=100 if param=='mix' else 1
                    for address in addresses:
                        observed=next(x for x in h['automation'] if x['param']==address)
                        self.assertTrue(observed['enabled']);self.assertEqual(h['mixer']['automation_mode'],'Read')
                        self.assertEqual([x['at'] for x in observed['points']],[round(x.tick*48000*60/(960*126)) for x in lane.points])
                        for x,y in zip(observed['points'],lane.points):self.assertAlmostEqual(x['value'],y.value*factor,delta=.002)
            a.render(root/'reopened-native',root/'independent-D.wav',end_seconds=end)
            self.assertEqual(file_hash(root/'independent-D.wav'),file_hash(release/'D-phase10-combined-native.wav'))
            q=crop(p,32,8,[PULSE_ID]);a.export(q,root/'independent-pulse')
            a.render(root/'independent-pulse',root/'independent-pulse.wav',end_seconds=8*4*60/126+8)
            self.assertEqual(file_hash(root/'independent-pulse.wav'),file_hash(release/'controls/pulse/audio.wav'))
            c=r['controls'];self.assertTrue(c['pulse_accepted'])
            self.assertTrue(-20<=c['pulse_relative_bass_db']<=-10)
            windows=pulse_windows(release/'controls/lowend-ON/audio.wav',release/'controls/lowend-OFF/audio.wav')
            self.assertGreaterEqual(windows['minimum_db'],-.75)
            powers=[sub_power(release/('controls/'+key+'/audio.wav'),8*4*60/126)['mean_square'] for key in ('lowend-OFF','lowend-ON')]
            import math
            self.assertTrue(-.15<=10*math.log10(powers[1]/powers[0])<=.35)
            self.assertLess(sample_steps(root/'independent-pulse.wav')['maximum_adjacent_sample_step'],.005)
            self.assertEqual(c['voice_leakage']['before']['rms'],0);self.assertLessEqual(c['voice_leakage']['released']['rms'],1e-6)
            self.assertTrue(-1.8<=c['pad_rms_change_db']<=.4)
            self.assertTrue(compare_wavs(release/'controls/pads-wet/audio.wav',release/'controls/pads-dry/audio.wav')['measurable_change'])
            self.assertLess(c['echo_timing']['max_spacing_error_ms'],10)
            for label in ('A','D','E'):
                m=measure(release/'listening'/(label+'-full-LUFS-matched.wav'),library=os.environ.get('KUANG_EBUR128'))
                self.assertAlmostEqual(m['integrated_lufs'],r['matching'][label]['target_lufs'],delta=.001)
                self.assertEqual(m['clipped_samples'],0);self.assertEqual(m['frames'],6091429)
            s=spatial_metrics(root/'independent-D.wav')
            self.assertGreater(s['bands']['low_20_120']['mono_energy_retention'],.99)
            self.assertGreater(s['bands']['high_over_500']['mono_energy_retention'],.85)
            self.assertGreaterEqual(s['bands']['high_over_500']['side_to_mid_power_ratio'],r['spatial']['A']['bands']['high_over_500']['side_to_mid_power_ratio']*1.15)
            self.assertLess(s['last_250ms']['rms'],10**(-65/20))
            op=SetParameter('set_parameter','effect-sub-pulse-lowpass','soundcraft.freq',135)
            a.apply(root/'independent-native',root/'edited',[op],Scope([PULSE_ID],[],['soundcraft.freq'],None,None),state_hash(p))
            changed=a.inspect(root/'edited')['native'];expected=deepcopy(native)
            expected['tracks'][-1]['mixer']['inserts'][1]['params']['freq']=135
            self.assertEqual(changed,expected)
            receipt=receipt_from_dict(json.loads((root/'edited/receipt.json').read_text()));edited=a.import_project(root/'edited')
            self.assertEqual(dumps(replay(edited,receipt,undo=True)),dumps(p))
            self.assertEqual(dumps(replay(p,receipt,undo=False)),dumps(edited))
            archive=release/'phase10-house-listening.zip';self.assertLessEqual(archive.stat().st_size,180000000)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                for f in (release/'native').iterdir():
                    if f.is_file():self.assertEqual(z.read('editable-D/native/'+f.name),f.read_bytes())
                self.assertFalse(any(x.lower().endswith(('.mp3','.flac','.clap','.vst3','.so')) for x in z.namelist()))
                extracted=root/'download';z.extractall(extracted)
            result=subprocess.run([os.sys.executable,str(extracted/'reproduce/master.py'),str(extracted/'D-phase10-combined-native.wav'),
                str(root/'repeated-E.wav'),'--recipe',str(extracted/'reproduce/master-recipe.json')],cwd=extracted,capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(file_hash(root/'repeated-E.wav'),file_hash(release/'E-phase10-master-OFFHOST.wav'))
            self.assertEqual(inventory([release]),before)
            (root/'independent-checks.json').write_text(json.dumps({'full_native_repeat':True,'all_note_fields_fx_lane_points_markers':True,
                'pulse_repeated_pcm_exact':True,'actual_pcm_acceptance_gates':True,'lufs_match_remeasured':True,
                'scoped_native_edit_and_replay':True,'actual_zip_master_exact':True,'read_only_release_unchanged':True},indent=2)+'\n')
        finally:
            if temp:temp.cleanup()
