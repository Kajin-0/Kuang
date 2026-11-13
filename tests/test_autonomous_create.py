import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch, Mock

from kuang import autonomous_create as ac
from kuang.composer import compose
from kuang.external_synth import read_patch
from kuang.production import refine_house
from kuang.schema import ValidationError
from kuang.song import rules_plan
from kuang._private_vital_worker import wave_frames
from test_autonomous_palette import preset


class AutonomousCreateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='.test-autonomous-',dir=Path.cwd())
        self.root = Path(self.tmp.name)
        self.catalog = self.root/'library/reports/catalog.json'
        self.catalog.parent.mkdir(parents=True)
        self.catalog.write_text('{}')
        self.plugin = self.root/'plugin.vst3'; self.plugin.mkdir()
        self.host = '/does/not/exist'

    def tearDown(self): self.tmp.cleanup()

    def call(self, **kw):
        return ac.create('deep house in C minor no lead',self.catalog,self.plugin,self.host,
                         self.root/'output',**kw)

    def test_master_preview_requires_groove_template_before_private_work(self):
        with patch.object(ac,'select_palette') as select, self.assertRaisesRegex(ValidationError,'requires --groove-template'):
            self.call(private=True,master_preview=True)
        select.assert_not_called()
        with patch.object(ac,'select_palette') as select, self.assertRaisesRegex(ValidationError,'must be boolean'):
            self.call(private=True,groove_template=True,master_preview='true')
        select.assert_not_called()

    def test_explicit_private_consent_required(self):
        with patch.object(ac,'select_palette') as select, self.assertRaises(ValidationError): self.call()
        select.assert_not_called()

    def test_existing_output_never_touched(self):
        out=self.root/'output'; out.mkdir(); (out/'keep').write_text('safe')
        with patch.object(ac,'select_palette') as select, self.assertRaises(ValidationError): self.call(private=True)
        select.assert_not_called(); self.assertEqual((out/'keep').read_text(),'safe')

    def test_output_within_library_rejected(self):
        with patch.object(ac,'select_palette') as select, self.assertRaises(ValidationError):
            ac.create('house',self.catalog,self.plugin,self.host,self.catalog.parent/'out',private=True)
        select.assert_not_called()

    def test_unsupported_bar_count_and_conflicting_prompt_rejected(self):
        with self.assertRaises(ValidationError): self.call(private=True,bars=8)
        with patch.object(ac,'select_palette') as select, self.assertRaises(ValidationError):
            ac.create('house 32 bars',self.catalog,self.plugin,self.host,self.root/'output',private=True,bars=16)
        select.assert_not_called()

    def test_other_genre_rejected_before_plugin_work(self):
        with patch.object(ac,'select_palette') as select, self.assertRaises(ValidationError):
            ac.create('ambient song',self.catalog,self.plugin,self.host,self.root/'output',private=True)
        select.assert_not_called()

    def test_incomplete_selection_does_not_publish(self):
        def selector(prompt,catalog,plugin,out,**kw):
            out.mkdir(); (out/'selection.json').write_text(json.dumps({'status':'incomplete','roles':{}}))
        with patch.object(ac,'select_palette',side_effect=selector), self.assertRaises(ValidationError): self.call(private=True)
        self.assertFalse((self.root/'output').exists())
        self.assertFalse(list(self.root.glob('.autonomous-create-*')))

    def test_no_pad_prompt_passes_one_shared_spec_to_selector(self):
        recorded = {}
        def selector(prompt, catalog, plugin, out, **kwargs):
            recorded.update(kwargs)
            out.mkdir()
            (out/'selection.json').write_text(json.dumps({'status':'incomplete','roles':{}}))
        with patch.object(ac,'select_palette',side_effect=selector), self.assertRaises(ValidationError):
            ac.create('house in C minor, without pad, no lead',self.catalog,self.plugin,self.host,
                      self.root/'output',private=True,seed=19)
        self.assertEqual((recorded['musical_spec'].tonic, recorded['musical_spec'].mode), (0,'minor'))
        self.assertEqual(recorded['musical_spec'].seed, 19)
        self.assertFalse((self.root/'output').exists())

    def test_sample_drum_source_requires_explicit_groove_mode(self):
        with patch.object(ac,'select_palette') as select, self.assertRaisesRegex(ValidationError,'require --groove-template'):
            self.call(private=True,sample_pack=self.root/'not-available')
        select.assert_not_called()
        with patch.object(ac,'select_palette') as select, self.assertRaisesRegex(ValidationError,'require --groove-template'):
            self.call(private=True,harmony_profile='simple')
        select.assert_not_called()
        with patch.object(ac,'select_palette') as select, self.assertRaisesRegex(ValidationError,'drum_variant'):
            self.call(private=True,groove_template=True,drum_variant=2)
        select.assert_not_called()

    def test_groove_harmony_modes_fail_before_private_audition(self):
        with patch.object(ac,'select_palette') as select, self.assertRaisesRegex(ValidationError,'does not support'):
            ac.create('deep house in A Phrygian',self.catalog,self.plugin,self.host,self.root/'output',
                      private=True,groove_template=True)
        select.assert_not_called()
        with patch.object(ac,'select_palette') as select, self.assertRaisesRegex(ValidationError,'conflicts'):
            ac.create('house with simple triads',self.catalog,self.plugin,self.host,self.root/'output',
                      private=True,groove_template=True,harmony_profile='extended')
        select.assert_not_called()
        self.assertFalse((self.root/'output').exists())

    def test_groove_sample_mode_passes_validated_spec_to_private_selector(self):
        captured={}
        def selector(prompt,catalog,plugin,out,**kw):
            captured.update(kw); out.mkdir()
            (out/'selection.json').write_text(json.dumps({'status':'incomplete','roles':{}}))
        with patch.object(ac,'select_palette',side_effect=selector), self.assertRaisesRegex(ValidationError,'complete selection'):
            ac.create('deep house in D minor, 16 bars, no lead, without pad',self.catalog,self.plugin,self.host,
                      self.root/'output',private=True,groove_template=True,
                      sample_pack=self.root/'placeholder-pack',harmony_profile='simple',seed=17)
        self.assertEqual(captured['musical_spec'].tonic,2)
        self.assertEqual(captured['musical_spec'].mode,'minor')
        self.assertEqual(captured['musical_spec'].seed,17)
        self.assertFalse((self.root/'output').exists())

    def test_private_manifest_cannot_enter_original_adapter(self):
        private=self.root/'patch'; private.mkdir()
        (private/'manifest.json').write_text(json.dumps({'version':'private-selected-vital-1'}))
        with self.assertRaises(ValidationError): read_patch(private)
        with self.assertRaises(ValidationError): ac.read_private_patch(private,{},self.root,'0'*64)

    def test_unselected_preset_is_rejected(self):
        private=self.root/'patch'; private.mkdir()
        (private/'manifest.json').write_text(json.dumps({'version':'private-selected-vital-1','plugin':ac.PLUGIN_ID,
             'plugin_version':ac.VERSION,'plugin_sha256':'0'*64,'license':'unknown; private local use only','source_sha256':'1'*64}))
        with self.assertRaisesRegex(ValidationError,'not selected'):
            ac.read_private_patch(private,{},self.root,'0'*64)

    def test_waveform_readback_detects_changes_and_external_sources(self):
        original=preset('fixture')
        for wave in original['settings']['wavetables']:
            wave['groups'][0]['components'][0]['keyframes'][0]['position']=0
        changed=deepcopy(original)
        changed['settings']['wavetables'][0]['groups'][0]['components'][0]['keyframes'][0]['wave_data']='changed'
        self.assertNotEqual(wave_frames(original),wave_frames(changed))
        changed['settings']['wavetables'][0]['groups'][0]['components'][0]['type']='File Source'
        with self.assertRaises(ValidationError): wave_frames(changed)

    def test_private_host_only_binds_its_staging_tree_writable(self):
        adapter=ac.PrivateExternal.__new__(ac.PrivateExternal)
        adapter.scratch=self.root/'stage/scratch'; adapter.scratch.mkdir(parents=True)
        adapter.plugin=self.plugin; adapter.bwrap='/usr/bin/bwrap'
        with patch.object(ac.subprocess,'run',return_value=Mock(returncode=0,stderr='',stdout='')) as run:
            adapter.call(['/bin/true'],adapter.scratch)
        argv=run.call_args.args[0]
        self.assertIn('--unshare-net',argv)
        self.assertEqual(argv[argv.index('--bind')+1:argv.index('--bind')+3],[str(adapter.scratch.parent)]*2)
        with patch.object(ac.subprocess,'run',return_value=Mock(returncode=0,stderr='',stdout='')) as run:
            adapter.call(['/bin/true'],self.root)
        self.assertEqual(run.call_args.kwargs['cwd'],adapter.scratch)

    def test_binding_preserves_midi_and_no_lead(self):
        spec,_=rules_plan('house in C minor no lead',17)
        project=refine_house(spec,compose(spec)); original=[(t.id,t.clips) for t in project.tracks]
        path=self.root/'patch'; path.mkdir(); (path/'manifest.json').write_text('{}')
        rows=[{'canonical_id':'vitalium.param1','normalized':.4}]
        class Dummy: selection={}; preset_root=None; plugin_sha='x'
        with patch.object(ac,'read_private_patch',return_value=({},rows)):
            result=ac._bind(project,{'track-bass':path},Dummy())
        self.assertEqual(original,[(t.id,t.clips) for t in result.tracks])
        self.assertNotIn('track-lead',[t.id for t in result.tracks])
        self.assertEqual(next(t for t in result.tracks if t.id=='track-bass').instrument.plugin_ref,ac.PLUGIN_ID)
        self.assertNotEqual(next(t for t in project.tracks if t.id=='track-bass').instrument.plugin_ref,ac.PLUGIN_ID)
        with self.assertRaises(ValidationError): ac._bind(project,{'track-does-not-exist':path},Dummy())

    def test_optional_pad_and_actual_kick_note_ducking(self):
        spec,_=rules_plan('house in C minor, no lead',17)
        without=refine_house(spec,compose(spec),include_pad=False,kick_aligned_ducking=True)
        self.assertNotIn('track-pad',{t.id for t in without.tracks})
        kick=next(t for t in without.tracks if t.id=='track-kick')
        onsets={c.start+n.start for c in kick.clips for n in c.notes}
        self.assertTrue(onsets)
        self.assertNotIn(0,onsets)
        lane=next(x for x in without.automation if x.id=='production-harmony-duck')
        points={p.tick:p.value for p in lane.points}
        self.assertEqual(points[0], 0)
        self.assertEqual(points[min(onsets)], -5)
        self.assertTrue(all(t in onsets for t,v in points.items() if v == -5))
        with_pad=refine_house(spec,compose(spec),include_pad=True,kick_aligned_ducking=True)
        self.assertIn('track-pad',{t.id for t in with_pad.tracks})
        no_pump=refine_house(spec,compose(spec),include_pad=False,kick_aligned_ducking=False)
        self.assertEqual(next(x for x in no_pump.automation if x.id=='production-harmony-duck').points[0].value,-5)

    def test_cli_help_is_stdlib_only(self):
        p=subprocess.run([sys.executable,'-m','kuang.autonomous_create','--help'],capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0); self.assertIn('--private-third-party-presets',p.stdout)


if __name__=='__main__': unittest.main()
