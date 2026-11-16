"""Opt-in source-specific House bass-level trials, never an automatic mix decision.

Use existing native verified candidate projects and their real SoundCraft WAVs.
Same note onsets and patches across A/B, same section and duration. Compare
*relative* kick/offbeat low-band energy; measure headroom independently.
A passing diagnostic remains conditional on native kick/bass stem interaction
and listening. No fixed Phase44 curve, no globally selected bass gain.
"""
from __future__ import annotations

import math
from copy import deepcopy
from pathlib import Path

from . import midi
from .house_groove_pocket import VERSION as POCKET_VERSION, evaluate_pocket
from .loudness import measure
from .schema import ValidationError, state_hash, validate

VERSION = "house-bass-audio-gate-v1"
BANDS = ((25., 90.), (90., 250.))
MAX_TRIAL_GAIN_DB = 6.
MIN_SUB_IMPROVEMENT_DB = 1.0
MIN_BODY_IMPROVEMENT_DB = .5
TRUE_PEAK_CEILING_DBTP = -1.0


def _finite(x):
    return type(x) in (int, float) and math.isfinite(x)


def bass_gain_trial(project, *, gain_db):
    """Change only bass track gain and any bass mixer-gain automation offset.

    Returns an independent canonical project. This is a private audition
    *hypothesis*, not a production default or recommended mix balance.
    """
    validate(project)
    if not _finite(gain_db) or not 0. < gain_db <= MAX_TRIAL_GAIN_DB:
        raise ValidationError("bass audition gain must be finite and in (0,6] dB")
    before = state_hash(project)
    result = deepcopy(project)
    bass = next((t for t in result.tracks if t.id == "track-bass"), None)
    if bass is None or "mixer.gain_db" not in bass.controls:
        raise ValidationError("canonical bass track gain is required")
    bass.controls["mixer.gain_db"] += gain_db
    for lane in result.automation:
        if lane.target_id == bass.id and lane.parameter_id == "mixer.gain_db":
            for point in lane.points:
                point.value += gain_db
    validate(result)
    if midi.export_bytes(result) != midi.export_bytes(project):
        raise ValidationError("bass-level audition modified MIDI")
    if state_hash(project) != before:
        raise ValidationError("bass-level audition modified source")
    return result, {
        "version": VERSION, "source_project_sha256": before,
        "candidate_project_sha256": state_hash(result),
        "bass_gain_offset_db": gain_db,
        "midi_unchanged": True, "nonbass_tracks_unchanged": True,
        "patches_fx_sends_unchanged": True,
        "native_validation": "REQUIRED",
        "default_enabled": False, "musical_winner": None,
    }


def _ratios(pocket):
    if (type(pocket) is not dict or pocket.get("version") != POCKET_VERSION or
            pocket.get("kick_onsets_used", 0) < 4):
        raise ValidationError("actual aligned native groove-pocket evidence required")
    rows = pocket.get("bands")
    if type(rows) is not list or len(rows) != 2:
        raise ValidationError("both 25-90 and 90-250 Hz pocket bands are required")
    vals = []
    for i, row in enumerate(rows):
        if (type(row) is not dict or row.get("hz") != list(BANDS[i])):
            raise ValidationError("unexpected groove-pocket band definition")
        ratio = row.get("kick_near_0_100ms_vs_offbeat_200_300ms_db")
        if not _finite(ratio):
            raise ValidationError("nonfinite native groove-pocket ratio")
        vals.append(ratio)
    return vals


def _safe(meter):
    if (type(meter) is not dict or not all(
            _finite(meter.get(k)) for k in ("integrated_lufs", "true_peak_dbtp", "duration_seconds")) or
            type(meter.get("clipped_samples")) is not int):
        raise ValidationError("complete measured native loudness, peak and clip evidence required")
    return (meter["clipped_samples"] == 0 and
            meter["true_peak_dbtp"] <= TRUE_PEAK_CEILING_DBTP)


def review_native_bass_trials(source_project, source_wav, candidates, *,
                              section="Groove", library=None):
    """Evaluate genuine, native verified, source-preserving WAV counterfactuals.

    candidates: tuples (gain_db, candidate_project, native_wav, native_verified)
    in deliberate preference-neutral order. Returns a conditional shortlist,
    *not* a chosen gain or automatic production patch.
    """
    validate(source_project)
    if type(candidates) not in (list, tuple) or not 1 <= len(candidates) <= 4:
        raise ValidationError("1..4 bounded native bass candidates required")
    source_hash = state_hash(source_project)
    source_midi = midi.export_bytes(source_project)
    base_meter = measure(source_wav, library=library)
    if not _safe(base_meter):
        raise ValidationError("baseline fullmix must be nonclipped with true peak margin")
    base_pocket = evaluate_pocket(source_project, source_wav, section=section)
    base_bands = _ratios(base_pocket)
    output = []
    seen = set()
    for item in candidates:
        if type(item) not in (tuple, list) or len(item) != 4:
            raise ValidationError("gain, project, native WAV, verified flag required")
        gain, candidate, path, native_verified = item
        if not _finite(gain) or gain in seen:
            raise ValidationError("duplicate or invalid trial gain")
        seen.add(gain)
        if native_verified is not True:
            raise ValidationError("trial requires independently verified native save and reopen")
        expected, receipt = bass_gain_trial(source_project, gain_db=gain)
        if candidate != expected or midi.export_bytes(candidate) != source_midi:
            raise ValidationError("candidate modifies MIDI, sources, routing, FX or unrelated tracks")
        if state_hash(source_project) != source_hash:
            raise ValidationError("source project mutated during review")
        meter = measure(path, library=library)
        if abs(meter["duration_seconds"] - base_meter["duration_seconds"]) > 1/48000 + 1e-8:
            raise ValidationError("unaligned native source/candidate WAV durations")
        pocket = evaluate_pocket(candidate, path, section=section)
        bands = _ratios(pocket)
        if pocket["kick_onsets_used"] != base_pocket["kick_onsets_used"]:
            raise ValidationError("candidate altered sampled kick events")
        low, body = [round(a-b, 3) for a, b in zip(base_bands, bands)]
        safe = _safe(meter)
        conditional = (safe and low >= MIN_SUB_IMPROVEMENT_DB and
                       body >= MIN_BODY_IMPROVEMENT_DB)
        output.append({
            "gain_db": gain, "candidate_sha256": receipt["candidate_project_sha256"],
            "native_verified": True, "peak_and_clipping_safe": safe,
            "true_peak_dbtp": meter["true_peak_dbtp"],
            "clipped_samples": meter["clipped_samples"],
            "lufs_delta_vs_original": round(meter["integrated_lufs"]-base_meter["integrated_lufs"], 3),
            "sub_25_90_beat_offbeat_delta_db": low,
            "body_90_250_beat_offbeat_delta_db": body,
            "raw_beat_offbeat_db": bands,
            "conditional_spectral_gate": conditional,
            "stem_interference_and_mono_review": "REQUIRED_BEFORE_PROMOTION",
            "human_listening": "REQUIRED_BEFORE_PROMOTION",
        })
    allowed = sorted((r for r in output if r["conditional_spectral_gate"]),
                     key=lambda r: r["gain_db"])
    return {
        "version": VERSION, "source_project_sha256": source_hash,
        "section": section, "source_bpm": source_project.tempo_bpm,
        "baseline_beat_offbeat_db": base_bands,
        "baseline_lufs": base_meter["integrated_lufs"],
        "baseline_true_peak_dbtp": base_meter["true_peak_dbtp"],
        "tested": output,
        "minimum_conditional_gain_db": allowed[0]["gain_db"] if allowed else None,
        "candidate_status": "SPECTRAL_SHORTLIST_ONLY" if allowed else "NO_SPECTRAL_PASS",
        "automatic_gain_change": False, "winner": None,
        "production_default_changed": False,
        "phase_aware_stem_review": "NOT_YET_MEASURED",
        "perceptual_quality": "NOT_EVALUATED",
        "interpretation": "A lower fullmix beat/offbeat ratio is an energy change, not proof of stronger musical groove. Different presets/styles need independent native evidence. Do not optimize to Phase44 numbers.",
    }
