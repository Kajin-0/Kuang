"""Bounded, reproducible *preview mastering* for private house templates.

Two objectively verifiable renders: (A) transparent, peak-safe PCM gain
and (B) gentle linked compression followed by peak-safe gain. Neither is
a subjective winner, professional master, limiter, or native-bus effect.
The original native editable mix remains untouched.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import tempfile
from pathlib import Path

from .loudness import measure
from .mastering import attenuate, apply_master, file_hash, validate_recipe, _compress
from .sample_assets import write
from .schema import ValidationError

VERSION = "house-master-preview-v1"
TARGET_TRUE_PEAK = -1.7   # safety margin; not a universal mastering law
MAX_GAIN_DB = 12.0
MIN_DURATION_S = 2
MAX_DURATION_S = 600  # also permits full songs; native renderer has a 600-second ceiling

def _verified_input(folder, *, library):
    path=folder/"preview.wav"
    if path.is_symlink() or not path.is_file():
        raise ValidationError("missing unmodified private premix WAV")
    if not (folder/"native"/"session.scraft").is_file():
        raise ValidationError("missing editable native premix session")
    proof=json.loads((folder/"report.json").read_text())
    if not proof.get("native_save_reopen_equal"):
        raise ValidationError("source native save/reopen not verified")
    actual=measure(path,library=library)
    if (actual["sample_rate"],actual["channels"],actual["bits_per_sample"]) != (48000,2,24):
        raise ValidationError("only stereo 48-kHz 24-bit original PCM is supported")
    if actual["integrated_lufs"] is None or actual["clipped_samples"]:
        raise ValidationError("source audio must be non-silent and unclipped")
    if not MIN_DURATION_S <= actual["duration_seconds"] <= MAX_DURATION_S:
        raise ValidationError("master preview requires 2..600s original PCM")
    if actual["true_peak_dbtp"] > -1.0:
        raise ValidationError("source intersample peak already unsafe")
    original=proof.get("measurement",{})
    for key,tolerance in (("integrated_lufs",.1),("true_peak_dbtp",.15)):
        value=original.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or abs(value-actual[key])>tolerance:
            raise ValidationError("source differs from its original audio evidence: "+key)
    return path,actual


def _peak_safe_gain(peak_dbtp):
    if not math.isfinite(peak_dbtp) or peak_dbtp > -1:
        raise ValidationError("unsafe peak before mastering gain")
    needed=TARGET_TRUE_PEAK-peak_dbtp
    # Explicit constraint: never exceed +12 dB gain and never add gain to an
    # already loud mix. A poor dynamic/crest factor is not solved by gain.
    return round(max(0.,min(MAX_GAIN_DB,needed)),4)


def _assert_safe(pre,post,gain_db):
    if post["clipped_samples"] or post["true_peak_dbtp"] > -1.1:
        raise ValidationError("master preview clipped or exceeded -1.1 dBTP")
    if (post["sample_rate"],post["channels"],post["bits_per_sample"],post["frames"]) != (
         pre["sample_rate"],pre["channels"],pre["bits_per_sample"],pre["frames"]):
        raise ValidationError("master preview changed frame count or PCM format")
    if not math.isfinite(post["integrated_lufs"]) or post["integrated_lufs"] < pre["integrated_lufs"]-.2:
        raise ValidationError("master preview did not preserve input loudness")
    if not -0.0001 <= gain_db <= MAX_GAIN_DB:
        raise ValidationError("unbounded gain")


def render_previews(folder, out_dir, *, library=None):
    """Produce two separate private WAV choices without altering the song."""
    folder=Path(folder).absolute()
    out_dir=Path(out_dir).absolute()
    if (folder.is_symlink() or not folder.is_dir() or out_dir.is_symlink() or
        out_dir.exists() or not out_dir.parent.is_dir() or
        out_dir == folder or out_dir.is_relative_to(folder)):
        raise ValidationError("source/output must be separate existing/private directories")
    source,before=_verified_input(folder,library=library)
    source_digest=file_hash(source)
    with tempfile.TemporaryDirectory(prefix=".master-preview-",dir=out_dir.parent) as temporary:
        stage=Path(temporary)
        # A: gain-only version. Its crest factor and relative mix are unchanged.
        flat_gain=_peak_safe_gain(before["true_peak_dbtp"])
        gain_file=stage/"gain-only.wav"
        attenuate(source,gain_file,flat_gain)
        flat_meter=measure(gain_file,library=library)
        _assert_safe(before,flat_meter,flat_gain)

        # B: restrained, actual linked compressor — not a fictional limiter.
        # Threshold follows the true input peak so it generalizes to quiet
        # previews, and stays bounded by the source's measured level.
        recipe={
            "version":"gentle-master-1","input_sha256":source_digest,
            "threshold_dbfs":round(max(-38.,min(-12.,before["sample_peak_dbfs"]-14.)),4),
            "ratio":1.3,"attack_ms":15.,"release_ms":150.,
            "gain_db":0.,"ceiling_dbtp":TARGET_TRUE_PEAK
        }
        validate_recipe(recipe)
        scratch=stage/"compressed-analysis.wav"
        reduction=_compress(source,scratch,recipe)
        compressed=measure(scratch,library=library)
        recipe["gain_db"]=_peak_safe_gain(compressed["true_peak_dbtp"])
        gentle_file=stage/"gentle-compression.wav"
        actual_recipe=apply_master(source,gentle_file,recipe)
        compressed_meter=measure(gentle_file,library=library)
        _assert_safe(before,compressed_meter,recipe["gain_db"])
        scratch.unlink()

        # Reject a compressor that does nothing or mangles amplitude without
        # revealing an actual change. Distinct from a musical verdict.
        if file_hash(gain_file)==file_hash(gentle_file):
            raise ValidationError("gentle compressor produced no distinct variant")
        if file_hash(source)!=source_digest:
            raise ValidationError("source audio changed during processing")
        mode={
            "gain_only":{"wav":"gain-only.wav","sha256":file_hash(gain_file),
                         "gain_db":flat_gain,"meter":flat_meter,
                         "DSP":"constant gain only; no limiter/compression"},
            "gentle":{"wav":"gentle-compression.wav",
                      "sha256":file_hash(gentle_file),
                      "gain_db":recipe["gain_db"],"meter":compressed_meter,
                      "compressor_recipe":recipe,
                      "compressor_measured_reduction":reduction,
                      "DSP":"linked stereo 1.3:1 comp / 15ms attack / 150ms release and gain"},
        }
        record={
            "version":VERSION,"input_sha256":source_digest,
            "original_premix_native":"source/native/session.scraft",
            "input_meter":before,"target_true_peak_dbtp":TARGET_TRUE_PEAK,
            "max_preview_gain_db":MAX_GAIN_DB,"modes":mode,
            "preferred_mode":None,
            "perceptual_quality":"NEEDS_LISTENING",
            "producer_ready":False,
            "warnings":[
                "Peak-normalized listening previews do not establish a professional master.",
                "DSP variants are offline derivatives; source native mixing project stays editable.",
                "This pass does not solve kick/bass/chord masking, poor preset choices or high crest.",
                "No quality winner selected by LUFS, crest, spectral shape or compressor activity."
            ]}
        write(stage/"master-preview-report.json",record)
        out_dir.mkdir(mode=0o700)
        try:
            for item in stage.iterdir():
                shutil.move(str(item),out_dir/item.name)
        except BaseException:
            shutil.rmtree(out_dir)
            raise
    return {
        "output":str(out_dir),"input_lufs":before["integrated_lufs"],
        "variants":{name:{
            "lufs":round(item["meter"]["integrated_lufs"],3),
            "true_peak_dbtp":round(item["meter"]["true_peak_dbtp"],3),
            "crest_db":round(item["meter"]["crest_db"],3),
            "clipped_samples":item["meter"]["clipped_samples"],
            "gain_db":item["gain_db"]
        } for name,item in mode.items()},
        "producer_ready":False
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-dir",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--library",default=None)
    a=p.parse_args(argv)
    try:
        result=render_previews(a.source_dir,a.out_dir,library=a.library)
    except (ValidationError,OSError,ValueError,KeyError,TypeError) as exc:
        p.exit(2,"house-master-preview: "+str(exc)+"\n")
    print(json.dumps(result,sort_keys=True,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
