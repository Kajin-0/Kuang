"""End-to-end one-prompt symbolic full-length house template tests."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kuang import midi
from kuang.create import create
from kuang.schema import BAR, ValidationError, dumps, load, state_hash
from kuang import autonomous_create as ac


class FullSongCreateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()

    def test_full_song_from_one_prompt_is_editable_and_preserves_receipts(self):
        with patch.dict(os.environ,{"KUANG_SOUNDCRAFT":""}):
            result=create("warm deep house in C minor, 128 bars, without pad, no lead",
                          self.root/"song",seed=17,production="groove-template")
        p=load(self.root/"song/project.kuang.json")
        r=json.loads((self.root/"song/arrangement-evidence.json").read_text())
        spec=json.loads((self.root/"song/song-spec.json").read_text())
        self.assertEqual(p.bars,128)
        self.assertEqual(spec["bars"],32)  # internal source-plan scope only
        self.assertEqual(result["actual_project_bars"],128)
        self.assertEqual(result["arrangement"]["output_bars"],128)
        self.assertTrue(all(r["technical_gates"].values()))
        self.assertEqual(len(p.sections),8)
        self.assertNotIn("track-pad",{t.id for t in p.tracks})
        self.assertNotIn("track-lead",{t.id for t in p.tracks})
        self.assertEqual(p.key_mode,"minor")
        self.assertEqual(p.key_tonic,0)
        self.assertIn("arrangement-evidence.json",result["artifact_sha256"])
        self.assertEqual((self.root/"song/song.mid").read_bytes(),midi.export_bytes(p))
        self.assertFalse(result["validation"]["audio_verified"])
        self.assertEqual(result["arrangement"]["perceptual_quality"],"NEEDS_LISTENING")

    def test_full_length_prompt_without_explicit_bars(self):
        with patch.dict(os.environ,{"KUANG_SOUNDCRAFT":""}):
            result=create("funky house, full-length, no lead",self.root/"full",
                          seed=8,production="groove-template")
        self.assertEqual(result["actual_project_bars"],128)
        self.assertEqual(result["groove"]["selected_profile"],"jackin")

    def test_conflicts_and_legacy_modes_fail_closed(self):
        with patch.dict(os.environ,{"KUANG_SOUNDCRAFT":""}):
            cases=[
              ("house 96 bars",{"production":"sketch"}),
              ("house 96 bars",{"production":"groove-template","full_song_bars":128}),
              ("house 128 bars",{"production":"groove-template","model":"ollama"}),
              ("house 16 bars",{"production":"groove-template","full_song_bars":128}),
            ]
            for i,(prompt,settings) in enumerate(cases):
                with self.subTest(case=i),self.assertRaises(ValidationError):
                    create(prompt,self.root/f"bad-{i}",**settings)
                self.assertFalse((self.root/f"bad-{i}").exists())

    def test_private_full_form_receives_32_bar_source_spec_before_preset_selection(self):
        # The first failing palette stub confirms the expensive private path
        # receives the bounded source SongSpec, without requiring VST binaries.
        with tempfile.TemporaryDirectory(prefix=".test-house-private-",dir=Path.cwd()) as s:
            root=Path(s)
            catalog=root/"catalog/reports/catalog.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text("{}")
            plugin=root/"plugin.vst3";plugin.mkdir()
            captured={}
            def stub(prompt,catalog,plugin,out,**kwargs):
                captured.update(kwargs)
                out.mkdir()
                (out/"selection.json").write_text(json.dumps({"status":"incomplete","roles":{}}))
            with patch.object(ac,"select_palette",side_effect=stub):
                with self.assertRaisesRegex(ValidationError,"complete selection"):
                    ac.create("deep house in D minor, 128 bars, without pad",catalog,plugin,
                              "/no/host",root/"out",seed=17,private=True,
                              groove_template=True,full_song_bars=128)
            self.assertEqual(captured["musical_spec"].bars,32)
            self.assertEqual(captured["musical_spec"].tonic,2)
            self.assertEqual(captured["musical_spec"].mode,"minor")
            self.assertFalse((root/"out").exists())
