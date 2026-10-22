import json
import unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from kuang.composer import compose
from kuang.generator import generate
from kuang.revision import (ChangeIntent, RevisionRequest, RulesRevisionPlanner, apply_plan,
                            comparison, prepare_revision, replay_revision, resolve_region, resolve_tracks)
from kuang.schema import (BAR, PPQ, AutomationLane, AutomationPoint, Lock, Note,
                          ValidationError, decode, dumps, load, state_hash, validate)
from kuang.transactions import LockedError
from test_song import PROMPTS
from kuang.song import rules_plan

COMPOUND = "make the bass more aggressive, simplify the drums in the Main, keep everything else unchanged"


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.project = compose(rules_plan(PROMPTS[0], 17)[0])
        self.before = dumps(self.project)
        self.planner = RulesRevisionPlanner()

    def prepare(self, prompt=COMPOUND, project=None):
        p = project or self.project
        return prepare_revision(p, self.planner.propose(p, prompt))

    def test_compound_matches_full_independently_constructed_expected_state(self):
        plan, result, receipt = self.prepare()
        expected = deepcopy(self.project)
        bass = next(t for t in expected.tracks if t.id == "track-bass")
        bass.instrument.parameters.update({"synth.cutoff_hz": 880, "synth.resonance": 0.28})
        removed = {r["note"]["id"] for r in plan["comparison"]["removed_notes"]}
        self.assertGreater(len(removed), 0)
        for track in expected.tracks:
            for clip in track.clips:
                clip.notes = [n for n in clip.notes if n.id not in removed]
        self.assertEqual(dumps(result), dumps(expected))
        self.assertEqual(dumps(self.project), self.before)
        self.assertEqual(result.metadata, self.project.metadata)
        self.assertEqual(result.automation, self.project.automation)
        self.assertEqual(plan["comparison"]["unchanged_projection_before_hash"], plan["comparison"]["unchanged_projection_after_hash"])

    def test_each_intent_keeps_its_narrow_scope_and_hash_chain(self):
        plan, result, receipt = self.prepare()
        scalar, notes = plan["steps"]
        self.assertEqual(scalar["scope"], {"track_ids": ["track-bass"], "clip_ids": [],
            "parameter_ids": ["synth.cutoff_hz", "synth.resonance"], "start": None, "end": None})
        self.assertEqual((notes["scope"]["start"], notes["scope"]["end"]), (4*BAR, 8*BAR))
        self.assertEqual(notes["scope"]["parameter_ids"], [])
        self.assertEqual(scalar["after_hash"], notes["before_hash"])
        self.assertEqual(len(receipt["receipts"]), 2)
        oxford, _, _ = self.prepare("Please make the bass more aggressive, and simplify the drums in Main, then keep everything else unchanged.")
        self.assertEqual([s["operations"] for s in oxford["steps"]], [s["operations"] for s in plan["steps"]])

    def test_surviving_notes_ids_order_and_outside_region_are_exact(self):
        plan, result, _ = self.prepare()
        old = {n.id: n for t in self.project.tracks for c in t.clips for n in c.notes}
        for t in result.tracks:
            original = next(x for x in self.project.tracks if x.id == t.id)
            for c, before in zip(t.clips, original.clips):
                self.assertEqual(c.notes, [n for n in before.notes if n.id in {x.id for x in c.notes}])
                for n in c.notes: self.assertEqual(n, old[n.id])
                if c.start+c.length <= 4*BAR or c.start >= 8*BAR:
                    self.assertEqual(c.notes, before.notes)
        for removal in plan["comparison"]["removed_notes"]:
            self.assertGreaterEqual(removal["absolute_start"], 4*BAR)
            self.assertLessEqual(removal["absolute_end"], 8*BAR)
        self.assertEqual(result.sections, self.project.sections)

    def test_thinning_preserves_one_accent_per_pitch_per_halfbar(self):
        plan, result, _ = self.prepare("simplify the drums in bars 5-8")
        for t in result.tracks[:3]:
            buckets = []
            for c in t.clips:
                for n in c.notes:
                    start = c.start+n.start
                    if 4*BAR <= start < 8*BAR:
                        buckets.append((start//BAR, start % BAR//(2*PPQ), n.pitch))
            self.assertEqual(len(buckets), len(set(buckets)))
        self.assertEqual(plan["comparison"]["parameter_changes"], [])

    def test_independent_gain_and_reverb_changes_leave_fx_order_and_automation(self):
        plan, result, _ = self.prepare("make the lead reverb wetter and turn the lead down by 3 dB")
        old, new = self.project.tracks[-1], result.tracks[-1]
        self.assertEqual(new.controls["mixer.gain_db"], old.controls["mixer.gain_db"]-3)
        self.assertAlmostEqual(new.effects[-1].parameters["effect.wet"], old.effects[-1].parameters["effect.wet"]+0.12)
        self.assertEqual([e.id for e in old.effects], [e.id for e in new.effects])
        self.assertEqual(result.automation, self.project.automation)
        self.assertEqual(len(plan["comparison"]["parameter_changes"]), 2)

    def test_exact_compound_undo_redo_including_array_order(self):
        _, result, receipt = self.prepare()
        self.assertEqual(dumps(replay_revision(result, receipt, undo=True)), self.before)
        self.assertEqual(dumps(replay_revision(self.project, receipt, undo=False)), dumps(result))

    def test_unsupported_whole_or_partial_clauses_never_change_project(self):
        for prompt in ("make it better", "add distortion", "make bass louder", "simplify the drums", "change the tempo to 150",
                       "make the bass more aggressive, add vocals", "make the lead reverb wetter but only in Main",
                       "make the bass more aggressive; rm -rf /", "keep everything else unchanged", "make bass aggressive,", ""):
            with self.subTest(prompt=prompt):
                with self.assertRaises(ValidationError): self.prepare(prompt)
                self.assertEqual(dumps(self.project), self.before)

    def test_missing_section_is_not_aliased_to_main(self):
        with self.assertRaisesRegex(ValidationError, "available: Intro, Main, Break, Finale"):
            self.prepare("simplify the drums in the verse")

    def test_bar_ranges_are_one_based_inclusive_then_half_open_ticks(self):
        self.assertEqual(resolve_region(self.project, "bars 5-8"), (4*BAR, 8*BAR))
        self.assertEqual(resolve_region(self.project, "bar 16"), (15*BAR, 16*BAR))
        self.assertEqual(resolve_region(self.project, "section Main"), (4*BAR, 8*BAR))
        for region in ("bars 0-2", "bars 9-3", "bars 1-17", "bar -1", "bars 5.5-8"):
            with self.assertRaises(ValidationError): resolve_region(self.project, region)

    def test_region_crossing_note_is_rejected_without_truncation(self):
        hats = self.project.tracks[2].clips[1]
        hats.notes.append(Note("cross-boundary", BAR-60, 120, 75, 70, 9))
        validate(self.project)
        before = dumps(self.project)
        with self.assertRaisesRegex(ValidationError, "crosses"):
            self.prepare("simplify drums in bars 6-8")
        self.assertEqual(dumps(self.project), before)

    def test_explicit_preservation_conflicts_fail_whole_compound(self):
        for prompt in (COMPOUND + ", keep the bass unchanged", COMPOUND + ", keep the hats unchanged"):
            with self.assertRaisesRegex(ValidationError, "preserved"):
                self.prepare(prompt)
        plan, result, _ = self.prepare(COMPOUND + ", keep the lead unchanged")
        self.assertEqual(result.tracks[-1], self.project.tracks[-1])
        self.assertEqual(plan["request"]["preserve_track_ids"], ["track-lead"])

    def test_device_track_clip_and_parameter_locks_reject(self):
        for target, parameter, prompt in (
            ("track-bass", None, COMPOUND), ("instrument-bass", None, COMPOUND),
            ("instrument-bass", "synth.resonance", COMPOUND),
            ("track-hats", None, COMPOUND), ("clip-hats-1", None, COMPOUND),
            ("effect-lead-reverb", "effect.wet", "make the lead reverb wetter"),
            ("track-lead", "mixer.gain_db", "turn the lead down by 3 dB"),
        ):
            with self.subTest(target=target):
                p = deepcopy(self.project); p.locks.append(Lock("test-lock", target, parameter))
                before = dumps(p)
                with self.assertRaises(LockedError): self.prepare(prompt, p)
                self.assertEqual(dumps(p), before)

    def test_automated_base_parameter_edit_is_explicitly_rejected(self):
        with self.assertRaisesRegex(ValidationError, "automated"):
            self.prepare("turn the harmony up by 2 dB")
        self.project.automation.append(AutomationLane("test-filter-lane", "instrument-bass", "synth.cutoff_hz",
                                      [AutomationPoint("test-filter-point", 0, 220, "linear")]))
        with self.assertRaisesRegex(ValidationError, "automated"):
            self.prepare("make the bass more aggressive")

    def test_no_implicit_fx_or_parameters_inserted(self):
        p = deepcopy(self.project); p.tracks[-1].effects = []
        with self.assertRaisesRegex(ValidationError, "existing reverb"):
            self.prepare("make the lead reverb wetter", p)
        p = deepcopy(self.project); del p.tracks[3].instrument.parameters["synth.cutoff_hz"]
        with self.assertRaisesRegex(ValidationError, "explicit existing"):
            self.prepare("make the bass more aggressive", p)

    def test_saturation_never_lowers_already_aggressive_parameters(self):
        p = deepcopy(self.project)
        p.tracks[3].instrument.parameters.update({"synth.cutoff_hz": 19000, "synth.resonance": 0.9})
        with self.assertRaisesRegex(ValidationError, "no change"):
            self.prepare("make the bass more aggressive", p)

    def test_duplicate_parameter_or_overlapping_region_intents_fail(self):
        for prompt in ("turn lead down by 2 dB, turn lead down by 1 dB", "make bass aggressive, make bass aggressive",
                       "simplify drums in Main, simplify drums in bars 5-6"):
            with self.assertRaises(ValidationError): self.prepare(prompt)
        plan, _, _ = self.prepare("simplify drums in Main, simplify drums in Finale")
        self.assertEqual(len(plan["steps"]), 2)

    def test_strict_structured_request_schema_and_semantic_bounds(self):
        request = asdict(self.planner.propose(self.project, COMPOUND))
        for update in ({"version": "99"}, {"command": "touch /tmp/injected"}, {"intents": []},
                       {"expected_before_hash": "invalid"}, {"preserve_track_ids": ["missing"]}):
            with self.subTest(update=update):
                with self.assertRaises(ValidationError): prepare_revision(self.project, decode(RevisionRequest, {**request, **update}))
        for intent in (ChangeIntent("gain", ["track-lead"], None, None, 7), ChangeIntent("gain", ["track-lead"], None, None, 0),
                       ChangeIntent("gain", ["track-lead"], 0, BAR, 1), ChangeIntent("gain", ["missing"], None, None, 1),
                       ChangeIntent("simplify_drums", ["track-hats"], 1, BAR, None),
                       ChangeIntent("simplify_drums", ["track-lead"], 0, BAR, None),
                       ChangeIntent("reverb", ["track-lead", "track-lead"], None, None, 0.2)):
            with self.assertRaises(ValidationError):
                prepare_revision(self.project, RevisionRequest("1", state_hash(self.project), "structured request", [intent], []))

    def test_stale_hash_covers_unrelated_state_and_metadata(self):
        request = self.planner.propose(self.project, COMPOUND)
        self.project.metadata["annotation"] = "human edit"
        with self.assertRaisesRegex(ValidationError, "stale"):
            prepare_revision(self.project, request)

    def test_reviewed_plan_tampering_unknown_fields_and_scope_types_fail(self):
        plan, result, receipt = self.prepare()
        self.assertEqual(dumps(apply_plan(self.project, plan)[0]), dumps(result))
        for mutation in (lambda p:p.update(command="exec"), lambda p:p["steps"][1]["scope"].update(start=0),
                         lambda p:p["steps"][0]["operations"][0].update(value=10000),
                         lambda p:p["steps"][0]["scope"].update(start=False),
                         lambda p:p["comparison"].update(unchanged_equal=1)):
            bad = deepcopy(plan); mutation(bad)
            with self.assertRaises(ValidationError): apply_plan(self.project, bad)

    def test_corrupt_receipt_chain_versions_hashes_order_and_locks_fail(self):
        _, result, receipt = self.prepare()
        for mutation in (lambda r:r.update(version="99"), lambda r:r.update(before_hash="f"*64),
                         lambda r:r["receipts"].reverse(), lambda r:r.update(extra="x"), lambda r:r.update(receipts=[])):
            bad = deepcopy(receipt); mutation(bad)
            with self.assertRaises(ValidationError): replay_revision(result, bad, undo=True)
        result.locks.append(Lock("post-revision-lock", "track-bass", None))
        with self.assertRaises(ValidationError): replay_revision(result, receipt, undo=True)

    def test_comparison_detects_collateral_even_on_an_edited_track(self):
        plan, result, _ = self.prepare()
        for mutation in (lambda p:p.metadata.update(unknown="discarded"), lambda p:setattr(p, "key_tonic", 0),
                         lambda p:p.tracks[3].controls.update({"mixer.pan": 0.5}),
                         lambda p:setattr(p.tracks[0].clips[0].notes[0], "velocity", 1)):
            bad = deepcopy(result); mutation(bad)
            with self.assertRaisesRegex(ValidationError, "outside"):
                comparison(self.project, bad, plan["steps"])

    def test_units_and_final_gain_ranges_remain_strict(self):
        p = deepcopy(self.project)
        next(x for x in p.parameters if x.id == "synth.cutoff_hz").unit = "ms"
        with self.assertRaisesRegex(ValidationError, "unit/range"):
            self.prepare("make bass aggressive", p)
        p = deepcopy(self.project); p.tracks[-1].controls["mixer.gain_db"] = 11
        with self.assertRaisesRegex(ValidationError, "unit/range"):
            self.prepare("turn the lead up by 3 dB", p)

    def test_old_generator_verse_and_soundcraft_profile_are_compatible(self):
        old = generate()
        plan, result, _ = self.prepare("simplify the drums in the verse", old)
        self.assertGreater(len(plan["comparison"]["removed_notes"]), 0)
        self.assertEqual(result.metadata, old.metadata)
        with self.assertRaisesRegex(ValidationError, "explicit existing"):
            self.prepare("make bass aggressive", old)
        sc = load(Path(__file__).resolve().parents[1]/"examples/soundcraft-demo.kuang.json")
        self.prepare("make bass aggressive", sc)

    def test_ambient_and_already_thin_drums_fail_precisely(self):
        ambient = compose(rules_plan(PROMPTS[2])[0])
        _, revised, _ = self.prepare("make bass aggressive and make the harmony reverb wetter", ambient)
        self.assertEqual(revised.metadata, ambient.metadata)
        with self.assertRaisesRegex(ValidationError, "no matching track"):
            self.prepare("simplify drums in Expansion", ambient)
        _, thin, _ = self.prepare("simplify drums in Main")
        with self.assertRaisesRegex(ValidationError, "no change"):
            self.prepare("simplify drums in Main", thin)

    def test_ambiguous_track_and_section_are_not_guessed(self):
        p = deepcopy(self.project)
        p.tracks[3].id = "human-bass"; p.tracks[-1].name = "Second bass"
        with self.assertRaisesRegex(ValidationError, "ambiguous track"):
            resolve_tracks(p, "bass")
        p = deepcopy(self.project); p.sections[-1].name = "Main"
        with self.assertRaisesRegex(ValidationError, "ambiguous section"):
            resolve_region(p, "Main")
