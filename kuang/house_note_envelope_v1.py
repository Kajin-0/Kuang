"""MIDI-aligned native note attack/release diagnostics; zero preference claims.

Measure the performed role's PCM envelope at original MIDI onsets. This is
*not* the synth's direct wet-free envelope: track FX, overlapping notes,
automation and previous tails matter. Only sufficiently isolated onsets
qualify. Reuse previously verified scratch role bounces, never source WAVs
or lossy mastered previews.
"""
from __future__ import annotations

import math
import statistics
import wave
import hashlib
from pathlib import Path

from .schema import BAR, PPQ, ValidationError, validate

VERSION="house-note-envelope-v1"
SAMPLE_RATE=48000
HOP_MS=5
MAX_EVENTS=20
ROLE_IDS=("harmony","bass","pad")


CHORD_STRUM_SPREAD_TICKS=24  # 12.5ms at 120 BPM, not across separate stabs


def _rollups(groups, *, group_strummed_chords=False):
    """Cluster tiny, intentional polyphonic MIDI note staggering.

    Source generation offsets each chord voice by 5 PPQ ticks. Treating these
    as four distinct musical stabs led to ZERO eligible onsets in original
    128-bar songs. Use a fixed max 24-tick distance from the cluster anchor,
    never chain neighboring offsets into wider and wider "chords." Two notes
    of identical pitch cannot share a chord attack by this heuristic.
    """
    events=[]
    for at, items in sorted(groups.items()):
        for dur,pitch in items:
            last=events[-1] if events else None
            if (group_strummed_chords and last is not None
                and at-last["tick"]<=CHORD_STRUM_SPREAD_TICKS
                and pitch not in last["_pitches"]):
                last["duration_ticks"]=max(last["duration_ticks"],dur+(at-last["tick"]))
                last["voices"]+=1
                last["_pitches"].add(pitch)
                last["max_strum_spread_ticks"]=max(last["max_strum_spread_ticks"],
                                                  at-last["tick"])
            else:
                events.append({"tick":at,"duration_ticks":dur,"voices":1,
                               "max_strum_spread_ticks":0,"_pitches":{pitch}})
    for event in events:
        event.pop("_pitches")
    return events


def _note_onsets(project, role, section, bars):
    validate(project)
    if role not in ROLE_IDS or type(bars) is not int or not 2<=bars<=16:
        raise ValidationError("bounded original MIDI role and bars required")
    s=next((s for s in project.sections if s.name==section),None)
    if s is None or s.length<bars*BAR:
        raise ValidationError("missing complete target section")
    t=next((t for t in project.tracks if t.id=="track-"+role),None)
    if t is None:raise ValidationError("source role missing")
    start=s.start
    end=start+bars*BAR
    groups={}
    # All notes in the section are included to evaluate preceding release
    # and next-onset contamination, even if only a subset is sampled.
    for clip in t.clips:
        for note in clip.notes:
            when=clip.start+note.start
            if start<=when<end:
                groups.setdefault(when,[]).append((note.duration,note.pitch))
    merged=_rollups(groups,group_strummed_chords=(role=="harmony"))
    return merged,start,end


def _samples(wav,first,last):
    """Return stereo RMS in 5ms bins from an existing 48k/PCM24 native WAV."""
    with wave.open(str(wav),"rb") as src:
        if (src.getframerate(),src.getnchannels(),src.getsampwidth(),src.getcomptype())!=(
                SAMPLE_RATE,2,3,"NONE"):
            raise ValidationError("actual SoundCraft 48kHz stereo PCM24 required")
        if not 0<=first<last<=src.getnframes():
            raise ValidationError("note window outside original native role bounce")
        hop=round(SAMPLE_RATE*HOP_MS/1000)
        src.setpos(first)
        remaining=last-first
        result=[]
        while remaining>0:
            count=min(hop,remaining)
            raw=src.readframes(count)
            if len(raw)!=count*6:
                raise ValidationError("truncated note-analysis native role waveform")
            energy=0.
            for offset in range(0,len(raw),3):
                v=int.from_bytes(raw[offset:offset+3],"little",signed=True)/8388608.
                energy+=v*v
            result.append(math.sqrt(energy/(count*2)))
            remaining-=count
    return result


def _med(values):
    return round(statistics.median(values),3) if values else None


def native_note_envelope(project,wav,*,role,section,bars=16,max_events=MAX_EVENTS):
    """Profile isolated MIDI onsets and bounded note-off tails.

    For an onset to qualify, last note-on is >=180ms earlier and next
    note-on >=250ms later. Previous overlapping note-off can still
    contaminate the target; such samples are marked and excluded.
    Attack rise is a *rendered 5ms-window proxy* 10%->90% of the local
    0..160ms excursion above the immediately preceding 40ms RMS floor.
    """
    events,start,end=_note_onsets(project,role,section,bars)
    if (type(max_events) is not int or not 1<=max_events<=MAX_EVENTS):
        raise ValidationError("bounded event count required")
    path=Path(wav)
    if path.is_symlink() or not path.is_file():raise ValidationError("existing native role WAV required")
    bpm=project.tempo_bpm
    seconds_per_tick=60./(bpm*PPQ)
    enough=[]
    with wave.open(str(path),"rb") as source:
        if (source.getframerate(),source.getnchannels(),source.getsampwidth(),
            source.getcomptype())!=(SAMPLE_RATE,2,3,"NONE"):
            raise ValidationError("verified 48kHz stereo PCM24 source required")
        total_frames=source.getnframes()
    total_skipped={"near_prior_onset":0,"near_next_onset":0,
                   "overlapping_prior_note":0,"audio_window":0,"low_signal":0}
    # Limit from the *first* portion of Groove to keep source comparisons
    # reproducible, never cherry-pick a subset for an aesthetically nice result.
    for i,event in enumerate(events):
        t=(event["tick"]-start)*seconds_per_tick
        previous=events[i-1] if i else None
        following=events[i+1] if i+1<len(events) else None
        if previous is not None and (event["tick"]-previous["tick"])*seconds_per_tick<.18:
            total_skipped["near_prior_onset"]+=1;continue
        if following is not None and (following["tick"]-event["tick"])*seconds_per_tick<.25:
            total_skipped["near_next_onset"]+=1;continue
        if previous is not None and (previous["tick"]+previous["duration_ticks"]-event["tick"])*seconds_per_tick>-.025:
            total_skipped["overlapping_prior_note"]+=1;continue
        if t<.06 or (t+.28)*SAMPLE_RATE>total_frames:
            total_skipped["audio_window"]+=1;continue
        onset_frame=round(t*SAMPLE_RATE)
        first=onset_frame-round(.05*SAMPLE_RATE)
        last=onset_frame+round(.26*SAMPLE_RATE)
        values=_samples(path,first,last)
        # offset is 50 ms / 5 ms = 10; attack bins 10..42
        zero=round(.05*1000/HOP_MS)
        floor=statistics.median(values[zero-8:zero])
        after=values[zero:zero+round(.16*1000/HOP_MS)]
        crest=max(after)
        if crest<=1e-7 or crest<floor*1.7:
            total_skipped["low_signal"]+=1;continue
        excursion=crest-floor
        def crossing(frac):
            threshold=floor+frac*excursion
            return next((idx for idx,v in enumerate(after) if v>=threshold),None)
        ten=crossing(.1);ninety=crossing(.9)
        if ten is None or ninety is None:
            total_skipped["low_signal"]+=1;continue
        # Use RMS (not peak) to compare the transient and body at identical
        # original MIDI velocity/register, with a shared backing/FX context.
        def energy(start_ms,end_ms):
            a=zero+start_ms//HOP_MS
            b=zero+end_ms//HOP_MS
            return math.sqrt(sum(v*v for v in values[a:b])/max(1,b-a))
        e030=energy(0,30);e30100=energy(30,100);e100200=energy(100,200)
        def db_ratio(a,b):
            return round(20*math.log10(max(a,1e-9)/max(b,1e-9)),3)
        # Separate release analysis is only meaningful if nothing new enters
        # around the actual note-off; it is marked unavailable otherwise.
        noteoff=t+event["duration_ticks"]*seconds_per_tick
        next_t=((following["tick"]-start)*seconds_per_tick if following else float("inf"))
        release_delta=None
        if noteoff-t>=.15 and noteoff+.18<min(next_t,total_frames/SAMPLE_RATE):
            before=int(round((noteoff-.04)*SAMPLE_RATE))
            afteroff=int(round((noteoff+.06)*SAMPLE_RATE))
            if before>0 and afteroff+round(.1*SAMPLE_RATE)<total_frames:
                left=_samples(path,before,before+round(.04*SAMPLE_RATE))
                right=_samples(path,afteroff,afteroff+round(.1*SAMPLE_RATE))
                left_r=math.sqrt(sum(x*x for x in left)/len(left))
                right_r=math.sqrt(sum(x*x for x in right)/len(right))
                if left_r>1e-6:
                    release_delta=db_ratio(right_r,left_r)
        enough.append({
          "onset_tick":event["tick"],"polyphonic_voices":event["voices"],
          "max_strum_spread_ticks":event["max_strum_spread_ticks"],
          "attack_10_90_ms":round((ninety-ten)*HOP_MS,2),
          "time_to_90pct_ms":ninety*HOP_MS,
          "first30_vs_30to100_db":db_ratio(e030,e30100),
          "30to100_vs_100to200_db":db_ratio(e30100,e100200),
          "release_60to160ms_vs_before_noteoff_db":release_delta,
          "baseline_to_attack_peak_db":db_ratio(crest,floor),
        })
        if len(enough)>=max_events:break
    attacks=[x["attack_10_90_ms"] for x in enough]
    relative=[x["first30_vs_30to100_db"] for x in enough]
    arrivals=[x["time_to_90pct_ms"] for x in enough]
    releases=[x["release_60to160ms_vs_before_noteoff_db"] for x in enough
              if x["release_60to160ms_vs_before_noteoff_db"] is not None]
    return {
      "version":VERSION,
      "role":role,"region":section+" first "+str(bars)+" bars",
      "midi_onset_groups":len(events),
      "strummed_chord_grouping_max_ticks":CHORD_STRUM_SPREAD_TICKS if role=="harmony" else 0,
      "qualified_isolated_events":len(enough),
      "minimum_valid_events_for_diagnosis":3,
      "evidence_sufficient":len(enough)>=3,
      "median_attack_10_90_ms":_med(attacks),
      "median_midi_onset_to_90pct_ms":_med(arrivals),
      "median_first30_vs_30to100_db":_med(relative),
      "median_post_noteoff_tail_db":_med(releases),
      "qualified_release_events":len(releases),
      "release_evidence_sufficient":len(releases)>=3,
      "skips":total_skipped,
      "per_event":enough,
      "source_hash":hashlib.sha256(path.read_bytes()).hexdigest(),
      "important_limitations":[
        "Measured from fully effected/fader-controlled native stereo stem, not oscillator ADSR.",
        "5ms sampled RMS and MIDI-aligned rise is a proxy, not psychophysical onset time.",
        "Not suitable for dense and overlapping notes; insufficient coverage must not trigger a source swap.",
        "Post-noteoff tails confounded by programmed release, reverb, delay and automation.",
        "Spectral masking and preference cannot be established by these numbers alone.",
      ],
      "musical_quality":"NOT_EVALUATED"
    }
