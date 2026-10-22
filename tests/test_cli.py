import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from kuang.cli import main
from kuang.schema import load, state_hash


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main([str(x) for x in args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_complete_cli_generation_proposal_edit_receipt_undo_redo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, stdout, stderr = self.invoke("demo", "--out-dir", root, "--seed", 7)
            self.assertEqual((code, stderr), (0, ""))
            self.assertIn("no audio rendered", stdout)
            session = root / "demo.kuang.json"
            original = session.read_bytes()
            self.assertEqual(self.invoke("validate", session)[0], 0)
            self.assertEqual(self.invoke("propose", session, root/"request.json", "--track", "track-arp", "--clip", "clip-arp-hook-a")[0], 0)
            self.assertEqual(session.read_bytes(), original)
            self.assertEqual(self.invoke("apply", session, root/"request.json", root/"edited.json", "--receipt", root/"receipt.json")[0], 0)
            self.assertNotEqual((root/"edited.json").read_bytes(), original)
            receipt = json.loads((root/"receipt.json").read_text())
            self.assertEqual(receipt["before_hash"], state_hash(load(session)))
            self.assertEqual(self.invoke("undo", root/"edited.json", root/"receipt.json", root/"restored.json")[0], 0)
            self.assertEqual((root/"restored.json").read_bytes(), original)
            self.assertEqual(self.invoke("redo", root/"restored.json", root/"receipt.json", root/"redone.json")[0], 0)
            self.assertEqual((root/"redone.json").read_bytes(), (root/"edited.json").read_bytes())
            self.assertEqual(self.invoke("midi", root/"edited.json", root/"edited.mid")[0], 0)
            self.assertEqual(self.invoke("reaper", root/"edited.json", root/"edited.lua", "--plan", root/"edited.plan.json")[0], 0)

    def test_invalid_request_writes_neither_session_nor_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.invoke("demo", "--out-dir", root)[0], 0)
            session = root/"demo.kuang.json"
            request = {"expected_before_hash": state_hash(load(session)),
                       "scope": {"track_ids": ["track-kick"], "clip_ids": [], "parameter_ids": ["mixer.pan"], "start": None, "end": None},
                       "operations": [{"op": "set_parameter", "target_id": "track-kick", "parameter_id": "mixer.pan", "value": 0.2},
                                      {"op": "set_parameter", "target_id": "track-kick", "parameter_id": "mixer.pan", "value": 2}]}
            (root/"request.json").write_text(json.dumps(request))
            code, _, stderr = self.invoke("apply", session, root/"request.json", root/"edited.json", "--receipt", root/"receipt.json")
            self.assertEqual(code, 2)
            self.assertIn("range", stderr)
            self.assertFalse((root/"edited.json").exists())
            self.assertFalse((root/"receipt.json").exists())

    def test_existing_outputs_protected_and_explicit_force_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.invoke("demo", "--out-dir", root)[0], 0)
            original = (root/"demo.kuang.json").read_bytes()
            code, _, stderr = self.invoke("demo", "--out-dir", root, "--seed", 8)
            self.assertEqual(code, 2)
            self.assertIn("already exists", stderr)
            self.assertEqual((root/"demo.kuang.json").read_bytes(), original)
            self.assertEqual(self.invoke("demo", "--out-dir", root, "--seed", 8, "--force")[0], 0)
            self.assertNotEqual((root/"demo.kuang.json").read_bytes(), original)

    def test_malformed_json_unknown_operation_and_scope_bounds_fail_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root/"bad.json"
            bad.write_text('{"version":NaN}')
            self.assertEqual(self.invoke("validate", bad)[0], 2)
            self.assertEqual(self.invoke("demo", "--out-dir", root)[0], 0)
            self.assertEqual(self.invoke("propose", root/"demo.kuang.json", root/"request.json", "--track", "track-arp",
                                         "--clip", "clip-arp-hook-a", "--start", 0)[0], 2)

    def test_duplicate_output_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.invoke("demo", "--out-dir", root)[0], 0)
            code, _, stderr = self.invoke("reaper", root/"demo.kuang.json", root/"same", "--plan", root/"same")
            self.assertEqual(code, 2)
            self.assertIn("distinct", stderr)

    def test_derived_outputs_cannot_clobber_source_even_with_force(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.invoke("demo", "--out-dir", root)[0], 0)
            source = root/"demo.kuang.json"
            original = source.read_bytes()
            self.assertEqual(self.invoke("midi", source, source, "--force")[0], 2)
            self.assertEqual(self.invoke("apply", source, root/"absent-request.json", root/"edited.json",
                                         "--receipt", source, "--force")[0], 2)
            self.assertEqual(source.read_bytes(), original)
