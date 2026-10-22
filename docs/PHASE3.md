# Phase 3: exact local revision and A/B audition

The CLI revises an existing song instead of regenerating it. Core runtime remains Python 3.11+ standard library only, canonical schema **0.1**, existing public typed operations and the optional external SoundCraft **0.11.0** executable. No new model, provider, UI framework or audio engine is installed or required. The MIT license and Phase 0/1/2 functionality remain intact.

## One-command workflow

```bash
python3 -m kuang revise artifacts/phase2-trap-final \
  "make the bass more aggressive, simplify the drums in Main, keep everything else unchanged" \
  --out-dir out/trap-revised \
  --soundcraft /home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli \
  --render
```

The absolute binary path above is the already installed VPS executable; elsewhere supply your installed 0.11.0 path. `KUANG_SOUNDCRAFT` is also supported. The source can be a Phase 2 `create` directory, a prior `revise` directory, or a verified SoundCraft bundle with `project.kuang.json` at its root. Canonical-only directories also work. Existing outputs (even empty directories or dangling symlinks), outputs inside the source, drifted sources and incomplete/unsupported native mappings fail. No overwrite option is provided.

`--render` exports a fresh native result, renders fresh **original.wav** and **preview.wav**, measures both and checks an aligned PCM difference. Existing source previews are neither trusted as the A/B baseline nor modified. Even if the source has no WAV, both previews are produced in the new output. Listen in any WAV player, or open `native/session.scraft` in SoundCraft to edit/audition native notes, synth parameters, FX, mixer and automation. `original-native/session.scraft` is the baseline companion. No SoundCraft GUI or human listening test was performed on the headless VPS.

Continue by passing the revised directory to another `revise` command. Omit `--soundcraft`/`--render` and unset `KUANG_SOUNDCRAFT` for canonical/MIDI-only editing; reports explicitly mark native/audio as unverified. Static native hashes/snapshot agreement are still checked when a bundle is present. With a backend, its original executable/contract pin, canonical mapping and host inspection are also verified. Manually changed native state is not automatically reconciled.

## Supported prose, exact intent and limitations

The rules planner is a finite grammar, not general language understanding. Each complete clause must match; one unsupported clause rejects the whole compound request. It accepts case variation, optional `the`/`please`, a final period, commas, semicolons, `and` and `then`. No substring-based partial success occurs. Paths, commands and unknown instructions from prose are never executed.

| Intent | Example | Exact operation |
| --- | --- | --- |
| Bass aggression | `make the bass more aggressive` | Existing `synth.cutoff_hz` ×4 up to 8 kHz and resonance +0.2 up to 0.65; never reduces an already higher setting |
| Regional drum simplification | `simplify the drums in Main` / `simplify hats in bars 5-8` | For each percussion track/pitch/half-bar, retain one hit, preferring a quarter-note onset then earliest onset/ID; remove remaining fully contained notes |
| Existing reverb | `make the lead reverb wetter` / `make the harmony reverb drier` | Add/subtract 0.12 normalized wet amount, clamped to 0..1; exactly one existing reverb required |
| Mixer gain | `turn the lead down by 3 dB` / `turn the bass up by 2 dB` | Explicit nonzero delta up to ±6 dB, within the existing registry's final range |
| Preservation | `keep the lead unchanged` / `keep everything else unchanged` | Explicit target conflicts reject the request; every non-authorized field is always preserved |

Parameter changes are global. Existing nonempty automation on that exact target/parameter overrides a base value, so such edits are rejected rather than clearing or rewriting automation. For example Phase 2 harmony gain is automated: `turn harmony up by 2 dB` fails precisely. Parameter/FX creation, new effect chains, arbitrary synthesis controls, pitch slides, tempo/key changes, arrangement resizing, vocal generation and unrestricted musical instructions are unsupported. Saturated controls and already thin/no-note regions fail as no-op requests. A bypassed/muted/otherwise inaudible edit can fail the render difference gate; a signal-change check does not establish subjective audibility.

Track selection uses exact IDs/names or unambiguous semantic labels (`bass`, `kick`, `snare`, `hats`, `pad`, `harmony`, `chords`, `arp`, `lead`). `drums` resolves nonempty MIDI tracks containing exclusively channel-9 notes. Generated stable IDs take priority for their role. Ambiguity fails with available targets. Named sections must exist: Phase 2 has **Intro, Main, Break, Finale**, not Verse. Ambient uses **Arrival, Expansion, Suspension, Dissolve**; it has no default drum track. Phase 0's actual Verse is supported for drum edits, but its MIDI placeholders lack explicit bass controls/compatible GM-free native mappings; unsupported bass/native requests are rejected.

Regions use zero-based integer ticks and half-open `[start,end)` bounds. Human `bars 5-8` is inclusive and compiles to `[4*3840,8*3840)`. A single `bar 5` is supported. Bounds must be whole bars within the project; no numeric clamping or missing-section alias is used. A note intersecting and crossing either region boundary causes rejection, never truncation. Surviving notes retain all fields, IDs and relative list order, including within changed clips. Canonical clips and sections retain identity, length and position.

## Plan review and exact replay

```bash
python3 -m kuang revise artifacts/phase2-trap-final \
  "make the bass more aggressive, simplify drums in Main" --plan-only > /tmp/trap-plan.json
python3 -m kuang revise artifacts/phase2-trap-final --plan /tmp/trap-plan.json \
  --out-dir out/trap-reviewed \
  --soundcraft /absolute/path/to/soundcraft-cli --render
```

`--plan-only` prints a **revision-plan-1** JSON document and writes no project, directory or host state. It validates on private copies, so locks and invalid late intents fail at review too. The plan includes typed intents, current hash, per-step scopes/operations and hashes, expected final hash, exact parameter before/after values, removed note IDs/fields/absolute timing, surviving-note identity hash and unchanged-state hashes. Default one-command execution records this same plan in staging before candidate application and host work; user authorization does not require an extra confirmation prompt.

`--plan` accepts the reviewed file instead of prose. It strictly decodes the **RevisionRequest/ChangeIntent** fields, recompiles operations/scopes from existing objects, reruns the transactions and compares the entire regenerated plan. Unknown fields, unsupported intent types, numeric/type/range errors, changed scopes/operations/comparison and stale source hashes fail. An optional `--expected-hash SHA256` supplies an additional source precondition. Plans and receipts are unsigned local files: editing all structured intent data coherently creates a new request, not an authenticated authorization record.

Each intent retains its own scope. A global bass parameter edit and regional drum edit never become a single unbounded union scope. The unchanged transaction engine applies them sequentially to a private candidate. No source or published output changes until the complete batch, preservation, replay, host and optional audio checks pass. A later failure discards all earlier tentative edits.

`revision-receipt.json` is a strict **revision-1** wrapper around a hash-linked list of ordinary **0.1** receipts; the originals are also in `receipts/01.json`, etc. Existing CLI undo/redo accepts the wrapper and replays every receipt with its original scope/locks/hash checks:

```bash
python3 -m kuang undo out/trap-reviewed/project.kuang.json \
  out/trap-reviewed/revision-receipt.json out/trap-undone.kuang.json
python3 -m kuang redo out/trap-undone.kuang.json \
  out/trap-reviewed/revision-receipt.json out/trap-redone.kuang.json
```

This replays canonical state exactly, including ordering and metadata. It does not alter a native session in place. To audition an undo/redo, export the resulting canonical file through the existing SoundCraft export/render commands into new paths. Replay rejects stale/tampered state, broken chains, changed scopes and violated locks.

## Artifacts and preservation

| New output | Meaning |
| --- | --- |
| `change-plan.json` | Reviewable validated request, scopes, operations and expected comparison |
| `project.kuang.json`, `song.mid` | Revised authoritative state and editable symbolic MIDI |
| `original.kuang.json` | Exact incoming canonical file bytes |
| `revision-receipt.json`, `receipts/` | Compound exact undo/redo chain and ordinary scoped receipts |
| `source-report.json`, `song-spec.json` when present | Immediate incoming report and original composition plan, copied without rewriting |
| `provenance/` | Content-addressed copies of incoming and ancestor JSON reports, retained across iterations without rewriting/deduplicating away content |
| `original-native/`, `native/` with backend | Verified original baseline clone/export and fresh revised native bundle, including snapshots/maps/reports |
| `original.wav`, `preview.wav` with render | Fresh full-length A/B bounces plus one-second tail |
| `report.json` and stdout | Provenance, capabilities, changed IDs/values, preservation/source hashes, native comparison, audio measurements/delta and actual timings |

All original canonical metadata, SongSpec, planner/model identifiers, locks, automation, unknown annotations and unrelated fields stay exact. The copied SongSpec describes the original composition; it is historical provenance after edits, not a regenerated recipe for the revised controls/notes. Revision provenance goes in sidecars. A subsequent revision copies its immediate source report, carries all existing archived reports forward and retains the unchanged canonical original provenance. Reports are stored by SHA-256 of their exact bytes; equal content is stored once. Prior directories remain untouched as the complete edit history, and moving the new directory does not lose ancestor report/model provenance. No model call or regenerated project is disguised as an edit.

An independent comparison reconstructs the allowed scalar replacements and note removals, then requires full canonical equality. A second comparison projects out exactly those intended changes and requires identical before/after hashes. This covers metadata, all untouched tracks, other fields on edited tracks, all surviving notes, list ordering, routing, locks, sections and automation. Original source inventory is streamed before and after work (up to 512 regular files / 1 GiB, no contained symlinks); any concurrent change aborts publication without overwriting the external change.

For native output, the original bundle is cloned/save-reopened, or a canonical-only source is freshly exported. The revised project always uses **fresh export**: instrument/note edits do not exceed the native in-place apply contract. Both mapped states are verified by the adapter. `compare_revision` independently replays the scoped receipts and compares the entire persistent native object after allowing only the mapped scalar values and exact note removals. Host f32 tolerance applies only to explicitly edited scalar paths. Every untouched native field must match exactly; unsupported/unmapped source state or derived bounds that cannot be preserved cause failure. Another save/reopen comparison is part of export and the real tests.

`--render` bounces both verified sessions from zero with the same canonical tempo, length and sections. Each WAV must be non-silent with RMS >1e-6, peak <1, zero clipped samples, expected duration and 48 kHz/24-bit stereo PCM. `compare_wavs` requires equal formats/frame counts and measures changed samples, delta peak/RMS/dBFS and delta-to-original RMS ratio. It uses **sample-zero alignment**, with no offset guessing, resampling, time warping or gain normalization. Publication requires delta RMS >1e-5 and >1% of the original RMS, preventing identical or rounding-only “audio differences.” Exact hashes identify both bounces. These are objective signal measurements, not a human listening or composition-quality assessment.

Source validation, new files, host work and audio are staged in an isolated temporary directory. Only after verification does `mkdir` reserve a new final path, refusing races even with empty directories/symlinks. Failed moves clean only that owned directory. This is single-writer publication with failure cleanup, not a multi-file crash-atomic database or protection against a writer changing source files after the final check. Source files are never edited to synthesize host support.

## Provider independence and verification

`RevisionPlanner.propose(Project, prompt) -> RevisionRequest` is the future provider boundary. `ChangeIntent` is an allowlisted semantic object with explicit tracks, region and amount. The compiler alone derives public typed operations and narrow scopes; future Codex/BYO model output must pass this same strict decoder/compiler/transaction/preservation path. Song creation continues through SongSpec. No Codex or other provider backend was added, no recursive Codex invocation occurred, no paid inference ran, and no model weights were downloaded. Ollama remains an optional Phase 2 experiment; rules revision does not call it. Provider cost/licensing and future A/B model-quality benchmarking remain separate proposed work, not a core dependency.

Run `python3 -m unittest discover -s tests -v`. To execute all real host tests, use the existing opt-in contract with a **new/empty** artifact directory:

```bash
KUANG_SOUNDCRAFT_INTEGRATION=1 \
KUANG_SOUNDCRAFT=/absolute/path/to/soundcraft-cli \
KUANG_SOUNDCRAFT_ARTIFACTS=/new/empty/verification-directory \
python3 -m unittest discover -s tests -v
```

Tests retain the original 100 and add fully scoped compounds, exact canonical comparison, IDs/order/region boundaries, corruption/stale hashes/locks, strict prose/plans, source drift, iterative edits, publication/race/failure cleanup, measured PCM math and real native A/B revisions. CI uses Python 3.11/3.13, offline rules and exact compound CLI replay without downloading a backend/model. See [STATUS.md](STATUS.md) and [phase3-verification.json](phase3-verification.json) for actual counts, hashes, measurements, artifact paths and skipped checks.
