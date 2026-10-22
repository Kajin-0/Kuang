"""Opt-in real native 64-bar arrangement; no binary or asset download."""

import json
import os
import tempfile
import unittest
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.depth import PAD_IDS, depth_house, note_fingerprints
from kuang.house_song import arrange_house, corrected_pads
from kuang.schema import BAR, AutomationPoint, dumps, load, save, state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import AddAutomationPoints, Scope, SetParameter, receipt_from_dict, replay
from tools.phase7_house import ROOT, SCRATCH, inventory, package, pad_preview, song_build


@unittest.skipUnless(os.environ.get('KUANG_SOUNDCRAFT_INTEGRATION')=='1','opt in to installed SoundCraft 64-bar proof')
class HouseSongIntegrationTests(unittest.TestCase):
    def test_real_pad_correction_song_sections_full_native_edits_audio_and_zip(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        selected=os.environ.get('KUANG_SOUNDCRAFT_ARTIFACTS')
        temp=tempfile.TemporaryDirectory(dir=SCRATCH) if not selected else None
        root=Path(selected+'-phase7' if selected else temp.name)
        if root.exists() and any(root.iterdir()):raise RuntimeError('Phase 7 proof requires new/empty outputs')
        root.mkdir(parents=True,exist_ok=True)
        try:
            a=SoundCraftAdapter(timeout=240)
            source=root/'source';source.mkdir()
            old=depth_house();save(old,source/'project.kuang.json')
            a.export(old,source/'native')
            a.render(source/'native',source/'B-phase6-depth.wav',end_seconds=old.length/960*60/126+4)
            before=inventory([source])
            pads=root/'pad-fix';pr=pad_preview(pads,source=source,executable=str(a.executable))
            corrected=load(pads/'project.kuang.json')
            self.assertEqual(dumps(corrected),dumps(corrected_pads()))
            self.assertEqual(note_fingerprints(old),note_fingerprints(corrected))
            self.assertLess(pr['pad_stem_change_db'],-3)
            self.assertLess(pr['stem_balance']['B-pads']['peak'],pr['stem_balance']['B-lead']['peak'])
            self.assertLess(pr['stem_balance']['B-pads']['rms'],pr['stem_balance']['B-drums']['rms']*.5)
            for delta in pr['wet_dry'].values():self.assertTrue(delta['measurable_change'])
            levels=[v['audio']['rms_dbfs'] for v in pr['rms_matching'].values()]
            self.assertAlmostEqual(*levels,places=5)
            out=root/'song';r=song_build(out,source=pads,executable=str(a.executable))
            p=load(out/'project.kuang.json');native=a.inspect(out/'native')['native']
            self.assertEqual(dumps(p),dumps(arrange_house(corrected)))
            self.assertEqual(p.bars,64);self.assertEqual(len(native['markers']),6)
            for marker,s in zip(native['markers'],p.sections):
                self.assertEqual(marker['name'],s.name)
                self.assertEqual((marker['start'],marker['end']),
                    (round(s.start*48000*60/(960*126)),round((s.start+s.length)*48000*60/(960*126))))
            self.assertEqual(a.inspect(out/'saved-native')['native'],native)
            self.assertEqual(dumps(a.import_project(out/'saved-native')),dumps(p))
            for t,h in zip(p.tracks,native['tracks']):
                actual=[(n['start'],n['length'],n['pitch'],n['velocity'],n['channel'],n['release_velocity'])
                        for c in h['playlists'][0]['clips'] for n in c['content']['Midi']['sequence']['notes']]
                expected=[(c.start+n.start,n.duration,n.pitch,n.velocity,n.channel,0) for c in t.clips for n in c.notes]
                self.assertEqual(Counter(actual),Counter(expected))
                fx=[x for x in h['mixer']['inserts'] if x]
                self.assertEqual([x['plugin'] for x in fx],[e.plugin_ref.split(':')[1] for e in t.effects])
                if t.id in PAD_IDS:
                    self.assertAlmostEqual(fx[-1]['params']['decay'],t.effects[-1].parameters['soundcraft.decay_ms']/1000,places=6)
                    self.assertEqual(fx[-1]['params']['width'],75)
                    self.assertGreaterEqual(fx[-1]['params']['low_cut'],500)
                    self.assertEqual(h['instrument']['params']['amp_attack'],t.instrument.parameters['soundcraft.amp_attack'])
                    self.assertEqual(h['instrument']['params']['amp_release'],t.instrument.parameters['soundcraft.amp_release'])
                if t.id in ('track-kick','track-bass'):self.assertEqual(h['mixer']['pan'],[0,0])
                for lane in (x for x in p.automation if x.target_id in {t.id,*(e.id for e in t.effects)}):
                    if lane.target_id==t.id:
                        addresses=['Volume'] if lane.parameter_id=='mixer.gain_db' else [{'Pan':0},{'Pan':1}]
                        factor=1
                    else:
                        slot=next(i for i,e in enumerate(t.effects) if e.id==lane.target_id)
                        addresses=[{'Plugin':{'slot':slot,'param':'mix' if lane.parameter_id=='effect.wet' else 'lpf_freq'}}]
                        factor=100 if lane.parameter_id=='effect.wet' else 1
                    for address in addresses:
                        host=next(x for x in h['automation'] if x['param']==address)
                        self.assertTrue(host['enabled']);self.assertEqual(h['mixer']['automation_mode'],'Read')
                        self.assertEqual([v['at'] for v in host['points']],[round(x.tick*48000*60/(960*126)) for x in lane.points])
                        for v,x in zip(host['points'],lane.points):self.assertAlmostEqual(v['value'],x.value*factor,delta=.002)
            audio=r['metrics'];self.assertEqual((audio['sample_rate'],audio['bits_per_sample'],audio['channels']),(48000,24,2))
            self.assertGreater(audio['duration_seconds'],120);self.assertEqual(audio['clipped_samples'],0)
            energy=audio['sections']
            self.assertLess(energy['Breakdown']['rms'],energy['Main Drop']['rms']*.65)
            self.assertLess(energy['DJ Intro']['rms'],energy['Main Drop']['rms'])
            self.assertLess(energy['DJ Outro']['rms'],energy['Main Drop']['rms'])
            self.assertEqual(len({round(energy[s.name]['rms_dbfs'],3) for s in p.sections}),6)
            spectra=r['section_spectrum']['sections']
            self.assertLess(spectra['Breakdown']['band_power_fraction']['sub_20_120'],
                            spectra['Main Drop']['band_power_fraction']['sub_20_120']*.5)
            self.assertGreater(r['spatial']['bands']['low_20_120']['mono_energy_retention'],.99)
            self.assertLess(r['spatial']['last_250ms']['rms'],10**(-65/20))
            zreport=package(root)
            with zipfile.ZipFile(zreport['zip']) as z:
                self.assertIsNone(z.testzip())
                for directory,label in ((pads,'editable-pad-fix'),(out,'editable-song')):
                    for name in ('session.scraft','manifest.json','project.kuang.json'):
                        self.assertEqual(z.read(label+'/native/'+name),(directory/'native'/name).read_bytes())
                self.assertEqual(z.read('C-phase7-house-64bars.wav'),(out/'C-phase7-house-64bars.wav').read_bytes())
                self.assertFalse(any(n.endswith(('.so','.clap','.vst3')) for n in z.namelist()))
                levels=json.loads(z.read('levels.json'))
                self.assertFalse(levels['C_matched_to_A_B'])
                self.assertAlmostEqual(*[v['audio']['rms_dbfs'] for v in levels['A_B_excerpt_rms_matching'].values()],places=5)
            ops=[SetParameter('set_parameter','effect-depth-pad-plate','soundcraft.decay_ms',3000),
                 AddAutomationPoints('add_automation_points','song-lead-pan',
                                     [AutomationPoint('reviewed-song-pan',240,-.2,'linear')])]
            edited=root/'edited'
            a.apply(out/'native',edited,ops,Scope([PAD_IDS[0],'track-lead'],[],['soundcraft.decay_ms','mixer.pan'],None,None),state_hash(p))
            new=a.inspect(edited)['native'];expected=deepcopy(native)
            # Body plate is slot 3; air plate is slot 2. Slots remain explicit.
            expected['tracks'][-2]['mixer']['inserts'][3]['params']['decay']=3
            lead_index=next(i for i,t in enumerate(p.tracks) if t.id=='track-lead')
            for index in (0,1):
                lane=next(x for x in expected['tracks'][lead_index]['automation'] if x['param']=={'Pan':index})
                observed=next(x for x in new['tracks'][lead_index]['automation'] if x['param']=={'Pan':index})
                point=next(x for x in observed['points'] if x['at']==round(240*48000*60/(960*126)))
                self.assertAlmostEqual(point['value'],-.2,places=6)
                lane['points'].append(deepcopy(point));lane['points'].sort(key=lambda x:x['at'])
            self.assertEqual(new,expected)
            a.save(edited,root/'edited-saved');self.assertEqual(a.inspect(root/'edited-saved')['native'],expected)
            receipt=receipt_from_dict(json.loads((edited/'receipt.json').read_text()));q=a.import_project(edited)
            self.assertEqual(dumps(replay(q,receipt,undo=True)),dumps(p))
            self.assertEqual(dumps(replay(p,receipt,undo=False)),dumps(q))
            self.assertEqual(before,inventory([source]))
            (root/'independent-checks.json').write_text(json.dumps({'all_native_note_fields':True,
                'markers':True,'native_fx_lane_units':True,'full_reopen':True,'exact_edit_and_replay':True,
                'section_pcm_contrast':True,'same_midi_pad_comparison':True,'zip':zreport},indent=2)+'\n')
        finally:
            if temp:temp.cleanup()
