"""Source-locked 8-bar native House spatial return A/B/C across three styles.

Pure opt-in benchmark. Does not alter source MIDI, patches, source references,
legacy generator defaults, or publish musical winners. Real aux bus inserts,
not offline stereo tricks. Requires pinned local SoundCraft/Vitalium/CC0 assets.
"""
from __future__ import annotations
import json
import hashlib
import math
import sys
from copy import deepcopy
from pathlib import Path

from kuang import midi
from kuang.gestures import crop
from kuang.house_v3_space import house_v3_space
from kuang.house_mix_roles import _host_adapter
from kuang.house_source_policy import source_exclusion
from kuang.loudness import measure
from kuang.production_host import add_spread, graph_contract
from kuang.sample_assets import inventory
from kuang.schema import Effect, Send, Track, ValidationError, load, state_hash, validate, BAR
from kuang.vitalium_patch import PLUGIN_ID
from tools.audio_fingerprint import analyze_window

SCENES=("A_dry","B_room_plate","C_room_plate_echo")
SOURCE_CASES={
    "03_jackin":"ten-song-v1-03-jackin-20261115",
    "06_deep":"ten-song-v1-06-deep-20261115",
    "07_minimal":"ten-song-v1-07-minimal-20261115",
}
HOST="/home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli"
ROOT=Path("/home/User/Kuang")
LOCAL=ROOT/".local"
LIB=str(LOCAL/"producer/libebur128.so")
REFERENCE=LOCAL/"phase44-experiment/release"


def make_scene(source, reference, style):
    if style not in SCENES:
        raise ValidationError("unknown native spatial production scene")
    p=deepcopy(source)
    if style=="A_dry":
        graph_contract(p)
        return p
    if style=="B_room_plate":
        return house_v3_space(p)
    templates={t.id:t for t in reference.tracks}
    by={t.id:t for t in p.tracks}
    # Only dry, source-preserving upper roles are fed to shared wet returns.
    for name,id,original,send_levels in (
        ("room","house-v3-room","phase15-shared-room",
         {"track-harmony":-6.,"track-pad":-11.}),
        ("plate","house-v3-plate","phase17-dark-space",
         {"track-harmony":-10.,"track-pad":-7.}),
        ("echo","house-v3-echo","phase17-echo",
         {"track-harmony":-10.}),
    ):
        if name=="echo" and style!="C_room_plate_echo":
            continue
        template=templates[original]
        fx=[deepcopy(template.effects[-1])]
        fx[0].id="house-v3-"+name+"-fx"
        bus=Track(id,"House-v3 shared "+name,"bus",None,
            {"mixer.gain_db":6.020599913279624,"mixer.pan":0.,
             "mixer.mute":0.},fx,[],[],True)
        p.tracks.append(bus)
        add_spread(p,bus,1.)
        for tid,db in send_levels.items():
            if tid in by:
                by[tid].sends.append(Send("house-v3-"+name+"-"+tid,
                    id,db,0.,"post_fader"))
    # Copy only missing exact verified canonical parameter specifications.
    existing={x.id:x for x in p.parameters}
    for spec in reference.parameters:
        if spec.id not in existing:
            p.parameters.append(deepcopy(spec))
            existing[spec.id]=spec
    p.metadata["house_v3_spatial_experiment"]="opt-in; real 100-percent-wet native room/plate/echo returns; dry direct and source immutable"
    validate(p);graph_contract(p)
    if midi.export_bytes(source)!=midi.export_bytes(p):
        raise ValidationError("scene changed source MIDI")
    if any(a!=b for a,b in zip(source.tracks,p.tracks[:len(source.tracks)])):
        # Source track sends intentionally change; all other fields must not.
        for a,b in zip(source.tracks,p.tracks[:len(source.tracks)]):
            copy=deepcopy(b);copy.sends=deepcopy(a.sends)
            if copy!=a:
                raise ValidationError("scene changed source track besides permitted new wet sends")
    for tid in ("track-kick","track-bass"):
        if tid in by and by[tid].sends:
            raise ValidationError("kick or bass sent to wet spatial returns")
    return p


def source_crop(project):
    begin,end=16*BAR,24*BAR
    tids=[
      t.id for t in project.tracks if t.kind=="midi" and
      any(begin <= c.start+n.start < end for c in t.clips for n in c.notes)
    ]
    p=crop(project,16,8,tids)
    return p


def run(output):
    if output.exists():
        raise ValidationError("refusing to overwrite spatial A/B evidence")
    output.mkdir(parents=True)
    reference=load(REFERENCE/"project.kuang.json")
    summary={"version":"house-v3-native-spatial-source-locked-v1",
             "dry_sources_preserved":True,"human_musical_winner":None,
             "production_default_changed":False,
             "source_songs":{}}
    for label,dirname in SOURCE_CASES.items():
        original=LOCAL/dirname
        src=load(original/"project.kuang.json")
        selected=json.loads((original/"palette/selection.json").read_text())
        bass=selected["roles"]["bass"]["source_sha256"]
        if source_exclusion("bass",bass):
            raise ValidationError("producer rejected source cannot enter spatial trial")
        inventory_before=inventory(original)
        base=source_crop(src)
        patches={t.id:original/"native/patches"/t.id
                 for t in base.tracks if t.instrument and t.instrument.plugin_ref==PLUGIN_ID}
        samples={t.id:original/"native/assets"/t.id
                 for t in base.tracks if t.instrument and t.instrument.plugin_ref=="soundcraft:sampler"}
        scene_dir=output/label;scene_dir.mkdir()
        adapter=_host_adapter(original,ROOT,output/"scratch",HOST)
        bar_seconds=4*60/src.tempo_bpm
        song_result={"source_project_hash":state_hash(src),
                     "source_bass_sha256":bass,
                     "profile":label,"cases":{}}
        for scene in SCENES:
            p=make_scene(base,reference,scene)
            target=scene_dir/scene
            target.mkdir()
            adapter.export(p,samples,patches,target/"native")
            adapter.save(target/"native",target/"reopened")
            if adapter.inspect(target/"reopened")["canonical_hash"]!=state_hash(p):
                raise ValidationError("native spatial save/reopen identity drift")
            adapter.render(target/"native",target/"preview.wav",end_seconds=8*bar_seconds+8)
            meter=measure(target/"preview.wav",library=LIB)
            if meter["clipped_samples"] or meter["true_peak_dbtp"] > -1:
                raise ValidationError("spatial production preview violated peak safety")
            f=analyze_window(target/"preview.wav",0,8*bar_seconds,loudness_library=LIB)
            song_result["cases"][scene]={
                "native_roundtrip_verified":True,"canonical_hash":state_hash(p),
                "meters":{"lufs":meter["integrated_lufs"],
                          "true_peak_dbtp":meter["true_peak_dbtp"],
                          "clipped_samples":meter["clipped_samples"]},
                "source_midi_sha256":hashlib.sha256(midi.export_bytes(p)).hexdigest(),
                "groove":f}
            print("NATIVE",label,scene,
                "2-8k width",f["frequency_bands"]["presence_2000_8000"]["side_mid_db"],
                "sub retention",f["frequency_bands"]["sub_20_120"]["mono_retention_fraction"],
                "TP",round(meter["true_peak_dbtp"],3),flush=True)
        a=song_result["cases"]["A_dry"]["groove"]
        for scene in SCENES[1:]:
            f=song_result["cases"][scene]["groove"]
            old=a["frequency_bands"]["presence_2000_8000"]["side_mid_db"]
            new=f["frequency_bands"]["presence_2000_8000"]["side_mid_db"]
            delta=round(new-old,3) if new is not None and old is not None else None
            low=f["frequency_bands"]["sub_20_120"]["mono_retention_fraction"]
            song_result["cases"][scene]["delta_upper_stereo_db"]=delta
            song_result["cases"][scene]["sub_mono_safe"]=low is not None and low>=.995
        if inventory(original)!=inventory_before:
            raise ValidationError("private original source assets were modified")
        summary["source_songs"][label]=song_result
        (scene_dir/"evidence.json").write_text(json.dumps(song_result,indent=2))
        print("SOURCE_DONE",label,flush=True)
    gains=[c["delta_upper_stereo_db"] for x in summary["source_songs"].values()
           for s,c in x["cases"].items() if s=="C_room_plate_echo"]
    summary["all_sources_rendered"]=len(summary["source_songs"])==3
    summary["C_upper_stereo_gain_db_by_style"]=gains
    summary["C_gain_at_least_3db_count"]=sum(x is not None and x>=3 for x in gains)
    summary["technical_spatial_candidate"]=(
      summary["C_gain_at_least_3db_count"]>=2 and
      all(v["cases"]["C_room_plate_echo"]["sub_mono_safe"]
          for v in summary["source_songs"].values()))
    (output/"summary.json").write_text(json.dumps(summary,indent=2))
    print("SPATIAL_BATCH_COMPLETE",summary["technical_spatial_candidate"],gains,flush=True)


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    run(args.out)
