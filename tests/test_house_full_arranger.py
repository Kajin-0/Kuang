"""Generalization tests: many house styles, keys, lengths, seeds, same reusable grammar."""
import hashlib
import unittest
from copy import deepcopy

from kuang.house_full_arranger import (
    ALLOWED_BARS, FORMS, arrange_full_song, parse_long_form,
)
from kuang.house_template import PROFILES, template
from kuang.midi import export_bytes
from kuang.schema import BAR, PPQ, ValidationError, dumps, state_hash, validate
from kuang.song import rules_plan


def source(profile="deep",key="C minor",seed=17,include_pad=True):
    spec,_=rules_plan(f"{profile} house in {key}, 32 bars",seed)
    return template(spec,profile=profile,include_pad=include_pad,
                    harmony_profile="simple")[0]


class FullHouseFormTests(unittest.TestCase):
    def test_full_matrix_four_styles_keys_lengths_seeds(self):
        for profile in PROFILES:
            for key in ("C major","D minor"):
                seed=17
                s=source(profile,key,seed)
                before=state_hash(s)
                for bars in ALLOWED_BARS:
                    with self.subTest(profile=profile,key=key,bars=bars,seed=seed):
                            p,proof=arrange_full_song(s,bars=bars,seed=seed)
                            validate(p)
                            self.assertEqual(s.bars,32)
                            self.assertEqual(state_hash(s),before)
                            self.assertTrue(proof["technical_pass"])
                            self.assertTrue(all(proof["technical_gates"].values()))
                            self.assertEqual(p.bars,bars)
                            self.assertEqual(sum(sec.length for sec in p.sections),bars*BAR)
                            self.assertEqual([sec.length//BAR for sec in p.sections],list(FORMS[bars]))
                            self.assertEqual(len(proof["sections"]),8)
                            self.assertEqual(proof["perceptual_quality"],"NEEDS_LISTENING")
                            self.assertNotIn("track-lead",{t.id for t in p.tracks})
                            self.assertNotIn("track-arp",{t.id for t in p.tracks})
                            self.assertGreater(len(export_bytes(p)),1000)

    def test_optin_development_reuses_source_drop_phrase_and_keeps_groove(self):
        from kuang.house_gates import evaluate
        from kuang.house_full_arranger import DEVELOPMENT_VERSION
        spec,_=rules_plan("jackin house in G major 32 bars, 127 bpm",217)
        source,_=template(spec,profile="jackin",impact_pocket=True,
                          groove_identity_v2=True)
        old=state_hash(source)
        legacy,old_receipt=arrange_full_song(source,bars=128,profile="jackin",seed=217)
        changed,receipt=arrange_full_song(source,bars=128,profile="jackin",
                                           seed=217,phrase_development_v1=True)
        self.assertEqual(state_hash(source),old)
        self.assertNotIn("phrase_development_version",legacy.metadata)
        self.assertEqual(receipt["phrase_development"]["version"],DEVELOPMENT_VERSION)
        self.assertEqual(receipt["technical_gates"],old_receipt["technical_gates"])
        self.assertEqual(changed.metadata["phrase_development_version"],DEVELOPMENT_VERSION)
        self.assertNotEqual(export_bytes(legacy),export_bytes(changed))
        self.assertEqual([(x.name,x.start,x.length) for x in legacy.sections],
                         [(x.name,x.start,x.length) for x in changed.sections])
        def section_events(p,role,section):
            track=next(t for t in p.tracks if t.id=="track-"+role)
            region=next(s for s in p.sections if s.name==section)
            return [(c.start+n.start-region.start,n.duration,n.pitch,n.velocity)
                    for c in track.clips for n in c.notes
                    if region.start<=c.start+n.start<region.start+region.length]
        for role in ("bass","harmony","kick"):
            self.assertEqual(section_events(legacy,role,"Groove A"),
                             section_events(changed,role,"Groove A"))
        self.assertEqual(section_events(legacy,"kick","Main Drop"),
                         section_events(changed,"kick","Main Drop"))
        self.assertNotEqual(section_events(legacy,"bass","Main Drop"),
                            section_events(changed,"bass","Main Drop"))
        self.assertNotEqual(section_events(legacy,"harmony","Main Drop"),
                            section_events(changed,"harmony","Main Drop"))
        old_gate=evaluate(legacy,expected_no_lead_arp=True)
        new_gate=evaluate(changed,expected_no_lead_arp=True)
        self.assertEqual(old_gate["hard_failures"],[])
        self.assertEqual(new_gate["hard_failures"],[])
        self.assertEqual(old_gate["diagnostics"]["D02_core_groove_drop_equal_fraction"]["bass"],1.)
        self.assertLess(new_gate["diagnostics"]["D02_core_groove_drop_equal_fraction"]["bass"],.5)
        self.assertFalse(receipt["phrase_development"]["new_melodic_notes_added"])

    def test_development_matrix_profiles_and_source_immutability(self):
        from kuang.house_gates import evaluate
        for profile in PROFILES:
            for key in ("C major","D minor"):
                spec,_=rules_plan(f"{profile} house in {key}, 32 bars, 126 bpm",17)
                original,_=template(spec,profile=profile,impact_pocket=True,
                                    groove_identity_v2=True)
                snapshot=dumps(original)
                for bars in (96,128,160):
                    with self.subTest(profile=profile,key=key,bars=bars):
                        p,proof=arrange_full_song(original,bars=bars,profile=profile,
                             seed=17,phrase_development_v1=True)
                        self.assertTrue(proof["technical_pass"])
                        self.assertEqual(snapshot,dumps(original))
                        score=evaluate(p,expected_no_lead_arp=True)
                        self.assertEqual(score["hard_failures"],[])
                        self.assertEqual(score["diagnostics"]["D02_core_groove_drop_equal_fraction"]["bass"],0.)
                        self.assertTrue(all(
                            x["kick_source"]=="Groove" and
                            x["bass_source"]==x["harmony_source"]
                            for x in proof["phrase_development"]["source_eight_bar_blocks"]))
                        self.assertGreater(len(export_bytes(p)),1000)

    def test_explicit_bool_required_for_development(self):
        with self.assertRaises(ValidationError):
            arrange_full_song(source(),phrase_development_v1="yes")

    def test_same_prompt_seed_exact_and_other_seed_musically_varied(self):
        s=source("jackin","G minor",17)
        a,ar=arrange_full_song(s,bars=128,seed=17)
        b,br=arrange_full_song(s,bars=128,seed=17)
        c,cr=arrange_full_song(s,bars=128,seed=18)
        self.assertEqual(dumps(a),dumps(b))
        self.assertEqual(ar,br)
        self.assertNotEqual(export_bytes(a),export_bytes(c))
        self.assertEqual([(sec.name,sec.length) for sec in a.sections],
                         [(sec.name,sec.length) for sec in c.sections])
        # Variation cannot replace bass/kick pitches or their actual note onset.
        for role in ("kick","bass"):
            ta=next(t for t in a.tracks if t.id=="track-"+role)
            tc=next(t for t in c.tracks if t.id=="track-"+role)
            notes=lambda t:sorted((cl.start+n.start,n.pitch,n.duration,n.velocity)
                                   for cl in t.clips for n in cl.notes)
            self.assertEqual(notes(ta),notes(tc))

    def test_impact_full_form_preserves_source_harmony_attack_and_bass_pad_duck(self):
        from kuang.house_template import _reschedule_impact_duck
        spec,_=rules_plan("jackin house in G major 32 bars, 127 bpm",217)
        source,source_receipt=template(spec,profile="jackin",include_pad=True,
                                       impact_pocket=True,groove_identity_v2=True)
        self.assertEqual(source.metadata["ducking_policy"],
                         "bass-tail-3db-115ms; pad-1.25db-143ms; harmony-dry-0db")
        self.assertFalse(any(a.id=="production-harmony-duck" for a in source.automation))
        original=state_hash(source)
        full,report=arrange_full_song(source,bars=128,profile="jackin",seed=217)
        self.assertEqual(original,state_hash(source))
        self.assertTrue(report["technical_pass"])
        self.assertFalse(any(a.id=="production-harmony-duck" for a in full.automation))
        bass=next(a for a in full.automation if a.id=="production-bass-duck")
        pad=next(a for a in full.automation if a.id=="production-pad-duck")
        self.assertIn(next(t for t in full.tracks if t.id=="track-bass").controls["mixer.gain_db"]-3,
                      [v.value for v in bass.points])
        self.assertIn(next(t for t in full.tracks if t.id=="track-pad").controls["mixer.gain_db"]-1.25,
                      [v.value for v in pad.points])
        self.assertGreater(len(bass.points),500)
        self.assertEqual(report["perceptual_quality"],"NEEDS_LISTENING")

    def test_non_impact_full_form_retains_legacy_harmony_duck(self):
        baseline=source("jackin","G major",217,include_pad=True)
        p,receipt=arrange_full_song(baseline,bars=128,seed=217)
        chord=next(t for t in p.tracks if t.id=="track-harmony")
        lane=next(a for a in p.automation if a.id=="production-harmony-duck")
        self.assertEqual(lane.points[2].value,chord.controls["mixer.gain_db"]-5)
        self.assertTrue(receipt["technical_pass"])

    def test_break_main_drop_outro_no_pad(self):
        s=source("minimal","E major",19,include_pad=False)
        p,proof=arrange_full_song(s,bars=112,seed=19)
        self.assertNotIn("track-pad",{t.id for t in p.tracks})
        matrix={s["name"]:s for s in proof["sections"]}
        self.assertEqual(matrix["Breakdown"]["events"]["kick"],0)
        self.assertEqual(matrix["Breakdown"]["events"]["bass"],0)
        self.assertGreater(matrix["Main Drop"]["events"]["kick"],0)
        self.assertGreater(matrix["Main Drop"]["events"]["bass"],0)
        self.assertGreater(matrix["Outro"]["events"]["kick"],0)
        self.assertGreater(matrix["Build"]["events"]["hats"],0)
        self.assertGreater(matrix["Intro"]["events"]["kick"],0)
        self.assertEqual(matrix["Groove A"]["events"]["percussion"],0)

    def test_unmatched_sources_rejected_and_no_mutation(self):
        s=source()
        snapshot=dumps(s)
        for bars in (8,16,32,100,200,None):
            with self.subTest(bars=bars),self.assertRaises(ValidationError):
                arrange_full_song(s,bars=bars)
        with self.assertRaises(ValidationError):
            arrange_full_song(s,profile="unsupported")
        s2=deepcopy(s);s2.bars=40
        with self.assertRaises(ValidationError):
            arrange_full_song(s2)
        self.assertEqual(dumps(s),snapshot)

    def test_prompt_intent_explicit_and_minutes(self):
        self.assertEqual(parse_long_form("deep house, 128 bars",bpm=126),
                         (128,"deep house, 32 bars"))
        self.assertEqual(parse_long_form("warm deep house full-length, 126 bpm"),
                         (128,"warm deep house full-length, 126 bpm"))
        self.assertEqual(parse_long_form("extended mix house"),
                         (160,"extended mix house"))
        target,planner=parse_long_form("make house about 4 minutes",bpm=126)
        self.assertIn(target,ALLOWED_BARS)
        self.assertIn("house",planner)
        with self.assertRaises(ValidationError):
            parse_long_form("house 96 bars",requested=128)
        with self.assertRaises(ValidationError):
            parse_long_form("house 128 bars around 4 minutes",bpm=126)


class DrumSceneDevelopmentTests(unittest.TestCase):
    """Independent seed/style technical proof, no subjective score claims."""

    def test_style_seed_matrix_preserves_kick_bass_harmony_and_diversifies_hats(self):
        from kuang.house_gates import evaluate
        for style in ("straight","deep","jackin","minimal"):
            for seed in (17,41,217):
                with self.subTest(style=style,seed=seed):
                    spec,_=rules_plan(f"{style} house C minor 32 bars 126 bpm",seed)
                    short,_=template(spec,profile=style,impact_pocket=True,
                                     groove_identity_v2=True)
                    original=dumps(short)
                    baseline,_=arrange_full_song(
                        short,bars=128,seed=seed,phrase_development_v1=True)
                    variant,receipt=arrange_full_song(
                        short,bars=128,seed=seed,phrase_development_v1=True,
                        drum_scenes_v1=True)
                    self.assertEqual(dumps(short),original)
                    validate(variant)
                    self.assertTrue(receipt["technical_gates"]["four_on_floor_groove_a"])
                    self.assertTrue(receipt["drum_scenes"]["protected_kick_bass_chords"])
                    self.assertGreater(sum(x["added"]+x["removed"]
                                           for x in receipt["drum_scenes"]["changes"]),0)
                    for name in ("kick","bass","harmony"):
                        a=next(t for t in baseline.tracks if t.id=="track-"+name)
                        b=next(t for t in variant.tracks if t.id=="track-"+name)
                        self.assertEqual(a,b)
                    a=evaluate(baseline,expected_no_lead_arp=True)
                    b=evaluate(variant,expected_no_lead_arp=True)
                    self.assertEqual(b["hard_failures"],[])
                    self.assertEqual(a["diagnostics"]["D02_core_groove_drop_equal_fraction"]["hats"],1.)
                    self.assertLess(b["diagnostics"]["D02_core_groove_drop_equal_fraction"]["hats"],1.)
                    self.assertEqual(b["diagnostics"]["D02_core_groove_drop_equal_fraction"]["kick"],1.)
                    self.assertEqual(b["diagnostics"]["D02_core_groove_drop_equal_fraction"]["snare"],1.)

    def test_optin_default_unchanged_and_idempotency_gate(self):
        from kuang.house_drum_scenes_v1 import apply_drum_scenes
        s=source()
        a,_=arrange_full_song(s,bars=128,seed=17)
        b,_=arrange_full_song(s,bars=128,seed=17,drum_scenes_v1=False)
        self.assertEqual(dumps(a),dumps(b))
        c,_=apply_drum_scenes(a,seed=17)
        self.assertNotEqual(export_bytes(a),export_bytes(c))
        with self.assertRaises(ValidationError):
            apply_drum_scenes(c,seed=17)
        with self.assertRaises(ValidationError):
            arrange_full_song(s,bars=128,drum_scenes_v1="yes")
