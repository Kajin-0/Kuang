"""Standalone staged revision and A/B audition of an existing local song directory."""

import hashlib
import json
import os
import shutil
import tempfile
import time
from copy import deepcopy
from pathlib import Path

from . import midi
from .audio import compare_wavs
from .revision import (SUPPORTED, RulesRevisionPlanner, _digest, apply_plan, prepare_revision,
                       replay_revision)
from .schema import ValidationError, dumps, load, state_hash, strict_json
from .soundcraft import SoundCraftAdapter


def add_parser(commands):
    command = commands.add_parser("revise", help="strict rules revision, exact preservation and optional A/B audio")
    command.add_argument("source", help="create/revise directory or canonical SoundCraft bundle")
    command.add_argument("prompt", nargs="?", help=SUPPORTED)
    command.add_argument("--out-dir", help="new directory; required unless --plan-only")
    command.add_argument("--plan-only", action="store_true", help="print validated change plan without writing or running a host")
    command.add_argument("--plan", help="apply a previously reviewed JSON plan instead of prose")
    command.add_argument("--expected-hash", help="optional SHA-256 precondition, in addition to the plan's precondition")
    command.add_argument("--soundcraft", help="installed 0.11.0 CLI or KUANG_SOUNDCRAFT")
    command.add_argument("--soundcraft-timeout", type=float, default=120)
    command.add_argument("--render", action="store_true", help="render fresh original/revised WAVs and verify aligned PCM difference")


def _bytes(path):
    if not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
        raise ValidationError(f"missing/oversized project or JSON file: {path}")
    return path.read_bytes()


def _read(path):
    return strict_json(_bytes(Path(path)).decode("utf-8"))


def _write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def source_hashes(root):
    """Bounded, streaming inventory, including previews and unrecognized local files."""
    result, size = {}, 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValidationError("song directory must not contain symlinks")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValidationError("song directory contains a nonregular file")
        size += path.stat().st_size
        if len(result) >= 512 or size > 1024**3:
            raise ValidationError("revision source exceeds MVP inventory limit (512 files / 1 GiB)")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        result[str(path.relative_to(root))] = digest.hexdigest()
    return result


def _source(root):
    _bytes(root / "project.kuang.json")
    project = load(root / "project.kuang.json")
    native = root / "native" if (root / "native").exists() else root if (root / "session.scraft").exists() or (root / "manifest.json").exists() else None
    if native:
        _bytes(native / "project.kuang.json")
        snapshot = load(native / "project.kuang.json")
        manifest, host = _read(native / "manifest.json"), _read(native / "session.scraft")
        if (type(manifest) is not dict or manifest.get("version") != "1" or
                dumps(snapshot) != dumps(project) or manifest.get("canonical_hash") != state_hash(project) or
                manifest.get("native_hash") != _digest(host) or
                manifest.get("native_file_sha256") != hashlib.sha256(_bytes(native / "session.scraft")).hexdigest()):
            raise ValidationError("source bundle drift; explicit snapshot recovery/re-export is required")
    report_path = root / "report.json"
    if report_path.exists():
        report = _read(report_path)
        if type(report) is not dict:
            raise ValidationError("source report must be an object")
        validation = report.get("validation", {})
        expected = validation.get("canonical_hash") if type(validation) is dict else None
        expected = expected or report.get("canonical_hash")
        if expected and expected != state_hash(project):
            raise ValidationError("source canonical/report drift; use a new validated export")
    return project, native


def _audio_ok(report):
    a = report["analysis"]
    if not (a["non_silent"] and a["rms"] > 1e-6 and a["peak"] < 1 and a["clipped_samples"] == 0 and report["native_unchanged"]):
        raise ValidationError("A/B preview failed non-silence/clipping/native preservation checks")


def revise(source, prompt=None, output=None, *, plan=None, plan_only=False, expected_hash=None,
           soundcraft=None, soundcraft_timeout=120, render=False):
    started = time.perf_counter()
    root = Path(source).expanduser().resolve()
    if not root.is_dir():
        raise ValidationError("revision source must be an existing song directory")
    destination = None
    if not plan_only:
        if not output:
            raise ValidationError("--out-dir is required unless --plan-only")
        raw = Path(output).expanduser()
        destination = raw.resolve()
        if raw.is_symlink() or destination.exists():
            raise ValidationError("revision output already exists; choose a new directory")
        if destination.is_relative_to(root):
            raise ValidationError("revision output must be outside the source directory")
    if (prompt is None) == (plan is None):
        raise ValidationError("provide either a revision prompt or --plan, exclusively")
    files_before = source_hashes(root)
    original, native_source = _source(root)
    if expected_hash is not None and expected_hash != state_hash(original):
        raise ValidationError("stale project hash; revision rejected")
    if plan is None:
        request = RulesRevisionPlanner().propose(deepcopy(original), prompt)
        prepared, _, _ = prepare_revision(original, request)
    else:
        prepared = deepcopy(plan)
        apply_plan(original, prepared)
    planning_seconds = time.perf_counter() - started
    if plan_only:
        if source_hashes(root) != files_before:
            raise ValidationError("source changed while planning")
        return prepared
    selected = soundcraft or os.environ.get("KUANG_SOUNDCRAFT")
    if render and not selected:
        raise ValidationError("--render requires --soundcraft /absolute/path/to/soundcraft-cli or KUANG_SOUNDCRAFT")
    adapter = SoundCraftAdapter(selected, timeout=soundcraft_timeout) if selected else None
    if adapter and native_source:
        if dumps(adapter.import_project(native_source)) != dumps(original):
            raise ValidationError("source native snapshot differs from the canonical project")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".kuang-revise-", dir=destination.parent) as directory:
        stage = Path(directory) / "publish"
        stage.mkdir()
        # The reviewable plan is recorded before candidate application or host work.
        _write(stage / "change-plan.json", prepared)
        apply_started = time.perf_counter()
        revised, receipt = apply_plan(original, _read(stage / "change-plan.json"))
        if (dumps(replay_revision(revised, receipt, undo=True)) != dumps(original) or
                dumps(replay_revision(original, receipt, undo=False)) != dumps(revised)):
            raise ValidationError("revision failed exact undo/redo verification")
        apply_seconds = time.perf_counter() - apply_started
        (stage / "original.kuang.json").write_bytes(_bytes(root / "project.kuang.json"))
        (stage / "project.kuang.json").write_text(dumps(revised), encoding="utf-8")
        (stage / "song.mid").write_bytes(midi.export_bytes(revised))
        _write(stage / "revision-receipt.json", receipt)
        (stage / "receipts").mkdir()
        for i, step in enumerate(receipt["receipts"], 1):
            _write(stage / "receipts" / f"{i:02d}.json", step)
        for name, target in (("report.json", "source-report.json"), ("song-spec.json", "song-spec.json")):
            if (root / name).exists():
                (stage / target).write_bytes(_bytes(root / name))
        # Keep complete report provenance when users move a revised directory
        # independently of its ancestors. Content addressing deduplicates history.
        provenance = stage / "provenance"
        provenance.mkdir()
        incoming = [root / "report.json", root / "source-report.json"]
        if (root / "provenance").is_dir():
            incoming += sorted((root / "provenance").rglob("*.json"))
        for path in incoming:
            if path.exists():
                data = _bytes(path)
                strict_json(data.decode("utf-8"))
                archived = provenance / (hashlib.sha256(data).hexdigest() + ".json")
                if not archived.exists():
                    archived.write_bytes(data)
        artifacts = {"canonical": str(destination / "project.kuang.json"), "original_canonical": str(destination / "original.kuang.json"),
                     "midi": str(destination / "song.mid"), "plan": str(destination / "change-plan.json"),
                     "receipt": str(destination / "revision-receipt.json"), "report": str(destination / "report.json")}
        validation = {"canonical_hash": state_hash(revised), "original_canonical_hash": state_hash(original),
                      "exact_undo_redo": True, "unchanged_canonical_equal": True, "source_static_manifest_verified": bool(native_source),
                      "source_host_verified": bool(adapter and native_source), "native_verified": False, "audio_verified": False}
        capabilities = {"adapter": None, "reason": "canonical/MIDI only; native/audio not verified"}
        exports, native_comparison, audio = {}, None, None
        native_started = time.perf_counter()
        if adapter:
            capabilities = adapter.capabilities(revised)
            exports["original"] = (adapter.save(native_source, stage / "original-native") if native_source else
                                   adapter.export(original, stage / "original-native"))
            exports["revised"] = adapter.export(revised, stage / "native")
            native_comparison = adapter.compare_revision(stage / "original-native", stage / "native", receipt["receipts"])
            for label, folder in (("original", "original-native"), ("revised", "native")):
                exports[label]["output"] = str(destination / folder)
                _write(stage / folder / "report.json", exports[label])
            artifacts.update(original_native=str(destination / "original-native/session.scraft"), native=str(destination / "native/session.scraft"))
            validation["native_verified"] = True
        native_seconds = time.perf_counter() - native_started
        render_started = time.perf_counter()
        if render:
            a = adapter.render(stage / "original-native", stage / "original.wav")
            b = adapter.render(stage / "native", stage / "preview.wav")
            _audio_ok(a); _audio_ok(b)
            difference = compare_wavs(stage / "original.wav", stage / "preview.wav")
            if not difference["measurable_change"]:
                raise ValidationError("revision has no sufficiently large aligned PCM difference; no output published")
            a["output"], b["output"] = str(destination / "original.wav"), str(destination / "preview.wav")
            audio = {"original": a, "revised": b, "difference": difference,
                     "timing": "equal canonical tempo, length, sections and tick positions; both bounces start at zero"}
            artifacts.update(original_preview=a["output"], preview=b["output"])
            validation["audio_verified"] = True
        render_seconds = time.perf_counter() - render_started
        if source_hashes(root) != files_before:
            raise ValidationError("source changed during revision; output discarded")
        report = {"version": "1", "action": "revise", "prompt": prepared["request"]["prompt"], "source": str(root),
                  "engine": {"planner": "rules-revision-v1" if plan is None else "validated-plan", "ai_plan": False if plan is None else None,
                             "inference_performed": False, "model": None},
                  "plan": prepared, "comparison": prepared["comparison"], "validation": {**validation, "source_files_unchanged": True},
                  "source_files_sha256": files_before, "artifacts": artifacts, "capabilities": capabilities,
                  "native_exports": exports, "native_comparison": native_comparison, "audio": audio,
                  "timing_seconds": {"planning": planning_seconds, "apply_and_replay": apply_seconds, "native": native_seconds,
                                     "render_and_compare": render_seconds, "total_before_publish": time.perf_counter()-started},
                  "supported_requests": SUPPORTED, "unsupported_requests": [],
                  "limitations": ["Finite fully matched rules grammar; unsupported clauses fail the whole request.",
                                  "Parameters are global and must already exist; automated parameter edits and FX insertion are unsupported.",
                                  "Drum thinning keeps one hit per pitch per half-bar; surviving notes/IDs/order remain exact.",
                                  "Fresh native export; no host-to-canonical reconciliation or subjective listening evaluation.",
                                  "Single writer; final directory publication is staged with cleanup, not crash-atomic across files."],
                  "artifact_sha256": source_hashes(stage)}
        _write(stage / "report.json", report)
        destination.mkdir()
        try:
            for child in stage.iterdir():
                child.rename(destination / child.name)
        except BaseException:
            shutil.rmtree(destination)
            raise
    return report


def run(args):
    plan = _read(Path(args.plan).expanduser()) if args.plan else None
    result = revise(args.source, args.prompt, args.out_dir, plan=plan, plan_only=args.plan_only,
                    expected_hash=args.expected_hash, soundcraft=args.soundcraft,
                    soundcraft_timeout=args.soundcraft_timeout, render=args.render)
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 0
