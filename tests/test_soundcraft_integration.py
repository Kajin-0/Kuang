"""Opt-in, real SoundCraft 0.11.0 execution. Never downloads a backend."""

import json
import contextlib
import io
import os
import tempfile
import unittest
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from kuang.generator import generate
from kuang.schema import AutomationPoint, dumps, load, state_hash
from kuang.soundcraft import AdapterError, SoundCraftAdapter
from kuang.transactions import AddAutomationPoints, ScopeError, SetParameter
from kuang.cli import main
from test_song import PROMPTS, content
from helpers import full_scope, small_project


@unittest.skipUnless(os.environ.get("KUANG_SOUNDCRAFT_INTEGRATION") == "1", "opt in with KUANG_SOUNDCRAFT_INTEGRATION=1 and an installed 0.11.0 binary")
class SoundCraftIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = SoundCraftAdapter(timeout=120)
        selected = os.environ.get("KUANG_SOUNDCRAFT_ARTIFACTS")
        cls.temporary = tempfile.TemporaryDirectory(prefix="kuang-real-soundcraft-") if not selected else None
        cls.root = Path(selected or cls.temporary.name).expanduser().resolve()
        if selected and cls.root.exists() and any(cls.root.iterdir()):
            raise RuntimeError("integration artifact directory must be new or empty")
        cls.root.mkdir(parents=True, exist_ok=True)
        cls.results = {}
        cls.project = load(Path(__file__).resolve().parents[1]/"examples/soundcraft-demo.kuang.json")

    @classmethod
    def tearDownClass(cls):
        (cls.root/"verification-results.json").write_text(json.dumps({"complete": set(cls.results) == {"demo7", "demo8", "negative", "phase2"},
            "soundcraft": cls.adapter.capabilities(), "results": cls.results}, indent=2, sort_keys=True)+"\n")
        if cls.temporary:
            cls.temporary.cleanup()

    def assert_all_notes(self, canonical, native):
        self.assertEqual(len(native["tracks"]), len(canonical.tracks))
        for track, host in zip(canonical.tracks, native["tracks"]):
            self.assertEqual(host["name"], track.name)
            observed = []
            for clip in host["playlists"][0]["clips"]:
                self.assertEqual(clip["start"], 0)
                observed += [(n["start"], n["length"], n["pitch"], n["velocity"], n["channel"])
                             for n in clip["content"]["Midi"]["sequence"]["notes"]]
            expected = [(c.start+n.start, n.duration, n.pitch, n.velocity, n.channel) for c in track.clips for n in c.notes]
            self.assertEqual(Counter(observed), Counter(expected))
        self.assertEqual(sum(len(c["content"]["Midi"]["sequence"]["notes"]) for t in native["tracks"] for c in t["playlists"][0]["clips"]), 1083)

    def assert_audio(self, report):
        audio = report["analysis"]
        self.assertEqual((audio["sample_rate"], audio["bits_per_sample"], audio["channels"]), (48000, 24, 2))
        self.assertTrue(audio["non_silent"])
        self.assertGreater(audio["rms"], 1e-6)
        self.assertGreater(audio["peak"], 1e-5)
        self.assertLess(audio["peak"], 1)
        self.assertEqual(audio["clipped_samples"], 0)
        self.assertGreater(audio["duration_seconds"], 62)
        self.assertTrue(report["native_unchanged"])

    def test_real_demo7_roundtrip_reopen_all_notes_and_full_render(self):
        bundle = self.root/"demo7"
        export = self.adapter.export(self.project, bundle)
        restored = self.adapter.import_project(bundle)
        self.assertEqual(dumps(restored), dumps(self.project))
        self.assert_all_notes(restored, self.adapter.inspect(bundle)["native"])
        manifest = json.loads((bundle/"manifest.json").read_text())
        self.assertEqual(len(manifest["identities"]["notes"]), 1083)
        render = self.adapter.render(bundle, self.root/"demo7.wav")
        self.assert_audio(render)
        self.results["demo7"] = {"export": export, "render": render}

    def test_real_second_seed_staged_eq_automation_edit_save_render(self):
        second = deepcopy(self.project)
        velocities = {n.id: n.velocity for t in generate(8).tracks for c in t.clips for n in c.notes}
        for track in second.tracks:
            for clip in track.clips:
                for note in clip.notes:
                    note.velocity = velocities[note.id]
        second.metadata["seed"] = "8"
        self.assertNotEqual(state_hash(second), state_hash(self.project))
        source = self.root/"demo8-source"
        self.adapter.export(second, source)
        original = (source/"session.scraft").read_bytes()
        ops = [SetParameter("set_parameter", "track-kick", "mixer.gain_db", -10),
               SetParameter("set_parameter", "track-arp", "mixer.pan", -0.15),
               SetParameter("set_parameter", "effect-bass-eq", "soundcraft.hpf_freq", 55),
               SetParameter("set_parameter", "effect-bass-eq", "soundcraft.low_mid_gain", -3),
               AddAutomationPoints("add_automation_points", "automation-pad-gain", [AutomationPoint("point-pad-phase1-real", 4800, -24, "linear")])]
        scope = full_scope(second)
        (self.root/"demo8-edit-request.json").write_text(json.dumps({"expected_before_hash": state_hash(second), "scope": asdict(scope), "operations": [asdict(op) for op in ops]}, indent=2)+"\n")
        edited = self.root/"demo8"
        edit = self.adapter.apply(source, edited, ops, scope, state_hash(second))
        self.assertTrue(edit["full_native_preservation"])
        self.assertEqual((source/"session.scraft").read_bytes(), original)
        project = self.adapter.import_project(edited)
        native = self.adapter.inspect(edited)["native"]
        self.assert_all_notes(project, native)
        expected = json.loads(original)
        expected["tracks"][0]["mixer"]["volume_db"] = -10
        expected["tracks"][6]["mixer"]["pan"] = [-0.15, -0.15]
        expected["tracks"][3]["mixer"]["inserts"][0]["params"].update(hpf_freq=55, low_mid_gain=-3)
        points = expected["tracks"][5]["automation"][0]["points"]
        points.append({"at": round(4800*48000*60/(960*124)), "value": -24})
        points.sort(key=lambda p: p["at"])
        self.assertEqual(native, expected)
        clone = self.root/"demo8-saved"
        self.adapter.save(edited, clone)
        self.assertEqual(self.adapter.inspect(clone)["native"], native)
        render = self.adapter.render(clone, self.root/"demo8.wav")
        self.assert_audio(render)
        self.results["demo8"] = {"edit": edit, "render": render}

    def test_real_failed_scoped_edit_and_drift_leave_source_untouched(self):
        p = small_project()
        bundle = self.root/"negative-source"
        self.adapter.export(p, bundle)
        original = (bundle/"session.scraft").read_bytes()
        scope = full_scope(p)
        scope.track_ids = ["track-snare"]
        scope.clip_ids = []
        with self.assertRaises(ScopeError):
            self.adapter.apply(bundle, self.root/"rejected", [SetParameter("set_parameter", "track-kick", "mixer.pan", 0.5)], scope, state_hash(p))
        self.assertFalse((self.root/"rejected").exists())
        self.assertEqual((bundle/"session.scraft").read_bytes(), original)
        drift = json.loads(original)
        drift["tracks"][0]["playlists"][0]["clips"][0]["content"]["Midi"]["sequence"]["notes"][0]["velocity"] -= 1
        (bundle/"session.scraft").write_text(json.dumps(drift))
        changed = (bundle/"session.scraft").read_bytes()
        with self.assertRaisesRegex(AdapterError, "drift"):
            self.adapter.import_project(bundle)
        self.assertEqual(self.adapter.inspect(bundle)["native"], drift)
        self.assertEqual((bundle/"session.scraft").read_bytes(), changed)
        self.results["negative"] = {"scope_rejected": True, "same_count_note_drift_rejected": True, "inspection_read_only": True}

    def test_real_phase2_cli_varied_prompts_full_notes_fx_reopen_and_audio(self):
        reports, projects, natives = [], [], []
        for index, prompt in enumerate(PROMPTS[:2]):
            output = self.root/f"phase2-{index}"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(main(["create", prompt + ", 8 bars", "--out-dir", str(output),
                                       "--soundcraft", str(self.adapter.executable), "--render"]), 0)
            report = json.loads(stdout.getvalue())
            self.assertEqual(report, json.loads((output/"report.json").read_text()))
            self.assertTrue(report["validation"]["audio_verified"])
            self.assertTrue(report["validation"]["save_reopen_equal"])
            audio = report["render"]["analysis"]
            self.assertEqual((audio["sample_rate"], audio["bits_per_sample"], audio["channels"]), (48000, 24, 2))
            self.assertTrue(audio["non_silent"])
            self.assertGreater(audio["rms"], 1e-6)
            self.assertLess(audio["peak"], 1)
            self.assertEqual(audio["clipped_samples"], 0)
            project = self.adapter.import_project(output/"native")
            self.assertEqual(dumps(project), (output/"project.kuang.json").read_text())
            native = self.adapter.inspect(output/"native")["native"]
            # Independent exact-field check, rather than trusting adapter report flags.
            for track, host in zip(project.tracks, native["tracks"]):
                observed = [(n["start"], n["length"], n["pitch"], n["velocity"], n["channel"])
                            for c in host["playlists"][0]["clips"] for n in c["content"]["Midi"]["sequence"]["notes"]]
                expected = [(c.start+n.start, n.duration, n.pitch, n.velocity, n.channel) for c in track.clips for n in c.notes]
                self.assertEqual(Counter(observed), Counter(expected))
            saved = self.root/f"phase2-{index}-saved"
            self.adapter.save(output/"native", saved)
            self.assertEqual(self.adapter.inspect(saved)["native"], native)
            for artifact in report["artifacts"].values():
                self.assertTrue(Path(artifact).is_file())
            reports.append(report); projects.append(project); natives.append(native)
        self.assertNotEqual(content(projects[0]), content(projects[1]))
        self.assertNotEqual(natives[0]["tempo"], natives[1]["tempo"])
        self.assertNotEqual([t["instrument"] for t in natives[0]["tracks"]], [t["instrument"] for t in natives[1]["tracks"]])
        self.results["phase2"] = reports
