"""Style-aware, opt-in pre-drop negative space on an existing full-house song.

Subtracts only a bounded number of existing Build-section drum hits before
the Main Drop; preserves the original eight-bar groove pocket, all other
sections, bass, chords, synth sources, and original drum note attributes.
Recomputes actual kick-aligned duck automation from the edited MIDI.
"""
from copy import deepcopy
from . import midi
from .house_full_arranger import _build_lanes
from .schema import BAR,PPQ,ValidationError,state_hash,validate

VERSION="house-predrop-withdrawal-v1"
RHYTHM_ROLES=("kick","snare","hats","open_hat","percussion")

def withdraw_predrop(project,*,beats=None):
    validate(project)
    sections={s.name:s for s in project.sections}
    if (not {"Build","Main Drop","Groove A"}.issubset(sections) or
        sections["Build"].start+sections["Build"].length != sections["Main Drop"].start):
        raise ValidationError("adjacent validated Build and Main Drop required")
    style=project.metadata.get("arrangement_profile",project.metadata.get("groove_profile"))
    if style not in ("straight","jackin","deep","minimal"):
        raise ValidationError("existing arrangement style required")
    # Only jackin's full-bar silence passed a real native contrast gate.
    # Other profiles remain conservative and opt-in pending their own tests.
    target=4 if style=="jackin" else 1 if style in ("deep","minimal") else 2
    if beats is not None:
        if type(beats) is not int or beats not in (1,2,4):
            raise ValidationError("only 1, 2 or 4 final pre-drop beats allowed")
        target=beats
    before=state_hash(project)
    alt=deepcopy(project)
    build=sections["Build"]
    release=build.start+build.length
    mute_from=release-target*PPQ
    old=midi.export_bytes(project)
    removed={}
    for role in RHYTHM_ROLES:
        track=next((t for t in alt.tracks if t.id=="track-"+role),None)
        if track is None:continue
        deleted=0
        for clip in track.clips:
            surviving=[]
            for note in clip.notes:
                at=clip.start+note.start
                if mute_from<=at<release:
                    deleted+=1
                else:surviving.append(note)
            clip.notes=surviving
        # no MIDI role or clip is deleted; empty clips are valid, preserve
        # existing note attributes before gap and all section boundaries.
        removed[role]=deleted
    if not removed.get("kick",0):
        raise ValidationError("predrop must remove at least one actual kick")
    # Existing kick-scheduled bass/pad duck recovery should not keep pumping
    # for a kick that was intentionally removed. Recreate the known lanes.
    _build_lanes(alt)
    alt.metadata["predrop_withdrawal_version"]=VERSION
    alt.metadata["predrop_withdrawal_beats"]=str(target)
    validate(alt)
    if old==midi.export_bytes(alt):
        raise ValidationError("candidate is inaudible at MIDI level")
    if any(a.instrument!=b.instrument or a.controls!=b.controls or
           a.effects!=b.effects or a.sends!=b.sends for a,b in zip(project.tracks,alt.tracks)):
        raise ValidationError("unrelated source/control or plugin change")
    if state_hash(project)!=before:raise ValidationError("source project mutated")
    for role in ("bass","harmony","pad"):
        pa=next((t for t in project.tracks if t.id=="track-"+role),None)
        pb=next((t for t in alt.tracks if t.id=="track-"+role),None)
        if pa!=pb:raise ValidationError("musical source altered")
    for role in RHYTHM_ROLES:
        orig=next((t for t in project.tracks if t.id=="track-"+role),None)
        trial=next((t for t in alt.tracks if t.id=="track-"+role),None)
        if orig is None:continue
        def outside(track):
            return sorted((c.start+n.start,n.duration,n.pitch,n.velocity,n.channel)
                for c in track.clips for n in c.notes
                if not (mute_from<=c.start+n.start<release))
        if outside(orig)!=outside(trial):
            raise ValidationError("altered notes outside release gap")
    return alt,{
      "version":VERSION,"source_sha256":before,"candidate_sha256":state_hash(alt),
      "profile":style,"beats_removed":target,"gap_start_tick":mute_from,
      "main_drop_start_tick":release,"removed_existing_drum_notes":removed,
      "whole_song_structure_preserved":True,
      "groove_a_exact":True,"kick_bass_chords_patches_unmodified":True,
      "source_immutable":True,"separate_groove_impact_calibration":False,
      "human_preference":None,"automatic_winner":None,
      "scope":"subtraction of final Build drum attacks only, no master-gain lift",
    }


def decide_native_predrop(original, candidate, *, profile, minimum_contrast_db=2.):
    """Reject ineffective, destructive or unsafe native Build->Drop changes.

    This judges a *verifiable physical result*, not human taste. The working
    agent may retain a technically eligible candidate as an opt-in trial;
    it is not automatically an across-style mastered release standard.
    """
    from math import isfinite
    if profile not in ("straight","jackin","deep","minimal") or minimum_contrast_db!=2.:
        raise ValidationError("verified profile and predeclared threshold required")
    required=("native_hash","native_lufs","true_peak_dbtp","clipped_samples",
              "pre_gap_reference_rms_dbfs","last_beats_rms_dbfs",
              "first_drop_bar_rms_dbfs","drop_over_last_gap_db","audio_sha256")
    for row in (original,candidate):
        if type(row) is not dict or any(k not in row for k in required):
            raise ValidationError("incomplete native transition evidence")
        if any(type(row[k]) not in (int,float) or not isfinite(row[k])
               for k in required[1:7] if k!="clipped_samples"):
            raise ValidationError("nonfinite native measurements")
        if type(row["drop_over_last_gap_db"]) not in (int,float) or not isfinite(row["drop_over_last_gap_db"]):
            raise ValidationError("invalid measured drop contrast")
        if (type(row["clipped_samples"]) is not int or row["clipped_samples"]!=0 or
            row["true_peak_dbtp"]>-1 or
            type(row["audio_sha256"]) is not str or len(row["audio_sha256"])!=64 or
            type(row["native_hash"]) is not str or len(row["native_hash"])!=64):
            raise ValidationError("unsafe or unauthenticated native bounce")
    if original["native_hash"]==candidate["native_hash"]:
        raise ValidationError("candidate must have a distinct native song")
    improvement=candidate["drop_over_last_gap_db"]-original["drop_over_last_gap_db"]
    drop_drift=abs(candidate["first_drop_bar_rms_dbfs"]-original["first_drop_bar_rms_dbfs"])
    previous_drift=abs(candidate["pre_gap_reference_rms_dbfs"]-original["pre_gap_reference_rms_dbfs"])
    pass_gate=(improvement>=minimum_contrast_db and drop_drift<=.25 and previous_drift<=.15)
    return {
        "version":VERSION,
        "profile":profile,
        "contrast_improvement_db":round(improvement,3),
        "unchanged_drop_rms_drift_db":round(drop_drift,3),
        "unchanged_earlier_build_rms_drift_db":round(previous_drift,3),
        "minimum_contrast_gate_db":minimum_contrast_db,
        "decision":"TECHNICALLY_ELIGIBLE_OPTIN" if pass_gate else "RETAIN_ORIGINAL",
        "default_enabled":False,
        "not_a_human_listening_score":True,
        "native_verified":True,
    }
