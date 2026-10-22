"""Typed, scoped, atomic edits. No model output is executable code."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Literal

from .schema import (AutomationPoint, Note, Project, ValidationError, decode,
                     state_hash, targets, validate)


class ScopeError(ValidationError):
    pass


class LockedError(ValidationError):
    pass


@dataclass
class Scope:
    track_ids: list[str]
    clip_ids: list[str]
    parameter_ids: list[str]
    start: int | None
    end: int | None


@dataclass
class SetParameter:
    op: Literal["set_parameter"]
    target_id: str
    parameter_id: str
    value: float


@dataclass
class AddNotes:
    op: Literal["add_notes"]
    clip_id: str
    notes: list[Note]


@dataclass
class UpdateNote:
    op: Literal["update_note"]
    clip_id: str
    note: Note


@dataclass
class RemoveNotes:
    op: Literal["remove_notes"]
    clip_id: str
    note_ids: list[str]


@dataclass
class ReplaceNotesInRegion:
    op: Literal["replace_notes_in_region"]
    clip_id: str
    start: int
    end: int
    notes: list[Note]


@dataclass
class AddAutomationPoints:
    op: Literal["add_automation_points"]
    lane_id: str
    points: list[AutomationPoint]


@dataclass
class DeleteAutomationPoints:
    op: Literal["delete_automation_points"]
    lane_id: str
    point_ids: list[str]


@dataclass
class RestoreNotes:
    """Engine-generated inverse; restores exact order as well as values."""
    op: Literal["restore_notes"]
    clip_id: str
    notes: list[Note]


@dataclass
class RestoreAutomation:
    op: Literal["restore_automation"]
    lane_id: str
    points: list[AutomationPoint]


Operation = (SetParameter | AddNotes | UpdateNote | RemoveNotes | ReplaceNotesInRegion |
             AddAutomationPoints | DeleteAutomationPoints | RestoreNotes | RestoreAutomation)
PUBLIC_OPERATIONS = {
    "set_parameter": SetParameter, "add_notes": AddNotes, "update_note": UpdateNote,
    "remove_notes": RemoveNotes, "replace_notes_in_region": ReplaceNotesInRegion,
    "add_automation_points": AddAutomationPoints, "delete_automation_points": DeleteAutomationPoints,
}
INVERSE_OPERATIONS = {**PUBLIC_OPERATIONS, "restore_notes": RestoreNotes, "restore_automation": RestoreAutomation}


def parse_operations(data, *, inverses=False) -> list[Operation]:
    if type(data) is not list:
        raise ValidationError("operations must be an array")
    classes = INVERSE_OPERATIONS if inverses else PUBLIC_OPERATIONS
    result = []
    for item in data:
        if type(item) is not dict or type(item.get("op")) is not str or item["op"] not in classes:
            raise ValidationError("unknown operation")
        result.append(decode(classes[item["op"]], item))
    return result


@dataclass
class Receipt:
    version: str
    before_hash: str
    after_hash: str
    scope: Scope
    operations: list[Operation]
    inverse: list[Operation]


def receipt_from_dict(data) -> Receipt:
    if type(data) is not dict or set(data) != {"version", "before_hash", "after_hash", "scope", "operations", "inverse"}:
        raise ValidationError("invalid receipt fields")
    if data["version"] != "0.1":
        raise ValidationError("unsupported receipt version")
    for name in ("before_hash", "after_hash"):
        digest = data[name]
        if type(digest) is not str or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValidationError("invalid receipt hash")
    return Receipt(data["version"], data["before_hash"], data["after_hash"], decode(Scope, data["scope"]),
                   parse_operations(data["operations"]), parse_operations(data["inverse"], inverses=True))


def _check_scope(project: Project, scope: Scope):
    decode(Scope, asdict(scope))
    tracks = {t.id for t in project.tracks}
    clips = {c.id for t in project.tracks for c in t.clips if t.id in scope.track_ids}
    parameters = {s.id for s in project.parameters}
    for values, allowed in ((scope.track_ids, tracks), (scope.clip_ids, clips), (scope.parameter_ids, parameters)):
        if len(values) != len(set(values)) or not set(values) <= allowed:
            raise ScopeError("scope contains duplicate or unknown IDs (clips must belong to allowed tracks)")
    if not scope.track_ids:
        raise ScopeError("scope must explicitly allow a track")
    if (scope.start is None) != (scope.end is None):
        raise ScopeError("scope requires both start and end or neither")
    if scope.start is not None and not 0 <= scope.start < scope.end <= project.length:
        raise ScopeError("invalid absolute tick scope")


def _authorize(project, scope, track_id, target_id, parameter_id=None, interval=None):
    if track_id not in scope.track_ids:
        raise ScopeError(f"track outside scope: {track_id}")
    if parameter_id is None:
        if target_id not in scope.clip_ids:
            raise ScopeError(f"clip outside scope: {target_id}")
    elif parameter_id not in scope.parameter_ids:
        raise ScopeError(f"parameter outside scope: {parameter_id}")
    if scope.start is not None:
        if interval is None:
            raise ScopeError("base parameter edits cannot have a time-limited scope")
        start, end = interval
        if start < scope.start or end > scope.end or start >= scope.end:
            raise ScopeError("edit outside absolute tick scope")
    for lock in project.locks:
        if lock.target_id in {track_id, target_id} and (lock.parameter_id is None or lock.parameter_id == parameter_id):
            raise LockedError(f"locked: {lock.target_id}/{lock.parameter_id or '*'}")


def _changed(before, after):
    old, new = {x.id: x for x in before}, {x.id: x for x in after}
    return [x for x in before if new.get(x.id) != x] + [x for x in after if old.get(x.id) != x]


def _apply(project: Project, operation: Operation, scope: Scope) -> Operation:
    # Direct Python callers receive the same strict field/type checks as JSON callers.
    cls = INVERSE_OPERATIONS.get(getattr(operation, "op", None))
    if cls is None or type(operation) is not cls:
        raise ValidationError("unknown typed operation")
    operation = decode(cls, asdict(operation))
    if isinstance(operation, SetParameter):
        target = targets(project).get(operation.target_id)
        if target is None or operation.parameter_id not in target[2]:
            raise ValidationError("parameter target must already exist")
        _, track_id, controls = target
        _authorize(project, scope, track_id, operation.target_id, operation.parameter_id)
        inverse = SetParameter("set_parameter", operation.target_id, operation.parameter_id, controls[operation.parameter_id])
        controls[operation.parameter_id] = operation.value
        return inverse
    if isinstance(operation, (AddNotes, UpdateNote, RemoveNotes, ReplaceNotesInRegion, RestoreNotes)):
        found = [(t, c) for t in project.tracks for c in t.clips if c.id == operation.clip_id]
        if not found or found[0][1].kind != "midi":
            raise ValidationError("unknown MIDI clip")
        track, clip = found[0]
        # Check even no-op requests against track/clip locks and permissions.
        if track.id not in scope.track_ids or clip.id not in scope.clip_ids:
            raise ScopeError("note target outside scope")
        for lock in project.locks:
            if lock.target_id in (track.id, clip.id) and lock.parameter_id is None:
                raise LockedError(f"locked: {lock.target_id}")
        before = deepcopy(clip.notes)
        if isinstance(operation, AddNotes):
            after = before + operation.notes
        elif isinstance(operation, UpdateNote):
            old_note = next((n for n in before if n.id == operation.note.id), None)
            if old_note is None:
                raise ValidationError("unknown note")
            for note in (old_note, operation.note):
                _authorize(project, scope, track.id, clip.id,
                           interval=(clip.start + note.start, clip.start + note.start + note.duration))
            after = [operation.note if n.id == operation.note.id else n for n in before]
        elif isinstance(operation, RemoveNotes):
            if len(operation.note_ids) != len(set(operation.note_ids)) or not set(operation.note_ids) <= {n.id for n in before}:
                raise ValidationError("duplicate/unknown note to remove")
            after = [n for n in before if n.id not in operation.note_ids]
        elif isinstance(operation, ReplaceNotesInRegion):
            if not 0 <= operation.start < operation.end <= clip.length:
                raise ValidationError("invalid clip-local replacement region")
            _authorize(project, scope, track.id, clip.id,
                       interval=(clip.start + operation.start, clip.start + operation.end))
            intersecting = [n for n in before if n.start < operation.end and n.start + n.duration > operation.start]
            if any(n.start < operation.start or n.start + n.duration > operation.end for n in intersecting):
                raise ValidationError("replacement would cut a note at the region boundary")
            if any(n.start < operation.start or n.start + n.duration > operation.end for n in operation.notes):
                raise ValidationError("replacement note outside region")
            # Surviving objects retain their relative order; inserted notes follow them.
            after = [n for n in before if n not in intersecting] + operation.notes
        else:
            after = operation.notes
        for note in _changed(before, after):
            _authorize(project, scope, track.id, clip.id,
                       interval=(clip.start + note.start, clip.start + note.start + note.duration))
        clip.notes = deepcopy(after)
        return RestoreNotes("restore_notes", clip.id, before)
    found = [lane for lane in project.automation if lane.id == operation.lane_id]
    if not found:
        raise ValidationError("unknown automation lane")
    lane = found[0]
    _, track_id, _ = targets(project)[lane.target_id]
    if track_id not in scope.track_ids or lane.parameter_id not in scope.parameter_ids:
        raise ScopeError("automation target outside scope")
    for lock in project.locks:
        if lock.target_id in (track_id, lane.target_id) and lock.parameter_id in (None, lane.parameter_id):
            raise LockedError(f"locked: {lock.target_id}")
    before = deepcopy(lane.points)
    if isinstance(operation, AddAutomationPoints):
        after = before + operation.points
    elif isinstance(operation, DeleteAutomationPoints):
        if len(operation.point_ids) != len(set(operation.point_ids)) or not set(operation.point_ids) <= {p.id for p in before}:
            raise ValidationError("duplicate/unknown automation point")
        after = [p for p in before if p.id not in operation.point_ids]
    else:
        after = operation.points
    for point in _changed(before, after):
        _authorize(project, scope, track_id, lane.target_id, lane.parameter_id, (point.tick, point.tick))
    lane.points = deepcopy(after)
    return RestoreAutomation("restore_automation", lane.id, before)


def _execute(project, operations, scope, expected_hash=None):
    before_hash = state_hash(project)
    if expected_hash is not None and expected_hash != before_hash:
        raise ValidationError("stale project hash; transaction rejected")
    _check_scope(project, scope)
    candidate = deepcopy(project)
    inverse = []
    for operation in operations:
        inverse.insert(0, _apply(candidate, operation, scope))
        validate(candidate)  # Every operation must leave a valid project, not just the batch.
    return candidate, Receipt("0.1", before_hash, state_hash(candidate), deepcopy(scope), deepcopy(operations), inverse)


class Engine:
    def __init__(self, project: Project):
        validate(project)
        self._project = deepcopy(project)
        self._undo: list[Receipt] = []
        self._redo: list[Receipt] = []

    @property
    def project(self):
        return deepcopy(self._project)

    def apply(self, operations: list[Operation], scope: Scope, expected_hash: str | None = None) -> Receipt:
        if any(type(op) not in PUBLIC_OPERATIONS.values() for op in operations):
            raise ValidationError("inverse operations are reserved for receipt replay")
        candidate, receipt = _execute(self._project, operations, scope, expected_hash)
        self._project = candidate
        self._undo.append(deepcopy(receipt))
        self._redo.clear()
        return receipt

    def undo(self) -> Receipt:
        if not self._undo:
            raise ValidationError("nothing to undo")
        receipt = self._undo[-1]
        candidate = replay(self._project, receipt, undo=True)
        self._project = candidate
        self._redo.append(self._undo.pop())
        return deepcopy(receipt)

    def redo(self) -> Receipt:
        if not self._redo:
            raise ValidationError("nothing to redo")
        receipt = self._redo[-1]
        candidate = replay(self._project, receipt, undo=False)
        self._project = candidate
        self._undo.append(self._redo.pop())
        return deepcopy(receipt)


def replay(project: Project, receipt: Receipt, *, undo: bool) -> Project:
    receipt = receipt_from_dict(asdict(receipt))
    candidate, result = _execute(project, receipt.inverse if undo else receipt.operations, receipt.scope,
                                 receipt.after_hash if undo else receipt.before_hash)
    if result.after_hash != (receipt.before_hash if undo else receipt.after_hash):
        raise ValidationError("receipt replay did not reproduce the expected state")
    return candidate
