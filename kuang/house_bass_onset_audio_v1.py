"""Native bass note-onset-aligned production diagnostics.

The earlier kick-relative 150–250 ms window starts BEFORE the conventional
offbeat bass attack at 120–130 BPM. This module anchors bass measurements to
actual MIDI onset ticks, not fixed time relative to the quarter-note kick.

One source of evidence, not a music preference oracle or universal EQ target.
Requires true native 48 kHz stereo PCM24 source-isolated stems with identical
frame count / time origin, and a complete Groove section.
"""
from __future__ import annotations

import math
import statistics
import wave
from pathlib import Path

from .production_audio import _decode, _fft
from .schema import ValidationError

VERSION = "house-bass-native-note-onset-audit-v1"
RATE = 48000
NFFT = 8192
MAX_EVENTS = 16
BANDS = {"sub_25_90":(25.,90.), "body_90_250":(90.,250.),
         "harmonics_250_1000":(250.,1000.)}
WIN = {"attack_0_40_ms":(0.,.04),
       "body_40_140_ms":(.04,.14),
       "late_140_220_ms":(.14,.22)}


def _read(w, sample, count):
    if sample < 0 or sample+count > w.getnframes():
        raise ValidationError("MIDI onset window exceeds source stem")
    w.setpos(sample)
    raw=w.readframes(count)
    if len(raw)!=count*6:
        raise ValidationError("truncated native stem PCM")
    return list(_decode(raw,3,2))


def _spectral(stereo):
    n=len(stereo)
    if not 512<=n<=NFFT:
        raise ValidationError("invalid window length")
    hann=[.5-.5*math.cos(2*math.pi*i/(n-1)) for i in range(n)]
    norm=sum(a*a for a in hann)*n
    if norm<=0:
        raise ValidationError("invalid spectral normalization")
    fft=[]
    for c in (0,1):
        fft.append(_fft([s[c]*h for s,h in zip(stereo,hann)] + [0.]*(NFFT-n)))
    bands={}
    for label,(lo,hi) in BANDS.items():
        ks=[k for k in range(1,NFFT//2) if lo<=k*RATE/NFFT<hi]
        stereo_power=sum(abs(fft[c][k])**2 for c in (0,1) for k in ks)/(2*norm)
        mid_power=sum(abs((fft[0][k]+fft[1][k])/2)**2 for k in ks)/norm
        bands[label]={"power":stereo_power,
                      "mono_retention_db":10*math.log10(max(mid_power,stereo_power*1e-12)/stereo_power)
                                          if stereo_power>0 else None}
    return bands


def _onsets(project, role, section):
    track=next((t for t in project.tracks if t.id=="track-"+role),None)
    if track is None:
        raise ValidationError("missing native rhythm track "+role)
    ticks=sorted({c.start+n.start for c in track.clips for n in c.notes
                  if section.start<=c.start+n.start<section.start+section.length})
    if len(ticks)<4:
        raise ValidationError("insufficient actual role MIDI note onsets")
    if len(ticks)>MAX_EVENTS:
        ticks=[ticks[i*(len(ticks)-1)//(MAX_EVENTS-1)] for i in range(MAX_EVENTS)]
    return ticks


def evaluate_note_aligned_pocket(project, kick_wav, bass_wav, *, section="Groove"):
    sections=[s for s in project.sections if s.name==section]
    if len(sections)!=1:
        raise ValidationError("one active Groove section required")
    part=sections[0]
    samples={}
    for role in ("kick","bass"):
        samples[role]=[round(t/project.ppq*60/project.tempo_bpm*RATE)
                       for t in _onsets(project,role,part)]
    paths=[Path(kick_wav),Path(bass_wav)]
    if any(p.is_symlink() or not p.is_file() for p in paths):
        raise ValidationError("native stem source missing or symlinked")
    observations={}
    with wave.open(str(paths[0]),"rb") as kick, wave.open(str(paths[1]),"rb") as bass:
        if (kick.getframerate(),kick.getnchannels(),kick.getsampwidth(),
            kick.getcomptype())!=(RATE,2,3,"NONE"):
            raise ValidationError("expected native 48 kHz stereo PCM24")
        if (bass.getframerate(),bass.getnchannels(),bass.getsampwidth(),
            bass.getcomptype(),bass.getnframes())!=(RATE,2,3,"NONE",kick.getnframes()):
            raise ValidationError("native stems must be frame-aligned")
        for role,w in (("kick",kick),("bass",bass)):
            frame_metrics={}
            for window,(start,end) in WIN.items():
                measures=[]
                for tick in samples[role]:
                    first=tick+round(start*RATE)
                    n=round((end-start)*RATE)
                    measures.append(_spectral(_read(w,first,n)))
                metrics={}
                for label in BANDS:
                    power=statistics.median(row[label]["power"] for row in measures)
                    mono=[row[label]["mono_retention_db"] for row in measures
                          if row[label]["mono_retention_db"] is not None]
                    metrics[label]={"power_median":power,
                                    "power_dbfs":round(10*math.log10(power),3)
                                    if power>0 else None,
                                    "mono_retention_db_median":round(statistics.median(mono),3)
                                    if mono else None}
                frame_metrics[window]=metrics
            observations[role]={"onsets_used":len(samples[role]),"windows":frame_metrics}
    def get(role,window,band):
        return observations[role]["windows"][window][band]["power_median"]
    relation={}
    for label in BANDS:
        # Across roles, both are evaluated at their own note attacks. This
        # measures actual rendered source energy, not energy before a note.
        kick_power=get("kick","attack_0_40_ms",label)
        for w in ("attack_0_40_ms","body_40_140_ms"):
            bass_power=get("bass",w,label)
            relation["bass_"+w+"_versus_kick_attack_"+label+"_db"]=(
                round(10*math.log10(bass_power/kick_power),3)
                if kick_power>1e-20 and bass_power>1e-20 else None)
    return {"version":VERSION,"section":section,"bpm":project.tempo_bpm,
            "window_ms":{"attack":[0,40],"body":[40,140],"late":[140,220]},
            "frequency_bands_hz":{k:list(v) for k,v in BANDS.items()},
            "fft_size":NFFT,"roles":observations,
            "between_role":relation,
            "bass_timing_anchor":"actual bass MIDI note-onset ticks",
            "kick_timing_anchor":"actual kick MIDI note-onset ticks",
            "technical_quality":"MEASURED_NOT_MUSICALLY_RANKED",
            "caveats":["No perceptual-quality prediction",
                       "Native isolated stems retain FX, mix-bus nonlinear interactions not reconstructed",
                       "Different note registers and velocities affect relative band power",
                       "Do not use the kick-relative 150-250ms window to infer onset quality"]}


def block_severe_native_source_faults(result, *, articulation_intent="driving"):
    """Conservative screening: never auto-promotes a source or claims 'sounds good'.

    Bass sub mono retention below -6dB (at real bass attacks/body) can signal
    dangerous channel cancellation; signal absence is likewise a technical
    fault. Weak bass relative to kick is reported for further source search,
    not hard-rejected by a global taste-dependent numerical cutoff.
    """
    if type(result) is not dict or result.get("version")!=VERSION:
        raise ValidationError("note-aligned native evidence required")
    if articulation_intent not in ("driving", "sustained"):
        raise ValidationError("explicit driving or sustained bass articulation intent required")
    flags=[]
    review_flags=[]
    # At a true bass MIDI onset, both sub and upper-bass attacks more than
    # 24/30dB below the kick's initial 40ms are a severe rhythmic articulation
    # deficiency. These conservative provisional limits are *review gates*,
    # not empirical human preference optima. Require both bands to fail.
    rel=result.get("between_role",{})
    attack_sub=rel.get("bass_attack_0_40_ms_versus_kick_attack_sub_25_90_db")
    attack_body=rel.get("bass_attack_0_40_ms_versus_kick_attack_body_90_250_db")
    weak_onset = (type(attack_sub) in (int,float) and
                  type(attack_body) in (int,float) and
                  math.isfinite(attack_sub) and math.isfinite(attack_body) and
                  attack_sub < -24 and attack_body < -30)
    if weak_onset:
        # A deliberately sustained bass may have no initial pluck. Only
        # *defer* the driving-onset fault when both 40-140ms source bands
        # independently recover enough against the same kick reference.
        # Never mark deferred bass musically approved: context/masking still
        # requires the native mix and phrase-level audio evaluation.
        body_sub=rel.get("bass_body_40_140_ms_versus_kick_attack_sub_25_90_db")
        body_mid=rel.get("bass_body_40_140_ms_versus_kick_attack_body_90_250_db")
        recovered=(articulation_intent=="sustained" and
                   type(body_sub) in (int,float) and type(body_mid) in (int,float) and
                   math.isfinite(body_sub) and math.isfinite(body_mid) and
                   body_sub >= -18 and body_mid >= -26)
        if recovered:
            review_flags.append("bass_slow_attack_requires_fullmix_context_review")
        else:
            flags.append("bass_onset_attack_severely_masked_by_kick")
    bass=result.get("roles",{}).get("bass",{}).get("windows",{})
    for stage in ("attack_0_40_ms","body_40_140_ms"):
        for band in ("sub_25_90","body_90_250"):
            row=bass.get(stage,{}).get(band,{})
            m=row.get("mono_retention_db_median")
            p=row.get("power_dbfs")
            if type(p) not in (int,float) or not math.isfinite(p):
                flags.append("silent_or_unmeasurable_bass_"+stage+"_"+band)
            elif p < -110:
                flags.append("near_silent_bass_"+stage+"_"+band)
            if m is not None and m < -6:
                flags.append("severe_sub_mono_or_body_loss_"+stage+"_"+band)
    return {"version":VERSION,"hard_flags":flags,
            "review_flags":review_flags,
            "articulation_intent":articulation_intent,
            "eligible_for_more_context_review":not flags,
            "requires_fullmix_context_review":bool(review_flags),
            "musical_winner":None,"automatic_preset_promotion":False}
