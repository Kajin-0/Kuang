# Contextual pad selection V1 — bounded, opt-in, native source compatibility

## Mission and architectural constraint

Kuang's goal remains reliable one-prompt, high-quality, editable house tracks, not repeated manual optimization of one song. The user heard a clear improvement in the earlier C (minimal F-sharp minor) track when the lower-mid-heavy In the Dark pad was replaced with a verified Strings of Cygnus candidate while all other MIDI, kick, bass, chord and effects were locked.

This document describes a provisional role-compatibility safeguard built **inside the existing** autonomous_create, house_one_prompt_context, native SoundCraft, licensed CC0 and privately validated Vitalium pipeline. It does not replace SongSpec, house_template, the harmony interlock, house_full_arranger, or the prior successful/failed Phase44 evidence. No commercial preset state may be committed to this repository.

## Bounded experimental decision

New pure, deterministic module kuang/house_pad_context.py accepts native band_rms evidence of existing bass, original pad and alternative pad measured on the **same Groove window**. Native band RMS is measured on 48-kHz 24-bit stereo renders, using existing FFT infrastructure.

Let B120 denote bass 120–500 Hz dBFS, P120 original pad 120–500 Hz, P500 original pad 500–2000 Hz, and primed values the alternate pad.

The experiment marks a technical rescue eligible only if:
- Original pad is materially dominant in lower-midrange: P120 - B120 >= 8 dB.
- Original pad has a lower-mid-heavy tilt: P120 - P500 >= 6 dB.
- Candidate reduces relative tilt by at least 4.5 dB.
- Candidate's 500–2000 Hz RMS is no more than 7 dB below the original (not a simple blanket fader cut).
- Candidate 120–500 Hz RMS does not exceed bass by more than 4 dB.
- Candidate native full-mix render has zero clipped samples, true peak <= -1 dBTP, non-silent signal, pre-match integrated loudness within 5 LUFS of baseline, save/reopen integrity and no new destructive kick/sub compatibility faults.

These numeric values are **provisional thresholds**, not an established psychoacoustic model or universal producer mixing law. They originate from the user-approved C example with conservative margins. The rule does not compare raw band **fractions** as if they were absolute levels. Full candidate audio still needs listening.

## Integration into existing workflow

New optional private CLI switch --contextual-pad-rescue requires --contextual-shortlist. This extends house_one_prompt_context.choose_sources, which previously considered only bass and chord sources for hard-fault remediation. It does not introduce another generator or renderer.

Only one independently runtime-verified pad runner-up can be considered, and only when the first-stage role review flags possible pad low-band congestion. Original source selections and MIDI remain the default unless qualified native analysis supports a technical replacement. If the song has no pad, no verified alternative, no role review flags or another source already replaced in the same pass, the system skips pad work. C's named presets are not used in source selection logic.

An evidence receipt stores original and candidate source SHA256 hashes, measured native band RMS differences, threshold results, before/after LUFS and true peaks, source status, and the explicit statement perceptual_quality=NOT_ESTABLISHED. All private assets remain under Kuang's private .local workspace.

## Acceptance / STOP gates

- Maintain exact earlier baseline behavior with --contextual-pad-rescue disabled.
- Independently test valid/invalid thresholds, energy-only and fader-only counterexamples and missing evidence; fail closed.
- Complete fresh autonomous native C-like render with the flag, verify actual selection receipt, host save/reopen, source integrity, no clipping, and full-output audibility.
- Evaluate screening across A/B independent prompts. When their pads are not suspicious, do not substitute merely for variety.
- If the C-like native run does not qualify or deviates from original MIDI/source assumptions, keep flag experimental and investigate the failure rather than force a result.
- Even when a candidate qualifies and sounds better in the known C-style song, do not claim repeated professional-quality success without future new-prompt listening across keys/styles.
- Preserve old assets, old failed experiments, explicit user-approved improvements and rollback. Keep main unchanged until accepted.

Status: experimental; final native-run evidence appended after test completion.



## Completed fresh autonomous native test

Fresh end-to-end one-prompt C-style test with seed 29, minimal house, F-sharp minor, 122 BPM, 16 bars, Groove Identity V2, Musical Plan V2, audited CC0 drums, private runtime-verified Vitalium and SoundCraft native export/save/reopen:

- Input and experiment are independent of the old C project's native patch edits. New fresh private output: /home/User/Kuang/.local/minimal-Fsharp-autopad-rescue-20261114/. The earlier C project remains unchanged.
- The generator selected LD Bass and minimal house dub stab 23 exactly as before, and automatically changed only pad from In the Dark to Strings of Cygnus. The identical MIDI export SHA256 begins e6742007e8044b66c53cedf6 in original and new project. The progression remained [0,6,0,5].
- Native 120–500 Hz original pad vs bass advantage was +11.689 dB; original pad body minus its midrange was +9.260 dB. The verified pad runner-up reduced pad-versus-bass body to −0.359 dB; candidate body-minus-mid became +2.546 dB. The tilt reduction was 6.713 dB, preserving pad midrange at only −5.334 dB relative to the prior source.
- One separately verified candidate pad full-mix native render was checked, then the final song successfully saved/reopened and rendered. Output measured −23.748 LUFS and −5.204 dBTP, zero clipped samples. The original release measured −20.911 LUFS and −5.204 dBTP, zero clipped samples. The reduced loudness is an important caveat: improved spectral compatibility is not equivalent to automatic mastering.
- The existing source selector did NOT replace bass or chords: both candidates were skipped as technically acceptable, using exactly the existing hard-fault policy. The pad selection receipt explicitly says TECHNICAL_PAD_RESCUE, sets chosen=true, marks perceptual quality unestablished and reports no new sub-band hard compatibility faults.
- For fair subjective comparison, original and new complete ~31-second clips were matched to approximately **−20.302 LUFS** without clipping. Original measured −4.637 dBTP after gain matching; new measured −1.800 dBTP. Share: https://gofile.io/d/yI6N3bBb (external host retention not guaranteed). Private authoritative pair: /home/User/Kuang/.local/autopad-compare-listening-20261114/.

### Generalization checks and pending acceptance

The previously generated independent deep E-major and jackin B-flat major songs produced **no suspicious-pad flags**, so the new source-review stage correctly has no reason to audition or change their pads. Regression testing also establishes that missing pads, missing alternatives, clean pad review records and unsupported CLI combinations do not trigger native replacements. These checks establish safe **screening behavior**, not producer-quality acceptance across fresh music.

The fresh C-like result is a valid first automated algorithm gate, and it reproduces the user-preferred type of source substitution. It is **not yet proof that the heuristic generalizes to unrelated troublesome songs or always identifies growling timbres**. The flag remains opt-in, current default tracks unchanged; new-prompt listening and further low-end evaluation remain necessary before rollout.

