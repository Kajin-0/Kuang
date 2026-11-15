"""First-pass house source selection: actual native role audibility and prompt intent.

This module does not assign musical taste or run a language model. It identifies
a candidate search when the source instrument contradicts the intended role.
Candidate suitability is determined on actual locked-MIDI native audio before
any preference decision. No broad "better spectrum = better music" shortcut.
"""
from __future__ import annotations

import math
import re
from .schema import ValidationError

VERSION="house-context-palette-v2"
ROLE="harmony"
# Provisional experiment-trigger only, NOT a mastering/balance target.
CHORD_CRITICALLY_QUIET_REL_KICK_DB=-24.
SOURCE_SEARCH_LIMIT=2
PRESENCE_BANDS=("body_120_500","mids_500_2000","presence_2000_6000")


def _metric(metrics,role,key):
    if type(metrics) is not dict or type(metrics.get(role)) is not dict:
        raise ValidationError("actual native stem for "+role+" required")
    value=metrics[role].get(key)
    if type(value) not in (float,int) or not math.isfinite(value):
        raise ValidationError("nonfinite/missing verified native stem "+role+"."+key)
    return float(value)


def chord_intent(prompt,style):
    """Only explicit chord adjectives; avoid confusing 'minimal' with silence."""
    if type(prompt) is not str or not prompt.strip() or type(style) is not str:
        raise ValidationError("full song prompt/style required")
    p=prompt.casefold()
    if not any(t in p for t in ("chord","stab","piano","keys")):
        return "unspecified"
    if re.search(r"\b(wide|sustained|lush|spacey|full|warm|rich)\b",p):
        return "prominent_sustained"
    if re.search(r"\b(short|staccato|tight|dub|piano\s+house|stab)\b",p):
        return "percussive_stabs"
    return "unspecified"


def review_source(project,*,prompt,profile,stems,source_verified,
                  source_sha256,source_name,runner_up_count):
    """Decide audition/no-audition from actual native audio, not source names."""
    from .schema import state_hash,validate
    validate(project)
    if type(source_verified) is not bool or not source_verified:
        raise ValidationError("only runtime-verified private source allowed")
    if (type(source_sha256) is not str or len(source_sha256)!=64 or
        any(c not in "0123456789abcdef" for c in source_sha256) or
        type(source_name) is not str or not source_name or
        type(runner_up_count) is not int or runner_up_count<0):
        raise ValidationError("verified source catalog provenance required")
    kick=_metric(stems,"kick","rms_dbfs")
    bass=_metric(stems,"bass","rms_dbfs")
    harmony=_metric(stems,"harmony","rms_dbfs")
    if not all(-180<=v<=12 for v in (kick,bass,harmony)):
        raise ValidationError("unreasonable native meter")
    gap=round(harmony-kick,3)
    intent=chord_intent(prompt,profile)
    # Even a very quiet chord is not automatically incorrect. A minimalist
    # low-in-the-mix stab is a legitimate production decision.
    critical=(gap<=CHORD_CRITICALLY_QUIET_REL_KICK_DB)
    emphasize=intent=="prominent_sustained"
    if critical and emphasize and runner_up_count:
        action="AUDITION_VERIFIED_CHORD_ALTERNATIVES"
        reason="Explicit wide/sustained chord intent conflicts with very low native chord audibility."
    elif critical and intent=="percussive_stabs":
        action="RETAIN_WITH_ARTICULATION_REVIEW"
        reason="Quiet short stabs may be intentional; no replacement without a measured source-fit failure."
    else:
        action="KEEP_SOURCE"
        reason="No sufficiently supported contradiction between prompt and measured source."
    return {
       "version":VERSION,"project_sha256":state_hash(project),
       "source_sha256":source_sha256,"source_name":source_name,
       "prompt_chord_intent":intent,"profile":profile,
       "native_kick_rms_dbfs":round(kick,3),
       "native_bass_rms_dbfs":round(bass,3),
       "native_chord_rms_dbfs":round(harmony,3),
       "chord_minus_kick_rms_db":gap,
       "critical_source_audibility_trigger_db":CHORD_CRITICALLY_QUIET_REL_KICK_DB,
       "action":action,"reason":reason,
       "max_candidates":min(SOURCE_SEARCH_LIMIT,runner_up_count) if action=="AUDITION_VERIFIED_CHORD_ALTERNATIVES" else 0,
       "measured_native_mix":False,
       "perceptual_winner":None,"source_replaced":False,
    }


def assess_alternative(review,*,candidate_sha256,candidate_source_verified,
                       original_mix,candidate_mix):
    """Technical candidacy from two genuine equal-context full-mix measurements.

    A candidate can be eligible to LISTEN to, but not chosen as an artistic
    winner. Peak, LUFS, relative bass, stereo/mono and source identity matter.
    """
    if review.get("version")!=VERSION or review.get("action")!="AUDITION_VERIFIED_CHORD_ALTERNATIVES":
        raise ValidationError("a justified source-audibility review is required")
    if (type(candidate_source_verified) is not bool or not candidate_source_verified or
        type(candidate_sha256) is not str or len(candidate_sha256)!=64 or
        candidate_sha256==review["source_sha256"]):
        raise ValidationError("alternative must be independently runtime-verified")
    keys=("integrated_lufs","true_peak_dbtp","presence_1k_4k_rel_30_250_db",
          "lowmid_250_1k_rel_30_250_db","side_mid_db")
    for x in (original_mix,candidate_mix):
        if type(x) is not dict:
            raise ValidationError("real full-mix feature receipt required")
        for k in keys:
            if type(x.get(k)) not in (int,float) or not math.isfinite(x[k]):
                raise ValidationError("nonfinite/missing actual native feature "+k)
        if type(x.get("clipped_samples")) is not int or x["clipped_samples"]<0:
            raise ValidationError("no clipped-sample verification")
    diffs={k:round(candidate_mix[k]-original_mix[k],3) for k in keys}
    safe=(candidate_mix["true_peak_dbtp"]<=-1. and candidate_mix["clipped_samples"]==0)
    # Enormous level changes must be controlled with gain-only A/B, not
    # mistaken for a universally preferred replacement.
    large_gain=abs(diffs["integrated_lufs"])>3.
    return {
        "version":VERSION,"project_sha256":review["project_sha256"],
        "original_source_sha256":review["source_sha256"],
        "candidate_source_sha256":candidate_sha256,
        "real_native_audio_required":True,
        "technical_status":"ELIGIBLE_FOR_GAIN_MATCHED_LISTENING" if safe else "REJECT_NATIVE_AUDIO_SAFETY",
        "native_mix_delta":diffs,"large_source_level_difference":large_gain,
        "preserve_original_on_disk":True,
        "musical_source_compatible":"UNDETERMINED",
        "automatic_winner_selected":False,
        "human_listening_verdict":None,
        "mix_mastering_quality_proven":False,
    }
