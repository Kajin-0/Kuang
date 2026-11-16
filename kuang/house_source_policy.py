"""House producer source-selection constraints: evidence, not a taste oracle.

A producer's explicit rejection is an identity-level hard exclusion that must
survive future independent one-shot runs. Audio features are *separate* safety
and suitability observations; no FFT proxy is allowed to invent user liking.
No third-party preset bytes or private catalog file names are embedded here.
"""
from __future__ import annotations

import math
import re
from .schema import ValidationError

VERSION = "house-source-producer-policy-v1"
SHA = re.compile(r"^[0-9a-f]{64}$")

# Public SHA256 identifier only. The user rejected recurring growling
# minimal-house bass material; its selected source record is LD Bass.
# This is an explicit negative preference, NOT an objective growl detector.
REJECTED_ROLE_SOURCES = {
    "bass": {
        "6e4e2259440015123c1f5670b2991674638c00f0ed198119dd20f3fb97cd918c":
        "producer_rejected_growling_minimal_house_bass",
    },
}
# Heuristic on genuine isolated-source runtime features: if most signal
# energy is bass but full-band side signal dominates, the patch merits
# native sub-mono inspection. This is NOT evidence of growl or poor sound.
BASS_SIDE_REVIEW_FRACTION = .65
BASS_LOW_REVIEW_FRACTION = .80
# Bass and pads must not routinely compete for deep sub authority.
# The known low-heavy 'In the Dark' pad had 0.2797 isolated low-band
# fraction and was replaced in an earlier independently verified minimal
# native pad rescue. 0.20 is a conservative *review trigger*, not an
# aesthetic score or a calibrated limit for every synthesizer patch.
PAD_LOW_BAND_REVIEW_FRACTION = .20


def source_exclusion(role, source_sha256):
    if type(role) is not str or type(source_sha256) is not str or not SHA.fullmatch(source_sha256):
        raise ValidationError("source exclusion needs role and verified catalog SHA256")
    return REJECTED_ROLE_SOURCES.get(role, {}).get(source_sha256)


def bass_timbre_observation(features):
    """Role compatibility review, not a subjective quality estimate."""
    if type(features) is not dict:
        raise ValidationError("verified runtime feature map required")
    values = {key:features.get(key) for key in
              ("low_fraction", "mid_fraction", "high_fraction",
               "stereo_side_fraction","attack_ratio","tail_ratio")}
    if any(type(x) not in (float,int) or not math.isfinite(x) for x in values.values()):
        raise ValidationError("nonfinite/missing runtime timbre features")
    if any(not 0 <= values[x] <= 1 for x in ("low_fraction","mid_fraction",
                                            "high_fraction","stereo_side_fraction")):
        raise ValidationError("invalid normalized timbre features")
    side_risk = (values["stereo_side_fraction"] >= BASS_SIDE_REVIEW_FRACTION and
                 values["low_fraction"] >= BASS_LOW_REVIEW_FRACTION)
    return {
        "version":VERSION,
        "source_low_fraction":values["low_fraction"],
        "source_stereo_side_fraction":values["stereo_side_fraction"],
        "low_dominant_wide_source_review":side_risk,
        "required_follow_up":"NATIVE_SUB_MONO_AND_PITCH_ENVELOPE_REVIEW" if side_risk else None,
        "growl_detected":None,
        "musical_quality":"UNKNOWN",
    }



def pad_timbre_observation(features):
    """Preflight unusual low-band dominance in a House pad source."""
    if type(features) is not dict:
        raise ValidationError("verified runtime pad features required")
    value=features.get("low_fraction")
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:
        raise ValidationError("invalid pad low-band fraction")
    return {
        "version": VERSION,
        "source_low_fraction": value,
        "low_heavy_pad_review": value >= PAD_LOW_BAND_REVIEW_FRACTION,
        "required_follow_up": "NATIVE_PAD_BASS_MASKING_REVIEW"
                              if value >= PAD_LOW_BAND_REVIEW_FRACTION else None,
        "growl_detected": None,
        "musical_quality": "UNKNOWN",
    }
