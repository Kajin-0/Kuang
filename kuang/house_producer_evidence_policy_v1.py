"""Conservative autonomous producer decisions using verified native evidence.

A practical noninteractive fallback until a calibrated listening model exists.
A known human preference dominates spectral heuristics. If a user reports a
clear defect but cannot distinguish limited A/Bs, choose the *smallest*
reversible measured correction, not a claimed artistic winner. No source
library, song notes or plugin states are modified by this policy.
"""
from __future__ import annotations
import math
from .schema import ValidationError

VERSION="house-producer-evidence-policy-v1"

def decide_chord_trial(evidence,*,preferred_variant=None,reported_problem=None):
    if type(evidence) is not dict or evidence.get("version")!="house-chord-cohesion-native-ab-v1":
        raise ValidationError("verified source chord experiment required")
    candidates=evidence.get("candidates")
    if type(candidates) is not list or len(candidates)<2:
        raise ValidationError("two or more verified real native candidates required")
    by_label={}
    for row in candidates:
        label=row.get("variant")
        if (type(label) is not str or label in by_label or
            not row.get("native_same_bounce_path") or not row.get("midi_locked") or
            row.get("clipped_samples")!=0 or
            type(row.get("true_peak_dbtp")) not in (int,float) or
            not math.isfinite(row["true_peak_dbtp"]) or row["true_peak_dbtp"]>-1. or
            type(row.get("matched_lufs")) not in (int,float) or
            not math.isfinite(row["matched_lufs"])):
            raise ValidationError("unverified or unsafe native source trial")
        by_label[label]=row
    baseline=by_label.get("A-original")
    if baseline is None:raise ValidationError("original safe native reference missing")
    if max(row["matched_lufs"] for row in candidates)-min(row["matched_lufs"] for row in candidates)>.2:
        raise ValidationError("candidate loudness mismatch prevents fair comparison")
    if preferred_variant is not None:
        if type(preferred_variant) is not str or preferred_variant not in by_label:
            raise ValidationError("reported human preference must match real variant")
        chosen=preferred_variant
        reason="Explicit user preference for this song takes precedence over acoustic proxies."
        status="USER_APPROVED_FOR_THIS_SONG"
    elif reported_problem=="chords_too_loud":
        eligible=sorted((abs(row.get("chord_gain_offset_db")),row["variant"])
                        for row in candidates
                        if type(row.get("chord_gain_offset_db")) in (int,float) and
                            -3<=row["chord_gain_offset_db"]<0 and
                            row.get("source_sha256")==baseline.get("source_sha256"))
        if eligible:
            chosen=eligible[0][1]
            reason="Reported chord dominance; smallest measured bounded fader reduction is the conservative reversible correction."
            status="PROVISIONAL_AGENT_CHOICE"
        else:
            chosen="A-original"
            reason="No safe source-preserving gain correction; avoid speculative preset changes."
            status="NO_CHANGE"
    else:
        chosen="A-original"
        reason="No reliable user preference or defensible corrective hypothesis; retain incumbent."
        status="NO_CHANGE"
    return {
       "version":VERSION,"source_song":evidence.get("song"),
       "source_original_canonical_hash":evidence.get("source_original_canonical_hash"),
       "chosen_variant":chosen,"selected_project_hash":by_label[chosen]["candidate_canonical_hash"],
       "status":status,"decision_reason":reason,
       "native_safety_validated":True,"listening_quality_proven":preferred_variant is not None,
       "not_a_global_source_preset_default":True,
       "original_project_preserved":True,
       "promote_to_global_house_default":False,
    }
