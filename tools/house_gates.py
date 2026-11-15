#!/usr/bin/env python3
"""Fast, deterministic matrix: legacy sketch/refined vs current opted-in groove."""
import argparse,json,sys
from collections import defaultdict
from pathlib import Path
from statistics import median
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from kuang.song import rules_plan
from kuang.composer import compose
from kuang.production import refine_house
from kuang.house_musical_plan import enrich_house_spec
from kuang.house_template import template
from kuang.house_full_arranger import arrange_full_song
from kuang.house_gates import evaluate,CORE,VERSION
from kuang.schema import ValidationError

PROFILES=("deep","straight","jackin","minimal")
KEYS=("C major","D minor")
LENGTHS=(16,32)
SEEDS=(17,18,19)
VARIANTS=("sketch","refined","groove-v2")

def make(profile,key,bars,seed,variant):
    prompt=f"{profile} house in {key}, {bars} bars, 126 bpm"
    spec,_=rules_plan(prompt,seed)
    if variant=="sketch":return compose(spec)
    if variant=="refined":return refine_house(spec,compose(spec))
    if variant=="groove-v2":
        spec,_=enrich_house_spec(spec,prompt,profile)
        return template(spec,profile=profile,impact_pocket=True,groove_identity_v2=True)[0]
    raise ValidationError("unsupported composer variant")

def benchmark(*,profiles=PROFILES,keys=KEYS,lengths=LENGTHS,seeds=SEEDS,variants=VARIANTS,
              long_form=False, developed_long_form=False):
    rows=[];errors=[]
    for variant in variants:
        for profile in profiles:
            for key in keys:
                for bars in lengths:
                    for seed in seeds:
                        desc=dict(variant=variant,profile=profile,key=key,bars=bars,seed=seed)
                        try:
                            project=make(profile,key,bars,seed,variant)
                            rows.append({**desc,"gates":evaluate(project,expected_no_lead_arp=variant=="groove-v2")})
                        except (ValidationError,AssertionError,ValueError) as err:
                            errors.append({**desc,"exception":str(err)})
    if long_form or developed_long_form:
        for developed in (False, True):
            if (developed and not developed_long_form) or (not developed and not long_form):
                continue
            for profile in profiles:
                for key in keys:
                    for seed in seeds[:1]:
                        variant="groove-full-developed-128" if developed else "groove-full-128"
                        desc=dict(variant=variant,profile=profile,key=key,bars=128,seed=seed)
                        try:
                            source=make(profile,key,32,seed,"groove-v2")
                            project,_=arrange_full_song(source,bars=128,profile=profile,seed=seed,
                                                        phrase_development_v1=developed)
                            rows.append({**desc,"gates":evaluate(project,expected_no_lead_arp=True)})
                        except (ValidationError,AssertionError,ValueError) as err:
                            errors.append({**desc,"exception":str(err)})
    summary={}
    for variant in (*variants,"groove-full-128","groove-full-developed-128"):
        group=[row for row in rows if row["variant"]==variant]
        if not group:continue
        def fraction(values):return round(sum(bool(x) for x in values)/len(values),4) if values else None
        def med(values):return round(median(values),4) if values else None
        windows=defaultdict(list)
        for row in group:windows[(row["profile"],row["key"],row["bars"])].append(row)
        unique=[len({r["gates"]["fingerprints"]["musical_core"] for r in block}) for block in windows.values()]
        distinct_rhythm=[len({r["gates"]["fingerprints"]["rhythm_core"] for r in block}) for block in windows.values()]
        first=group[0]["gates"]["hard_gates"]
        summary[variant]={
            "songs":len(group),
            "hard_pass_pct":round(100*fraction([not r["gates"]["hard_failures"] for r in group]),2),
            "hard_gate_pass_rates":{gate:fraction([r["gates"]["hard_gates"][gate] for r in group
                          if r["gates"]["hard_gates"][gate] is not None]) for gate in first},
            "median_unique_musical_seeds":med(unique),
            "median_unique_rhythm_seeds":med(distinct_rhythm),
            "musical_unique_by_style_key_bars":{"|".join(map(str,key)):len({r["gates"]["fingerprints"]["musical_core"] for r in entries})
                 for key,entries in sorted(windows.items())},
            "no_lead_arp_rate":fraction([r["gates"]["diagnostics"]["D01_no_lead_arp"] for r in group]),
            "core_groove_drop_identical_bar_fraction_median":{
                role:med([r["gates"]["diagnostics"]["D02_core_groove_drop_equal_fraction"][role]
                    for r in group if r["gates"]["diagnostics"]["D02_core_groove_drop_equal_fraction"] is not None
                    and role in r["gates"]["diagnostics"]["D02_core_groove_drop_equal_fraction"]])
                for role in CORE},
            "outro_minus_groove_core_density_median":med([r["gates"]["diagnostics"]["D04_outro_minus_groove_core_onsets_per_bar"]
                        for r in group if r["gates"]["diagnostics"]["D04_outro_minus_groove_core_onsets_per_bar"] is not None]),
            "minor_leading_tone_presence_rate":fraction([r["gates"]["diagnostics"]["D08_minor_leading_tone_present"]
                        for r in group if r["gates"]["diagnostics"]["D08_minor_leading_tone_present"] is not None]),
        }
    return {
        "version":"house-musical-benchmark-v1","gates_version":VERSION,
        "matrix":{"profiles":list(profiles),"keys":list(keys),"lengths":list(lengths),
                  "seeds":list(seeds),"variants":list(variants),"long_form":long_form,
                  "developed_long_form":developed_long_form},
        "summary":summary,"cases":rows,"errors":errors,
        "notes":"Source-only. No external VST, host, renderer, audio, or perceptual success claims. Key-specific benchmark with controlled seed matrix."
    }

def markdown(data):
    lines=["# Kuang: Symbolic Musical Quality Benchmark V1","",
           "These are **symbolic MIDI gates**, not audible-quality claims. Hard failures and musical diagnostics are separate.","",
           "| Version | Songs | Hard pass | Musical seed uniqueness (median) | Rhythmic seed uniqueness (median) | No lead/arp |",
           "|---|---:|---:|---:|---:|---:|"]
    for name,r in data["summary"].items():
        lines.append(f"| {name} | {r['songs']} | {r['hard_pass_pct']}% | {r['median_unique_musical_seeds']} | {r['median_unique_rhythm_seeds']} | {r['no_lead_arp_rate']} |")
    lines.extend(["","## Core-role Groove/Drop identical-bar fraction (first 8 corresponding bars)","",
                  "| Version | Kick | Snare | Hats | Bass | Harmony |","|---|---:|---:|---:|---:|---:|"])
    for name,r in data["summary"].items():
        x=r["core_groove_drop_identical_bar_fraction_median"]
        lines.append("| "+name+" | "+" | ".join(str(x[v]) for v in CORE)+" |")
    lines.extend(["","## Scope and interpretation","",
      "- H01–H03: valid 4/4/960PPQ, contiguous section partition, active bass and harmony.",
      "- H04: every quarter-note kick during named active Groove/Groove A/Main. N/A without such a section.",
      "- H05: no kick or bass during a named Breakdown/Break. N/A otherwise.",
      "- H06: disallow lead/arp ONLY when explicitly required for current groove templates. N/A legacy composer.",
      "- H07: preserve dry-harmony policy in groove-impact projects; N/A legacy composer.",
      "- D01–D08: lead/arp prevalence, groove/drop core-role bar similarity, onset density, outro thinning, chord register, eight-bar repetition, kick-free gain automation and minor leading-tone presence. Diagnostics are NOT pass/fail musical law.",
      "- Musical core fingerprints capture exact time, duration and pitch; rhythm captures time and duration only. Velocity and note IDs excluded to avoid false seed diversity.",
      "- The leading-tone check measures a pitch class, not harmonic dominant-function certainty.",
      "- Chord range, drop intensity, and outro thinning can be artistically valid exceptions. No threshold was retrofitted to make a variant look good.",
      "- Actual sound, mix quality, groove feel, perceptual arrangement contrast, and user preference remain unmeasured.",
      "",f"Generator exceptions: {len(data['errors'])}",""])
    return "\n".join(lines)

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--out-dir",required=True)
    cli.add_argument("--smoke",action="store_true")
    cli.add_argument("--full-form",action="store_true")
    cli.add_argument("--developed",action="store_true",
                     help="add opt-in developed long-form candidates; does not change frozen baseline")
    a=cli.parse_args()
    data=benchmark(profiles=PROFILES[:2] if a.smoke else PROFILES,
          keys=KEYS[:1] if a.smoke else KEYS,seeds=SEEDS[:2] if a.smoke else SEEDS,
          long_form=a.full_form and not a.smoke,
          developed_long_form=a.developed and not a.smoke)
    out=Path(a.out_dir)
    if out.exists() or out.is_symlink():raise ValidationError("output exists: frozen benchmark must not be overwritten")
    out.mkdir(parents=True)
    (out/"scorecard.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    (out/"scorecard.md").write_text(markdown(data)+"\n")
    for version,summary in data["summary"].items():
        print(version,summary["songs"],"songs hard",summary["hard_pass_pct"],"musical-unique",summary["median_unique_musical_seeds"])
    if data["errors"]:raise SystemExit("generator failures: "+str(len(data["errors"])))
    hard_failure_count=sum(bool(row["gates"]["hard_failures"]) for row in data["cases"])
    if hard_failure_count:
        raise SystemExit("hard structural gate failures: "+str(hard_failure_count))
if __name__=="__main__":main()
