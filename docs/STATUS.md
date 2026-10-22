# Phase 0 delivery status

Implementation and local verification: 2026-10-22, headless Linux VPS, Python 3.13.7. The GitHub repository was empty at clone time. No existing repository work was replaced. No system packages, model weights, samples, plugin binaries or paid services were installed/used. Local virtual-environment packaging checks used already installed build tools without dependency downloads.

## Working and checked

| Area | Evidence |
| --- | --- |
| Package/CLI | `python3 -m kuang`; editable installation and `kuang --version` / validation from outside checkout; standard wheel builds and includes Lua template |
| Schema | Strict nested types/fields, version rejection, IDs, deterministic JSON load/save, numeric normalization, metadata preservation, controls, audio/MIDI/bus types, routing invariants, automation and locks |
| Seeded composition | Seed 7: 32 bars, 124 BPM, A minor, 8 tracks, 1,083 notes, 5 sections; same-seed byte equality and different-seed velocity variation |
| MIDI | Type-1 file, conductor plus eight musical tracks, tempo/key/signature/section metadata, note/channel/velocity/duration equality checked by an independent parser; adjacent note-off ordering |
| Transactions | Typed operations, atomic rollback, track/clip/parameter locks, spatial/time scope, stale-hash rejection, exact inverse replay and undo/redo |
| Preservation | Full-project comparison after each of 20 successive edits, then 20 undos and 20 redos; unrelated state and IDs retained |
| Engine boundary | Seeded velocity engine produces typed proposals and passes through the same validator; no actual model inference |
| REAPER adapter | Inspectable contract plus generated self-contained Lua; native note/FX/mixer/automation/routing API calls executed against a mock with the VPS's existing Lua 5.3 shared library |
| Failure handling | Invalid batches leave state/history unchanged; stale/tampered receipts fail; missing plugins/presets/renamed controls request host undo; derived exports cannot overwrite canonical sources |

Final local suite: `python3 -m unittest discover -s tests -v` — **51 tests passed, 0 failures/errors, 0 skipped**, 19.929 seconds. This includes six test methods that execute generated Lua against a mock API. The optional Lua ABI harness uses an existing Lua 5.3/5.4 shared library; on machines without one, those methods report skips while Python adapter contract tests still run. No library is downloaded by tests.

A separate shell-level smoke test generated files, proposed 64 scoped arp velocity edits, applied the proposal, saved its receipt, undid it and redid it. `cmp` confirmed byte equality of original/restored and edited/redone sessions. Documentation links and staged whitespace are checked before commit. GitHub Actions is configured for Python 3.11 and 3.13 on Ubuntu 24.04, with the unit suite and the same CLI workflow; remote results must be read from Actions rather than inferred from the local run.

Committed fixtures:

- [demo.kuang.json](../examples/demo.kuang.json): canonical seed-7 session, state/file SHA-256 `ad69af4e634f7e5d7ac6e0a0e05963c3373e9fd52f0e5fde0249ca07831d234c`.
- [demo.mid](../examples/demo.mid): deterministic symbolic type-1 MIDI, 10,664 bytes.
- [edit-arp-pan.json](../examples/edit-arp-pan.json): one validated parameter-edit request against that exact session hash.
- [vital-bindings.example.json](../examples/vital-bindings.example.json): a local configuration template with explicit placeholders, not an installed or tested Vital preset.

The smoke-test edited state hash was `9c30c361abf30f664e462de5c0e41016017d271a71714fc2dcef6e9b64e7a330` for seed-17 velocity variation in `clip-arp-hook-a`.

## Blockers and limits

1. **Real REAPER/Vital execution is unavailable on this VPS.** Native API/track-chunk behavior, host rollback, envelope interpolation, save/reopen behavior and plugin sound must be checked in a real host. The Lua mock proves the adapter's call/data contract, not host integration. [REAPER.md](REAPER.md) contains concrete human validation steps.
2. **Repository license selection is deferred.** No third-party assets are bundled. The maintainer still needs the dependency/asset review recorded in [LICENSE](../LICENSE) before choosing distribution terms. This does not block the implemented development slice.
3. **No audio engine, rendered master or quality evaluation exists.** MIDI placeholders need user instruments. Plugin references/calibration do not freeze external plugin versions or preset state. No professional AI composition claim is made.
4. **Desktop UI, audio import/render, tempo maps, actual model inference, host-to-canonical reconciliation and collaborative/multi-process editing remain proposed.** Save operations are atomic per file; a receipt/session/export bundle is not one filesystem transaction. The current workflow assumes a single writer.

## Next milestone

Validate the generated importer in a real REAPER project with an already installed Vital instance: check notes/mixer/envelope values, measured macro calibration, failure rollback, save/reopen and native editability. Record host/plugin versions and discrepancies. Then implement a thin local desktop project editor and host reconciliation around these existing exact edit semantics. Add an actual model engine only through validated proposals; make audio-quality and rendering claims only after real output and listening/measurement evidence exist.
