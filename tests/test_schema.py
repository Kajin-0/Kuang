import json
import math
import tempfile
import unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from kuang.generator import generate
from kuang.schema import (AutomationLane, AutomationPoint, Clip, Lock, Send, Track,
                          ValidationError, dumps, load, loads, save, state_hash, validate)
from helpers import small_project


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.project = small_project()

    def test_deterministic_roundtrip_and_numeric_normalization(self):
        text = dumps(self.project)
        self.assertEqual(text, dumps(loads(text)))
        self.assertEqual(state_hash(self.project), state_hash(loads(text)))
        other = deepcopy(self.project)
        other.tempo_bpm = float(other.tempo_bpm)
        self.assertEqual(dumps(other), text)

    def test_save_load_and_atomic_failure_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.kuang.json"
            save(self.project, path)
            original = path.read_bytes()
            self.assertEqual(dumps(load(path)), dumps(self.project))
            with patch("kuang.schema.os.replace", side_effect=OSError("simulated disk failure")):
                with self.assertRaises(OSError):
                    save(generate(22), path)
            self.assertEqual(original, path.read_bytes())
            self.assertEqual([p.name for p in path.parent.iterdir()], [path.name])

    def test_strict_json_types_unknown_keys_and_version(self):
        original = asdict(self.project)
        for change in [{"ppq": True}, {"tempo_bpm": "124"}, {"unknown": 4}, {"version": "9"},
                       {"time_signature": [3, 4]}, {"tempo_bpm": math.inf}, {"bars": 0}]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                loads(json.dumps({**original, **change}))
        with self.assertRaises(ValidationError):
            loads('{"version":"0.1","version":"0.1"}')
        missing = deepcopy(original)
        del missing["locks"]
        with self.assertRaises(ValidationError):
            loads(json.dumps(missing))
        with self.assertRaises(ValidationError):
            loads(json.dumps({**original, "tempo_bpm": 10**1000}))
        with self.assertRaises(ValidationError):
            loads(json.dumps({**original, "name": "\ud800"}))

    def test_notes_boundaries_overlap_and_ids(self):
        for field, value in [("pitch", 128), ("velocity", 0), ("channel", 16), ("duration", 0),
                             ("start", -1), ("duration", 999999), ("id", "bad id")]:
            project = deepcopy(self.project)
            setattr(project.tracks[0].clips[0].notes[0], field, value)
            with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                validate(project)
        project = deepcopy(self.project)
        project.tracks[0].clips[0].notes[1].start = 100
        with self.assertRaisesRegex(ValidationError, "overlapping"):
            validate(project)
        project = deepcopy(self.project)
        project.tracks[0].clips[0].notes[1].id = "test-note-a"
        with self.assertRaisesRegex(ValidationError, "duplicate ID"):
            validate(project)

    def test_overlap_across_clips_rejected(self):
        clip = deepcopy(self.project.tracks[0].clips[0])
        clip.id = "another-clip"
        for note in clip.notes:
            note.id += "-copy"
        self.project.tracks[0].clips.append(clip)
        with self.assertRaisesRegex(ValidationError, "overlapping"):
            validate(self.project)

    def test_registry_ranges_target_types_and_immutable_mixer_semantics(self):
        for parameter, value in [("mixer.pan", 1.01), ("mixer.mute", 0.5), ("synth.resonance", 0.3), ("unregistered", 0)]:
            project = deepcopy(self.project)
            project.tracks[0].controls[parameter] = value
            with self.subTest(parameter=parameter), self.assertRaises(ValidationError):
                validate(project)
        self.project.parameters[0].minimum = -100
        with self.assertRaisesRegex(ValidationError, "required mixer"):
            validate(self.project)

    def test_sections_cover_timeline_without_gaps(self):
        self.project.sections[1].start += 1
        with self.assertRaisesRegex(ValidationError, "sections"):
            validate(self.project)

    def test_automation_and_lock_references(self):
        for change in ("unknown-target", "duplicate-tick", "bad-range", "unknown-parameter"):
            project = deepcopy(self.project)
            lane = project.automation[0]
            if change == "unknown-target": lane.target_id = "absent"
            if change == "duplicate-tick": lane.points[1].tick = 0
            if change == "bad-range": lane.points[0].value = 12
            if change == "unknown-parameter": lane.parameter_id = "missing"
            with self.subTest(change=change), self.assertRaises(ValidationError):
                validate(project)
        self.project.locks = [Lock("lock-a", "missing", None)]
        with self.assertRaises(ValidationError):
            validate(self.project)

    def test_boolean_automation_requires_step(self):
        self.project.automation = [AutomationLane("lane-mute", "track-kick", "mixer.mute", [
            AutomationPoint("point-mute", 0, 1, "linear")])]
        with self.assertRaisesRegex(ValidationError, "step"):
            validate(self.project)
        self.project.automation[0].points[0].shape = "step"
        validate(self.project)

    def test_routing_valid_destinations_and_no_cycles(self):
        self.project.tracks[0].sends = [Send("send-a", "track-snare", -9, 0.1, "post_fader")]
        validate(self.project)
        self.project.tracks[1].sends = [Send("send-b", "track-kick", -12, 0, "pre_fader")]
        with self.assertRaisesRegex(ValidationError, "routing cycle"):
            validate(self.project)
        self.project.tracks[1].sends[0].target_track_id = "missing"
        with self.assertRaisesRegex(ValidationError, "destination"):
            validate(self.project)

    def test_audio_and_bus_schema_are_structured_but_no_renderer_implied(self):
        self.project.tracks.append(Track("track-audio", "Reference", "audio", None,
                                        {"mixer.gain_db": -12, "mixer.pan": 0, "mixer.mute": 0}, [],
                                        [Clip("clip-audio", "Local recording", "audio", 0, 960, [], "user:recording.wav")], [], True))
        self.project.tracks.append(Track("track-bus", "Bus", "bus", None,
                                        {"mixer.gain_db": 0, "mixer.pan": 0, "mixer.mute": 0}, [], [], [], True))
        self.assertEqual(dumps(self.project), dumps(loads(dumps(self.project))))
