"""SoundCraft 0.11.0 backend: isolated native edits, complete verification, no sync."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from . import midi
from .audio import analyze_wav
from .schema import Project, ValidationError, dumps, load, save, state_hash, strict_json, validate
from .transactions import AddAutomationPoints, DeleteAutomationPoints, Engine, SetParameter

HOST_VERSION = "0.11.0"
COMMANDS = ("engine.plugins", "session.new", "session.inspect", "session.save", "file.import_midi",
            "event.tempo", "mix.volume", "mix.pan", "mix.mute", "mix.instrument", "mix.insert",
            "mix.insert_params", "mix.insert_bypass", "automation.set_point", "automation.clear",
            "mix.automation_mode", "track.comments", "markers.add", "file.bounce_mix")
MIXER = {"mixer.gain_db": ("mix.volume", "db", "volume_db"),
         "mixer.pan": ("mix.pan", "pan", "pan"), "mixer.mute": ("mix.mute", "value", "mute")}


class AdapterError(ValidationError):
    pass


class UnsupportedError(AdapterError):
    def __init__(self, report):
        self.report = report
        super().__init__("unsupported SoundCraft mapping: " + "; ".join(report["unsupported"]))


def _json(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _hash(data):
    return hashlib.sha256(_json(data).encode("utf-8")).hexdigest()


def _write_json(path, data):
    Path(path).write_text(json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def _close(actual, expected):
    return type(actual) in (int, float) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=2e-7, abs_tol=1e-6)


def _path(path, suffix=None):
    if not str(path) or "\x00" in str(path):
        raise AdapterError("empty/NUL path")
    result = Path(path).expanduser().resolve()
    if suffix and result.suffix.lower() != suffix:
        raise AdapterError(f"expected {suffix} file: {result}")
    return result


def _read_json(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
        raise AdapterError(f"missing or oversized JSON file: {path}")
    result = strict_json(path.read_text(encoding="utf-8"))
    try:
        _json(result)
    except ValueError as exc:
        raise AdapterError("JSON contains a non-finite number") from exc
    return result


class SoundCraftAdapter:
    def __init__(self, executable=None, *, timeout=60):
        selected = executable or os.environ.get("KUANG_SOUNDCRAFT") or shutil.which("soundcraft-cli")
        if not selected:
            raise AdapterError("SoundCraft is optional: supply --executable or KUANG_SOUNDCRAFT")
        self.executable = _path(selected)
        if not self.executable.is_file() or not os.access(self.executable, os.X_OK):
            raise AdapterError("SoundCraft executable must be an executable regular file")
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 600:
            raise AdapterError("timeout must be >0 and <=600 seconds")
        self.timeout = timeout
        self._discovery = None

    def _call(self, argv, cwd):
        try:
            result = subprocess.run([str(self.executable), *argv], cwd=cwd, capture_output=True,
                                    text=True, encoding="utf-8", timeout=self.timeout, check=False)
        except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
            raise AdapterError(f"SoundCraft process failed: {exc}") from exc
        if result.returncode != 0 or result.stderr.strip():
            raise AdapterError(f"SoundCraft exit {result.returncode}: {result.stderr.strip()[:2000] or result.stdout[:2000]}")
        if len(result.stdout) > 32 * 1024 * 1024:
            raise AdapterError("oversized SoundCraft report")
        return result.stdout

    def _run(self, commands, directory, *, source=None, destination=None):
        argv = ["run"]
        if source:
            argv += ["--in", str(source)]
        for command, params in commands:
            if command not in COMMANDS:
                raise AdapterError(f"unapproved host command: {command}")
            argv += ["--cmd", command + "=" + _json(params)]
        if destination:
            argv += ["--save", str(destination)]
        lines = self._call(argv, directory).splitlines()
        if len(lines) != len(commands) + bool(destination):
            raise AdapterError("unexpected SoundCraft result count")
        results = []
        for (command, _), line in zip(commands, lines):
            prefix = command + ": "
            if not line.startswith(prefix):
                raise AdapterError("unexpected SoundCraft command result")
            results.append(strict_json(line[len(prefix):]))
        if destination:
            result = strict_json(lines[-1])
            if type(result) is not dict or result.get("path") != str(destination) or not Path(destination).is_file():
                raise AdapterError("SoundCraft did not save the requested native file")
        return results

    def _discover(self):
        if self._discovery is None:
            with tempfile.TemporaryDirectory(prefix="kuang-sc-discover-") as directory:
                version = self._call(["--version"], directory).strip()
                if version != f"SoundCraft CLI {HOST_VERSION}":
                    raise AdapterError(f"expected SoundCraft CLI {HOST_VERSION}, received {version!r}")
                descriptions = {}
                for command in COMMANDS:
                    description = strict_json(self._call(["describe", command], directory))
                    if type(description) is not dict or description.get("id") != command or type(description.get("params")) is not str:
                        raise AdapterError(f"invalid command description: {command}")
                    descriptions[command] = description
                plugins = self._run([("engine.plugins", {})], directory)[0]
                if type(plugins) is not list or not plugins:
                    raise AdapterError("invalid plugin discovery")
                for plugin in plugins:
                    if (type(plugin) is not dict or type(plugin.get("id")) is not str or
                            type(plugin.get("instrument")) is not bool or type(plugin.get("params")) is not list):
                        raise AdapterError("invalid plugin descriptor")
                    for parameter in plugin["params"]:
                        if type(parameter) is not dict or not {"id", "min", "max", "unit", "default"} <= parameter.keys():
                            raise AdapterError("incomplete plugin parameter descriptor")
                        if (type(parameter["id"]) is not str or type(parameter["unit"]) is not str or
                                any(type(parameter[k]) not in (int, float) or not math.isfinite(parameter[k]) for k in ("min", "max", "default")) or
                                not parameter["min"] <= parameter["default"] <= parameter["max"]):
                            raise AdapterError("invalid plugin parameter range/type")
                self._discovery = {"version": HOST_VERSION, "commands": descriptions,
                                   "plugins": {p["id"]: p for p in plugins}}
        return self._discovery

    def _device(self, track):
        inst = track.instrument
        if inst.kind == "midi":
            return "drum_synth" if {n.channel for c in track.clips for n in c.notes} == {9} else "subtractive_synth"
        if not inst.plugin_ref or not inst.plugin_ref.startswith("soundcraft:"):
            raise AdapterError(f"instrument {inst.id} requires a soundcraft: built-in reference")
        return inst.plugin_ref.removeprefix("soundcraft:")

    def _parameter(self, project, device, plugin, parameter, value):
        descriptors = self._discover()["plugins"]
        if plugin not in descriptors:
            raise AdapterError(f"unknown built-in plugin: {plugin}")
        if parameter == "effect.bypass":
            if not hasattr(device, "kind"):
                return "bypass", bool(value)
            raise AdapterError("instrument bypass has no canonical mapping")
        scale = 1
        if parameter == "effect.wet":
            name, scale = "mix", 100
        elif parameter == "synth.cutoff_hz":
            name = "cutoff"
        elif parameter == "synth.resonance":
            name, scale = "resonance", 100
        elif parameter.startswith("soundcraft."):
            name = parameter.removeprefix("soundcraft.")
        else:
            raise AdapterError(f"unmapped built-in parameter: {parameter}")
        descriptor = next((p for p in descriptors[plugin]["params"] if p["id"] == name), None)
        if descriptor is None:
            raise AdapterError(f"{plugin} has no discovered parameter {name}")
        spec = next(s for s in project.parameters if s.id == parameter)
        units = {"dB": "Db", "Hz": "Hz", "ms": "Ms", "boolean": "Toggle", "normalized": "Percent"}
        if units.get(spec.unit) != descriptor["unit"]:
            raise AdapterError(f"unit mismatch: {parameter} / {descriptor['unit']}")
        if parameter.startswith("soundcraft.") and spec.unit == "normalized":
            scale = 100
        converted = value * scale
        if not descriptor["min"] <= converted <= descriptor["max"]:
            raise AdapterError(f"outside discovered plugin range: {parameter}")
        return name, converted

    def _lane(self, project, lane):
        for index, track in enumerate(project.tracks):
            if lane.target_id == track.id:
                mapping = {"mixer.gain_db": [("volume", "Volume")],
                           "mixer.pan": [("pan", {"Pan": 0}), ("pan2", {"Pan": 1})],
                           "mixer.mute": [("mute", "Mute")]}
                if lane.parameter_id not in mapping:
                    break
                return index, [(name, native, [(p.id, p.tick, p.value) for p in sorted(lane.points, key=lambda x: x.tick)])
                               for name, native in mapping[lane.parameter_id]]
            for slot, effect in enumerate(track.effects):
                if lane.target_id == effect.id:
                    if lane.parameter_id == "effect.bypass":
                        raise AdapterError("FX bypass automation is unsupported")
                    plugin = effect.plugin_ref.removeprefix("soundcraft:")
                    name, _ = self._parameter(project, effect, plugin, lane.parameter_id, effect.parameters[lane.parameter_id])
                    points = [(p.id, p.tick, self._parameter(project, effect, plugin, lane.parameter_id, p.value)[1])
                              for p in sorted(lane.points, key=lambda x: x.tick)]
                    return index, [(f"plugin:{slot}:{name}", {"Plugin": {"slot": slot, "param": name}}, points)]
        raise AdapterError(f"unsupported automation target: {lane.target_id}/{lane.parameter_id}")

    def capabilities(self, project=None):
        discovery = self._discover()
        report = {"adapter": "soundcraft", "version": HOST_VERSION, "contract_hash": _hash(discovery),
                  "executable_sha256": hashlib.sha256(self.executable.read_bytes()).hexdigest(),
                  "operations": ["set_parameter", "add_automation_points", "delete_automation_points"],
                  "apply_targets": {"set_parameter": "standard track mixer controls and mapped effect parameters",
                                    "automation": "existing canonical track/effect lanes; instrument and bypass automation unsupported",
                                    "notes": "edit canonical JSON through Kuang transactions, then create a fresh export"},
                  "unsupported": [], "notes": [
                      "MIDI clips merge per track; original clip/note/point IDs are retained in the companion canonical snapshot and identity map.",
                      "Native import restores a verified snapshot only; external host edits require explicit reconciliation and are rejected.",
                      "One canonical pan drives both native stereo panners; audio panning laws are host-defined.",
                      "Key, locks and other canonical-only intent remain in the snapshot; native save names the session from its filename."]}
        if project is not None:
            validate(project)
            plugins = discovery["plugins"]
            for track in project.tracks:
                try:
                    if track.kind != "midi" or not track.clips or not any(c.notes for c in track.clips):
                        raise AdapterError("only nonempty MIDI tracks are supported")
                    if not track.name or track.sends or not track.output_master or set(track.controls) != set(MIXER):
                        raise AdapterError("requires named tracks, master output, standard mixer controls and no sends")
                    instrument = track.instrument
                    if instrument.preset_ref or instrument.midi_program is not None:
                        raise AdapterError("preset/GM program timbres require explicit built-in instrument configuration (midi_program=null)")
                    plugin = self._device(track)
                    if plugin not in plugins or not plugins[plugin]["instrument"] or plugin == "sampler":
                        raise AdapterError("only discovered, self-contained built-in synthesizers are supported")
                    for parameter, value in instrument.parameters.items():
                        self._parameter(project, instrument, plugin, parameter, value)
                    if len(track.effects) > 10:
                        raise AdapterError("native insert limit is 10")
                    for effect in track.effects:
                        if effect.preset_ref or not effect.plugin_ref.startswith("soundcraft:"):
                            raise AdapterError(f"unbound effect or preset: {effect.id}")
                        plugin = effect.plugin_ref.removeprefix("soundcraft:")
                        if plugin not in plugins or plugins[plugin]["instrument"]:
                            raise AdapterError(f"unknown native effect: {plugin}")
                        for parameter, value in effect.parameters.items():
                            self._parameter(project, effect, plugin, parameter, value)
                except AdapterError as exc:
                    report["unsupported"].append(f"{track.id}: {exc}")
            for lane in project.automation:
                try:
                    self._lane(project, lane)
                    if lane.points and min(p.tick for p in lane.points) != 0:
                        raise AdapterError("nonempty automation must start at tick 0 (native holds first value before first point)")
                    expected = "step" if lane.parameter_id == "mixer.mute" else "linear"
                    if any(p.shape != expected for p in lane.points):
                        raise AdapterError(f"native lane requires {expected} interpolation")
                except AdapterError as exc:
                    report["unsupported"].append(f"{lane.id}: {exc}")
        report["supported"] = not report["unsupported"]
        return report

    def _require(self, project):
        report = self.capabilities(project)
        if not report["supported"]:
            raise UnsupportedError(report)
        return report

    def _native(self, source):
        path = _path(source)
        if path.is_dir():
            path = path / "session.scraft"
        path = _path(path, ".scraft")
        data = _read_json(path)
        plugins = self._discover()["plugins"]
        try:
            if (data["format_version"] != 1 or data["sample_rate"] != 48000 or data["bit_depth"] != "Int24" or
                    data["sources"] or data["videos"] or data["busses"]):
                raise AdapterError("native inspection supports self-contained 48 kHz / 24-bit MIDI sessions only")
            for track in data["tracks"]:
                if (track["kind"] != "Instrument" or track["instrument"]["plugin"] not in plugins or
                        not plugins[track["instrument"]["plugin"]]["instrument"]):
                    raise AdapterError("external/native non-instrument tracks are unsupported")
                if track["instrument"]["plugin"] == "sampler":
                    raise AdapterError("sampler assets are unsupported")
                for effect in track["mixer"]["inserts"]:
                    if effect is not None and (effect["plugin"] not in plugins or plugins[effect["plugin"]]["instrument"]):
                        raise AdapterError("external plugins are unsupported")
                for playlist in track["playlists"]:
                    for clip in playlist["clips"]:
                        if set(clip["content"]) != {"Midi"}:
                            raise AdapterError("only native MIDI clips are supported")
        except (KeyError, TypeError) as exc:
            raise AdapterError("invalid native session structure") from exc
        return path, data

    def inspect(self, source):
        path, native = self._native(source)
        before = path.read_bytes()
        with tempfile.TemporaryDirectory(prefix="kuang-sc-inspect-") as directory:
            host = self._run([("session.inspect", {"detail": "full"})], directory, source=path)[0]
        if before != path.read_bytes():
            raise AdapterError("source changed during read-only inspection")
        try:
            if len(host["tracks"]) != len(native["tracks"]) or host["sample_rate"] != native["sample_rate"]:
                raise AdapterError("host inspection disagrees with native state")
            for track, summary in zip(native["tracks"], host["tracks"]):
                clips = track["playlists"][track["active_playlist"]]["clips"]
                if summary["id"] != track["id"] or [c["notes"] for c in summary["clips"]] != [len(c["content"]["Midi"]["sequence"]["notes"]) for c in clips]:
                    raise AdapterError("host MIDI inspection disagrees with persisted notes")
        except (KeyError, TypeError) as exc:
            raise AdapterError("invalid host inspection JSON") from exc
        return {"native": native, "host": host, "native_hash": _hash(native),
                "native_file_sha256": hashlib.sha256(before).hexdigest()}

    @staticmethod
    def _samples(project, tick):
        return round(tick * 48000 * 60 / (project.ppq * project.tempo_bpm))

    def _verify_project(self, project, native):
        """Every mapped note field, base control, device and automation value is checked."""
        def require(ok, message):
            if not ok:
                raise AdapterError("native verification: " + message)

        require(len(native["tracks"]) == len(project.tracks), "track count")
        require(native["tempo"]["tempos"] == [{"tick": 0, "bpm": project.tempo_bpm}], "exact tempo")
        require(native["tempo"]["meters"] == [{"tick": 0, "numerator": 4, "denominator": 4}], "meter")
        identities = {"tracks": {}, "notes": {}, "automation": {}}
        for track, host in zip(project.tracks, native["tracks"]):
            require(host["name"] == track.name and host["active_playlist"] == 0 and len(host["playlists"]) == 1, "track identity/playlists")
            clips = host["playlists"][0]["clips"]
            require(len(clips) == 1 and clips[0]["start"] == 0, "expected one imported clip at zero")
            notes = clips[0]["content"]["Midi"]["sequence"]["notes"]
            fingerprint = lambda n: (n["start"], n["length"], n["pitch"], n["velocity"], n["channel"])
            expected = [(c.start+n.start, n.duration, n.pitch, n.velocity, n.channel) for c in track.clips for n in c.notes]
            require(Counter(map(fingerprint, notes)) == Counter(expected), "full note pitch/timing/duration/velocity/channel equality")
            require(all(n["release_velocity"] == 0 for n in notes), "unexpected note release velocities")
            require(not clips[0]["content"]["Midi"]["sequence"]["ctrls"], "unexpected MIDI controllers")
            indexes = {fingerprint(n): i for i, n in enumerate(notes)}
            identities["tracks"][track.id] = host["id"]
            for clip in track.clips:
                for note in clip.notes:
                    key = (clip.start+note.start, note.duration, note.pitch, note.velocity, note.channel)
                    identities["notes"][note.id] = {"native_clip_id": clips[0]["id"], "index": indexes[key], "kuang_clip_id": clip.id}
            controls = track.controls
            require(_close(host["mixer"]["volume_db"], controls["mixer.gain_db"]), "gain")
            require(all(_close(p, controls["mixer.pan"]) for p in host["mixer"]["pan"]), "linked stereo pan")
            require(host["mixer"]["mute"] is bool(controls["mixer.mute"]), "mute")
            require(host["mixer"]["output"] == "Main" and not any(host["mixer"]["sends"]), "master routing")
            devices = [(track.instrument, host["instrument"], self._device(track))]
            require(sum(e is not None for e in host["mixer"]["inserts"]) == len(track.effects), "FX count")
            devices += [(effect, host["mixer"]["inserts"][slot], effect.plugin_ref.removeprefix("soundcraft:")) for slot, effect in enumerate(track.effects)]
            for config, device, plugin in devices:
                require(device is not None and device["plugin"] == plugin and device["active"], "built-in device")
                supplied = dict(self._parameter(project, config, plugin, p, v) for p, v in config.parameters.items())
                require(device["bypass"] is supplied.pop("bypass", False), "device bypass")
                defaults = {p["id"]: p["default"] for p in self._discover()["plugins"][plugin]["params"]}
                require(set(supplied) <= set(device["params"]) <= set(defaults), "device parameter keys")
                for parameter, value in device["params"].items():
                    require(_close(value, supplied.get(parameter, defaults[parameter])), "device parameter value: " + parameter)
        for lane in project.automation:
            index, mapped = self._lane(project, lane)
            entries = []
            for _, native_param, points in mapped:
                matches = [a for a in native["tracks"][index]["automation"] if a["param"] == native_param]
                require(len(matches) == 1 or (not points and not matches), "automation lane identity")
                observed = matches[0]["points"] if matches else []
                require(len(observed) == len(points), "automation point count")
                for actual, (_, tick, value) in zip(observed, points):
                    require(actual["at"] == self._samples(project, tick) and _close(actual["value"], value), "automation time/value")
                entries.append({"native_param": native_param, "point_indices": {p[0]: i for i, p in enumerate(points)}})
            identities["automation"][lane.id] = entries
        for index, host in enumerate(native["tracks"]):
            allowed = [_json(param) for lane in project.automation for i, mappings in [self._lane(project, lane)]
                       if i == index for _, param, _ in mappings]
            observed = [_json(lane["param"]) for lane in host["automation"]]
            require(len(observed) == len(set(observed)) and set(observed) <= set(allowed), "unexpected/duplicate automation lanes")
        return identities

    def _load_bundle(self, source):
        path, native = self._native(source)
        project = load(path.parent / "project.kuang.json")
        manifest = _read_json(path.parent / "manifest.json")
        if type(manifest) is not dict:
            raise AdapterError("invalid bundle manifest")
        self._require(project)
        if (manifest.get("version") != "1" or manifest.get("soundcraft_version") != HOST_VERSION or
                manifest.get("contract_hash") != _hash(self._discover()) or
                manifest.get("executable_sha256") != hashlib.sha256(self.executable.read_bytes()).hexdigest() or
                manifest.get("canonical_hash") != state_hash(project) or manifest.get("native_hash") != _hash(native) or
                manifest.get("native_file_sha256") != hashlib.sha256(path.read_bytes()).hexdigest()):
            raise AdapterError("bundle drift or invalid provenance; automatic reconciliation is not supported")
        if manifest.get("identities") != self._verify_project(project, native):
            raise AdapterError("bundle identity map mismatch")
        return path, project, native

    def import_project(self, source):
        path, project, native = self._load_bundle(source)
        inspection = self.inspect(path)
        if inspection["native"] != native:
            raise AdapterError("native changed while importing")
        return project

    def _publish(self, stage, destination, project, native_path, report):
        inspection = self.inspect(native_path)
        identities = self._verify_project(project, inspection["native"])
        shutil.copyfile(native_path, stage / "session.scraft")
        save(project, stage / "project.kuang.json")
        _write_json(stage / "inspection.json", inspection)
        manifest = {"version": "1", "soundcraft_version": HOST_VERSION, "canonical_hash": state_hash(project),
                    "contract_hash": _hash(self._discover()), "executable_sha256": hashlib.sha256(self.executable.read_bytes()).hexdigest(),
                    "native_hash": inspection["native_hash"], "native_file_sha256": inspection["native_file_sha256"], "identities": identities}
        _write_json(stage / "manifest.json", manifest)
        report = {**report, "canonical_hash": state_hash(project), "native_hash": inspection["native_hash"],
                  "note_count": len(identities["notes"]), "tracks": len(project.tracks), "verified": True,
                  "output": str(destination)}
        _write_json(stage / "report.json", report)
        if destination.exists():
            raise AdapterError("output already exists; choose a new bundle path")
        os.rename(stage, destination)
        return report

    def _destination(self, destination, source=None):
        destination = _path(destination)
        if destination.exists() or destination.is_symlink():
            raise AdapterError("output already exists; choose a new path (no overwrite mode)")
        if source and destination.is_relative_to(_path(source).parent):
            raise AdapterError("derived output must be outside the source bundle")
        destination.parent.mkdir(parents=True, exist_ok=True)
        return destination

    def _reopen(self, path, directory):
        before = _read_json(path)
        reopened = Path(directory) / "reopen" / "session.scraft"
        reopened.parent.mkdir()
        self._run([("session.inspect", {"detail": "full"})], directory, source=path, destination=reopened)
        if _read_json(reopened) != before:
            raise AdapterError("save/reopen changed persistent native state")
        return reopened

    def _automation_commands(self, project, lane, native):
        index, mappings = self._lane(project, lane)
        commands = []
        for parameter, _, points in mappings:
            commands.append(("automation.clear", {"track": native["tracks"][index]["id"], "param": parameter,
                                                  "start": 0, "end": self._samples(project, project.length)+1}))
            commands.extend(("automation.set_point", {"track": native["tracks"][index]["id"], "param": parameter,
                                                       "at": self._samples(project, tick), "value": value}) for _, tick, value in points)
        return commands

    def export(self, project, destination):
        report = self._require(project)
        destination = self._destination(destination)
        with tempfile.TemporaryDirectory(prefix=".kuang-sc-", dir=destination.parent) as directory:
            work = Path(directory)
            (work / "publish").mkdir()
            mid = work / "source.mid"
            midi.export(project, mid)
            native_path = work / "session.scraft"
            self._run([("session.new", {"sample_rate": 48000, "bit_depth": 24}), ("file.import_midi", {"path": str(mid)}),
                       ("event.tempo", {"bpm": project.tempo_bpm, "at": 0})], work, destination=native_path)
            baseline = _read_json(native_path)
            if len(baseline["tracks"]) != len(project.tracks):
                raise AdapterError("MIDI import did not produce the expected tracks")
            commands = []
            for track, host in zip(project.tracks, baseline["tracks"]):
                target = host["id"]
                for parameter, (command, arg, _) in MIXER.items():
                    value = bool(track.controls[parameter]) if parameter == "mixer.mute" else track.controls[parameter]
                    commands.append((command, {"track": target, arg: value}))
                    if parameter == "mixer.pan":
                        commands[-1][1]["index"] = 0
                        commands.append((command, {"track": target, arg: value, "index": 1}))
                plugin = self._device(track)
                params = dict(self._parameter(project, track.instrument, plugin, p, v) for p, v in track.instrument.parameters.items())
                commands.append(("mix.instrument", {"track": target, "plugin": plugin, "params": params}))
                commands.append(("track.comments", {"track": target, "comments": _json({"kuang_track_id": track.id})}))
                for slot, effect in enumerate(track.effects):
                    plugin = effect.plugin_ref.removeprefix("soundcraft:")
                    params = dict(self._parameter(project, effect, plugin, p, v) for p, v in effect.parameters.items())
                    bypass = params.pop("bypass", False)
                    commands += [("mix.insert", {"track": target, "slot": slot, "plugin": plugin, "params": params}),
                                 ("mix.insert_bypass", {"track": target, "slot": slot, "value": bypass})]
            for lane in project.automation:
                commands += self._automation_commands(project, lane, baseline)
            for section in project.sections:
                commands.append(("markers.add", {"name": section.name, "start": self._samples(project, section.start),
                                                 "end": self._samples(project, section.start+section.length), "kind": "selection"}))
            self._run(commands, work, source=native_path, destination=native_path)
            after = _read_json(native_path)
            expected = deepcopy(baseline)
            for old, new in zip(expected["tracks"], after["tracks"]):
                for key in ("instrument", "automation", "comments"):
                    old[key] = deepcopy(new[key])
                for key in ("volume_db", "pan", "mute", "inserts"):
                    old["mixer"][key] = deepcopy(new["mixer"][key])
            expected["markers"], expected["next_id"] = after["markers"], after["next_id"]
            if expected != after:
                raise AdapterError("export changed state outside the mapped fields")
            self._verify_project(project, after)
            if len(after["markers"]) != len(project.sections) or any(
                    m["name"] != s.name or m["start"] != self._samples(project, s.start) or m["end"] != self._samples(project, s.start+s.length)
                    for m, s in zip(after["markers"], project.sections)):
                raise AdapterError("section markers differ from canonical sections")
            reopened = self._reopen(native_path, work)
            return self._publish(work / "publish", destination, project, reopened, {"action": "export", "capabilities": report})

    def save(self, source, destination):
        path, project, _ = self._load_bundle(source)
        destination = self._destination(destination, path)
        original = path.read_bytes()
        with tempfile.TemporaryDirectory(prefix=".kuang-sc-", dir=destination.parent) as directory:
            work = Path(directory)
            (work / "publish").mkdir()
            shutil.copyfile(path, work / "session.scraft")
            reopened = self._reopen(work / "session.scraft", work)
            if path.read_bytes() != original:
                raise AdapterError("source changed during save")
            return self._publish(work / "publish", destination, project, reopened, {"action": "save"})

    def apply(self, source, destination, operations, scope, expected_before_hash):
        path, project, before = self._load_bundle(source)
        engine = Engine(project)
        receipt = engine.apply(operations, scope, expected_before_hash)
        candidate = engine.project
        self._require(candidate)
        if any(type(op) not in (SetParameter, AddAutomationPoints, DeleteAutomationPoints) for op in operations):
            raise AdapterError("native apply supports parameter and automation edits only; note edits require a fresh export")
        destination = self._destination(destination, path)
        original = path.read_bytes()
        with tempfile.TemporaryDirectory(prefix=".kuang-sc-", dir=destination.parent) as directory:
            work = Path(directory)
            (work / "publish").mkdir()
            native_path = work / "session.scraft"
            shutil.copyfile(path, native_path)
            commands, mutations = [], []
            target_pairs = list(dict.fromkeys((op.target_id, op.parameter_id) for op in operations if isinstance(op, SetParameter)))
            for target, parameter in target_pairs:
                for index, track in enumerate(candidate.tracks):
                    native_id = before["tracks"][index]["id"]
                    if target == track.id:
                        command, arg, key = MIXER[parameter]
                        value = bool(track.controls[parameter]) if parameter == "mixer.mute" else track.controls[parameter]
                        commands.append((command, {"track": native_id, arg: value}))
                        if key == "pan":
                            commands[-1][1]["index"] = 0
                            commands.append((command, {"track": native_id, arg: value, "index": 1}))
                        mutations.append((index, ["mixer", key], [value, value] if key == "pan" else value))
                    elif target == track.instrument.id:
                        raise AdapterError("native apply does not yet edit instrument parameters; use a fresh export")
                    for slot, effect in enumerate(track.effects):
                        if target == effect.id:
                            name, value = self._parameter(candidate, effect, effect.plugin_ref.removeprefix("soundcraft:"), parameter, effect.parameters[parameter])
                            if name == "bypass":
                                commands.append(("mix.insert_bypass", {"track": native_id, "slot": slot, "value": value}))
                                mutations.append((index, ["mixer", "inserts", slot, "bypass"], value))
                            else:
                                commands.append(("mix.insert_params", {"track": native_id, "slot": slot, "params": {name: value}}))
                                mutations.append((index, ["mixer", "inserts", slot, "params", name], value))
            lanes = [lane for lane in candidate.automation if lane.id in {op.lane_id for op in operations if isinstance(op, (AddAutomationPoints, DeleteAutomationPoints))}]
            for lane in lanes:
                commands += self._automation_commands(candidate, lane, before)
            self._run(commands, work, source=native_path, destination=native_path)
            after, expected = _read_json(native_path), deepcopy(before)
            for index, keys, value in mutations:
                target, actual = expected["tracks"][index], after["tracks"][index]
                for key in keys[:-1]:
                    target, actual = target[key], actual[key]
                observed = actual[keys[-1]]
                if type(value) is bool:
                    valid = observed is value
                elif isinstance(value, list):
                    valid = type(observed) is list and len(observed) == len(value) and all(_close(a, b) for a, b in zip(observed, value))
                else:
                    valid = _close(observed, value)
                if not valid:
                    raise AdapterError("requested native parameter value did not persist")
                target[keys[-1]] = observed
            for lane in lanes:
                index, mappings = self._lane(candidate, lane)
                for _, param, points in mappings:
                    old_lanes = expected["tracks"][index]["automation"]
                    observed = next((x for x in after["tracks"][index]["automation"] if x["param"] == param), None)
                    if observed is None or len(observed["points"]) != len(points) or not observed["enabled"]:
                        raise AdapterError("automation replacement failed")
                    old = next((x for x in old_lanes if x["param"] == param), None)
                    prior = {p["at"]: p["value"] for p in old["points"]} if old else {}
                    replacement = {"param": param, "points": [], "enabled": True}
                    for actual, (_, tick, value) in zip(observed["points"], points):
                        at = self._samples(candidate, tick)
                        if actual["at"] != at or not _close(actual["value"], value):
                            raise AdapterError("automation time/value verification failed")
                        # Rewriting a lane must retain exact serialized values of unchanged points.
                        previous = next((p for p in project.automation if p.id == lane.id), None)
                        old_point = next((p for p in previous.points if p.tick == tick), None) if previous else None
                        new_point = next(p for p in lane.points if p.tick == tick)
                        exact = prior.get(at, actual["value"]) if old_point and old_point.value == new_point.value else actual["value"]
                        replacement["points"].append({"at": at, "value": exact})
                    if old is None:
                        old_lanes.append(replacement)
                    else:
                        old_lanes[old_lanes.index(old)] = replacement
            if after != expected:
                raise AdapterError("collateral native change detected; staged edit discarded")
            self._verify_project(candidate, after)
            reopened = self._reopen(native_path, work)
            if original != path.read_bytes():
                raise AdapterError("source changed during transaction")
            _write_json(work / "publish" / "receipt.json", asdict(receipt))
            return self._publish(work / "publish", destination, candidate, reopened,
                                 {"action": "apply", "before_hash": receipt.before_hash, "after_hash": receipt.after_hash,
                                  "full_native_preservation": True})

    def render(self, source, output, *, end_seconds=None):
        path, project, before = self._load_bundle(source)
        output = self._destination(output, path)
        if output.suffix.lower() != ".wav":
            raise AdapterError("render output must be .wav")
        end = project.length / project.ppq * 60 / project.tempo_bpm + 1 if end_seconds is None else end_seconds
        if type(end) not in (int, float) or not math.isfinite(end) or not 0 < end <= 600:
            raise AdapterError("render end must be >0 and <=600 seconds")
        original = path.read_bytes()
        with tempfile.TemporaryDirectory(prefix=".kuang-sc-render-", dir=output.parent) as directory:
            work = Path(directory)
            native_path = work / "session.scraft"
            shutil.copyfile(path, native_path)
            wav = work / "render.wav"
            self._run([("file.bounce_mix", {"path": str(wav), "format": "wav", "bit_depth": 24,
                                           "start": {"seconds": 0}, "end": {"seconds": end}, "dither": False})],
                      work, source=native_path, destination=native_path)
            if _read_json(native_path) != before or path.read_bytes() != original:
                raise AdapterError("render changed native project state")
            analysis = analyze_wav(wav)
            if (analysis["sample_rate"], analysis["channels"], analysis["bits_per_sample"]) != (48000, 2, 24) or abs(analysis["duration_seconds"]-end) > 1/48000:
                raise AdapterError("unexpected WAV format/duration")
            # Hard-link publication is atomic and fails if another writer created the output.
            os.link(wav, output)
            return {"action": "render", "output": str(output), "canonical_hash": state_hash(project), "analysis": analysis,
                    "wav_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "native_unchanged": True}
