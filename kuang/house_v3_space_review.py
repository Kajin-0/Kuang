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
