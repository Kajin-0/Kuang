"""Bounded, optional native pad level guard driven by full-section rendered RMS.

Uses both 100/400ms P95 and *sample* peaks, not full-song LUFS or a single
isolated-preset RMS. This cannot judge musical taste or true-peak mastering.
"""
from __future__ import annotations
import math
from copy import deepcopy

from . import midi
from .schema import ValidationError, state_hash, validate

VERSION="native-pad-multisection-level-v1"
MAX_TRIM_DB=12.0
DEADBAND_DB=1.5
PEAK_TOLERANCE_DB=1.0


def _metric(section, name):
    if name in ("window_100ms", "window_400ms"):
        part=section.get(name)
        v=part.get("p95_rms_dbfs") if type(part) is dict else None
    else:
        v=section.get("sample_peak_dbfs")
    if type(v) not in (float,int) or not math.isfinite(v) or not -180<v<3:
        raise ValidationError("missing pad native section measurement: "+name)
    return float(v)


def recommend_trim(pad_levels, harmony_levels, active_sections):
    """Return bounded gain move; does not trim if role is already balanced.

    Input stems must be rendered at the actual final track gain/automation
    with unchanged native effects on identical project and regions.
    """
    if type(active_sections) not in (list,tuple) or not active_sections or any(
            type(s) is not str for s in active_sections):
        raise ValidationError("explicit active pad sections required")
    if len(set(active_sections))!=len(active_sections):
        raise ValidationError("duplicate active pad section")
    if (type(pad_levels) is not dict or type(harmony_levels) is not dict or
            pad_levels.get("version")!="house-native-section-levels-v1" or
            harmony_levels.get("version")!="house-native-section-levels-v1"):
        raise ValidationError("native section measurements required")
    p=pad_levels.get("sections");h=harmony_levels.get("sections")
    if type(p) is not dict or type(h) is not dict:
        raise ValidationError("native sections absent")
    evidence=[];requested=0.
    for name in active_sections:
        a=p.get(name);b=h.get(name)
        if type(a) is not dict or type(b) is not dict:
            raise ValidationError("pad/harmony active section missing")
        if a.get("start_seconds")!=b.get("start_seconds") or a.get("end_seconds")!=b.get("end_seconds"):
            raise ValidationError("pad/harmony source windows misaligned")
        metrics={}
        for key,label,allow in (
            ("window_100ms","p95_100ms",0.),
            ("window_400ms","p95_400ms",0.),
            ("sample_peak_dbfs","sample_peak",PEAK_TOLERANCE_DB),
        ):
            pa=_metric(a,key);ha=_metric(b,key)
            gap=pa-ha
            metrics[label+"_pad_minus_harmony_db"]=round(gap,3)
            requested=max(requested,gap-allow)
        evidence.append({"section":name,**metrics})
    requested=max(0.,requested)
    trim=0. if requested<DEADBAND_DB else -min(MAX_TRIM_DB,requested)
    return round(trim,3),{
        "version":VERSION,
        "active_sections":list(active_sections),
        "section_metrics":evidence,
        "requested_attenuation_db":round(requested,3),
        "applied_pad_trim_db":round(trim,3),
        "bounded_at_12db":requested>MAX_TRIM_DB,
        "deadband_db":DEADBAND_DB,
        "peak_tolerance_db":PEAK_TOLERANCE_DB,
        "goal":"supporting pad no louder than existing harmony in comparable active sections",
        "measurement":"100/400ms RMS P95 and PCM sample peak, all actual final-source native sections",
        "true_peak_judged_by_separate_native_render":True,
        "perceptual_quality":"NEEDS_LISTENING",
        "limitations":[
            "Harmonies are an experimental reference, not an established mix standard.",
            "Source timbres/effects can make equal RMS sound differently loud.",
            "PCM sample peaks do not replace an oversampled true-peak check.",
            "Does not automatically adjust kick, bass, harmonic processing, or section presence."
        ]
    }


def apply_trim(project,db):
    if type(db) not in (float,int) or not math.isfinite(db) or not -MAX_TRIM_DB<=db<=0:
        raise ValidationError("pad attenuation must be bounded")
    original_hash=state_hash(project)
    old_midi=midi.export_bytes(project)
    out=deepcopy(project)
    pad=next((t for t in out.tracks if t.id=="track-pad" and t.kind=="midi"),None)
    if pad is None:
        raise ValidationError("editable pad track missing")
    if db:
        pad.controls["mixer.gain_db"]=round(pad.controls["mixer.gain_db"]+db,6)
        for lane in out.automation:
            if lane.target_id=="track-pad" and lane.parameter_id=="mixer.gain_db":
                for point in lane.points:point.value=round(point.value+db,6)
    validate(out)
    if original_hash!=state_hash(project) or old_midi!=midi.export_bytes(out) or project.sections!=out.sections:
        raise ValidationError("pad gain changed source or musical score")
    for a,b in zip(project.tracks,out.tracks):
        if (a.id,a.instrument,a.clips,a.effects,a.sends,a.output_master)!=(b.id,b.instrument,b.clips,b.effects,b.sends,b.output_master):
            raise ValidationError("pad balancing modified music or source")
        if a.id!="track-pad" and a.controls!=b.controls:
            raise ValidationError("pad balancing modified another track")
    return out
