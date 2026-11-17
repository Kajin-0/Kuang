"""Opt-in four-bar chord-phrase regularization on an existing house nucleus.

The legacy harmony interlock optimizes each bar independently. This bounded
candidate uses one rhythmic pattern for each four-bar Groove/Drop phrase,
without changing notes, instruments, buses, FX, source presets, or bass/drums.
It must not increase near-simultaneous (<80-tick) chord/bass attacks relative
to the existing per-bar interlock. That narrow engineering guard is NOT an
aesthetic preference score; native matched-level listening is still required.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy

from .house_harmony_interlock import PATTERNS, STEP, _clusters
from .schema import BAR, ValidationError, state_hash, validate

VERSION = "house-chord-phrase-coherence-v2-optin"


def _anchors(pattern, bar, count, seed):
    """The existing groove-interlock vocabulary, without any new MIDI events."""
    if count == 1:
        positions = (pattern[(bar + seed) % 3],)
    elif count == 2:
        positions = (pattern[0], pattern[2])
    elif count == 3:
        positions = pattern
    else:
        return None
    ticks = tuple(step * STEP for step in positions)
    # Preserve at least 330 ticks between a pair of authored chord attacks.
    if any(b - a < 330 for a, b in zip(ticks, ticks[1:])):
        return None
    return ticks


def _collisions(bar, anchors, bass_times, window):
    return sum(min((abs(bar * BAR + tick - bass) for bass in bass_times),
                   default=BAR) < window for tick in anchors)


def _safe_positions(rows, pattern, seed):
    """Map all original staggered chord voices without clipping notes."""
    selected = {}
    for bar, groups, clip in rows:
        anchors = _anchors(pattern, bar, len(groups), seed)
        if anchors is None:
            return None
        for (old_abs, voices), anchor in zip(groups, anchors):
            for note in voices:
                absolute = bar * BAR + anchor + clip.start + note.start - old_abs
                relative = absolute - clip.start
                if (relative < 0 or relative + note.duration > clip.length
                        or absolute // BAR != bar):
                    return None
        selected[bar] = anchors
    return selected


def regularize_chord_phrases(source, *, profile, seed):
    """Return a new optional candidate plus a structural/provenance receipt.

    No file writes, plugin changes or additional source selection occur. If
    no coherent pattern satisfies the prior near-bass-onset count, it keeps
    that phrase untouched. A no-change result is a valid outcome.
    """
    validate(source)
    if profile not in PATTERNS or type(seed) is not int or not 0 <= seed < 2**32:
        raise ValidationError("supported house profile and uint32 seed required")
    sections = {s.name: s for s in source.sections}
    if not {"Groove", "Drop"} <= set(sections):
        raise ValidationError("original 16/32-bar Groove and Drop source required")
    bass = next((t for t in source.tracks if t.id == "track-bass"), None)
    harmony = next((t for t in source.tracks if t.id == "track-harmony"), None)
    if bass is None or harmony is None:
        raise ValidationError("source bass and harmony tracks required")
    original = state_hash(source)
    candidate = deepcopy(source)
    target = next(t for t in candidate.tracks if t.id == "track-harmony")
    bass_times = sorted(clip.start + n.start for clip in bass.clips for n in clip.notes)
    allowed = {bar for name in ("Groove", "Drop")
               for bar in range(sections[name].start // BAR,
                                (sections[name].start + sections[name].length) // BAR)}
    seen = 0
    coherent = 0
    unchanged = 0
    moved = 0
    total_before = 0
    total_after = 0
    decisions = []
    for clip in target.clips:
        buckets = defaultdict(list)
        for note in clip.notes:
            bar = (clip.start + note.start) // BAR
            if bar in allowed:
                buckets[bar].append(note)
        phrases = defaultdict(list)
        for bar, notes in sorted(buckets.items()):
            groups = _clusters(notes, clip.start)
            if 1 <= len(groups) <= 3:
                phrases[bar // 4].append((bar, groups, clip))
        for phrase_number, rows in sorted(phrases.items()):
            if len(rows) < 2:
                continue
            seen += 1
            before = sum(_collisions(bar, tuple(old - bar * BAR
                                              for old, _ in groups),
                                     bass_times, 80)
                         for bar, groups, _ in rows)
            total_before += before
            choices = []
            for index, pattern in enumerate(PATTERNS[profile]):
                positions = _safe_positions(rows, pattern, seed)
                if positions is None:
                    continue
                near = sum(_collisions(bar, positions[bar], bass_times, 80)
                           for bar, _, _ in rows)
                if near > before:
                    continue
                moderate = sum(_collisions(bar, positions[bar], bass_times, 155)
                               for bar, _, _ in rows)
                tie = (index - ((seed + phrase_number) % len(PATTERNS[profile]))) % len(PATTERNS[profile])
                choices.append(((near, moderate, tie, index), positions))
            if not choices:
                unchanged += 1
                total_after += before
                decisions.append({"first_bar": rows[0][0] + 1,
                                  "choice": "RETAIN_LEGACY",
                                  "near_before": before, "near_after": before})
                continue
            (near, _, _, selected_index), positions = min(choices, key=lambda x: x[0])
            for bar, groups, group_clip in rows:
                for (old_abs, notes), anchor in zip(groups, positions[bar]):
                    for note in notes:
                        new_time = (bar * BAR + anchor +
                                    group_clip.start + note.start - old_abs)
                        relative = new_time - group_clip.start
                        if relative != note.start:
                            note.start = relative
                            moved += 1
            coherent += 1
            total_after += near
            decisions.append({"first_bar": rows[0][0] + 1,
                              "choice": "COHERENT_PATTERN",
                              "pattern_index": selected_index,
                              "near_before": before, "near_after": near})
    validate(candidate)
    if total_after > total_before:
        raise ValidationError("phrase candidate worsened near-bass attack collisions")
    if any(t != next(x for x in candidate.tracks if x.id == t.id)
           for t in source.tracks if t.id != "track-harmony"):
        raise ValidationError("chord phrase revision changed another role")
    if (harmony.instrument != target.instrument or harmony.effects != target.effects
            or harmony.controls != target.controls or harmony.sends != target.sends):
        raise ValidationError("phrase revision changed a source/FX/mixer")
    def properties(t):
        return sorted((n.id, n.pitch, n.velocity, n.duration, n.channel)
                      for c in t.clips for n in c.notes)
    if properties(harmony) != properties(target):
        raise ValidationError("phrase revision modified chord notes")
    if state_hash(source) != original:
        raise ValidationError("phrase regularizer mutated the original source")
    candidate.metadata["house_chord_phrase_coherence_version"] = VERSION
    return candidate, {
        "version": VERSION, "source_sha256": original,
        "candidate_sha256": state_hash(candidate),
        "profile": profile, "seed": seed, "phrase_length_bars": 4,
        "phrases_reviewed": seen, "coherent_phrases": coherent,
        "phrases_retained": unchanged, "chord_voice_events_moved": moved,
        "near_bass_attacks_before": total_before,
        "near_bass_attacks_after": total_after,
        "source_immutable": True, "other_roles_exact": True,
        "pitch_velocity_gate_and_instrument_exact": True,
        "per_phrase_decisions": decisions,
        "musical_quality": "NOT_EVALUATED",
        "status": "EXPERIMENTAL_LISTENING_REQUIRED",
    }
