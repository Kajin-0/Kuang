"""Executable symbolic house gates; musical taste and production audio NOT evaluated."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from statistics import median
from .schema import BAR,PPQ,ValidationError,validate

VERSION="house-gates-symbolic-v1"
CORE=("kick","snare","hats","bass","harmony")

def _events(project):
    return {t.id.removeprefix("track-"): sorted((c.start+n.start,n.duration,n.pitch,n.velocity) for c in t.clips for n in c.notes)
            for t in project.tracks}

def _section(project,names):
    for name in names:
        for s in project.sections:
            if s.name==name:return s.start,s.start+s.length
    return None

def _count(events,window):
    return sum(window[0]<=t<window[1] for t,_,_,_ in events) if window else 0

def _bars(events,window):
    return tuple(tuple(sorted((t-at,d,p) for t,d,p,_ in events if at<=t<at+BAR))
                 for at in range(window[0],window[1],BAR)) if window else ()

def _hash(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def _invariant(project):
    secs=project.sections
    return (bool(secs) and secs[0].start==0 and
            secs[-1].start+secs[-1].length==project.length and
            all(a.start+a.length==b.start for a,b in zip(secs,secs[1:])))

def evaluate(project,*,expected_no_lead_arp=False):
    if type(expected_no_lead_arp) is not bool:raise ValidationError("explicit role-policy required")
    validate(project)
    ev=_events(project)
    groove=_section(project,("Groove A","Groove","Main"))
    drop=_section(project,("Main Drop","Drop","Finale"))
    breakdown=_section(project,("Breakdown","Break"))
    outro=_section(project,("Outro",))
    def density(role,window):
        return _count(ev.get(role,[]),window)/((window[1]-window[0])/BAR) if window else None
    fourfloor=None
    if groove:
        kicks={t for t,_,_,_ in ev.get("kick",[]) if groove[0]<=t<groove[1]}
        target={bar+beat*PPQ for bar in range(groove[0],groove[1],BAR) for beat in range(4)}
        fourfloor=bool(target) and target.issubset(kicks)
    breakdown_quiet=None if not breakdown else not (_count(ev.get("kick",[]),breakdown) or _count(ev.get("bass",[]),breakdown))
    no_extra=not any(ev.get(r) for r in ("lead","arp"))
    hard={
        "H01_four_four":project.time_signature==[4,4] and project.ppq==PPQ,
        "H02_section_partition":_invariant(project),
        "H03_required_bass_chords":bool(ev.get("bass")) and bool(ev.get("harmony")),
        "H04_kick_in_active_groove":fourfloor,
        "H05_breakdown_kick_bass_absent":breakdown_quiet,
        "H06_no_lead_arp_when_requested":no_extra if expected_no_lead_arp else None,
        "H07_preserve_dry_harmony_impact_policy":
            not any(a.id=="production-harmony-duck" for a in project.automation)
            if project.metadata.get("ducking_policy")=="bass-tail-3db-115ms; pad-1.25db-143ms; harmony-dry-0db"
            else None,
    }
    identity={}
    if groove and drop:
        for role in CORE:
            a=_bars(ev.get(role,[]),groove)
            b=_bars(ev.get(role,[]),drop)
            n=min(8,len(a),len(b))
            identity[role]=round(sum(a[i]==b[i] for i in range(n))/n,4) if n else None
    pitch_cells={}
    for role in CORE:
        events=ev.get(role,[])
        cells=tuple(tuple(sorted((t-start,d,p) for t,d,p,_ in events if start<=t<min(start+8*BAR,project.length)))
                    for start in range(0,project.length,8*BAR))
        pitch_cells[role]={"total":len(cells),"distinct":len(set(cells)),
                           "fraction_repeated":round(1-len(set(cells))/len(cells),4) if cells else None}
    musical=tuple((role,[(t,d,p) for t,d,p,_ in ev.get(role,[])]) for role in CORE)
    rhythm=tuple((role,[(t,d) for t,d,_,_ in ev.get(role,[])]) for role in CORE)
    kickless_automation={}
    kick_positions=[t for t,_,_,_ in ev.get("kick",[])]
    for s in project.sections:
        if any(s.start<=t<s.start+s.length for t in kick_positions):continue
        for lane in project.automation:
            if lane.id.endswith("-duck") and lane.parameter_id=="mixer.gain_db":
                vals=[point.value for point in lane.points if s.start<=point.tick<s.start+s.length]
                if len(vals)>=2 and max(vals)-min(vals)>=.5:
                    kickless_automation.setdefault(s.name,{})[lane.id]=round(max(vals)-min(vals),3)
    harmony_pitches=[p for _,_,p,_ in ev.get("harmony",[])]
    diagnostics={
        "D01_no_lead_arp":no_extra,
        "D02_core_groove_drop_equal_fraction":identity or None,
        "D03_core_drop_minus_groove_onsets_per_bar":
            {r:round(density(r,drop)-density(r,groove),4) for r in CORE} if groove and drop else None,
        "D04_outro_minus_groove_core_onsets_per_bar":
            round(sum(density(r,outro)-density(r,groove) for r in CORE),4) if groove and outro else None,
        "D05_chord_median_pitch_midi":median(harmony_pitches) if harmony_pitches else None,
        "D06_eight_bar_pitch_rhythm_repetition":pitch_cells,
        "D07_kickless_section_duck_automation":kickless_automation,
        "D08_minor_leading_tone_present":
            any(p%12==(project.key_tonic+11)%12 for p in harmony_pitches) if project.key_mode=="minor" else None,
    }
    failures=[k for k,v in hard.items() if v is False]
    return {"version":VERSION,"hard_gates":hard,"hard_failures":failures,
            "hard_applicable":sum(x is not None for x in hard.values()),
            "hard_passed":sum(x is True for x in hard.values()),
            "diagnostics":diagnostics,
            "fingerprints":{"musical_core":_hash(musical),"rhythm_core":_hash(rhythm)},
            "metadata":{"bars":project.bars,"tonic":project.key_tonic,"mode":project.key_mode,
                        "tempo_bpm":project.tempo_bpm},
            "perceptual_quality":"NOT_EVALUATED"}
