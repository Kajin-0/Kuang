"""SoundCraft subcommands. Native bundles and files are never overwritten."""

import json
import os
import tempfile
from pathlib import Path

from .schema import ValidationError, decode, dumps, load, strict_json
from .soundcraft import SoundCraftAdapter, UnsupportedError
from .transactions import Scope, parse_operations


def add_parser(commands):
    root = commands.add_parser("soundcraft", help="optional SoundCraft 0.11.0 native backend")
    root.add_argument("--executable", help="installed soundcraft-cli (or KUANG_SOUNDCRAFT / PATH)")
    root.add_argument("--timeout", type=float, default=60)
    actions = root.add_subparsers(dest="soundcraft_action", required=True)
    cap = actions.add_parser("capabilities", help="discover contracts and report unsupported project fields")
    cap.add_argument("session", nargs="?")
    export = actions.add_parser("export", help="create a verified native bundle from canonical JSON")
    export.add_argument("session")
    export.add_argument("output")
    for name in ("inspect", "import", "save", "apply", "render"):
        command = actions.add_parser(name)
        command.add_argument("source", help=".scraft file or Kuang bundle directory")
        if name == "apply":
            command.add_argument("request", help="typed Kuang edit request with scope/hash")
        if name != "inspect":
            command.add_argument("output")
        if name == "render":
            command.add_argument("--end", type=float, help="render from zero to this second; default project end +1s")
    for command in actions.choices.values():
        command.add_argument("--report", help="also write JSON to a new report path")


def create_file(path, data):
    """Atomic no-clobber file publication; staging is on the same filesystem."""
    path = Path(path).expanduser().resolve()
    if path.exists():
        raise ValidationError("output already exists; choose a new path")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".kuang-sc-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def run(args):
    report_path = Path(args.report).expanduser().resolve() if args.report else None
    if report_path:
        if report_path.exists():
            raise ValidationError("report already exists")
        if getattr(args, "output", None):
            output = Path(args.output).expanduser().resolve()
            if report_path == output or report_path.is_relative_to(output):
                raise ValidationError("report must be separate from output artifact/bundle")
    adapter = SoundCraftAdapter(args.executable, timeout=args.timeout)
    action = args.soundcraft_action
    try:
        if action == "capabilities":
            result = adapter.capabilities(load(args.session) if args.session else None)
        elif action == "export":
            result = adapter.export(load(args.session), args.output)
        elif action == "inspect":
            result = adapter.inspect(args.source)
        elif action == "import":
            project = adapter.import_project(args.source)
            create_file(args.output, dumps(project).encode("utf-8"))
            result = {"action": "import", "output": str(Path(args.output).resolve()), "restored_verified_snapshot": True}
        elif action == "save":
            result = adapter.save(args.source, args.output)
        elif action == "apply":
            request = strict_json(Path(args.request).read_text(encoding="utf-8"))
            if type(request) is not dict or set(request) != {"expected_before_hash", "scope", "operations"}:
                raise ValidationError("request requires exactly expected_before_hash, scope, operations")
            result = adapter.apply(args.source, args.output, parse_operations(request["operations"]),
                                   decode(Scope, request["scope"]), decode(str, request["expected_before_hash"]))
        else:
            result = adapter.render(args.source, args.output, end_seconds=args.end)
    except UnsupportedError as exc:
        if report_path:
            create_file(report_path, (json.dumps(exc.report, sort_keys=True, indent=2) + "\n").encode("utf-8"))
        print(json.dumps(exc.report, sort_keys=True, indent=2))
        return 2
    encoded = (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    if report_path:
        create_file(report_path, encoded)
    print(encoded.decode("utf-8"), end="")
    return 0
