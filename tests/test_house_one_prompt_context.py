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

    def test_pad_rescue_requires_explicit_context_mode_and_valid_boolean(self):
        for opts in (
            {"contextual_pad_rescue":True},
            {"groove_template":True,"contextual_pad_rescue":True},
            {"groove_template":True,"contextual_shortlist":True,
             "contextual_pad_rescue":"yes"},
        ):
            with self.subTest(opts=opts):
                with patch.object(ac,"select_palette") as selector:
                    with self.assertRaises(ValidationError):
                        self.try_create(**opts)
                    selector.assert_not_called()
                self.assertFalse((self.root/"out").exists())

    def test_no_pad_source_review_skips_without_auto_adding_pad(self):
        from kuang.house_timbre_suitability import source_names
        # Source review remains purely opt-in; no new song role is introduced.
        selection={"status":"complete","roles":{}}
        receipt=source_names(selection)
        self.assertEqual(receipt["roles"],{})
        self.assertIsNone(receipt["winner"])

    def test_pad_context_screening_skips_clean_songs_without_native_render(self):
        from kuang.house_one_prompt_context import _pad_candidate
        from unittest.mock import Mock
        candidate={"status":"accepted","runtime_verified":True,
                   "source_sha256":"b"*64,"source_preset_name":"verified other pad"}
        native=Mock()
        # This models the normal A/B situation: verified pad present but no
        # isolated-source review flag indicating excess lower-mid congestion.
        result,receipt=_pad_candidate(
            project=None,assignments={"track-pad":"private-patch"},
            shortlist={"pad":[candidate]},adapter=None,defaults=None,native=native,
            sound_assets=None,scratch=None,window=None,excerpt_seconds=None,
            timeout=None,library=None,baseline_meter=None,
            original_bass_stem=None,
            pad_review={"source_sha256":"a"*64,"review_flags":[],
                        "source_name":"existing suitable pad"},
            original_hash=None,baseline_hard=set())
        self.assertIsNone(result)
        self.assertEqual(receipt["status"],"SKIPPED_NO_PAD_CONFLICT_FLAG")
        self.assertFalse(receipt["chosen"])
        native.export.assert_not_called()
        native.render.assert_not_called()

    def test_pad_context_does_not_insert_missing_pad(self):
        from kuang.house_one_prompt_context import _pad_candidate
        from unittest.mock import Mock
        native=Mock()
        candidate,observation=_pad_candidate(
            project=None,assignments={},shortlist={},adapter=None,
            defaults=None,native=native,sound_assets=None,scratch=None,
            window=None,excerpt_seconds=None,timeout=None,library=None,
            baseline_meter=None,original_bass_stem=None,
            pad_review=None,original_hash=None,baseline_hard=set())
        self.assertIsNone(candidate)
        self.assertEqual(observation["status"],"SKIPPED_NO_PAD")
        native.render.assert_not_called()

    def test_full_length_context_mode_uses_same_prompt_short_nucleus(self):
        """Long-form requests must now reach native-palette preflight.

        The 32-bar nucleus is arranged ONLY after context source selection.
        No Vital audition or native render is required for this test.
        """
        seen={}
        def fail_selection(*args,**kwargs):
            seen.update(kwargs)
            raise ValidationError("intentional test stop before private source work")
        with patch.object(ac,"select_palette",side_effect=fail_selection) as mock:
            with self.assertRaisesRegex(ValidationError,"intentional test stop"):
                ac.create("deep house in C minor, 128 bars",self.lib,self.plugin,
                         "/no/host",self.root/"out",private=True,
                         groove_template=True,contextual_shortlist=True,
                         per_role=2,max_candidates=8)
            mock.assert_called_once()
        self.assertEqual(seen["musical_spec"].bars,32)
        self.assertFalse((self.root/"out").exists())

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

    def test_32bar_source_becomes_96bar_song_without_reselecting_sounds(self):
        from kuang.house_one_prompt_context import short_audition_project
        from kuang.house_full_arranger import arrange_full_song
        from kuang.house_template import template
        from kuang.song import rules_plan
        from kuang.schema import state_hash, validate
        source_spec,_=rules_plan("deep house in D minor, 32 bars",51)
        nucleus,_=template(source_spec,profile="deep",harmony_profile="simple",include_pad=False)
        original=state_hash(nucleus)
        groove=next(x for x in nucleus.sections if x.name=="Groove")
        audition=short_audition_project(nucleus,groove.start+groove.length)
        validate(audition)
        self.assertEqual(audition.bars,16)
        expanded,receipt=arrange_full_song(nucleus,bars=96,profile="deep",seed=51)
        validate(expanded)
        self.assertEqual(expanded.bars,96)
        self.assertEqual(state_hash(nucleus),original)
        for role in ("track-bass","track-harmony"):
            original_track=next(t for t in nucleus.tracks if t.id==role)
            long_track=next(t for t in expanded.tracks if t.id==role)
            self.assertEqual(original_track.instrument,long_track.instrument)
            self.assertEqual(original_track.effects,long_track.effects)
            self.assertEqual(original_track.controls,long_track.controls)

    def test_missing_audition_cannot_publish(self):
        def no_selection(*args,**kw):
            output=Path(args[3]);output.mkdir()
            (output/"selection.json").write_text('{"status":"incomplete","roles":{}}')
        with patch.object(ac,"select_palette",side_effect=no_selection):
            with self.assertRaisesRegex(ValidationError,"complete selection"):
                self.try_create(groove_template=True,contextual_shortlist=True,
                                per_role=2,max_candidates=8)
        self.assertFalse((self.root/"out").exists())
