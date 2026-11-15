# Groove-first template MVP (experimental)

**Status:** feature-branch implementation proposal, *not* a professional-quality audio release. This first slice takes the product specification in [PRODUCER_READY_TEMPLATE_PRODUCT.md](PRODUCER_READY_TEMPLATE_PRODUCT.md) into an opt-in, reproducible MIDI construction path.

## CLI

```sh
python3 -m kuang create \
  "warm deep house in C minor, 126 bpm, 32 bars, without pad" \
  --out-dir artifacts/groove-deep-17 \
  --production groove-template \
  --groove-profile deep \
  --harmony-profile simple \
  --seed 17
```

**Available groove families:** `straight`, `deep`, `jackin`, `minimal`; `auto` selects an archetype from the prompt or seed. **Harmonic options:** `--harmony-profile auto|simple|extended`, with `simple` retaining three-note triads and `extended` retaining the original diatonic four-note sevenths. Auto defaults to seventh chords for `deep` and triads for other families unless the prompt explicitly requests a compatible style. The harmony profile is recorded in the groove evidence and affects chord/pad note pitch classes **without changing the kick/bass/percussion MIDI**. Explicit Phrygian, Dorian, Mixolydian, borrowed-chord and other unsupported modes fail closed; no actual ninth/sus/modal implementation is claimed. Input constraints, 8/16/32-bar sizes, 4/4 time signature and diatonic key handling inherit the bounded SongSpec rules parser. MIDI events are newly authored templates with seeded variations. No old Phase43/44 source MIDI or third-party sample assets are embedded.

The output contains `project.kuang.json`, `song.mid`, `song-spec.json`, `groove-evidence.json` and `report.json`. Native `.scraft` and an actual WAV require an explicitly chosen compatible SoundCraft binary and `--render`; without these options no audio rendering or native verification has occurred. In particular, the built-in drum-synth kick/clap/hat sounds are **not** proof of producer-ready sample selection.

The template deliberately omits lead and arp, reuses the existing SoundCraft-capable refined effects, includes a restrained additional percussion channel, maps Intro / Groove / Breakdown / Drop, and rebuilds programmed sidechain-like gain envelopes from the *new actual* kick MIDI events. It is not true external audio-triggered sidechain compression. Optional `without pad` removes pad entirely.

## Verification semantics

`groove-evidence.json` records the selected style/seed, groove onset fingerprints, role-presence checks, classic-house quarter-note kick coverage, backbeat offsets, harmonic-profile technical evidence and exact source limitations. The harmonic checks inspect intended chord pitch classes by bar, whether bass pitches serve as roots or fifths, and whether chord rhythm was preserved. They do **not** establish appealing voice leading, true modal support or musical quality. The `technical_pass` flag means **only** that the structural checks passed and canonical project validated. The sole perceptual outcome is `NEEDS_LISTENING`.

**Reusable full-song architecture:** [HOUSE_FULL_SONG_ARRANGER.md](HOUSE_FULL_SONG_ARRANGER.md) records the full 96/112/128/160-bar part-presence arranger, its automatic structural gates, multi-profile test matrix and native full-length SoundCraft verification. This is substantially more than the original short 8/16/32-bar MIDI nucleus, but it does **not** certify final artistic or mixing quality. The user is not required to listen to VPS-local internal engineering tests.

**Real-source progress:** [HOUSE_REAL_SOURCES_MVP.md](HOUSE_REAL_SOURCES_MVP.md) documents a separate opt-in CC0 drum sample binder and two native rendered candidate kits, including a separate open-hat sampler, plus an opt-in **private** combined Vital chord/bass/pad path. These are actual technical proofs, **not** validated producer-ready mixes or automatic quality selection. Sample versions and private license restrictions are documented there. The old symbolic `create` path remains unchanged.

The first strong product result will require **more than this structural engine**: context-aware sample/Vital preset audition, a measured/human-calibrated groove-selection gate, a reusable full-song (>32 bar) arrangement mapper, per-role calibrated mixing, a legitimate premaster/master, and producer usability evaluations on many prompts/seeds. Those are explicitly not implemented by this MVP.

## Compatibility and preservation

The default `--production sketch` and existing `--production refined` paths remain unchanged. The new style profile is only meaningful with `--production groove-template`. The original project schema, transaction/history engine, external adapter and historical Phase43/44 assets are not modified.

**Observed VPS integration evidence (2026-11-13):** Two fresh 8-bar C-minor/deep-house renders at seed 17, one `simple` and one `extended`, ran with the separately installed pinned SoundCraft 0.11.0 CLI. Both exported real editable `native/session.scraft`, passed canonical native save/reopen equality and non-silence/zero-clipped-sample checks, at 48 kHz / 24-bit stereo. Simple: sample peak -9.6193 dBFS, WAV SHA-256 beginning `7f4b9250c38dbaa3`. Extended: sample peak -8.6572 dBFS, WAV SHA-256 beginning `9f878607cff6c045`. The **groove fingerprint was identical** (`a2094dbdc06a24ed...`) while the final WAV differed—expected because only chord/pad voicings changed. These are technical/source checks, **not true-peak-master, perceived groove or professional-quality certification**. Outputs are kept in ignored local worktree `.local/` directories and are not published or committed.

**Acceptance sequence before merging:** (1) focused engine-free tests, (2) full GitHub CI, (3) authorized native host export/reopen/render and measured non-silent unclipped audio, (4) human-level-matched listening comparison, clearly separate from technical proof. Do not auto-promote to a professional-quality status from unit-test success.
