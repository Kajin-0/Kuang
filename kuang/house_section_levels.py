"""Time-resolved native role levels in fixed musical sections.

Reports linear-window RMS and sample peaks without conflating isolated source
audition loudness, absolute full-track peaks and perceptual preference. This
report does not alter any notes, patches, gains, FX or audio.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path
from .schema import ValidationError

RATE=48000
FRAMES=480 # 10 ms complete windows. Reliable sample peak; not oversampled TP.
VERSION="house-native-section-levels-v1"


def analyze(path, sections):
    if type(sections) not in (tuple,list) or not sections:
        raise ValidationError("explicit nonempty sections required")
    source=Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValidationError("missing or symlinked WAV")
    with wave.open(str(source),"rb") as wav:
        if (wav.getframerate(),wav.getnchannels(),wav.getsampwidth(),wav.getcomptype())!=(RATE,2,3,"NONE"):
            raise ValidationError("native level analysis requires 48k stereo PCM24")
        length=wav.getnframes()
        output={}
        for name,start,end in sections:
            if type(name) is not str or not name or type(start) not in (int,float) or type(end) not in (int,float):
                raise ValidationError("invalid audio section")
            if not (math.isfinite(start) and math.isfinite(end) and 0<=start<end<=length/RATE):
                raise ValidationError("section extends outside native WAV")
            first=round(start*RATE);last=round(end*RATE)
            if last-first<FRAMES*10:
                raise ValidationError("section needs at least 100ms")
            wav.setpos(first)
            blocks=[]
            remaining=last-first
            while remaining:
                take=min(FRAMES,remaining)
                raw=wav.readframes(take)
                if len(raw)!=take*6:raise ValidationError("truncated native PCM24")
                power=0.;peak=0.
                for i in range(0,len(raw),3):
                    sample=int.from_bytes(raw[i:i+3],"little",signed=True)/8388608.
                    power+=sample*sample
                    peak=max(peak,abs(sample))
                blocks.append((power/(take*2),peak,take))
                remaining-=take
            total=sum(x[2] for x in blocks)
            total_power=sum(x[0]*x[2] for x in blocks)/total
            overall_peak=max(x[1] for x in blocks)
            def decibels(x):
                return round(20*math.log10(x),3) if x>0 else None
            def levels_ms(ms):
                units=round(ms/10)
                chunks=[]
                # Nonoverlapping 10/100/400ms blocks; don't assert these
                # are EBU loudness or true-peak measurements.
                for i in range(0,len(blocks),units):
                    group=blocks[i:i+units]
                    if len(group)<units:break
                    chunks.append(math.sqrt(sum(item[0]*item[2] for item in group)/
                                            sum(item[2] for item in group)))
                if not chunks:return None
                sorted_levels=sorted(chunks)
                return {
                    "max_rms_dbfs":decibels(max(chunks)),
                    "p95_rms_dbfs":decibels(sorted_levels[math.ceil(.95*len(chunks))-1]),
                    "median_rms_dbfs":decibels(sorted_levels[len(chunks)//2]),
                    "windows":len(chunks),
                }
            output[name]={
                "start_seconds":round(start,5),"end_seconds":round(end,5),
                "section_rms_dbfs":decibels(math.sqrt(total_power)),
                "sample_peak_dbfs":decibels(overall_peak),
                "crest_db":round(20*math.log10(overall_peak/math.sqrt(total_power)),3) if total_power>0 else None,
                "window_10ms":levels_ms(10),
                "window_100ms":levels_ms(100),
                "window_400ms":levels_ms(400),
                "perceptual_quality":"NOT_EVALUATED"
            }
    return {"version":VERSION,"measurement":"PCM amplitude/sample peak, no oversampled true peak",
            "sections":output}
