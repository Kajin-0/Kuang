"""Local project files and optional explicitly selected native DAW execution."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__
from . import midi, reaper
from .engines import SeededVelocityEngine
from .generator import generate
from .schema import ValidationError, atomic_write, decode, load, save, state_hash, strict_json
from .transactions import Engine, Scope, parse_operations, receipt_from_dict, replay
from .soundcraft_cli import add_parser as add_soundcraft_parser, run as run_soundcraft


def _json_write(path, data):
    atomic_write(path, (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"))


def _outputs(paths, force):
    resolved = [Path(p).resolve() for p in paths]
    if len(resolved) != len(set(resolved)):
        raise ValidationError("output paths must be distinct")
    if not force:
        existing = [str(p) for p in resolved if p.exists()]
        if existing:
            raise ValidationError(f"output already exists (use --force to replace): {', '.join(existing)}")


def parser():
    root = argparse.ArgumentParser(prog="kuang", description="Structured local music projects and exact edits")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    add_soundcraft_parser(commands)
    demo = commands.add_parser("demo", help="write seeded session, type-1 MIDI and REAPER importer")
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument("--out-dir", default="out")
    demo.add_argument("--force", action="store_true")
    validate = commands.add_parser("validate", help="validate and hash a session")
    validate.add_argument("session")
    for name in ("midi", "reaper"):
        command = commands.add_parser(name, help=f"export {name}")
        command.add_argument("session")
        command.add_argument("output")
        command.add_argument("--force", action="store_true")
        if name == "reaper":
            command.add_argument("--bindings", help="local installed-plugin binding JSON")
            command.add_argument("--plan", help="also write the inspectable adapter contract JSON")
    propose = commands.add_parser("propose", help="propose seeded symbolic velocity edits")
    propose.add_argument("session")
    propose.add_argument("output")
    propose.add_argument("--track", required=True)
    propose.add_argument("--clip", required=True)
    propose.add_argument("--seed", type=int, default=17)
    propose.add_argument("--start", type=int)
    propose.add_argument("--end", type=int)
    propose.add_argument("--force", action="store_true")
    apply = commands.add_parser("apply", help="validate and atomically apply a typed request")
    apply.add_argument("session")
    apply.add_argument("request")
    apply.add_argument("output")
    apply.add_argument("--receipt", required=True)
    apply.add_argument("--force", action="store_true")
    for name in ("undo", "redo"):
        command = commands.add_parser(name, help=f"{name} an exact saved receipt")
        command.add_argument("session")
        command.add_argument("receipt")
        command.add_argument("output")
        command.add_argument("--force", action="store_true")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "soundcraft":
            return run_soundcraft(args)
        if args.command == "demo":
            directory = Path(args.out_dir)
            paths = [directory / name for name in ("demo.kuang.json", "demo.mid", "import_demo.lua", "import_demo.plan.json")]
            _outputs(paths, args.force)
            project = generate(args.seed)
            # Build every representation before writing any output.
            mid, lua, plan = midi.export_bytes(project), reaper.script(project), reaper.import_plan(project)
            save(project, paths[0])
            atomic_write(paths[1], mid)
            atomic_write(paths[2], lua.encode("utf-8"))
            _json_write(paths[3], plan)
            print(f"Created {directory}: 8 tracks, 32 bars, symbolic MIDI; no audio rendered")
            print(state_hash(project))
            return 0
        project = load(args.session)
        if args.command == "validate":
            notes = sum(len(c.notes) for t in project.tracks for c in t.clips)
            print(f"Valid {project.version}: {len(project.tracks)} tracks, {notes} notes, {project.bars} bars")
            print(state_hash(project))
            return 0
        paths = [args.output]
        if args.command == "apply":
            paths.append(args.receipt)
        if args.command == "reaper" and args.plan:
            paths.append(args.plan)
        protected = []
        if args.command in ("midi", "reaper", "propose"):
            protected.append(args.session)
            if args.command == "reaper" and args.bindings:
                protected.append(args.bindings)
        elif args.command == "apply":
            protected.append(args.request)
            if Path(args.receipt).resolve() == Path(args.session).resolve():
                raise ValidationError("receipt cannot replace the source session")
        elif args.command in ("undo", "redo"):
            protected.append(args.receipt)
        if {Path(p).resolve() for p in paths} & {Path(p).resolve() for p in protected}:
            raise ValidationError("output cannot replace a source or edit log")
        _outputs(paths, args.force)
        if args.command == "midi":
            midi.export(project, args.output)
        elif args.command == "reaper":
            bindings = decode(reaper.Bindings, strict_json(Path(args.bindings).read_text(encoding="utf-8"))) if args.bindings else None
            lua, plan = reaper.script(project, bindings), reaper.import_plan(project, bindings)
            atomic_write(args.output, lua.encode("utf-8"))
            if args.plan:
                _json_write(args.plan, plan)
        elif args.command == "propose":
            scope = Scope([args.track], [args.clip], [], args.start, args.end)
            proposal = SeededVelocityEngine().propose(project, scope, seed=args.seed)
            _json_write(args.output, proposal.to_dict())
            print(f"Proposed {len(proposal.operations)} typed note edits; session unchanged")
        elif args.command == "apply":
            request = strict_json(Path(args.request).read_text(encoding="utf-8"))
            if type(request) is not dict or set(request) != {"expected_before_hash", "scope", "operations"}:
                raise ValidationError("request requires exactly expected_before_hash, scope, operations")
            expected = decode(str, request["expected_before_hash"])
            scope = decode(Scope, request["scope"])
            engine = Engine(project)
            receipt = engine.apply(parse_operations(request["operations"]), scope, expected)
            # Receipt first: a session write failure still leaves the reproducible edit log.
            _json_write(args.receipt, asdict(receipt))
            save(engine.project, args.output)
            print(f"Applied {len(receipt.operations)} operations: {receipt.before_hash} -> {receipt.after_hash}")
        elif args.command in ("undo", "redo"):
            receipt = receipt_from_dict(strict_json(Path(args.receipt).read_text(encoding="utf-8")))
            result = replay(project, receipt, undo=args.command == "undo")
            save(result, args.output)
            print(state_hash(result))
        return 0
    except (ValidationError, OSError, UnicodeError) as exc:
        print(f"kuang: {exc}", file=sys.stderr)
        return 2
