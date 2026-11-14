"""Groove-aware chord articulation for independently generated house projects.

Uses each generated bass MIDI pattern, a family of musical chord rhythms,
and the existing voicing groups. Never imports the Phase44 reference score,
private sound sources or universal EQ presets. Onset collisions are only a
rhythmic engineering proxy; they do not diagnose musical quality.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict

from .schema import BAR, PPQ, ValidationError, validate

VERSION = "house-harmony-interlock-v1"
STEP = PPQ // 4

# 16th-grid positions per bar. These are *alternatives*, not the particular
# approved reference rhythm. Odd/even bars and seeds choose among them.
PATTERNS = {
    "deep": ((3, 9, 14), (3, 8, 13), (1, 9, 14), (3, 11, 14)),
    "straight": ((3, 11, 14), (1, 9, 13), (3, 8, 14), (7, 11, 14)),
    "jackin": ((1, 5, 12), (3, 8, 13), (3, 9, 14), (1, 7, 14)),
    "minimal": ((3, 11, 14), (7, 13, 14), (3, 9, 13), (1, 10, 14)),
}


def _clusters(notes, clip_start):
    """Group staggered voices at a common stab while retaining their strum."""
    groups = []
    for n in sorted(notes, key=lambda x: (x.start, x.pitch, x.id)):
        at = clip_start + n.start
        if not groups or at - groups[-1][0] > 32:
            groups.append((at, [n]))
        else:
            groups[-1][1].append(n)
    return groups


def _choose_positions(bar, count, bass_ticks, profile, seed):
    """Select a phrase rhythm with minimal exact attack collisions.

    Candidates all have intentional syncopated phrasing. Small tie variations
    are seed-dependent, not key-specific or reference-song-specific.
    """
    patterns = PATTERNS[profile]
    ranked = []
    for i, pattern in enumerate(patterns):
        if count == 1:
            steps = (pattern[(bar + seed) % 3],)
        elif count == 2:
            steps = (pattern[0], pattern[2])
        else:
            steps = pattern
        anchors = [step * STEP for step in steps]
        # A pattern with two adjacent sixteenths can cause overlapping
        # same-pitch chord voices when source patches have 300-tick gates.
        # Skip those candidates before comparing bass-relative positions.
        # This is a validator correction, not a musical-quality ranking.
        if any(y-x < 330 for x,y in zip(anchors,anchors[1:])):
            continue
        # 80 ticks = 42ms at 126BPM. This deliberately measures only
        # simultaneous attack collisions, not musical sustain/psychoacoustics.
        near = sum(min((abs((bar * BAR + x) - t) for t in bass_ticks), default=BAR)
                   < 80 for x in anchors)
        moderate = sum(min((abs((bar * BAR + x) - t) for t in bass_ticks), default=BAR)
                       < 155 for x in anchors)
        # Rotate tie rank across seeds and bars to avoid a single rhythm
        # becoming an unconditional fixed recipe.
        variety = (i - ((seed + 3 * bar) % len(patterns))) % len(patterns)
        ranked.append((near, moderate, variety, tuple(anchors), i))
    best = min(ranked)
    return best[3], best[4]


def _collisions(harmony, bass, sections):
    sections = set(sections)
    bass_ticks = sorted(c.start + n.start for c in bass.clips for n in c.notes)
    count = 0
    grouped = 0
    for c in harmony.clips:
        for bar in range(c.start // BAR, (c.start + c.length - 1) // BAR + 1):
            if bar not in sections:
                continue
            notes = [n for n in c.notes if (c.start + n.start) // BAR == bar]
            for at, _ in _clusters(notes, c.start):
                grouped += 1
                if min((abs(at - b) for b in bass_ticks), default=BAR) < 80:
                    count += 1
    return count, grouped


def apply_interlock(project, profile, seed):
    if profile not in PATTERNS or type(seed) is not int or not 0 <= seed <= 2**32-1:
        raise ValidationError("unsupported harmony interlock profile or seed")
    harmony = next((t for t in project.tracks if t.id == "track-harmony"), None)
    bass = next((t for t in project.tracks if t.id == "track-bass"), None)
    if harmony is None or bass is None:
        raise ValidationError("harmony interlock requires original bass and chord tracks")
    original_bass = [(c.start, n.start, n.duration, n.pitch, n.velocity)
                     for c in bass.clips for n in c.notes]
    original_harmony_pitches = sorted((n.id, n.pitch, n.velocity, n.channel)
                                      for c in harmony.clips for n in c.notes)
    active_bars = {
        bar for section in project.sections if section.name in ("Groove", "Drop")
        for bar in range(section.start // BAR, (section.start + section.length) // BAR)
    }
    if not active_bars:
        raise ValidationError("interlock requires Groove or Drop sections")
    before, total = _collisions(harmony, bass, active_bars)
    bass_ticks = sorted(c.start + n.start for c in bass.clips for n in c.notes)
    adjustments = 0
    phrase_choice = {}
    skipped = 0
    for c in harmony.clips:
        # Only retime the distinct existing chord attacks. Do not invent new
        # voicings, extensions or extra notes.
        buckets = defaultdict(list)
        for n in c.notes:
            buckets[(c.start + n.start) // BAR].append(n)
        for bar, notes in sorted(buckets.items()):
            if bar not in active_bars:
                continue
            groups = _clusters(notes, c.start)
            if not 1 <= len(groups) <= 3:
                skipped += 1
                continue
            anchors, choice = _choose_positions(bar, len(groups), bass_ticks, profile, seed)
            phrase_choice[bar] = choice
            for (old_anchor, chord_notes), anchor in zip(groups, anchors):
                for n in chord_notes:
                    # Preserve intentional note-strum offsets, then keep all
                    # notes in their existing section/clip and original bar.
                    at = bar * BAR + anchor + (c.start + n.start - old_anchor)
                    relative = at - c.start
                    if (relative < 0 or relative + n.duration > c.length
                            or at // BAR != bar):
                        raise ValidationError("interlock would move chord beyond its bar")
                    if n.start != relative:
                        n.start = relative
                        adjustments += 1
    if original_bass != [(c.start,n.start,n.duration,n.pitch,n.velocity)
                        for c in bass.clips for n in c.notes]:
        raise ValidationError("interlock modified bass score")
    if original_harmony_pitches != sorted((n.id,n.pitch,n.velocity,n.channel)
                                         for c in harmony.clips for n in c.notes):
        raise ValidationError("interlock changed chord voicing")
    validate(project)
    after, resulting = _collisions(harmony, bass, active_bars)
    fingerprint = [(c.start + n.start,n.pitch) for c in harmony.clips for n in c.notes]
    result = {
        "version": VERSION,
        "profile": profile,
        "seed": seed,
        "retimed_chord_voice_events": adjustments,
        "active_bars": len(active_bars),
        "chord_groups_before": total,
        "chord_groups_after": resulting,
        "near_bass_onset_groups_before": before,
        "near_bass_onset_groups_after": after,
        "pattern_choices": {str(k):v for k,v in sorted(phrase_choice.items())},
        "unhandled_bars": skipped,
        "harmony_midi_fingerprint_sha256": hashlib.sha256(json.dumps(
            fingerprint,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "source_selection_unchanged": True,
        "bass_drums_unchanged": True,
        "effect_processing_unchanged": True,
        "perceptual_quality": "NEEDS_LISTENING",
        "caveat": "Intentional chord rhythms chosen from musical candidates; onset collisions are only a proxy, not an aesthetic score."
    }
    return result
