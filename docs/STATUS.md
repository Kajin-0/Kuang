# Kuang delivery status

## Phase 1 — verified SoundCraft backend

Implemented and checked on 2026-10-22, headless Linux VPS, Python 3.13.7, against the already installed SoundCraft CLI **0.11.0**. The original Phase 0 schema, generator fixtures, transaction engine and REAPER adapter remain intact. SoundCraft is now the primary optional executable backend; no proprietary DAW is required for this slice.

Working paths: `kuang/adapters.py` (DAWAdapter Protocol), `soundcraft.py` (discovery/native backend), `soundcraft_cli.py` (CLI), `audio.py` (PCM measurements), a separate built-in-instrument canonical example/edit request, recorded contract fixtures, mocked process tests and real opt-in integration tests. See [SOUNDCRAFT.md](SOUNDCRAFT.md) for exact supported mappings and command usage.

The backend discovers commands and plugin ranges, generates native sessions through the actual CLI, checks every mapped note field, creates real editable mixer/FX/automation state, verifies full native before/after preservation for supported edits, and checks a further save/reopen. It publishes new native/canonical/identity/receipt/report bundles and rejects existing outputs, unsupported mappings, stale scope/hash/locks, backend drift and unreviewed host edits. Native import restores a verified canonical snapshot; it does not infer or synchronize arbitrary host changes.

Final local verification with integration enabled: **77 tests passed, 0 failures/errors, 0 skipped**, 35.239 seconds. Breakdown: all 51 Phase 0 tests, 23 new contract/process/WAV unit tests and 3 actual SoundCraft integration tests. This includes the original 20 successive edits/full undo-redo regression. Default CI discovers the same suite, runs 74 tests and explicitly skips the three opt-in real tests; it installs/downloads no SoundCraft backend.

A separate real public-CLI smoke workflow exercised `capabilities → export → apply → save → inspect → import → render`. `cmp` confirmed restored canonical bytes equal the edited snapshot. The four-second CLI render measured -12.16 dBFS sample peak / -29.82 dBFS RMS, 48 kHz / 24-bit stereo, zero clipped samples, and no persistent native change.

The full real integration run produced two complete 32-bar sessions, each retaining **8 tracks and 1,083 notes**, with exact pitch/start/duration/velocity/channel comparisons, ID maps, native reopen, mixer/EQ/automation edits and negative drift/scope tests:

| Artifact | Duration | Sample peak | RMS | Clipped samples |
| --- | --- | --- | --- | --- |
| `demo7.wav` | 62.935479 s | -13.0089 dBFS | -31.1971 dBFS | 0 |
| `demo8.wav` | 62.935479 s | -14.0760 dBFS | -31.9971 dBFS | 0 |

Both files are non-silent, **48,000 Hz / 24-bit integer PCM / stereo**, 3,020,903 frames. Duration includes one second of render tail. These are real offline renders and sample-domain measurements, not listening, mastering or professional AI composition evaluations. No native GUI test was performed.

Persistent VPS artifacts (outside Git):

- `/home/User/kuang-eval/phase1-verification-final/verification-results.json`: full backend hashes, result reports and measured render properties.
- `/home/User/kuang-eval/phase1-verification-final/demo7/session.scraft` and `demo7.wav`: first full native session/render.
- `/home/User/kuang-eval/phase1-verification-final/demo8/session.scraft`, `demo8-saved/session.scraft` and `demo8.wav`: second seed, staged mixer/EQ/automation edit, saved clone and full render.
- `/home/User/kuang-eval/phase1-verification-final/demo8-edit-request.json`: exact typed request for the second render.
- `/home/User/kuang-eval/phase1-cli/`: separate public CLI workflow, native bundles, restored JSON, inspection and render report.
- `/tmp/kuang-phase1-final-tests.log`: local 77-test transcript (temporary log).

Measured installed executable SHA-256: `84466d199a6cb4d4924a9179fdf36b0c6d1ab3a0082b60ceed50d06f09f0b130`. Native manifests pin this executable, its discovered command/plugin contract and version. The canonical SoundCraft example hashes to `611d19e956c21c1863bbf1a428db28073a9436f398811b1bc610dea9fb7384de`; the edited second seed hashes to `c3fb4c9e0fdc60a9592818f5a8e226d4bb8dd395489370c4cfb4102308d6a714`.

Render file SHA-256 values: seed 7 `03d779a08650ee1141305899084135f54f5010a5e052627b8697f62ae215f19c`; edited seed 8 `b4cda109f1bc2babc6287bf07dec4c7ac5b03fbf309c7da682773dfe7883da8d`. These identify this run's files; general cross-build audio determinism is not claimed.

### Current limits and next milestone

No blocker remains for this verified slice. Explicit limits remain: no automatic two-way reconciliation; native notes/points lack canonical IDs and imported clips merge (the companion snapshot/map preserves identity); native apply supports mixer/effect parameters and supported existing automation lanes, while note/instrument edits need fresh export; audio/bus/sends/external media/plugins/presets and unsupported automation shapes are rejected. REAPER/Vital real host validation, native GUI testing, Kuang's own desktop UI and actual model inference are outstanding. License selection remains deferred; SoundCraft is a separate MIT/Apache-2.0 optional executable, with no new Python dependencies or redistributed backend/assets.

Next milestone: a thin local editor around the canonical project and verified adapter, plus an explicit reviewed reconciliation design for host edits. Expand native note-edit support only when exact command contracts and preservation can be verified; evaluate musical quality through actual listening and appropriate measurements rather than implying it from successful rendering.

## Phase 0 delivery record (historical)

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
