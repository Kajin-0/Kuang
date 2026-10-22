# SoundCraft Phase 1 backend

SoundCraft is Kuang's primary optional executable backend. The adapter is verified against the installed **SoundCraft CLI 0.11.0**, using its real native `.scraft` format, built-in instruments/FX and offline WAV bounce. No proprietary DAW, Vital, external samples, model weights, Python dependencies or system installations are needed. Kuang does not download or bundle SoundCraft. REAPER remains an optional legacy adapter with separate, unverified host integration.

The backend uses [versioned CLI commands](https://github.com/storytold/soundcraft/blob/v0.11.0/apps/soundcraft-cli/src/main.rs), discovers each supported command through `describe <id>`, and obtains actual plugin IDs, parameter IDs, units/ranges/defaults from `engine.plugins`. It never guesses VST indices. Upstream SoundCraft code is [MIT OR Apache-2.0](https://github.com/storytold/soundcraft/blob/v0.11.0/LICENSE-MIT); it remains a separate installed program. Kuang's license decision remains deferred in [LICENSE](../LICENSE).

## CLI workflow

```bash
export KUANG_SOUNDCRAFT=/absolute/path/to/soundcraft-cli
# Alternatively: kuang soundcraft --executable /absolute/path/to/soundcraft-cli ...
python3 -m kuang soundcraft capabilities examples/soundcraft-demo.kuang.json
python3 -m kuang soundcraft export examples/soundcraft-demo.kuang.json out/sc-original
python3 -m kuang soundcraft inspect out/sc-original --report out/sc-inspection.json
python3 -m kuang soundcraft apply out/sc-original examples/edit-soundcraft-mix.json out/sc-edited
python3 -m kuang soundcraft save out/sc-edited out/sc-reopened
python3 -m kuang soundcraft import out/sc-reopened out/restored.kuang.json
cmp out/sc-reopened/project.kuang.json out/restored.kuang.json
python3 -m kuang soundcraft render out/sc-reopened out/demo.wav --report out/render.json
```

`--timeout` on the `soundcraft` command defaults to 60 seconds per process and accepts >0..600. `render --end 4` renders seconds 0..4; otherwise the range is the canonical project end plus one second of tail. All commands produce JSON reports. `capabilities` can report unsupported fields without creating a project; attempted exports with those fields exit 2 and return the explicit report. `--report` writes an additional new JSON file. There is **no overwrite/force mode**. Choose new output paths for another run.

Paths are resolved/validated, command arguments are subprocess argv with JSON values (no shell), exit codes/timeouts and JSON result ordering/counts are checked, and even zero-exit stderr warnings fail the operation. Native input is restricted to self-contained built-in MIDI sessions before opening it in the backend; external plugins, samplers, media sources and video are rejected. Read-only inspection can inspect an untracked supported `.scraft`; import/apply/save/render require a verified Kuang bundle.

## Bundle and authority

An output bundle is a new directory:

| File | Purpose |
| --- | --- |
| `session.scraft` | Real, editable native session, generated/saved/reopened by SoundCraft |
| `project.kuang.json` | Exact canonical source snapshot; schema version 0.1 remains authoritative |
| `manifest.json` | Canonical/native hashes, native file SHA, exact backend executable and command-contract hashes, track/note/automation identity map |
| `inspection.json` | Complete persistent native JSON plus SoundCraft's own inspection response |
| `report.json` | Supported mappings/loss notes, counts, hashes and completed verification |
| `receipt.json` | Present on staged apply: standard Kuang forward/inverse transaction receipt |

The CLI's `session.inspect` includes note counts rather than note objects, even with `detail=full`. Kuang therefore also reads the complete **saved native JSON** and checks all note fields. Native JSON is read for inspection, never hand-written to invent backend features. The complete persisted document, including UI/unmodeled state, participates in preservation checks and hashes.

`import` means **verified snapshot recovery**: the native file, canonical snapshot, identity map, backend version/build and discovered contract must match the manifest; the native session is opened/inspected without modifying it. Only then is the original canonical project written to a new path. This preserves original IDs, clip boundaries, registry, locks, key and metadata exactly. It does not infer canonical state from arbitrary `.scraft` files. Human edits made in the host change the native hash and cause import/apply/save/render to refuse with a drift/reconciliation error. `inspect` remains available to examine that changed state. Reports and hashes are provenance checks, not cryptographic signatures or an authorization mechanism.

## Verified mappings and explicit limits

| Canonical state | Native behavior |
| --- | --- |
| MIDI tracks and notes | One imported native clip per track. Every absolute start tick, duration, pitch, velocity and zero-based channel is checked as a multiset, including later sections; MIDI note ticks remain 960 PPQ. Release velocities/controllers are checked against the generated MIDI contract. |
| Stable IDs | Native tracks have numeric IDs; native note/automation objects have no stable string IDs. Original IDs and note-to-native-index/point mappings remain in the companion manifest/snapshot. Native clip partition and per-note IDs are not independently retained by `.scraft` alone. |
| Gain/mute | dB and boolean track values set through discovered mixer commands. |
| Pan | A single Kuang pan value sets both native stereo panners, including two corresponding pan automation lanes. Values are verified; equivalence of stereo width/panning laws to other DAWs is not claimed. |
| Tempo/meter | Exact canonical constant tempo reapplied after MIDI import (MIDI microsecond tempo has rounding). 4/4 verified on save/reopen. |
| Sections | Native selection markers with names and sample positions. Native save derives the session display name from `session.scraft`; original project name/key remain in the canonical snapshot. |
| Instruments | Explicit `soundcraft:<id>` discovered self-contained built-ins; the demo uses `drum_synth` and `subtractive_synth`. MIDI placeholders with null program/preset select drums for channel-9-only tracks, synth otherwise. Existing GM program/preset timbres are rejected, not silently substituted. |
| Effects | Ordered built-in inserts (up to ten), mapped numeric parameters and bypass. The compatible example has bass `eq_7band` and pad `room_reverb`. |
| Automation | Native absolute sample points (`round(tick * 48000 * 60 / (960 * BPM))`), linear volume/pan/effect lanes and stepped mute. Nonempty lanes must start at tick 0 because the native engine holds its first point before that point. Other step shapes, instrument automation and FX bypass automation are rejected. |
| WAV | Real built-in synthesis/bounce, 48 kHz, stereo, 24-bit integer PCM, explicit range, no normalization, dither disabled; measured format/duration/peak/RMS/clipped-sample report. Rendering is checked to leave the complete native session unchanged. Silence is reported honestly and can be intentional. |

Parameters use their canonical registry definitions. `synth.cutoff_hz` maps to discovered `cutoff` in Hz; `synth.resonance` and `effect.wet` convert 0..1 into the native percent parameters `resonance`/`mix`. Additional `soundcraft.<parameter_id>` controls map by the discovered ID and compatible unit: dB→Db, Hz→Hz, ms→Ms, boolean→Toggle, normalized→Percent (×100). Values outside discovered ranges, unsupported units/IDs and preset references fail before execution. Native scalar values are float32; requested mapped values allow relative 2e-7 / absolute 1e-6 conversion tolerance. Unchanged persisted values are compared exactly.

Audio/bus/empty MIDI tracks, sends, non-master routing, external plugins/media, native preset loading, native note edits and arbitrary host reconciliation are not implemented in this slice. Canonical schema can still represent them; the backend returns explicit unsupported mappings. Locks remain enforced by canonical transactions, rather than preventing a human from editing the GUI.

The unchanged Phase 0 `examples/demo.kuang.json` contains REAPER FX and GM references and is intentionally **not** silently adapted. `examples/soundcraft-demo.kuang.json` is a separate, editable profile selecting built-ins and compatible controls. Its canonical hash is `611d19e956c21c1863bbf1a428db28073a9436f398811b1bc610dea9fb7384de`.

## Transactional apply

1. Validate bundle provenance and the complete mapped canonical/native state.
2. Apply the typed request with the existing Kuang engine, including hash precondition, scope, locks, invariants and inverse receipt. Native apply currently accepts track mixer/effect `set_parameter` and existing-lane `add_automation_points` / `delete_automation_points`. Instrument parameter and note edits require a fresh canonical export; they are explicitly rejected on native apply.
3. Copy the native source into an isolated temporary directory. Execute only mapped commands. Automation rewrites retain exact persisted values for unchanged points and preserve every other lane.
4. Verify requested values and compare the **entire** resulting native document to an independently patched copy of its prior state. Any unrequested note, FX, routing, UI, metadata or other persisted change discards the candidate.
5. Save/reopen into another isolated session and require complete native equality again. Reinspect through the real CLI, recheck all notes/controls/automation, then publish native + canonical + manifest + receipt + reports together by renaming the completed directory.

Original native/canonical files are never used as save destinations. Failed checks leave the destination absent. Existing files/nonempty directories are never replaced; a final existence check guards bundle rename, and atomic hard-link publication protects standalone WAV/JSON files from overwrites. The workflow assumes a single writer; it is not a collaborative transaction database and does not promise power-loss durability. Additional CLI `--report` files are separate publications; their I/O failure does not roll back an already published complete bundle.

Undo/redo is available through the canonical receipt engine. There is no native host undo/redo bridge yet: recover/replay canonical state through `kuang undo` / `redo` and export a new verified bundle. No hidden reverse synchronization occurs.

## Tests and actual evidence

Default tests need no SoundCraft executable:

```bash
python3 -m unittest discover -s tests -v
```

Opt in with the already installed exact backend, and use a new/empty artifact directory:

```bash
KUANG_SOUNDCRAFT_INTEGRATION=1 \
KUANG_SOUNDCRAFT=/absolute/path/to/soundcraft-cli \
KUANG_SOUNDCRAFT_ARTIFACTS=/new/empty/verification-directory \
python3 -m unittest discover -s tests -v
```

The real suite exports two distinct 32-bar sessions (seeds 7/8), saves/reopens them, restores canonical snapshots, checks all 1,083 notes per session, applies mixer/EQ/automation edits, compares all untouched native state, renders both full sessions, and asserts non-silence/format/duration/peak/RMS/no clipped samples. It also executes a rejected scoped transaction and rejects a same-note-count host velocity change without modifying that source. Unit tests inject subprocess failures, stderr warnings, malformed reports, stale hashes, locks, scope violations, collateral note/UI changes and reopen drift. CI runs these contract tests and explicitly skips the three real tests unless opted in; it does not download the binary.

See [STATUS.md](STATUS.md) for the actual run, output paths and metrics. These are headless CLI/offline audio results. No native GUI test, listening evaluation, mastering quality, general timbre fidelity, full two-way sync or professional AI music quality is claimed.
