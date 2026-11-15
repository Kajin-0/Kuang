"""Frequency-resolved house mix diagnostics, not a perceptual balance judge.

Reports band-specific *absolute* RMS energy of the same native stem crop;
never equates a transient kick's full-window RMS to a sustained chord's.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path

from .production_audio import _decode, _fft, BANDS
from .schema import ValidationError

NFFT = 4096
WINDOWS = 32


def band_rms(path, region, *, windows=WINDOWS):
    """32 fixed Hann windows, stereo averaged, 48-kHz 24-bit mono/stereo-safe."""
    if type(windows) is not int or not 8 <= windows <= 64:
        raise ValidationError("bounded spectral window count required")
    if type(region) is not dict or set(region) < {"start_seconds","end_seconds"}:
        raise ValidationError("explicit region required")
    begin = region["start_seconds"]
    finish = region["end_seconds"]
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in (begin,finish)):
        raise ValidationError("invalid spectral region")
    with wave.open(str(path),"rb") as wav:
        if (wav.getframerate(),wav.getnchannels(),wav.getsampwidth(),wav.getcomptype()) != (48000,2,3,"NONE"):
            raise ValidationError("spectrum needs 48-kHz stereo PCM24")
        first = round(begin*48000)
        last = round(finish*48000)
        if not 0 <= first < last <= wav.getnframes() or last-first < 2*NFFT:
            raise ValidationError("spectrum requires a valid 8192-frame or longer region")
        # Standard Hann power-normalization and one-sided conjugate energy.
        win = [.5-.5*math.cos(2*math.pi*i/(NFFT-1)) for i in range(NFFT)]
        window_power = sum(x*x for x in win)
        power = {label:0. for label,_,_ in BANDS}
        for idx in range(windows):
            offset = first + (last-first-NFFT)*idx//(windows-1)
            wav.setpos(offset)
            chunk = wav.readframes(NFFT)
            if len(chunk) != NFFT*6:
                raise ValidationError("short spectral window")
            stereo = list(_decode(chunk,3,2))
            for ch in (0,1):
                f = _fft([sample[ch]*window for sample,window in zip(stereo,win)])
                for k in range(1,NFFT//2+1):
                    frequency=k*48000/NFFT
                    energy=(abs(f[k])**2)*(1 if k==NFFT//2 else 2)/(NFFT*window_power)
                    for label,low,high in BANDS:
                        if low <= frequency < high:
                            power[label] += energy
                            break
    # Average across two independent stereo channels and sample windows.
    power = {name:v/(2*windows) for name,v in power.items()}
    total = sum(power.values())
    return {"method":"32 equally-spaced 4096-point stereo Hann windows, power-corrected",
            "rate":48000,"fft_size":NFFT,"bin_hz":48000/NFFT,
            "window_count":windows,"frequency_bands_hz":{name:[a,b if math.isfinite(b) else 24000]
                                                          for name,a,b in BANDS},
            "band_rms_dbfs":{name:10*math.log10(v) if v>0 else None
                            for name,v in power.items()},
            "band_power_fraction":{name:v/total if total else 0. for name,v in power.items()},
            "region_seconds":[begin,finish]}


def _delta(a,b):
    return round(a-b,3) if a is not None and b is not None else None


def role_spectral_diagnostics(bands):
    """No arbitrary EQ or fader changes, merely explicit overlapping-energy evidence."""
    if type(bands) is not dict or set(bands)!={"kick","bass","chords"}:
        raise ValidationError("need all three native stem spectra")
    for role,d in bands.items():
        if type(d) is not dict or set(d.get("band_rms_dbfs",{})) != {name for name,_,_ in BANDS}:
            raise ValidationError("incomplete role spectrum: "+role)
    k=bands["kick"]["band_rms_dbfs"]
    b=bands["bass"]["band_rms_dbfs"]
    c=bands["chords"]["band_rms_dbfs"]
    return {"bass_vs_kick_sub_20_120_db":_delta(b["sub_20_120"],k["sub_20_120"]),
            "chords_vs_bass_body_120_500_db":_delta(c["body_120_500"],b["body_120_500"]),
            "chords_vs_bass_mid_500_2000_db":_delta(c["mid_500_2000"],b["mid_500_2000"]),
            "chord_sub_fraction":bands["chords"]["band_power_fraction"]["sub_20_120"],
            "interpretation":"Band-specific RMS/energy only. Phase, source timbre, transient feel, masking and musicality require listening.",
            "quality_improvement_established":False}
