"""Opt-in phrase-coherent chord timing: structural tests, not musical approval."""
import unittest

from kuang.house_full_arranger import arrange_full_song
from kuang.house_phrase_coherence_v2 import VERSION, regularize_chord_phrases
from kuang.house_template import template
from kuang.schema import ValidationError, dumps, state_hash, validate
from kuang.song import rules_plan


def house(profile, key="F minor", seed=21, **kw):
    spec, _ = rules_plan(f"{profile} house in {key}, 32 bars, 126 bpm", seed)
    return template(spec, profile=profile, impact_pocket=True,
                    groove_identity_v2=True, **kw)


def note_identity(project):
    harmony = next(t for t in project.tracks if t.id == "track-harmony")
    return sorted((n.id, n.pitch, n.velocity, n.duration, n.channel)
                  for clip in harmony.clips for n in clip.notes)


class PhraseCoherenceV2Tests(unittest.TestCase):
    CASES = (("deep", "C minor", 43),
             ("straight", "A minor", 41),
             ("jackin", "G major", 217),
             ("minimal", "D minor", 19),
             ("deep", "E major", 67),
             ("straight", "F# minor", 29),
             ("jackin", "Bb major", 83),
             ("minimal", "G major", 17))

    def test_default_off_preserves_exact_legacy_hash_and_receipt(self):
        a, a_report = house("deep", seed=43)
        b, b_report = house("deep", seed=43, phrase_stable_chords_v2=False)
        self.assertEqual(dumps(a), dumps(b))
        self.assertEqual(a_report, b_report)
        self.assertNotIn("harmony_phrase_v2", a_report)
        self.assertNotIn("house_chord_phrase_coherence_version", a.metadata)

    def test_independent_styles_preserve_notes_sources_and_other_roles(self):
        distinct = set()
        coherent_total = 0
        retimed_total = 0
        for profile, key, seed in self.CASES:
            with self.subTest(profile=profile, key=key, seed=seed):
                original, _ = house(profile, key=key, seed=seed)
                original_text = dumps(original)
                revised, evidence = regularize_chord_phrases(
                    original, profile=profile, seed=seed)
                self.assertEqual(dumps(original), original_text)
                self.assertEqual(evidence["version"], VERSION)
                self.assertTrue(evidence["source_immutable"])
                self.assertTrue(evidence["other_roles_exact"])
                self.assertEqual(evidence["near_bass_attacks_after"] <=
                                 evidence["near_bass_attacks_before"], True)
                validate(revised)
                self.assertEqual(note_identity(original), note_identity(revised))
                original_harmony = next(t for t in original.tracks
                                        if t.id == "track-harmony")
                revised_harmony = next(t for t in revised.tracks
                                       if t.id == "track-harmony")
                self.assertEqual(original_harmony.instrument, revised_harmony.instrument)
                self.assertEqual(original_harmony.controls, revised_harmony.controls)
                self.assertEqual(original_harmony.effects, revised_harmony.effects)
                self.assertEqual(original_harmony.sends, revised_harmony.sends)
                for t in original.tracks:
                    if t.id != "track-harmony":
                        self.assertEqual(t, next(q for q in revised.tracks if q.id == t.id))
                coherent_total += evidence["coherent_phrases"]
                retimed_total += evidence["chord_voice_events_moved"]
                distinct.add(state_hash(revised))
        self.assertEqual(len(distinct), len(self.CASES))
        self.assertGreater(coherent_total, 0)
        self.assertGreater(retimed_total, 0)

    def test_repeatable_and_template_receipt_exposed_only_when_opted_in(self):
        first, receipt = house("jackin", key="G major", seed=217,
                               phrase_stable_chords_v2=True)
        second, repeated = house("jackin", key="G major", seed=217,
                                 phrase_stable_chords_v2=True)
        self.assertEqual(dumps(first), dumps(second))
        self.assertEqual(receipt, repeated)
        self.assertEqual(receipt["harmony_phrase_v2"]["version"], VERSION)
        self.assertEqual(first.metadata["house_chord_phrase_coherence_version"], VERSION)
        self.assertEqual(receipt["harmony_phrase_v2"]["musical_quality"],
                         "NOT_EVALUATED")

    def test_final_canonical_project_drives_groove_evidence_after_copy(self):
        """Regression: template's original role map must not feed post-copy diagnostics."""
        import hashlib
        import json
        from kuang.schema import BAR

        revisions = 0
        for profile, key, seed in self.CASES:
            with self.subTest(profile=profile, key=key, seed=seed):
                original, original_evidence = house(profile, key=key, seed=seed)
                final, report = house(profile, key=key, seed=seed,
                                      phrase_stable_chords_v2=True)
                groove = next(section for section in final.sections
                              if section.name == "Groove")
                expected = {}
                for role in report["full_groove_onsets"]:
                    track = next(t for t in final.tracks
                                 if t.id == "track-" + role)
                    expected[role] = sorted(
                        c.start + n.start - groove.start
                        for c in track.clips for n in c.notes
                        if groove.start <= c.start + n.start <
                        groove.start + groove.length)
                self.assertEqual(report["full_groove_onsets"], expected)
                actual_digest = hashlib.sha256(json.dumps(
                    expected, sort_keys=True,
                    separators=(",", ":")).encode()).hexdigest()
                self.assertEqual(report["groove_fingerprint_sha256"],
                                 actual_digest)
                self.assertEqual([s.start for s in original.sections],
                                 [s.start for s in final.sections])
                chords = next(t for t in final.tracks if t.id == "track-harmony")
                reported = sorted(c.start + n.start - groove.start
                                  for c in chords.clips for n in c.notes
                                  if groove.start <= c.start + n.start <
                                  groove.start + groove.length)
                self.assertEqual(
                    report["harmony_phrase_v2_groove_note_onsets"], reported)
                original_chords = next(t for t in original.tracks
                                       if t.id == "track-harmony")
                old = sorted(c.start + n.start - groove.start
                             for c in original_chords.clips for n in c.notes
                             if groove.start <= c.start + n.start <
                             groove.start + groove.length)
                revisions += int(old != reported)
        self.assertGreater(revisions, 0, "No sampled case exercises changed chord timing")

    def test_full_song_arrangement_preserves_native_ready_structure(self):
        for profile in ("deep", "straight", "jackin", "minimal"):
            with self.subTest(profile=profile):
                source, receipt = house(profile, key="D minor", seed=41,
                                        phrase_stable_chords_v2=True)
                original = state_hash(source)
                full, report = arrange_full_song(
                    source, bars=128, seed=41, profile=profile,
                    phrase_development_v1=True)
                self.assertEqual(state_hash(source), original)
                self.assertTrue(all(report["technical_gates"].values()))
                self.assertTrue(report["technical_pass"])
                self.assertEqual(full.bars, 128)
                validate(full)

    def test_invalid_flags_fail_closed(self):
        spec, _ = rules_plan("deep house in C minor, 32 bars", 43)
        for bad in ("yes", 1, None):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                template(spec, profile="deep", impact_pocket=True,
                         phrase_stable_chords_v2=bad)
        with self.assertRaises(ValidationError):
            template(spec, profile="deep", phrase_stable_chords_v2=True)
        with self.assertRaises(ValidationError):
            template(spec, profile="deep", impact_pocket=True,
                     harmony_interlock=False, phrase_stable_chords_v2=True)

    def test_invalid_source_constraints_do_not_modify_project(self):
        original, _ = house("deep")
        snapshot = dumps(original)
        for profile, seed in (("not-house", 21), ("deep", -1),
                              ("deep", True), ("deep", 2**32)):
            with self.subTest(profile=profile, seed=seed), self.assertRaises(ValidationError):
                regularize_chord_phrases(original, profile=profile, seed=seed)
        self.assertEqual(dumps(original), snapshot)


if __name__ == "__main__":
    unittest.main()
