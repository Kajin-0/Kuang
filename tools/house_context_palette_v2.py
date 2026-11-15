#!/usr/bin/env python3
"""Opt-in offline private post-generation source review; no automatic source swaps.

Input JSON must come from independently rendered native SoundCraft isolated
stem measurements. Never infer sound quality from a preset name or LUFS alone.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from kuang.schema import load,ValidationError,state_hash
from kuang.house_context_palette_v2 import review_source

def review_verified_source(source_root,stems_data):
    from kuang.house_palette_compare import _source
    root,selection,source_report,project=_source(source_root)
    if not stems_data.get("source_preserved") or stems_data.get("native_canonical_sha256")!=state_hash(project):
        raise ValidationError("actual native role stems do not match source canonical project")
    if (stems_data.get("measured_region")!="Groove A first 16 bars" or
            not all(role in stems_data.get("role_stems",{}) for role in ("kick","bass","harmony"))):
        raise ValidationError("complete same-region live native role stems required")
    chosen=selection["roles"]["chord"]
    evidence=review_source(project,
        prompt=source_report["prompt"],
        profile=source_report["groove_profile"],
        stems=stems_data["role_stems"],
        source_verified=(chosen["runtime_verified"] is True),
        source_sha256=chosen["source_sha256"],
        source_name=chosen["source_preset_name"],
        runner_up_count=len(selection.get("shortlist",{}).get("chord",[])))
    evidence["executable_stage"]="source-audibility first-pass diagnostic"
    evidence["original_native_session"]=str(root/"native/session.scraft")
    evidence["producer_approval_required"]=True
    evidence["technically_eligible_source_swap_is_not_perceptual_preference"]=True
    evidence["prompt"]=source_report["prompt"]
    return evidence

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,help="previously complete private native result")
    p.add_argument("--stems",required=True,help="real SoundCraft role evidence JSON")
    p.add_argument("--out",required=True,help="new receipt, never overwrite")
    args=p.parse_args()
    out=Path(args.out)
    if out.exists() or out.is_symlink() or not out.parent.is_dir():
        raise ValidationError("private receipt path must be fresh")
    evidence=review_verified_source(args.source,json.loads(Path(args.stems).read_text()))
    out.write_text(json.dumps(evidence,indent=2)+"\n")
    print(evidence["action"],"chord_vs_kick_db",evidence["chord_minus_kick_rms_db"],
          "max_candidates",evidence["max_candidates"])
if __name__=="__main__":main()
