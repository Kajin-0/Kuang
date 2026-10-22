# Operational context

Kuang is an audio engineering / desktop DAW project. Preserve local-first operation, reproducibility, human editability and exact edit semantics. Do not pivot to a web SaaS or waveform-only generator.

## Current implementation

- Python >=3.11; runtime standard library only. Run from this checkout with `python3 -m kuang`.
- Canonical `.kuang.json` schema version `0.1` is authoritative. See `docs/ARCHITECTURE.md` before changing timing, IDs, validation or transactions.
- `kuang/schema.py`: dataclasses, strict JSON, validation, canonical hashes, atomic file replacement.
- `kuang/transactions.py`: typed operations, scope/locks, atomic candidate apply, inverse receipts/history.
- `kuang/generator.py`, `midi.py`, `engines.py`: seeded symbolic arrangement, type-1 writer, model proposal boundary.
- `kuang/reaper.py`, `reaper_adapter.lua`: data-only import plan and native editable host objects.
- No REAPER process or Vital installation was available for Phase 0. Mock/API-contract tests do not establish real host compatibility or audio quality.

## Required checks and preservation

Run `python3 -m unittest discover -s tests -v` after code changes. Exercise CLI generation, proposal, apply, undo and redo when changing those paths. Compare full canonical state after scoped edits. Keep the 20-edit regression and exact undo/redo checks meaningful.

Update the committed `examples/demo.kuang.json` and `examples/demo.mid` deliberately if generator/schema changes require it; tests detect fixture drift. Do not silently migrate versions, regenerate IDs on load, clear automation during parameter edits, weaken locks, accept unknown operations, or discard unknown fields silently.

Preserve unrelated work. Do not force-push, commit credentials, install system packages, download large model/audio assets, use paid services, or bundle third-party plugins/presets/samples. Review third-party licensing before adding dependencies or choosing a repository license. The current decision is deferred in `LICENSE`.

Keep working features and proposed work distinct. Record actual checks, skipped checks, blockers and host limitations in `docs/STATUS.md`. Never claim rendered audio, listening tests, professional composition quality or real host verification without evidence. Runtime dependency additions and schema changes need an explicit rationale.
