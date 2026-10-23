"""Opt-in, pinned real-host gestures: complete native state and real PCM."""

import hashlib
import json
import os
import tempfile
import unittest
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.gestures import gesture_house
from kuang.house_song import arrange_house
from kuang.schema import AutomationPoint, dumps, load, save, state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import AddAutomationPoints, Scope, SetParameter, receipt_from_dict, replay
from tools.phase8_house import ROOT, SCRATCH, build, inventory, package


@unittest.skipUnless(os.environ.get('KUANG_SOUNDCRAFT_INTEGRATION')=='1','opt in to installed SoundCraft gesture audio proof')
class GestureIntegrationTests(unittest.TestCase):
    def test_real_sweeps_echoes_reverb_pump_native_roundtrip_edit_and_download(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        selected=os.environ.get('KUANG_SOUNDCRAFT_ARTIFACTS')
        temp=tempfile.TemporaryDirectory(dir=SCRATCH) if not selected else None
        root=Path(selected+'-phase8' if selected else temp.name)
        if root.exists() and any(root.iterdir()):raise RuntimeError('new/empty Phase 8 proof required')
        root.mkdir(parents=True,exist_ok=True)
        try:
            a=SoundCraftAdapter(timeout=240);old=arrange_house()
            source=root/'source';source.mkdir();save(old,source/'project.kuang.json')
            a.export(old,source/'native')
            a.render(source/'native',source/'C-phase7-house-64bars.wav',end_seconds=old.length/960*60/126+5)
            before=inventory([source]);out=root/'release'
            r=build(out,source=source,executable=str(a.executable));p=load(out/'project.kuang.json')
            self.assertEqual(dumps(p),dumps(gesture_house(old)))
            self.assertTrue(r['sources_unchanged']);self.assertEqual(before,inventory([source]))
            self.assertFalse(r['human_listening']);self.assertFalse(r['club_ready'])
            native=a.inspect(out/'native')['native']
            self.assertEqual(native,a.inspect(out/'saved-native')['native'])
            self.assertEqual(dumps(p),dumps(a.import_project(out/'saved-native')))
            self.assertEqual(len(native['markers']),6)
            for m,s in zip(native['markers'],p.sections):
                self.assertEqual((m['name'],m['start'],m['end']),
                    (s.name,round(s.start*48000*60/(960*126)),round((s.start+s.length)*48000*60/(960*126))))
            for t,h in zip(p.tracks,native['tracks']):
                notes=[(n['start'],n['length'],n['pitch'],n['velocity'],n['channel'],n['release_velocity'])
                    for c in h['playlists'][0]['clips'] for n in c['content']['Midi']['sequence']['notes']]
                expected=[(c.start+n.start,n.duration,n.pitch,n.velocity,n.channel,0) for c in t.clips for n in c.notes]
                self.assertEqual(Counter(notes),Counter(expected))
                inserts=[e for e in h['mixer']['inserts'] if e]
                self.assertEqual([e['plugin'] for e in inserts],[e.plugin_ref.split(':')[1] for e in t.effects])
                for e,native_fx in zip(t.effects,inserts):
                    for key,value in e.parameters.items():
                        if key=='effect.bypass':self.assertEqual(native_fx['bypass'],bool(value));continue
                        param=key.removeprefix('soundcraft.')
                        unit=next(x.unit for x in p.parameters if x.id==key)
                        if key=='effect.wet':param='mix';value*=100
                        elif param=='decay_ms':param='decay';value/=1000
                        elif param.endswith('_slope'):value*=3
                        elif unit=='normalized':value*=100
                        self.assertAlmostEqual(native_fx['params'][param],value,delta=.002)
                if t.id in ('track-kick','track-bass'):self.assertEqual(h['mixer']['pan'],[0,0])
                owners={t.id,*(e.id for e in t.effects)}
                for lane in (x for x in p.automation if x.target_id in owners):
                    if lane.target_id==t.id:
                        addresses=['Volume'] if lane.parameter_id=='mixer.gain_db' else [{'Pan':0},{'Pan':1}]
                        factor=1
                    else:
                        slot=next(i for i,e in enumerate(t.effects) if e.id==lane.target_id)
                        param='mix' if lane.parameter_id=='effect.wet' else lane.parameter_id.removeprefix('soundcraft.')
                        addresses=[{'Plugin':{'slot':slot,'param':param}}]
                        factor=100 if param=='mix' else 1
                    for address in addresses:
                        actual=next(x for x in h['automation'] if x['param']==address)
                        self.assertTrue(actual['enabled']);self.assertEqual(h['mixer']['automation_mode'],'Read')
                        self.assertEqual([x['at'] for x in actual['points']],
                            [round(x.tick*48000*60/(960*126)) for x in lane.points])
                        for x,y in zip(actual['points'],lane.points):self.assertAlmostEqual(x['value'],y.value*factor,delta=.002)
            # Full saved-native render, exact PCM equality. Native persistence
            # is independently exercised beyond comparing JSON parameters.
            a.render(out/'saved-native',root/'reopened.wav',end_seconds=p.length/960*60/126+5)
            self.assertEqual(hashlib.sha256((root/'reopened.wav').read_bytes()).hexdigest(),
                hashlib.sha256((out/'B-phase8-motion-64bars.wav').read_bytes()).hexdigest())
            self.assertEqual((out/'A-phase7-original-64bars.wav').read_bytes(),(source/'C-phase7-house-64bars.wav').read_bytes())
            m=r['metrics']['phase8']
            self.assertEqual((m['sample_rate'],m['bits_per_sample'],m['channels']),(48000,24,2))
            self.assertEqual(m['clipped_samples'],0);self.assertGreater(m['rms'],1e-4)
            self.assertAlmostEqual(m['duration_seconds'],64*4*60/126+5,delta=1/48000)
            self.assertLess(m['sections']['Breakdown']['rms'],m['sections']['Main Drop']['rms']*.7)
            levels=list(r['rms_matching'].values())
            self.assertAlmostEqual(levels[0]['audio']['rms_dbfs'],levels[1]['audio']['rms_dbfs'],places=4)
            self.assertTrue(all(x['gain_db']<=0 for x in levels))
            dsp=r['dsp']
            self.assertLess(dsp['filter_deltas']['late_hpf_lowmid_db'],-3)
            self.assertLess(dsp['filter_deltas']['early_lpf_high_db'],-4)
            self.assertLess(dsp['pump_phase_energy']['duck']['on_off_db'],-6)
            self.assertGreater(dsp['pump_phase_energy']['open']['on_off_db'],-2)
            self.assertLess(dsp['compression']['peak_gain_db'],-1)
            self.assertGreater(dsp['compression']['envelope']['gain_variation_db'],1)
            self.assertLess(dsp['delay_peak_timing']['max_spacing_error_ms'],10)
            self.assertGreaterEqual(sum(v['wet_rms']>max(1e-5,v['dry_rms']*2) for v in dsp['delay_echo_windows'].values()),2)
            self.assertGreater(r['spatial']['bands']['low_20_120']['mono_energy_retention'],.99)
            self.assertGreater(r['spatial']['bands']['high_over_500']['mono_energy_retention'],.7)
            self.assertLess(r['spatial']['last_250ms']['rms'],10**(-65/20))
            for control in dsp['controls'].values():
                if 'difference' in control:self.assertTrue(control['difference']['measurable_change']);self.assertTrue(control['same_midi'])
            # Legitimate Hz/ms editing of new lanes and existing delay controls;
            # verify EVERY persistent native field outside the exact edit.
            ops=[SetParameter('set_parameter','effect-lead-delay','soundcraft.time',60000/126),
                 AddAutomationPoints('add_automation_points','gesture-lead-hpf',
                    [AutomationPoint('user-hpf-ramp',960,450,'linear')])]
            dest=root/'edited'
            a.apply(out/'native',dest,ops,Scope(['track-lead'],[],['soundcraft.time','soundcraft.hpf_freq'],None,None),state_hash(p))
            edited=a.inspect(dest)['native'];expected=deepcopy(native)
            i=next(i for i,t in enumerate(p.tracks) if t.id=='track-lead')
            observed=edited['tracks'][i]['mixer']['inserts'][1]['params']['time']
            self.assertAlmostEqual(observed,60000/126,delta=.0001)
            expected['tracks'][i]['mixer']['inserts'][1]['params']['time']=observed
            address={'Plugin':{'slot':0,'param':'hpf_freq'}}
            x=next(x for x in edited['tracks'][i]['automation'] if x['param']==address)
            added=next(x for x in x['points'] if x['at']==round(48000*60/126))
            self.assertEqual(added['value'],450)
            lane=next(x for x in expected['tracks'][i]['automation'] if x['param']==address)
            lane['points'].append(added);lane['points'].sort(key=lambda x:x['at'])
            self.assertEqual(edited,expected)
            a.save(dest,root/'edited-saved');self.assertEqual(a.inspect(root/'edited-saved')['native'],expected)
            receipt=receipt_from_dict(json.loads((dest/'receipt.json').read_text()));q=a.import_project(dest)
            self.assertEqual(dumps(replay(q,receipt,undo=True)),dumps(p))
            self.assertEqual(dumps(replay(p,receipt,undo=False)),dumps(q))
            download=package(out)
            with zipfile.ZipFile(download['zip']) as z:
                self.assertIsNone(z.testzip())
                for f in (out/'native').iterdir():
                    if f.is_file():self.assertEqual(z.read('editable-phase8/native/'+f.name),f.read_bytes())
                for f in (out/'listening').iterdir():self.assertEqual(z.read(f.name),f.read_bytes())
                self.assertIn('NOT a kick-input-triggered sidechain',z.read('README.txt').decode())
                self.assertFalse(any(x.endswith(('.clap','.so','.vst3','.mp3')) for x in z.namelist()))
            (root/'independent-checks.json').write_text(json.dumps({'native_notes_all_fields':True,
                'fx_units_and_all_lane_points':True,'markers':True,'reopened_pcm_exact':True,
                'exact_scoped_native_edits_and_replay':True,'localized_pcm_gates':True,
                'unchanged_source':True,'zip':download},indent=2)+'\n')
        finally:
            if temp:temp.cleanup()
