"""One-prompt bounded native context check for pre-auditioned Vital runners-up.

Uses the same project MIDI and CC0 drums; checks the initial palette and at
most one bass/chord alternative per role before the final native render.
The default source remains selected unless an alternative resolves a measured
technical failure. No fabricated artistic preference is assigned.
"""
from __future__ import annotations

import json
import math
import wave
import shutil
from copy import deepcopy
from pathlib import Path

from .autonomous_create import _bind, _prepare
from .house_mix_roles import _role_solo, _window
from .house_source_fit import fit_diagnostics
from .house_palette_compare import contextual_review_flags
from .loudness import measure
from .schema import BAR, ValidationError, state_hash, validate
from .sample_assets import write

VERSION = "one-prompt-native-context-v1"
ROLE_TRACK = {"bass":"track-bass","chord":"track-harmony"}
HARD_FLAGS = {"kick_bass_sub_destructive_summation",
              "full_mix_sub_mono_folddown_loss"}


def short_audition_project(project, groove_end_tick):
    """A valid eight-bar native project, not a partial WAV bounce."""
    if groove_end_tick % BAR or not 0 < groove_end_tick < project.length:
        raise ValidationError("audition cut must be an interior bar boundary")
    q=deepcopy(project)
    q.bars=groove_end_tick//BAR
    q.sections=[s for s in q.sections
                if s.start+s.length<=groove_end_tick]
    if [s.name for s in q.sections] != ["Intro","Groove"]:
        raise ValidationError("short native audition requires complete Intro and Groove")
    for track in q.tracks:
        clips=[c for c in track.clips if c.start<groove_end_tick]
        if any(c.start+c.length>groove_end_tick for c in clips):
            raise ValidationError("audition boundary intersects an original MIDI clip")
        track.clips=clips
    q.automation=[lane for lane in q.automation
                  if any(p.tick<=groove_end_tick for p in lane.points)]
    for lane in q.automation:
        lane.points=[p for p in lane.points if p.tick<=groove_end_tick]
    validate(q)
    return q


def choose_sources(project, assignments, shortlist, adapter, defaults,
                   native, sound_assets, stage, *, duration, timeout, library=None):
    """One baseline + at most two conditional groove alternatives; no full-length renders.

    Preconditions: original private Vital patches are bound, conservative gain staging
    and a fully rendered 8/16-bar native calibration WAV exist.
    """
    if not (isinstance(shortlist,dict) and set(shortlist) <= {"bass","chord","pad"}):
        raise ValidationError("invalid same-prompt shortlist")
    if not 16 <= project.bars <= 32:
        raise ValidationError("source shortlist requires short house nucleus")
    original=state_hash(project)
    window=_window(project)
    audition_source=short_audition_project(project,window["end_tick"])
    root=Path(stage)
    scratch=root/"context-shortlist"
    scratch.mkdir(mode=0o700)
    source=Path(stage)/"calibration.wav"
    if not source.is_file():
        raise ValidationError("baseline mix must be native-rendered first")
    # Context checks need only the actual Groove and a short tail.
    excerpt_seconds=min(duration,window["end_seconds"]+6.)
    baseline_crop=scratch/"baseline-short.wav"
    with wave.open(str(source),"rb") as src:
        if (src.getframerate(),src.getnchannels(),src.getsampwidth(),src.getcomptype()) != (48000,2,3,"NONE") or src.getnframes()<round(excerpt_seconds*48000):
            raise ValidationError("invalid bounded native WAV excerpt")
        with wave.open(str(baseline_crop),"wb") as dst:
            dst.setnchannels(2);dst.setsampwidth(3);dst.setframerate(48000)
            dst.writeframes(src.readframes(round(excerpt_seconds*48000)))

    def stem(song, role, patches, path):
        folder=scratch/path
        folder.mkdir(mode=0o700)
        native.export(_role_solo(song,role),sound_assets,patches,folder/"native")
        native.render(folder/"native",folder/"stem.wav",end_seconds=excerpt_seconds)
        return folder/"stem.wav"

    stems={r:stem(audition_source,r,assignments,"base-"+r)
           for r in ("kick","bass")}
    baseline_fit=fit_diagnostics(project,window,stems["kick"],stems["bass"],
                                 None,baseline_crop)
    baseline_meter=measure(baseline_crop,library=library)
    selected=dict(assignments)
    baseline_hard=HARD_FLAGS.intersection(baseline_fit['warnings'])
    # Only genuine hard technical faults authorize expensive alternative
    # native renders. A passing baseline cannot benefit from sound-choice
    # reranking based on uncalibrated audio-quality proxies.
    observations=[]
    for role in ("bass","chord"):
        options=shortlist.get(role,[])
        if not options:
            observations.append({"role":role,"status":"NO_RUNNER_UP"})
            continue
        if len(options)!=1 or options[0].get("status")!="accepted" or options[0].get("runtime_verified") is not True:
            raise ValidationError("one vetted private runner-up per role required")
        entry=options[0]
        # Hard-fault repair is the only evidence-backed reason to replace the
        # original isolated-audition winner. When it passes, rendering extra
        # candidates cannot change the decision and only wastes CPU.
        if not baseline_hard:
            observations.append({
                'role':role,'status':'SKIPPED_BASELINE_TECHNICALLY_ACCEPTABLE',
                'alternative_name':entry['source_preset_name'],
                'source_sha256':entry['source_sha256'],
                'runtime_verified_alternative':True,
                'evaluated_in_native_mix':False,'chosen':False,
                'reason':'original had no hard technical compatibility faults; no supported artistic ranking',
            })
            continue
        role_id=ROLE_TRACK[role]
        prepared=_prepare(adapter,entry,defaults,scratch/("patch-"+role),timeout)
        alt=_bind(project,{role_id:prepared},adapter)
        if state_hash(project)!=original:
            raise ValidationError("source changed while comparing alternatives")
        alternate=dict(assignments);alternate[role_id]=prepared
        folder=scratch/("candidate-"+role)
        folder.mkdir()
        native.export(short_audition_project(alt,window["end_tick"]),sound_assets,alternate,folder/"native")
        native.render(folder/"native",folder/"mix.wav",end_seconds=excerpt_seconds)
        alternative_meter=measure(folder/"mix.wav",library=library)
        if alternative_meter["clipped_samples"] or alternative_meter["true_peak_dbtp"] > -1.:
            observations.append({"role":role,"status":"REJECT_UNSAFE_AUDIO",
                                 "alternative_name":entry["source_preset_name"]})
            continue
        bass_stem=(stem(short_audition_project(alt,window["end_tick"]),"bass",alternate,"alternate-bass")
                   if role=="bass" else stems["bass"])
        fit=fit_diagnostics(alt,window,stems["kick"],bass_stem,
                             None,folder/"mix.wav")
        flags=contextual_review_flags(baseline_meter["integrated_lufs"],
                                       alternative_meter["integrated_lufs"],fit)
        original_hard=HARD_FLAGS.intersection(baseline_fit["warnings"])
        candidate_hard=HARD_FLAGS.intersection(flags)
        # Purely technical fallback. If both are sound, retain the independently
        # auditioned initial winner. No uncalibrated "best groove" score.
        replace=bool(original_hard and not candidate_hard and
                     "large_premix_loudness_change_same_locked_midi" not in flags)
        if replace:
            selected[role_id]=prepared
        observations.append({
            "role":role,
            "original_name":adapter.selection.get(
                next((key for key,value in adapter.selection.items()
                      if value["source_sha256"] != entry["source_sha256"]
                      and value.get("role")==role),""),
                {}).get("source_preset_name","initial verified palette"),
            "alternative_name":entry["source_preset_name"],
            "source_sha256":entry["source_sha256"],
            "baseline_integrated_lufs":baseline_meter["integrated_lufs"],
            "alternative_integrated_lufs":alternative_meter["integrated_lufs"],
            "candidate_context":fit,
            "review_flags":flags,
            "status":"TECHNICAL_RESCUE" if replace else
                     ("REVIEW" if flags else "BASELINE_RETAINED"),
            "chosen":replace,
        })
    if state_hash(project)!=original:
        raise ValidationError("audition changed source composition")
    evidence={"version":VERSION,"source_project_sha256":original,
              "candidate_count":sum(x.get('evaluated_in_native_mix', x['status'] not in ('NO_RUNNER_UP','SKIPPED_BASELINE_TECHNICALLY_ACCEPTABLE')) for x in observations),
              "verified_runner_ups":sum(x['status']!='NO_RUNNER_UP' for x in observations),
              "skipped_native_replacements":sum(x['status']=='SKIPPED_BASELINE_TECHNICALLY_ACCEPTABLE' for x in observations),
              "audition_render_seconds":excerpt_seconds,
              "audition_bars":audition_source.bars,
              "audition_source_canonical_sha256":state_hash(audition_source),
              "baseline_context":baseline_fit,
              "comparisons":observations,
              "source_policy":"initial independently vetted palette retained unless an alternative resolves a measured hard fault",
              "no_perceptual_winner":True,
              "full_length_rendered_for_candidates":False,
              "selection_mode":"conditional hard-fault remediation, not automatic perceptual ranking",
              "quality_judgment":"NOT_EVALUATED"}
    write(root/"context-shortlist-evidence.json",evidence)
    # Keep only chosen private patches; discard temporary native render artifacts.
    for folder in scratch.iterdir():
        if folder.name.startswith("patch-") and folder/"patch" in selected.values():
            continue
        if folder.is_dir():shutil.rmtree(folder)
        else:folder.unlink()
    scratch.rmdir() if not list(scratch.iterdir()) else None
    return selected,evidence
