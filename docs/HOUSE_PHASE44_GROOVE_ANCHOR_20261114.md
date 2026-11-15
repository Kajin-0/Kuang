# Kuang: Approved Phase 43–45 Low-End Groove Reference and Opt-In Experiment

**User listening feedback:** The original Phase 43–45 house demonstration is materially better than the new independent straight/jackin/minimal generators. The user finds all three new examples **mediocre, flat, and missing a physically felt low end**. This is a **musical-quality STOP** regardless of technical PCM integrity, LUFS or code test counts. The task is to improve the **general one-shot groove generator**, not manually tune one track to imitate the 45-phase demo.

## Grounded comparison, direct original project and WAV assets

Source: the user's previously approved `Kuang/.local/phase43-experiment/release/` and `phase44-experiment/release/`, including the exact editable native `project.kuang.json`, isolated licensed CC0 drum WAVs and master audio. Phase45 is a subsequent expressive variant of this mature sound and preserves key underlying groove assets. These are a **reference and validation source**, never overwritten or moved into GitHub.

| Property | Approved Phase 43–44 (C minor, 126 BPM, 118 bars) | New 16-bar generator (e.g. straight A minor, 125 BPM, seed41) |
|---|---|---|
| Drum kick source | `house.kick.punch-02`, original SHA-256 `a3a100ddcfc126bf75c282f54c3ac2a054ed09e6d0a393620a7226169b27b7f9` | `house.kick.punch-01` by current tied semantic sorting, 6–7 track premix |
| Kick mixer gain, **before global gain calibration** | **−2 dB** | **−18 dB** after new native source binding and safety staging |
| Bass gain, **before global gain calibration** | **−10.5 dB** | **−12 dB** after safety staging |
| Relative kick-bass fader difference | **+8.5 dB** | **−6 dB** |
| Kick FX | 65 Hz low-shelf +2 dB; approximately 2600 Hz presence EQ; compressor (8ms attack, 85ms release, wet .65); saturated path (drive 5/wet .36) | 0 dB low shelf; mild saturation (drive 3/wet .22); 18ms attack/95ms release dynamics, much lower kick fader |
| Bass groove | First three offbeats roughly at steps **2/6/10**, ~326/307 ticks, occasional octave step13 (~211 ticks), varied velocities around 95/90/94/80 | Sparse varying styles, typical offbeats 2/6/10/14, ~428-tick notes, velocities generally 77–87 |
| Hat feel | Staggered `-2,+10,+22,-2` tick microtiming around offbeats, realistic alternating velocities | One static offset of +12 or +20 ticks per style with narrow per-seed jitter |
| Supporting groove | Distinct clap, ghost snare, fuller shaker and bongo layering, several delays/FX buses in a **22-track** editable arrangement | Usually 6–7 tracks, lighter auxiliary percussion, relatively few accents or production buses |
| Human quality verdict | **Previously approved** producer reference | **Explicitly rejected as mediocre / weak low-end** |

**Crucial caution:** Different kick samples, nonlinear effects, sends, master dynamics, and overall gain staging make fader values **not acoustically equivalent**. The 14.5 dB *reversal of relative fader position* is a strong mechanical design clue, **not** proof that a particular fixed +14.5 dB boost is correct. Also, the two punch kick WAVs are quite similar in sample-level amplitude: source `punch-02` alone does not fix the groove.

The original Phase44 club master measures roughly −13.91 LUFS; the new generator **premix** is often −25 to −31 LUFS. Do not conflate mastered/reference loudness with percussion punch, or assume gain normalization will repair a musically flat groove. User-perceived low-end movement, rhythm and layering are the required subjective gates.

## Phase-referenced, original algorithm — opt-in only

New `--groove-impact` is a separate optional treatment under `kuang.autonomous_create --groove-template --sample-pack [audited CC0]`. Default template/source selection remains unchanged.

1. Change bass rhythm toward a reliable **offbeat 2, 6, 10** foundation, with conditional octave/pickup at sixteenth step **13**, normal note durations ~326 ticks and pickup ~211 ticks; preserve diatonic root relationships and seed/style variations. Never copy the C-minor reference's absolute pitches into other keys.
2. Shift hat offbeats to subtle **−2/+10/+22/−2 ticks** (per four-beat bar); add bounded more active shuffled percussive accents in non-minimal styles. This is informed by the user's own reference but is not automatically perceptually better.
3. On the original editable kick track, use source `house.kick.punch-02` from the audited local CC0 house-core pack for straight/deep/jackin only. **Verify this exact 2026 reference source is present** (not a renamed or imagined sample); minimal retains its intentionally short tight kick. The pack's manifest records original author, CC0 audit and source SHA; no redistributing foreign presets.
4. Increase **kick track** mixer gain by **+8 dB relative to the original generator** (not bass), add moderate 65-Hz low-shelf (+2 dB) and restrained saturation drive/wet derived from the Phase reference. The original global conservative peak-safety calibration still applies. This is an **experimental**, capped production choice, not an industry standard or calibrated preference.
5. Keep the same independently verified private Vital bass/chord source audition, section map, plugin states, MIDI export, full native SoundCraft project, source hashes, clipping/true peak gates, and optional separate preview mastering. The new mode is not the default and is **not yet approved** musically.

**Actual native test results (Nov 14, 2026):** Two new 16-bar, source-hashed and fully editable native SoundCraft experiments finished **without retries**: straight A minor/125 BPM/seed41 in **132.60 s**, selected Biow Bass 2 and minimal house dub stab 23, original premix **−27.671 LUFS / −5.619 dBTP**, zero clips; deep C minor/126 BPM/seed43 in **120.43 s**, automatically selected **WIP-D – Reese Bass** (not Biow) and SNFKFutureBounce Loaded Chords, original premix **−24.376 LUFS / −5.480 dBTP**, zero clips. Both used the exact audited Phase44 punch-02 SHA, retained the original private plugin source manifests, verified native save/reopen and identical MIDI, and left legacy examples untouched. On straight house auxiliary percussion notes increased **16→64**, kick track mixer −18→−10dB before full global calibration. This is a **structural and relative-level change only, not a producer-approved groove**.

**Important overemphasis warning:** A simple sub-band 23–129Hz average kick-window versus between-beat metric was **+1.63 dB in the approved Phase44 reference**, versus **+9.59 dB for revised straight** and **+16.83 dB for revised deep**. These are excerpts from different arrangements/mastering levels and not validated perceptual measures; nevertheless, the new output may **overemphasize kick while underrepresenting rolling offbeat bass**. Do NOT claim the new low end is better until listening confirms this.

**Approved bass-source import STOP:** The Phase44 project's original source is a private Vital `pl.zodiac`, SHA256 `9bef9326b3879c7215d00d8120a2dc513762a20161a863457a1fd3bf66070686`, but its modern catalog labels it `Keys` rather than `Bass`. An opt-in, SHA-scoped candidate audition path now permits a producer-approved Keys preset to be considered in bass role, **but its actual secure importer rejected PL Zodiac due to unsupported external wavetable resources**. A third attempted original-Cminor output therefore used the independently verified WIP-D Reese Bass fallback, **not** PL Zodiac: it must never be labeled as a Phase bass recreation. A subsequent fail-closed rule now rejects explicitly requested unimportable user-approved sources with an error rather than silently substituting another source. No resource-security validation was disabled or bypassed. The exact original Phase44 native project remains private and preserved.

**Lossless controlled listening clips prepared:** From Phase44 approved native club master bar32, revised deep Cminor bar4, and revised straight Aminor bar4, created three ~4bar 48kHz/24bit stereo WAVs with **simple amplitude-gain-only, post-measured −17.0 LUFS matched loudness**. No compression or rewritten samples in the comparison. The original Phase44 excerpt used −3.764dB scalar, new deep +7.590dB, straight +9.405dB; post true peak −5.788, −3.094, −2.381 dBTP, zero clips. Private receipt `/home/User/Kuang/.local/phase-reference-pocket-20261114/listening/listening-evidence.json`; downloadable temporary audio only, no private patch source uploaded. User listening verdict pending. Opt-in engine remains draft and **must not be enabled by default or called successful musically**.

### Hard gates and future

- **Engineering:** Native SoundCraft verifies separate MIDI/source identities, unchanged licensing, source sampler signal, no clipped samples and conservative peak safety. Same seed reproducible.
- **Comparative low-end check:** Measure the **kick-to-bass level and transient/low-band relationship**, not just total LUFS. If it does not demonstrably change, fix the source path or faders; do not claim improvement.
- **Musical:** Supply directly accessible new recorded audio **in chat** and contrast with the user's own established Phase 44 reference; user ultimately decides whether the low end is felt. An isolated spectral ratio is **not a quality score**.
- **Product:** If reference-style groove is consistently better, establish a **reusable per-style groove/palette policy** to produce that feel across *new prompts* without forcing the same Phase44 kick/bass sound for every track. Reject fixed overfitting or brittle hardcoded old preset paths.

Preserve all original phase artifacts, the current development branch's prior accepted technical results, and earlier unsuccessful tests. Do not merge this work into `main` until actual listening validation warrants it.
