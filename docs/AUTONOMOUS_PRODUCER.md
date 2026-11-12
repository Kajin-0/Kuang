# Autonomous palette selection

This is a **sound-selection subsystem**, not a one-shot song producer. A prompt
selects chord/keys, pad and bass candidates from a local Vital preset catalog,
auditions a bounded shortlist in the real Vitalium VST3, and chooses a candidate
for each role using an explicit signal-feature heuristic. The prompt parser and
composition facilities are rules-based; there is no neural music generation or
claim of professional sound quality. Human listening still decides preference.

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
`kuang.external_synth` validator is unchanged: this selector does **not** bind a
foreign patch into SoundCraft or bypass that validator.

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

A complete autonomous producer still needs: a safe, license-aware way to bind
selected foreign states into an editable DAW without weakening the original-only
adapter; prompt-driven harmonic composition and multi-section arrangement;
coherent sample and instrument role selection; calibrated gain staging, spatial
mixing and a reproducible native master; and an evaluation loop combining robust
signal/tuning checks with meaningful perceptual listening or human feedback.
It also needs explicit failure/stop conditions, source/host replay checks and
independent end-to-end prompts. None of those missing stages is implied by a
successful palette selection.
