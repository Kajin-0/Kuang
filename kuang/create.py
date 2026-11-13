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
from .production import REFINED_COMPOSER, REFINED_LIMITATIONS, refine_house
from .house_harmony import select_harmony
from .house_full_arranger import parse_long_form, arrange_full_song
from .house_template import (LIMITATIONS as GROOVE_LIMITATIONS, VERSION as GROOVE_VERSION,
                             select_profile, template)
from .local_planner import LOCAL_MODEL, ollama_plan
from .schema import ValidationError, dumps, state_hash
from .song import LIMITATIONS, rules_plan
from .soundcraft import SoundCraftAdapter


def add_parser(commands):
    command = commands.add_parser("create", help="local prompt to editable song sketch; rules by default")
    command.add_argument("prompt")
    command.add_argument("--out-dir", required=True, help="new output directory, never overwritten")
    command.add_argument("--seed", type=int, default=7)
    command.add_argument("--production", choices=("sketch", "refined", "groove-template"), default="sketch",
                         help="groove-template: opt-in curated, melody-free house MIDI with structural gates")
    command.add_argument("--groove-profile", choices=("auto", "straight", "deep", "jackin", "minimal"),
                         default="auto", help="curated rhythm family for --production groove-template")
    command.add_argument("--harmony-profile", choices=("auto", "simple", "extended"),
                         default="auto", help="triads or diatonic sevenths in groove-template mode")
    command.add_argument("--full-song-bars",type=int,choices=(96,112,128,160),
                         help="optional full-length original house arrangement from 32-bar nucleus")
    command.add_argument("--model", choices=("rules", "ollama"), default="rules")
    command.add_argument("--ollama-model", default=LOCAL_MODEL)
    command.add_argument("--ollama-timeout", type=float, default=120)
    command.add_argument("--soundcraft", help="installed 0.11.0 CLI (or KUANG_SOUNDCRAFT); omit for symbolic output")
    command.add_argument("--soundcraft-timeout", type=float, default=120)
    command.add_argument("--render", action="store_true", help="render and measure full arrangement + one second tail")


def _write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def create(prompt, output, *, seed=7, model="rules", ollama_model=LOCAL_MODEL, ollama_timeout=120,
           soundcraft=None, soundcraft_timeout=120, render=False, production="sketch",
           groove_profile="auto", harmony_profile="auto", full_song_bars=None):
    raw_output = Path(output).expanduser()
    if raw_output.is_symlink():
        raise ValidationError("output already exists or is a symlink; choose a new directory")
    destination = raw_output.resolve()
    if destination.exists():
        raise ValidationError("output already exists; choose a new directory (no overwrite mode)")
    selected = soundcraft or os.environ.get("KUANG_SOUNDCRAFT")
    if render and not selected:
        raise ValidationError("--render requires --soundcraft /absolute/path/to/soundcraft-cli or KUANG_SOUNDCRAFT")
    if full_song_bars is not None and production != "groove-template":
        raise ValidationError("full-song-bars requires --production groove-template")
    import re
    planning_prompt = re.sub(r"\b(96|112|128|160)\s*bars?\b", "32 bars", prompt, flags=re.I) if production == "groove-template" else prompt
    if model == "ollama":
        if full_song_bars is not None or planning_prompt != prompt:
            raise ValidationError("full-song arrangement currently requires rules model")
        spec, messages, provenance = ollama_plan(prompt, seed, model=ollama_model, timeout=ollama_timeout)
    elif model == "rules":
        spec, messages = rules_plan(planning_prompt, seed)
        provenance = {"planner": "rules-v1", "ai_plan": False, "model": None,
                      "reproducibility": "Same prompt, seed and code version produce identical canonical bytes."}
    else:
        raise ValidationError("model must be rules or ollama")
    if harmony_profile != "auto" and production != "groove-template":
        raise ValidationError("--harmony-profile is only valid with --production groove-template")
    if groove_profile != "auto" and production != "groove-template":
        raise ValidationError("--groove-profile is only valid with --production groove-template")
    groove_receipt = None
    arrangement_receipt = None
    if production == "groove-template":
        full_length, _ = parse_long_form(prompt, full_song_bars, bpm=spec.bpm)
        if full_length:
            if model != "rules":
                raise ValidationError("full-song arrangement currently requires rules model")
            spec.bars = 32
        if spec.genre != "house":
            raise ValidationError("groove-template requires a house prompt")
        # One authoritative spec is used for composition, serialized provenance,
        # preset planning and all downstream verification.
        spec.instruments = [role for role in spec.instruments if role not in ("lead", "arp")]
        import re
        include_pad = not bool(re.search(r"\b(?:no|without)\s+(?:a\s+)?pads?\b", prompt.lower()))
        selected_groove = select_profile(prompt, seed, groove_profile)
        selected_harmony = select_harmony(prompt, selected_groove, harmony_profile)
        project, groove_receipt = template(spec, profile=selected_groove,
                                           include_pad=include_pad,
                                           harmony_profile=selected_harmony)
        if full_length:
            project, arrangement_receipt = arrange_full_song(project,bars=full_length,
                                                              profile=selected_groove,seed=seed)
    else:
        project = compose(spec)
        if production == "refined":
            project = refine_house(spec, project)
        elif production != "sketch":
            raise ValidationError("production must be sketch, refined or groove-template")
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
        if groove_receipt is not None:
            _write(stage / "groove-evidence.json", groove_receipt)
        if arrangement_receipt is not None:
            _write(stage / "arrangement-evidence.json", arrangement_receipt)
        artifacts = {"canonical": str(destination / "project.kuang.json"), "midi": str(destination / "song.mid"),
                     "song_spec": str(destination / "song-spec.json"), "report": str(destination / "report.json")}
        if groove_receipt is not None:
            artifacts["groove_evidence"] = str(destination / "groove-evidence.json")
        if arrangement_receipt is not None:
            artifacts["arrangement_evidence"] = str(destination / "arrangement-evidence.json")
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
                  "engine": {**provenance, "composer": GROOVE_VERSION if production == "groove-template" else
                              REFINED_COMPOSER if production == "refined" else COMPOSER,
                             "production": production, "composition": "deterministic musical templates, not model-generated audio"},
                  "artifacts": artifacts, "capabilities": capabilities, "validation": validation,
                  "native_export": export, "render": audio, "groove": groove_receipt,
                  "arrangement": arrangement_receipt, "actual_project_bars": project.bars,
                  "interpretation_notes": messages,
                  "limitations": GROOVE_LIMITATIONS if production == "groove-template" else
                                 REFINED_LIMITATIONS if production == "refined" else LIMITATIONS, "tracks": len(project.tracks),
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
                    soundcraft_timeout=args.soundcraft_timeout, render=args.render, production=args.production,
                    groove_profile=args.groove_profile, harmony_profile=args.harmony_profile,
                    full_song_bars=args.full_song_bars)
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 0
