"""Bounded, deterministic shortlist of *technical* private Vital source alternatives.

Reuses previously verified locked-MIDI A/B renders where safely possible,
and renders only missing variants. Never chooses a subjective preset winner.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import tempfile
from pathlib import Path

from .external_synth import inventory
from .house_palette_compare import (_source, compare_existing,
                                    contextual_review_flags, substitute)
from .sample_assets import digest, write
from .schema import ValidationError, state_hash

VERSION = "house-technical-shortlist-v1"
MAX_ALTERNATIVES = 3
ROLES = ("bass", "chord")


def _input_folder(value):
    raw = Path(value).absolute()
    if raw.is_symlink():
        raise ValidationError("candidate folder cannot be symlinked")
    p = raw.resolve(strict=True)
    if not p.is_dir():
        raise ValidationError("candidate source directory required")
    return p


def plan_candidates(base, assignments):
    """Preflight a small list of (role, previously auditioned donor folder)."""
    if type(assignments) not in (list, tuple) or not 1 <= len(assignments) <= MAX_ALTERNATIVES:
        raise ValidationError("shortlist accepts 1..3 alternatives")
    root, selection, report, song = _source(base)
    if not report.get("groove_template") or song.bars not in (16,32):
        raise ValidationError("base must be short original groove-template")
    if any(t.instrument is None for t in song.tracks):
        raise ValidationError("unverified source instrument")
    seen = set()
    plan = []
    for i, request in enumerate(assignments, 1):
        if type(request) not in (list,tuple) or len(request)!=2:
            raise ValidationError("expected (role, private donor path)")
        role, source = request
        if role not in ROLES:
            raise ValidationError("only bass/chord alternatives are supported")
        donor, donor_selection, donor_report, donor_song = _source(source)
        if donor == root:
            raise ValidationError("alternative source must differ from base")
        if any(selection.get(x) != donor_selection.get(x)
               for x in ("catalog_sha256","preset_root")):
            raise ValidationError("donor preset catalog differs")
        if (selection["plugin"]["module_sha256"] !=
                donor_selection["plugin"]["module_sha256"]):
            raise ValidationError("donor Vital plugin binary differs")
        chosen = donor_selection["roles"][role]
        if chosen.get("status") != "accepted" or chosen.get("runtime_verified") is not True:
            raise ValidationError("donor has no verified private preset")
        key = (role, chosen.get("source_sha256"))
        if key in seen:
            raise ValidationError("same preset used twice in one role")
        seen.add(key)
        projected = substitute(song, donor_song, role)
        plan.append({
            "index":i,"role":role,"donor":str(donor),
            "source_preset_name":selection["roles"][role]["source_preset_name"],
            "alternate_preset_name":chosen["source_preset_name"],
            "donor_preset_source_sha256":chosen["source_sha256"],
            "source_canonical_sha256":state_hash(song),
            "alternate_canonical_sha256":state_hash(projected),
            "project_midi_sha256":digest(root/"song.mid"),
            "artifact_name":f"candidate-{i:02d}-{role}",
        })
    return root, plan


def _cached(candidate, item, base):
    """Validate old native comparison evidence and source audio identity.

    Existing sound assets and copyrighted preset states remain on the user's
    private local disk. Stale/cache-inconsistent reports fail closed.
    """
    folder=_input_folder(candidate)
    path=folder/"source-compare-report.json"
    if not path.is_file():
        raise ValidationError("cached comparison missing provenance")
    record=json.loads(path.read_text())
    expected={
        "swapped_role":item["role"],
        "source_project_sha256":item["source_canonical_sha256"],
        "alternate_project_sha256":item["alternate_canonical_sha256"],
        "source_midi_sha256":item["project_midi_sha256"],
        "locked_midi_identical":True,
        "unchanged_key_tempo_sections_effects_drums":True,
        "source_name":item["source_preset_name"],
        "alternate_name":item["alternate_preset_name"],
    }
    if any(record.get(k)!=v for k,v in expected.items()):
        raise ValidationError("cached source comparison identity drift")
    alt_wav=folder/"candidate"/"candidate.wav"
    native=folder/"candidate"/"native"/"session.scraft"
    ab=folder/"ab"/"ab-evidence.json"
    if not all(x.is_file() and not x.is_symlink() for x in (alt_wav,native,ab)):
        raise ValidationError("cached native/audio evidence missing")
    ab_data=json.loads(ab.read_text())
    audited_hashes=ab_data.get("source_wav_sha256",{})
    if type(audited_hashes) is not dict or sorted(audited_hashes.values())!=sorted([
            digest(base/"preview.wav"),digest(alt_wav)]):
        raise ValidationError("cached A/B audio drift")
    if record.get("subjective_winner") is not None or not record.get("technically_eligible") in (True,False):
        raise ValidationError("cached report makes unsupported quality claim")
    return folder,record


def evaluate_comparison(record):
    """Deterministic classification; no scalar music-quality score."""
    first=record.get("original_premix_meter",{})
    alternative=record.get("alternative_premix_meter",{})
    fit=record.get("alternative_context_fit",{})
    if (not record.get("locked_midi_identical") or
        not record.get("unchanged_key_tempo_sections_effects_drums")):
        raise ValidationError("alternate did not preserve source composition")
    if alternative.get("clipped_samples") != 0 or not isinstance(
            alternative.get("true_peak_dbtp"),(int,float)) or (
            not math.isfinite(alternative["true_peak_dbtp"])):
        raise ValidationError("invalid candidate audio evidence")
    if alternative["true_peak_dbtp"] > -1.0:
        return "REJECT",["unsafe_true_peak"]
    flags=contextual_review_flags(first.get("integrated_lufs"),
                                   alternative.get("integrated_lufs"),fit)
    hard=[x for x in flags if x in (
        "kick_bass_sub_destructive_summation",
        "full_mix_sub_mono_folddown_loss")]
    if hard:
        # Severe destructive interference is a genuine engineering concern,
        # but no global quality inference is made from source color.
        return "REJECT",flags
    return ("REVIEW" if flags else "TECHNICALLY_ELIGIBLE"),flags


def create_shortlist(base, assignments, out_dir, soundcraft, *,
                     existing=None, library=None):
    """Render missing variants sequentially; atomic evidence and bounded work."""
    base,plan=plan_candidates(base,assignments)
    existing = {} if existing is None else existing
    if type(existing) is not dict or any(
          type(k) is not int or not 1<=k<=len(plan) for k in existing):
        raise ValidationError("existing cache keys must be 1-based candidate indices")
    output=Path(out_dir).absolute()
    workspace=Path.cwd().resolve()
    if (output.exists() or output.is_symlink() or not output.parent.is_dir()
          or not output.resolve().is_relative_to(workspace)
          or output.resolve().is_relative_to(base)):
        raise ValidationError("fresh, separate workspace-local shortlist output required")
    protected=[base,*[_input_folder(p["donor"]) for p in plan]]
    before={str(p):inventory(p) for p in protected}
    records=[]
    with tempfile.TemporaryDirectory(prefix=".house-shortlist-",dir=output.parent) as tmp:
        stage=Path(tmp)
        for item in plan:
            if item["index"] in existing:
                cached,receipt=_cached(existing[item["index"]],item,base)
                reused=True
                artifact=str(cached)
            else:
                new=stage/item["artifact_name"]
                comparison=compare_existing(base,item["donor"],soundcraft,new,
                                            swap=item["role"],library=library)
                receipt=json.loads((new/"source-compare-report.json").read_text())
                reused=False
                artifact=item["artifact_name"]
                if comparison["subjective_winner"] is not None:
                    raise ValidationError("candidate unexpectedly chose a subjective winner")
            status,flags=evaluate_comparison(receipt)
            records.append({
                **item,
                "artifact":artifact,
                "cache_reused":reused,
                "technical_status":status,
                "review_flags":flags,
                "original_lufs":receipt["original_premix_meter"]["integrated_lufs"],
                "candidate_lufs":receipt["alternative_premix_meter"]["integrated_lufs"],
                "context_fit":receipt["alternative_context_fit"],
                "subjective_winner":None,
            })
        if any(inventory(p) != before[str(p)] for p in protected):
            raise ValidationError("source/donor altered during shortlist evaluation")
        result={
            "version":VERSION,
            "base_source":str(base),
            "base_project_sha256":plan[0]["source_canonical_sha256"],
            "original_midi_sha256":plan[0]["project_midi_sha256"],
            "roles_compared":sorted({i["role"] for i in plan}),
            "candidate_count":len(records),
            "maximum_alternatives":MAX_ALTERNATIVES,
            "candidate_results":records,
            "baseline_preserved_as_default":True,
            "automatic_sound_quality_winner":None,
            "quality_judgment":"NOT_EVALUATED",
            "technically_eligible_count":sum(x["technical_status"]=="TECHNICALLY_ELIGIBLE"
                                             for x in records),
            "review_count":sum(x["technical_status"]=="REVIEW" for x in records),
            "rejected_count":sum(x["technical_status"]=="REJECT" for x in records),
            "source_selection_approved":False,
            "limitations":[
                "Shortlist comparisons are independently measured source substitutions, not a musical ranking.",
                "Review flags are not validated perceptual preferences; compare at matched loudness.",
                "Base source stays the deterministic fallback until stronger evidence exists.",
                "Only already verified private Vital patch donors are supported.",
                "Do not publish private native sessions or unknown-license Vital preset assets.",
            ],
        }
        write(stage/"shortlist-evidence.json",result)
        output.mkdir(mode=0o700)
        try:
            for p in stage.iterdir():
                shutil.move(str(p),output/p.name)
        except BaseException:
            shutil.rmtree(output)
            raise
    return {"output":str(output),"candidate_count":len(records),
            "technical_statuses":[r["technical_status"] for r in records],
            "cached_reuse_count":sum(r["cache_reused"] for r in records),
            "automatic_sound_quality_winner":None}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base",required=True)
    p.add_argument("--donor",action="append",required=True,
                   help="role:absolute-private-output-directory; repeat up to three times")
    p.add_argument("--existing",action="append",default=[],
                   help="N:absolute-previous-compare-result, 1-based role order")
    p.add_argument("--soundcraft",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--library")
    args=p.parse_args(argv)
    try:
        def parse_one(value, delim):
            key,sep,path=value.partition(delim)
            if not sep or not key or not path:
                raise ValidationError("malformed candidate or cache declaration")
            return key,path
        donors=[parse_one(x,":") for x in args.donor]
        caches={}
        for item in args.existing:
            k,v=parse_one(item,":")
            if not k.isdecimal() or int(k) in caches:
                raise ValidationError("duplicate or invalid cache slot")
            caches[int(k)]=v
        result=create_shortlist(args.base,donors,args.out_dir,args.soundcraft,
                                existing=caches,library=args.library)
    except (ValidationError,OSError,ValueError,TypeError,KeyError,IndexError) as e:
        p.exit(2,"house-shortlist: "+str(e)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
