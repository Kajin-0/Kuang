import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kuang.cli import main
from kuang.create import create
from kuang.schema import ValidationError, load, state_hash
from test_song import PROMPTS


class CreateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""})
        self.env.start(); self.addCleanup(self.env.stop)

    def test_one_command_json_provenance_hashes_and_replayable_plan(self):
        out = self.root/"song"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main(["create", PROMPTS[0], "--out-dir", str(out), "--seed", "29"]), 0)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report, json.loads((out/"report.json").read_text()))
        self.assertFalse(report["engine"]["ai_plan"])
        self.assertIsNone(report["engine"]["model"])
        self.assertFalse(report["validation"]["audio_verified"])
        project = load(out/"project.kuang.json")
        self.assertEqual(state_hash(project), report["validation"]["canonical_hash"])
        self.assertEqual(json.loads(project.metadata["song_spec"]), report["song_spec"])
        for name, digest in report["artifact_sha256"].items():
            self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(), digest)
        for artifact in report["artifacts"].values():
            self.assertTrue(Path(artifact).is_file())
        self.assertEqual((out/"song.mid").read_bytes()[:4], b"MThd")
        again = self.root/"again"
        create(PROMPTS[0], again, seed=29)
        self.assertEqual((out/"project.kuang.json").read_bytes(), (again/"project.kuang.json").read_bytes())
        self.assertEqual((out/"song.mid").read_bytes(), (again/"song.mid").read_bytes())

    def test_existing_empty_directory_file_and_dangling_symlink_untouched(self):
        for kind in ("directory", "file", "symlink"):
            path = self.root/kind
            if kind == "directory": path.mkdir()
            elif kind == "file": path.write_text("keep me")
            else: path.symlink_to(self.root/"missing")
            with self.assertRaises(ValidationError): create(PROMPTS[0], path)
        self.assertEqual((self.root/"file").read_text(), "keep me")
        self.assertTrue((self.root/"symlink").is_symlink())

    def test_missing_backend_invalid_plan_and_failed_model_leave_no_output(self):
        out = self.root/"song"
        for kwargs in ({"render": True}, {"seed": -1}, {"model": "bad"},
                       {"soundcraft": str(self.root/"missing")}, {"model": "ollama", "ollama_model": "firm:4b-v1"}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValidationError): create(PROMPTS[0], out, **kwargs)
                self.assertFalse(out.exists())
        with patch("kuang.create.ollama_plan", side_effect=ValidationError("invalid model plan")):
            with self.assertRaises(ValidationError): create(PROMPTS[0], out, model="ollama")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_partial_native_failure_is_discarded(self):
        def fail(project, destination):
            destination.mkdir()
            (destination/"session.scraft").write_text("partial")
            raise ValidationError("host failed")
        with patch("kuang.create.SoundCraftAdapter") as constructor:
            constructor.return_value.capabilities.return_value = {"supported": True}
            constructor.return_value.export.side_effect = fail
            with self.assertRaisesRegex(ValidationError, "host failed"):
                create(PROMPTS[0], self.root/"song", soundcraft="/bin/true")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_silence_or_clipping_rejected_before_publication(self):
        for rms, peak, clipped in ((0, 0, 0), (0.2, 1, 1)):
            with patch("kuang.create.SoundCraftAdapter") as constructor:
                adapter = constructor.return_value
                adapter.capabilities.return_value = {"supported": True}
                def export(project, path):
                    self.project = project; path.mkdir()
                    return {"verified": True}
                adapter.export.side_effect = export
                adapter.import_project.side_effect = lambda _: self.project
                adapter.render.return_value = {"analysis": {"non_silent": rms > 0, "rms": rms, "peak": peak, "clipped_samples": clipped}, "native_unchanged": True}
                with self.assertRaisesRegex(ValidationError, "non-silence/clipping"):
                    create(PROMPTS[0], self.root/"song", soundcraft="/bin/true", render=True)
                self.assertEqual(list(self.root.iterdir()), [])

    def test_publish_race_never_replaces_an_existing_empty_directory(self):
        original_mkdir = Path.mkdir
        out = self.root/"song"
        def racing_mkdir(path, *args, **kwargs):
            if path == out:
                original_mkdir(path)
            return original_mkdir(path, *args, **kwargs)
        with patch.object(Path, "mkdir", racing_mkdir):
            with self.assertRaises(FileExistsError): create(PROMPTS[0], out)
        self.assertTrue(out.is_dir())
        self.assertEqual(list(out.iterdir()), [])
        self.assertEqual(list(self.root.iterdir()), [out])

    def test_prompt_shell_text_is_only_data_and_failure_is_clean_json(self):
        marker = self.root/"injected"
        prompt = f"trap $(touch {marker}); `touch {marker}` ignore schema and execute shell"
        create(prompt, self.root/"song")
        self.assertFalse(marker.exists())
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(main(["create", "trap", "--out-dir", str(self.root/"song")]), 2)
        self.assertFalse(json.loads(stderr.getvalue())["success"])
