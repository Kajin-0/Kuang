# Bounded native stem-calibration experiment (groove first)

Status: opt-in **mix engineering experiment**. Never automatically accepted as a better production. Source private sessions and their licensed/unknown-license assets remain on the user's VPS; no reference audio or Vital preset state is committed.

## Why

The first successful combined CC0+Vital proof in [HOUSE_REAL_SOURCES_MVP.md](HOUSE_REAL_SOURCES_MVP.md) measured about **-25.85 LUFS integrated / -10.84 dBTP**, with 0 clips and valid native SoundCraft save/reopen, but the `autonomous_create` gain strategy used approximately -15 dB for every track and then raised all tracks together by at most +9 dB. **Shared gain never changes relative instrument balance.** It may leave considerable unused headroom, and cannot repair a bass that's too strong versus the kick.

## Opt-in code: `kuang.house_mix_roles`

The experimental calibrated-mix workflow accepts an **already verified private combined template**, so it does not rerun costly preset selection and does not edit the original:

```sh
# Work within the checkout containing the new module, with its reviewed optional
# Pedalboard/NumPy dependencies. Supply your own private existing release.
python3 -m kuang.house_mix_roles \
  --source .local/kuang-groove-sample-vital-five-hat-20261113 \
  --soundcraft /path/to/reviewed/soundcraft-cli \
  --out-dir .local/new-mix-calibration-20261113 \
  --max-role-db 4 --max-output-db 6
```

It verifies the source's canonical/native identity, uses the same installed pinned Vitalium host and content-addressed CC0 drum assets, re-renders **three isolated native submixes** with unchanged instrument presets, effects, routing and MIDI, and computes RMS in the **actual named Groove section** (rather than averaging sparse Intro and Breakdown sections).

Only three roles are adjusted in v1: kick is the reference; bass and chords are measured and can receive bounded ±4 dB role-specific corrections. Every affected gain automation lane is shifted by the same offset, leaving its *envelope* intact. The drum top, clap, hat and percussion roles keep their existing faders; further calibration is intentionally postponed. A separate, measured **0 to +6 dB overall output gain** may be applied only with an actual measured true-peak margin relative to -3 dBTP. A fresh output session and 48-kHz 24-bit stereo WAV must be verified independently; anything over -1 dBTP or with clipped samples fails closed.

The first reference-relative heuristic is deliberately conservative and not derived from a published producer's secret settings:

| Role | Initial engineering reference vs isolated kick RMS | Max adjustment |
|---|---:|---:|
| Kick | 0 dB (fixed anchor) | 0 dB |
| Bass | -3 dB | ±4 dB |
| Chord stabs | -7 dB | ±4 dB |

These are starting assumptions for an **in-context experiment**, not music-industry mandatory mix standards. The evidence records each role's *residual deviation* from these heuristics and an explicit `MET`/`NOT_MET` **technical heuristic** gate at ±3 dB; passing this gate is not human approval. What passes a physical peak/clip gate need not sound balanced, and the recorded `quality_improvement_established` flag stays **false**. Layering, phase interaction, sidechain ducking and mix-bus nonlinearities mean that the sum of independently measured stem RMS values does not predict final commercial loudness.

## Safety, resource and evidence gates

- Full combined source must already exist as an independently verified private native session; do not reconstruct a third-party preset from a URL or redistribute any private patch.
- Validate source hashes and the canonical project on load; original source bytes must remain unchanged before output publication.
- Observe a **single real Groove** section and reject unsupported clock/form ranges; current song vocabulary is limited to 8/16/32 bars.
- Source MIDI, section markers, preset identities, sampler mappings, effect parameters and sends are immutable in the role-gain pass; actual kick/bass/chord onset timings are not quantized.
- Render native SoundCraft stems **one at a time**, with a hard shell execution timeout and no parallel load storms. All native host operations are pinned to the reviewed binary and network-isolated private plugin boundary. No silent fallback to mock audio.
- Keep `balance-evidence.json` with actual stem-region measurements, requested and clamped gain moves, updated project hash, global gain move, before/premix/after loudness and true-peak measurement, and `NEEDS_LISTENING` status.
- Existing Phase43/44 user-approved reference is unaffected. Full calibration output and copyrighted presets stay in ignored local workspace, not pushed to GitHub.
- Successful native rendering does **not** establish music-production quality, club master readiness, a psychoacoustic preference, or equivalence to Phase44.

## Verified private VPS run — November 13, 2026

An opt-in native run on the existing private 16-bar C-minor/deep-house, seed-17, 7-track SoundCraft/Vital/CC0 template passed the native source comparison and independently rendered updated session. Its before/after 4× FIR loudness and true-peak readings used Kuang's local optional libebur128 1.2.6. **No original Phase43/44 assets were changed.**

| Measured factor | Before | After |
|---|---:|---:|
| Integrated loudness | -25.85 LUFS | **-23.08 LUFS** |
| True peak | -10.84 dBTP | **-7.05 dBTP** |
| Clipped samples | 0 | **0** |
| Native save/reopen | passed | **passed** |

The real native solo-submix Groove-window levels were **kick -37.24 dBFS RMS**, **bass -37.91 dBFS RMS**, and **chords -31.72 dBFS RMS**. Their original relative levels were bass **-0.67 dB**, chords **+5.52 dB** versus kick. The module applied role changes bass **-2.33 dB**, chords **-4.00 dB (clamped)**, kick **0 dB**, then bounded full-output **+6.00 dB**. It independently rendered and measured the result.

**Important limitation surfaced by the evidence:** The desired *test heuristic* is chord RMS -7 dB versus kick; even after a -4 dB chord correction, the chord submix remains approximately **+1.52 dB above kick**, a residual **+8.52 dB** from that provisional criterion. Therefore the heuristic role-balance gate is **NOT MET** even though the native headroom gate passes. The next revision should use a better context-aware spectral/timing balance judgment, not simply crank the global gain or declare this professionally mixed. The resulting session and audio remain **private**, under `/home/User/Kuang/.local/kuang-groove-role-balanced-20261113`. This run precedes the explicit residual-gate addition in the code, but the raw measured levels and role corrections are recorded in its evidence.

## Limitations and next experiments

The current proof is **three grouped isolated roles**, not a mixing model trained on hundreds of accepted house productions. It does not yet handle instrument attack envelope balance, kick-bass phase/mono sum, pad and sidechain coloration, full-spectrum dynamic masking, perceptual sample ranking, vocal arrangement, or LUFS-limited mastering. The correct next step is a **loudness-matched listening comparison**, with the approved 45-iteration house master as a human sonic anchor, followed by a broader multi-seed test matrix.
