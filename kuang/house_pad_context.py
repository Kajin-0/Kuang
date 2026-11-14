"""Narrow, opt-in native pad-context safeguard for the existing source selector.

No universal pad preset, Phase44 preset parameters or arbitrary uniqueness.
Decisions are based on verified role-specific rendered band RMS and restricted
to *gross* lower-mid source conflicts. This is a safety/mix compatibility
heuristic, not a trained model of perceptual music quality.
"""
from __future__ import annotations
import math
from .schema import ValidationError

VERSION = "native-pad-context-compatibility-v1"
BODY = "body_120_500"
MID = "mid_500_2000"

# Pilot thresholds are explicitly provisional and must not be described as
# calibrated human preference. All measurements are native 48k 24-bit,
# same MIDI, identical faders, FX, section and spectral windows.
BODY_ABOVE_BASS_DB = 8.
BODY_ABOVE_MID_DB = 6.
TILT_IMPROVEMENT_DB = 4.5
CANDIDATE_MID_FLOOR_DB = -7.
CANDIDATE_BODY_MAX_ABOVE_BASS_DB = 4.


def _read(spectrum):
    if not isinstance(spectrum, dict) or not isinstance(spectrum.get("band_rms_dbfs"), dict):
        raise ValidationError("verified native band RMS spectrum required")
    bands = spectrum["band_rms_dbfs"]
    result = {}
    for band in (BODY, MID):
        v=bands.get(band)
        if type(v) not in (int,float) or not math.isfinite(v) or not -180 <= v <= 12:
            raise ValidationError("non-finite or missing native lower-mid spectrum")
        result[band] = float(v)
    return result


def compare_native_pad(bass_spectrum, baseline_pad_spectrum, alternate_pad_spectrum,
                       *, baseline_source_sha, candidate_source_sha):
    """Conservative automatic eligibility test with complete measurement receipt.

    Silent and lower-energy-only swaps cannot win: require a genuine reduction
    in pad lower-mid tilt with preserved pad midrange support, and sufficient
    reduction in absolute 120–500 Hz competition with the existing bass.
    """
    if (type(baseline_source_sha) is not str or type(candidate_source_sha) is not str or
            len(baseline_source_sha)!=64 or len(candidate_source_sha)!=64 or
            baseline_source_sha==candidate_source_sha or
            any(ch not in "0123456789abcdef" for sha in (baseline_source_sha,candidate_source_sha) for ch in sha)):
        raise ValidationError("two distinct verified SHA256 source identities required")
    bass = _read(bass_spectrum)
    old = _read(baseline_pad_spectrum)
    new = _read(alternate_pad_spectrum)
    bass_body=bass[BODY]
    old_body=old[BODY]
    old_mid=old[MID]
    new_body=new[BODY]
    new_mid=new[MID]
    old_tilt=old_body-old_mid
    new_tilt=new_body-new_mid
    evidence={
        "version": VERSION,
        "baseline_source_sha256": baseline_source_sha,
        "alternative_source_sha256": candidate_source_sha,
        "original_pad_body_minus_bass_body_db": round(old_body-bass_body,3),
        "original_pad_body_minus_mid_db": round(old_tilt,3),
        "candidate_pad_body_minus_bass_body_db": round(new_body-bass_body,3),
        "candidate_pad_body_minus_mid_db": round(new_tilt,3),
        "candidate_mid_minus_original_mid_db":round(new_mid-old_mid,3),
        "pad_tilt_reduction_db":round(old_tilt-new_tilt,3),
        "thresholds_db":{
            "original_body_vs_bass_min":BODY_ABOVE_BASS_DB,
            "original_body_vs_mid_min":BODY_ABOVE_MID_DB,
            "candidate_tilt_improvement_min":TILT_IMPROVEMENT_DB,
            "candidate_mid_preservation_min":CANDIDATE_MID_FLOOR_DB,
            "candidate_body_vs_bass_max":CANDIDATE_BODY_MAX_ABOVE_BASS_DB
        },
        "technical_compatibility_only":True,
        "perceptual_quality":"NOT_ESTABLISHED",
        "mix_winner":None,
    }
    severe=(old_body-bass_body>=BODY_ABOVE_BASS_DB and old_tilt>=BODY_ABOVE_MID_DB)
    better=(new_body-bass_body<=CANDIDATE_BODY_MAX_ABOVE_BASS_DB and
            old_tilt-new_tilt>=TILT_IMPROVEMENT_DB and
            new_mid-old_mid>=CANDIDATE_MID_FLOOR_DB)
    evidence["severe_original_lower_mid_overlap"]=severe
    evidence["candidate_preserves_midrange_and_reduces_overlap"]=better
    evidence["technical_replacement_eligible"]=bool(severe and better)
    evidence["reason"]=("gross lower-mid conflict reduced without simple broadband attenuation"
        if severe and better else
        "insufficient evidence of a safe, spectrally distinct context improvement")
    return evidence
