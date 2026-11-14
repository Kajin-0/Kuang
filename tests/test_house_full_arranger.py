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
