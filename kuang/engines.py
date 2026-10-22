"""Model boundary: propose typed edits; the transaction engine remains authoritative."""

import random
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from typing import Protocol

from .schema import Project, ValidationError, state_hash
from .transactions import Engine, Operation, Scope, UpdateNote


@dataclass
class Proposal:
    expected_before_hash: str
    scope: Scope
    operations: list[Operation]

    def to_dict(self):
        return asdict(self)


class ModelEngine(Protocol):
    def propose(self, project: Project, scope: Scope, *, seed: int) -> Proposal: ...


class SeededVelocityEngine:
    """Deterministic velocity variation used to exercise the complete edit boundary."""

    def propose(self, project: Project, scope: Scope, *, seed: int) -> Proposal:
        before_hash = state_hash(project)
        Engine(project).apply([], scope, before_hash)
        rng = random.Random(seed)
        operations = []
        for track in project.tracks:
            if track.id not in scope.track_ids:
                continue
            for clip in track.clips:
                if clip.id not in scope.clip_ids:
                    continue
                for note in clip.notes:
                    if scope.start is not None and not (scope.start <= clip.start + note.start and
                                                        clip.start + note.start + note.duration <= scope.end):
                        continue
                    velocity = max(1, min(127, note.velocity + rng.choice([-6, -3, 3, 6])))
                    operations.append(UpdateNote("update_note", clip.id, replace(note, velocity=velocity)))
        if not operations:
            raise ValidationError("no notes inside proposal scope")
        proposal = Proposal(before_hash, deepcopy(scope), operations)
        # No engine, including this fixture, bypasses validation, locks, or scope checks.
        Engine(project).apply(operations, scope, proposal.expected_before_hash)
        return proposal
