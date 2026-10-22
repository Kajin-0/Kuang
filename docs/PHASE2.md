# Phase 2: local prompt production slice

`python3 -m kuang create PROMPT --out-dir NEW_DIRECTORY [--seed N] [--soundcraft PATH] [--render]`

Rules mode is the default and needs no service/network. `--model ollama --ollama-model qwen3.5:4b` explicitly enables actual local LLM planning. No paid service, model download, external plugin, sample library or proprietary DAW is required. SoundCraft is a separate optional user-installed free executable, pinned to 0.11.0 by the existing adapter. `KUANG_SOUNDCRAFT` can supply its path. Without it, the command produces symbolic canonical/MIDI output and reports that native/audio validation did not run. `--render` requires the backend. No localhost UI is included; SoundCraft supplies the human editor.

## Plan and arrangement

`song.py` defines a separate typed **SongSpec version 1**. It does not change canonical schema **0.1**, timing, IDs or transactions. Every property is required. Unknown/missing fields, duplicate JSON keys, booleans in integer fields, non-finite numbers, unsupported enums, invalid ranges and duplicate instruments fail validation.

| Field | Bounds and meaning |
| --- | --- |
| genre | `trap`, `house`, `ambient`; broad template families, not style authenticity promises |
| bpm / tonic / mode | Integer 40–200; MIDI pitch class 0=C..11=B; major or natural minor |
| mood / energy | dark/uplifting/dreamy; low/medium/high |
| seed / bars | Integer 0..2^32−1; 8, 16 or 32 bars; always 4/4 |
| arrangement | `song`: intro/main/break/finale; `evolving`: arrival/expansion/suspension/dissolve |
| progression | Four zero-based diatonic degrees 0..6; triads built from the selected scale |
| palette / space | dark/warm/bright filter/envelope recipes; dry/room/wide room-reverb recipes |
| instruments | Unique subset of kick/snare/hats/bass/harmony/arp/lead; bass and harmony required |
| automation | `fade` gain contour or `pulse` beat gain contour; linear interpolation only |

Rules parse a limited English vocabulary, explicit `140 bpm`, `A minor`/`Bb major`/`F# minor`, `8 bars`, `I-V-vi-IV` (case does not override diatonic chord quality), low/medium/high energy, dark/uplifting/dreamy moods, dry/spacious, no drums and no lead. Defaults/unsupported requests are reported. Unsupported genre descriptions select a declared trap fallback. Ambiguous tempo/key or unsupported numeric values fail. Unknown prose remains an annotation and is not promised to be musically interpreted. This is not a general language understanding claim.

| Profile | Audible symbolic decisions |
| --- | --- |
| Dark trap | Half-time snare on beat 3, syncopated kick/sub relationship, hat rolls, descending diatonic motif, sustained pad; no 808 slides |
| Uplifting house | Four quarter-note kicks, beats 2/4 clap, offbeat hats/bass/chord stabs, brighter short envelopes, arpeggio and gain pulse |
| Ambient cinematic | No default drums, slower two-bar harmony movement, sustained low notes/pad, sparse droplets and floating motif, evolving sections |

Seeds affect motifs/arpeggios and some rhythms as well as velocities. Key transposition preserves drum notes; all generated pitched notes stay within the requested scale. Mood affects melodic contour, energy affects density, palette affects cutoff and reverb damping, space affects inserts, and instrumentation/arrangement affect clip presence. Native clips merge per track; named native section markers preserve arrangement navigation. The templates are finite musical recipes, not a trained generative music/audio model.

`composer.py` creates a fresh validated canonical project with explicit built-in instruments (no GM/preset references), conservative gains, EQ, room reverb and existing supported automation. Envelope/FX registry additions use existing canonical parameter units; no schema or runtime dependency is added. SoundCraft 0.11.0's adapter cannot map choice/semitone/seconds controls through schema 0.1, so oscillator wave choices, glide/slide and reverb decay edits are not invented. Voices vary through supported filters/envelopes and notes. Gain pulses are not sidechain compression. The stored SongSpec is in `song-spec.json` and the string-valued canonical metadata; prompt and planner provenance are retained.

## Local model boundary

Ollama HTTP uses fixed `127.0.0.1:11434` via stdlib HTTPConnection, ignoring proxy/endpoint environment variables. Redirects fail. Only installed `qwen3.5:4b` is allowlisted; inventory/show checks reject remote-backed entries and require Apache license metadata. The installed model digest and Ollama version are reported. No `pull`, cloud model, shell tool, file path, URL or operation from a model is executed. License metadata identifies a local installation; it is not a cryptographic attestation of model training provenance.

`/api/generate` receives a JSON Schema in `format`, a bounded prompt, temperature 0, explicit seed, 4,096 context tokens, 768 maximum output tokens, `think: false`, `stream: false` and `keep_alive: 0` (unload after use). Explicit seed/key/BPM/bar requests constrain the grammar and are checked again after decoding. Model output is capped at 16,384 characters; HTTP JSON at 262,144 bytes; a total request deadline defaults to 120 seconds and can be set to at most 300. No repair, markdown stripping, arbitrary-field acceptance or implicit fallback is used. Stop reason and response model are checked. Errors suggest retrying or explicitly choosing rules.

LLM inference is not promised bitwise deterministic. Saved SongSpec + seed + composer version reproduces the composition; replay it through `compose()` without rerunning the model. Canonical metadata also contains the original prompt and planner/model identity. The report distinguishes actual LLM plan generation from subsequent deterministic composition and host synthesis. See [Ollama generate](https://docs.ollama.com/api/generate) and [structured output documentation](https://docs.ollama.com/capabilities/structured-outputs).

## Artifacts, publication and exactness

The command stages under a new temporary directory on the output filesystem. It writes canonical JSON, SongSpec and MIDI, then invokes the existing adapter. Export checks all mapped note fields, devices, mixer and automation; compares native state outside explicit mappings; and saves/reopens. Import checks the snapshot, native hashes, build/contract pins and identity map. `--render` renders the entire composition plus one second of tail, verifies native state unchanged, PCM format/duration, RMS >1e-6, non-silence, peak <1 and zero clipped samples. Failure discards staging. No silent normalization or invented audio metrics occur.

Only after verification does `mkdir` reserve the final path without replacing even an existing empty directory or dangling symlink. Files are moved into that owned directory; a publication error cleans that directory. This is single-writer, staged publication, not an atomic multi-file transaction or crash-durable directory database. A crash during final moves could leave an incomplete output; choose a new directory and retain reports. The original canonical/native inputs and prior evaluation artifacts are never overwritten.

`report.json` and stdout contain SongSpec, engine provenance, artifact paths, file hashes (excluding the self-referential report), capabilities, interpretation notes and validation. With rendering, the report includes actual WAV SHA-256/peak/RMS/duration/format and native-preservation status. Failures print a JSON error on stderr with exit code 2, without publishing a song directory. Native bundle reports use final paths, not temporary ones. Default output is 16 bars (about 27 seconds at 140 BPM or 53 seconds at 72 BPM, before tail).

## Human editing

Open `OUTPUT/native/session.scraft` using SoundCraft's Open session action. The imported tracks hold native MIDI sequences; use SoundCraft's clip/note editor to change notes and its mixer/inserts/automation controls to edit the mix. Save manual work under a new session name. This GUI interaction is guidance, not a recorded GUI test on the headless VPS. The WAV is only a preview; the MIDI/canonical/native session retains editable musical data.

Native manual changes do not update `project.kuang.json`. Kuang intentionally rejects importing drift against the bundle manifest; import means verified snapshot recovery. Keep manual native work separate. To retain Kuang exact undo/redo, make scoped canonical transactions and export a new native bundle for note/instrument changes. Existing native apply supports mixer/effect parameters and existing supported automation lanes. No locks are removed, automation cleared by parameter edits, IDs regenerated on load or unsupported host capability synthesized by editing native JSON.

## Verification

Run `python3 -m unittest discover -s tests -v`. Real backend tests require explicit opt-in and an installed binary, with a **new/empty** artifact directory:

```bash
KUANG_SOUNDCRAFT_INTEGRATION=1 \
KUANG_SOUNDCRAFT=/absolute/path/to/soundcraft-cli \
KUANG_SOUNDCRAFT_ARTIFACTS=/new/empty/verification-directory \
python3 -m unittest discover -s tests -v
```

The suite retains all original 77 tests and adds style/seed/transposition/harmony tests, structured local-model corruption/injection/network bounds checks, provenance/no-clobber/failure cleanup checks and two real prompt render workflows in one integration method. CI tests Python 3.11 and 3.13 with offline rules and the legacy generation/propose/apply/undo/redo smoke workflow. It downloads neither SoundCraft nor models. Actual VPS measurements, local-model result, skipped checks and limitations are recorded in [STATUS.md](STATUS.md) and [phase2-verification.json](phase2-verification.json).
