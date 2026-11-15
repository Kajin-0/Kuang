"""Bounded four-way native kick/bass audition from an existing verified private song.

Keep the exact symbolic score, nonselected synths, drums and effect graph.
Compare two audited CC0 kicks x two verified Vital bass sources, in real
native SoundCraft context. No automatic perceptual winner is declared.
Private states and WAVs never enter the public git checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import tempfile
import wave
from copy import deepcopy
from pathlib import Path

from . import midi
from .autonomous_create import PrivateExternal, _bind, _prepare, _probe_defaults
from .house_mix_roles import _role_solo, _window
from .house_one_prompt_context import short_audition_project
from .house_source_fit import fit_diagnostics
from .house_sources import _source_candidates, _to_48k_pcm
from .loudness import measure
from .production_host import ProductionAdapter
from .sample_assets import create_asset, digest, inventory, read_asset, write
from .schema import ValidationError, dumps, load, save, state_hash, validate

VERSION = "house-native-pair-audition-v1"
RATE = 48000
BITS = 3
CHANNELS = 2


def _source_kick_id(path):
    manifest = read_asset(path)
    label = manifest["provenance"]["source"]
    if not label.startswith("house-core:") or "; original_sha256=" not in label:
        raise ValidationError("baseline kick lacks audited house-core provenance")
    return label.split(";", 1)[0].removeprefix("house-core:")


def _alternate_kick(pack, profile, original_id, dest, reference):
    choices = _source_candidates(pack, profile)["kick"]
    selected = next(((key, meta, path) for _, key, meta, path in choices
                     if key != original_id), None)
    if selected is None:
        raise ValidationError("no distinct audited kick candidate")
    key, meta, source = selected
    outwav = dest.with_suffix(".wav")
    stats = _to_48k_pcm(source, outwav)
    credit = {
        "creator": "Octal house-core sample pack authors",
        "source": f"house-core:{key}; original_sha256={stats['src_sha256']}",
        "license": "CC0-1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "notice": (f"Original CC0 source {meta['path']}; {meta['license_source']}; "
                   "deterministically resampled 44.1->48k and attenuated 1 dB"),
        "redistribution_permitted": True
    }
    create_asset(outwav, dest, credit, read_asset(reference)["mapping"])
    outwav.unlink()
    return key, read_asset(dest)


def _variant(source, *, kick_asset=None, bass_patch=None):
    result = deepcopy(source)
    if kick_asset is not None:
        t = next(t for t in result.tracks if t.id == "track-kick")
        if t.instrument is None or t.instrument.plugin_ref != "soundcraft:sampler":
            raise ValidationError("kick is not an editable native sampler")
        t.instrument.preset_ref = "sha256:" + digest(Path(kick_asset) / "asset.json")
    if bass_patch is not None:
        # Bass patch swap is bound by the validated private adapter separately.
        # This function intentionally does not accept unverified raw preset bytes.
        result = bass_patch(result)
    validate(result)
    if midi.export_bytes(result) != midi.export_bytes(source):
        raise ValidationError("source swap modified MIDI")
    for base, changed in zip(source.tracks, result.tracks):
        if (base.id, base.controls, base.effects, base.clips, base.sends,
                base.output_master) != (changed.id, changed.controls, changed.effects,
                                        changed.clips, changed.sends, changed.output_master):
            raise ValidationError("source swap changed timing, levels, FX or routing")
        if base.id not in ("track-kick", "track-bass") and base.instrument != changed.instrument:
            raise ValidationError("unrelated instrument changed")
    return result


def _clip(source, dest, *, start_seconds, length_seconds):
    with wave.open(str(source), "rb") as stream:
        if (stream.getframerate(), stream.getnchannels(), stream.getsampwidth(),
                stream.getcomptype()) != (RATE, CHANNELS, BITS, "NONE"):
            raise ValidationError("native audition needs 48-kHz stereo PCM24")
        first = round(start_seconds * RATE)
        length = round(length_seconds * RATE)
        if first < 0 or first + length > stream.getnframes():
            raise ValidationError("native listening excerpt outside WAV")
        stream.setpos(first)
        data = stream.readframes(length)
        if len(data) != length * CHANNELS * BITS:
            raise ValidationError("truncated listening excerpt")
    with wave.open(str(dest), "wb") as dst:
        dst.setnchannels(CHANNELS)
        dst.setsampwidth(BITS)
        dst.setframerate(RATE)
        dst.writeframes(data)


def _gain_only(source, dest, gain_db):
    multiplier = 10 ** (gain_db / 20)
    with wave.open(str(source), "rb") as a, wave.open(str(dest), "wb") as b:
        b.setparams(a.getparams())
        while data := a.readframes(4096):
            out = bytearray()
            for i in range(0, len(data), BITS):
                value = int.from_bytes(data[i:i + BITS], "little", signed=True)
                scaled = round(value * multiplier)
                if not -(2**23) <= scaled < 2**23:
                    raise ValidationError("loudness match would clip sample")
                out.extend(scaled.to_bytes(BITS, "little", signed=True))
            b.writeframes(out)


def _match_clips(items, lib, target=-17.5):
    """Gain-only match at the quietest safe LUFS; not peak limiting."""
    loud = [measure(item["raw"], library=lib) for item in items]
    safe_target = min([target] + [m["integrated_lufs"] - m["true_peak_dbtp"] - 1.8 for m in loud])
    if not math.isfinite(safe_target) or safe_target < -35:
        raise ValidationError("invalid loudness comparison")
    for item, original in zip(items, loud):
        gain = safe_target - original["integrated_lufs"]
        _gain_only(item["raw"], item["matched"], gain)
        after = measure(item["matched"], library=lib)
        if (abs(after["integrated_lufs"] - safe_target) > .08
                or after["clipped_samples"] or after["true_peak_dbtp"] > -1.7):
            raise ValidationError("matched clip failed true-peak or LUFS gate")
        item["matched_meter"] = {
            "integrated_lufs": after["integrated_lufs"],
            "true_peak_dbtp": after["true_peak_dbtp"],
            "gain_db": round(gain, 4),
            "sha256": digest(item["matched"])
        }
        Path(item["raw"]).unlink()
        item.pop("raw")
    return safe_target


def compare_existing(source, pack, soundcraft, output, *, profile="deep", timeout=30):
    """Evaluate exactly 2 CC0 kick x 2 verified Vital bass combinations.

    No source or project overwrite. No network access or outside licensed
    palette. No automatic music-quality ranking or final song promotion.
    """
    raw = Path(source).absolute()
    out = Path(output).absolute()
    workspace = Path.cwd().resolve()
    pack = Path(pack).absolute()
    if (raw.is_symlink() or not raw.resolve().is_relative_to(workspace)
            or not (raw / "native" / "session.scraft").is_file()):
        raise ValidationError("verified workspace-local private source required")
    if (out.exists() or out.is_symlink() or not out.parent.is_dir()
            or not out.resolve().is_relative_to(workspace)
            or out.resolve().is_relative_to(raw.resolve())):
        raise ValidationError("new separate workspace-local output required")
    if profile not in ("deep", "straight", "jackin", "minimal"):
        raise ValidationError("unknown house groove profile")
    selection = json.loads((raw / "palette" / "selection.json").read_text())
    shortlist = selection.get("shortlist", {}).get("bass", [])
    if (selection.get("status") != "complete" or len(shortlist) != 1
            or shortlist[0].get("status") != "accepted"
            or shortlist[0].get("runtime_verified") is not True
            or shortlist[0].get("source_sha256") == selection["roles"]["bass"]["source_sha256"]):
        raise ValidationError("one distinct verified bass runner-up required")
    src = load(raw / "project.kuang.json")
    if src.bars != 16:
        raise ValidationError("audition currently requires verified 16-bar nucleus")
    original_hash = state_hash(src)
    original_midi = hashlib.sha256(midi.export_bytes(src)).hexdigest()
    source_inventory = inventory(raw)
    kick_asset = raw / "native" / "assets" / "track-kick"
    original_kick = _source_kick_id(kick_asset)
    original_bass = selection["roles"]["bass"]["source_preset_name"]
    first = short_audition_project(src, _window(src)["end_tick"])
    section = _window(first)
    duration = first.length / first.ppq * 60 / first.tempo_bpm + 6.
    lib_file = workspace / ".local" / "producer" / "libebur128.so"
    lib = str(lib_file) if lib_file.is_file() else None

    with tempfile.TemporaryDirectory(prefix=".native-pair-", dir=out.parent) as work:
        stage = Path(work)
        native_patches = {
            t.id: raw / "native" / "patches" / t.id for t in first.tracks
            if t.instrument and t.instrument.plugin_ref.startswith("vst3:")
        }
        samples = {
            t.id: raw / "native" / "assets" / t.id for t in first.tracks
            if t.instrument and t.instrument.plugin_ref == "soundcraft:sampler"
        }
        if "track-bass" not in native_patches or "track-kick" not in samples:
            raise ValidationError("private native bass and sampled kick required")
        authorized = deepcopy(selection)
        authorized["roles"]["alternate-bass"] = shortlist[0]
        adapter = PrivateExternal(selection["plugin"]["path"], soundcraft,
                                  workspace, stage / "scratch", authorized)
        adapter.capabilities()
        native = ProductionAdapter(soundcraft, workspace=workspace, scratch=stage / "scratch")
        native.external = adapter
        native.samples.base = adapter.base
        native.base = adapter.base
        native.capabilities()
        originals = native.inspect(raw / "native")
        if originals["canonical_hash"] != original_hash:
            raise ValidationError("private native source differs from project")
        defaults = _probe_defaults(adapter, stage)
        alternate_patch = _prepare(adapter, shortlist[0], defaults,
                                   stage / "prepare-alternate-bass", timeout)
        alternate_name, _ = _alternate_kick(pack, profile, original_kick,
                                            stage / "alternate-kick", kick_asset)

        def change_bass(p):
            return _bind(p, {"track-bass": alternate_patch}, adapter)

        pairs = (("A-original", False, False), ("B-kick-alternate", True, False),
                 ("C-bass-alternate", False, True), ("D-both-alternates", True, True))
        outputs = []
        for label, altkick, altbass in pairs:
            p = _variant(first, kick_asset=stage / "alternate-kick" if altkick else None,
                         bass_patch=change_bass if altbass else None)
            assignment = dict(native_patches)
            assets = dict(samples)
            if altkick:
                assets["track-kick"] = stage / "alternate-kick"
            if altbass:
                assignment["track-bass"] = alternate_patch
            folder = stage / label
            folder.mkdir()
            native.export(p, assets, assignment, folder / "native")
            native.save(folder / "native", folder / "reopened")
            if native.inspect(folder / "reopened")["canonical_hash"] != state_hash(p):
                raise ValidationError("native save/reopen changed a source variant")
            save(p, folder / "project.kuang.json")
            (folder / "song.mid").write_bytes(midi.export_bytes(p))
            native.render(folder / "native", folder / "full.wav", end_seconds=duration)
            meter = measure(folder / "full.wav", library=lib)
            if (meter["clipped_samples"] or meter["true_peak_dbtp"] > -1
                    or meter["rms"] < 1e-6):
                raise ValidationError(f"candidate {label} failed safe-native-render gate")
            outputs.append({
                "name": label, "kick_source": alternate_name if altkick else original_kick,
                "bass_source": shortlist[0]["source_preset_name"] if altbass else original_bass,
                "project_sha256": state_hash(p),
                "midi_sha256": hashlib.sha256(midi.export_bytes(p)).hexdigest(),
                "full_mix": folder / "full.wav",
                "project": p, "assets": assets, "patches": assignment,
                "peak_dbtp": meter["true_peak_dbtp"]
            })
            print("NATIVE_PAIR", label, "kick", outputs[-1]["kick_source"],
                  "bass", outputs[-1]["bass_source"], flush=True)

        # Only four additional isolated role renders: two independent kicks
        # and two independent basses, shared between all four combinations.
        stems = {}
        for role in ("kick", "bass"):
            for alternate in (False, True):
                item = outputs[3 if alternate else 0]
                p = item["project"]
                assets = item["assets"]
                patches = item["patches"]
                folder = stage / f"stem-{role}-{'alt' if alternate else 'original'}"
                folder.mkdir()
                native.export(_role_solo(p, role), assets, patches, folder / "native")
                native.render(folder / "native", folder / "stem.wav", end_seconds=duration)
                stems[(role,alternate)] = folder / "stem.wav"

        audio_entries = []
        for item, (_, ak, ab) in zip(outputs, pairs):
            fit = fit_diagnostics(item["project"], section,
                                  stems["kick", ak], stems["bass", ab], None,
                                  item["full_mix"])
            folder = stage / item["name"]
            listen_raw = folder / "raw-listening.wav"
            listen_matched = folder / "matched-listening.wav"
            _clip(item["full_mix"], listen_raw,
                  start_seconds=section["start_seconds"] - .08,
                  length_seconds=section["end_seconds"]-section["start_seconds"] + .2)
            row = {k: v for k,v in item.items() if k not in (
                "project","assets","patches","full_mix")}
            row.update({
                "native_context": fit, "raw": str(listen_raw),
                "matched": str(listen_matched),
                "native_safe": True, "perceptual_winner": None
            })
            audio_entries.append(row)
        target = _match_clips(audio_entries, lib)
        for row in audio_entries:
            row["matched"] = str(Path(row["matched"]).relative_to(stage))
            row["notes"] = "measured only; no automatic ranking or musical approval"
        if inventory(raw) != source_inventory or state_hash(load(raw / "project.kuang.json")) != original_hash:
            raise ValidationError("private source mutated during comparison")
        evidence = {
            "version": VERSION, "source_project_sha256": original_hash,
            "source_midi_sha256": original_midi,
            "total_pairs": 4, "native_renders": 8,
            "kick_variants": [original_kick, alternate_name],
            "bass_variants": [original_bass, shortlist[0]["source_preset_name"]],
            "matching_target_lufs": target, "candidate_results": audio_entries,
            "automatic_winner_selected": False,
            "perceptual_quality": "REQUIRES_LISTENING",
            "source_licensing": "CC0 kick; Vital states are verified private-use only",
            "source_preservation": True
        }
        write(stage / "pair-comparison.json", evidence)
        # Private synth patches and audited CC0 assets remain on the VPS.
        # Preserve only required song reports, WAVs and native session projects.
        for path in list(stage.iterdir()):
            if path.name in [label for label,_,_ in pairs] or path.name == "pair-comparison.json":
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        for item in outputs:
            folder = stage / item["name"]
            (folder / "full.wav").unlink()
            shutil.rmtree(folder / "reopened")
        out.mkdir(mode=0o700)
        try:
            for child in stage.iterdir():
                shutil.move(str(child), out / child.name)
        except BaseException:
            shutil.rmtree(out)
            raise
    return {"output": str(out), "receipt": str(out / "pair-comparison.json"),
            "audio": [str(out / r["matched"]) for r in audio_entries],
            "perceptual_winner": None}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True)
    p.add_argument("--pack", required=True)
    p.add_argument("--soundcraft", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--profile", choices=("deep", "straight", "jackin", "minimal"), default="deep")
    args = p.parse_args(argv)
    try:
        report = compare_existing(args.source,args.pack,args.soundcraft,args.out,
                                  profile=args.profile)
    except (ValidationError, ValueError, OSError, RuntimeError, KeyError) as e:
        p.exit(2, f"native-pair-audition: {e}\n")
    print(json.dumps(report,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
