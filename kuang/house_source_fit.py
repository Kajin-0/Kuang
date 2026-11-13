"""Beat-aligned and spectral *technical* context diagnostics for house sources.

Measurements compare genuine, time-aligned native SoundCraft stem WAVs. They
do NOT assign a subjective sound quality score or prescribe arbitrary EQ.
All input stems must have identical 48 kHz stereo PCM24 frame counts.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path

from .production_audio import _decode, _fft
from .schema import ValidationError

RATE = 48000
FFT = 4096
MAX_ONSETS = 16
WINDOW_MS = (0, 85)
MONO_WINDOWS = 12


def _fmt(w):
    return (w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getcomptype())


def _reader(path):
    w = wave.open(str(path), "rb")
    if _fmt(w) != (RATE, 2, 3, "NONE"):
        w.close()
        raise ValidationError("source-fit needs 48k stereo PCM24 stems")
    return w


def _at(w, start_frame, count):
    if start_frame < 0 or start_frame + count > w.getnframes():
        raise ValidationError("source-fit window exceeds audio bounds")
    w.setpos(start_frame)
    data = w.readframes(count)
    if len(data) != count * 6:
        raise ValidationError("truncated source-fit WAV")
    return list(_decode(data, 3, 2))


def _rms(frames):
    n = len(frames)
    power = sum(l*l+r*r for l,r in frames)
    return math.sqrt(power/(2*n)) if n else 0.


def _db_ratio(a,b):
    if b <= 1e-16:
        return None
    # Complete cancellation is a meaningful loss, not missing data.
    return round(10*math.log10(max(a, b*1e-12)/b), 3)


def _channel_fft(frames):
    if len(frames) != FFT:
        raise ValidationError("invalid FFT frame length")
    hann = [.5-.5*math.cos(2*math.pi*i/(FFT-1)) for i in range(FFT)]
    return (_fft([pair[0]*z for pair,z in zip(frames,hann)]),
            _fft([pair[1]*z for pair,z in zip(frames,hann)]))


def _sub_interaction(a,b):
    """Measured sub power after linear summing vs incoherent energy sum.

    A positive reading is constructive interaction; negative means some
    destructive summation for the measured windows. This is NOT measured
    actual master-bus output where compressor/nonlinearity may intervene.
    """
    ka = _channel_fft(a)
    ba = _channel_fft(b)
    summed = isolated = 0.
    for c in (0,1):
        for k in range(2,11):  # 23.4 Hz to 117.2 Hz (4096/48k resolution)
            x,y=ka[c][k],ba[c][k]
            summed += abs(x+y)**2
            isolated += abs(x)**2+abs(y)**2
    return summed,isolated


def _mono_sub_power(frames):
    x,y=_channel_fft(frames)
    mid=stereo=0.
    for k in range(2,11):
        mid += abs((x[k]+y[k])/2)**2
        stereo += (abs(x[k])**2+abs(y[k])**2)/2
    return mid,stereo


def _kick_onsets(project, region):
    if type(region) is not dict or not {"start_tick","end_tick","start_seconds","end_seconds"} <= set(region):
        raise ValidationError("source-fit requires complete Groove region")
    kick=next((t for t in project.tracks if t.id=="track-kick"),None)
    if kick is None:
        raise ValidationError("missing kick")
    ticks=sorted(set(c.start+n.start for c in kick.clips for n in c.notes
                     if region["start_tick"] <= c.start+n.start < region["end_tick"]))
    if len(ticks)<4:
        raise ValidationError("source-fit requires >=4 actual kick onsets")
    picked=[ticks[i*(len(ticks)-1)//max(1, min(len(ticks),MAX_ONSETS)-1)]
            for i in range(min(len(ticks),MAX_ONSETS))]
    # Song timeline note ticks are absolute and conversion is sample-aligned.
    samples=[round(t/project.ppq*60/project.tempo_bpm*RATE) for t in picked]
    return picked,samples


def fit_diagnostics(project, region, kick_path, bass_path, chord_path,
                    fullmix_path, *, max_events=MAX_ONSETS):
    """Inspect the actual time-aligned native roles and full-mix mono fold-down."""
    if type(max_events) is not int or not 4<=max_events<=MAX_ONSETS:
        raise ValidationError("bounded onset count must be 4..16")
    ticks,samples=_kick_onsets(project,region)
    if len(samples)>max_events:
        chosen=[i*(len(samples)-1)//(max_events-1) for i in range(max_events)]
        ticks=[ticks[i] for i in chosen]
        samples=[samples[i] for i in chosen]
    opened=[]
    try:
        streams={}
        for role,path in (("kick",kick_path),("bass",bass_path),
                          ("chords",chord_path),("fullmix",fullmix_path)):
            path=Path(path)
            if path.is_symlink() or not path.is_file():
                raise ValidationError("missing or symlinked source-fit WAV")
            w=_reader(path)
            opened.append(w)
            streams[role]=w
        counts={w.getnframes() for w in streams.values()}
        if len(counts)!=1:
            raise ValidationError("unaligned source-fit WAV frame counts")
        end_frame=round(region["end_seconds"]*RATE)
        if end_frame>next(iter(counts)):
            raise ValidationError("Groove region exceeds source-fit WAV")
        # Use two independent time windows relative to actual kick onset.
        # No BPM hardcoding and no arbitrary beat subdivision assumptions.
        near,between,kick_early,kick_late = [],[],[],[]
        used_ticks=[]
        summed=separate=0.
        for tick,t in zip(ticks,samples):
            if t+round(.35*RATE)>end_frame:continue
            used_ticks.append(tick)
            kick_fft=_at(streams["kick"],t,FFT)
            bass_fft=_at(streams["bass"],t,FFT)
            a,b=_sub_interaction(kick_fft,bass_fft)
            summed+=a
            separate+=b
            near.append(_rms(_at(streams["bass"],t,round(.10*RATE)))**2)
            between.append(_rms(_at(streams["bass"],t+round(.15*RATE),round(.20*RATE)))**2)
            kick_early.append(max(abs(v) for pair in kick_fft[:round(.035*RATE)] for v in pair))
            kick_late.append(_rms(_at(streams["kick"],t+round(.035*RATE),round(.085*RATE))))
        if len(near)<4:
            raise ValidationError("not enough kick onset windows with audio tails")
        start=round(region["start_seconds"]*RATE)
        end=end_frame
        if end-start<2*FFT:
            raise ValidationError("Groove too short for mono test")
        mid_power=stereo_power=0.
        for i in range(MONO_WINDOWS):
            offset=start+(end-start-FFT)*i//(MONO_WINDOWS-1)
            mid,stereo=_mono_sub_power(_at(streams["fullmix"],offset,FFT))
            mid_power+=mid
            stereo_power+=stereo
        mean_near=sum(near)/len(near)
        mean_between=sum(between)/len(between)
        kick_transient=sum(kick_early)/len(kick_early)
        kick_body=sum(kick_late)/len(kick_late)
        bass_duck=_db_ratio(mean_near,mean_between)
        sub_summation=_db_ratio(summed,separate)
        mono_retention=_db_ratio(mid_power,stereo_power)
        kick_attack=(round(20*math.log10(kick_transient/kick_body),3)
                     if kick_body>1e-10 and kick_transient>1e-10 else None)
        # These are REVIEW FLAGS, not categorical musical flaws. The wet VST
        # bus, sidechain and relative phase may alter actual fullmix results.
        warnings=[]
        if sub_summation is not None and sub_summation < -3.:
            warnings.append("kick_bass_sub_destructive_summation")
        if mono_retention is not None and mono_retention < -6.:
            warnings.append("full_mix_sub_mono_folddown_loss")
        if bass_duck is not None and bass_duck > 3.:
            warnings.append("bass_more_active_at_kick_than_after")
        return {
            "version":"house-source-fit-v1",
            "onset_count":len(near),"onset_tick_selection":used_ticks,
            "sub_fft_bin_range_hz":[2*RATE/FFT,10*RATE/FFT],
            "source_stems_exactly_frame_aligned":True,
            "bass_on_kick_vs_between_power_db":bass_duck,
            "linear_sum_kick_bass_sub_interference_db":sub_summation,
            "full_mix_sub_mono_retention_db":mono_retention,
            "kick_early_peak_vs_late_rms_db":kick_attack,
            "warnings":warnings,
            "perceptual_quality":"NOT_EVALUATED",
            "technical_status":"MEASURED",
            "caveats":[
                "Native isolated stems include wet FX but nonlinear mix-bus interaction is not reconstructed.",
                "FFT analysis uses 23.4–117.2 Hz bins, not exact continuous 20–120 Hz.",
                "Onset-average energies depend on source notes, sample timbre, groove and ducking envelope.",
                "No single numeric target decides sound-source quality or subjective masking."
            ]
        }
    finally:
        for w in opened:w.close()
