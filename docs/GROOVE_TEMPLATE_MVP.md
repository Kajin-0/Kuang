# Groove-first template MVP (experimental)

**Status:** feature-branch implementation proposal, *not* a professional-quality audio release. This first slice takes the product specification in [PRODUCER_READY_TEMPLATE_PRODUCT.md](PRODUCER_READY_TEMPLATE_PRODUCT.md) into an opt-in, reproducible MIDI construction path.

## CLI

```sh
python3 -m kuang create \
  "warm deep house in C minor, 126 bpm, 32 bars, without pad" \
  --out-dir artifacts/groove-deep-17 \
  --production groove-template \
  --groove-profile deep \
  --seed 17
```

**Available groove families:** `straight`, `deep`, `jackin`, `minimal`; `auto` selects an archetype from the prompt or seed. Input constraints, 8/16/32-bar sizes, 4/4 time signature and diatonic key handling inherit the bounded SongSpec rules parser. MIDI events are newly authored templates with seeded variations. No old Phase43/44 source MIDI or third-party sample assets are embedded.

The output contains `project.kuang.json`, `song.mid`, `song-spec.json`, `groove-evidence.json` and `report.json`. Native `.scraft` and an actual WAV require an explicitly chosen compatible SoundCraft binary and `--render`; without these options no audio rendering or native verification has occurred. In particular, the built-in drum-synth kick/clap/hat sounds are **not** proof of producer-ready sample selection.

The template deliberately omits lead and arp, reuses the existing SoundCraft-capable refined effects, includes a restrained additional percussion channel, maps Intro / Groove / Breakdown / Drop, and rebuilds programmed sidechain-like gain envelopes from the *new actual* kick MIDI events. It is not true external audio-triggered sidechain compression. Optional `without pad` removes pad entirely.

## Verification semantics

`groove-evidence.json` records the selected style/seed, groove onset fingerprints, role-presence checks, classic-house quarter-note kick coverage, backbeat offsets, and exact source limitations. The `technical_pass` flag means **only** that the structural checks passed and canonical project validated. The sole perceptual outcome is `NEEDS_LISTENING`.

The first strong product result will require **more than this structural engine**: context-aware sample/Vital preset audition, a measured/human-calibrated groove-selection gate, a reusable full-song (>32 bar) arrangement mapper, per-role calibrated mixing, a legitimate premaster/master, and producer usability evaluations on many prompts/seeds. Those are explicitly not implemented by this MVP.

## Compatibility and preservation

The default `--production sketch` and existing `--production refined` paths remain unchanged. The new style profile is only meaningful with `--production groove-template`. The original project schema, transaction/history engine, external adapter and historical Phase43/44 assets are not modified.

**Acceptance sequence before merging:** (1) focused engine-free tests, (2) full GitHub CI, (3) optional authorized native host export/reopen/render and measured non-silent unclipped audio, (4) human-level-matched listening comparison, clearly separate from technical proof. Do not auto-promote to a professional-quality status from unit-test success.
