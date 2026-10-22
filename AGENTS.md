# Operational context

Kuang is an audio engineering / desktop DAW project. Preserve local-first operation, reproducibility, human editability and exact edit semantics. Do not pivot to a web SaaS or waveform-only generator.

## Current implementation

- Python >=3.11; runtime standard library only. Run from this checkout with `python3 -m kuang`.
- Phase 2 `create` is prompt → strict SongSpec v1 (`song.py`) → deterministic `composer.py` → canonical/MIDI and optional verified SoundCraft/render. Preserve the separate Phase 0 generator and fixtures. SongSpec is not a canonical schema migration.
- Rules planning is heuristic and must report `ai_plan: false`. Optional `local_planner.py` uses only fixed loopback Ollama HTTP, bounded structured output, the reviewed installed Apache-2.0 `qwen3.5:4b`, and no model downloads or fallback. Reject FIRM/cloud models and `qwen2.5:3b-instruct` (research license). Keep explicit tempo/key/seed/bar constraints checked after inference.
- Ollama is an optional experiment/benchmark, not assumed primary musical intelligence. Future optional stronger Codex CLI/other-provider planning must use the same strictly validated SongSpec/typed operations; inference costs/accounts/terms stay separate and optional. Do not recursively invoke Codex from a Codex development session. Do not expand Phase 2 into a provider backend; benchmark quality before claiming superiority.
- Canonical `.kuang.json` schema version `0.1` is authoritative. See `docs/ARCHITECTURE.md` before changing timing, IDs, validation or transactions.
- `kuang/schema.py`: dataclasses, strict JSON, validation, canonical hashes, atomic file replacement.
- `kuang/transactions.py`: typed operations, scope/locks, atomic candidate apply, inverse receipts/history.
- `kuang/generator.py`, `midi.py`, `engines.py`: seeded symbolic arrangement, type-1 writer, model proposal boundary.
- `kuang/reaper.py`, `reaper_adapter.lua`: data-only import plan and native editable host objects.
- `kuang/adapters.py`: DAWAdapter Protocol. `kuang/soundcraft.py` is the primary optional SoundCraft 0.11.0 backend; `soundcraft_cli.py` exposes native bundles, explicit snapshot import, staged edits, inspection/save and WAV export. `audio.py` measures integer PCM WAVs.
- SoundCraft CLI has real headless save/reopen/render coverage. It remains an external user-installed executable: discover with `describe` and `engine.plugins`, use subprocess argv, enforce the version/build/contract pin and reject unsupported mappings. Never edit native JSON directly to synthesize host support.
- `examples/soundcraft-demo.kuang.json` explicitly selects built-ins. Preserve the original Phase 0 demo and its hashes. Native notes have no IDs and MIDI clips merge; retain canonical IDs in the bundle manifest. Import is verified snapshot recovery, never automatic reconciliation of host edits.
- No REAPER process or Vital installation was available for Phase 0. Mock/API-contract tests do not establish real host compatibility or audio quality.

## Required checks and preservation

Run `python3 -m unittest discover -s tests -v` after code changes. Exercise CLI generation, proposal, apply, undo and redo when changing those paths. Compare full canonical state after scoped edits. Keep the 20-edit regression and exact undo/redo checks meaningful.

For SoundCraft changes, also opt in to real tests with `KUANG_SOUNDCRAFT_INTEGRATION=1 KUANG_SOUNDCRAFT=/absolute/path/to/soundcraft-cli KUANG_SOUNDCRAFT_ARTIFACTS=/new/empty/directory python3 -m unittest discover -s tests -v`. No binary is downloaded by the tests. The current VPS executable is `/home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli`. Preserve prior evaluation artifacts. Require full native before/after equality outside explicit edits, save/reopen equality, exact note field checks and real WAV format/peak/RMS checks. Note counts alone are insufficient.

SoundCraft outputs are new bundles/files only; there is no overwrite flag. Stage all native edits in isolated temporary sessions, publish only verified bundles, and leave original native/canonical files unchanged. Keep unsupported operations, preset/GM limitations, automation shape restrictions and external drift errors explicit in capability reports and docs.

Update the committed `examples/demo.kuang.json` and `examples/demo.mid` deliberately if generator/schema changes require it; tests detect fixture drift. Do not silently migrate versions, regenerate IDs on load, clear automation during parameter edits, weaken locks, accept unknown operations, or discard unknown fields silently.

Preserve unrelated work. Do not force-push, commit credentials, install system packages, download large model/audio assets, use paid services, or bundle third-party plugins/presets/samples. Kuang original code is MIT; review third-party licensing before adding dependencies/assets. See `docs/LICENSING.md` for the Phase 2 provenance review and separate backend/model terms.

For `create`, test style content beyond velocities, harmonic membership, seed reproducibility, transposition, clean JSON provenance, corrupt/injected model plans, no-clobber publication and failure cleanup. Opt-in real tests include two varied prompt workflows, exact notes/FX/mixer/automation, another native save/reopen and measured non-silent unclipped audio. Keep generated files in ignored `artifacts/`, not Git. There is no GUI/listening quality claim.

Keep working features and proposed work distinct. Record actual checks, skipped checks, blockers and host limitations in `docs/STATUS.md`. Never claim rendered audio, listening tests, professional composition quality or real host verification without evidence. Runtime dependency additions and schema changes need an explicit rationale.
