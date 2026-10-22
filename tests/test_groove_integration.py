"""Opt-in actual groove/FX/stem/ZIP checks; never downloads plugins or audio."""

import json
import os
import shutil
import tempfile
import unittest
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.audio import compare_wavs
from kuang.create import create
from kuang.schema import dumps,load,state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import Scope,SetParameter,receipt_from_dict,replay
from tools.phase5_house import ROOT,build


@unittest.skipUnless(os.environ.get('KUANG_SOUNDCRAFT_INTEGRATION')=='1','opt in to installed SoundCraft groove proof')
class GrooveIntegrationTests(unittest.TestCase):
    def test_real_loop_editable_fx_notes_full_reopen_stems_reference_and_listening_zip(self):
        selected=os.environ.get('KUANG_SOUNDCRAFT_ARTIFACTS')
        scratch=ROOT/'.local/phase5';scratch.mkdir(parents=True,exist_ok=True)
        temp=tempfile.TemporaryDirectory(dir=scratch) if not selected else None
        root=Path(selected+'-groove' if selected else temp.name)
        if root.exists() and any(root.iterdir()):raise RuntimeError('groove integration output must be new/empty')
        root.mkdir(parents=True,exist_ok=True)
        try:
            a=SoundCraftAdapter(timeout=120)
            baseline=root/'baseline'
            create('uplifting house, 126 bpm, C major, 16 bars',baseline,seed=29,
                   production='refined',soundcraft=str(a.executable),render=True)
            original=(baseline/'native/session.scraft').read_bytes()
            reference=root/'user-reference.wav'
            shutil.copyfile(baseline/'preview.wav',reference)
            result=root/'result'
            r=build(result,executable=str(a.executable),baseline=baseline,reference=reference,
                    credit='Original Kuang integration fixture',license_text='MIT')
            p=load(result/'project.kuang.json')
            native=a.inspect(result/'native')['native']
            for t,h in zip(p.tracks,native['tracks']):
                actual=[(n['start'],n['length'],n['pitch'],n['velocity'],n['channel'])
                        for c in h['playlists'][0]['clips'] for n in c['content']['Midi']['sequence']['notes']]
                expected=[(c.start+n.start,n.duration,n.pitch,n.velocity,n.channel) for c in t.clips for n in c.notes]
                self.assertEqual(Counter(actual),Counter(expected))
                inserts=[x for x in h['mixer']['inserts'] if x]
                self.assertEqual([x['plugin'] for x in inserts],[x.plugin_ref.split(':')[1] for x in t.effects])
                self.assertEqual(h['mixer']['automation_mode'],'Read')
                self.assertTrue(all(l['enabled'] for l in h['automation']))
            bass=next(h for h in native['tracks'] if h['name']=='Short mono bass')
            self.assertEqual(bass['instrument']['params']['osc_mix'],0)
            self.assertEqual(bass['instrument']['params']['amp_release'],28)
            self.assertEqual(a.inspect(result/'saved-native')['native'],native)
            self.assertLessEqual(r['stem_recombination']['peak_error_lsb'],5)
            for m in r['metrics'].values():
                self.assertEqual(m['clipped_samples'],0);self.assertGreater(m['rms'],1e-6)
            left,right=(r['rms_matching'][x]['audio']['rms_dbfs'] for x in ('phase4-baseline','candidate'))
            self.assertAlmostEqual(left,right,places=5)
            ref=r['reference']['matched']
            self.assertAlmostEqual(ref['reference']['rms_dbfs'],ref['candidate']['rms_dbfs'],places=5)
            self.assertFalse(r['club_quality_established'])
            with zipfile.ZipFile(result/'phase5-house-listening.zip') as z:
                self.assertIsNone(z.testzip())
                self.assertNotIn('private-reference',str(z.namelist()))
                self.assertEqual(z.read('editable/native/session.scraft'),(result/'native/session.scraft').read_bytes())
                self.assertEqual(z.read('editable/native/manifest.json'),(result/'native/manifest.json').read_bytes())
                self.assertFalse(any(n.endswith(('.so','.clap','.vst3')) for n in z.namelist()))
            # Independent full native comparison around an editable modulation FX.
            op=SetParameter('set_parameter','effect-harmony-chorus','effect.wet',0)
            edited=root/'chorus-dry'
            a.apply(result/'native',edited,[op],Scope(['track-harmony'],[],['effect.wet'],None,None),state_hash(p))
            expected=deepcopy(native)
            index=next(i for i,t in enumerate(p.tracks) if t.id=='track-harmony')
            expected['tracks'][index]['mixer']['inserts'][1]['params']['mix']=0
            self.assertEqual(a.inspect(edited)['native'],expected)
            receipt=receipt_from_dict(json.loads((edited/'receipt.json').read_text()))
            q=a.import_project(edited)
            self.assertEqual(dumps(replay(q,receipt,undo=True)),dumps(p))
            self.assertEqual(dumps(replay(p,receipt,undo=False)),dumps(q))
            a.save(edited,root/'chorus-dry-saved')
            self.assertEqual(a.inspect(root/'chorus-dry-saved')['native'],expected)
            a.render(edited,root/'chorus-dry.wav')
            delta=compare_wavs(result/'candidate.wav',root/'chorus-dry.wav')
            self.assertTrue(delta['measurable_change'])
            self.assertEqual((baseline/'native/session.scraft').read_bytes(),original)
            (root/'checks.json').write_text(json.dumps({'full_native_equality':True,'chorus_pcm_delta':delta,
                'stem_recombination':r['stem_recombination'],'rms_matched':True,'zip_verified':True},indent=2)+'\n')
        finally:
            if temp:temp.cleanup()
