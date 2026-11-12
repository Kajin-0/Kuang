# Autonomous palette selection

The private experimental workflow can now turn one prompt into an editable
16- or 32-bar house sketch: it automatically selects chord, pad and bass presets,
composes MIDI using rules, and renders a native SoundCraft session. This is not a
full-length autonomous producer or a professional-quality claim. Human listening
still decides preference. The preset-only CLI remains available separately.

## Private one-prompt native sketch

This opt-in command uses the same local catalog, reviewed installed Vitalium,
Pedalboard/NumPy/SoundFile interpreter and bubblewrap described below, plus the
pinned SoundCraft 0.11.0 CLI. Run it from the workspace root; the new output
must be inside that workspace, outside the source library, and have an existing
parent directory. Nothing is downloaded.

```bash
PYTHONPATH="$PWD/.local/phase30-experiment/packages" \
  "$PWD/.local/preset-library/.extract-venv/bin/python" \
  -m kuang.autonomous_create \
  "hypnotic deep house 126 bpm in C minor, warm chords, dark pad, punchy bass, no lead" \
  --catalog "$PWD/.local/preset-library/reports/catalog.json" \
  --plugin "$PWD/.local/phase28-tools/extracted/usr/lib/vst3/vitalium.vst3" \
  --soundcraft /home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli \
  --out-dir "$PWD/.local/autonomous-palette-eval/my-new-song" \
  --seed 17 --bars 16 --per-role 1 --max-candidates 12 --timeout 25 \
  --private-third-party-presets
```

The output includes `preview.wav`, `project.kuang.json`, `song.mid`,
`song-spec.json`, `palette/` selection evidence and `native/session.scraft`.
The **entire directory is private**: its native session and `native/patches/`
contain copied third-party preset state, not a license to redistribute it. The
native project needs the same separately installed pinned Vitalium binary and
original private source library. The adapter rechecks source hashes during
export, save and render. Archive provenance remains unverified catalog metadata.
It rejects missing or changed sources, unsupported patches and unsafe paths.

Every selected patch is checked against its source SHA and the audition receipt,
loaded into the real plugin, and independently restored with its 771 mapped
controls. Embedded waveform samples and positions, name, author and disabled
sample oscillator are checked in readback; host serialization need not be
byte-identical across different plugin instances. The SoundCraft host runs with
network disabled and only the private staging tree writable; native export is
verified against the canonical notes, effects and controls and saved/reopened.
The public original-only `external_synth` validator is unchanged and does not
accept these patches. The private adapter does not reconcile later GUI edits.

The renderer performs a quiet calibration render and bounded equal track-gain
adjustment, re-renders the native session, and rejects silence, clipping, or a
measured true peak above -1 dBTP. The measurement is not a certified mastering
or perceptual quality assessment. The output is an instrumental, rules-based
house sketch with built-in drums, not a complete full-length song; `no lead`
omits the lead track. It does not use a neural music model. More complex prompt
interpretation, sample selection, composition, arrangement and mastering remain
future work. A missing/incompatible preset, unavailable worker or host, failed
roundtrip, or failed audio gate stops publication.

## Local audition

Use a catalog with the Phase30 library layout: `reports/catalog.json` and
`presets/<source>/<relative>.vital` under the same library root. The caller must
supply an already-installed reviewed Vitalium 1.0.6 VST3, bubblewrap and a Python
interpreter with Pedalboard, NumPy and SoundFile. The core package and offline
tests remain standard-library-only. No downloads or paid services are performed.
For the existing local workspace:

```bash
mkdir -p .local/autonomous-palette-eval
PYTHONPATH="$PWD/.local/phase30-experiment/packages" \
  "$PWD/.local/preset-library/.extract-venv/bin/python" \
  -m kuang.autonomous_palette \
  "hypnotic deep house in C minor, warm chord stabs, dark soft pad, rounded bass" \
  --catalog "$PWD/.local/preset-library/reports/catalog.json" \
  --plugin "$PWD/.local/phase28-tools/extracted/usr/lib/vst3/vitalium.vst3" \
  --out-dir "$PWD/.local/autonomous-palette-eval/my-new-run" \
  --seed 17 --per-role 3 --max-candidates 12 --timeout 15
```

The output directory must be new, its parent must exist, and it must be outside
the source library. `--per-role` bounds accepted auditions per role (1–5);
`--max-candidates` bounds total worker executions (1–30); `--timeout` bounds
each worker (1–60 seconds). Structural preflights are separately bounded to
12 times `--max-candidates`, capped at 10,000. Roles are normally chord, pad and
bass; explicit phrases such as “without pad” omit a role. One explicit major or
minor key controls the audition phrases; otherwise they default to C minor.
This is a small keyword parser, not general language understanding.

`selection.json` has machine-readable role choices, library/catalog paths,
source relative paths and SHA-256 values, plugin hash, evidence and preview
hashes. `decision.json` includes attempted/preflight candidates, rejections,
features, scores, limits and plugin identity. `previews/` holds short 48 kHz,
24-bit stereo WAV auditions. An incomplete selection is still reported, with a
nonzero CLI exit code. No original preset is copied to the output, and no files
are silently overwritten.

## Eligibility, runtime and provenance

The catalog is bounded and parsed as strict JSON. Preset paths are canonical,
relative, descriptor-opened without following symlinks and confined to `presets/`.
File size and actual SHA-256 must match the catalog; selected references are
checked again after audition. Candidates must be catalogued `version_candidate`
with matching version no newer than 1.0.6, have the sample oscillator explicitly
disabled, and contain valid embedded waveform frames. Unsupported file/resource
references, missing waveforms, unsafe paths, enabled sample oscillators, malformed
JSON, oversized presets and source drift fail closed. Disabled sample state may
still be embedded in the preset, but is not played. These deliberately narrow
rules reject some otherwise usable presets.

Every audition uses a fresh subprocess with a deadline, a pinned reviewed plugin
module SHA-256 and runtime name/version check. Bubblewrap makes the filesystem
read-only except for a private scratch directory and disables network access.
The worker reconstructs a VST3 preset using the existing Vitalium container
helpers, loads it into Pedalboard, checks the name/author and disabled sample in
plugin readback, and renders a role-specific MIDI phrase. It rejects silence,
non-finite output, clipping and a gross spectral pitch mismatch. Readback checks
are not a claim of bit-identical state, exhaustive compatibility, or a security
boundary against a malicious kernel/plugin. The original-only
`kuang.external_synth` validator remains unchanged. The separate opt-in native
workflow above uses its own private source verification and does not bypass that
validator.

The proxy combines relative low/mid/high energy, envelope attack and tail, and
stereo energy against simple role-specific targets. Absolute RMS or peak is not
used as a ranking reward; those values are safety checks. Semantic rank uses
prompt/role and preset metadata, and the seed breaks shortlist ties. Ranking is
deterministic for the same metadata and measured features, but plugin rendering
can be nondeterministic. Spectral pitch matching permits harmonics and octaves;
it is not a full tuning or musical transcription test. The proxy is not a
perceptual, mastering or studio-quality score.

Source preset hashes and selected preview hashes are verified; the source archive
names and hashes in the catalog are recorded as **unverified catalog metadata**.
Neither a matching hash nor a catalog proves the source's authenticity or license.
Pedalboard and Vitalium are separate GPL-licensed dependencies, not bundled here.
Third-party preset, embedded wavetable and generated preview rights are not
audited. Keep source packs, reports and previews private, and check the actual
license before sharing or publishing anything derived from them.

## Remaining work toward one prompt to finished song

A complete autonomous producer still needs: fully audited redistribution rights
and portable asset management for foreign states; more capable prompt-driven
harmonic composition and full-length multi-section arrangement;
coherent sample and instrument role selection; calibrated gain staging, spatial
mixing and a reproducible native master; and an evaluation loop combining robust
signal/tuning checks with meaningful perceptual listening or human feedback.
It also needs explicit failure/stop conditions, source/host replay checks and
independent end-to-end prompts. None of those missing stages is implied by a
successful palette selection.
