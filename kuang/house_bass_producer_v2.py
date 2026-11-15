"""Opt-in, evidence-bounded house bass producer candidates.

An approved A/B in straight house motivated a separate cross-style test.
These moves are audition hypotheses; no automatic improvement ranking or
default composer change. Preserve all original instruments and note content.
"""
from __future__ import annotations

import math
from copy import deepcopy

from . import midi
from .house_bass_syncopation import propose_phrase_pickups
from .schema import ValidationError,state_hash,validate

VERSION="house-bass-producer-cross-style-v2"


def _solo_rms(receipt,role):
    value=receipt.get("role_stems",{}).get(role,{}).get("rms_dbfs")
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValidationError("verified native "+role+" stem RMS required")
    return float(value)


def context_bass_variants(project,*,native_stems,section="Groove A",bars=16):
    """Generate B (gain) and C (gain + sparse late-sixteenth phrase pickups).

    Conditional trial gain is chosen ONLY to test the hypothesis, not a
    calibrated producer-recommended fader level. Existing original gain
    automation is offset with the same constant so its shape is retained.
    """
    validate(project)
    if (type(native_stems) is not dict or
        native_stems.get("native_canonical_sha256")!=state_hash(project) or
        native_stems.get("source_preserved") is not True or
        type(bars) is not int or bars not in (8,16)):
        raise ValidationError("exact intact source and verified native stems required")
    rms_kick=_solo_rms(native_stems,"kick")
    rms_bass=_solo_rms(native_stems,"bass")
    gap=round(rms_bass-rms_kick,3)
    if not -80<=gap<=10:
        raise ValidationError("unexpected native bass relative level")
    # These are intentionally small A/B candidates, not a universal target.
    audition_gain_db=2.0 if gap<=-12 else 1.5 if gap<=-5 else 0.5
    b=deepcopy(project)
    bass=next((t for t in b.tracks if t.id=="track-bass"),None)
    if bass is None:raise ValidationError("bass track missing")
    bass.controls["mixer.gain_db"]+=audition_gain_db
    for lane in b.automation:
        if lane.target_id==bass.id and lane.parameter_id=="mixer.gain_db":
            for point in lane.points:
                point.value+=audition_gain_db
    validate(b)
    if midi.export_bytes(b)!=midi.export_bytes(project):
        raise ValidationError("gain-only trial modified MIDI")
    c,phrase_receipt=propose_phrase_pickups(
        b,section=section,bars=bars,interval_bars=4)
    # A sparse phrase with no existing eligible pickup must remain intact.
    # We may still audition gain B, but cannot fabricate an arbitrary C rhythm.
    if c.sections!=project.sections:
        raise ValidationError("song structure changed")
    for original,trial in zip(project.tracks,c.tracks):
        if original.id!="track-bass" and original!=trial:
            raise ValidationError("unrelated track changed")
        if (original.instrument!=trial.instrument or
            original.effects!=trial.effects or original.sends!=trial.sends):
            raise ValidationError("instrument or effect state changed")
    for orig,trial in zip(project.automation,b.automation):
        if (orig.id,orig.parameter_id,orig.target_id)!=(trial.id,trial.parameter_id,trial.target_id):
            raise ValidationError("automation lane identity changed")
        if [p.tick for p in orig.points]!=[p.tick for p in trial.points]:
            raise ValidationError("automation timing changed")
        offset=audition_gain_db if orig.target_id==bass.id and orig.parameter_id=="mixer.gain_db" else 0.
        if any(abs((old.value+offset)-new.value)>1e-8 for old,new in zip(orig.points,trial.points)):
            raise ValidationError("original gain envelope shape altered")
    return {
        "B":b,
        "C":c,
        "receipt":{
            "version":VERSION,
            "source_sha256":state_hash(project),
            "native_bass_minus_kick_rms_db":gap,
            "conditional_audition_gain_db":audition_gain_db,
            "phase_pickup_receipt":phrase_receipt,
            "locked_components":["kick","other instruments","patches","FX","note pitches","note count","song structure"],
            "technique":"context-conditional bass gain + only eligible existing phrase-ending pickups",
            "goal":"audible low-end impact without losing strong kick or overcomplicating bass",
            "phrase_variant_available":bool(phrase_receipt["changed_existing_notes"]),
            "auto_winner":None,
            "approval":"LISTENING_REQUIRED",
            "default_enabled":False
        },
    }
