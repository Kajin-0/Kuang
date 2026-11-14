"""Locked-MIDI house source A/B from two previously verified private sessions.

Compares alternative Vital patch states on exactly the same project MIDI,
effects, arrangement and drum sources. Only an explicitly requested bass/chord
instrument can change. Short native renders, bounded source-fit technical
checks and attenuation-only A/B: NO claimed perceptual winner or release master.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import tempfile
from copy import deepcopy
from pathlib import Path

from . import midi
from .external_synth import inventory
from .house_mix_roles import _host_adapter, _role_solo, _rms_region, _window
from .house_mix_spectrum import band_rms, role_spectral_diagnostics
from .house_source_fit import fit_diagnostics
from .house_mix_review import prepare_ab
from .loudness import measure
from .sample_assets import digest, write
from .schema import ValidationError, load, state_hash, validate
from .vitalium_patch import PLUGIN_ID

VERSION = "house-locked-source-compare-v1"
ROLE_TRACKS = {"bass":"track-bass", "chord":"track-harmony"}


def _source(root):
    raw=Path(root).absolute()
    if raw.is_symlink():
        raise ValidationError("candidate source symlink not allowed")
    root=raw.resolve(strict=True)
    selection=json.loads((root/"palette"/"selection.json").read_text())
    report=json.loads((root/"report.json").read_text())
    project=load(root/"project.kuang.json")
    if selection.get("status")!="complete" or not report.get("native_save_reopen_equal"):
        raise ValidationError("private source was not native-verified")
    if not (root/"native"/"session.scraft").is_file() or not (root/"preview.wav").is_file():
        raise ValidationError("private source native/session assets missing")
    if not {"bass","chord"} <= set(selection.get("roles",{})):
        raise ValidationError("private source missing bass/chord provenance")
    return root,selection,report,project


def substitute(source, alternate, role):
    """Canonical replacement of just one private instrument state; nothing else."""
    if role not in ROLE_TRACKS:
        raise ValidationError("only bass or chord source replacements are supported")
    track_id=ROLE_TRACKS[role]
    a=next(t for t in source.tracks if t.id==track_id)
    b=next(t for t in alternate.tracks if t.id==track_id)
    if (a.instrument.plugin_ref != PLUGIN_ID or b.instrument.plugin_ref != PLUGIN_ID
            or set(a.instrument.parameters)!=set(b.instrument.parameters)):
        raise ValidationError("incompatible private Vital parameter registry")
    if a.instrument.preset_ref == b.instrument.preset_ref:
        raise ValidationError("identical private source preset cannot be compared")
    q=deepcopy(source)
    changed=next(t for t in q.tracks if t.id==track_id)
    # Native instrument id is tied to destination track. Only plugin state,
    # parameters and hashed source preset identity change.
    changed.instrument=deepcopy(b.instrument)
    changed.instrument.id=a.instrument.id
    validate(q)
    if (midi.export_bytes(q)!=midi.export_bytes(source) or
        q.sections!=source.sections or q.tempo_bpm!=source.tempo_bpm or
        (q.key_tonic,q.key_mode)!=(source.key_tonic,source.key_mode)):
        raise ValidationError("locked arrangement/MIDI changed when replacing source")
    for t,u in zip(source.tracks,q.tracks):
        if (t.id,t.kind,t.clips,t.controls,t.effects,t.sends,t.output_master)!=(u.id,u.kind,u.clips,u.controls,u.effects,u.sends,u.output_master):
            raise ValidationError("source replacement changed MIDI, routing, FX or gains")
        if t.id!=track_id and t.instrument!=u.instrument:
            raise ValidationError("unrelated source instrument changed")
    return q


def contextual_review_flags(original_lufs, alternative_lufs, fit):
    if (type(original_lufs) not in (int,float) or
        type(alternative_lufs) not in (int,float) or
        not math.isfinite(original_lufs) or not math.isfinite(alternative_lufs) or
        type(fit) is not dict or type(fit.get('warnings')) is not list):
        raise ValidationError('invalid contextual comparison measurements')
    flags=list(fit['warnings'])
    # An unexpectedly large level change with identical MIDI/faders can be
    # legitimate timbre, but requires gain-matched contextual inspection.
    # This is a review trigger, never evidence of lower *musical quality*.
    if abs(alternative_lufs-original_lufs)>3.:
        flags.append('large_premix_loudness_change_same_locked_midi')
    return flags


def compare_existing(source, alternate, soundcraft, output, *,
                     swap="bass", library=None):
    """Produces exactly one alternate source candidate with matched A/B audio."""
    if swap not in ROLE_TRACKS:
        raise ValidationError("only bass or chord source replacements are supported")
    src,sel,source_report,original=_source(source)
    alt,sel_alt,alt_report,variant=_source(alternate)
    dest=Path(output).absolute()
    workspace=Path.cwd().resolve()
    if (src==alt or dest.exists() or dest.is_symlink() or
        not dest.parent.is_dir() or
        not all(x.is_relative_to(workspace) for x in (src,alt,dest.resolve())) or
        dest.resolve().is_relative_to(src) or dest.resolve().is_relative_to(alt)):
        raise ValidationError("private separate source and fresh workspace output required")
    for key in ("catalog_sha256","preset_root"):
        if sel.get(key)!=sel_alt.get(key):
            raise ValidationError("alternate source library/catalog differs")
    if sel.get("plugin",{}).get("module_sha256")!=sel_alt.get("plugin",{}).get("module_sha256"):
        raise ValidationError("private pinned Vital plugin differs")
    if original.bars not in (16,32) or not source_report.get("groove_template"):
        raise ValidationError("source comparison restricted to 16/32-bar house excerpts")
    new_project=substitute(original,variant,swap)
    chosen=sel_alt["roles"][swap]
    if chosen.get("status")!="accepted" or chosen.get("runtime_verified") is not True:
        raise ValidationError("alternate source preset was not independently auditioned")
    changed_id=ROLE_TRACKS[swap]
    patches={t.id:src/"native"/"patches"/t.id for t in original.tracks
             if t.instrument and t.instrument.plugin_ref==PLUGIN_ID}
    source_patch=alt/"native"/"patches"/changed_id
    if not source_patch.is_dir():
        raise ValidationError("alternate native patch asset missing")
    patches[changed_id]=source_patch
    assets={t.id:src/"native"/"assets"/t.id for t in original.tracks
            if t.instrument and t.instrument.plugin_ref=="soundcraft:sampler"}
    old_mid=midi.export_bytes(original)
    source_hash=state_hash(original)
    baseline_inventory=inventory(src)
    alt_inventory=inventory(alt)
    window=_window(original)
    if (original.tempo_bpm,original.ppq,original.length)!=(new_project.tempo_bpm,new_project.ppq,new_project.length):
        raise ValidationError("source tempo and arrangement changed")
    duration=original.length/original.ppq*60/original.tempo_bpm+12
    with tempfile.TemporaryDirectory(prefix=".house-locked-compare-",dir=dest.parent) as temporary:
        stage=Path(temporary)
        adapter=_host_adapter(src,workspace,stage/"scratch",soundcraft)
        # Extend only the in-memory verified source allowlist; immutable
        # on-disk palette proofs and third-party private assets are untouched.
        adapter.external.selection[chosen["source_sha256"]]=chosen
        if adapter.inspect(src/"native")["canonical_hash"]!=source_hash:
            raise ValidationError("base native source canonical drift")
        changes={}
        for role in ("kick","bass","chords"):
            project = new_project if ROLE_TRACKS.get(role)==changed_id else original
            # This is one baseline-only kick/chords stem, or the newly swapped
            # bass/chords stem, so no redundant complete song renders.
            work=stage/("stem-"+role)
            work.mkdir()
            solo=_role_solo(project,role)
            sub_patches=patches if project is new_project else {
                k:(src/"native"/"patches"/k) for k in patches}
            adapter.export(solo,assets,sub_patches,work/"native")
            adapter.render(work/"native",work/"stem.wav",end_seconds=duration)
            changes[role]=work/"stem.wav"
        session=stage/"candidate"
        session.mkdir()
        adapter.export(new_project,assets,patches,session/"native")
        adapter.save(session/"native",session/"reopened")
        if adapter.inspect(session/"reopened")["canonical_hash"]!=state_hash(new_project):
            raise ValidationError("alternate native state did not survive save/reopen")
        adapter.render(session/"native",session/"candidate.wav",end_seconds=duration)
        master_original=src/"preview.wav"
        master_alternate=session/"candidate.wav"
        original_meter=measure(master_original,library=library)
        alt_meter=measure(master_alternate,library=library)
        if alt_meter["clipped_samples"] or alt_meter["true_peak_dbtp"]>-1.:
            raise ValidationError("alternate source candidate clipped or unsafe true peak")
        if (alt_meter["sample_rate"],alt_meter["channels"],alt_meter["bits_per_sample"]) != (48000,2,24):
            raise ValidationError("altered source PCM format")
        if alt_meter["frames"]!=original_meter["frames"]:
            raise ValidationError("baseline and alternate WAV lengths differ")
        bands={r:band_rms(p,window,windows=8) for r,p in changes.items()}
        fit=fit_diagnostics(new_project,window,changes["kick"],changes["bass"],changes["chords"],master_alternate)
        # Baseline audio and native project are already independently verified.
        ab_out=stage/"ab"
        ab=prepare_ab(master_original,master_alternate,ab_out,library=library)
        review_flags=contextual_review_flags(original_meter['integrated_lufs'],
                                               alt_meter['integrated_lufs'],fit)
        technically_eligible=not fit['warnings'] and alt_meter['clipped_samples']==0
        record={
            "version":VERSION,
            "source_project_sha256":source_hash,
            "alternate_project_sha256":state_hash(new_project),
            "source_midi_sha256":digest(src/"song.mid"),
            "alternate_midi_sha256":digest(src/"song.mid"),
            "locked_midi_identical":midi.export_bytes(new_project)==old_mid,
            "unchanged_key_tempo_sections_effects_drums":True,
            "swapped_role":swap,
            "source_name":sel["roles"][swap]["source_preset_name"],
            "alternate_name":chosen["source_preset_name"],
            "original_premix_meter":original_meter,
            "alternative_premix_meter":alt_meter,
            "alternative_context_fit":fit,
            "alternative_native_spectrum":role_spectral_diagnostics(bands),
            "technically_eligible":technically_eligible,
            "review_flags":review_flags,
            "technical_status":"PASS" if not review_flags else "REVIEW",
            "automatic_source_winner_selected":False,
            "subjective_winner":None,
            "perceptual_quality":"NOT_EVALUATED",
            "matched_comparison_target_lufs":ab["target_lufs"],
            "notes":[
                "The base MIDI, drums, chords (if bass swap) or bass (if chord swap), arrangement and existing routing are unchanged.",
                "Tech eligibility is not a musical winner; source audition provenance remains private.",
                "Measured isolated summation is a hypothetical linear sum, not the nonlinear mix bus.",
                "Only two bounded native source configurations were compared; no broad source search.",
            ]
        }
        if inventory(src)!=baseline_inventory or inventory(alt)!=alt_inventory:
            raise ValidationError("one of the verified private sources changed")
        write(stage/"source-compare-report.json",record)
        # Retain ONLY the alternate native project, alternate original PCM,
        # matched A/B and technical JSON. Delete intermediate isolated stems.
        for role in changes:
            shutil.rmtree(stage/("stem-"+role))
        shutil.rmtree(stage/"scratch",ignore_errors=True)
        shutil.rmtree(session/"reopened",ignore_errors=True)
        dest.mkdir(mode=0o700)
        try:
            for item in stage.iterdir():
                shutil.move(str(item),dest/item.name)
        except BaseException:
            shutil.rmtree(dest)
            raise
    return {"output":str(dest),"swap":swap,"original_name":record["source_name"],
            "alternative_name":record["alternate_name"],"technical_status":record["technical_status"],
            "source_fit_warnings":fit["warnings"],
            "review_flags":review_flags,
            "original_lufs":original_meter["integrated_lufs"],
            "alternate_lufs":alt_meter["integrated_lufs"],
            "subjective_winner":None}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base",required=True)
    p.add_argument("--alternate",required=True)
    p.add_argument("--soundcraft",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--swap",choices=("bass","chord"),default="bass")
    p.add_argument("--library")
    args=p.parse_args(argv)
    try:
        result=compare_existing(args.base,args.alternate,args.soundcraft,args.out_dir,
                                swap=args.swap,library=args.library)
    except (ValidationError,OSError,ValueError,KeyError,TypeError) as exc:
        p.exit(2,"house-locked-source-compare: "+str(exc)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
