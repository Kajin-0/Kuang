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
        "native_session_present":True,"source_project_sha256":expected,
        "wav_sha256":digest(folder/"preview.wav"),
        "instrument_preset_names":names,
        "drum_source_ids":{k:v["source_id"] for k,v in _read(folder/"sample-selection.json").items()},
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
