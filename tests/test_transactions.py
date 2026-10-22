import unittest
from copy import deepcopy
from dataclasses import asdict, replace

from kuang.engines import SeededVelocityEngine
from kuang.generator import generate
from kuang.schema import (BAR, PPQ, AutomationPoint, Lock, Note, ValidationError, dumps, state_hash)
from kuang.transactions import (AddAutomationPoints, AddNotes, DeleteAutomationPoints, Engine,
                                LockedError, RemoveNotes, ReplaceNotesInRegion, Scope, ScopeError,
                                SetParameter, UpdateNote, parse_operations, receipt_from_dict, replay)
from helpers import full_scope, small_project


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.p = small_project()
        self.scope = full_scope(self.p)
        self.clip = self.p.tracks[0].clips[0]
        self.engine = Engine(self.p)

    def test_parameter_edit_preserves_every_untouched_field(self):
        expected = deepcopy(self.p)
        expected.tracks[0].controls["mixer.pan"] = -0.3
        receipt = self.engine.apply([SetParameter("set_parameter", "track-kick", "mixer.pan", -0.3)], self.scope)
        self.assertEqual(dumps(self.engine.project), dumps(expected))
        self.assertEqual(receipt.before_hash, state_hash(self.p))
        self.assertEqual(receipt.after_hash, state_hash(expected))
        self.assertEqual(receipt.inverse[0].value, 0)

    def test_atomic_rollback_when_later_operation_is_invalid(self):
        operations = [SetParameter("set_parameter", "track-kick", "mixer.pan", -0.2),
                      SetParameter("set_parameter", "track-snare", "mixer.gain_db", 400)]
        with self.assertRaises(ValidationError):
            self.engine.apply(operations, self.scope)
        self.assertEqual(dumps(self.engine.project), dumps(self.p))
        with self.assertRaisesRegex(ValidationError, "nothing to undo"):
            self.engine.undo()

    def test_add_update_remove_notes_and_exact_undo_redo(self):
        original = dumps(self.p)
        added = Note("new-note", 480, 120, 40, 78, 9)
        self.engine.apply([AddNotes("add_notes", self.clip.id, [added])], self.scope)
        updated = replace(self.clip.notes[1], pitch=37, velocity=82, start=1000)
        self.engine.apply([UpdateNote("update_note", self.clip.id, updated)], self.scope)
        self.engine.apply([RemoveNotes("remove_notes", self.clip.id, ["test-note-a"])], self.scope)
        final = dumps(self.engine.project)
        for _ in range(3): self.engine.undo()
        self.assertEqual(dumps(self.engine.project), original)
        for _ in range(3): self.engine.redo()
        self.assertEqual(dumps(self.engine.project), final)

    def test_replace_region_preserves_survivors_and_inverse_order(self):
        replacement = Note("region-note", 970, 100, 44, 77, 9)
        receipt = self.engine.apply([ReplaceNotesInRegion("replace_notes_in_region", self.clip.id, 960, 1440, [replacement])], self.scope)
        notes = self.engine.project.tracks[0].clips[0].notes
        self.assertEqual(notes, [self.clip.notes[0], self.clip.notes[2], replacement])
        restored = replay(self.engine.project, receipt_from_dict(asdict(receipt)), undo=True)
        self.assertEqual(dumps(restored), dumps(self.p))

    def test_region_refuses_cutting_boundary_notes_or_outside_inserts(self):
        operations = [ReplaceNotesInRegion("replace_notes_in_region", self.clip.id, 100, 200, []),
                      ReplaceNotesInRegion("replace_notes_in_region", self.clip.id, 480, 960,
                                           [Note("out", 950, 20, 40, 80, 9)])]
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValidationError):
                self.engine.apply([operation], self.scope)
            self.assertEqual(dumps(self.engine.project), dumps(self.p))

    def test_invalid_notes_duplicate_ids_and_missing_objects_rollback(self):
        operations = [AddNotes("add_notes", self.clip.id, [deepcopy(self.clip.notes[0])]),
                      AddNotes("add_notes", self.clip.id, [Note("overlap", 10, 20, 36, 80, 9)]),
                      UpdateNote("update_note", self.clip.id, replace(self.clip.notes[0], id="absent")),
                      RemoveNotes("remove_notes", self.clip.id, ["absent"]),
                      RemoveNotes("remove_notes", self.clip.id, ["test-note-a", "test-note-a"]),
                      AddNotes("add_notes", "absent-clip", []),
                      SetParameter("set_parameter", "track-kick", "absent", 1)]
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValidationError):
                self.engine.apply([operation], self.scope)
            self.assertEqual(dumps(self.engine.project), dumps(self.p))

    def test_track_clip_and_parameter_locks(self):
        cases = [(Lock("lock-a", "track-kick", None), UpdateNote("update_note", self.clip.id, replace(self.clip.notes[0], velocity=75))),
                 (Lock("lock-a", self.clip.id, None), AddNotes("add_notes", self.clip.id, [])),
                 (Lock("lock-a", "track-kick", "mixer.pan"), SetParameter("set_parameter", "track-kick", "mixer.pan", 0.2)),
                 (Lock("lock-a", "track-kick", "mixer.pan"), DeleteAutomationPoints("delete_automation_points", "test-lane", ["test-point-a"]))]
        for lock, operation in cases:
            p = deepcopy(self.p)
            p.locks = [lock]
            engine = Engine(p)
            with self.subTest(lock=lock), self.assertRaises(LockedError):
                engine.apply([operation], self.scope)
            self.assertEqual(dumps(engine.project), dumps(p))
        p = deepcopy(self.p)
        p.locks = [Lock("lock-a", "track-kick", "mixer.pan")]
        Engine(p).apply([SetParameter("set_parameter", "track-kick", "mixer.gain_db", -10)], self.scope)

    def test_child_instrument_and_effect_locks(self):
        p = generate()
        p.locks = [Lock("lock-effect", "effect-pad-reverb", "effect.wet")]
        with self.assertRaises(LockedError):
            Engine(p).apply([SetParameter("set_parameter", "effect-pad-reverb", "effect.wet", 0.5)], full_scope(p))
        p.locks = [Lock("lock-instrument", "instrument-chords", "synth.cutoff_hz")]
        p.tracks[4].instrument.parameters["synth.cutoff_hz"] = 1800
        with self.assertRaises(LockedError):
            Engine(p).apply([SetParameter("set_parameter", "instrument-chords", "synth.cutoff_hz", 2400)], full_scope(p))
        p.locks = [Lock("lock-track", "track-pad", None)]
        with self.assertRaises(LockedError):
            Engine(p).apply([SetParameter("set_parameter", "effect-pad-reverb", "effect.wet", 0.5)], full_scope(p))

    def test_scope_track_clip_parameter_and_unknown_ids(self):
        cases = [(Scope(["track-snare"], [], ["mixer.pan"], None, None),
                  SetParameter("set_parameter", "track-kick", "mixer.pan", 0.2)),
                 (Scope(["track-kick"], [], [], None, None), RemoveNotes("remove_notes", self.clip.id, ["test-note-a"])),
                 (Scope(["track-kick"], [], [], None, None), SetParameter("set_parameter", "track-kick", "mixer.pan", 0.2)),
                 (Scope(["absent"], [], [], None, None), AddNotes("add_notes", self.clip.id, [])),
                 (Scope(["track-kick"], [], [], 0, None), AddNotes("add_notes", self.clip.id, [])),
                 (Scope(["track-snare"], [self.clip.id], [], None, None), AddNotes("add_notes", self.clip.id, []))]
        for scope, operation in cases:
            with self.subTest(scope=scope), self.assertRaises(ScopeError):
                self.engine.apply([operation], scope)

    def test_time_scope_checks_both_old_and_new_note_extent(self):
        scope = Scope(["track-kick"], [self.clip.id], [], 0, 300)
        self.engine.apply([UpdateNote("update_note", self.clip.id, replace(self.clip.notes[0], velocity=70))], scope)
        for note in [replace(self.clip.notes[0], start=250), replace(self.clip.notes[1], start=10)]:
            with self.assertRaises(ScopeError):
                self.engine.apply([UpdateNote("update_note", self.clip.id, note)], scope)
        with self.assertRaises(ScopeError):
            self.engine.apply([SetParameter("set_parameter", "track-kick", "mixer.pan", 0)],
                              Scope(["track-kick"], [], ["mixer.pan"], 0, 300))

    def test_noop_note_update_still_requires_time_scope(self):
        with self.assertRaises(ScopeError):
            self.engine.apply([UpdateNote("update_note", self.clip.id, deepcopy(self.clip.notes[1]))],
                              Scope(["track-kick"], [self.clip.id], [], 0, 300))

    def test_nonzero_clip_position_uses_absolute_scope_ticks(self):
        clip = self.p.tracks[1].clips[0]
        note = clip.notes[0]
        scope = Scope(["track-snare"], [clip.id], [], clip.start+note.start, clip.start+note.start+note.duration)
        self.engine.apply([UpdateNote("update_note", clip.id, replace(note, velocity=67))], scope)
        with self.assertRaises(ScopeError):
            Engine(self.p).apply([UpdateNote("update_note", clip.id, replace(note, velocity=67))],
                                 replace(scope, start=note.start, end=note.start+note.duration))

    def test_automation_add_delete_and_undo(self):
        point = AutomationPoint("new-point", 480, -0.2, "step")
        self.engine.apply([AddAutomationPoints("add_automation_points", "test-lane", [point])], self.scope)
        self.engine.apply([DeleteAutomationPoints("delete_automation_points", "test-lane", ["test-point-a"])], self.scope)
        self.engine.undo()
        self.engine.undo()
        self.assertEqual(dumps(self.engine.project), dumps(self.p))
        for operation in [AddAutomationPoints("add_automation_points", "test-lane", [replace(point, tick=0)]),
                          AddAutomationPoints("add_automation_points", "test-lane", [replace(point, value=2)]),
                          DeleteAutomationPoints("delete_automation_points", "test-lane", ["absent"])]:
            with self.assertRaises(ValidationError): self.engine.apply([operation], self.scope)
        with self.assertRaises(ScopeError):
            self.engine.apply([DeleteAutomationPoints("delete_automation_points", "test-lane", ["test-point-b"])],
                              Scope(["track-kick"], [], ["mixer.pan"], 0, 1000))

    def test_stale_hash_and_tampered_receipts_rejected(self):
        op = SetParameter("set_parameter", "track-kick", "mixer.pan", 0.2)
        with self.assertRaisesRegex(ValidationError, "stale"):
            self.engine.apply([op], self.scope, "0" * 64)
        receipt = self.engine.apply([op], self.scope, state_hash(self.p))
        tampered = deepcopy(receipt)
        tampered.inverse[0].value = 0.1
        with self.assertRaisesRegex(ValidationError, "expected state"):
            replay(self.engine.project, tampered, undo=True)
        with self.assertRaisesRegex(ValidationError, "stale"):
            replay(self.p, receipt, undo=True)

    def test_defensive_copies_and_new_edit_discards_redo(self):
        p = self.engine.project
        p.tracks.clear()
        self.assertEqual(dumps(self.engine.project), dumps(self.p))
        receipt = self.engine.apply([SetParameter("set_parameter", "track-kick", "mixer.pan", 0.3)], self.scope)
        receipt.inverse.clear()
        self.engine.undo()
        self.assertEqual(dumps(self.engine.project), dumps(self.p))
        self.engine.apply([SetParameter("set_parameter", "track-kick", "mixer.pan", -0.2)], self.scope)
        with self.assertRaisesRegex(ValidationError, "nothing to redo"): self.engine.redo()

    def test_operation_parser_rejects_unknown_and_inverse_operations(self):
        for value in [[{"op": "run_shell", "command": "anything"}], [{"op": "restore_notes", "clip_id": self.clip.id, "notes": []}],
                      [{"op": "set_parameter", "target_id": "track-kick", "parameter_id": "mixer.pan", "value": True}],
                      [{"op": "set_parameter", "target_id": "track-kick", "parameter_id": "mixer.pan", "value": 0, "extra": 1}]]:
            with self.assertRaises(ValidationError): parse_operations(value)

    def test_twenty_successive_edits_without_collateral_changes_and_full_history(self):
        original = generate(7)
        expected, engine = deepcopy(original), Engine(original)
        scope = full_scope(original)
        clip = next(c for c in expected.tracks[6].clips if c.id == "clip-arp-hook-a")
        for i in range(20):
            group = i // 4
            if i % 4 == 0:
                expected.tracks[3].controls["mixer.gain_db"] = -12 + (group+1) / 10
                op = SetParameter("set_parameter", "track-bass", "mixer.gain_db", -12 + (group+1) / 10)
            elif i % 4 == 1:
                clip.notes[group].velocity += 1
                op = UpdateNote("update_note", clip.id, deepcopy(clip.notes[group]))
            elif i % 4 == 2:
                point = AutomationPoint(f"regression-point-{group}", (group+1)*BAR + PPQ//4, -23, "linear")
                expected.automation[0].points.append(deepcopy(point))
                op = AddAutomationPoints("add_automation_points", "automation-pad-gain", [point])
            else:
                expected.automation[0].points.pop()
                op = DeleteAutomationPoints("delete_automation_points", "automation-pad-gain", [f"regression-point-{group}"])
            before = state_hash(engine.project)
            receipt = engine.apply([op], scope, before)
            self.assertEqual(dumps(engine.project), dumps(expected), f"collateral edit at step {i+1}")
            self.assertEqual(receipt.before_hash, before)
            self.assertNotEqual(receipt.before_hash, receipt.after_hash)
        final = dumps(expected)
        for _ in range(20): engine.undo()
        self.assertEqual(dumps(engine.project), dumps(original))
        for _ in range(20): engine.redo()
        self.assertEqual(dumps(engine.project), final)

    def test_pluggable_seeded_engine_proposes_only_scoped_typed_notes(self):
        scope = Scope(["track-kick"], [self.clip.id], [], 0, 1500)
        model = SeededVelocityEngine()
        a, b = model.propose(self.p, scope, seed=8), model.propose(self.p, scope, seed=8)
        self.assertEqual(a.to_dict(), b.to_dict())
        self.assertEqual(len(a.operations), 2)
        self.assertEqual(dumps(self.p), dumps(self.engine.project))
        self.engine.apply(a.operations, a.scope, a.expected_before_hash)
        self.p.locks = [Lock("lock-a", self.clip.id, None)]
        with self.assertRaises(LockedError): model.propose(self.p, scope, seed=8)
