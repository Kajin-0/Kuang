"""Offline audit of separately acquired House reference WAVs; no downloads.

Source catalog labels are publisher claims, not evidence of audio quality or
permission to redistribute/AI-train on source audio. Quantitative metrics are
reference diagnostics, not a producer-quality score or optimization target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import wave
from pathlib import Path

from kuang.audio import analyze_wav
from kuang.loudness import measure
from kuang.production_audio import _decode, _fft
from kuang.schema import ValidationError

VERSION = "house-external-reference-audit-v1"
CATALOG = Path(__file__).resolve().parents[1] / "docs" / "HOUSE_AUDIO_REFERENCE_CATALOG.json"
BANDS = (("sub_20_40", 20, 40), ("kick_40_80", 40, 80),
         ("upper_bass_80_120", 80, 120), ("low_mid_120_250", 120, 250),
         ("body_250_500", 250, 500), ("mid_500_2000", 500, 2000),
         ("presence_2000_8000", 2000, 8000),
         ("air_8000_nyquist", 8000, math.inf))
ROLES = ("mixed", "kick", "snare", "clap", "hat", "percussion", "bass",
         "drum_loop", "instrument_stem", "drum_bus", "mix")


def catalog_sources(path=CATALOG):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("version") != "house-audio-source-catalog-v1":
        raise ValidationError("unrecognized external reference catalog")
    sources = doc.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValidationError("empty or invalid source catalog")
    ids = [row.get("id") for row in sources if isinstance(row, dict)]
    if len(ids) != len(sources) or len(set(ids)) != len(ids):
        raise ValidationError("duplicate/invalid catalog IDs")
    return {row["id"]: row for row in sources}


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def spectral_summary(path, *, frames, rate, channels, width, max_windows=16):
    """Average window power; intentionally no invented kick fundamental.

    Window length is largest power-of-two <= min(8192, frames). The upper
    frequency resolution limit is 1 / actual window duration; FFT-bin peaks
    may include bass or synthesis harmonics and are NOT pitch trajectories.
    """
    n = 1 << min(13, frames.bit_length() - 1)
    if n < 2048:
        return None
    positions = sorted({round(i * (frames - n) / max(1, min(max_windows, frames // n) - 1))
                        for i in range(min(max_windows, frames // n))})
    if not positions:
        return None
    hann = [.5 - .5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    powers = [0.] * (n // 2 + 1)
    with wave.open(str(path), "rb") as stream:
        for start in positions:
            stream.setpos(start)
            raw = stream.readframes(n)
            if len(raw) != n * width * channels:
                raise ValidationError("truncated spectral window")
            decoded = list(_decode(raw, width, channels))
            for channel in range(channels):
                fft = _fft([frame[channel] * gain for frame, gain in zip(decoded, hann)])
                for k in range(1, len(powers)):
                    powers[k] += abs(fft[k]) ** 2 * (1 if k == n // 2 else 2)
    band = {name: sum(v for k, v in enumerate(powers)
                      if low <= k * rate / n < min(high, rate / 2 + 1))
            for name, low, high in BANDS}
    total = sum(band.values())
    bins = [k for k in range(1, len(powers)) if 30 <= k * rate / n <= 150]
    candidate = max(bins, key=lambda k: powers[k]) if bins and total else None
    return {"method": "Hann FFT; equal-weight uniformly spaced windows and channels; excludes DC",
            "fft_size": n, "window_count": len(positions),
            "actual_window_seconds": n / rate, "bin_spacing_hz": rate / n,
            "dominant_30_150_hz_bin": round(candidate * rate / n, 4) if candidate else None,
            "dominant_bin_is_kick_fundamental": False,
            "band_power_fraction": {name: round(power / total, 8) if total else None
                                    for name, power in band.items()}}


def analyze_reference(path, *, role, loudness=False):
    if role not in ROLES:
        raise ValidationError("unrecognized sample role")
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValidationError("missing or symlinked reference WAV")
    info = analyze_wav(path)
    if info["channels"] not in (1, 2) or not 8000 <= info["sample_rate"] <= 192000:
        raise ValidationError("reference needs mono/stereo PCM at 8-192 kHz")
    crest = (info["peak_dbfs"] - info["rms_dbfs"]
             if info["rms_dbfs"] is not None else None)
    out = {"sha256": sha256_file(path), "role_label": role, "role_label_source": "user supplied",
           "format": {k: info[k] for k in ("sample_rate", "channels", "bits_per_sample", "frames", "duration_seconds")},
           "peak_dbfs": info["peak_dbfs"], "rms_dbfs": info["rms_dbfs"],
           "crest_db": crest, "clipped_samples": info["clipped_samples"],
           "non_silent": info["non_silent"],
           "spectrum": spectral_summary(path, frames=info["frames"], rate=info["sample_rate"],
                                        channels=info["channels"], width=info["bits_per_sample"] // 8)}
    # LUFS is gated, time-integrated loudness, not an isolated transient score.
    # Never label one-shot kick/clap/hat LUFS as a professional mix reference.
    eligible = role in ("drum_loop", "instrument_stem", "drum_bus", "mix") and info["duration_seconds"] >= .4
    if loudness and eligible:
        m = measure(path)
        out["loudness"] = {"integrated_lufs": m["integrated_lufs"],
                           "true_peak_dbtp": m["true_peak_dbtp"],
                           "shortterm_max_lufs": m["shortterm_max_lufs"],
                           "certified": False, "backend": m["backend"]}
    else:
        out["loudness"] = {"status": "not_requested" if not loudness else
                           "not_meaningful_for_role_or_short_duration"}
    return out


def _stat(values):
    vals = sorted(v for v in values if v is not None and math.isfinite(v))
    if not vals:
        return None
    return {"n_files": len(vals), "median": round(statistics.median(vals), 4),
            "min": round(vals[0], 4), "max": round(vals[-1], 4)}


def audit_collection(input_root, output, *, source_id, role, group_id=None,
                     loudness=False, limit=50, catalog=CATALOG):
    sources = catalog_sources(catalog)
    if source_id not in sources or role not in ROLES:
        raise ValidationError("source_id/role must be listed in source catalog/allowed roles")
    if type(limit) is not int or not 1 <= limit <= 2000:
        raise ValidationError("limit must be 1..2000")
    if group_id is not None and (not isinstance(group_id, str) or not group_id.strip() or len(group_id) > 96):
        raise ValidationError("group_id must be a short manual grouping label")
    root = Path(input_root)
    dest = Path(output)
    if root.is_symlink() or not root.is_dir() or dest.exists():
        raise ValidationError("reference folder must exist and output must be new")
    actual_root, actual_dest = root.resolve(), dest.resolve()
    if actual_dest.is_relative_to(actual_root):
        raise ValidationError("output must not be inside the reference-audio folder")
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".wav")
    if not files or len(files) > limit:
        raise ValidationError(f"WAV count outside 1..{limit}; increase --max-files explicitly")
    if any(p.is_symlink() or not p.resolve().is_relative_to(actual_root) for p in files):
        raise ValidationError("symlinked/out-of-tree reference WAV")
    if any(p.stat().st_size > 256 * 1024 ** 2 for p in files):
        raise ValidationError("one WAV exceeds 256 MiB per-file safety bound")
    records = []
    for p in files:
        name = p.relative_to(root).as_posix()
        try:
            metrics = analyze_reference(p, role=role, loudness=loudness)
            records.append({"relative_path": name, "status": "measured", **metrics})
        except (ValidationError, wave.Error, OSError, ValueError) as exc:
            records.append({"relative_path": name, "status": "rejected", "reason": str(exc)[:320]})
    good = [r for r in records if r["status"] == "measured"]
    result = {"version": VERSION, "source_id": source_id,
              "source_page": sources[source_id]["source_page"],
              "license_status": sources[source_id]["rights"]["status"],
              "source_fidelity_status": "not independently auditioned",
              "source_audio_embedded": False, "group_id": group_id,
              "independent_observations_established": False,
              "selection": "all WAVs sorted by relative path, no cherry-picking",
              "labels": {"role": role, "role_source": "user supplied; not inferred from filenames"},
              "settings": {"loudness_requested": loudness, "maximum_files": limit},
              "summary": {"files_found": len(files), "measured": len(good),
                          "rejected": len(files) - len(good),
                          "peak_dbfs": _stat(r["peak_dbfs"] for r in good),
                          "rms_dbfs": _stat(r["rms_dbfs"] for r in good),
                          "crest_db": _stat(r["crest_db"] for r in good)},
              "limitations": ["Source page is not a machine-verified license grant for arbitrary use.",
                              "File-level metrics do not certify professional quality or listening preference.",
                              "Files may be layers/processing variants from one construction kit; n_files is not independent n.",
                              "All comparisons require matched roles, mix stages, and appropriate analysis windows.",
                              "Spectral dominant bin is not proof of fundamental pitch; short-window resolution is limited.",
                              "No source audio or paths outside the input root are included."],
              "files": records}
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-root", type=Path, required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--role", choices=ROLES, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--group-id")
    p.add_argument("--loudness", action="store_true", help="Meter longer loops/mixes/stems; can be slow")
    p.add_argument("--max-files", type=int, default=50)
    args = p.parse_args(argv)
    result = audit_collection(args.input_root, args.out, source_id=args.source_id,
                              role=args.role, group_id=args.group_id,
                              loudness=args.loudness, limit=args.max_files)
    print(json.dumps({"report": str(args.out), "source_id": result["source_id"],
                      **result["summary"]}, indent=2))
    return 2 if result["summary"]["rejected"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
