"""Construct a private loudness-matched A/B from already verified Kuang mixes.

No preset or project changes; explicitly no automatic winner or preference.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import wave
from pathlib import Path

from .audio import compare_wavs
from .loudness import measure
from .mastering import match_lufs
from .sample_assets import digest, write
from .schema import ValidationError

VERSION = "house-mix-listening-ab-v1"


def prepare_ab(original, candidate, destination, *, library=None):
    src = Path(original).absolute()
    alt = Path(candidate).absolute()
    dest = Path(destination).absolute()
    if (src.is_symlink() or alt.is_symlink() or src == alt or
            dest.exists() or dest.is_symlink() or not dest.parent.is_dir() or
            dest == src or dest == alt):
        raise ValidationError("distinct existing WAVs and new output directory required")
    with wave.open(str(src),"rb") as a,wave.open(str(alt),"rb") as b:
        x=(a.getnchannels(),a.getsampwidth(),a.getframerate(),a.getnframes(),a.getcomptype())
        y=(b.getnchannels(),b.getsampwidth(),b.getframerate(),b.getnframes(),b.getcomptype())
        if x!=y or x[:3]!=(2,3,48000) or x[-1]!="NONE":
            raise ValidationError("A/B requires equal 48-kHz stereo PCM24 sample-aligned WAVs")
    before={str(p):digest(p) for p in (src,alt)}
    with tempfile.TemporaryDirectory(prefix=".house-mix-ab-",dir=dest.parent) as temp:
        stage=Path(temp)
        meter={role:measure(path,library=library)
               for role,path in (("original",src),("candidate",alt))}
        if any(m["integrated_lufs"] is None or m["clipped_samples"] for m in meter.values()):
            raise ValidationError("A/B source silent, gated or clipped")
        target=min(m["integrated_lufs"] for m in meter.values())-.1
        matched={}
        for role,path in (("original",src),("candidate",alt)):
            matched[role]=match_lufs(path,stage/(role+"-matched.wav"),target,library=library)
        if abs(matched["original"]["measurement"]["integrated_lufs"]-
               matched["candidate"]["measurement"]["integrated_lufs"])>.01:
            raise ValidationError("A/B loudness mismatch")
        difference=compare_wavs(stage/"original-matched.wav",stage/"candidate-matched.wav")
        if not difference["measurable_change"]:
            raise ValidationError("A/B audio content not measurably different")
        record={"version":VERSION,"source_wav_sha256":before,
                "source_meter":meter,"matched":matched,
                "delta":difference,"target_lufs":target,
                "perceptual_quality":"NEEDS_LISTENING","winner":None,
                "notes":"A/B is full-length, aligned, attenuation-only LUFS matched; "
                        "no claim either mix is better. Keep private due to Vital licensing."}
        write(stage/"ab-evidence.json",record)
        if any(digest(p)!=before[str(p)] for p in (src,alt)):
            raise ValidationError("source audio changed during A/B preparation")
        dest.mkdir(mode=0o700)
        try:
            for file in stage.iterdir():shutil.move(str(file),dest/file.name)
        except BaseException:
            shutil.rmtree(dest)
            raise
    return {"out":str(dest),"target_lufs":target,
            "original_gain_db":matched["original"]["gain_db"],
            "candidate_gain_db":matched["candidate"]["gain_db"],
            "perceptual_quality":"NEEDS_LISTENING"}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original",required=True)
    p.add_argument("--candidate",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--library")
    args=p.parse_args(argv)
    try:
        report=prepare_ab(args.original,args.candidate,args.out_dir,library=args.library)
    except (ValidationError,ValueError,OSError,wave.Error) as err:
        p.exit(2,str(err)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
