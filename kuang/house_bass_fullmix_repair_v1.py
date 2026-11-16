"""Fail-closed full-mix evidence for House bass-source technical rescue.

Compare real native PCM24 Groove output for the exact same kick/MIDI context.
This is a hard-fault recovery prerequisite, NOT a machine-listening quality
score. A louder source that does not actually improve offbeat bass energy is
never automatically promoted. Producer source vetoes are absolute.
"""
from __future__ import annotations

import math

from .house_groove_pocket import VERSION as POCKET_VERSION
from .house_source_policy import source_exclusion
from .schema import ValidationError

VERSION = "house-native-fullmix-bass-repair-v1"
BANDS = ((25., 90.), (90., 250.))
# Bounded and conservative: a weak-onset source needs measurable benefit in
# both independent low-band windows before replacing the existing instrument.
# NOT an optimized professional mix target or perceptual-quality metric.
MIN_RELATIVE_OFFBEAT_GAIN_DB = (1.0, 1.0)
MIN_ABSOLUTE_OFFBEAT_GAIN_DB = (1.0, 1.0)
MAX_KICK_NEAR_ENERGY_LOSS_DB = (1.5, 1.5)


def _pocket_values(evidence):
    if (type(evidence) is not dict or evidence.get("version") != POCKET_VERSION or
            evidence.get("section") != "Groove" or
            type(evidence.get("kick_onsets_used")) is not int or
            evidence["kick_onsets_used"] < 4 or
            type(evidence.get("bands")) is not list or
            len(evidence["bands"]) != 2):
        raise ValidationError("complete real native Groove pocket evidence required")
    values = []
    powers = []
    for row, span in zip(evidence["bands"], BANDS):
        if type(row) is not dict or row.get("hz") != list(span):
            raise ValidationError("unexpected native bass-pocket bands")
        ratio = row.get("kick_near_0_100ms_vs_offbeat_200_300ms_db")
        near = row.get("near_mean_power")
        off = row.get("offbeat_mean_power")
        if any(type(x) not in (int, float) or not math.isfinite(x)
               for x in (ratio, near, off)):
            raise ValidationError("nonfinite native bass-pocket powers")
        if near <= 0 or off <= 0:
            raise ValidationError("silent native bass-pocket energy")
        # Native pocket reports are rounded to 3 decimals for the ratio
        # and 6 decimals for the powers. Enforce numerical coherence rather
        # than trusting an arbitrary ratio that contradicts the waveform.
        observed = 10*math.log10(near/off)
        if abs(observed-ratio) > 0.01:
            raise ValidationError("inconsistent native beat/offbeat energy receipt")
        values.append(float(ratio))
        # A ratio alone is gameable: reducing the kick can make it appear
        # that the bass pocket improved. Preserve absolute offbeat energy
        # and the near-kick window as independent causal diagnostics.
        powers.append((float(near), float(off)))
    return values, powers


def review_fullmix_bass_rescue(original, candidate, *,
                               source_sha256, source_onset_gate,
                               candidate_onset_gate, candidate_fit,
                               native_roundtrip_verified):
    """Hard gate using source-aligned live native measurements and explicit veto.

    This pure deterministic decision only evaluates *technical* replacement
    eligibility after the initial selected source has a real hard onset fault.
    Caller separately validates clip-free audio, true peak, unchanged MIDI,
    source provenance, and that all WAVs are actual host renders.
    """
    if native_roundtrip_verified is not True:
        raise ValidationError("candidate native save/reopen must be verified")
    veto = source_exclusion("bass", source_sha256)
    if (type(source_onset_gate) is not dict or
            type(candidate_onset_gate) is not dict or
            type(source_onset_gate.get("hard_flags")) is not list or
            type(candidate_onset_gate.get("hard_flags")) is not list or
            type(candidate_fit) is not dict or
            type(candidate_fit.get("warnings")) is not list):
        raise ValidationError("complete onset and actual native context required")
    before, original_powers = _pocket_values(original)
    after, candidate_powers = _pocket_values(candidate)
    if (original["kick_onsets_used"] != candidate["kick_onsets_used"] or
            original.get("tempo_bpm") != candidate.get("tempo_bpm")):
        raise ValidationError("locked kick onsets and BPM required")
    if not source_onset_gate["hard_flags"]:
        raise ValidationError("automatic source replacement requires baseline hard fault")
    delta = [round(a - b, 3) for a, b in zip(before, after)]
    near_delta = [round(10*math.log10(b[0]/a[0]), 3)
                  for a, b in zip(original_powers, candidate_powers)]
    offbeat_delta = [round(10*math.log10(b[1]/a[1]), 3)
                     for a, b in zip(original_powers, candidate_powers)]
    if candidate_onset_gate["hard_flags"]:
        status = "REJECT_CANDIDATE_HARD_ONSET_FAULT"
    elif (candidate_onset_gate.get("requires_fullmix_context_review") is True
          or candidate_onset_gate.get("review_flags")):
        # Sustained/slow-attack status is an unresolved contextual question,
        # not an authorization to select it automatically as a driving bass.
        status = "DEFER_UNRESOLVED_SOURCE_ARTICULATION_REVIEW"
    elif veto:
        status = "REJECT_PRODUCER_SOURCE_VETO"
    elif any(x in candidate_fit["warnings"] for x in (
            "kick_bass_sub_destructive_summation",
            "full_mix_sub_mono_folddown_loss")):
        status = "REJECT_NATIVE_SUB_OR_MONO_FAULT"
    elif any(v < minimum for v, minimum in
             zip(delta, MIN_RELATIVE_OFFBEAT_GAIN_DB)):
        status = "REJECT_NO_MEANINGFUL_FULLMIX_OFFBEAT_REPAIR"
    elif any(v < minimum for v, minimum in
             zip(offbeat_delta, MIN_ABSOLUTE_OFFBEAT_GAIN_DB)):
        status = "REJECT_NO_ABSOLUTE_OFFBEAT_ENERGY_GAIN"
    elif any(v < -maximum for v, maximum in
             zip(near_delta, MAX_KICK_NEAR_ENERGY_LOSS_DB)):
        status = "REJECT_KICK_NEAR_ENERGY_COLLAPSE"
    else:
        status = "TECHNICAL_REPAIR_ELIGIBLE"
    return {
        "version": VERSION,
        "source_sha256": source_sha256,
        "source_veto_reason": veto,
        "baseline_beat_offbeat_db": before,
        "candidate_beat_offbeat_db": after,
        "relative_offbeat_gain_db": delta,
        "absolute_offbeat_energy_gain_db": offbeat_delta,
        "near_kick_energy_change_db": near_delta,
        "minimum_relative_gain_db": list(MIN_RELATIVE_OFFBEAT_GAIN_DB),
        "minimum_absolute_offbeat_gain_db": list(MIN_ABSOLUTE_OFFBEAT_GAIN_DB),
        "maximum_kick_near_loss_db": list(MAX_KICK_NEAR_ENERGY_LOSS_DB),
        "same_kick_onsets": True,
        "candidate_native_roundtrip_verified": True,
        "status": status,
        "technical_replacement_eligible": status == "TECHNICAL_REPAIR_ELIGIBLE",
        "perceptual_quality": "NOT_EVALUATED",
        "automatic_musical_winner": None,
    }
