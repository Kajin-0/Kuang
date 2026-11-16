"""Comparable musical-window PCM fingerprints for frozen Kuang House references.

Opt-in analytical CLI; zero audio modification, no presets loaded. Uses pinned
NumPy/SoundFile from producer's local private environment. Independent bands,
mid/side, and mono retention. LUFS uses the existing Kuang meter when enabled.
No musical preference score, mastering decision or quality claims.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

# Deliberately avoid importing optional NumPy at package import time.
from kuang.schema import BAR, PPQ, ValidationError, load

VERSION = "kuang-house-reference-fingerprint-v1"
BANDS = {
    "sub_20_120": (20, 120),
    "body_120_500": (120, 500),
    "presence_500_2000": (500, 2000),
    "presence_2000_8000": (2000, 8000),
    "air_8000_20000": (8000, 20000),
}
WINDOWS = {
    "phase44": {"Groove": ("First groove", 0),
                "Breakdown": ("Breakdown", 0),
                "Drop": ("Late climax", 0)},
    "generator": {"Groove": ("Groove A", 0),
                  "Breakdown": ("Breakdown", 0),
                  "Drop": ("Main Drop", 0)},
}


def windows_from_project(project, *, reference: str):
    if reference not in WINDOWS:
        raise ValidationError("unknown musical reference section mapping")
    bar_seconds = 4 * 60 / project.tempo_bpm
    sections = {s.name: s for s in project.sections}
    result = {}
    for name, (section_name, bar_offset) in WINDOWS[reference].items():
        section = sections.get(section_name)
        if section is None or section.length < (bar_offset+8)*BAR:
            raise ValidationError("missing matching eight-bar music passage: "+section_name)
        offset = section.start / BAR + bar_offset
        begin = offset * bar_seconds
        end = (offset+8) * bar_seconds
        result[name] = {
            "section_name": section_name,
            "bar_start_zero_based": int(offset),
            "bar_end_zero_based": int(offset+8),
            "start_seconds": begin, "end_seconds": end,
        }
    return result


def power_db(power: float):
    return round(10*math.log10(power), 4) if power > 0 else None


def ratio_db(numerator: float, denominator: float):
    return round(10*math.log10(numerator/denominator),4) if numerator > 0 and denominator > 0 else None


def energy_delta_db(after: float, before: float):
    return ratio_db(after, before)


def analyze_window(path, start, end, *, loudness_library=None):
    import numpy as np
    import soundfile as sf
    from kuang.loudness import measure

    with sf.SoundFile(str(path)) as w:
        if w.channels != 2 or w.samplerate != 48000 or w.subtype != "PCM_24":
            raise ValidationError("reference requires native stereo 48k PCM24")
        first = round(start * w.samplerate)
        last = round(end * w.samplerate)
        if not (0 <= first < last <= len(w)) or last-first < 8192:
            raise ValidationError("audio does not contain selected eight-bar window")
        w.seek(first)
        pcm = w.read(frames=last-first, dtype="float64", always_2d=True)
    if len(pcm) != last-first:
        raise ValidationError("native reference WAV truncated")
    if not np.isfinite(pcm).all():
        raise ValidationError("non-finite PCM values")

    mono = (pcm[:, 0]+pcm[:, 1])/2
    side = (pcm[:, 0]-pcm[:, 1])/2
    power_stereo = float(np.mean(pcm*pcm))
    power_mid = float(np.mean(mono*mono))
    power_side = float(np.mean(side*side))
    sample_peak = float(np.max(np.abs(pcm)))
    lufs = None
    true_peak = None
    if loudness_library is not None:
        if not Path(loudness_library).is_file():
            raise ValidationError("explicit libebur128 reference library missing")
        with tempfile.TemporaryDirectory(prefix="kuang-fingerprint-") as t:
            clip=Path(t)/"region.wav"
            sf.write(str(clip),pcm,48000,subtype="PCM_24")
            met=measure(clip,library=loudness_library)
            lufs=met["integrated_lufs"]
            true_peak=met["true_peak_dbtp"]

    # Analyze the same uniformly distributed 4096-frame Hann frames for
    # every reference. Use phase-consistent actual M=(L+R)/2 S=(L-R)/2.
    n=4096
    win=np.hanning(n)
    positions=np.linspace(0,len(pcm)-n,num=128,dtype=np.int64)
    freq=np.fft.rfftfreq(n,1/48000)
    mid_power=np.zeros(n//2+1)
    side_power=np.zeros(n//2+1)
    for pos in positions:
        spec=np.fft.rfft(mono[pos:pos+n]*win)
        mid_power += np.abs(spec)**2
        spec=np.fft.rfft(side[pos:pos+n]*win)
        side_power += np.abs(spec)**2
    # One-sided energy, with identical scaling across tracks/bands.
    normal=128*float(np.sum(win*win))*n
    mid_power/=normal
    side_power/=normal
    out={}
    for name,(low,high) in BANDS.items():
        idx=(freq>=low)&(freq<high)
        m=float(np.sum(mid_power[idx]))
        s=float(np.sum(side_power[idx]))
        out[name]={
            "mid_power":round(m,12),"side_power":round(s,12),
            "side_mid_db":ratio_db(s,m),
            "mono_retention_fraction":round(m/(m+s),6) if m+s else None,
            "stereo_energy_dbfs":power_db(m+s),
        }
    # Explicit 400ms short-term RMS percentiles; not EBU loudness.
    hop=round(0.4*48000)
    powers=[]
    for pos in range(0,len(pcm)-hop+1,hop):
        powers.append(float(np.mean(pcm[pos:pos+hop]**2)))
    powers.sort()
    return {
        "start_seconds":round(start,5),"end_seconds":round(end,5),
        "rms_dbfs":power_db(power_stereo),
        "sample_peak_dbfs":power_db(sample_peak*sample_peak),
        "crest_db":round(10*math.log10(sample_peak*sample_peak/power_stereo),4)
            if power_stereo else None,
        "side_mid_db":ratio_db(power_side,power_mid),
        "mono_retention_fraction":round(power_mid/(power_mid+power_side),6)
            if power_mid+power_side else None,
        "lowband_side_mid_db":out["sub_20_120"]["side_mid_db"],
        "400ms_median_rms_dbfs":power_db(powers[len(powers)//2]),
        "400ms_p95_rms_dbfs":power_db(powers[math.ceil(.95*len(powers))-1]),
        "short_region_integrated_lufs":round(lufs,4) if lufs is not None else None,
        "short_region_true_peak_dbtp":round(true_peak,4) if true_peak is not None else None,
        "frequency_bands":out,
        "frequency_side_mid_method":"128 equally spaced 4096-frame Hann FFTs; mid/side",
    }


def fingerprint(path, project_path, *, reference, label, loudness_library=None):
    import soundfile as sf
    project=load(project_path)
    passages=windows_from_project(project,reference=reference)
    with sf.SoundFile(str(path)) as wav:
        duration=len(wav)/wav.samplerate
    result={"version":VERSION,"label":label,"kind":reference,
            "mix_stage":"master" if reference=="phase44" else "premaster",
            "source_wav":str(path),"source_project":str(project_path),
            "bpm":project.tempo_bpm,"bars":project.bars,
            "audio_duration_seconds":round(duration,4),
            "sections":{},"artistic_quality":"NOT_EVALUATED"}
    for role,region in passages.items():
        result["sections"][role]={
            "actual_section_name":region["section_name"],
            "bar_start_zero_based":region["bar_start_zero_based"],
            "bar_end_zero_based":region["bar_end_zero_based"],
            **analyze_window(path,region["start_seconds"],region["end_seconds"],
                             loudness_library=loudness_library)
        }
    for metric,key in (("drop_minus_groove_rms_db","rms_dbfs"),
                       ("breakdown_minus_groove_rms_db","rms_dbfs"),
                       ("drop_minus_groove_shortterm_lufs","short_region_integrated_lufs"),
                       ("breakdown_minus_groove_shortterm_lufs","short_region_integrated_lufs")):
        left=result["sections"]["Drop" if metric.startswith("drop") else "Breakdown"].get(key)
        right=result["sections"]["Groove"].get(key)
        result[metric]=round(left-right,3) if left is not None and right is not None else None
    return result


def aggregate(results):
    import statistics
    generated=[x for x in results if x["kind"]=="generator"]
    if not generated:
        raise ValidationError("at least one generator song required")
    metrics={
        "drop_minus_groove_rms_db":"drop_minus_groove_rms_db",
        "breakdown_minus_groove_rms_db":"breakdown_minus_groove_rms_db",
        "drop_minus_groove_shortterm_lufs":"drop_minus_groove_shortterm_lufs",
        "breakdown_minus_groove_shortterm_lufs":"breakdown_minus_groove_shortterm_lufs",
    }
    out={}
    for label,key in metrics.items():
        vals=[p[key] for p in generated if p.get(key) is not None]
        out[label]={"median":round(statistics.median(vals),4),"minimum":min(vals),
                    "maximum":max(vals),"count":len(vals)} if vals else None
    for section in ("Groove","Breakdown","Drop"):
        for band in ("whole","sub_20_120","body_120_500","presence_500_2000","presence_2000_8000"):
            vals=[]
            for p in generated:
                record=p["sections"][section]
                val=(record["side_mid_db"] if band=="whole" else
                     record["frequency_bands"][band]["side_mid_db"])
                if val is not None:
                    vals.append(val)
            out[f"{section}.{band}.side_mid_db"]={
                "median":round(statistics.median(vals),4),
                "minimum":min(vals),"maximum":max(vals),"count":len(vals)
            } if vals else None
    return out


def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--phase44-wav",type=Path,required=True)
    a.add_argument("--phase44-project",type=Path,required=True)
    a.add_argument("--ten-song-root",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--library",type=Path)
    args=a.parse_args(argv)
    if args.out.exists():
        a.error("refuse to overwrite an existing evidence file")
    lib=str(args.library) if args.library else None
    work=[]
    sources=[("Phase44",args.phase44_wav,args.phase44_project,"phase44")]
    directories=sorted(args.ten_song_root.glob("ten-song-v1-??-*-20261115"))
    if len(directories)!=10:
        raise ValidationError(f"expected exactly ten frozen songs; found {len(directories)}")
    sources.extend((p.name,p/"preview.wav",p/"project.kuang.json","generator") for p in directories)
    for label,wav,proj,kind in sources:
        print("ANALYZING",label,flush=True)
        x=fingerprint(wav,proj,reference=kind,label=label,loudness_library=lib)
        work.append(x)
        print("COMPLETE",label,
              "drop",x["drop_minus_groove_rms_db"],
              "breakdown",x["breakdown_minus_groove_rms_db"],
              "groove width",x["sections"]["Groove"]["side_mid_db"],flush=True)
    report={"version":VERSION,"method":"Same 8-bar active sections; full stereo PCM; 128 equally spaced FFT Hann windows; no source edits; Phase44 master vs generator premaster",
            "phase44_reference":work[0],"generator_songs":work[1:],
            "generator_aggregate":aggregate(work),
            "comparison_limits":["Phase44 is mastered; Kuang is premastered",
                                 "matching passage role, not identical arrangement/harmonic content",
                                 "side/mid energy does not by itself establish preference",
                                 "short-region integrated LUFS does not equal momentary LUFS",
                                 "no chord/pad stem audibility without verified isolated stems"],
            "musical_quality":"NOT_EVALUATED","automatic_musical_winner":None,
            "production_defaults_modified":False}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x") as f:
        json.dump(report,f,sort_keys=True,indent=2)
    print("EVIDENCE",args.out,flush=True)


if __name__=="__main__":
    main()
