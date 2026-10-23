"""Actual optional live VST3 instrument proof; no plugin/host downloads."""
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.atmosphere import atmosphere_house
from kuang.audio import compare_wavs
from kuang.depth import note_fingerprints
from kuang.external_synth import ExternalSynthAdapter,digest,inventory,read_patch
from kuang.loudness import measure
from kuang.schema import ValidationError,dumps,load,state_hash
from kuang.transactions import Scope,SetParameter,receipt_from_dict,replay

ROOT=Path(__file__).resolve().parents[1]
SCRATCH=ROOT/'.local/phase11'


@unittest.skipUnless(os.environ.get('KUANG_VITALIUM_INTEGRATION')=='1','opt in to separately installed reviewed Vitalium VST3')
class ExternalSynthIntegrationTests(unittest.TestCase):
    def test_actual_live_state_all_notes_edit_audio_relocation_and_download(self):
        plugin=Path(os.environ['KUANG_VITALIUM_PLUGIN']);release=Path(os.environ['KUANG_PHASE11_RELEASE'])
        selected=os.environ.get('KUANG_SOUNDCRAFT_ARTIFACTS')
        temp=tempfile.TemporaryDirectory(dir=SCRATCH) if not selected else None
        root=Path(selected+'-phase11' if selected else temp.name)
        if root.exists() and any(root.iterdir()):raise RuntimeError('new/empty plugin integration proof required')
        root.mkdir(parents=True,exist_ok=True)
        try:
            a=ExternalSynthAdapter(plugin,os.environ['KUANG_SOUNDCRAFT'],workspace=ROOT)
            before=inventory(release);r=json.loads((release/'verification.json').read_text());p=load(release/'project.kuang.json')
            original=atmosphere_house();self.assertEqual(note_fingerprints(p),note_fingerprints(original))
            self.assertEqual(p.sections,original.sections);self.assertEqual(p.automation,original.automation)
            self.assertEqual((p.bars,p.tempo_bpm,p.key_tonic,p.key_mode),(64,126,0,'minor'))
            self.assertEqual(r['candidate_is'],'DISTRHO Vitalium 1.0.6, not current official Vital')
            self.assertFalse(r['human_listening']);self.assertFalse(r['official_vital_binary_available_locally'])
            self.assertEqual(r['capabilities']['normalized_static_controls'],771)
            patches={t.id:release/'native/patches'/t.id for t in p.tracks if t.instrument.plugin_ref.startswith('vst3:')}
            self.assertEqual(set(patches),{'track-depth-pad','track-bass','track-arp'})
            a.export(p,patches,root/'independent');a.save(root/'independent',root/'reopened')
            native=a.inspect(root/'reopened')['native']
            self.assertEqual(native,a.inspect(release/'native')['native'])
            self.assertEqual(dumps(a.import_project(root/'reopened')),dumps(p))
            self.assertEqual(len(native['markers']),6)
            for t,n in zip(p.tracks,native['tracks']):
                actual=[(v['start'],v['length'],v['pitch'],v['velocity'],v['channel'],v['release_velocity'])
                        for c in n['playlists'][0]['clips'] for v in c['content']['Midi']['sequence']['notes']]
                expected=[(c.start+v.start,v.duration,v.pitch,v.velocity,v.channel,0) for c in t.clips for v in c.notes]
                self.assertEqual(Counter(actual),Counter(expected))
                self.assertEqual([e['plugin'] for e in n['mixer']['inserts'] if e],[e.plugin_ref.split(':')[1] for e in t.effects])
                if t.id in patches:
                    asset=patches[t.id];self.assertEqual(len(n['instrument']['params']),2851)
                    import base64
                    self.assertEqual(base64.b64decode(n['instrument']['state']),(asset/'component.bin').read_bytes())
                    _,rows=read_patch(asset)
                    for row in rows:
                        self.assertAlmostEqual(n['instrument']['params'][row['native_id']],
                            t.instrument.parameters[row['canonical_id']]*row['scale'],delta=2e-5)
                if t.id in ('track-kick','track-bass','track-sub-pulse'):self.assertEqual(n['mixer']['pan'],[0,0])
            a.render(root/'reopened',root/'repeated-B.wav',end_seconds=64*4*60/126+5)
            self.assertEqual(digest(root/'repeated-B.wav'),digest(release/'B-live-vitalium.wav'))
            self.assertEqual((root/'reopened/song.mid').read_bytes(),(release/'song.mid').read_bytes())
            # Reopen with source bundle hidden and a separately copied plugin
            # module at another path. No copied third-party binary survives
            # this temporary scratch directory or enters release artifacts.
            with tempfile.TemporaryDirectory(dir=SCRATCH,prefix='relocated-plugin-') as d:
                moved_plugin=Path(d)/'Vitalium.vst3';shutil.copytree(plugin,moved_plugin)
                b=ExternalSynthAdapter(moved_plugin,os.environ['KUANG_SOUNDCRAFT'],workspace=ROOT)
                shutil.copytree(root/'reopened',root/'relocated')
                (root/'reopened').rename(root/'hidden-original')
                try:
                    self.assertEqual(b.inspect(root/'relocated')['native'],native)
                    b.render(root/'relocated',root/'relocated-B.wav',end_seconds=64*4*60/126+5)
                    self.assertEqual(digest(root/'relocated-B.wav'),digest(release/'B-live-vitalium.wav'))
                finally:(root/'hidden-original').rename(root/'reopened')
            stem=release/'stems/bass-B';sp=load(stem/'project.kuang.json');t=sp.tracks[0]
            _,rows=read_patch(stem/'patches'/t.id);row=next(x for x in rows if x['name']=='Filter 1 Cutoff')
            key=row['canonical_id'];scope=Scope([t.id],[],[key],None,None);value=.80
            a.apply(stem,root/'edited',[SetParameter('set_parameter',t.instrument.id,key,value)],scope,state_hash(sp))
            changed=a.inspect(root/'edited')['native'];expected=deepcopy(a.inspect(stem)['native'])
            expected['tracks'][0]['instrument']['params'][row['native_id']]=value*row['scale']
            observed=changed['tracks'][0]['instrument']['params'][row['native_id']]
            self.assertAlmostEqual(observed,value*row['scale'],delta=1e-6)
            expected['tracks'][0]['instrument']['params'][row['native_id']]=observed
            self.assertEqual(expected,changed)
            q=load(root/'edited/project.kuang.json');receipt=receipt_from_dict(json.loads((root/'edited/receipt.json').read_text()))
            self.assertEqual(dumps(replay(q,receipt,undo=True)),dumps(sp));self.assertEqual(dumps(replay(sp,receipt,undo=False)),dumps(q))
            a.render(root/'edited',root/'edited-bass.wav',end_seconds=8*4*60/126+8)
            delta=compare_wavs(release/'stems/bass-B.wav',root/'edited-bass.wav')
            self.assertGreater(delta['difference_to_original_rms_ratio'],.01)
            for label in ('A','B'):
                m=measure(release/'listening'/(label+'-full-LUFS-matched.wav'),library=os.environ.get('KUANG_EBUR128'))
                self.assertEqual(m['clipped_samples'],0);self.assertEqual(m['frames'],6091429)
                self.assertAlmostEqual(m['integrated_lufs'],r['full_matching'][label]['target_lufs'],delta=.001)
            mod=compare_wavs(release/'controls/pad-LFO-ON.wav',release/'controls/pad-LFO-OFF.wav')
            self.assertGreater(mod['difference_to_original_rms_ratio'],.05)
            with zipfile.ZipFile(release/'phase11-vitalium-listening.zip') as z:
                self.assertIsNone(z.testzip());self.assertEqual(z.read('native/session.scraft'),(release/'native/session.scraft').read_bytes())
                self.assertFalse(any(x.lower().endswith(('.so','.clap','.mp3','.whl')) for x in z.namelist()))
            with self.assertRaises(ValidationError):a.export(p,patches,root/'independent')
            self.assertEqual(inventory(release),before)
            (root/'independent-checks.json').write_text(json.dumps({'actual_live_vst3':True,'all_source_note_fields_exact':True,
                'embedded_patch_and_normalized_controls_exact':True,'full_native_and_pcm_repeat_exact':True,
                'relocated_bundle_source_hidden_new_plugin_path_pcm_exact':True,'typed_native_parameter_edit_audio_changed':delta,
                'exact_unrelated_state_undo_redo':True,'lufs_match_remeasured':True,'internal_lfo_pcm_delta':mod,
                'zip_verified_no_plugin_or_reference_audio':True,'release_read_only':True},indent=2)+'\n')
        finally:
            if temp:temp.cleanup()
