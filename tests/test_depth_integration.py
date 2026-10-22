"""Independent real-host depth proof. No plugin/audio/model downloads."""

import json
import os
import tempfile
import unittest
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.depth import PAD_IDS, depth_house, note_fingerprints
from kuang.groove import house_loop
from kuang.production_audio import production_metrics
from kuang.schema import AutomationPoint, dumps, load, save, state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import AddAutomationPoints, Scope, SetParameter, receipt_from_dict, replay
from tools.phase6_house import ROOT, build, control, inventory


@unittest.skipUnless(os.environ.get('KUANG_SOUNDCRAFT_INTEGRATION')=='1','opt in to installed SoundCraft depth proof')
class DepthIntegrationTests(unittest.TestCase):
    def test_real_depth_notes_fx_lanes_controls_mono_and_download_then_exact_edit(self):
        scratch=ROOT/'.local/phase6';scratch.mkdir(parents=True,exist_ok=True)
        selected=os.environ.get('KUANG_SOUNDCRAFT_ARTIFACTS')
        temp=tempfile.TemporaryDirectory(dir=scratch) if not selected else None
        root=Path(selected+'-phase6' if selected else temp.name)
        if root.exists() and any(root.iterdir()):raise RuntimeError('depth output must be new/empty')
        root.mkdir(parents=True,exist_ok=True)
        try:
            a=SoundCraftAdapter(timeout=120)
            source=root/'source';source.mkdir()
            old=house_loop();save(old,source/'project.kuang.json')
            a.export(old,source/'native');a.render(source/'native',source/'candidate.wav')
            before=inventory([source])
            result=root/'result';r=build(result,executable=str(a.executable),source=source)
            p=load(result/'project.kuang.json');self.assertEqual(dumps(p),dumps(depth_house(old)))
            native=a.inspect(result/'native')['native']
            self.assertEqual(a.inspect(result/'saved-native')['native'],native)
            for t,h in zip(p.tracks,native['tracks']):
                actual=[(n['start'],n['length'],n['pitch'],n['velocity'],n['channel'],n['release_velocity'])
                        for c in h['playlists'][0]['clips'] for n in c['content']['Midi']['sequence']['notes']]
                expected=[(c.start+n.start,n.duration,n.pitch,n.velocity,n.channel,0) for c in t.clips for n in c.notes]
                self.assertEqual(Counter(actual),Counter(expected))
                inserts=[x for x in h['mixer']['inserts'] if x]
                self.assertEqual([x['plugin'] for x in inserts],[e.plugin_ref.split(':')[1] for e in t.effects])
                for value in h['mixer']['pan']:
                    self.assertAlmostEqual(value,t.controls['mixer.pan'],places=6)
                if t.id in PAD_IDS:
                    for param in ('amp_attack','amp_decay','amp_release','filter_attack','filter_release'):
                        self.assertEqual(h['instrument']['params'][param],t.instrument.parameters['soundcraft.'+param])
                    self.assertAlmostEqual(h['instrument']['params']['amp_sustain'],t.instrument.parameters['soundcraft.amp_sustain']*100,places=4)
                    chorus=inserts[1]['params']
                    self.assertAlmostEqual(chorus['depth'],t.effects[1].parameters['soundcraft.depth']*100,places=4)
                    self.assertEqual(chorus['spread'],100)
                    self.assertAlmostEqual(inserts[-1]['params']['decay'],t.effects[-1].parameters['soundcraft.decay_ms']/1000,places=6)
                for lane in (x for x in p.automation if x.target_id in {t.id,*(e.id for e in t.effects)}):
                    if lane.target_id==t.id:address='Volume';factor=1
                    else:
                        slot=next(i for i,e in enumerate(t.effects) if e.id==lane.target_id)
                        address={'Plugin':{'slot':slot,'param':'mix' if lane.parameter_id=='effect.wet' else 'lpf_freq'}}
                        factor=100 if lane.parameter_id=='effect.wet' else 1
                    host=next(x for x in h['automation'] if x['param']==address)
                    self.assertTrue(host['enabled']);self.assertEqual(h['mixer']['automation_mode'],'Read')
                    self.assertEqual([x['at'] for x in host['points']],[round(x.tick*48000*60/(960*126)) for x in lane.points])
                    for x,y in zip(host['points'],lane.points):self.assertAlmostEqual(x['value'],y.value*factor,delta=.002)
            for key,value in note_fingerprints(old).items():self.assertEqual(note_fingerprints(p)[key],value)
            for name,data in r['controls'].items():
                self.assertTrue(data['same_midi']);self.assertTrue(data['delta']['measurable_change'])
                mode=name.rsplit('-',1)[0]
                expected=control(p,mode)
                if name.endswith('-pads'):
                    expected.tracks=[t for t in expected.tracks if t.id in PAD_IDS]
                actual=load(result/'controls'/(name+'-native')/'project.kuang.json')
                self.assertEqual(note_fingerprints(actual),note_fingerprints(expected))
            self.assertTrue(r['baseline_pcm_prefix_identical']);self.assertTrue(r['sources_unchanged'])
            self.assertLessEqual(r['stem_recombination']['peak_error_lsb'],6)
            for m in r['metrics'].values():
                self.assertEqual((m['sample_rate'],m['bits_per_sample'],m['channels']),(48000,24,2))
                self.assertEqual(m['clipped_samples'],0);self.assertGreater(m['rms'],1e-6)
            old_width=r['spatial']['A-phase5-unchanged']['bands']['high_over_500']['side_to_mid_power_ratio']
            new_width=r['spatial']['B-phase6-depth']['bands']['high_over_500']['side_to_mid_power_ratio']
            self.assertGreater(new_width,old_width*1.5)
            self.assertGreater(r['spatial']['B-phase6-depth']['bands']['high_over_500']['mono_energy_retention'],.7)
            self.assertLess(r['spatial']['B-phase6-depth']['last_250ms']['rms'],10**(-65/20))
            for name in ('kick','bass'):
                self.assertEqual(r['spatial_stems'][name]['bands']['high_over_500']['side'],0)
            # Independent release proof from the isolated same-native pad:
            # notes finish at 30 s; amplitude release and reverb extend beyond.
            length=p.length/p.ppq*60/p.tempo_bpm
            release=production_metrics(result/'stems/pad.wav',
                [('after_last_note',30.02,30.25),('after_song_end',length+.05,length+.4)])['sections']
            self.assertGreater(release['after_last_note']['rms'],1e-5)
            self.assertGreater(release['after_song_end']['rms'],1e-6)
            rms=[v['audio']['rms_dbfs'] for v in r['rms_matching'].values()]
            self.assertAlmostEqual(*rms,places=5)
            with zipfile.ZipFile(result/'phase6-house-listening.zip') as z:
                self.assertIsNone(z.testzip())
                for name in ('session.scraft','manifest.json','project.kuang.json'):
                    self.assertEqual(z.read('editable/native/'+name),(result/'native'/name).read_bytes())
                self.assertFalse(any(n.endswith(('.so','.clap','.vst3')) for n in z.namelist()))
                self.assertIn('A-phase5-unchanged-matched.wav',z.namelist())
                self.assertIn('B-phase6-depth-matched.wav',z.namelist())
            # Actual narrow edit of modulation, reverb and an LPF point. Every
            # other native field must stay exact, with full save/reopen again.
            ops=[SetParameter('set_parameter','effect-depth-pad-phaser','soundcraft.depth',.5),
                 SetParameter('set_parameter','effect-depth-air-plate','effect.wet',.3),
                 AddAutomationPoints('add_automation_points','depth-pad-filter',
                                     [AutomationPoint('depth-reviewed-filter',240,2100,'linear')])]
            scope=Scope(list(PAD_IDS),[],['soundcraft.depth','effect.wet','soundcraft.lpf_freq'],None,None)
            edited=root/'edited';a.apply(result/'native',edited,ops,scope,state_hash(p))
            expected=deepcopy(native)
            expected['tracks'][-2]['mixer']['inserts'][2]['params']['depth']=50
            expected['tracks'][-1]['mixer']['inserts'][2]['params']['mix']=30
            lane=next(x for x in expected['tracks'][-2]['automation'] if x['param']=={'Plugin':{'slot':0,'param':'lpf_freq'}})
            lane['points'].append({'at':round(240*48000*60/(960*126)),'value':2100})
            lane['points'].sort(key=lambda x:x['at'])
            self.assertEqual(a.inspect(edited)['native'],expected)
            a.save(edited,root/'edited-saved');self.assertEqual(a.inspect(root/'edited-saved')['native'],expected)
            receipt=receipt_from_dict(json.loads((edited/'receipt.json').read_text()))
            q=a.import_project(edited)
            self.assertEqual(dumps(replay(q,receipt,undo=True)),dumps(p))
            self.assertEqual(dumps(replay(p,receipt,undo=False)),dumps(q))
            self.assertEqual(before,inventory([source]))
            (root/'independent-checks.json').write_text(json.dumps({'all_note_fields':True,'fx_lane_units':True,
                'exact_native_edit':True,'full_reopen':True,'source_unchanged':True,'zip':True,
                'pad_release_regions':release},indent=2)+'\n')
        finally:
            if temp:temp.cleanup()
