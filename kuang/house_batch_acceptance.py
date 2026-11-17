"""Batch acceptance audit for original one-prompt Kuang house template outputs.

This checks deterministic, reproducible engineering fitness across several
prompts. Technical pass is never equivalent to a perceptual music review.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .house_mix_spectrum import band_rms
from .house_source_policy import source_exclusion
from .sample_assets import digest, write
from .schema import ValidationError, load, state_hash
from . import midi

VERSION = "house-batch-acceptance-v1"
# Provisional quality-control flags for a *near-finished* preview, not universal
# mastering laws. These WARN rather than rejecting creative stylistic choices.
PREVIEW_WARNINGS = {
    "max_unused_true_peak_headroom_dbtp": -6.0,
    "min_integrated_lufs": -23.0,
    "max_crest_db": 20.0,
}


def _read(path):
    try:
        data=json.loads(Path(path).read_text())
    except (OSError,ValueError) as exc:
        raise ValidationError("missing or invalid candidate evidence") from exc
    if not isinstance(data,dict):raise ValidationError("invalid candidate evidence")
    return data


def _drum_sources(receipt):
    # The real 2026 house-core selection includes a nested
    # groove_impact_pocket receipt in addition to actual sampler roles.
    # A source-list comprehension over all keys crashes on that metadata.
    if type(receipt) is not dict:
        raise ValidationError("audited drum source receipt required")
    roles={}
    for key,value in receipt.items():
        if type(value) is dict and type(value.get("source_id")) is str:
            roles[key]=value["source_id"]
    if not {"kick","snare","hats","open_hat"} <= set(roles):
        raise ValidationError("missing independently audited drum source roles")
    return roles


def _native_bass_rescue_status(evidence):
    if type(evidence) is not dict:
        raise ValidationError("malformed source quality receipt")
    if evidence.get("bass_onset_rescue_requested") is not True:
        return "NOT_ENABLED"
    gate=evidence.get("bass_onset_baseline_gate")
    if type(gate) is not dict or type(gate.get("hard_flags")) is not list:
        raise ValidationError("missing original native bass-onset proof")
    has_fault=bool(gate["hard_flags"])
    repaired=evidence.get("bass_onset_rescued")
    if type(repaired) is not bool or (has_fault and not repaired):
        raise ValidationError("unresolved bass source hard fault in published song")
    if not has_fault and repaired:
        raise ValidationError("unjustified bass source replacement")
    if not repaired:
        return "NO_SEVERE_INITIAL_FAULT"
    comparisons=evidence.get("comparisons")
    if type(comparisons) is not list:
        raise ValidationError("missing native bass alternatives")
    qualified=[x for x in comparisons if type(x) is dict and
               x.get("role")=="bass" and x.get("chosen") is True and
               type(x.get("native_fullmix_bass_repair")) is dict and
               x["native_fullmix_bass_repair"].get("technical_replacement_eligible") is True and
               x["native_fullmix_bass_repair"].get("status")=="TECHNICAL_REPAIR_ELIGIBLE" and
               not x.get("native_note_onset_gate",{}).get("hard_flags")]
    if len(qualified)!=1:
        raise ValidationError("native bass replacement missing actual fullmix quality gate")
    return "TECHNICAL_REPAIR_VERIFIED"


def inspect_candidate(folder, *, spectral=True):
    """Verify a private existing generated session without modifying any assets."""
    folder=Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValidationError("candidate folder must exist and not be a symlink")
    report=_read(folder/"report.json")
    song=load(folder/"project.kuang.json")
    proof=_read(folder/"groove-evidence.json")
    selection=_read(folder/"palette/selection.json")
    if selection.get("status") != "complete":
        raise ValidationError("incomplete Vital palette selection")
    if not (folder/"native/session.scraft").is_file():
        raise ValidationError("missing native session")
    expected=state_hash(song)
    if (folder/"song.mid").read_bytes()!=midi.export_bytes(song):
        raise ValidationError("song MIDI drift")
    if not proof.get("technical_pass") or not all(proof.get("technical_gates",{}).values()):
        raise ValidationError("groove technical gate failed")
    if not report.get("native_save_reopen_equal"):
        raise ValidationError("native reopen not verified")
    measurement=report.get("measurement",{})
    if (measurement.get("clipped_samples") != 0 or
        measurement.get("sample_rate") != 48000 or
        measurement.get("bits_per_sample") != 24 or
        measurement.get("channels") != 2 or
        not isinstance(measurement.get("true_peak_dbtp"),(int,float)) or
        measurement["true_peak_dbtp"] > -1 or
        not math.isfinite(measurement["true_peak_dbtp"])):
        raise ValidationError("invalid published full mix PCM/peak verification")
    if not (folder/"preview.wav").is_file():
        raise ValidationError("missing native audio preview")
    if not (folder/"sample-selection.json").is_file():
        raise ValidationError("missing CC0 sample evidence")
    if report.get("quality_judgment") != "unreviewed; no professional audio quality established":
        raise ValidationError("unexpected quality-approval claim")
    roles=selection.get("roles")
    if type(roles) is not dict or not {"bass","chord"} <= set(roles):
        raise ValidationError("missing required Vital bass and chord")
    names={k:v.get("source_preset_name") for k,v in roles.items()}
    if any(not isinstance(v,str) or not v for v in names.values()):
        raise ValidationError("missing source-preset identity")
    bass_sha=roles["bass"].get("source_sha256")
    if source_exclusion("bass",bass_sha):
        raise ValidationError("producer-rejected bass source in candidate")
    context_path=folder/"context-shortlist-evidence.json"
    bass_repair_status=(_native_bass_rescue_status(_read(context_path))
                        if context_path.is_file() else "NOT_ENABLED")
    warning=[]
    tp=measurement["true_peak_dbtp"]
    lufs=measurement.get("integrated_lufs")
    crest=measurement.get("crest_db")
    if tp < PREVIEW_WARNINGS["max_unused_true_peak_headroom_dbtp"]:
        warning.append("unused_peak_headroom_gt_6db")
    if type(lufs) not in (int,float) or not math.isfinite(lufs):
        warning.append("unmeasurable_integrated_lufs")
    elif lufs < PREVIEW_WARNINGS["min_integrated_lufs"]:
        warning.append("near_finished_preview_loudness_low")
    if type(crest) not in (int,float) or not math.isfinite(crest):
        warning.append("unmeasurable_crest")
    elif crest > PREVIEW_WARNINGS["max_crest_db"]:
        warning.append("very_high_full_mix_crest")
    groove=next((s for s in song.sections if s.name=="Groove"),None)
    if groove is None:raise ValidationError("missing groove section")
    region={"start_seconds":groove.start/song.ppq*60/song.tempo_bpm,
            "end_seconds":(groove.start+groove.length)/song.ppq*60/song.tempo_bpm}
    spectrum=band_rms(folder/"preview.wav",region,windows=8) if spectral else None
    return {
        "candidate":folder.name,
        "genre":proof["selected_profile"],"bpm":song.tempo_bpm,
        "key":f"{song.key_tonic}:{song.key_mode}","bars":song.bars,
        "midi_note_count":sum(len(c.notes) for t in song.tracks for c in t.clips),
        "groove_fingerprint":proof["groove_fingerprint_sha256"],
        "seed":report.get("seed"),
        "bass_source_sha256":bass_sha,
        "autonomous_bass_repair_status":bass_repair_status,
        "native_session_present":True,"source_project_sha256":expected,
        "wav_sha256":digest(folder/"preview.wav"),
        "instrument_preset_names":names,
        "drum_source_ids":_drum_sources(_read(folder/"sample-selection.json")),
        "render_integrity":"PASS","mix_level_warnings":warning,
        "technical_quality": "PASS",
        "near_finished_preview_readiness":"NOT_READY" if warning else "UNVERIFIED_PERCEPTUAL",
        "measurement":{"integrated_lufs":lufs,"true_peak_dbtp":tp,"crest_db":crest,
                       "clipped_samples":measurement["clipped_samples"],
                       "duration_seconds":measurement.get("duration_seconds")},
        "groove_mix_spectrum":spectrum,
        "perceptual_quality":"NOT_EVALUATED",
    }


def batch_audit(folders, *, output=None, spectral=True):
    if type(folders) not in (list,tuple) or not 2<=len(folders)<=8:
        raise ValidationError("batch must contain 2..8 independent candidates")
    if len({Path(x).resolve() for x in folders})!=len(folders):
        raise ValidationError("duplicate candidates")
    results=[inspect_candidate(x,spectral=spectral) for x in folders]
    distinct={key:len({json.dumps(r[key],sort_keys=True) for r in results})
              for key in ("groove_fingerprint","instrument_preset_names","drum_source_ids")}
    summary={
        "version":VERSION,"candidate_count":len(results),
        "all_native_integrity_pass":all(x["render_integrity"]=="PASS" for x in results),
        "distinct_sources_and_grooves":distinct,
        "autonomous_bass_repair_counts":{
            status:sum(r.get("autonomous_bass_repair_status")==status for r in results)
            for status in ("TECHNICAL_REPAIR_VERIFIED",
                           "NO_SEVERE_INITIAL_FAULT","NOT_ENABLED")},
        "distinct_bass_source_count":len({r.get("bass_source_sha256") for r in results}),
        "distinct_seed_count":len({r.get("seed") for r in results}),
        "near_finished_preview_ready_count":sum(
            x["near_finished_preview_readiness"]=="UNVERIFIED_PERCEPTUAL"
            for x in results),
        "producer_ready":False,
        "reason":"Technical source integrity is verifiable, but measured preview levels "
                 "and spectral bands are not reliable predictors of professional artistic quality.",
        "technical_evidence":results,
        "subjective_quality":"NOT_EVALUATED",
        "user_review_requested":False,
    }
    if output is not None:
        out=Path(output)
        if out.exists() or out.is_symlink() or not out.parent.is_dir():
            raise ValidationError("audit output must not already exist")
        write(out,summary)
    return summary


def audit_autonomous_attempts(manifest, *, spectral=False):
    """Evaluate every attempted native one-prompt song, including failures.

    Do not cherry-pick only successful session folders. A hard-fault refusal
    is safe behaviour but a failed one-shot production attempt, NOT a pass.
    Reject incomplete runs and never infer a musical winner from metrics.
    """
    manifest=Path(manifest)
    root=manifest.parent
    data=_read(manifest)
    if data.get("complete") is not True or data.get("defaults_modified") is not False:
        raise ValidationError("frozen completed non-mutating batch required")
    cases=data.get("cases")
    if type(cases) is not dict or not 2<=len(cases)<=8:
        raise ValidationError("bounded 2..8-case production batch required")
    attempts=[]
    seen_seeds=set()
    for name,row in cases.items():
        if (type(name) is not str or not name or name.startswith(".") or
                "/" in name or "\\" in name or type(row) is not dict or
                type(row.get("seed")) is not int or
                type(row.get("style")) is not str or
                row.get("status") not in ("PASS_NATIVE_TECHNICAL","FAIL_CLOSED",
                                          "TIMEOUT_FAIL_CLOSED","EVIDENCE_FAIL_CLOSED")):
            raise ValidationError("invalid batch case or unresolved status")
        if row["seed"] in seen_seeds:
            raise ValidationError("batch seeds must be distinct")
        seen_seeds.add(row["seed"])
        entry={"case":name,"seed":row["seed"],"style":row["style"],
               "status":row["status"]}
        if row["status"]=="PASS_NATIVE_TECHNICAL":
            proof=inspect_candidate(root/name,spectral=spectral)
            if proof["seed"] != row["seed"] or proof["genre"] != row["style"]:
                raise ValidationError("native output does not match frozen batch manifest")
            if proof["autonomous_bass_repair_status"]=="NOT_ENABLED":
                raise ValidationError("native bass-repair experiment was not actually enabled")
            entry.update({"native_project_verified":True,
                          "bass_repair":proof["autonomous_bass_repair_status"],
                          "bass_source_sha256":proof["bass_source_sha256"],
                          "groove_fingerprint":proof["groove_fingerprint"],
                          "drum_source_ids":proof["drum_source_ids"],
                          "mix_level_warnings":proof["mix_level_warnings"]})
        else:
            err=row.get("stderr_tail","")
            entry.update({"native_project_verified":False,
                          "failure_category":(
                              "NO_SAFE_BASS_REPAIR" if
                              type(err) is str and
                              "bass native onset fault had no safe verified source rescue" in err
                              else "OTHER_FAILURE")})
        attempts.append(entry)
    success=[x for x in attempts if x["status"]=="PASS_NATIVE_TECHNICAL"]
    yield_fraction=len(success)/len(attempts)
    status=("GENERALIZATION_TECHNICAL_GATE_PASS" if
            yield_fraction >= .9 and len(success)>=3 and
            len({x["style"] for x in attempts})>=3
            else "GENERALIZATION_TECHNICAL_GATE_FAIL")
    return {"version":"house-autonomous-native-bass-batch-v1",
            "attempted":len(attempts),"completed":len(success),
            "failed_closed":len(attempts)-len(success),
            "technical_yield":round(yield_fraction,4),
            "independent_seeds":len(seen_seeds),
            "styles":sorted({x["style"] for x in attempts}),
            "distinct_successful_bass_sources":len({x["bass_source_sha256"] for x in success}),
            "distinct_successful_grooves":len({x["groove_fingerprint"] for x in success}),
            "outcome":status,"production_default_promotion":False,
            "artistic_quality":"NOT_EVALUATED",
            "user_intermediate_listening_required":False,
            "attempts":attempts}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidate_dirs",nargs="+")
    p.add_argument("--out",required=True)
    p.add_argument("--skip-spectral",action="store_true")
    args=p.parse_args(argv)
    try:
        result=batch_audit(args.candidate_dirs,output=args.out,
                           spectral=not args.skip_spectral)
    except (ValidationError,OSError,KeyError,ValueError) as err:
        p.exit(2,"house-batch-acceptance: "+str(err)+"\n")
    print(json.dumps({
        "candidate_count":result["candidate_count"],
        "all_native_integrity_pass":result["all_native_integrity_pass"],
        "distinct_sources_and_grooves":result["distinct_sources_and_grooves"],
        "near_finished_preview_ready_count":result["near_finished_preview_ready_count"],
        "producer_ready":result["producer_ready"],
        "candidate_warnings":{r["candidate"]:r["mix_level_warnings"]
                              for r in result["technical_evidence"]},
    },sort_keys=True,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
