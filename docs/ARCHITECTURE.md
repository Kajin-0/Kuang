# Phase 0 architecture and exact semantics

The canonical project is the source of truth. MIDI, REAPER objects and future audio renders are derived views. A render cannot replace the structured project. All state is local; the CLI opens only paths supplied by the user and performs no network access.

```text
Human edits / model request
          ↓
ModelEngine → typed proposal + scope + expected state hash
          ↓
strict decode → scope / lock checks → candidate copy → invariant checks
          ↓                                      failure → discard candidate
atomic in-memory commit → canonical JSON + inverse receipt
          ↓
type-1 MIDI / generated REAPER Lua → native editable host objects
```

## Project version 0.1

`kuang/schema.py` is the executable schema. Dataclasses and their type annotations define every required field; JSON has no implicit defaults. Objects with missing/extra fields, duplicate JSON keys, invalid types, NaN/infinity or unsupported versions are rejected. No automatic migration is implemented. User annotations belong in the string-valued `metadata` map and survive all edits.

| Object | Canonical state |
| --- | --- |
| Project | Version, stable ID, name, constant tempo, key tonic/mode, signature, PPQ, bars, sections, registry, tracks, automation, locks, metadata |
| Section | ID, name, start, length; ordered partition of the project on bar boundaries |
| Track | ID, name, MIDI/audio/bus kind, optional instrument, controls, ordered FX/clips/sends, master output flag |
| Clip | ID, name, MIDI/audio kind, absolute start, length, notes or local source reference |
| Note | ID, clip-local start, duration, MIDI pitch/velocity/channel |
| Instrument | ID, MIDI placeholder or user plugin, plugin/preset reference, optional zero-based MIDI program, explicit parameters |
| Effect | ID, plugin/preset reference, explicit parameters; list order is signal-chain order |
| Send | ID, destination track ID, gain in dB, pan, pre/post-fader mode |
| Automation | Lane ID, target ID, parameter ID, point IDs/ticks/values/shapes |
| Lock | ID, track/clip/device target, optional parameter ID |

All object IDs, including registry entries and note/point IDs, are unique across a project. IDs match `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`. Loading and editing preserve IDs. New operations supply new IDs; duplicates fail. Seeded generation uses deterministic IDs stable across seeds.

### Time and musical data

- `ppq = 960`: one tick is 1/960 of a quarter-note beat. Version 0.1 supports 4/4 only; one bar is 3,840 ticks.
- Machine positions are zero-based integers. Display bar 1 / beat 1 is tick 0. `tick = (bar-1)*3840 + (beat-1)*960 + subbeat_ticks`.
- Clips and sections use absolute project ticks; note starts are relative to their clip. Automation points use absolute project ticks.
- Notes and clip/region/time scopes occupy half-open intervals `[start, end)`. Notes must fit fully inside their clips; clips must fit the project. Positive durations only.
- Automation points may lie at the exact project endpoint. A time-limited scope excludes its right boundary; use an unbounded time scope to edit that endpoint.
- MIDI pitch 0..127, velocity 1..127, channel **0..15** (percussion channel 9). MIDI programs are **0..127**.
- Overlapping same-pitch/channel notes on one track are rejected, including overlap across clips. Adjacent note-off/on at the same tick is valid. Other pitches can overlap for chords.
- Tempo is constant, 20..300 BPM. Key tonic is MIDI pitch class 0=C through 11=B; major/minor are supported. Key describes the project and does not forbid intentional chromatic edits.
- Audio source references are structured but are not resolved/rendered in Phase 0. Buses have no clips/instrument. MIDI tracks require an instrument configuration.

### Registry and automation

Every control and automated value must reference a registry entry with explicit unit, inclusive range, default and valid target kinds. Defaults are descriptive; absent controls are never silently materialized during an edit. MIDI instruments can remain placeholders with no synthesis parameters.

| Parameter | Unit | Range | Target |
| --- | --- | --- | --- |
| `mixer.gain_db` | dB | -90..12 | track |
| `mixer.pan` | pan | -1..1 (left..right) | track |
| `mixer.mute` | boolean | 0 or 1 | track |
| `synth.cutoff_hz` | Hz | 20..20000 | instrument |
| `synth.resonance` | normalized | 0..1 | instrument |
| `effect.wet` | normalized | 0..1 | effect |
| `effect.bypass` | boolean | 0 or 1 | effect |

The three mixer definitions are fixed by version 0.1. Additional registry entries are allowed, with validation. They do not imply a host mapping. Units also include `ms`. Plugin mapping requires explicit local bindings.

Each automated target/parameter pair has at most one lane, and the target must have an explicit base parameter. Point times are unique within a lane. `linear` or `step` describes the outgoing segment; boolean lanes require step. The intended canonical value before the first point is the base value, and after the last point is the last value. Linear segments interpolate canonical parameter values. No audio/control evaluator is shipped in this phase. Host interpolation between converted points requires validation, especially for dB and nonlinear plugin controls; point times and converted values are contract-tested.

Controls, MIDI/audio clips, effects, presets, sends, routing, automation and locks are human-editable through canonical JSON. The CLI validates on load/save. The REAPER import exposes supported fields as native controls/items/FX/envelopes. Unsupported adapter features fail explicitly rather than silently dropping them. Routing destinations must exist; feedback cycles and self-sends are rejected.

## Operations, atomicity and preservation

The public operations are `set_parameter`, `add_notes`, `update_note`, `remove_notes`, `replace_notes_in_region`, `add_automation_points`, and `delete_automation_points`. `update_note` supplies a full Note with the existing ID; it cannot rename that ID. Parameter operations require an existing explicit parameter; they do not insert arbitrary paths.

Each transaction supplies a `Scope`:

```json
{
  "track_ids": ["track-arp"],
  "clip_ids": ["clip-arp-hook-a"],
  "parameter_ids": [],
  "start": null,
  "end": null
}
```

Track IDs always form an explicit allowlist. Note edits also require the clip allowlist. Parameter/automation edits require the parameter allowlist and an owning allowed track. Empty lists grant no access in that dimension. Both optional absolute time bounds must be present or both null. Base parameter edits are global in time and fail under a time-limited scope. A note update must keep both its old and new full extent inside scope. Automation edits check old/deleted and new point times.

Track locks cover all child notes/devices/automation. Clip locks cover their notes. A device/track parameter lock blocks that parameter's base and automation edits. Operations cannot unlock targets. Human lock changes are explicit JSON edits.

Region replacement uses **clip-local** `[start,end)` and replaces fully contained intersecting notes. A note crossing either boundary causes rejection; it is never truncated silently. Replacement notes must fit the region. Surviving objects keep their order, and inserted notes append. All other object/list/metadata state is preserved. Generic move/resize-clip, routing edits and lane creation are not AI operations in Phase 0; those remain explicit human JSON edits.

The engine owns a defensive copy. Each batch runs on a separate candidate, enforcing authorization and full invariants after each operation. Any failure discards the entire batch and leaves history unchanged. A hash precondition rejects stale proposals. The CLI requires that precondition; the library also supports explicitly local edits without one. Model text, code and arbitrary JSON patch paths are never executed.

Receipts record version, complete forward operations, scope, before/after SHA-256 and generated typed inverse operations. Internal `restore_notes` / `restore_automation` inverses restore exact list ordering and IDs. Public proposal parsing rejects those internal operations. Replay checks the starting hash, reruns scope/lock/invariant checks, then requires the exact expected final hash. A fresh edit clears the in-memory redo branch. Saved receipts enable CLI undo/redo across processes. Receipts are local edit logs, not signatures or an authorization mechanism.

Canonical bytes use UTF-8, sorted JSON object keys, two-space indentation, finite normalized floating values and a final newline. Array order is preserved and contributes to hashes. Numerically identical integer/float values in floating fields produce identical canonical bytes. Hashes cover the complete project, including locks and metadata. Determinism is covered on the supported Python versions; no claim of a cross-language canonical JSON standard is made.

Saving uses a flushed/fsynced same-directory temporary file and `os.replace`. Each file replacement is atomic. Session, receipt and derived exports are separate files, not one atomic filesystem bundle. CLI apply writes the receipt first; a later I/O failure can leave a receipt without the output session. There is no cross-process writer lock or directory-fsync crash-durability guarantee; use a single writer and distinct output paths. `--force` explicitly permits replacement. Full collaborative editing and a persistent transaction database are proposed work.

## Engines and host boundary

`ModelEngine` is a Python Protocol returning `Proposal(expected_before_hash, scope, operations)`. `SeededVelocityEngine` is a working deterministic implementation. It changes only scoped note velocities and validates the proposal through the transaction engine. Future language/model engines should receive copies, emit this envelope, and pass through the same engine; downloading/running a real model is outside Phase 0.

The seeded composer separately constructs a full validated arrangement: Am–F–C–G harmony, rhythmic bass/kick relationships, backbeats, hat accents/fills, pad/chord voices, arp and lead motifs, intro/verse/hooks/break. Seed changes vary velocities; arrangement and note identities remain stable. This proves reproducible symbolic orchestration, not professional AI composition.

The MIDI writer emits type 1, a conductor track plus one track per MIDI track, tempo/signature/key/section metadata, names, optional program changes, note-on/off and end-of-track. Note-offs sort before same-tick note-ons. Audio tracks, FX, mixer state and automation are outside this MIDI export; use canonical JSON and the REAPER importer for those fields.

REAPER import is one way. Native edits remain editable in `.RPP`, but reverse reconciliation into canonical JSON is not implemented. The imported canonical manifest/hash is provenance, not a live sync mechanism. See [REAPER.md](REAPER.md) for installed-user-plugin contracts and host validation.
