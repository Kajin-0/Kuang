import contextlib
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
import wave
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from kuang.adapters import DAWAdapter
from kuang.audio import analyze_wav
from kuang.cli import main
from kuang.schema import AutomationLane, AutomationPoint, Lock, ParameterSpec, ValidationError, dumps, state_hash
from kuang.soundcraft import AdapterError, SoundCraftAdapter, UnsupportedError, _hash
from kuang.transactions import (AddAutomationPoints, DeleteAutomationPoints, Engine, LockedError,
                                Scope, ScopeError, SetParameter, UpdateNote)
from helpers import small_project, full_scope
from soundcraft_fake import CONTRACT, NATIVE, FakeCLI


class SoundCraftTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.binary = self.root / "soundcraft-cli"
        self.binary.write_text("test executable placeholder")
        self.binary.chmod(0o700)
        self.fake = FakeCLI()
        self.mock = patch("kuang.soundcraft.subprocess.run", side_effect=self.fake)
        self.mock.start()
        self.addCleanup(self.mock.stop)
        self.adapter = SoundCraftAdapter(self.binary)
        self.adapter._discovery = deepcopy(CONTRACT)
        self.project = small_project()
        work = self.root/"working"
        work.mkdir()
        self.native = work/"session.scraft"
        self.native.write_text(json.dumps(NATIVE))
        stage = self.root/"stage"
        stage.mkdir()
        self.bundle = self.root/"source"
        self.adapter._publish(stage, self.bundle, self.project, self.native, {"action": "fixture"})
        self.scope = full_scope(self.project)

    def test_discovery_uses_describe_and_actual_parameter_contracts(self):
        adapter = SoundCraftAdapter(self.binary)
        report = adapter.capabilities(self.project)
        self.assertTrue(report["supported"])
        self.assertEqual(report["version"], "0.11.0")
        self.assertEqual(len(report["executable_sha256"]), 64)
        self.assertEqual({argv[2] for argv, _ in self.fake.calls if argv[1] == "describe"}, set(CONTRACT["commands"]))
        self.assertTrue(all(call[1].get("shell") is not True for call in self.fake.calls))

    def test_protocol_has_discovery_apply_inspect_save_export(self):
        for method in ("capabilities", "apply", "inspect", "save", "export"):
            self.assertTrue(callable(getattr(self.adapter, method)))
            self.assertTrue(hasattr(DAWAdapter, method))

    def test_export_roundtrip_preserves_every_canonical_byte_and_identity(self):
        result = self.adapter.export(self.project, self.root/"export")
        self.assertTrue(result["verified"])
        self.assertEqual(result["note_count"], sum(len(c.notes) for t in self.project.tracks for c in t.clips))
        self.assertEqual(dumps(self.adapter.import_project(self.root/"export")), dumps(self.project))
        manifest = json.loads((self.root/"export/manifest.json").read_text())
        self.assertIn("test-note-a", manifest["identities"]["notes"])
        self.assertIn("test-point-a", manifest["identities"]["automation"]["test-lane"][0]["point_indices"])

    def test_native_apply_changes_only_requested_fields_and_writes_receipt(self):
        before = (self.bundle/"session.scraft").read_bytes()
        ops = [SetParameter("set_parameter", "track-kick", "mixer.gain_db", -6),
               SetParameter("set_parameter", "track-snare", "mixer.pan", 0.25)]
        self.adapter.apply(self.bundle, self.root/"edited", ops, self.scope, state_hash(self.project))
        after = json.loads((self.root/"edited/session.scraft").read_text())
        expected = deepcopy(NATIVE)
        expected["tracks"][0]["mixer"]["volume_db"] = -6
        expected["tracks"][1]["mixer"]["pan"] = [0.25, 0.25]
        self.assertEqual(after, expected)
        self.assertEqual((self.bundle/"session.scraft").read_bytes(), before)
        self.assertTrue((self.root/"edited/receipt.json").is_file())

    def test_revision_full_native_comparison_accepts_only_replayed_changes(self):
        ops = [SetParameter("set_parameter", "track-kick", "mixer.gain_db", -10)]
        receipt = Engine(self.project).apply(ops, self.scope, state_hash(self.project))
        edited = self.root/"revision"
        self.adapter.apply(self.bundle, edited, ops, self.scope, state_hash(self.project))
        result = self.adapter.compare_revision(self.bundle, edited, [asdict(receipt)])
        self.assertTrue(result["full_native_preservation"])
        bad = asdict(receipt); bad["operations"][0]["value"] = -11
        with self.assertRaises(ValidationError): self.adapter.compare_revision(self.bundle, edited, [bad])

    def test_revision_unchanged_native_parameter_requires_exact_equality(self):
        ops = [SetParameter("set_parameter", "track-kick", "mixer.gain_db", -10)]
        receipt = Engine(self.project).apply(ops, self.scope, state_hash(self.project))
        edited = self.root/"revision"
        self.adapter.apply(self.bundle, edited, ops, self.scope, state_hash(self.project))
        path = edited/"session.scraft"
        native = json.loads(path.read_text())
        # Deliberate tiny corruption inside the ordinary mapping tolerance. A
        # re-signed unit-test fixture must still fail full preservation comparison.
        params = native["tracks"][1]["instrument"]["params"]
        params["hat_decay"] = params.get("hat_decay", 80) + 1e-7
        path.write_text(json.dumps(native))
        manifest = json.loads((edited/"manifest.json").read_text())
        manifest.update(native_hash=_hash(native), native_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        (edited/"manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(AdapterError, "outside authorized"):
            self.adapter.compare_revision(self.bundle, edited, [asdict(receipt)])

    def test_automation_add_delete_preserves_other_lane_and_point_values(self):
        add = AddAutomationPoints("add_automation_points", "test-lane", [AutomationPoint("phase1-point", 480, -0.2, "linear")])
        self.adapter.apply(self.bundle, self.root/"automation", [add], self.scope, state_hash(self.project))
        changed = self.adapter.import_project(self.root/"automation")
        delete = DeleteAutomationPoints("delete_automation_points", "test-lane", ["phase1-point"])
        self.adapter.apply(self.root/"automation", self.root/"deleted", [delete], self.scope, state_hash(changed))
        self.assertEqual(dumps(self.adapter.import_project(self.root/"deleted")), dumps(self.project))
        self.assertEqual(json.loads((self.root/"deleted/session.scraft").read_text()), NATIVE)

    def test_same_note_count_with_collateral_velocity_change_is_rejected(self):
        def collateral(doc):
            doc["tracks"][1]["playlists"][0]["clips"][0]["content"]["Midi"]["sequence"]["notes"][0]["velocity"] -= 1
        self.fake.collateral = collateral
        with self.assertRaisesRegex(AdapterError, "collateral"):
            self.adapter.apply(self.bundle, self.root/"bad", [SetParameter("set_parameter", "track-kick", "mixer.pan", 0.2)], self.scope, state_hash(self.project))
        self.assertFalse((self.root/"bad").exists())
        self.assertEqual(json.loads((self.bundle/"session.scraft").read_text()), NATIVE)

    def test_collateral_unmodeled_state_and_save_reopen_drift_are_rejected(self):
        self.fake.collateral = lambda doc: doc["edit"].update(playhead=100)
        with self.assertRaisesRegex(AdapterError, "collateral"):
            self.adapter.apply(self.bundle, self.root/"bad-ui", [SetParameter("set_parameter", "track-kick", "mixer.pan", 0.2)], self.scope, state_hash(self.project))
        self.fake.reopen_drift = True
        with self.assertRaisesRegex(AdapterError, "save/reopen"):
            self.adapter.save(self.bundle, self.root/"bad-save")
        self.assertFalse((self.root/"bad-save").exists())

    def test_wrong_parameter_persistence_discards_entire_staged_batch(self):
        self.fake.collateral = lambda doc: doc["tracks"][0]["mixer"].update(volume_db=-12)
        with self.assertRaisesRegex(AdapterError, "did not persist"):
            self.adapter.apply(self.bundle, self.root/"bad", [SetParameter("set_parameter", "track-kick", "mixer.gain_db", -6)], self.scope, state_hash(self.project))
        self.assertFalse((self.root/"bad").exists())

    def test_host_drift_and_missing_companion_are_read_only_errors(self):
        native = self.bundle/"session.scraft"
        changed = json.loads(native.read_text())
        changed["tracks"][0]["comments"] += "human host edit"
        native.write_text(json.dumps(changed))
        with self.assertRaisesRegex(AdapterError, "drift"):
            self.adapter.import_project(self.bundle)
        self.assertEqual(self.adapter.inspect(self.bundle)["native"], changed)
        (self.bundle/"manifest.json").unlink()
        with self.assertRaises(AdapterError): self.adapter.import_project(self.bundle)

    def test_locks_scope_stale_hash_and_note_edits_are_not_bypassed(self):
        op = SetParameter("set_parameter", "track-kick", "mixer.pan", 0.1)
        with self.assertRaises(ScopeError):
            self.adapter.apply(self.bundle, self.root/"bad-scope", [op], Scope(["track-snare"], [], ["mixer.pan"], None, None), state_hash(self.project))
        with self.assertRaisesRegex(ValidationError, "stale"):
            self.adapter.apply(self.bundle, self.root/"stale", [op], self.scope, "0"*64)
        note = deepcopy(self.project.tracks[0].clips[0].notes[0]);note.velocity -= 1
        with self.assertRaisesRegex(AdapterError, "note edits"):
            self.adapter.apply(self.bundle, self.root/"notes", [UpdateNote("update_note", self.project.tracks[0].clips[0].id, note)], self.scope, state_hash(self.project))
        self.project.locks = [Lock("phase1-lock", "track-kick", "mixer.pan")]
        locked = self.root/"locked"
        self.adapter.export(self.project, locked)
        with self.assertRaises(LockedError): self.adapter.apply(locked, self.root/"bad-lock", [op], self.scope, state_hash(self.project))

    def test_overwrites_nested_outputs_and_invalid_paths_are_rejected(self):
        with self.assertRaisesRegex(AdapterError, "already exists"): self.adapter.export(self.project, self.bundle)
        with self.assertRaisesRegex(AdapterError, "outside"): self.adapter.save(self.bundle, self.bundle/"nested")
        with self.assertRaises(AdapterError): self.adapter.inspect(self.root/"missing.scraft")
        with self.assertRaises(AdapterError): self.adapter.inspect("bad\x00path")
        with self.assertRaises(AdapterError): SoundCraftAdapter(self.root/"missing-binary")
        with self.assertRaises(AdapterError): SoundCraftAdapter(self.binary, timeout=float("nan"))

    def test_subprocess_argv_keeps_untrusted_json_and_paths_inert(self):
        self.project.tracks[0].name = 'Kick; touch SHOULD_NOT_EXIST $(echo injected)'
        # Native mapping uses numeric track IDs and JSON argv values, never a shell.
        self.adapter._run([("track.comments", {"track": 1, "comments": self.project.tracks[0].name})], self.root,
                          source=self.bundle/"session.scraft", destination=self.root/"quoted file.scraft")
        argv, options = self.fake.calls[-1]
        self.assertIsInstance(argv, list)
        self.assertNotIn("shell", options)
        self.assertIn("$(echo injected)", argv[argv.index("--cmd")+1])
        self.assertFalse((self.root/"SHOULD_NOT_EXIST").exists())

    def test_nonzero_exit_stderr_timeout_and_malformed_json_all_fail(self):
        for failure in ("exit", "warning", "timeout", "json"):
            self.fake.failure = failure
            with self.subTest(failure=failure), self.assertRaises(AdapterError): self.adapter.inspect(self.bundle)

    def test_version_pin_and_malformed_descriptors_are_rejected(self):
        with patch("kuang.soundcraft.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "SoundCraft CLI 0.12.0\n", "")):
            with self.assertRaisesRegex(AdapterError, "expected SoundCraft"): SoundCraftAdapter(self.binary).capabilities()
        adapter = SoundCraftAdapter(self.binary)
        original = self.fake.__call__
        def bad(argv, **kwargs):
            result = original(argv, **kwargs)
            if argv[1] == "describe": result.stdout = '{"id":"wrong","params":"{}"}'
            return result
        with patch("kuang.soundcraft.subprocess.run", side_effect=bad):
            with self.assertRaisesRegex(AdapterError, "description"): adapter.capabilities()

    def test_missing_or_invalid_plugin_parameter_contracts_are_rejected(self):
        original = self.fake.__call__
        def bad(argv, **kwargs):
            result = original(argv, **kwargs)
            if any("engine.plugins=" in arg for arg in argv):
                result.stdout = 'engine.plugins: [{"id":"drum_synth","instrument":true,"params":[{"id":"level","min":0,"max":1,"default":2,"unit":"Db"}]}]\n'
            return result
        with patch("kuang.soundcraft.subprocess.run", side_effect=bad):
            with self.assertRaisesRegex(AdapterError, "range/type"): SoundCraftAdapter(self.binary).capabilities()

    def test_backend_contract_or_binary_drift_blocks_snapshot_import(self):
        self.binary.write_text("a changed executable with the same reported version")
        with self.assertRaisesRegex(AdapterError, "drift"): self.adapter.import_project(self.bundle)

    def test_unknown_parameter_units_ranges_and_automation_targets_fail_explicitly(self):
        p = load_compatible_example()
        p.tracks[3].effects[0].parameters["soundcraft.hpf_freq"] = 10000
        with self.assertRaises(ValidationError): self.adapter.capabilities(p)
        p = load_compatible_example()
        next(s for s in p.parameters if s.id == "soundcraft.hpf_freq").maximum = 10000
        p.tracks[3].effects[0].parameters["soundcraft.hpf_freq"] = 3000
        self.assertFalse(self.adapter.capabilities(p)["supported"])
        p = load_compatible_example()
        next(s for s in p.parameters if s.id == "soundcraft.hpf_freq").unit = "ms"
        self.assertFalse(self.adapter.capabilities(p)["supported"])
        p = load_compatible_example()
        p.parameters.append(ParameterSpec("soundcraft.missing", "Hz", 20, 20000, 100, ["effect"]))
        p.tracks[3].effects[0].parameters["soundcraft.missing"] = 100
        self.assertFalse(self.adapter.capabilities(p)["supported"])
        p = load_compatible_example()
        p.automation.append(AutomationLane("instrument-auto", "instrument-bass", "synth.cutoff_hz", [AutomationPoint("cutoff-point", 0, 400, "linear")]))
        self.assertFalse(self.adapter.capabilities(p)["supported"])

    def test_result_count_mismatch_and_unexpected_automation_are_rejected(self):
        with patch("kuang.soundcraft.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")):
            with self.assertRaisesRegex(AdapterError, "result count"): self.adapter.inspect(self.bundle)
        altered = deepcopy(NATIVE)
        altered["tracks"][0]["automation"].append({"param": "Mute", "points": [], "enabled": True})
        with self.assertRaisesRegex(AdapterError, "automation lanes"): self.adapter._verify_project(self.project, altered)

    def test_capabilities_reports_unsupported_without_writing(self):
        from kuang.generator import generate
        report = self.adapter.capabilities(generate(7))
        self.assertFalse(report["supported"])
        with self.assertRaises(UnsupportedError): self.adapter.export(generate(7), self.root/"unsupported")
        self.assertFalse((self.root/"unsupported").exists())
        self.project.automation[0].points[0].shape = "step"
        self.assertFalse(self.adapter.capabilities(self.project)["supported"])

    def test_save_clone_keeps_full_native_and_canonical_state(self):
        self.adapter.save(self.bundle, self.root/"clone")
        self.assertEqual(json.loads((self.root/"clone/session.scraft").read_text()), NATIVE)
        self.assertEqual(dumps(self.adapter.import_project(self.root/"clone")), dumps(self.project))

    def test_cli_import_and_export_reports_and_protects_report_path(self):
        def invoke(*argv):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return main(["soundcraft", "--executable", str(self.binary), *map(str, argv)])
        self.assertEqual(invoke("import", self.bundle, self.root/"restored.json", "--report", self.root/"import-report.json"), 0)
        self.assertEqual((self.root/"restored.json").read_text(), dumps(self.project))
        self.assertEqual(invoke("import", self.bundle, self.root/"restored.json"), 2)
        self.assertEqual(invoke("export", self.bundle/"project.kuang.json", self.root/"new-bundle", "--report", self.root/"new-bundle/report.json"), 2)


class WavAnalysisTests(unittest.TestCase):
    def test_known_pcm_peak_rms_and_silence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"known.wav"
            for value in (0, 1<<21):
                with wave.open(str(path), "wb") as stream:
                    stream.setparams((2, 3, 48000, 0, "NONE", "not compressed"))
                    stream.writeframes(value.to_bytes(3, "little", signed=True)*480)
                result = analyze_wav(path)
                self.assertEqual(result["peak"], value/(1<<23))
                self.assertEqual(result["rms"], value/(1<<23))
                self.assertEqual(result["non_silent"], value != 0)
                self.assertEqual(result["sample_rate"], 48000)

    def test_invalid_or_empty_wav_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"bad.wav"
            path.write_bytes(b"not WAV")
            with self.assertRaises(ValidationError): analyze_wav(path)


def load_compatible_example():
    from kuang.schema import load
    return load(Path(__file__).resolve().parents[1]/"examples/soundcraft-demo.kuang.json")
