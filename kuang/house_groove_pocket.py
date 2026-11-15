"""Active-groove, beat-aligned band-power diagnostics for existing native house WAVs.

Operates on real, correctly aligned PCM playback. Documents relationships
between kick-near and offbeat full-mix energy, not isolated bass loudness.
Does not impose Suno/Phase44 settings or claim a perceptual quality score.
"""
from __future__ import annotations

import math
import wave

from .production_audio import _decode, _fft
from pathlib import Path

from .schema import ValidationError

VERSION = "house-fullmix-groove-pocket-v1"
RATE = 48000
BANDS = ((25., 90.), (90., 250.))
MAX_EVENTS = 32
WIN = ((0., .105), (.150, .350))


def _bandpowers(data):
    # Use a 100 ms Hann window and a 4800+ point real FFT, interpolating
    # frequency bins; integrated band-power *ratio* uses identical window sizes
    # for both temporal positions and avoids raw dBFS mixed-window comparison.
    if len(data) < 4800:
        raise ValidationError("groove diagnostic requires >=100ms PCM")
    mid = [(pair[0]+pair[1])/2 for pair in data[:4800]]
    window = [mid[i]*(.5-.5*math.cos(2*math.pi*i/(len(mid)-1)))
              for i in range(len(mid))]
    spectrum = _fft(window + [0.]*(16384-len(window)))
    return [sum(abs(spectrum[k])**2 for k in range(1,8193)
                if lo <= k*RATE/16384 < hi) for lo,hi in BANDS]


def evaluate_pocket(project, wav, *, section="Groove", max_events=MAX_EVENTS,
                    start_offset_s=0.):
    """Compare near-kick and late-offbeat 100ms spectral energy.

    start_offset_s is for intentionally cropped listening files only.
    A full private native preview should use the default of zero.
    """
    if type(max_events) is not int or not 4 <= max_events <= MAX_EVENTS:
        raise ValidationError("bounded groove onset count required")
    if not isinstance(start_offset_s,(int,float)) or not math.isfinite(start_offset_s):
        raise ValidationError("nonfinite groove audio offset")
    kick=next((x for x in project.tracks if x.id=="track-kick"),None)
    if not kick:
        raise ValidationError("missing kick MIDI")
    spans=[s for s in project.sections if s.name.lower() == section.lower()]
    if len(spans)!=1:
        raise ValidationError("requires one requested active section")
    part=spans[0]
    first,last=part.start,part.start+part.length
    onset=sorted({c.start+n.start for c in kick.clips for n in c.notes
                  if first <= c.start+n.start < last})
    if len(onset)<4:
        raise ValidationError("at least four active kicks required")
    if len(onset)>max_events:
        onset=[onset[i*(len(onset)-1)//(max_events-1)] for i in range(max_events)]
    wav=Path(wav)
    if wav.is_symlink() or not wav.is_file():
        raise ValidationError("missing or symlinked groove WAV")
    with wave.open(str(wav),"rb") as w:
        if (w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getcomptype()) != (RATE,2,3,"NONE"):
            raise ValidationError("groove pocket needs 48 kHz stereo PCM24")
        count=w.getnframes()
        measured=[]
        for tick in onset:
            # 0–100ms and 200–300ms windows, both equal in length.
            seconds=tick/project.ppq*60./project.tempo_bpm+start_offset_s
            pairs=[]
            for delay in (0., .2):
                start=round((seconds+delay)*RATE)
                if start<0 or start+4800 > count:
                    break
                w.setpos(start)
                raw=w.readframes(4800)
                if len(raw)!=4800*6:
                    raise ValidationError("truncated groove audio")
                pairs.append(_bandpowers(list(_decode(raw, 3, 2))))
            if len(pairs)==2:
                measured.append(pairs)
    if len(measured)<4:
        raise ValidationError("insufficient valid beat windows in selected section")
    near=[m[0] for m in measured];late=[m[1] for m in measured]
    ratios=[]
    for i,(lo,hi) in enumerate(BANDS):
        numerator=sum(row[i] for row in near)/len(near)
        denominator=sum(row[i] for row in late)/len(late)
        if min(numerator,denominator)<1e-16:
            raise ValidationError("silent selected groove band")
        ratios.append({
            "hz":[lo,hi],
            "kick_near_0_100ms_vs_offbeat_200_300ms_db":round(
                10*math.log10(numerator/denominator),3),
            "near_mean_power":round(numerator,6),
            "offbeat_mean_power":round(denominator,6)
        })
    return {
        "version": VERSION,"section":section,
        "tempo_bpm":project.tempo_bpm,
        "kick_onsets_used":len(measured),
        "bands":ratios,
        "windows_ms":[[0,100],[200,300]],
        "analysis": "full-mix beat-aligned mono band power, not kick/bass isolated stems",
        "perceptual_quality": "NOT_EVALUATED",
        "reference_policy": "No fixed Phase44 or Suno target. Compare equivalent song sections.",
        "limitations": [
            "Kick/bass share the measured full mix; cannot assign energy to either role.",
            "Full mix may include chord notes and effects in the measured bands.",
            "FFT window and playback section influence measured ratios.",
            "Same ratios can represent different musical feel; use human listening."
        ]
    }
