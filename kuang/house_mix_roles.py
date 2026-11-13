"""Opt-in measured per-role balance for an existing private Kuang native song.

One Groove-section window, three isolated full-context native submixes,
bounded fader/automation changes, and an independently rendered result.

This is a *premix* technical experiment, not mastered audio or a perceptual
quality judge. Private Vital presets never leave the workspace.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import tempfile
import wave
from copy import deepcopy
from pathlib import Path

from . import midi
from .autonomous_create import PrivateExternal
from .external_synth import inventory
from .loudness import measure
from .production_host import ProductionAdapter
from .sample_assets import digest, write
from .vitalium_patch import PLUGIN_ID
from .schema import ValidationError, dumps, load, save, state_hash, validate

VERSION = "house-mix-roles-v1"
ROLES = {"kick": ("track-kick",), "bass": ("track-bass",),
         "chords": ("track-harmony",)}
# Start-of-mix engineering heuristics, not normative hit-song statistics.
TARGET_RELATIVE_RMS_DB = {"kick": 0., "bass": -3., "chords": -7.}
MAX_ROLE_MOVE_DB = 4.
MAX_OUTPUT_MOVE_DB = 6.
MAX_MEASUREMENT_SECONDS = 60


def _window(project):
    """Use the real Groove section, not the mostly sparse intro/breakdown."""
    sections = [s for s in project.sections if s.name.lower() == "groove"]
    if len(sections) != 1:
        raise ValidationError("one identifiable Groove section required")
    s = sections[0]
    start = s.start / project.ppq * 60 / project.tempo_bpm
    end = (s.start + s.length) / project.ppq * 60 / project.tempo_bpm
    if not 0 <= start < end <= MAX_MEASUREMENT_SECONDS:
        raise ValidationError("unsupported calibration duration/section")
    return {"name": s.name, "start_seconds": start, "end_seconds": end,
            "start_tick": s.start, "end_tick": s.start + s.length}


def _rms_region(path, window):
    """Stereo time-domain RMS over the same exact musically active window."""
    with wave.open(str(path), "rb") as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getcomptype()) != (48000, 2, 3, "NONE"):
            raise ValidationError("calibration requires 48-kHz stereo 24-bit PCM")
        start = round(window["start_seconds"] * 48000)
        end = round(window["end_seconds"] * 48000)
        if end <= start or end > w.getnframes():
            raise ValidationError("calibration window outside rendered WAV")
        w.setpos(start)
        remaining = end - start
        power = 0
        peak = 0
        samples = 0
        while remaining:
            data = w.readframes(min(16384, remaining))
            if not data or len(data) % 6:
                raise ValidationError("truncated calibration audio")
            for i in range(0, len(data), 3):
                value = int.from_bytes(data[i:i+3], "little", signed=True)
                power += value * value
                peak = max(peak, abs(value))
                samples += 1
            remaining -= len(data) // 6
    rms = math.sqrt(power / samples) / (2**23)
    if not math.isfinite(rms) or rms < 1e-7:
        raise ValidationError("missing or silent role stem in Groove window")
    return {"rms_dbfs": 20*math.log10(rms),
            "sample_peak_dbfs": 20*math.log10(peak/(2**23)) if peak else None,
            "start_seconds": window["start_seconds"],
            "end_seconds": window["end_seconds"],
            "wav_sha256": digest(path)}


def _role_solo(source, name):
    """Mute all other instruments, preserving native instruments, FX and buses."""
    if name not in ROLES:
        raise ValidationError("unsupported role")
    q = deepcopy(source)
    allowed = set(ROLES[name])
    for t in q.tracks:
        if t.kind == "midi":
            t.controls["mixer.mute"] = 0 if t.id in allowed else 1
    validate(q)
    return q


def role_offsets(metrics, *, limit_db=MAX_ROLE_MOVE_DB):
    if set(metrics) != set(ROLES) or type(limit_db) not in (int,float) or not 0 < limit_db <= 6:
        raise ValidationError("complete bounded per-role stem levels required")
    for role, data in metrics.items():
        if type(data) is not dict or type(data.get("rms_dbfs")) not in (int,float) or not math.isfinite(data["rms_dbfs"]):
            raise ValidationError("invalid per-role stem level: " + role)
        if not -100 < data["rms_dbfs"] < 0:
            raise ValidationError("impossible isolated role level: " + role)
    reference = metrics["kick"]["rms_dbfs"]
    offset = {"kick": 0.}
    evidence = {}
    for role in ("bass", "chords"):
        observed = metrics[role]["rms_dbfs"] - reference
        requested = TARGET_RELATIVE_RMS_DB[role] - observed
        bounded = max(-limit_db, min(limit_db, requested))
        offset[role] = round(bounded, 4)
        residual = observed + bounded - TARGET_RELATIVE_RMS_DB[role]
        evidence[role] = {"observed_vs_kick_db": round(observed,4),
                          "reference_target_vs_kick_db": TARGET_RELATIVE_RMS_DB[role],
                          "requested_db": round(requested,4),
                          "applied_db": offset[role],
                          "clamped": abs(requested) > limit_db,
                          "residual_vs_heuristic_db": round(residual,4),
                          "within_3db_heuristic": abs(residual) <= 3.,
                          "heuristic_only": True}
    return offset, evidence


def apply_offsets(project, adjustments):
    if set(adjustments) != set(ROLES):
        raise ValidationError("incomplete role adjustments")
    q = deepcopy(project)
    before = midi.export_bytes(project)
    tracks = {t.id: t for t in q.tracks}
    for role, ids in ROLES.items():
        delta = adjustments[role]
        if type(delta) not in (int,float) or not math.isfinite(delta) or abs(delta) > MAX_ROLE_MOVE_DB:
            raise ValidationError("role gain adjustment outside bounded range")
        for tid in ids:
            if tid not in tracks:
                raise ValidationError("required role missing: " + tid)
            t = tracks[tid]
            t.controls["mixer.gain_db"] += delta
            for lane in q.automation:
                if lane.target_id == tid and lane.parameter_id == "mixer.gain_db":
                    for point in lane.points:
                        point.value += delta
    validate(q)
    if midi.export_bytes(q) != before or q.sections != project.sections:
        raise ValidationError("role gain adjustment changed MIDI or section layout")
    for t,u in zip(project.tracks,q.tracks):
        if (t.id,t.instrument,t.clips,t.effects,t.sends,t.output_master) != (u.id,u.instrument,u.clips,u.effects,u.sends,u.output_master):
            raise ValidationError("role gain adjustment changed instruments, routing, notes or effects")
    return q


def _host_adapter(source_root, workspace, scratch, soundcraft):
    selection_path = source_root/"palette"/"selection.json"
    if not selection_path.is_file():
        raise ValidationError("private vetted palette selection required")
    selection = json.loads(selection_path.read_text())
    if selection.get("status") != "complete":
        raise ValidationError("incomplete private palette")
    private = PrivateExternal(selection["plugin"]["path"],soundcraft,workspace,scratch,selection)
    private.capabilities()
    native = ProductionAdapter(soundcraft,workspace=workspace,scratch=scratch)
    native.external = private
    native.samples.base = private.base
    native.base = private.base
    native.capabilities()
    return native


def calibrate_existing(source, soundcraft, output, *, max_role_db=4., max_output_db=6.):
    """Render kick/bass/chords in context, adjust faders, verify a *new* premix.

    The source session, original samples, presets and main branch are immutable.
    """
    raw_source = Path(source).absolute()
    if raw_source.is_symlink():
        raise ValidationError("source symlinks are not permitted")
    src = raw_source.resolve(strict=True)
    out = Path(output).absolute()
    workspace = Path.cwd().resolve()
    if (out.exists() or out.is_symlink() or
        not src.is_relative_to(workspace) or not out.resolve().is_relative_to(workspace) or
        not out.parent.is_dir() or out.resolve().is_relative_to(src)):
        raise ValidationError("new workspace-local output required, separate from source")
    if type(max_role_db) not in (int,float) or not 0 < max_role_db <= MAX_ROLE_MOVE_DB:
        raise ValidationError("role gain ceiling must be (0,4] dB")
    if type(max_output_db) not in (int,float) or not 0 <= max_output_db <= MAX_OUTPUT_MOVE_DB:
        raise ValidationError("output gain ceiling must be [0,6] dB")
    if not (src/"native"/"session.scraft").is_file():
        raise ValidationError("private native source is missing")
    original = load(src/"project.kuang.json")
    window = _window(original)
    source_hash = state_hash(original)
    before = inventory(src)
    assets = {t.id:src/"native"/"assets"/t.id for t in original.tracks
              if t.instrument and t.instrument.plugin_ref == "soundcraft:sampler"}
    patches = {t.id:src/"native"/"patches"/t.id for t in original.tracks
               if t.instrument and t.instrument.plugin_ref == PLUGIN_ID}
    # No license-unknown external patch states may ever be written to a public path.
    if not patches or not assets:
        raise ValidationError("existing combined sampler and vetted private Vital tracks required")
    with tempfile.TemporaryDirectory(prefix=".mix-roles-",dir=out.parent) as temp:
        stage = Path(temp)
        adapter = _host_adapter(src,workspace,stage/"scratch",soundcraft)
        baseline = adapter.inspect(src/"native")
        if baseline["canonical_hash"] != source_hash:
            raise ValidationError("native and source canonical drift")
        metrics = {}
        duration = original.length/original.ppq*60/original.tempo_bpm+12
        for role in ROLES:
            isolated = _role_solo(original,role)
            folder = stage/role
            folder.mkdir()
            adapter.export(isolated,assets,patches,folder/"native")
            adapter.render(folder/"native",folder/"stem.wav",end_seconds=duration)
            metrics[role] = _rms_region(folder/"stem.wav",window)
        proposed,relative = role_offsets(metrics,limit_db=max_role_db)
        revised = apply_offsets(original,proposed)
        folder = stage/"premix"
        folder.mkdir()
        adapter.export(revised,assets,patches,folder/"native")
        adapter.save(folder/"native",folder/"reopened")
        if adapter.inspect(folder/"reopened")["canonical_hash"] != state_hash(revised):
            raise ValidationError("revised premix did not persist after native save/reopen")
        raw = adapter.render(folder/"native",folder/"premix.wav",end_seconds=duration)
        library=workspace/".local"/"producer"/"libebur128.so"
        lib=str(library) if library.is_file() else None
        before_audio = measure(src/"preview.wav",library=lib)
        after_audio = measure(folder/"premix.wav",library=lib)
        if after_audio["clipped_samples"] or after_audio["true_peak_dbtp"] > -1.:
            raise ValidationError("calibrated premix failed peak headroom")
        # Bounded post-premix gain is separate, measured and never a club-master claim.
        headroom = -3. - after_audio["true_peak_dbtp"]
        final_gain = round(max(0., min(max_output_db, headroom)),4)
        if final_gain >= .1:
            final = deepcopy(revised)
            for track in final.tracks:
                track.controls["mixer.gain_db"] += final_gain
            for lane in final.automation:
                if lane.parameter_id == "mixer.gain_db":
                    for point in lane.points:
                        point.value += final_gain
            validate(final)
            adapter.export(final,assets,patches,folder/"output-native")
            adapter.save(folder/"output-native",folder/"output-reopened")
            output_report = adapter.render(folder/"output-native",folder/"output.wav",end_seconds=duration)
            final_audio = measure(folder/"output.wav",library=lib)
            if final_audio["clipped_samples"] or final_audio["true_peak_dbtp"] > -1.:
                raise ValidationError("post-balance output failed headroom")
            actual_project=final
        else:
            final_gain=0.
            output_report=raw
            final_audio=after_audio
            actual_project=revised
        write(stage/"balance-evidence.json",{
            "version": VERSION, "original_canonical_hash": source_hash,
            "calibrated_canonical_hash":state_hash(actual_project),
            "measurement_window":window,"stem_metrics":metrics,
            "relative_rms":relative,
            "role_balance_heuristic_gate": "MET" if all(x["within_3db_heuristic"] for x in relative.values()) else "NOT_MET",
            "role_gain_moves_db":proposed,
            "global_gain_move_db":final_gain,
            "source_loudness":before_audio, "premix_loudness":after_audio,
            "result_loudness":final_audio,
            "native_reopened_exact":True,"notes_and_sections_exact":True,
            "perceptual_quality":"NEEDS_LISTENING",
            "quality_improvement_established":False,
            "limitations":["RMS-based levels are role-aware engineering heuristics, not a balanced commercial-mix guarantee.",
                           "Three solo submixes include each role's real effects; nonlinearity means stem sum need not equal full mix.",
                           "Kick is anchor; other drum roles retain their earlier staging and are not individually calibrated.",
                           "No independent mastering chain, dynamic sidechain detector, or automatic psychoacoustic winner selection."]})
        # Preserve only one preferred *technical candidate*, and the measured evidence.
        # Never rewrite the original published reference, patches or palette.
        if inventory(src) != before:
            raise ValidationError("private source changed during balance calibration")
        for role in ROLES:
            shutil.rmtree(stage/role)
        shutil.rmtree(stage/"scratch",ignore_errors=True)
        shutil.rmtree(folder/"reopened",ignore_errors=True)
        shutil.rmtree(folder/"output-reopened",ignore_errors=True)
        out.mkdir(mode=0o700)
        try:
            for child in stage.iterdir():
                shutil.move(str(child),out/child.name)
        except BaseException:
            shutil.rmtree(out)
            raise
    return {"output":str(out),"role_moves_db":proposed,
            "global_gain_db":final_gain,"result_lufs":final_audio["integrated_lufs"],
            "result_dbtp":final_audio["true_peak_dbtp"],
            "human_approval":"NEEDS_LISTENING"}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",required=True)
    parser.add_argument("--soundcraft",required=True)
    parser.add_argument("--out-dir",required=True)
    parser.add_argument("--max-role-db",type=float,default=4.)
    parser.add_argument("--max-output-db",type=float,default=6.)
    args=parser.parse_args(argv)
    try:
        result=calibrate_existing(args.source,args.soundcraft,args.out_dir,
                                  max_role_db=args.max_role_db,max_output_db=args.max_output_db)
    except (ValidationError,OSError,ValueError,KeyError,TypeError) as e:
        parser.exit(2,"house-mix-roles: "+str(e)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
