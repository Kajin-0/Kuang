# Kuang Experimental Chord-Source Gain Stability — 2026-11-14

## Goal / scope lock

Constrain the demonstrated **6.21 LU premix loudness spread** across independently prompted straight, jackin, and minimal house, **without touching MIDI, selected private Vital presets, drums, effects, timing, sample rights, source identities, or kick/bass level relationships**. Preserve a measurable A/B baseline; change one reusable algorithm, not three songs by hand.

This issue was isolated using the genuine native `kuang.house_mix_roles --diagnostics-only` runs on the existing straight-A-minor and jackin-F-minor sessions. Both have almost identical kick and bass RMS, but the native chord stems differ in level and harmonic energy.

| Native Groove RMS | Straight Am /125 | Jackin Fm /127 |
|---|---:|---:|
| Kick | −38.188 dBFS | −38.115 dBFS |
| Bass | −36.626 dBFS | −36.070 dBFS |
| Chords | −36.635 dBFS | −31.090 dBFS |
| Full premix LUFS-I | −31.304 | −25.089 |

**Cause supported:** the chosen chord presets have markedly different native amplitude and frequency response, especially in 120–2000 Hz; neither the almost identical kick/bass levels nor the **same +9 dB global calibration gain** explains the premix discrepancy. This is an engineering consistency problem. It is not evidence either chord timbre is musically wrong.

## General reusable experimental remedy

Opt-in only: `python3 -m kuang.autonomous_create ... --groove-template --chord-level-calibration`.

The new `kuang.house_role_level` compares **source-level audition RMS** from the private, independently runtime-verified `selection.json` for the selected chord vs bass. It then applies a **conservative, bounded ±3 dB** correction *to the chord track only*, before the final full-song arrangement and shared safety gain. A deadband of **−8 to −2 dB source-audition chord-vs-bass RMS** avoids touching already comparable source levels. This range is explicitly an *experimental engineering heuristic*, **not** a perceptually calibrated house target or an EQ standard.

- Bad, silent, drifted or unverified audition-source measurements fail closed.
- All original MIDI events, velocities, section times, sample-source identities, plugin states, effects, sends, native automation timepoints and kick/bass faders remain intact.
- Shift any existing chord gain-automation values by exactly the same dB, preserving rhythmic ducking instead of overriding it with fixed gain.
- All project validation and independent full-song PCM clipping/true-peak gates remain in force.
- Original default behavior does **not** enable the experiment. The change is limited to explicitly requested `--chord-level-calibration`.
- Add `chord-level-evidence.json` with source hashes, initial/target RMS ratio, capped gain, updated track-level gain and invariant checks; `report.json` records the opt-in state.
- Do not claim that reduced LUFS variation establishes better musical balance or producer readiness. The isolated Vital audition stimulus is a proxy, not an in-context perceptual evaluator.

## Paired native A/B validation

**All original and new outputs are private.** Matching prompt, style, key, sample pack, seed, plugin binary and catalog ensures source and exact MIDI identities stay fixed. The independently published before/after artifacts were audited by a separate private `audit_chord_calibration.py`. The script rejects any changed MIDI bytes, key/sections, selected preset source SHA, effects, drum-source identities, invalid 48kHz/24bit audio, or clipping. The only accepted non-chord fader difference is a possible documented shared final safety-gain offset.

| Original case | Chord audition-to-bass ratio | Trim | Original LUFS-I | Calibrated LUFS-I | Original dBTP | Calibrated dBTP |
|---|---:|---:|---:|---:|---:|---:|
| Straight Am /125 /seed41 | −7.290 dB | **0 dB** | −31.304 | **−31.304** | −13.344 | **−13.344** |
| Jackin Fm /127 /seed83 | +1.998 dB | **−3.0 dB** | −25.089 | **−27.622** | −9.203 | **−11.604** |
| Minimal Gm /122 /seed97 | −11.698 dB | **+3.0 dB** | −30.571 | **−28.477** | −11.498 | **−8.931** |

The straight-house song retained exactly the same PCM meter values because its source ratio was within the neutral deadband. The louder jackin chords were reduced while actual native/SHA/source and no-clipping gates remained intact. The minimal-house chord trim was independently measured in the third pair below. **This is level consistency, not an artistic sound-quality verdict**.

**The third positive-trim test passed**: the minimal-house G-minor composition preserved exact source MIDI, selected Vital patches, sample/drum instruments, effects and automation timing while adding 3 dB of chord-level gain. Its full-mix LUFS increased **2.094 LU**, and true peak remained safe at **−8.931 dBTP**, with zero clipped samples. The three-style original premix spread fell **6.215 LU → 3.682 LU (40.75% reduction)**. This is a cross-style loudness-consistency improvement across these exact three cases, **not** evidence of a better musical mix or validated generalization to unseen prompts. All three native before/after pairs were independently audited, with per-track and source/hash invariants passing.

## STOP/GO

- **GO** if all measured native pairs preserve MIDI, sampler and preset identities, mono/peak integrity and original default behavior; keep opt-in until more evidence exists.
- **STOP** if any case clips, source identities change, or a trim silently rewrites the user's arrangement.
- **Not yet achieved:** multi-prompt subjective assessment, guaranteed genre-wide mix balance, validated source semantic ranking, automatic diversity preference, or an actual producer-acceptable master. The existing selected bass preset remained `Biow Bass 2` across three style tests; no random source changes or unproven quality-rank heuristics have been introduced.
- Next product gate is accessible user listening using audio **provided in chat**, after a small independent producer-quality test. Do not require the user to listen to files on the VPS.

### Reproducibility

`Kuang/.local/house-portfolio-20261114/` contains the original unmodified 16-bar native SoundCraft sources, an opt-in new output per matched prompt, private bounded command logs, and `audit_chord_calibration.py` with per-prompt verification and machine-readable receipts. Private Vital/source and WAV contents are **never** committed to the public GitHub repository.
