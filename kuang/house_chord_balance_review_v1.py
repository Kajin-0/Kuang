"""Reversible, bounded chord gain-only source-aware producer audition.

No automatic preference or source replacement. Preserve all MIDI, presets,
effects, routing and automation times. Requires real native A/B to evaluate.
"""
from copy import deepcopy
from .schema import validate, ValidationError, state_hash
from . import midi

VERSION="house-chord-balance-review-v1"


def chord_gain_candidate(source, offset_db):
    validate(source)
    if type(offset_db) not in (float,int) or offset_db not in (-2.,-3.):
        raise ValidationError("only conservative -2dB/-3dB chord audits allowed")
    result=deepcopy(source)
    chords=next((t for t in result.tracks if t.id=="track-harmony"),None)
    if chords is None:raise ValidationError("chord role missing")
    chords.controls["mixer.gain_db"]+=offset_db
    for lane in result.automation:
        if lane.target_id==chords.id and lane.parameter_id=="mixer.gain_db":
            for p in lane.points:p.value+=offset_db
    validate(result)
    if midi.export_bytes(result)!=midi.export_bytes(source):
        raise ValidationError("chord fader change altered MIDI")
    if result.sections!=source.sections:raise ValidationError("song structure changed")
    for a,b in zip(source.tracks,result.tracks):
        if a.id!="track-harmony" and a!=b:
            raise ValidationError("unrelated role altered")
        if (a.instrument,a.clips,a.effects,a.sends,a.output_master)!=(
                b.instrument,b.clips,b.effects,b.sends,b.output_master):
            raise ValidationError("source patch, MIDI or signal path altered")
    for a,b in zip(source.automation,result.automation):
        if (a.id,a.target_id,a.parameter_id)!=(b.id,b.target_id,b.parameter_id):
            raise ValidationError("automation lane identities changed")
        if [p.tick for p in a.points]!=[p.tick for p in b.points]:
            raise ValidationError("automation times changed")
        offset=offset_db if a.target_id=="track-harmony" and a.parameter_id=="mixer.gain_db" else 0.
        if any(abs(x.value+offset-y.value)>1e-8 for x,y in zip(a.points,b.points)):
            raise ValidationError("automation envelope changed shape")
    return result,{"version":VERSION,"original_sha256":state_hash(source),
       "candidate_sha256":state_hash(result),"chord_fader_offset_db":offset_db,
       "changed_fields":["track-harmony mixer.gain_db",
                         "track-harmony existing mixer.gain_db automation values"],
       "original_midi_exact":True,"source_patch_preserved":True,
       "human_preference":None,"auto_winner":False,"mastering_claim":"NONE"}
