"""Sound traits from actual native PCM24; objective descriptors only.

Covers a rendered MIDI performance in its intended note register, rather than
ranking a preset name or predicting human musical taste. Stdlib implementation.
"""
from __future__ import annotations
import hashlib, math, wave
from pathlib import Path
from .production_audio import _decode, _fft
from .schema import ValidationError

VERSION="house-sound-fingerprint-v1"
RATE=48000
NFFT=4096
BANDS={"sub_30_120":(30,120),"body_120_250":(120,250),
       "lowmid_250_1000":(250,1000),"presence_1000_4000":(1000,4000),
       "air_4000_12000":(4000,12000)}

def _db(value):
    return round(10*math.log10(max(value,1e-25)),3)

def fingerprint(wav,*,start_seconds=0.,duration_seconds=2.,windows=16):
    if (type(windows) is not int or not 8<=windows<=32 or
        type(start_seconds) not in (int,float) or
        type(duration_seconds) not in (int,float) or
        not math.isfinite(start_seconds) or not math.isfinite(duration_seconds) or
        start_seconds<0 or duration_seconds<.2):
        raise ValidationError("bounded finite actual PCM region required")
    path=Path(wav)
    if path.is_symlink() or not path.is_file():
        raise ValidationError("verified source WAV required")
    with wave.open(str(path),"rb") as f:
        if (f.getframerate(),f.getnchannels(),f.getsampwidth(),f.getcomptype())!=(RATE,2,3,"NONE"):
            raise ValidationError("actual 48kHz stereo 24-bit PCM required")
        first=round(start_seconds*RATE);length=round(duration_seconds*RATE)
        if first+length>f.getnframes() or length<NFFT*2:
            raise ValidationError("source waveform interval missing")
        spectrum={k:0. for k in BANDS}
        powers=[];side=0.;mid=0.
        hann=[.5-.5*math.cos(2*math.pi*i/(NFFT-1)) for i in range(NFFT)]
        for index in range(windows):
            pos=first+(length-NFFT)*index//(windows-1)
            f.setpos(pos)
            raw=f.readframes(NFFT)
            if len(raw)!=NFFT*6:raise ValidationError("truncated source PCM")
            frames=list(_decode(raw,3,2))
            m=[(a+b)*.5 for a,b in frames]
            mid+=sum(v*v for v in m)
            side+=sum(((a-b)*.5)**2 for a,b in frames)
            powers.append(sum(v*v for v in m)/NFFT)
            fft=_fft([m[i]*hann[i] for i in range(NFFT)])
            for bin in range(1,NFFT//2+1):
                hz=bin*RATE/NFFT
                energy=abs(fft[bin])**2
                for label,(low,high) in BANDS.items():
                    if low<=hz<high:
                        spectrum[label]+=energy
                        break
    total=sum(spectrum.values())
    if total<1e-18 or mid<1e-18:
        return {"version":VERSION,"signal_present":False,"spectral_bands":None}
    ordered=sorted(powers)
    return {
        "version":VERSION,"signal_present":True,"sample_rate":RATE,
        "fft_size":NFFT,"windows":windows,
        "spectral_bands":{k:round(v/total,6) for k,v in spectrum.items()},
        "sampled_rms_dbfs":_db(mid/(windows*NFFT)),
        "stereo_side_mid_db":_db(side/mid),
        "short_window_range_db":round(_db(ordered[-2])-_db(ordered[1]),3),
        "wav_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "musical_quality":"NOT_EVALUATED",
        "limitations":["Windowed descriptors depend on note register/gate and performance.",
                       "Band overlap alone is not masking, phase coherence or preference.",
                       "The descriptor does not measure human syncopation or perceived bass impact."]
    }

def compatible_rhythm(kick,bass,rhythm):
    """Context descriptor, NOT an automatic gain or syncopation maximizer."""
    if (kick.get("version")!=VERSION or bass.get("version")!=VERSION or
        not kick.get("signal_present") or not bass.get("signal_present") or
        rhythm.get("version")!="house-bass-syncopation-fingerprint-v1"):
        raise ValidationError("verified role fingerprints and MIDI rhythm required")
    lo=("sub_30_120","body_120_250")
    overlap=sum(min(kick["spectral_bands"][k],bass["spectral_bands"][k]) for k in lo)
    return {
        "version":VERSION,
        "kick_bass_low_band_overlap_proxy":round(overlap,5),
        "native_bass_vs_kick_sampled_rms_db":round(bass["sampled_rms_dbfs"]-
                                                   kick["sampled_rms_dbfs"],3),
        "bass_offbeat_fraction":rhythm["bass_offbeat_onset_fraction"],
        "bass_anticipation_fraction":rhythm["bass_anticipation_fraction"],
        "kick_quarter_coverage":rhythm["kick_quarter_coverage"],
        "recommended_action":"Compare locked-MIDI bounded bass gain/source/pocket candidates using actual native audio and listening.",
        "automatic_bass_boost_db":None,"automatic_syncopation_maximum":None,
        "perceptual_quality":"NOT_EVALUATED",
    }
