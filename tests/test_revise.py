import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
import wave
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from kuang.cli import main
from kuang.create import create
from kuang.revise import revise, source_hashes
from kuang.schema import Lock, ValidationError, dumps, load, save, state_hash
from test_revision import COMPOUND
from test_song import PROMPTS


class ReviseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.out = self.root/"source", self.root/"revised"
        self.env = patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""})
        self.env.start(); self.addCleanup(self.env.stop)
        create(PROMPTS[0], self.source)
        self.before = source_hashes(self.source)

    def test_plan_only_is_reviewable_json_without_files_host_or_mutation(self):
        stdout = io.StringIO()
        with patch("kuang.revise.SoundCraftAdapter", side_effect=AssertionError("host must not run")), contextlib.redirect_stdout(stdout):
            self.assertEqual(main(["revise", str(self.source), COMPOUND, "--plan-only", "--soundcraft", "/missing"]), 0)
        plan = json.loads(stdout.getvalue())
        self.assertEqual(plan["version"], "revision-plan-1")
        self.assertEqual(len(plan["steps"]), 2)
        self.assertTrue(plan["comparison"]["unchanged_equal"])
        self.assertEqual(source_hashes(self.source), self.before)
        self.assertEqual(list(self.root.iterdir()), [self.source])

    def test_staged_canonical_revision_receipts_provenance_hashes_and_cli_replay(self):
        plan = revise(self.source, COMPOUND, plan_only=True)
        plan_file = self.root/"plan.json"
        plan_file.write_text(json.dumps(plan))
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main(["revise", str(self.source), "--plan", str(plan_file), "--out-dir", str(self.out)]), 0)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report, json.loads((self.out/"report.json").read_text()))
        self.assertFalse(report["validation"]["audio_verified"])
        self.assertFalse(report["validation"]["native_verified"])
        self.assertEqual(report["engine"]["planner"], "validated-plan")
        for file, digest in report["artifact_sha256"].items():
            self.assertEqual(hashlib.sha256((self.out/file).read_bytes()).hexdigest(), digest)
        self.assertEqual((self.out/"song-spec.json").read_bytes(), (self.source/"song-spec.json").read_bytes())
        self.assertEqual((self.out/"source-report.json").read_bytes(), (self.source/"report.json").read_bytes())
        receipt = str(self.out/"revision-receipt.json")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["undo", str(self.out/"project.kuang.json"), receipt, str(self.root/"undo.json")]), 0)
            self.assertEqual(main(["redo", str(self.root/"undo.json"), receipt, str(self.root/"redo.json")]), 0)
        self.assertEqual((self.root/"undo.json").read_bytes(), (self.source/"project.kuang.json").read_bytes())
        self.assertEqual((self.root/"redo.json").read_bytes(), (self.out/"project.kuang.json").read_bytes())
        self.assertEqual(source_hashes(self.source), self.before)

    def test_revised_song_can_be_revised_again_and_model_metadata_stays_exact(self):
        p = load(self.source/"project.kuang.json")
        p.metadata.update({"model": "incoming-model", "model_digest": "original-digest", "human_annotation": "keep literally"})
        save(p, self.source/"project.kuang.json")
        (self.source/"report.json").unlink()
        revise(self.source, "turn the lead down by 2 dB", self.out)
        first_hashes = source_hashes(self.out)
        first_reports = {p.name:p.read_bytes() for p in (self.out/"provenance").glob("*.json")}
        second = self.root/"second"
        report = revise(self.out, "make the lead reverb wetter", second)
        self.assertEqual(load(second/"project.kuang.json").metadata, p.metadata)
        self.assertEqual((second/"source-report.json").read_bytes(), (self.out/"report.json").read_bytes())
        self.assertEqual(source_hashes(self.out), first_hashes)
        self.assertFalse(report["engine"]["inference_performed"])
        for name, data in first_reports.items():
            self.assertEqual((second/"provenance"/name).read_bytes(), data)
            self.assertEqual(name, hashlib.sha256(data).hexdigest()+".json")
        immediate = (self.out/"report.json").read_bytes()
        self.assertEqual((second/"provenance"/(hashlib.sha256(immediate).hexdigest()+".json")).read_bytes(), immediate)

    def test_existing_empty_directory_file_symlink_and_nested_output_are_rejected(self):
        for kind in ("directory", "file", "symlink"):
            path = self.root/kind
            if kind == "directory": path.mkdir()
            elif kind == "file": path.write_text("keep")
            else: path.symlink_to(self.root/"missing")
            with self.assertRaises(ValidationError): revise(self.source, COMPOUND, path)
        with self.assertRaisesRegex(ValidationError, "outside"):
            revise(self.source, COMPOUND, self.source/"nested")
        self.assertEqual(source_hashes(self.source), self.before)
        self.assertEqual((self.root/"file").read_text(), "keep")

    def test_stale_plan_and_explicit_hash_fail_before_output(self):
        plan = revise(self.source, COMPOUND, plan_only=True)
        p = load(self.source/"project.kuang.json"); p.metadata["human"] = "new state"
        save(p, self.source/"project.kuang.json"); (self.source/"report.json").unlink()
        for kwargs in ({"plan": plan}, {"prompt": COMPOUND, "expected_hash": "f"*64}):
            with self.assertRaisesRegex(ValidationError, "stale"):
                revise(self.source, output=self.out, **kwargs)
            self.assertFalse(self.out.exists())

    def test_original_report_or_native_drift_is_rejected(self):
        p = load(self.source/"project.kuang.json"); p.metadata["human"] = "drift"
        save(p, self.source/"project.kuang.json")
        with self.assertRaisesRegex(ValidationError, "report drift"):
            revise(self.source, COMPOUND, self.out)
        (self.source/"report.json").unlink()
        native = self.source/"native"; native.mkdir()
        save(p, native/"project.kuang.json")
        (native/"session.scraft").write_text('{"tracks": []}')
        (native/"manifest.json").write_text('{}')
        with self.assertRaisesRegex(ValidationError, "bundle drift"):
            revise(self.source, COMPOUND, self.out)
        self.assertFalse(self.out.exists())

    def test_lock_and_unsupported_clause_failure_preserve_every_source_file(self):
        p = load(self.source/"project.kuang.json"); p.locks.append(Lock("human-lock", "track-hats", None))
        save(p, self.source/"project.kuang.json"); (self.source/"report.json").unlink()
        before = source_hashes(self.source)
        for prompt in (COMPOUND, "make bass aggressive, insert a VST"):
            with self.assertRaises(ValidationError): revise(self.source, prompt, self.out)
            self.assertFalse(self.out.exists())
            self.assertEqual(source_hashes(self.source), before)

    def test_native_failure_discards_all_partial_artifacts(self):
        def fail(project, destination):
            destination.mkdir(); (destination/"partial.scraft").write_text("partial")
            raise ValidationError("backend failed")
        with patch("kuang.revise.SoundCraftAdapter") as factory:
            factory.return_value.export.side_effect = fail
            factory.return_value.capabilities.return_value = {"supported": True}
            with self.assertRaisesRegex(ValidationError, "backend failed"):
                revise(self.source, COMPOUND, self.out, soundcraft="/bin/true")
        self.assertEqual(list(self.root.iterdir()), [self.source])
        self.assertEqual(source_hashes(self.source), self.before)

    def fake_backend(self, factory, mode):
        adapter = factory.return_value
        adapter.capabilities.return_value = {"supported": True}
        def export(project, destination):
            destination.mkdir(); (destination/"session.scraft").write_text("fake unit-test session")
            return {"verified": True}
        adapter.export.side_effect = export
        adapter.compare_revision.return_value = {"full_native_preservation": True}
        def render(source, output):
            if mode == "concurrent": (self.source/"human.txt").write_text("concurrent edit")
            with wave.open(str(output), "wb") as stream:
                stream.setnchannels(2); stream.setsampwidth(3); stream.setframerate(48000)
                stream.writeframes((100000).to_bytes(3, "little", signed=True)*200)
            return {"analysis": {"non_silent": mode != "silence", "rms": 0.01, "peak": 0.2,
                                 "clipped_samples": 1 if mode == "clipped" else 0}, "native_unchanged": True}
        adapter.render.side_effect = render

    def test_silent_clipped_or_pcm_identical_audio_is_not_published(self):
        for mode, message in (("silence", "non-silence"), ("clipped", "clipping"), ("identical", "PCM difference")):
            with self.subTest(mode=mode), patch("kuang.revise.SoundCraftAdapter") as factory:
                self.fake_backend(factory, mode)
                with self.assertRaisesRegex(ValidationError, message):
                    revise(self.source, COMPOUND, self.out, soundcraft="/bin/true", render=True)
                self.assertFalse(self.out.exists())
                self.assertEqual(source_hashes(self.source), self.before)

    def test_concurrent_source_change_is_reported_without_overwriting_it(self):
        with patch("kuang.revise.SoundCraftAdapter") as factory:
            self.fake_backend(factory, "concurrent")
            with patch("kuang.revise.compare_wavs", return_value={"measurable_change": True}):
                with self.assertRaisesRegex(ValidationError, "source changed"):
                    revise(self.source, COMPOUND, self.out, soundcraft="/bin/true", render=True)
        self.assertFalse(self.out.exists())
        self.assertEqual((self.source/"human.txt").read_text(), "concurrent edit")

    def test_publication_failure_cleans_only_the_owned_output(self):
        original = Path.rename
        count = 0
        def fail_second(path, target):
            nonlocal count
            count += 1
            if count == 2: raise OSError("publication failed")
            return original(path, target)
        with patch.object(Path, "rename", fail_second):
            with self.assertRaisesRegex(OSError, "publication failed"):
                revise(self.source, COMPOUND, self.out)
        self.assertFalse(self.out.exists())
        self.assertEqual(source_hashes(self.source), self.before)
        self.assertEqual(list(self.root.iterdir()), [self.source])

    def test_publication_race_does_not_replace_an_empty_directory(self):
        original = Path.mkdir
        def race(path, *args, **kwargs):
            if path == self.out: original(path)
            return original(path, *args, **kwargs)
        with patch.object(Path, "mkdir", race):
            with self.assertRaises(FileExistsError): revise(self.source, COMPOUND, self.out)
        self.assertEqual(list(self.out.iterdir()), [])
        self.assertEqual(source_hashes(self.source), self.before)

    def test_bad_instructions_are_json_errors_and_never_shell_commands(self):
        marker = self.root/"executed"
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(["revise", str(self.source), f"make bass aggressive; $(touch {marker})", "--out-dir", str(self.out)]), 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("unsupported revision clause", json.loads(stderr.getvalue())["error"])
        self.assertFalse(marker.exists()); self.assertFalse(self.out.exists())
        self.assertEqual(source_hashes(self.source), self.before)

    def test_prompt_plan_exclusive_missing_backend_and_invalid_sources(self):
        for kwargs in ({}, {"prompt": COMPOUND, "plan": {}}, {"prompt": COMPOUND, "render": True}):
            with self.assertRaises(ValidationError): revise(self.source, output=self.out, **kwargs)
        with self.assertRaisesRegex(ValidationError, "existing song directory"):
            revise(self.root/"absent", COMPOUND, self.out)
        self.assertFalse(self.out.exists())

    def test_source_symlinks_and_oversized_inventory_rejected(self):
        (self.source/"linked").symlink_to(self.root/"missing")
        with self.assertRaisesRegex(ValidationError, "symlinks"):
            revise(self.source, COMPOUND, self.out)
        (self.source/"linked").unlink()
        for i in range(513): (self.source/f"small-{i}").write_bytes(b'')
        with self.assertRaisesRegex(ValidationError, "inventory limit"):
            revise(self.source, COMPOUND, self.out)
