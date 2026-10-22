"""Opt-in full real revisions, source preservation, replay, drift and measured A/B."""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from kuang.cli import main
from kuang.create import create
from kuang.revise import revise, source_hashes
from kuang.schema import ValidationError, dumps, load
from kuang.soundcraft import SoundCraftAdapter
from test_revision import COMPOUND
from test_song import PROMPTS


@unittest.skipUnless(os.environ.get("KUANG_SOUNDCRAFT_INTEGRATION") == "1", "opt in to installed SoundCraft 0.11.0 revisions")
class SoundCraftRevisionIntegrationTests(unittest.TestCase):
    def test_two_real_revision_workflows_exact_native_ab_replay_and_drift(self):
        selected = os.environ.get("KUANG_SOUNDCRAFT_ARTIFACTS")
        temporary = tempfile.TemporaryDirectory(prefix="kuang-phase3-real-") if not selected else None
        try:
            root = Path(selected)/"phase3" if selected else Path(temporary.name)
            if root.exists() and any(root.iterdir()):
                raise RuntimeError("Phase 3 artifact directory must be new or empty")
            root.mkdir(parents=True, exist_ok=True)
            adapter = SoundCraftAdapter(timeout=120)
            results = []
            for i, prompt in enumerate(PROMPTS[:2]):
                source, output = root/f"source-{i}", root/f"revision-{i}"
                create(prompt+", 8 bars", source, soundcraft=str(adapter.executable))
                self.assertFalse((source/"preview.wav").exists())
                before_files = source_hashes(source)
                before = load(source/"project.kuang.json")
                instruction = COMPOUND if i == 0 else "simplify drums in bars 3-4, make the harmony reverb drier, turn lead down by 3 dB, keep bass unchanged"
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(main(["revise", str(source), instruction, "--out-dir", str(output),
                                           "--soundcraft", str(adapter.executable), "--render"]), 0)
                report = json.loads(stdout.getvalue())
                self.assertEqual(report, json.loads((output/"report.json").read_text()))
                self.assertEqual(source_hashes(source), before_files)
                self.assertTrue(report["native_comparison"]["full_native_preservation"])
                self.assertTrue(report["comparison"]["unchanged_equal"])
                self.assertTrue(report["audio"]["difference"]["measurable_change"])
                self.assertGreater(report["audio"]["difference"]["difference_to_original_rms_ratio"], 0.01)
                for label in ("original", "revised"):
                    a = report["audio"][label]["analysis"]
                    self.assertEqual((a["sample_rate"], a["bits_per_sample"], a["channels"]), (48000, 24, 2))
                    self.assertTrue(a["non_silent"]); self.assertLess(a["peak"], 1)
                    self.assertGreater(a["rms"], 1e-6); self.assertEqual(a["clipped_samples"], 0)
                after = load(output/"project.kuang.json")
                self.assertEqual(after.metadata, before.metadata)
                native = adapter.inspect(output/"native")["native"]
                for track, host in zip(after.tracks, native["tracks"]):
                    actual = [(n["start"], n["length"], n["pitch"], n["velocity"], n["channel"])
                              for c in host["playlists"][0]["clips"] for n in c["content"]["Midi"]["sequence"]["notes"]]
                    expected = [(c.start+n.start, n.duration, n.pitch, n.velocity, n.channel) for c in track.clips for n in c.notes]
                    self.assertEqual(Counter(actual), Counter(expected))
                adapter.save(output/"native", root/f"saved-{i}")
                self.assertEqual(adapter.inspect(root/f"saved-{i}")["native"], native)
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["undo", str(output/"project.kuang.json"), str(output/"revision-receipt.json"), str(root/f"undo-{i}.json")]), 0)
                    self.assertEqual(main(["redo", str(root/f"undo-{i}.json"), str(output/"revision-receipt.json"), str(root/f"redo-{i}.json")]), 0)
                self.assertEqual(dumps(load(root/f"undo-{i}.json")), dumps(before))
                self.assertEqual(dumps(load(root/f"redo-{i}.json")), dumps(after))
                # A second revision is an actual iteration on the existing result.
                iteration = revise(output, "turn the lead down by 1 dB", root/f"iteration-{i}", soundcraft=str(adapter.executable))
                self.assertTrue(iteration["native_comparison"]["full_native_preservation"])
                results.append(report)
            # Mutate only a new copy; neither real source nor published revision is edited.
            drift = root/"drift-copy"
            shutil.copytree(root/"revision-0", drift)
            path = drift/"native/session.scraft"
            native = json.loads(path.read_text())
            native["tracks"][0]["mixer"]["volume_db"] -= 1
            path.write_text(json.dumps(native))
            with self.assertRaisesRegex(ValidationError, "drift"):
                revise(drift, "turn lead down by 1 dB", root/"rejected", soundcraft=str(adapter.executable))
            self.assertFalse((root/"rejected").exists())
            (root/"revision-results.json").write_text(json.dumps({"complete": True, "results": results,
                "drift_rejected": True, "iterations_verified": True}, sort_keys=True, indent=2)+"\n")
        finally:
            if temporary: temporary.cleanup()
