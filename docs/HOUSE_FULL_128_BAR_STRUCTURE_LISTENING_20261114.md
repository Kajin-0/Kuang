# Kuang 128-bar native house structure listening gate — 2026-11-14

## Goal and scope

User explicitly requested to move beyond 16-bar compressed/abbreviated song demonstrations and test whether Kuang's existing arranger can produce a complete, musically convincing house track. This is an evaluation of the **general existing full-song arrangement algorithm**, not a per-song rescue, and not a new composer. Preserve the previous Groove Identity V2, source selection, pad-balance experiments and Phase44 quality anchors.

## One complete independent native production

New one-prompt test:
- Prompt: jackin house in G major, 127 BPM, energetic syncopated funky bass, confident kick, bright piano-like chord stabs, lively swung percussion, no lead, **128 bars**.
- Seed 217; 32-bar independently generated source nucleus; source selector opt-in Groove Identity V2, Musical Plan V2, audited CC0 samples, Vitalium, native context shortlist/groove-body diagnostics.
- Existing `house_full_arranger.arrange_full_song` expanded the nucleus into a real 128-bar eight-section full song, without changing the original 32-bar generated source.
- Verified native private files under `.local/full-song-jackin-G-128-20261114/`: `project.kuang.json`, `song.mid`, `native/session.scraft` and complete unmastered `preview.wav`.
- Native instrument sources: Biow Bass 2 (bass), WIP-D - Retro Piano (chords), Strings of Cygnus (pad), CC0 house.kick.punch-01; third-party preset states remain private on VPS.
- Actual musical duration **241.890 seconds (4:01.89)**, plus 12 seconds of release tail. The audio WAV is **253.890 seconds**. This is real 127-BPM playback, not speed-compressed. 48kHz/24-bit stereo, 73,120,358 bytes. WAV SHA256 begins `cf3a6b754beaa43e60`. User-visible full WAV share: https://gofile.io/d/142mKtF4 (temporary third-party host; authoritative original preserved privately).
- Full-song unmastered integrated loudness **−26.707 LUFS**, oversampled true peak **−11.559 dBTP**, zero clipped samples. Preserve as a **premix baseline**; it was not peak-maximized or mastered, and mastering was deliberately not used to conceal arrangement/mix issues.
- Native save/reopen equality passed. All **13** arranger structural gates passed, including bar partition, correct 4/4 kick during Groove A, no bass/kick during Breakdown, active return and outro, no unauthorized lead/arp, source-nucleus immutability.
- All five existing full-arranger regression tests passed prior to native execution.

## Actual 128-bar arrangement

At 127 BPM one bar lasts 1.88976378 seconds. The sections are:

| Section | Bars | Start / end | Objective role activity |
| --- | ---: | --- | --- |
| Intro | 16 | 0:00.00 – 0:30.24 | 32 kicks, 8 bass events, 24 harmony, 48 pad |
| Groove A | 24 | 0:30.24 – 1:15.59 | 96 kicks, 96 bass, 180 harmony, 0 pad |
| Groove B | 16 | 1:15.59 – 1:45.83 | 64 kicks, 64 bass, 120 harmony, 0 pad |
| Breakdown | 8 | 1:45.83 – 2:00.94 | 0 kicks, 0 bass, 24 harmony, 24 pad |
| Build | 8 | 2:00.94 – 2:16.06 | 8 kicks near end, 0 bass, 24 harmony, 24 pad |
| Main Drop | 24 | 2:16.06 – 3:01.42 | 96 kicks, 96 bass, 180 harmony, 0 pad |
| Return | 16 | 3:01.42 – 3:31.65 | 64 kicks, 64 bass, 120 harmony, 0 pad |
| Outro | 16 | 3:31.65 – 4:01.89 | 64 kicks, 32 bass, 60 harmony, 0 pad |

The current full arranger uses generated eight-bar source cells and seeded top/percussion velocity variation. It can create a complete DJ-like part-presence form, but does not yet create substantial newly composed material throughout the song; this limitation is intentional in the editable-template specification, but some phrase development is necessary.

## Structural repetition and energy assessment

An independent audit of actual native project notes counted **16 eight-bar blocks** over all 128 bars, hashing exact note onset, duration, pitch and velocity within each block:

| Musical role | Distinct eight-bar MIDI blocks | Exact block repetition fraction |
| --- | ---: | ---: |
| Kick | 3 / 16 | 81.2% |
| Bass | 3 / 16 | 81.2% |
| Harmony | 4 / 16 | 75.0% |
| Pad | 3 / 16 | 81.2% |
| Snare | 16 / 16 | 0.0% (small seeded velocity changes) |
| Hats | 16 / 16 | 0.0% (small seeded velocity changes) |
| Percussion | 9 / 16 | 43.8% |

This counts exact MIDI equality, including empty or transition sections. Distinct percussive hashes caused by minor velocity jitter **do not prove** distinct audible grooves. Most bass and harmony material genuinely repeats. The right direction is **controlled phrase-level variation and meaningful section contrast**, not arbitrary note randomization or copying another song.

Actual complete mixed native WAV section level inspection:
- Groove A p95 of 400ms RMS windows: **−27.482 dBFS**.
- Groove B: **−27.313 dBFS**.
- Main Drop: **−27.320 dBFS**.
- Intro: **−25.258 dBFS**.
- Breakdown: **−26.401 dBFS**.
- Build: **−25.539 dBFS**.

Main Drop is therefore only **+0.162 dB above Groove A** and +0.007 dB below Groove B by sustained-window p95, despite nominally being the peak section. The intro/build can be more intense by this metric than the drop. This is an **objective warning**, not a universal requirement that drops be louder: musical energy also depends on rhythm, spectral balance, dynamics and context.

## Limitations, decisions and next acceptance

- Newest short-form `--pad-level-calibration` does not support long songs. This full native render ran **without it**, preserving a readable baseline instead of globally hard-coding C's prior −12 dB pad correction. Rework pad evaluation for full-length only when justified by actual listening.
- This output was not mastered; the current −26.707 LUFS is a premix level and will be quieter than commercial streaming references. Compare at user-adjusted playback volume; do not interpret quietness as structural proof.
- No new lead, vocals or arpeggio: intentional in current product contract.
- **Do not claim professional, finished or 80% producer-ready quality** from technical validations.
- The user's listening verdict is still **pending**. Evaluate the full 4:02 WAV first, especially 0:30 Groove A, 1:16 Groove B, 1:46 Breakdown, 2:16 Main Drop, 3:02 Return and 3:32 Outro.
- The likely next arrangement milestone should improve the existing arranger's **Groove B/Main Drop distinctions and controlled 8-/16-bar phrase developments** while preserving original kick/bass pocket and editable sounds. Require fixed-prompt/seed before-after native comparison, objective transition evidence, and user listening before any default promotion.
- Keep prior short-form references, experimental failed attempts and latest native full song immutable. Do not start repeated 4-minute renders as a substitute for a decisive change.

**Status:** one complete baseline full-song production rendered, technically validated, share link verified, structural limits quantified, awaiting the user's qualitative structure assessment.
