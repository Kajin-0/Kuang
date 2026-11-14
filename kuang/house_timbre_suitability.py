"""Role-aware preset suitability reviews, never an automated musical winner.

Extends the existing vetted Vital source feature records. Review flags are
warnings (candidate audit triggers), not hard aesthetic exclusions or
replacement decisions. No copying a preferred source between songs.
"""
from __future__ import annotations

import math

from .schema import ValidationError

VERSION = "house-timbre-role-review-v1"
ROLES = ("bass", "chord", "pad")


def review_sources(features_by_role):
    if type(features_by_role) is not dict or not set(features_by_role) <= set(ROLES):
        raise ValidationError("unsupported timbre role registry")
    results = {}
    for role, data in features_by_role.items():
        if type(data) is not dict:
            raise ValidationError("missing role audio features")
        required = ("low_fraction", "mid_fraction", "high_fraction",
                    "stereo_side_fraction", "tail_ratio", "rms")
        if any(type(data.get(k)) not in (float, int) or not math.isfinite(data[k])
               for k in required):
            raise ValidationError("invalid private source feature measurements")
        if (any(not 0 <= data[k] <= 1 for k in required[:4])
                or not 0 <= data["tail_ratio"] <= 20
                or not 0 <= data["rms"] <= 1
                or abs(sum(data[k] for k in required[:3])-1) > .05):
            raise ValidationError("invalid spectral/timbre feature range")
        flags = []
        if role == "pad":
            if data["low_fraction"] > .20:
                flags.append("pad_has_appreciable_low_band_energy")
            if data["rms"] > .18 and data["low_fraction"] > .15:
                flags.append("loud_low_pad_requires_kick_bass_context_review")
        elif role == "bass":
            if data["stereo_side_fraction"] > .45:
                flags.append("bass_stereo_requires_sub_band_mono_measurement")
            if data["mid_fraction"] < .08:
                flags.append("bass_may_lack_upper_harmonic_translation")
            if data["tail_ratio"] < .01:
                flags.append("very_short_bass_tail_may_reduce_between_kick_body")
        else:
            if data["tail_ratio"] > .45:
                flags.append("long_chord_tail_may_mask_adjacent_rhythmic_parts")
            if data["low_fraction"] > .12:
                flags.append("chord_low_band_requires_bass_context_review")
        results[role] = {
            "review_flags": flags,
            "analysis_source": "isolated Vital runtime audition; different from native mix or sub-specific measurement",
            "perceptual_quality": "NOT_EVALUATED",
            "action": "compare verified alternate in locked native context, never auto reject" if flags
                      else "no proxy review flag; musical compatibility remains unknown"
        }
    return {"version": VERSION, "roles": results,
            "verified_suitability": False, "winner": None,
            "calibration": "provisional conservative review thresholds only; not trained perception"}


def source_names(selection):
    """Extract only audited feature records without loading private preset bytes."""
    if type(selection) is not dict or selection.get("status") != "complete":
        raise ValidationError("complete verified private selection required")
    selected = selection.get("roles")
    if type(selected) is not dict or not set(selected) <= set(ROLES):
        raise ValidationError("invalid selection role list")
    observations = {}
    for role, entry in selected.items():
        if (type(entry) is not dict or entry.get("status") != "accepted"
                or entry.get("runtime_verified") is not True
                or type(entry.get("source_preset_name")) is not str):
            raise ValidationError("unverified private source")
        observations[role] = entry.get("features")
    evidence = review_sources(observations)
    for role, entry in selected.items():
        evidence["roles"][role]["source_name"] = entry["source_preset_name"]
        evidence["roles"][role]["source_sha256"] = entry["source_sha256"]
    return evidence
