"""Source-aware objective review of real native chord-room/plate stem probes.

Never automatically certifies musical preference. Attack, tail and presence
measurements must derive from a source-locked real native A/B pair.
"""
from __future__ import annotations
import math

from .schema import ValidationError

VERSION="house-v3-space-native-chord-review-v1"


def review_chord_space(stems):
    if type(stems) is not dict or stems.get("source_midi_unchanged") is not True or stems.get("kick_bass_stem_byte_exact") is not True:
        raise ValidationError("source-locked native chord and kick+bass stem evidence required")
    count=stems.get("eligible_isolated_onsets")
    if type(count) is not int or count<8:
        raise ValidationError("at least 8 uncontaminated chord-note windows required")
    keys=("attack_change_db","tail_change_db",
          "chord_to_kick_bass_presence_2k_8k_dry_db",
          "chord_to_kick_bass_presence_2k_8k_wet_db")
    values={}
    for key in keys:
        v=stems.get(key)
        if type(v) not in (float,int) or not math.isfinite(v):
            raise ValidationError("missing finite native chord signal metric: "+key)
        values[key]=float(v)
    warnings=[]
    # Experimental diagnostic flags, not perceptual sound-quality
    # requirements. A long chord tail can be intentional in deep house.
    if values["tail_change_db"]>4.:
        warnings.append("LARGE_WET_TAIL_GAIN_REVIEW_SOURCE_ARTICULATION")
    if values["attack_change_db"]>2.:
        warnings.append("DIRECT_CHORD_ATTACK_ENERGY_CHANGED")
    if values["chord_to_kick_bass_presence_2k_8k_wet_db"] < -12.:
        warnings.append("CHORD_2K_8K_POWER_LOW_RELATIVE_TO_KICK_BASS")
    return {"version":VERSION,"qualified_windows":count,
            "warnings":warnings,
            "requires_source_aware_review":bool(warnings),
            "technical_provenance_valid":True,
            "automatic_musical_winner":None,
            "automatic_global_send_promotion":False}


def recommend_spatial_scene(room_plate_review, room_only, *,
                            dry_width_2k_8k_db):
    """Source-specific technical scene candidate from independent native data.

    Only a source with a diagnosed high-tail room+plate fault can
    consider a separately measured room-only option. No style-name
    heuristics, producer preference inference or automatic default.
    """
    if (type(room_plate_review) is not dict or
        room_plate_review.get("technical_provenance_valid") is not True or
        "LARGE_WET_TAIL_GAIN_REVIEW_SOURCE_ARTICULATION" not in
          room_plate_review.get("warnings", [])):
        raise ValidationError("explicit original room-plate high-tail fault required")
    if type(room_only) is not dict or room_only.get("canonical_roundtrip") is not True:
        raise ValidationError("source-locked native room-only proof required")
    required=("width_2k_8k_db","mono_retention_sub_20_120",
              "chord_tail_vs_dry_db","chord_attack_vs_dry_db",
              "true_peak_dbtp")
    if (type(dry_width_2k_8k_db) not in (float,int) or
        not math.isfinite(dry_width_2k_8k_db)):
        raise ValidationError("missing dry reference width")
    for k in required:
        v=room_only.get(k)
        if type(v) not in (float,int) or not math.isfinite(v):
            raise ValidationError("missing finite native room-only evidence: "+k)
    if type(room_only.get("clipped_samples")) is not int:
        raise ValidationError("missing native clip evidence")
    improvement=round(room_only["width_2k_8k_db"]-dry_width_2k_8k_db,3)
    qualified=(improvement >= 3. and
        room_only["chord_tail_vs_dry_db"] <= 4. and
        room_only["chord_attack_vs_dry_db"] <= 2. and
        room_only["mono_retention_sub_20_120"] >= .995 and
        room_only["true_peak_dbtp"] <= -1. and
        room_only["clipped_samples"] == 0)
    return {
        "version":"house-v3-source-aware-spatial-choice-v1",
        "status":"TECHNICAL_ROOM_ONLY_CANDIDATE" if qualified
                 else "REVIEW_SOURCE_SPACE_UNRESOLVED",
        "upper_width_gain_db":improvement,
        "source_context_only":True,
        "production_default_change":False,
        "musical_winner":None,
    }
