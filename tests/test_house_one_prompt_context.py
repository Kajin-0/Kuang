"""Focused fail-closed and program-level tests for one-prompt contextual source selection."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from kuang import autonomous_create as ac
from kuang.schema import ValidationError


class OnePromptContextTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path.cwd(),prefix=".test-oneprompt-")
        self.root=Path(self.temp.name)
        self.lib=self.root/"catalog/reports/catalog.json"
        self.lib.parent.mkdir(parents=True)
        self.lib.write_text("{}")
        self.plugin=self.root/"plugin.vst3"
        self.plugin.mkdir()
    def tearDown(self):
        self.temp.cleanup()

    def try_create(self,**kwargs):
        return ac.create("deep house in D minor, 16 bars, no lead, without pad",
                         self.lib,self.plugin,"/not/a/host",self.root/"out",
                         private=True,**kwargs)

    def test_optin_requires_valid_groove_mode_and_bounded_audition(self):
        for options in [
            {"contextual_shortlist":True},
            {"groove_template":True,"contextual_shortlist":True,"per_role":1},
            {"groove_template":True,"contextual_shortlist":True,
             "per_role":2,"max_candidates":3},
            {"groove_template":True,"contextual_shortlist":"yes"},
        ]:
            with self.subTest(options=options):
                with patch.object(ac,"select_palette") as mock:
                    with self.assertRaises(ValidationError):
                        self.try_create(**options)
                    mock.assert_not_called()
                self.assertFalse((self.root/"out").exists())

    def test_full_length_context_mode_fail_closed(self):
        with patch.object(ac,"select_palette") as mock:
            with self.assertRaisesRegex(ValidationError,"full-length"):
                ac.create("deep house in C minor, 128 bars",self.lib,self.plugin,
                         "/no/host",self.root/"out",private=True,
                         groove_template=True,contextual_shortlist=True,
                         per_role=2,max_candidates=8)
            mock.assert_not_called()

    def test_short_audition_is_whole_valid_8bar_native_project(self):
        from kuang.house_one_prompt_context import short_audition_project
        from kuang.house_template import template
        from kuang.song import rules_plan
        from kuang.schema import state_hash, validate
        spec,_=rules_plan("deep house in D minor, 16 bars",51)
        source,_=template(spec,profile="deep",harmony_profile="simple",include_pad=False)
        original=state_hash(source)
        cut=source.sections[1].start+source.sections[1].length
        excerpt=short_audition_project(source,cut)
        validate(excerpt)
        self.assertEqual(excerpt.bars,8)
        self.assertEqual([s.name for s in excerpt.sections],["Intro","Groove"])
        self.assertTrue(all(c.start+c.length<=cut for t in excerpt.tracks for c in t.clips))
        self.assertTrue(all(p.tick<=cut for l in excerpt.automation for p in l.points))
        self.assertEqual(state_hash(source),original)
        with self.assertRaises(ValidationError):
            short_audition_project(source,cut+1)

    def test_missing_audition_cannot_publish(self):
        def no_selection(*args,**kw):
            output=Path(args[3]);output.mkdir()
            (output/"selection.json").write_text('{"status":"incomplete","roles":{}}')
        with patch.object(ac,"select_palette",side_effect=no_selection):
            with self.assertRaisesRegex(ValidationError,"complete selection"):
                self.try_create(groove_template=True,contextual_shortlist=True,
                                per_role=2,max_candidates=8)
        self.assertFalse((self.root/"out").exists())
