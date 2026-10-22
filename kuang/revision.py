"""Provider-independent semantic revision requests, exact scoped plans and replay."""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Literal, Protocol

from .schema import BAR, PPQ, Project, ValidationError, decode, dumps, state_hash, targets
from .song import check_prompt
from .transactions import Engine, RemoveNotes, Scope, SetParameter, receipt_from_dict, replay

SUPPORTED = (
    "make the bass more aggressive; simplify the drums in SECTION / bars N-M; "
    "make the TRACK reverb wetter/drier; turn the TRACK up/down by N dB (0<N<=6); "
    "keep the TRACK unchanged; keep everything else unchanged. "
    "Combine complete clauses with commas, 'and' or semicolons."
)


@dataclass
class ChangeIntent:
    kind: Literal["bass_aggressive", "simplify_drums", "gain", "reverb"]
    track_ids: list[str]
    start: int | None
    end: int | None
    amount: float | None


@dataclass
class RevisionRequest:
    version: Literal["1"]
    expected_before_hash: str
    prompt: str
    intents: list[ChangeIntent]
    preserve_track_ids: list[str]


class RevisionPlanner(Protocol):
    """Future providers return data only; compilation/transactions remain authoritative."""
    def propose(self, project: Project, prompt: str) -> RevisionRequest: ...


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _check_hash(value):
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValidationError("revision requires a lowercase SHA-256 precondition")


def _drums(track):
    notes = [n for c in track.clips for n in c.notes]
    return track.kind == "midi" and bool(notes) and all(n.channel == 9 for n in notes)


def resolve_tracks(project, label):
    label = label.strip().lower().removeprefix("the ").strip('"')
    label = {"pads": "pad", "808": "bass", "drum": "drums", "hi-hats": "hats"}.get(label, label)
    if label == "drums":
        found = [t.id for t in project.tracks if _drums(t)]
    else:
        exact = [t.id for t in project.tracks if label in (t.id.lower(), t.name.lower())]
        stable = [t.id for t in project.tracks if t.id == "track-" + label]
        patterns = {"bass": r"\b(?:bass|808|drone)\b", "pad": r"\bpad\b", "harmony": r"\b(?:pad|chords?)\b",
                    "chords": r"\bchords?\b", "lead": r"\b(?:lead|motif)\b", "arp": r"\b(?:arp|arpeggio|droplets)\b",
                    "kick": r"\b(?:kick|four on floor)\b", "snare": r"\b(?:snare|clap)\b", "hats": r"\bhats?\b"}
        found = exact or stable or [t.id for t in project.tracks if label in patterns and re.search(patterns[label], t.name.lower())]
        if len(found) > 1:
            raise ValidationError(f"ambiguous track {label!r}; use an exact track ID: {', '.join(found)}")
    if not found:
        raise ValidationError(f"no matching track {label!r}; available: " + ", ".join(f"{t.id} ({t.name})" for t in project.tracks))
    return found


def resolve_region(project, text):
    text = text.strip().lower().removeprefix("the ").removeprefix("section ").strip('"')
    bars = re.fullmatch(r"bars? (\d+)(?:\s*(?:-|–|to)\s*(\d+))?", text)
    if bars:
        start, end = int(bars[1]), int(bars[2] or bars[1])
        if not 1 <= start <= end <= project.bars:
            raise ValidationError(f"bar range must be inclusive, 1..{project.bars}")
        return (start - 1) * BAR, end * BAR
    sections = [s for s in project.sections if text in (s.name.lower(), s.id.lower())]
    if len(sections) != 1:
        raise ValidationError(f"unknown/ambiguous section {text!r}; available: " + ", ".join(s.name for s in project.sections))
    return sections[0].start, sections[0].start + sections[0].length


class RulesRevisionPlanner:
    """Finite, fully matched prose grammar. Never drops an unsupported clause."""
    def propose(self, project, prompt):
        check_prompt(prompt)
        intents, preserve = [], []
        for clause in re.split(r"\s*(?:[,;\n](?:\s*(?:and|then)\b)?|\band\b|\bthen\b)\s*", prompt.lower().strip()):
            clause = re.sub(r"\s+", " ", clause.strip()).removeprefix("please ").rstrip(".! ")
            if not clause:
                raise ValidationError("empty revision clause. Supported: " + SUPPORTED)
            if clause in ("keep everything else unchanged", "leave everything else unchanged"):
                continue  # Exact preservation is mandatory for every revision.
            kept = re.fullmatch(r"(?:keep|leave) (?:the )?(.+?) unchanged", clause)
            aggressive = re.fullmatch(r"make (?:the )?bass (?:more )?aggressive", clause)
            simple = re.fullmatch(r"simplify (?:the )?(drums|kick|snare|hats) in (.+)", clause)
            reverb = re.fullmatch(r"make (?:the )?(.+?) reverb (wetter|drier)", clause)
            gain = re.fullmatch(r"turn (?:the )?(.+?) (up|down) by (\d+(?:\.\d+)?) db", clause)
            if kept:
                preserve.extend(resolve_tracks(project, kept[1]))
            elif aggressive:
                intents.append(ChangeIntent("bass_aggressive", resolve_tracks(project, "bass"), None, None, None))
            elif simple:
                start, end = resolve_region(project, simple[2])
                intents.append(ChangeIntent("simplify_drums", resolve_tracks(project, simple[1]), start, end, None))
            elif reverb:
                intents.append(ChangeIntent("reverb", resolve_tracks(project, reverb[1]), None, None,
                                            0.12 if reverb[2] == "wetter" else -0.12))
            elif gain:
                amount = float(gain[3]) * (1 if gain[2] == "up" else -1)
                intents.append(ChangeIntent("gain", resolve_tracks(project, gain[1]), None, None, amount))
            else:
                raise ValidationError(f"unsupported revision clause {clause!r}. Supported: {SUPPORTED}")
        return RevisionRequest("1", state_hash(project), prompt, intents, sorted(set(preserve)))


def validate_request(project, request):
    request = decode(RevisionRequest, asdict(request))
    check_prompt(request.prompt)
    _check_hash(request.expected_before_hash)
    if state_hash(project) != request.expected_before_hash:
        raise ValidationError("stale project hash; revision rejected")
    ids = {t.id for t in project.tracks}
    if not 1 <= len(request.intents) <= 16:
        raise ValidationError("revision requires 1..16 change intents")
    if len(request.preserve_track_ids) != len(set(request.preserve_track_ids)) or not set(request.preserve_track_ids) <= ids:
        raise ValidationError("preservation list contains duplicate/unknown tracks")
    regions = []
    for intent in request.intents:
        if not intent.track_ids or len(set(intent.track_ids)) != len(intent.track_ids) or not set(intent.track_ids) <= ids:
            raise ValidationError("intent requires unique existing track IDs")
        if set(intent.track_ids) & set(request.preserve_track_ids):
            raise ValidationError("intent conflicts with explicitly preserved track(s)")
        if intent.kind == "simplify_drums":
            if (intent.amount is not None or intent.start is None or intent.end is None or
                    not 0 <= intent.start < intent.end <= project.length or intent.start % BAR or intent.end % BAR):
                raise ValidationError("drum simplification requires a bar-aligned half-open tick region, no amount")
            if any(not _drums(t) for t in project.tracks if t.id in intent.track_ids):
                raise ValidationError("simplify_drums targets only nonempty, exclusively channel-9 MIDI tracks")
            for track in intent.track_ids:
                if any(track == t and intent.start < e and intent.end > s for t, s, e in regions):
                    raise ValidationError("overlapping drum simplification intents")
                regions.append((track, intent.start, intent.end))
        else:
            if intent.start is not None or intent.end is not None or len(intent.track_ids) != 1:
                raise ValidationError("parameter intents require one track and global time scope")
            if intent.kind == "bass_aggressive":
                if intent.amount is not None or intent.track_ids != resolve_tracks(project, "bass"):
                    raise ValidationError("bass_aggressive requires the resolved bass track and no amount")
            elif intent.amount is None or not math.isfinite(intent.amount) or not 0 < abs(intent.amount) <= (6 if intent.kind == "gain" else 0.5):
                raise ValidationError("gain delta must be nonzero and <=6 dB; reverb delta <=0.5 normalized")
    return request


def _intent_operations(project, intent):
    operations, clip_ids, parameter_ids = [], [], []
    for track in project.tracks:
        if track.id not in intent.track_ids:
            continue
        if intent.kind == "simplify_drums":
            groups = {}
            for clip in track.clips:
                for note in clip.notes:
                    start, end = clip.start + note.start, clip.start + note.start + note.duration
                    if start < intent.end and end > intent.start:
                        if start < intent.start or end > intent.end:
                            raise ValidationError(f"note {note.id} crosses the requested region boundary")
                        key = (start // BAR, start % BAR // (2 * PPQ), note.pitch)
                        groups.setdefault(key, []).append((clip, note, start))
            removed = set()
            for notes in groups.values():
                ordered = sorted(notes, key=lambda item: (item[2] % PPQ != 0, item[2], item[1].id))
                removed.update(n.id for _, n, _ in ordered[1:])
            for clip in track.clips:
                selected = [n.id for n in clip.notes if n.id in removed]
                if selected:
                    operations.append(RemoveNotes("remove_notes", clip.id, selected))
                    clip_ids.append(clip.id)
            continue
        if intent.kind == "bass_aggressive":
            inst = track.instrument
            if not inst or not {"synth.cutoff_hz", "synth.resonance"} <= inst.parameters.keys():
                raise ValidationError("bass aggression needs explicit existing synth.cutoff_hz and synth.resonance parameters")
            edits = [(inst.id, "synth.cutoff_hz", max(inst.parameters["synth.cutoff_hz"], min(8000, inst.parameters["synth.cutoff_hz"] * 4))),
                     (inst.id, "synth.resonance", max(inst.parameters["synth.resonance"], min(0.65, inst.parameters["synth.resonance"] + 0.2)))]
        elif intent.kind == "gain":
            edits = [(track.id, "mixer.gain_db", track.controls["mixer.gain_db"] + intent.amount)]
        else:
            effects = [e for e in track.effects if "verb" in e.plugin_ref.lower() and "effect.wet" in e.parameters]
            if len(effects) != 1:
                raise ValidationError(f"{track.id} requires exactly one existing reverb with effect.wet; effects are never inserted implicitly")
            effect = effects[0]
            edits = [(effect.id, "effect.wet", max(0, min(1, effect.parameters["effect.wet"] + intent.amount)))]
        registry = {p.id: p for p in project.parameters}
        for target, parameter, value in edits:
            spec = registry[parameter]
            expected_unit = {"mixer.gain_db": "dB", "synth.cutoff_hz": "Hz", "synth.resonance": "normalized", "effect.wet": "normalized"}[parameter]
            if spec.unit != expected_unit or not spec.minimum <= value <= spec.maximum:
                raise ValidationError(f"unsupported unit/range for {parameter}: requires {expected_unit}, proposed {value}")
            if any(a.target_id == target and a.parameter_id == parameter and a.points for a in project.automation):
                raise ValidationError(f"{target}/{parameter} is automated; base-only revision would be overridden; automation editing is unsupported")
            if value != targets(project)[target][2][parameter]:
                operations.append(SetParameter("set_parameter", target, parameter, value))
                parameter_ids.append(parameter)
    if not operations:
        raise ValidationError(f"{intent.kind} would make no change in the requested track/region")
    scope = Scope(list(intent.track_ids), clip_ids, sorted(set(parameter_ids)), intent.start, intent.end)
    return operations, scope


def comparison(before, after, steps):
    """Independently mask only authorized scalar changes and removed note IDs."""
    expected, old_mask, new_mask = deepcopy(before), deepcopy(before), deepcopy(after)
    changes, removed, changed_tracks = [], [], set()
    for step in steps:
        for operation in step["operations"]:
            if operation["op"] == "set_parameter":
                target, parameter = operation["target_id"], operation["parameter_id"]
                old = targets(before)[target][2][parameter]
                new = targets(after)[target][2][parameter]
                if new != operation["value"]:
                    raise ValidationError("revision parameter differs from authorized plan")
                targets(expected)[target][2][parameter] = new
                targets(new_mask)[target][2][parameter] = old
                changed_tracks.add(targets(before)[target][1])
                changes.append({"target_id": target, "parameter_id": parameter, "before": old, "after": new})
            elif operation["op"] == "remove_notes":
                clip_id, ids = operation["clip_id"], set(operation["note_ids"])
                track, clip = next((t, c) for t in before.tracks for c in t.clips if c.id == clip_id)
                changed_tracks.add(track.id)
                removed += [{"track_id": track.id, "clip_id": clip.id, "note": asdict(n),
                             "absolute_start": clip.start+n.start, "absolute_end": clip.start+n.start+n.duration}
                            for n in clip.notes if n.id in ids]
                for p in (expected, old_mask):
                    c = next(c for t in p.tracks for c in t.clips if c.id == clip_id)
                    c.notes = [n for n in c.notes if n.id not in ids]
            else:
                raise ValidationError("revision comparison only supports parameter changes and exact note removal")
    if dumps(expected) != dumps(after) or dumps(old_mask) != dumps(new_mask):
        raise ValidationError("revision changed canonical state outside the authorized edits")
    unchanged = [t.id for t in before.tracks if t.id not in changed_tracks]
    survivors = [n.id for t in after.tracks for c in t.clips for n in c.notes]
    return {"before_hash": state_hash(before), "after_hash": state_hash(after), "parameter_changes": changes,
            "removed_notes": removed, "changed_track_ids": sorted(changed_tracks), "unchanged_track_ids": unchanged,
            "unchanged_track_hashes": {t.id: _digest(asdict(t)) for t in before.tracks if t.id in unchanged},
            "unchanged_projection_before_hash": state_hash(old_mask), "unchanged_projection_after_hash": state_hash(new_mask),
            "unchanged_equal": True, "surviving_note_count": len(survivors), "surviving_note_ids_hash": _digest(survivors),
            "metadata_equal": before.metadata == after.metadata, "timing_equal": (before.tempo_bpm, before.length, before.sections) == (after.tempo_bpm, after.length, after.sections)}


def prepare_revision(project, request):
    request = validate_request(project, request)
    engine, steps, receipts, touched = Engine(project), [], [], set()
    for intent in request.intents:
        operations, scope = _intent_operations(engine.project, intent)
        for op in operations:
            key = (op.target_id, op.parameter_id) if isinstance(op, SetParameter) else None
            if key and key in touched:
                raise ValidationError("multiple intents edit the same parameter; use one unambiguous instruction")
            if key:
                touched.add(key)
        receipt = engine.apply(operations, scope, state_hash(engine.project))
        receipts.append(asdict(receipt))
        steps.append({"intent": asdict(intent), "scope": asdict(scope), "operations": [asdict(op) for op in operations],
                      "before_hash": receipt.before_hash, "after_hash": receipt.after_hash})
    result = engine.project
    report = comparison(project, result, steps)
    if report["before_hash"] == report["after_hash"]:
        raise ValidationError("revision has no net change")
    plan = {"version": "revision-plan-1", "request": asdict(request), "steps": steps,
            "expected_after_hash": state_hash(result), "comparison": report}
    receipt = {"version": "revision-1", "before_hash": state_hash(project), "after_hash": state_hash(result), "receipts": receipts}
    return plan, result, receipt


def apply_plan(project, plan):
    if type(plan) is not dict or set(plan) != {"version", "request", "steps", "expected_after_hash", "comparison"} or plan["version"] != "revision-plan-1":
        raise ValidationError("invalid revision plan fields/version")
    request = decode(RevisionRequest, plan["request"])
    rebuilt, result, receipt = prepare_revision(project, request)
    if _digest(rebuilt) != _digest(plan):
        raise ValidationError("revision plan differs from the strictly compiled intents/scopes/operations")
    return result, receipt


def replay_revision(project, data, *, undo):
    if type(data) is not dict or set(data) != {"version", "before_hash", "after_hash", "receipts"} or data["version"] != "revision-1":
        raise ValidationError("invalid revision receipt fields/version")
    for name in ("before_hash", "after_hash"):
        _check_hash(data[name])
    if type(data["receipts"]) is not list or not 1 <= len(data["receipts"]) <= 16:
        raise ValidationError("revision receipt requires 1..16 scoped receipts")
    receipts = [receipt_from_dict(r) for r in data["receipts"]]
    if (receipts[0].before_hash != data["before_hash"] or receipts[-1].after_hash != data["after_hash"] or
            any(a.after_hash != b.before_hash for a, b in zip(receipts, receipts[1:]))):
        raise ValidationError("broken revision receipt hash chain")
    expected = data["after_hash"] if undo else data["before_hash"]
    if state_hash(project) != expected:
        raise ValidationError("stale project hash for revision replay")
    result = deepcopy(project)
    for receipt in reversed(receipts) if undo else receipts:
        result = replay(result, receipt, undo=undo)
    if state_hash(result) != (data["before_hash"] if undo else data["after_hash"]):
        raise ValidationError("revision replay hash mismatch")
    return result
