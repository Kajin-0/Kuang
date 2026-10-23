"""Installed host, independent native/PCM state checks and off-host replay."""
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.gestures import gesture_house
from kuang.mastering import apply_master,file_hash
from kuang.schema import dumps,load,save,state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import Scope,SetParameter,receipt_from_dict,replay
from kuang.translation import translation_house
from tools.phase9_host_gate import gate
from tools.phase9_house import ROOT,SCRATCH,build,inventory,package


@unittest.skipUnless(os.environ.get('KUANG_SOUNDCRAFT_INTEGRATION')=='1','opt in to installed SoundCraft translation/master proof')
class TranslationIntegrationTests(unittest.TestCase):
    def test_real_native_stems_meter_master_asset_gate_replay_and_zip(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);selected=os.environ.get('KUANG_SOUNDCRAFT_ARTIFACTS')
        temp=tempfile.TemporaryDirectory(dir=SCRATCH) if not selected else None
        root=Path(selected+'-phase9' if selected else temp.name)
        if root.exists() and any(root.iterdir()):raise RuntimeError('new/empty Phase 9 proof required')
        root.mkdir(parents=True,exist_ok=True)
        try:
            a=SoundCraftAdapter(timeout=240);old=gesture_house();source=root/'source';source.mkdir()
            save(old,source/'project.kuang.json');a.export(old,source/'native')
            end=old.length/960*60/126+5
            a.render(source/'native',source/'B-phase8-motion-64bars.wav',end_seconds=end)
            before=inventory([source]);out=root/'release'
            r=build(out,source=source,executable=str(a.executable),library=os.environ.get('KUANG_EBUR128'))
            p=load(out/'project.kuang.json');self.assertEqual(dumps(p),dumps(translation_house(old)))
            self.assertTrue(r['same_all_notes']);self.assertTrue(r['same_all_automation'])
            self.assertEqual(r['note_deviations'],[]);self.assertEqual(before,inventory([source]))
            native=a.inspect(out/'native')['native']
            self.assertEqual(native,a.inspect(out/'saved-native')['native'])
            self.assertEqual(dumps(p),dumps(a.import_project(out/'saved-native')))
            self.assertEqual(len(native['markers']),6)
            for m,s in zip(native['markers'],p.sections):
                self.assertEqual((m['name'],m['start'],m['end']),
                    (s.name,round(s.start*48000*60/(960*126)),round((s.start+s.length)*48000*60/(960*126))))
            for t,h in zip(p.tracks,native['tracks']):
                actual=[(n['start'],n['length'],n['pitch'],n['velocity'],n['channel'],n['release_velocity'])
                    for c in h['playlists'][0]['clips'] for n in c['content']['Midi']['sequence']['notes']]
                expected=[(c.start+n.start,n.duration,n.pitch,n.velocity,n.channel,0) for c in t.clips for n in c.notes]
                self.assertEqual(Counter(actual),Counter(expected))
                inserts=[e for e in h['mixer']['inserts'] if e]
                self.assertEqual([e['plugin'] for e in inserts],[e.plugin_ref.split(':')[1] for e in t.effects])
                for e,n in zip(t.effects,inserts):
                    for k,v in e.parameters.items():
                        if k=='effect.bypass':self.assertEqual(n['bypass'],bool(v));continue
                        param=k.removeprefix('soundcraft.');unit=next(x.unit for x in p.parameters if x.id==k)
                        if k=='effect.wet':param='mix';v*=100
                        elif param=='decay_ms':param='decay';v/=1000
                        elif param.endswith('_slope'):v*=3
                        elif unit=='normalized':v*=100
                        self.assertAlmostEqual(n['params'][param],v,delta=.002)
                if t.id in ('track-kick','track-bass'):self.assertEqual(h['mixer']['pan'],[0,0])
                for lane in (x for x in p.automation if x.target_id in {t.id,*(e.id for e in t.effects)}):
                    if lane.target_id==t.id:
                        addresses=['Volume'] if lane.parameter_id=='mixer.gain_db' else [{'Pan':0},{'Pan':1}];factor=1
                    else:
                        slot=next(i for i,e in enumerate(t.effects) if e.id==lane.target_id)
                        param='mix' if lane.parameter_id=='effect.wet' else lane.parameter_id.removeprefix('soundcraft.')
                        addresses=[{'Plugin':{'slot':slot,'param':param}}];factor=100 if param=='mix' else 1
                    for address in addresses:
                        n=next(x for x in h['automation'] if x['param']==address)
                        self.assertTrue(n['enabled']);self.assertEqual(h['mixer']['automation_mode'],'Read')
                        self.assertEqual([x['at'] for x in n['points']],[round(x.tick*48000*60/(960*126)) for x in lane.points])
                        for x,y in zip(n['points'],lane.points):self.assertAlmostEqual(x['value'],y.value*factor,delta=.002)
            a.render(out/'saved-native',root/'reopened.wav',end_seconds=end)
            self.assertEqual(file_hash(root/'reopened.wav'),file_hash(out/'B-phase9-premaster.wav'))
            for m in r['metrics'].values():
                self.assertEqual((m['sample_rate'],m['channels'],m['bits_per_sample']),(48000,2,24))
                self.assertEqual(m['frames'],6091429);self.assertEqual(m['clipped_samples'],0)
                self.assertIsNotNone(m['integrated_lufs']);self.assertFalse(m['certified'])
            self.assertLess(r['metrics']['C']['true_peak_dbtp'],-1)
            self.assertFalse(r['master_native_editable']);self.assertFalse(r['master']['native_editable'])
            for values in (r['matching'],r['drop_matching']):
                levels=[x['measurement']['integrated_lufs'] for x in values.values()]
                self.assertLess(max(levels)-min(levels),.002)
                self.assertTrue(all(x['gain_db']<=0 for x in values.values()))
            d=r['stems']['deltas'];self.assertGreater(d['bass_absolute_100_400_db'],3)
            self.assertLess(abs(d['bass_rms_change_db']),1);self.assertGreater(d['kick_attack_change_db'],1)
            self.assertLess(d['kick_tail_change_db'],-3)
            self.assertGreater(r['stems']['B-interaction']['interference_db'],-.5)
            self.assertTrue(r['stems']['saturation_difference']['measurable_change'])
            self.assertLess(r['music_meter_audit']['python8']['true_peak_dbtp']-r['music_meter_audit']['python4']['true_peak_dbtp'],.1)
            for v in r['spatial'].values():
                self.assertGreater(v['bands']['low_20_120']['mono_energy_retention'],.99)
                self.assertGreater(v['bands']['high_over_500']['mono_energy_retention'],.7)
                self.assertLess(v['last_250ms']['rms'],10**(-65/20))
            apply_master(out/'B-phase9-premaster.wav',root/'master-repeated.wav',r['master']['recipe'])
            self.assertEqual(file_hash(root/'master-repeated.wav'),file_hash(out/'C-phase9-master-OFFHOST.wav'))
            # Exact native scalar edit with complete unrelated-state equality.
            i=next(i for i,t in enumerate(p.tracks) if t.id=='track-bass')
            op=SetParameter('set_parameter','effect-bass-saturation','soundcraft.output',1)
            a.apply(out/'native',root/'edited',[op],Scope(['track-bass'],[],['soundcraft.output'],None,None),state_hash(p))
            q=a.inspect(root/'edited')['native'];expected=deepcopy(native)
            expected['tracks'][i]['mixer']['inserts'][2]['params']['output']=1
            self.assertEqual(q,expected)
            receipt=receipt_from_dict(json.loads((root/'edited/receipt.json').read_text()));edited=a.import_project(root/'edited')
            self.assertEqual(dumps(replay(edited,receipt,undo=True)),dumps(p))
            self.assertEqual(dumps(replay(p,receipt,undo=False)),dumps(edited))
            host=gate(root/'host-gate',str(a.executable));self.assertTrue(host['full_native_equal']);self.assertTrue(host['pcm_equal'])
            self.assertFalse(host['canonical_sampler_supported']);self.assertFalse(host['candidate_uses_sampler'])
            download=package(out)
            with zipfile.ZipFile(download['zip']) as z:
                self.assertIsNone(z.testzip())
                for f in (out/'native').iterdir():
                    if f.is_file():self.assertEqual(z.read('editable-B/native/'+f.name),f.read_bytes())
                self.assertEqual(z.read('B-phase9-premaster.wav'),(out/'B-phase9-premaster.wav').read_bytes())
                self.assertFalse(any(x.endswith(('.so','.vst3','.clap')) for x in z.namelist()))
                extracted=root/'extracted';z.extractall(extracted)
            # The actual downloaded standalone script, away from checkout
            # imports, must reconstruct the exact C from raw B and the recipe.
            result=subprocess.run([os.sys.executable,str(extracted/'reproduce/master.py'),
                str(extracted/'B-phase9-premaster.wav'),str(root/'zip-repeated.wav'),
                '--recipe',str(extracted/'reproduce/master-recipe.json')],cwd=extracted,
                capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(file_hash(root/'zip-repeated.wav'),file_hash(out/'C-phase9-master-OFFHOST.wav'))
            (root/'independent-checks.json').write_text(json.dumps({'every_native_note_field':True,'fx_and_lane_units':True,
                'native_and_pcm_reopen_exact':True,'exact_scoped_edit_and_replay':True,'all_notes_and_automation_preserved':True,
                'absolute_harmonic_and_transient_gates':True,'lufs_matched':True,'master_recipe_exact':True,
                'actual_zip_script_exact':True,'host_sampler_assets_relocated':True,'download':download},indent=2)+'\n')
        finally:
            if temp:temp.cleanup()
