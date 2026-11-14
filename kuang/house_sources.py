"""Opt-in CC0 house sample-kits in editable SoundCraft groove templates.

No network or third-party preset redistribution. Source pack is locally
supplied; audible quality requires a producer's listening decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import struct
import tempfile
import wave
from copy import deepcopy
from pathlib import Path

from .house_harmony import select_harmony
from .house_template import select_profile, template
from .midi import export_bytes
from .production_host import ProductionAdapter
from .sample_assets import create_asset, digest, inventory, read_asset, write
from .sampled_instrument import bind_samples
from .schema import ValidationError, dumps, load, save, validate
from .song import rules_plan, validate_spec

VERSION = "groove-house-cc0-samples-v1"
ROLES = {
    "kick": "kick",
    "snare": "clap",
    "hats": "hat_closed",
    "open_hat": "hat_open",
    "percussion": "perc",
}
PREFER = {
    "deep": {"kick": ("warm", "round"), "snare": ("tight", "dry"),
             "hats": ("dark", "tight"), "open_hat": ("airy", "open"), "percussion": ("shaker", "tight")},
    "straight": {"kick": ("punchy", "solid"), "snare": ("tight", "snappy"),
                 "hats": ("crisp", "tight"), "open_hat": ("bright", "open"), "percussion": ("tick", "dry")},
    "jackin": {"kick": ("punchy", "driving"), "snare": ("snappy", "bright"),
               "hats": ("bright", "crisp"), "open_hat": ("bright", "open"), "percussion": ("shaker", "driving")},
    "minimal": {"kick": ("tight", "short"), "snare": ("tight", "dry"),
                "hats": ("tight", "soft"), "open_hat": ("airy", "open"), "percussion": ("tick", "dry")},
}
MAX_SOURCE_BYTES = 2 * 1024 * 1024


def _sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _source_candidates(pack, profile, count=2):
    raw_pack = Path(pack)
    if raw_pack.is_symlink():
        raise ValidationError("sample pack symlinks are not permitted")
    pack = raw_pack.resolve(strict=True)
    if (pack / "manifest.json").is_symlink():
        raise ValidationError("sample pack symlinks are not permitted")
    manifest = json.loads((pack / "manifest.json").read_text())
    if (type(manifest) is not dict or manifest.get("name") != "house-core" or
        manifest.get("license") != "CC0-1.0" or type(manifest.get("samples")) is not dict):
        raise ValidationError("expected audited house-core CC0 manifest")
    if not (pack / "LICENSES.md").is_file() or not (pack / "LICENSE").is_file():
        raise ValidationError("missing pack licensing and per-sample audit")
    listing = manifest["samples"]
    if not 8 <= len(listing) <= 200:
        raise ValidationError("unsupported pack sample count")
    result = {}
    for role, expected in ROLES.items():
        possible = []
        for key, row in listing.items():
            if type(key) is not str or type(row) is not dict or row.get("type") != expected:
                continue
            relative = row.get("path")
            if (type(relative) is not str or Path(relative).is_absolute() or
                ".." in Path(relative).parts or not relative.endswith(".wav")):
                raise ValidationError("invalid source relative WAV path")
            path = pack / relative
            if (path.is_symlink() or not path.resolve().is_relative_to(pack) or
                not path.is_file() or path.stat().st_size > MAX_SOURCE_BYTES):
                raise ValidationError("missing, symlink or oversized source WAV")
            if type(row.get("license_source")) is not str or "CC0" not in row["license_source"]:
                raise ValidationError("source sample lacks explicit CC0 audit attribution")
            tags = tuple(row.get("character_tags", ()))
            if not all(type(t) is str and len(t) <= 50 for t in tags):
                raise ValidationError("invalid source character tags")
            score = sum(3 if t == PREFER[profile][role][0] else 1
                        for t in tags if t in PREFER[profile][role])
            if role == "percussion":
                if "shaker" in key and "shaker" in PREFER[profile][role]:
                    score += 3
                if "tick" in key and "tick" in PREFER[profile][role]:
                    score += 3
            possible.append((-score, key, row, path))
        possible.sort(key=lambda c: (c[0], c[1]))
        if len(possible) < count:
            raise ValidationError("insufficient audited sample candidates for role " + role)
        result[role] = possible[:count]
    return result


def _to_48k_pcm(src, dest):
    """Deterministic bandlimited sinc resampling, 44.1k 16-bit mono -> 48k 24-bit."""
    src, dest = Path(src), Path(dest)
    if src.is_symlink() or src.stat().st_size > MAX_SOURCE_BYTES:
        raise ValidationError("invalid source")
    with wave.open(str(src), "rb") as w:
        rate = w.getframerate()
        frames = w.getnframes()
        if (w.getnchannels(), w.getsampwidth(), w.getcomptype(), rate) != (1, 2, "NONE", 44100):
            raise ValidationError("CC0 pack source must be 44100 Hz mono 16-bit PCM")
        if not 128 <= frames <= rate * 3:
            raise ValidationError("sample duration out of bounds")
        pcm = w.readframes(frames)
    if len(pcm) != 2 * frames:
        raise ValidationError("truncated source PCM")
    samples = [int.from_bytes(pcm[i:i+2], "little", signed=True) / 32768.
               for i in range(0, len(pcm), 2)]
    ratio = rate / 48000
    length = (frames * 48000 + rate//2) // rate
    # Windowed sinc, 16 source-sample radius, 90% anti-alias cutoff. No
    # endpoint wrapping; every output is independently bounded.
    def sinc(t):
        return 1. if t == 0 else math.sin(math.pi * t) / (math.pi * t)
    output = bytearray()
    for i in range(length):
        x = i * ratio
        center = int(x)
        value = 0.
        norm = 0.
        for index in range(center - 15, center + 17):
            delta = x - index
            if abs(delta) >= 16:
                continue
            taper = .5 + .5 * math.cos(math.pi * delta / 16)
            weight = .90 * sinc(.90 * delta) * taper
            norm += weight
            if 0 <= index < frames:
                value += samples[index] * weight
        if norm:
            value /= norm
        # -1 dB safety attenuation; prevent accidental full-scale samples.
        scaled = max(-(1 - 2**-23), min((1 - 2**-23), value * 10**(-1/20)))
        q = round(scaled * (2**23 - 1))
        output.extend(q.to_bytes(3, "little", signed=True))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dest), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(48000)
        w.writeframes(output)
    return {"rate_in": rate, "rate_out": 48000, "frames_in": frames,
            "frames_out": length, "src_sha256": digest(src),
            "wav_sha256": digest(dest), "algorithm": "windowed-sinc-16-0.90-v1",
            "safety_attenuation_db": -1}


def prepare_kit(project, pack, library, profile, index=0, impact_pocket=False,
                groove_identity_v2=False):
    """Install an original four/five-drum-role kit without changing MIDI events."""
    if (profile not in PREFER or type(index) is not int or index not in (0, 1)
            or type(impact_pocket) is not bool or type(groove_identity_v2) is not bool
            or (groove_identity_v2 and not impact_pocket)):
        raise ValidationError("unknown kit or impact candidate")
    library = Path(library)
    library.mkdir(parents=True, exist_ok=False)
    candidates = _source_candidates(pack, profile)
    # The user's approved Phase44 kick is an explicitly CC0-audited source
    # already present in this same pack, not a private sample redistribution.
    approved_kick = None
    if impact_pocket and not groove_identity_v2 and profile in ('straight','deep','jackin'):
        approved_kick = next((c for c in _source_candidates(pack,'straight')['kick']
                              if c[1] == 'house.kick.punch-02'),None)
        if approved_kick is None:
            raise ValidationError('audited Phase44 kick punch-02 missing from pack')
    # The canonical groove intentionally contains MIDI 42 (closed) and 46
    # (open). The native sampler supports only one sample per track, so split
    # articulations into two editable sampler roles without adding MIDI hits.
    project = deepcopy(project)
    # Minimal house may intentionally omit auxiliary percussion; an empty
    # instrument track is rejected by the native host. Never add drum hits
    # solely to satisfy a sample binding. Preserve the source project.
    silent_perc = next((t for t in project.tracks if t.id == "track-percussion"
                        and not any(c.notes for c in t.clips)),None)
    if silent_perc is not None:
        owners = {silent_perc.id, *(fx.id for fx in silent_perc.effects)}
        if any(s.target_track_id == silent_perc.id
               for t in project.tracks for s in t.sends) or any(
               lane.target_id in owners for lane in project.automation):
            raise ValidationError("empty percussion has active routing or automation")
        project.tracks.remove(silent_perc)
    hat = next(t for t in project.tracks if t.id == "track-hats")
    opened = deepcopy(hat)
    opened.id = "track-open_hat"
    opened.name = "Open hat accents"
    opened.instrument.id = "instrument-open_hat"
    for fx in opened.effects:
        fx.id += "-open-hat"
    opened.clips = []
    for clip in hat.clips:
        open_notes = [n for n in clip.notes if n.pitch == 46]
        if open_notes:
            copied = deepcopy(clip)
            copied.id += "-open-hat"
            copied.name += " / open"
            copied.notes = open_notes
            opened.clips.append(copied)
        clip.notes = [n for n in clip.notes if n.pitch != 46]
    if not opened.clips or not any(n.pitch == 42 for c in hat.clips for n in c.notes):
        raise ValidationError("template needs separately articulated closed and open hats")
    project.tracks.append(opened)
    bindings = {}
    receipt = {}
    for role in ROLES:
        if not any(t.id == "track-" + role for t in project.tracks):
            if role == "percussion":
                continue
            raise ValidationError("required drum role missing: " + role)
        _, key, meta, src = (approved_kick if role == 'kick' and approved_kick else
                             candidates[role][index])
        item = library / role
        wav = item.with_suffix(".wav")
        stats = _to_48k_pcm(src, wav)
        source = {
            "creator": "Octal house-core sample pack authors",
            "source": f"house-core:{key}; original_sha256={stats['src_sha256']}",
            "license": "CC0-1.0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "notice": (f"Original CC0 source {meta['path']}; {meta['license_source']}; "
                       "deterministically resampled 44.1->48k and attenuated 1 dB"),
            "redistribution_permitted": True,
        }
        pitches = [n.pitch for track in project.tracks if track.id == "track-" + role
                   for clip in track.clips for n in clip.notes]
        if not pitches:
            raise ValidationError("sampled track lacks MIDI notes: " + role)
        mapping = {"root_note": pitches[0], "key_low": min(pitches),
                   "key_high": max(pitches), "velocity_low": 1,
                   "velocity_high": 127, "key_tracking": False,
                   "playback": "one_shot"}
        create_asset(wav, item, source, mapping)
        wav.unlink()
        read_asset(item)
        bindings["track-" + role] = item
        receipt[role] = {"source_id": key, "character_tags": meta["character_tags"],
                         "source_kind": "locally provided CC0 sample", "resample": stats,
                         "asset_sha256": digest(item / "asset.json")}
    result = bind_samples(project, bindings)
    for role in ROLES:
        if "track-" + role not in bindings:
            continue
        track = next(t for t in result.tracks if t.id == "track-" + role)
        # Independent per-role safety gains, with no hidden gain automation
        # on these drum tracks in the groove template.
        track.controls["mixer.gain_db"] -= {"kick": 5, "snare": 6, "hats": 6,
                                            "open_hat": 7, "percussion": 7}[role]
        if role == 'kick' and impact_pocket:
            track.controls['mixer.gain_db'] += 8.0
    validate(result)
    if impact_pocket:
        receipt['groove_impact_pocket'] = {
            'version':'phase44-derived-kick-balance-v1',
            'requested':True,
            'kick_relative_gain_delta_db':8.0,
            'kick_source':receipt['kick']['source_id'],
            'source_license':'CC0-1.0',
            'note':'No perceptual verdict; retains editable source and safe native output validation',
        }
    return result, bindings, receipt


def generate_sample_templates(prompt, pack, soundcraft, output, *, seed=17, bars=8,
                              groove_profile="auto", harmony_profile="auto",
                              max_variants=2, render=True):
    """Produce 1-2 real-source native candidate sessions, never assert a winner."""
    if type(max_variants) is not int or max_variants not in (1, 2):
        raise ValidationError("max_variants must be 1 or 2")
    if bars not in (8, 16, 32):
        raise ValidationError("sample audition currently supports 8/16/32 bars")
    out = Path(output).absolute()
    workspace = Path.cwd().resolve()
    if (not out.resolve().is_relative_to(workspace) or out.exists() or out.is_symlink() or
        not out.parent.is_dir()):
        raise ValidationError("sample-audition output must be a new workspace-local directory")
    if not soundcraft:
        raise ValidationError("real sample audition requires explicit SoundCraft executable")
    spec, notes = rules_plan(prompt, seed)
    if spec.genre != "house":
        raise ValidationError("only house is supported")
    import re
    explicit = re.search(r"\b(\d+)\s*bars?\b", prompt.lower())
    if explicit and int(explicit[1]) != bars:
        raise ValidationError("prompt and requested bar count conflict")
    spec.bars = bars
    validate_spec(spec)
    spec.instruments = [r for r in spec.instruments if r not in ("lead", "arp")]
    gp = select_profile(prompt, seed, groove_profile)
    hp = select_harmony(prompt, gp, harmony_profile)
    pad = not bool(re.search(r"\b(?:no|without)\s+(?:a\s+)?pads?\b", prompt.lower()))
    base, groove = template(spec, profile=gp, harmony_profile=hp, include_pad=pad)
    with tempfile.TemporaryDirectory(prefix=".sample-template-", dir=out.parent) as temp:
        stage = Path(temp)
        adapter = ProductionAdapter(soundcraft, workspace=workspace,
                                    scratch=stage / "scratch")
        adapter.capabilities()
        results = []
        for index in range(max_variants):
            candidate = stage / f"candidate-{index}"
            candidate.mkdir()
            bound, assets, sounds = prepare_kit(base, pack, candidate/"assets",
                                                 gp, index)
            # Export the real native SoundCraft sampler/VST-compatible graph.
            adapter.export(bound, assets, {}, candidate/"native")
            adapter.save(candidate/"native", candidate/"reopened")
            actual = load(candidate/"reopened"/"project.kuang.json")
            adapter.inspect(candidate/"reopened")
            if dumps(actual) != dumps(bound):
                raise ValidationError("sample-based native save/reopen drift")
            result = None
            if render:
                duration = bars * 4 * 60 / spec.bpm
                result = adapter.render(candidate/"native", candidate/"preview.wav",
                                        end_seconds=duration+5)
                if not result["audio"]["non_silent"] or result["audio"]["clipped_samples"]:
                    raise ValidationError("audition render silent or clipped")
            save(bound, candidate/"project.kuang.json")
            (candidate/"song.mid").write_bytes(export_bytes(bound))
            write(candidate/"evidence.json", {"index": index, "sounds": sounds,
                "source_binding_parent_hash": bound.metadata["sample_binding_parent_hash"],
                "groove_fingerprint_sha256": groove["groove_fingerprint_sha256"],
                "harmony_profile": hp, "native_save_reopen_equal": True,
                "audio": result, "perceptual_quality": "NEEDS_LISTENING",
                "quality_winner": None,
                "scope": "full-context preview; no independent quality verdict"})
            results.append({"id": f"candidate-{index}",
                            "kit": {k:v["source_id"] for k,v in sounds.items()},
                            "audio": result, "perceptual_quality": "NEEDS_LISTENING"})
        # No candidate is 'best' without evaluation. Keep every passing variant.
        write(stage/"report.json", {"version": VERSION, "prompt": prompt, "seed": seed,
            "bars": bars, "profile": gp, "harmony_profile": hp,
            "groove_fingerprint_sha256": groove["groove_fingerprint_sha256"],
            "groove": groove, "candidates": results, "quality_winner": None,
            "model_decision": "none; producer to compare candidates at matched loudness",
            "limitations": [
                "Open and closed hats are now separately editable sampler tracks with source MIDI note positions preserved.",
                "Vital bass/chord/pad private preset audition is not integrated into this command.",
                "Two default source kits are *candidate alternatives*, not a validated perceptual ranking.",
                "No per-role mix calibration, final true-peak master or full-length arrangement.",
                "Preset and sample quality are not certified by technical validation.",
            ]})
        # Remove temporary scratch and extra save; never publish an incomplete stage.
        shutil.rmtree(stage/"scratch", ignore_errors=True)
        for folder in stage.glob("candidate-*"):
            shutil.rmtree(folder/"reopened", ignore_errors=True)
        out.mkdir(mode=0o700)
        try:
            for child in stage.iterdir():
                shutil.move(str(child), out/child.name)
        except BaseException:
            shutil.rmtree(out)
            raise
    return {"output": str(out), "candidates": len(results),
            "quality_winner": None, "groove_profile": gp,
            "harmony_profile": hp}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument("--pack", required=True)
    parser.add_argument("--soundcraft", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--bars", type=int, choices=(8,16,32), default=8)
    parser.add_argument("--groove-profile", choices=("auto","straight","deep","jackin","minimal"),
                        default="auto")
    parser.add_argument("--harmony-profile", choices=("auto","simple","extended"),default="auto")
    parser.add_argument("--max-variants", type=int, choices=(1,2), default=2)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = generate_sample_templates(
            args.prompt, args.pack, args.soundcraft, args.out_dir,
            seed=args.seed, bars=args.bars, groove_profile=args.groove_profile,
            harmony_profile=args.harmony_profile,
            max_variants=args.max_variants, render=not args.no_render)
    except (ValidationError,OSError,ValueError,KeyError,TypeError) as e:
        parser.exit(2, f"house-sample-template: {e}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
