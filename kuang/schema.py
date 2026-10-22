"""Versioned, strict project model. All time values are integer ticks at 960 PPQ."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import types
from dataclasses import asdict, dataclass, fields, is_dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal, Union, get_args, get_origin, get_type_hints

VERSION = "0.1"
PPQ = 960
BAR = 4 * PPQ


class ValidationError(ValueError):
    """Invalid or unsupported project or request."""


@dataclass
class ParameterSpec:
    id: str
    unit: Literal["dB", "pan", "normalized", "Hz", "ms", "boolean"]
    minimum: float
    maximum: float
    default: float
    targets: list[Literal["track", "instrument", "effect"]]


@dataclass
class Note:
    id: str
    start: int
    duration: int
    pitch: int
    velocity: int
    channel: int


@dataclass
class Clip:
    id: str
    name: str
    kind: Literal["midi", "audio"]
    start: int
    length: int
    notes: list[Note]
    source_ref: str | None


@dataclass
class Instrument:
    id: str
    kind: Literal["midi", "plugin"]
    plugin_ref: str | None
    preset_ref: str | None
    midi_program: int | None
    parameters: dict[str, float]


@dataclass
class Effect:
    id: str
    plugin_ref: str
    preset_ref: str | None
    parameters: dict[str, float]


@dataclass
class Send:
    id: str
    target_track_id: str
    gain_db: float
    pan: float
    mode: Literal["post_fader", "pre_fader"]


@dataclass
class Track:
    id: str
    name: str
    kind: Literal["midi", "audio", "bus"]
    instrument: Instrument | None
    controls: dict[str, float]
    effects: list[Effect]
    clips: list[Clip]
    sends: list[Send]
    output_master: bool


@dataclass
class Section:
    id: str
    name: str
    start: int
    length: int


@dataclass
class AutomationPoint:
    id: str
    tick: int
    value: float
    shape: Literal["linear", "step"]


@dataclass
class AutomationLane:
    id: str
    target_id: str
    parameter_id: str
    points: list[AutomationPoint]


@dataclass
class Lock:
    id: str
    target_id: str
    parameter_id: str | None


@dataclass
class Project:
    version: str
    id: str
    name: str
    tempo_bpm: float
    key_tonic: int
    key_mode: Literal["minor", "major"]
    time_signature: list[int]
    ppq: int
    bars: int
    sections: list[Section]
    parameters: list[ParameterSpec]
    tracks: list[Track]
    automation: list[AutomationLane]
    locks: list[Lock]
    metadata: dict[str, str]

    @property
    def length(self) -> int:
        return self.bars * BAR


def standard_parameters() -> list[ParameterSpec]:
    return [
        ParameterSpec("mixer.gain_db", "dB", -90, 12, 0, ["track"]),
        ParameterSpec("mixer.pan", "pan", -1, 1, 0, ["track"]),
        ParameterSpec("mixer.mute", "boolean", 0, 1, 0, ["track"]),
        ParameterSpec("synth.cutoff_hz", "Hz", 20, 20000, 1800, ["instrument"]),
        ParameterSpec("synth.resonance", "normalized", 0, 1, 0.15, ["instrument"]),
        ParameterSpec("effect.wet", "normalized", 0, 1, 1, ["effect"]),
        ParameterSpec("effect.bypass", "boolean", 0, 1, 0, ["effect"]),
    ]


@lru_cache(maxsize=None)
def _hints(cls):
    return get_type_hints(cls)


def decode(cls, data, path: str = "$"):
    """Strict recursive decoder shared by projects and operation envelopes."""
    origin, args = get_origin(cls), get_args(cls)
    if origin in (Union, types.UnionType):
        for alternative in args:
            try:
                return decode(alternative, data, path)
            except ValidationError:
                pass
        raise ValidationError(f"{path}: expected {cls}")
    if origin is Literal:
        if data not in args or type(data) not in {type(x) for x in args}:
            raise ValidationError(f"{path}: expected one of {args}")
        return data
    if is_dataclass(cls):
        if type(data) is not dict:
            raise ValidationError(f"{path}: expected object")
        expected = {f.name for f in fields(cls)}
        if set(data) != expected:
            raise ValidationError(f"{path}: missing {sorted(expected - set(data))}, unknown {sorted(set(data) - expected)}")
        hints = _hints(cls)
        return cls(**{k: decode(hints[k], v, f"{path}.{k}") for k, v in data.items()})
    if origin is list:
        if type(data) is not list:
            raise ValidationError(f"{path}: expected array")
        return [decode(args[0], v, f"{path}[{i}]") for i, v in enumerate(data)]
    if origin is dict:
        if type(data) is not dict:
            raise ValidationError(f"{path}: expected object")
        return {decode(args[0], k, path): decode(args[1], v, f"{path}.{k}") for k, v in data.items()}
    if cls is float:
        try:
            finite = type(data) in (int, float) and math.isfinite(data)
        except OverflowError:
            finite = False
        if not finite:
            raise ValidationError(f"{path}: expected finite number")
        return float(data)
    if cls is type(None):
        if data is not None:
            raise ValidationError(f"{path}: expected null")
    elif type(data) is not cls:
        raise ValidationError(f"{path}: expected {cls.__name__}")
    if cls is str:
        try:
            data.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValidationError(f"{path}: string must be valid UTF-8") from exc
    return data


def strict_json(text: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValidationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValidationError(f"invalid JSON number: {x}")))
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValidationError(f"invalid JSON: {exc}") from exc


def targets(project: Project) -> dict[str, tuple[str, str, dict[str, float]]]:
    """target ID -> (kind, owning track ID, explicit parameter values)."""
    result = {}
    for track in project.tracks:
        result[track.id] = ("track", track.id, track.controls)
        if track.instrument:
            result[track.instrument.id] = ("instrument", track.id, track.instrument.parameters)
        for effect in track.effects:
            result[effect.id] = ("effect", track.id, effect.parameters)
    return result


def validate(project: Project) -> None:
    decode(Project, asdict(project))  # Also validates callers constructing dataclasses directly.

    def require(condition, message):
        if not condition:
            raise ValidationError(message)

    require(project.version == VERSION, "unsupported schema version; migration required")
    require(project.ppq == PPQ and project.time_signature == [4, 4], "Phase 0 requires 960 PPQ and 4/4")
    require(20 <= project.tempo_bpm <= 300, "tempo outside 20..300 BPM")
    require(0 <= project.key_tonic <= 11 and 1 <= project.bars <= 4096, "invalid key or project length")
    seen = set()

    def identity(obj):
        require(bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", obj.id)), f"invalid ID: {obj.id}")
        require(obj.id not in seen, f"duplicate ID: {obj.id}")
        seen.add(obj.id)

    identity(project)
    specs = {}
    for spec in project.parameters:
        identity(spec)
        require(spec.minimum <= spec.default <= spec.maximum and spec.minimum < spec.maximum, f"invalid range: {spec.id}")
        require(bool(spec.targets) and len(spec.targets) == len(set(spec.targets)), "invalid parameter targets")
        if spec.unit == "boolean":
            require((spec.minimum, spec.maximum) == (0, 1) and spec.default in (0, 1), "boolean range must be 0..1")
        specs[spec.id] = spec
    # Host-independent mixer semantics cannot be redefined by a session.
    for spec in standard_parameters()[:3]:
        require(specs.get(spec.id) == spec, f"required mixer registry definition: {spec.id}")

    def value(parameter, number, kind):
        require(parameter in specs, f"unregistered parameter: {parameter}")
        spec = specs[parameter]
        require(kind in spec.targets and spec.minimum <= number <= spec.maximum, f"parameter target/range: {parameter}")
        require(spec.unit != "boolean" or number in (0, 1), f"boolean parameter: {parameter}")

    cursor = 0
    for section in project.sections:
        identity(section)
        require(section.start == cursor and section.length > 0 and section.start % BAR == 0 and section.length % BAR == 0,
                "sections must partition the timeline on bar boundaries")
        cursor += section.length
    require(cursor == project.length, "sections must cover project length")
    track_ids = {track.id for track in project.tracks}
    for track in project.tracks:
        identity(track)
        require(set(track.controls) >= {"mixer.gain_db", "mixer.pan", "mixer.mute"}, "missing mixer controls")
        require((track.kind == "midi") == (track.instrument is not None), "only MIDI tracks require an instrument")
        if track.instrument:
            inst = track.instrument
            identity(inst)
            require(inst.midi_program is None or 0 <= inst.midi_program <= 127, "MIDI program outside 0..127")
            require((inst.kind == "plugin") == bool(inst.plugin_ref), "plugin instrument needs a plugin_ref; MIDI instrument has none")
        for effect in track.effects:
            identity(effect)
            require(bool(effect.plugin_ref), "empty effect plugin reference")
        intervals = {}
        for clip in track.clips:
            identity(clip)
            require(track.kind == clip.kind, "clip type must match its track; buses have no clips")
            require(clip.start >= 0 and clip.length > 0 and clip.start + clip.length <= project.length, "clip outside project")
            require((clip.kind == "audio") == bool(clip.source_ref), "audio clip needs source_ref; MIDI clip has none")
            require(clip.kind == "midi" or not clip.notes, "audio clip cannot contain MIDI notes")
            for note in clip.notes:
                identity(note)
                require(0 <= note.start < clip.length and note.duration > 0 and note.start + note.duration <= clip.length, "note outside clip")
                require(0 <= note.pitch <= 127 and 1 <= note.velocity <= 127 and 0 <= note.channel <= 15, "invalid MIDI note data")
                intervals.setdefault((note.channel, note.pitch), []).append((clip.start + note.start, clip.start + note.start + note.duration))
        for group in intervals.values():
            group.sort()
            require(all(a[1] <= b[0] for a, b in zip(group, group[1:])), "overlapping same-pitch/channel notes on track")
        for send in track.sends:
            identity(send)
            require(send.target_track_id in track_ids and send.target_track_id != track.id, "invalid send destination")
            require(-90 <= send.gain_db <= 12 and -1 <= send.pan <= 1, "invalid send gain/pan")
    target_map = targets(project)
    for kind, _, controls in target_map.values():
        for parameter, number in controls.items():
            value(parameter, number, kind)
    pairs = set()
    for lane in project.automation:
        identity(lane)
        require(lane.target_id in target_map, "unknown automation target")
        kind, _, controls = target_map[lane.target_id]
        require(lane.parameter_id in controls, "automation requires an explicit base parameter")
        pair = (lane.target_id, lane.parameter_id)
        require(pair not in pairs, "duplicate automation lane for parameter")
        pairs.add(pair)
        ticks = set()
        for point in lane.points:
            identity(point)
            require(0 <= point.tick <= project.length and point.tick not in ticks, "invalid/duplicate automation tick")
            ticks.add(point.tick)
            value(lane.parameter_id, point.value, kind)
            require(specs[lane.parameter_id].unit != "boolean" or point.shape == "step", "boolean automation must use step")
    clip_ids = {clip.id for track in project.tracks for clip in track.clips}
    for lock in project.locks:
        identity(lock)
        require(lock.target_id in target_map or lock.target_id in clip_ids, "unknown lock target")
        if lock.parameter_id is not None:
            require(lock.target_id in target_map and lock.parameter_id in target_map[lock.target_id][2], "unknown locked parameter")
    graph = {t.id: [s.target_track_id for s in t.sends] for t in project.tracks}
    visiting, visited = set(), set()

    def visit(node):
        require(node not in visiting, "routing cycle")
        if node in visited:
            return
        visiting.add(node)
        for target in graph[node]:
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def dumps(project: Project) -> str:
    validate(project)
    # JSON numbers have one canonical form even if callers supplied integers for floats.
    normalized = decode(Project, asdict(project))
    return json.dumps(asdict(normalized), sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def loads(text: str) -> Project:
    project = decode(Project, strict_json(text))
    validate(project)
    return project


def state_hash(project: Project) -> str:
    return hashlib.sha256(dumps(project).encode("utf-8")).hexdigest()


def atomic_write(path: str | Path, data: bytes) -> None:
    """Same-directory replace: readers see either the old or complete new file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save(project: Project, path: str | Path) -> None:
    atomic_write(path, dumps(project).encode("utf-8"))


def load(path: str | Path) -> Project:
    return loads(Path(path).read_text(encoding="utf-8"))
