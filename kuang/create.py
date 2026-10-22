"""One-command local prompt → plan → canonical/MIDI → optional native/audio."""

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path

from . import midi
from .composer import COMPOSER, compose
from .local_planner import LOCAL_MODEL, ollama_plan
from .schema import ValidationError, dumps, state_hash
from .song import LIMITATIONS, rules_plan
from .soundcraft import SoundCraftAdapter


def add_parser(commands):
    command = commands.add_parser("create", help="local prompt to editable song sketch; rules by default")
    command.add_argument("prompt")
    command.add_argument("--out-dir", required=True, help="new output directory, never overwritten")
    command.add_argument("--seed", type=int, default=7)
    command.add_argument("--model", choices=("rules", "ollama"), default="rules")
    command.add_argument("--ollama-model", default=LOCAL_MODEL)
    command.add_argument("--ollama-timeout", type=float, default=120)
    command.add_argument("--soundcraft", help="installed 0.11.0 CLI (or KUANG_SOUNDCRAFT); omit for symbolic output")
    command.add_argument("--soundcraft-timeout", type=float, default=120)
    command.add_argument("--render", action="store_true", help="render and measure full arrangement + one second tail")


def _write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def create(prompt, output, *, seed=7, model="rules", ollama_model=LOCAL_MODEL, ollama_timeout=120,
           soundcraft=None, soundcraft_timeout=120, render=False):
    raw_output = Path(output).expanduser()
    if raw_output.is_symlink():
        raise ValidationError("output already exists or is a symlink; choose a new directory")
    destination = raw_output.resolve()
    if destination.exists():
        raise ValidationError("output already exists; choose a new directory (no overwrite mode)")
    selected = soundcraft or os.environ.get("KUANG_SOUNDCRAFT")
    if render and not selected:
        raise ValidationError("--render requires --soundcraft /absolute/path/to/soundcraft-cli or KUANG_SOUNDCRAFT")
    if model == "ollama":
        spec, messages, provenance = ollama_plan(prompt, seed, model=ollama_model, timeout=ollama_timeout)
    elif model == "rules":
        spec, messages = rules_plan(prompt, seed)
        provenance = {"planner": "rules-v1", "ai_plan": False, "model": None,
                      "reproducibility": "Same prompt, seed and code version produce identical canonical bytes."}
    else:
        raise ValidationError("model must be rules or ollama")
    project = compose(spec)
    project.metadata.update({"prompt": prompt, "planner": provenance["planner"], "ai_plan": str(provenance["ai_plan"]).lower()})
    if model == "ollama":
        project.metadata.update({"model": provenance["model"], "model_digest": provenance["model_digest"]})
    adapter = SoundCraftAdapter(selected, timeout=soundcraft_timeout) if selected else None
    capabilities = adapter.capabilities(project) if adapter else {"adapter": None, "supported": None,
                         "reason": "SoundCraft not selected; canonical/MIDI only; no native or audio verification."}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".kuang-create-", dir=destination.parent) as directory:
        work = Path(directory)
        stage = work / "publish"
        stage.mkdir()
        (stage / "project.kuang.json").write_text(dumps(project), encoding="utf-8")
        (stage / "song.mid").write_bytes(midi.export_bytes(project))
        _write(stage / "song-spec.json", asdict(spec))
        artifacts = {"canonical": str(destination / "project.kuang.json"), "midi": str(destination / "song.mid"),
                     "song_spec": str(destination / "song-spec.json"), "report": str(destination / "report.json")}
        validation = {"canonical": True, "canonical_hash": state_hash(project), "native_mapped_state": False,
                      "save_reopen_equal": False, "audio_verified": False}
        export, audio = None, None
        if adapter:
            export = adapter.export(project, stage / "native")
            restored = adapter.import_project(stage / "native")
            if dumps(restored) != dumps(project):
                raise ValidationError("canonical snapshot changed during native round trip")
            validation.update(native_mapped_state=export["verified"], save_reopen_equal=export["verified"])
            artifacts["native"] = str(destination / "native/session.scraft")
            artifacts["native_manifest"] = str(destination / "native/manifest.json")
            export["output"] = str(destination / "native")
            _write(stage / "native/report.json", export)
            if render:
                audio = adapter.render(stage / "native", stage / "preview.wav")
                measured = audio["analysis"]
                if (not measured["non_silent"] or measured["rms"] <= 1e-6 or
                        measured["peak"] >= 1 or measured["clipped_samples"] != 0 or not audio["native_unchanged"]):
                    raise ValidationError("preview failed non-silence/clipping/state checks; no output published")
                audio["output"] = str(destination / "preview.wav")
                artifacts["preview"] = audio["output"]
                validation["audio_verified"] = True
        report = {"version": "1", "action": "create", "song_spec": asdict(spec), "prompt": prompt,
                  "engine": {**provenance, "composer": COMPOSER, "composition": "deterministic musical templates, not model-generated audio"},
                  "artifacts": artifacts, "capabilities": capabilities, "validation": validation,
                  "native_export": export, "render": audio, "interpretation_notes": messages,
                  "limitations": LIMITATIONS, "tracks": len(project.tracks),
                  "note_count": sum(len(c.notes) for t in project.tracks for c in t.clips),
                  "artifact_sha256": {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in sorted(stage.rglob("*")) if p.is_file()}}
        _write(stage / "report.json", report)
        # Reserve the final name with mkdir, which fails even for existing empty
        # directories or dangling symlinks. Only our owned directory is cleaned.
        destination.mkdir()
        try:
            for child in stage.iterdir():
                child.rename(destination / child.name)
        except BaseException:
            shutil.rmtree(destination)
            raise
    return report


def run(args):
    result = create(args.prompt, args.out_dir, seed=args.seed, model=args.model, ollama_model=args.ollama_model,
                    ollama_timeout=args.ollama_timeout, soundcraft=args.soundcraft,
                    soundcraft_timeout=args.soundcraft_timeout, render=args.render)
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 0
