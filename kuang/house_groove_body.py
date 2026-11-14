"""Real native kick/bass spectral pocket diagnostics on a common MIDI timeline.

No universal 'professional' target: reports time/frequency energy relationships,
source variation, phase and mono evidence for one-prompt source choice.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path

from .production_audio import _decode, _fft
from .schema import ValidationError

VERSION = "house-kick-bass-body-v1"
RATE = 48000
NFFT = 8192
WIN = 4800
MAX_KICKS = 16
BANDS = {"sub_25_90":(25,90),"body_90_250":(90,250)}


def _power(path, times):
    if type(times) is not list or not times or len(times)>MAX_KICKS*3:
        raise ValidationError("bounded native source onset windows required")
    out={b:[] for b in BANDS}
    with wave.open(str(path),"rb") as w:
        if (w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getcomptype())!=(RATE,2,3,"NONE"):
            raise ValidationError("native groove body requires 48k stereo PCM24")
        for secs in times:
            first=round(secs*RATE)
            if first<0 or first+WIN>w.getnframes():
                raise ValidationError("native groove window exceeds source PCM")
            w.setpos(first)
            raw=w.readframes(WIN)
            if len(raw)!=WIN*6:raise ValidationError("truncated native source PCM")
            frames=list(_decode(raw,3,2))
            mid=[(l+r)*.5 for l,r in frames]
            hann=[.5-.5*math.cos(2*math.pi*i/(WIN-1)) for i in range(WIN)]
            f=_fft([x*y for x,y in zip(mid,hann)]+[0.]*(NFFT-WIN))
            for name,(low,high) in BANDS.items():
                val=sum(abs(f[k])**2 for k in range(1,NFFT//2+1)
                        if low<=k*RATE/NFFT<high)
                out[name].append(val)
    return {name:sum(vals)/len(vals) for name,vals in out.items()}


def _ratio(a,b):
    if a<=1e-20 or b<=1e-20:
        raise ValidationError("no significant energy in required native groove band")
    return round(10*math.log10(a/b),3)


def groove_body(project,region,kick_wav,bass_wav,*,max_kicks=MAX_KICKS):
    """Kick onset vs bass offbeat without assuming BPM, note names or sample IDs.

    Both sources must be native renders with the SAME MIDI, same sample clock,
    same level controls, effects and common time origin.
    """
    if type(max_kicks) is not int or not 4<=max_kicks<=MAX_KICKS:
        raise ValidationError("invalid bounded kick count")
    if type(region) is not dict or not {"start_tick","end_tick","start_seconds","end_seconds"} <= region.keys():
        raise ValidationError("active groove section required")
    kick=next((t for t in project.tracks if t.id=="track-kick"),None)
    if kick is None:raise ValidationError("missing actual kick MIDI")
    ticks=sorted({c.start+n.start for c in kick.clips for n in c.notes
                  if region["start_tick"]<=c.start+n.start<region["end_tick"]})
    if len(ticks)<4:raise ValidationError("insufficient actual kick onsets")
    if len(ticks)>max_kicks:
        ticks=[ticks[i*(len(ticks)-1)//(max_kicks-1)] for i in range(max_kicks)]
    beat=[t/project.ppq*60./project.tempo_bpm for t in ticks]
    # Consistent 100 ms windows; use actual kick MIDI, not BPM-based fixed 126.
    # Bass early 150–250 ms and late 250–350 ms after each kick.
    early=[t+.150 for t in beat]
    late=[t+.250 for t in beat]
    for target in (early,late):
        if any(t+.100>region["end_seconds"]+.0001 for t in target):
            # Exclude final kick if its late offbeat would exceed section end.
            indices=[i for i,t in enumerate(late) if t+.100<=region["end_seconds"]+.0001]
            beat=[beat[i] for i in indices]
            early=[early[i] for i in indices]
            late=[late[i] for i in indices]
            break
    if len(beat)<4:raise ValidationError("insufficient valid active-groove windows")
    with wave.open(str(kick_wav),"rb") as kick_pcm, wave.open(str(bass_wav),"rb") as bass_pcm:
        if kick_pcm.getnframes()!=bass_pcm.getnframes():
            raise ValidationError("native kick and bass sources must share exact PCM timeline")
    near=_power(kick_wav,beat)
    bass_early=_power(bass_wav,early)
    bass_late=_power(bass_wav,late)
    result={}
    for label in BANDS:
        result[label]={
            "kick_near_power":near[label],
            "bass_early_offbeat_power":bass_early[label],
            "bass_late_offbeat_power":bass_late[label],
            "bass_early_vs_kick_db":_ratio(bass_early[label],near[label]),
            "bass_late_vs_kick_db":_ratio(bass_late[label],near[label]),
            "bass_late_vs_early_db":_ratio(bass_late[label],bass_early[label])
        }
    return {"version":VERSION,"kick_onsets_used":len(beat),
            "window_ms":{"kick":[0,100],"bass_early":[150,250],"bass_late":[250,350]},
            "bands":result,"perceptual_quality":"NOT_EVALUATED",
            "purpose":"source/body audibility and kick pocket comparison on identical song MIDI",
            "limitations":[
                "Upper-bass and sub spectral power are objective but not a psychoacoustic listening score.",
                "PCM stems preserve native FX; master-bus nonlinearity is not reconstructed.",
                "The actual musical role of each offbeat depends on genre and generated MIDI.",
                "A candidate with higher energy may be unpleasant or clash with the harmony.",
                "No universal numerical target and no automatic source winner."
            ]}


def upper_body_audition_gate(original_features, candidate_features):
    """Cost gate for ONE runtime-verified source; not a music-quality classifier.

    Fractions are from identical private isolated-preset audition procedure.
    A different upper-harmonic composition justifies a contextual render;
    it does not justify automatically changing sources in the user's song.
    """
    if type(original_features) is not dict or type(candidate_features) is not dict:
        raise ValidationError("verified private source features required")
    values=[]
    for record in (original_features,candidate_features):
        value=record.get("mid_fraction")
        if type(value) not in (float,int) or not math.isfinite(value) or not 0<=value<=1:
            raise ValidationError("invalid audited isolated-source mid fraction")
        values.append(float(value))
    old,new=values
    return {
        "version":"upper-body-native-audition-gate-v1",
        "original_mid_fraction":round(old,6),
        "candidate_mid_fraction":round(new,6),
        "mid_fraction_difference":round(new-old,6),
        "audition_warranted":new-old>=.08,
        "automatic_source_swap":False,
        "threshold_note":"8 percentage point difference limits native compute; not a perceptual ranking"
    }


def compare_bass_sources(original,candidate):
    if original.get("version")!=VERSION or candidate.get("version")!=VERSION:
        raise ValidationError("two complete source-body receipts required")
    if original["kick_onsets_used"]!=candidate["kick_onsets_used"]:
        raise ValidationError("source auditions must share identical kick timeline")
    out={}
    for label in BANDS:
        a=original["bands"][label];b=candidate["bands"][label]
        out[label]={
            "early_bass_vs_kick_delta_db":round(b["bass_early_vs_kick_db"]-a["bass_early_vs_kick_db"],3),
            "late_bass_vs_kick_delta_db":round(b["bass_late_vs_kick_db"]-a["bass_late_vs_kick_db"],3),
            "late_vs_early_delta_db":round(b["bass_late_vs_early_db"]-a["bass_late_vs_early_db"],3),
        }
    return {"version":"house-native-bass-comparison-v1","bands":out,
            "automatic_winner":None,"source_quality":"REQUIRES_MATCHED_LISTENING"}
