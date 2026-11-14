"""Opt-in harmonic plan enrichment for the EXISTING Kuang SongSpec pipeline.

This module changes only a validated four-degree diatonic progression. It
deliberately does not implement a second composer, groove, arranger, source
selector, sound engine, voicing system or musical-quality critic.
"""
from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from .song import SongSpec, check_prompt, validate_spec
from .schema import ValidationError

VERSION = "house-musical-plan-v2-experimental"

# Coherent, recognizable four-chord house archetypes. Degrees are zero-based
# within the selected MAJOR or NATURAL MINOR scale. These are common harmonic
# functions, not reproduced recorded songs. Existing production changes
# harmony every two bars and is intentionally not modified here.
FAMILIES = {
    ("deep", "major"): (
        ("soulful", (0, 3, 5, 4)),
        ("reflective", (5, 3, 0, 4)),
        ("tonic_pedal", (0, 3, 0, 4)),
        ("gentle_turnaround", (0, 5, 3, 4)),
    ),
    ("deep", "minor"): (
        ("aeolian", (0, 5, 2, 6)),
        ("meditative", (0, 6, 5, 6)),
        ("minor_pedal", (0, 3, 0, 5)),
        ("descending_color", (0, 5, 3, 6)),
    ),
    ("straight", "major"): (
        ("classic", (0, 4, 5, 3)),
        ("plagal", (0, 3, 4, 3)),
        ("uplift", (0, 5, 3, 4)),
        ("tonic_return", (0, 3, 0, 4)),
    ),
    ("straight", "minor"): (
        ("aeolian", (0, 5, 2, 6)),
        ("night_drive", (0, 3, 5, 6)),
        ("minor_turnaround", (0, 6, 3, 4)),
        ("minor_vamp", (0, 3, 0, 6)),
    ),
    ("jackin", "major"): (
        ("call_response", (0, 3, 4, 3)),
        ("tonic_to_iv", (0, 3, 0, 4)),
        ("bright_cycle", (0, 4, 3, 4)),
        ("soulful", (0, 3, 5, 4)),
    ),
    ("jackin", "minor"): (
        ("minor_call_response", (0, 3, 4, 3)),
        ("minor_pedal", (0, 3, 0, 6)),
        ("minor_turnaround", (0, 6, 3, 4)),
        ("aeolian", (0, 5, 2, 6)),
    ),
    ("minimal", "major"): (
        ("tonic_stasis", (0, 0, 3, 0)),
        ("two_chord_iv", (0, 3, 0, 3)),
        ("two_chord_v", (0, 4, 0, 4)),
        ("gentle_motion", (0, 3, 4, 3)),
    ),
    ("minimal", "minor"): (
        ("minor_stasis", (0, 0, 5, 0)),
        ("minor_two_chord", (0, 5, 0, 5)),
        ("minor_pedal", (0, 3, 0, 3)),
        ("sparse_aeolian", (0, 6, 0, 5)),
    ),
}

# Match the actual Roman-progression contract in song.rules_plan, not a
# broad roman-looking fragment such as a prose word. The spec is parsed by
# rules_plan first, so explicitly requested progressions remain authoritative.
_EXPLICIT_ROMAN = re.compile(r"\b([ivIV]+(?:\s*[-–]\s*[ivIV]+){3})\b")


def enrich_house_spec(spec: SongSpec, prompt: str, groove_profile: str):
    """Return a NEW SongSpec plus a traceable, side-effect-free plan receipt.

    Call AFTER the existing rules_plan and profile selection, BEFORE palette
    audition or project generation. Never changes the original input object.
    No songwriter, quality or cross-prompt diversity success is claimed.
    """
    check_prompt(prompt)
    if groove_profile not in ("deep", "straight", "jackin", "minimal"):
        raise ValidationError("unsupported musical-plan house style")
    validated = validate_spec(spec)
    if validated.genre != "house" or validated.arrangement != "song":
        raise ValidationError("musical plan currently supports house-song intent only")
    if type(validated.seed) is not int:
        raise ValidationError("musical plan requires deterministic integer seed")

    planned = deepcopy(validated)
    explicit = _EXPLICIT_ROMAN.search(prompt) is not None
    choice = None
    if not explicit:
        candidates = FAMILIES[(groove_profile, validated.mode)]
        # Seed and musical character (not arbitrary prose punctuation)
        # determine the family. An unchanged prompt/seed remains reproducible.
        context = ":".join(str(x) for x in (
            validated.seed, groove_profile, validated.mode,
            validated.mood, validated.energy, validated.palette))
        digest = hashlib.sha256(context.encode("utf-8")).digest()
        choice = candidates[int.from_bytes(digest[:8], "big") % len(candidates)]
        planned.progression = list(choice[1])
    planned = validate_spec(planned)
    if (planned.tonic, planned.mode, planned.bpm, planned.seed, planned.bars,
            planned.instruments, planned.space, planned.energy) != (
            validated.tonic, validated.mode, validated.bpm, validated.seed,
            validated.bars, validated.instruments, validated.space, validated.energy):
        raise ValidationError("musical-plan enrichment changed locked SongSpec fields")

    receipt = {
        "version": VERSION,
        "status": "EXPERIMENTAL_NOT_MUSICALLY_APPROVED",
        "source_spec_version": validated.version,
        "profile": groove_profile,
        "seed": validated.seed,
        "tonic": validated.tonic,
        "mode": validated.mode,
        "selection": "explicit_roman" if explicit else "curated_style_seed",
        "family": "user_explicit" if explicit else choice[0],
        "progression_degrees": list(planned.progression),
        "original_progression_degrees": list(validated.progression),
        "harmonic_change_every_bars": 2,
        "legacy_composer_retained": True,
        "legacy_arranger_retained": True,
        "native_source_selection_unchanged": True,
        "perceptual_quality": "NEEDS_LISTENING",
        "limitations": [
            "Four-degree diatonic progression only, major/natural minor.",
            "Style-conditioned templates do not constitute a trained quality critic.",
            "Existing chords, bass and arrangement engines consume this shared SongSpec.",
            "No automatic preset or progression diversity quota.",
        ],
    }
    return planned, receipt
