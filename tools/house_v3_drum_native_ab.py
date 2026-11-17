"""Run the P2 native drum scene A/B against one existing, vetted 128-bar song.

Requires the authorized machine's existing private Vitalium and SoundCraft
native assets. Does NOT download sources, search presets, change production
defaults, or replace existing outputs. The section crop resets DSP; it is
not a sample-exact extract from a continuous 128-bar bounce.

Example (from Kuang repository root):
  python -m tools.house_v3_drum_native_ab \
    --source .local/ten-song-v1-03-jackin-20261115 \
    --out .local/house-v3-drum-main-drop-ab-NEW \
    --soundcraft /path/to/pinned/soundcraft-cli \
    --library .local/producer/libebur128.so
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from kuang.external_synth import inventory
from kuang.house_drum_scenes_v1 import apply_drum_scenes
from kuang.house_mix_roles import _host_adapter
from kuang.house_native_excerpt import crop_sounding_native
from kuang.loudness import measure
from kuang.schema import BAR, ValidationError, load, state_hash
from kuang.vitalium_patch import PLUGIN_ID


def _signature(project, role):
    track=next(t for t in project.tracks if t.id=="track-"+role)
    events=sorted((c.start+n.start,n.pitch,n.velocity,n.duration)
                  for c in track.clips for n in c.notes)
    return hashlib.sha256(repr(events).encode()).hexdigest()


def run(source, output, soundcraft, library, *, seed=217):
    source=Path(source).resolve()
    output=Path(output).absolute()
    workspace=Path.cwd().resolve()
    if (output.exists() or output.is_symlink() or
        not output.parent.is_dir() or
        not output.parent.resolve().is_relative_to(workspace) or
        output.is_relative_to(source)):
        raise ValidationError("native drum A/B requires fresh workspace destination")
    original=load(source/"project.kuang.json")
    before=state_hash(original)
    inventory_before=inventory(source)
    transformed,scene=apply_drum_scenes(original,seed=seed)
    drop=next((s for s in original.sections if s.name=="Main Drop"),None)
    if drop is None or drop.length<8*BAR:
        raise ValidationError("song lacks an eight-bar Main Drop")
    first=drop.start//BAR
    a,a_crop=crop_sounding_native(original,first,8)
    b,b_crop=crop_sounding_native(transformed,first,8)
    protected=("kick","bass","harmony","snare")
    for role in protected:
        if _signature(a,role)!=_signature(b,role):
            raise ValidationError("drum scene changed protected native "+role)
    if _signature(a,"hats")==_signature(b,"hats"):
        raise ValidationError("new drum scene has no actual hat MIDI difference")
    if {t.id for t in a.tracks}!={t.id for t in b.tracks}:
        raise ValidationError("drum scene changed cropped native role inventory")
    output.mkdir(mode=0o700)
    host=_host_adapter(source,workspace,output/"scratch",soundcraft)
    results={}
    for name,project,receipt in (
        ("A_unmodified",a,a_crop),("B_drum_scenes",b,b_crop)):
        folder=output/name
        folder.mkdir()
        assets={t.id:source/"native/assets"/t.id for t in project.tracks
                if t.instrument and t.instrument.plugin_ref=="soundcraft:sampler"}
        patches={t.id:source/"native/patches"/t.id for t in project.tracks
                 if t.instrument and t.instrument.plugin_ref==PLUGIN_ID}
        host.export(project,assets,patches,folder/"native")
        host.save(folder/"native",folder/"reopened")
        if host.inspect(folder/"reopened")["canonical_hash"]!=state_hash(project):
            raise ValidationError("native SoundCraft save/reopen drift")
        # Source-aware guard: give final samplers and spatial returns a
        # generous release window; never truncate to exact 8-bar endpoint.
        duration=8*4*60/project.tempo_bpm+12.
        host.render(folder/"native",folder/"preview.wav",end_seconds=duration)
        met=measure(folder/"preview.wav",library=str(library))
        if (met["clipped_samples"] or met["true_peak_dbtp"] > -1):
            raise ValidationError("drum A/B violated native true-peak/clip gate")
        results[name]={
            "canonical_native_reopen":True,
            "project_sha256":state_hash(project),
            "source_identity_sha256":before,
            "midi_hashes":{r:_signature(project,r) for r in
                           (*protected,"hats")},
            "audio_sha256":hashlib.sha256((folder/"preview.wav").read_bytes()).hexdigest(),
            "rms_dbfs":met["rms_dbfs"],
            "integrated_lufs":met["integrated_lufs"],
            "true_peak_dbtp":met["true_peak_dbtp"],
            "clipped_samples":met["clipped_samples"],
            "crop_proof":receipt,
        }
        print("NATIVE",name,"LUFS",met["integrated_lufs"],
              "dBTP",met["true_peak_dbtp"],flush=True)
    first_result=results["A_unmodified"]
    second_result=results["B_drum_scenes"]
    if first_result["audio_sha256"]==second_result["audio_sha256"]:
        raise ValidationError("different hat MIDI did not produce changed native audio")
    if state_hash(original)!=before or inventory(source)!=inventory_before:
        raise ValidationError("frozen source changed during A/B")
    report={
        "version":"house-v3-drum-scenes-native-ab-v1",
        "source_original_unmodified":True,
        "source_scene_evidence":scene,
        "results":results,
        "protected_midi_roles":list(protected),
        "changed_midi_roles":["hats"],
        "audio_causally_changed":True,
        "relative_lufs_delta":round(
            second_result["integrated_lufs"]-first_result["integrated_lufs"],3),
        "native_technical_gate_passed":True,
        "music_preference":"NOT_EVALUATED",
        "production_default_changed":False,
    }
    with (output/"summary.json").open("x") as file:
        json.dump(report,file,indent=2)
    print("NATIVE_DRUM_AB_PASS",report["relative_lufs_delta"],flush=True)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--soundcraft",required=True)
    p.add_argument("--library",required=True,type=Path)
    p.add_argument("--seed",type=int,default=217)
    a=p.parse_args()
    run(a.source,a.out,a.soundcraft,a.library,seed=a.seed)


if __name__=="__main__":
    main()
