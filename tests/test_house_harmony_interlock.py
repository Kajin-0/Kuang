"""Cross-style structural and regression tests, not musical approval."""
import unittest
from copy import deepcopy

from kuang import midi
from kuang.house_harmony_interlock import apply_interlock
from kuang.house_template import template
from kuang.schema import BAR, ValidationError, dumps, state_hash, validate
from kuang.song import rules_plan


def events(p, role):
    track = next(t for t in p.tracks if t.id == "track-" + role)
    return [(c.start + n.start, n.duration, n.pitch, n.velocity, n.channel)
            for c in track.clips for n in c.notes]


class HarmonyInterlockGeneralizationTests(unittest.TestCase):
    CASES = [
        ("deep", "C minor", 43, 126),
        ("straight", "A minor", 41, 125),
        ("jackin", "F minor", 51, 129),
        ("minimal", "G major", 17, 122),
        ("deep", "E major", 67, 123),
        ("straight", "D minor", 19, 128),
        ("jackin", "Bb major", 83, 124),
        ("minimal", "F# minor", 29, 127),
    ]

    def test_eight_distinct_independent_keys_styles_preserve_score_and_diversity(self):
        different_chord_fingerprints = set()
        choices = set()
        for profile, key, seed, bpm in self.CASES:
            with self.subTest(profile=profile, key=key, seed=seed):
                spec, _ = rules_plan(f"{profile} house in {key}, 16 bars, {bpm} bpm", seed)
                original, _ = template(spec, profile=profile, include_pad=True,
                                       impact_pocket=True, harmony_interlock=False)
                improved, report = template(spec, profile=profile, include_pad=True,
                                            impact_pocket=True)
                replay, replay_report = template(spec, profile=profile, include_pad=True,
                                                 impact_pocket=True)
                self.assertEqual(dumps(improved), dumps(replay))
                self.assertEqual(report, replay_report)
                validate(improved)
                evidence = report["harmony_interlock"]
                self.assertEqual(evidence["profile"], profile)
                self.assertGreater(evidence["retimed_chord_voice_events"], 0)
                self.assertEqual(evidence["unhandled_bars"], 0)
                self.assertLessEqual(evidence["near_bass_onset_groups_after"],
                                     evidence["near_bass_onset_groups_before"])
                self.assertEqual(evidence["chord_groups_before"], evidence["chord_groups_after"])
                self.assertEqual(evidence["perceptual_quality"], "NEEDS_LISTENING")
                for role in ("kick","snare","hats","percussion","bass","pad"):
                    self.assertEqual(events(original,role), events(improved,role))
                a = next(t for t in original.tracks if t.id == "track-harmony")
                b = next(t for t in improved.tracks if t.id == "track-harmony")
                self.assertEqual(a.effects,b.effects)
                self.assertEqual(a.controls,b.controls)
                self.assertEqual(a.instrument,b.instrument)
                self.assertEqual(sorted((n.id,n.pitch,n.velocity,n.duration)
                                  for c in a.clips for n in c.notes),
                                 sorted((n.id,n.pitch,n.velocity,n.duration)
                                  for c in b.clips for n in c.notes))
                different_chord_fingerprints.add(evidence["harmony_midi_fingerprint_sha256"])
                choices.add(tuple(evidence["pattern_choices"].values()))
        self.assertEqual(len(different_chord_fingerprints),len(self.CASES))
        self.assertGreaterEqual(len(choices),3)

    def test_opt_out_preserves_legacy_impact_rhythm(self):
        spec,_=rules_plan("deep house in C minor 16 bars",43)
        old,_=template(spec,profile="deep",impact_pocket=True,
                       harmony_interlock=False)
        new,_=template(spec,profile="deep",impact_pocket=True,
                       harmony_interlock=True)
        self.assertNotEqual(events(old,"harmony"),events(new,"harmony"))
        self.assertEqual(events(old,"bass"),events(new,"bass"))
        self.assertIsNone(template(spec,profile="deep", impact_pocket=False)[1]["harmony_interlock"])

    def test_invalid_profile_rejected_without_source_modification(self):
        spec,_=rules_plan("deep house in C minor 16 bars",43)
        p,_=template(spec,profile="deep",impact_pocket=True,harmony_interlock=False)
        old=state_hash(p)
        with self.assertRaises(ValidationError):
            apply_interlock(p,"unknown",43)
        self.assertEqual(old,state_hash(p))


if __name__ == "__main__":
    unittest.main()
