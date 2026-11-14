"""Opt-in native pad measurement + bounded trim in the existing production host.

Measure actual selected pad and chord source at final track/FX/automation
levels in all sections where BOTH roles have note onsets. Reuses real rendered
SoundCraft/verified Vital output; no new composer or plugin host.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path

from .house_pad_level import apply_trim, recommend_trim
from .house_section_levels import analyze
from .schema import ValidationError, state_hash, validate
from . import midi
from .loudness import measure


def _solo_role(project, track_id):
    out=deepcopy(project)
    if track_id not in {t.id for t in out.tracks if t.kind=="midi"}:
        raise ValidationError("native pad calibrator missing role "+track_id)
    for t in out.tracks:
        if t.kind=="midi":
            t.controls["mixer.mute"]=0 if t.id==track_id else 1
    validate(out)
    return out


def _active_sections(project):
    tracks={t.id:t for t in project.tracks}
    if not {"track-pad","track-harmony"} <= tracks.keys():
        return [],[]
    sections=[];active=[]
    for sec in project.sections:
        a=sec.start;b=a+sec.length
        secs=(sec.name,a/project.ppq*60/project.tempo_bpm,
              b/project.ppq*60/project.tempo_bpm)
        sections.append(secs)
        if all(any(a<=c.start+n.start<b for c in tracks[role].clips for n in c.notes)
               for role in ("track-pad","track-harmony")):
            active.append(sec.name)
    if len({x[0] for x in sections})!=len(sections):
        raise ValidationError("pad-level calibration requires unique section labels")
    return sections,active


def native_pad_balance(project, native, assignments, sound_assets, stage,
                       *, duration_seconds, library=None):
    """Return (new project, final rendered audio metrics, render receipt, evidence).

    Requires a full valid original final preview already at stage/preview.wav,
    and stage/native to contain the exact original complete project.
    All alternate states are temporary/private and no source output is changed
    until the new full-native render is independently verified.
    """
    stage=Path(stage)
    original_hash=state_hash(project)
    orig_midi=midi.export_bytes(project)
    sections,active=_active_sections(project)
    if not active:
        return project,None,None,{"status":"NO_COMMON_PAD_AND_CHORD_NOTES",
                                 "applied_pad_trim_db":0,"perceptual_quality":"NOT_EVALUATED"}
    patch_ids=set(assignments)
    if not {"track-pad","track-harmony"} <= patch_ids:
        raise ValidationError("pad and harmony private source assignments required")
    measured={}
    for role in ("track-pad","track-harmony"):
        solo=_solo_role(project,role)
        folder=stage/("pad-measure-"+role)
        folder.mkdir(mode=0o700)
        native.export(solo,sound_assets,assignments,folder/"native")
        native.render(folder/"native",folder/"role.wav",
                      end_seconds=duration_seconds+12)
        measured[role]=analyze(folder/"role.wav",sections)
    delta,receipt=recommend_trim(measured["track-pad"],measured["track-harmony"],active)
    receipt["status"]="APPLIED" if delta else "NO_LEVEL_CONFLICT"
    receipt["original_project_sha256"]=original_hash
    receipt["original_midi_unchanged"]=True
    receipt["pad_by_section"]=measured["track-pad"]
    receipt["harmony_by_section"]=measured["track-harmony"]
    receipt["final_native_save_reopen_passed"]=False
    if not delta:
        return project,None,None,receipt

    changed=apply_trim(project,delta)
    if state_hash(project)!=original_hash or midi.export_bytes(changed)!=orig_midi:
        raise ValidationError("pad balancing modified original source or musical MIDI")
    native.export(changed,sound_assets,assignments,stage/"pad-level-native")
    native.save(stage/"pad-level-native",stage/"pad-level-reopened")
    if native.inspect(stage/"pad-level-reopened")["canonical_hash"]!=state_hash(changed):
        raise ValidationError("pad-balanced native project failed save/reopen")
    rendered=native.render(stage/"pad-level-native",stage/"pad-level-preview.wav",
                           end_seconds=duration_seconds+12)
    meter=measure(stage/"pad-level-preview.wav",library=library)
    if meter["clipped_samples"] or meter["true_peak_dbtp"]>-1. or meter["rms"]<1e-6:
        raise ValidationError("pad-balanced final audio failed true-peak/clipping/silence gate")
    receipt["final_native_save_reopen_passed"]=True
    receipt["final_true_peak_dbtp"]=meter["true_peak_dbtp"]
    receipt["final_integrated_lufs"]=meter["integrated_lufs"]
    receipt["perceptual_quality"]="NEEDS_LISTENING"
    return changed,meter,rendered,receipt
