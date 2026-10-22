"""Descriptive transient/interference checks, never a musical quality score."""

import math
import statistics
import wave
from contextlib import ExitStack

from .schema import ValidationError


def _format(s):
    result = (s.getnchannels(),s.getsampwidth(),s.getframerate(),s.getnframes(),s.getcomptype())
    if result[0] != 2 or result[1] not in (2,3,4) or result[3] <= 0 or result[4] != "NONE":
        raise ValidationError("expected nonempty stereo integer PCM")
    return result


def transient_metrics(path, bpm=126, beats=64):
    """Energy in 0–20/20–100/100–200 ms after each grid beat (no onset guessing)."""
    if type(bpm) not in (int,float) or not math.isfinite(bpm) or not 20 <= bpm <= 300 or type(beats) is not int or not 1 <= beats <= 16384:
        raise ValidationError("invalid transient grid")
    windows = {"attack_0_20ms":(0,.02),"body_20_100ms":(.02,.1),"tail_100_200ms":(.1,.2)}
    result = {}
    with wave.open(str(path),'rb') as s:
        channels,width,rate,frames,_ = _format(s)
        limit = 1 << (8*width-1)
        for name,(start,end) in windows.items():
            values = []
            for beat in range(beats):
                first,last = round((beat*60/bpm+start)*rate),round((beat*60/bpm+end)*rate)
                if last > frames:
                    raise ValidationError("transient grid exceeds PCM duration")
                s.setpos(first)
                data = s.readframes(last-first)
                if len(data) != (last-first)*width*channels:
                    raise ValidationError("truncated transient PCM")
                square = sum(int.from_bytes(data[i:i+width],'little',signed=True)**2 for i in range(0,len(data),width))
                values.append(math.sqrt(square/((last-first)*channels))/limit)
            median = statistics.median(values)
            result[name] = {"median_rms":median,"median_rms_dbfs":20*math.log10(median) if median else None,
                            "min_rms":min(values),"max_rms":max(values)}
    return {"method":"fixed grid, stereo energy; descriptive, not detected/perceptual attack", "beats":beats,"windows":result}


def low_end_interaction(kick, bass):
    """20 Hz one-pole HP → 120 Hz one-pole LP, summed mono stem interference.

    Not a narrow-band phase alignment measurement. The host exposes no oscillator
    reset control. Correlation/interference describe this actual pair of stems.
    """
    with wave.open(str(kick),'rb') as a, wave.open(str(bass),'rb') as b:
        fmt = _format(a)
        if _format(b) != fmt:
            raise ValidationError("kick/bass PCM formats must match")
        channels,width,rate,frames,_ = fmt
        limit = 1 << (width*8-1)
        hp = math.exp(-2*math.pi*20/rate)
        lp = 1-math.exp(-2*math.pi*120/rate)
        last = [0.,0.]; high = [0.,0.]; low = [0.,0.]
        energies = [0.,0.]; cross = 0.; count = 0
        while da := a.readframes(65536):
            db = b.readframes(65536)
            if len(da) != len(db) or len(da) % (width*channels):
                raise ValidationError("truncated stem PCM")
            for offset in range(0,len(da),width*channels):
                for i,data in enumerate((da,db)):
                    value = sum(int.from_bytes(data[offset+c*width:offset+(c+1)*width],'little',signed=True)
                                for c in range(channels))/(channels*limit)
                    high[i] = hp*(high[i]+value-last[i]); last[i] = value
                    low[i] += lp*(high[i]-low[i])
                    energies[i] += low[i]*low[i]
                cross += low[0]*low[1]
                count += 1
        if count != frames:
            raise ValidationError("truncated stem PCM")
    reference = sum(energies)
    summed = max(0,reference+2*cross)
    return {"method":"mono stems, one-pole 20 Hz HP then 120 Hz LP; not phase calibration",
        "correlation":cross/math.sqrt(energies[0]*energies[1]) if all(energies) else None,
        "interference_db":10*math.log10(summed/reference) if reference and summed else None,
        "summed_to_independent_energy_ratio":summed/reference if reference else None,
        "kick_band_rms":math.sqrt(energies[0]/count),"bass_band_rms":math.sqrt(energies[1]/count)}


def stem_sum_error(mix, stems):
    """Independent integer PCM stem summation; report actual quantization error."""
    if not stems:
        raise ValidationError("at least one stem required")
    with ExitStack() as stack:
        streams = [stack.enter_context(wave.open(str(p),'rb')) for p in [mix,*stems]]
        fmt = _format(streams[0])
        if any(_format(s) != fmt for s in streams[1:]):
            raise ValidationError("stem/mix formats must match")
        channels,width,rate,frames,_ = fmt
        count = square = peak = 0
        while data := streams[0].readframes(65536):
            parts = [s.readframes(65536) for s in streams[1:]]
            if any(len(d) != len(data) for d in parts) or len(data) % (width*channels):
                raise ValidationError("truncated stem sum PCM")
            for i in range(0,len(data),width):
                error = int.from_bytes(data[i:i+width],'little',signed=True)-sum(int.from_bytes(d[i:i+width],'little',signed=True) for d in parts)
                square += error*error; peak = max(peak,abs(error)); count += 1
        if count != frames*channels:
            raise ValidationError("truncated stem sum PCM")
    rms = math.sqrt(square/count)/(1 << (width*8-1))
    return {"peak_error_lsb":peak,"error_rms":rms,"error_rms_dbfs":20*math.log10(rms) if rms else None,
            "method":"sum independent native stem PCM without gain changes; quantization differences expected"}
