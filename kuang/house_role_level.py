"""Conservative per-role audition-level compensation for private house sources.

This is an optional producer-template gain-staging experiment, NOT a music
quality ranker. It uses relative verified Vital preset audition RMS to constrain
gross source loudness mismatch before the final editable native render.
"""
from __future__ import annotations

import math
from copy import deepcopy

from . import midi
from .schema import ValidationError, validate, state_hash

VERSION = "house-source-relative-chord-level-v1"
MAX_TRIM_DB = 3.0
MIN_RELATIVE_DB = -8.0
MAX_RELATIVE_DB = -2.0


def _rms(entry, role):
    if not isinstance(entry, dict) or entry.get("status") != "accepted" or entry.get("runtime_verified") is not True:
        raise ValidationError("private "+role+" source must have verified audition")
    value = entry.get("features", {}).get("rms")
    if type(value) not in (float, int) or not math.isfinite(value) or not 1e-5 <= value <= 1.:
        raise ValidationError("invalid "+role+" audition RMS")
    return float(value)


def chord_trim(selection):
    """Constrain relative audition RMS mismatch with at most +/-3 dB.

    The -8..-2 dB *source audition* ratio is an explicit experimental
    engineering deadband, not a validated perceptual / mix threshold.
    Nothing is changed within the deadband. Bass/kick MIDI/FX/gains stay fixed.
    """
    if not isinstance(selection, dict) or selection.get("status") != "complete":
        raise ValidationError("complete verified private palette required")
    roles = selection.get("roles")
    if not isinstance(roles, dict) or not {"bass", "chord"} <= roles.keys():
        raise ValidationError("bass/chord palette identities required")
    rms_bass = _rms(roles["bass"], "bass")
    rms_chord = _rms(roles["chord"], "chord")
    relative = 20 * math.log10(rms_chord/rms_bass)
    if relative < MIN_RELATIVE_DB:
        raw_delta = MIN_RELATIVE_DB-relative
    elif relative > MAX_RELATIVE_DB:
        raw_delta = MAX_RELATIVE_DB-relative
    else:
        raw_delta = 0.
    bounded = max(-MAX_TRIM_DB,min(MAX_TRIM_DB,raw_delta))
    return round(bounded,4), {
        "relative_audition_rms_db":round(relative,4),
        "bass_audition_rms":rms_bass,"chord_audition_rms":rms_chord,
        "requested_db":round(raw_delta,4),
        "bounded_db":round(bounded,4),
        "clamped":abs(raw_delta)>MAX_TRIM_DB,
    }


def apply_chord_calibration(project, selection):
    trim, input_evidence = chord_trim(selection)
    old_hash=state_hash(project)
    old_midi=midi.export_bytes(project)
    out=deepcopy(project)
    harmony=next((t for t in out.tracks if t.id == "track-harmony"),None)
    if harmony is None or harmony.instrument is None:
        raise ValidationError("missing editable chord source")
    before_controls=dict(harmony.controls)
    lane_count=0
    if trim:
        harmony.controls["mixer.gain_db"] = round(harmony.controls["mixer.gain_db"]+trim,6)
        for lane in out.automation:
            if lane.target_id == harmony.id and lane.parameter_id == "mixer.gain_db":
                lane_count+=1
                for point in lane.points:point.value=round(point.value+trim,6)
    validate(out)
    if midi.export_bytes(out) != old_midi or project.sections != out.sections or state_hash(project) != old_hash:
        raise ValidationError("chord gain adjustment changed MIDI, sections or source")
    for t,u in zip(project.tracks,out.tracks):
        if t.id != u.id or (t.instrument,t.effects,t.clips,t.sends,t.output_master) != (u.instrument,u.effects,u.clips,u.sends,u.output_master):
            raise ValidationError("chord gain adjustment changed musical or source identity")
        if t.id != harmony.id and t.controls != u.controls:
            raise ValidationError("chord calibration changed another track gain")
    return out,{
        "version":VERSION,
        "selected_sources":{
            role:selection["roles"][role]["source_sha256"]
            for role in ("bass","chord")},
        **input_evidence,
        "harmony_gain_db_before":before_controls["mixer.gain_db"],
        "harmony_gain_db_after":harmony.controls["mixer.gain_db"],
        "automation_lanes_updated":lane_count,
        "all_other_tracks_unchanged":True,
        "midi_and_effects_unchanged":True,
        "source_project_sha256":old_hash,
        "technical_status":"GAIN_BOUNDED",
        "perceptual_quality":"NOT_EVALUATED",
        "reason":"Conservative source-level consistency only; no subjective preference or fullmix optimality implied",
    }
