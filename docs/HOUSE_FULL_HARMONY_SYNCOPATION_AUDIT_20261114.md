# Kuang full-song harmony syncopation audit and controlled correction (November 14, 2026)

## User observation and scope

After hearing the generated 128-bar, 127 BPM G-major jackin-house track, the user judged the complete production "pretty good" but reported that the **background chords' syncopation sounded strange and did not quite match**. This deserves diagnosis of the actual score and processing, not another overhaul of the composition or hand-adjusted preset mix. The original full native project, audio, MIDI, audited CC0 drum samples, third-party private Vital states and earlier section baseline must remain immutable.

Original native output: private `.local/full-song-jackin-G-128-20261114/`. Earlier full-song report: `docs/HOUSE_FULL_128_BAR_STRUCTURE_LISTENING_20261114.md`.

## Confirmed root cause #1 — contradictory full-arranger chord duck automation

The **short-form groove-impact source** explicitly marks its ducking policy as:
- Bass −3 dB at kick onset, recover over 115 ms.
- Pad −1.25 dB at kick onset, recover over 143 ms.
- **Dry/background harmony 0 dB at kick onset.**

This was an intentional correction from earlier Phase44 groove listening: foreground chord transients should not be repeatedly pumped by the kick.

**Defect in `kuang/house_full_arranger._build_lanes`:** When expanding 32-bar groove cells to 128 bars, it unconditionally deletes the source duck automation and re-creates **−5 dB kick-aligned ducking on bass, harmony and pad**, with fixed 100/420-tick intermediate recovery. Thus the long-form arranger silently overrides the source's explicit `harmony-dry-0db` metadata. The saved 128-bar native project indeed had a `production-harmony-duck` automation lane with **1,699 points**, repeatedly dipping chord gain by −5 dB on actual kick notes. At 127 BPM, 420 ticks corresponds to ~206.7 ms. This changes chord-groove emphasis despite identical chord MIDI, and makes the song sound more unnecessarily pumped than the user-approved short groove.

**Implemented correction:** `house_full_arranger._build_lanes` now detects source metadata `groove_impact_pocket=source-preserving-impact-v2` and calls the existing, thoroughly used `house_template._reschedule_impact_duck` against **the expanded long-form kick MIDI**. It removes the unintended harmony duck entirely, and uses only the existing approved bass/pad depth/recovery. Legacy non-impact long songs retain their original −5 dB lanes unchanged. No new parameter tuning or another arranger was introduced. Regressions explicitly test both source policies, note preservation and structural validity.

## Root cause #2 — unstable chord rhythmic vocabulary (not yet changed)

The actual generated 128-bar song uses only **two** bass rhythm variants in 24 bars of Groove A: bass note starts at 16th-grid steps (2,5,9,13) or (2,6,9,14). The background-chord interlock selects from **five distinct** 2- or 3-stab note-attack patterns in the same passage:

- 2-stab: (1,12) or (3,14).
- 3-stab: (1,7,14), (3,8,13), or (1,5,12).

Across 24 bars of Groove A, the exact chord stab-position set changes in **23 of 23 adjacent bar transitions**; this is partly intentional alternation between two- and three-attack bars, but its internal anchor choices also rotate independently of the more stable bass and drum grid. No chord attack was within 40 ms of a bass attack in the audit: exact simultaneous bass/chord onset collision is **not** the obvious issue. Instead, a frequently changing syncopated figure can sound inconsistent with a bass groove that repeats in 4-bar phrases.

Chord MIDI notes have a 300-tick (~147.6 ms) gate; the selected real Vital chord preset WIP-D - Retro Piano is processed with chorus (18% wet) and plate reverb (10% wet, 1050 ms decay) in the native arrangement. Reverb tails and transient ducking can further obscure where each stab belongs. Audio/timbre evidence is not enough to assert whether the source preset's intrinsic attack causes this mismatch; the two objective score/automation faults warrant controlled evaluation.

**Not yet modified:** The harmony interlock's pattern selection or the chord preset's attack/reverb. Doing both simultaneously with the duck fix would conceal which correction helped. A later opt-in four-bar phrase-stable chord-pattern policy is reasonable, but should be evaluated separately against the **same** MIDI/harmony voicings and listener feedback.

## Controlled experiment design

Render exactly one corrected copy of the original 128-bar native project, changing **only** the three recognized duck automation lanes. Do not move any chord, bass or percussion notes; do not alter patches, mixer faders, sends, FX, timing, section markers, or tempo. Verify the project MIDI SHA256 is identical before/after, old project tree unchanged, full SoundCraft native save/reopen hash equality, zero clipped PCM samples and true peak <= −1 dBTP. Prepare pairs of full-mix 16-bar excerpts from Groove A and Main Drop with *gain-only* matched integrated LUFS, avoiding compression or limiting. Preserve original and revised full native audio privately; distribute audio only, never commercial Vital states.

**Evaluation:** If the corrected version sits more naturally rhythmically, preserve the source duck policy fix. If the chords still sound mismatched, test one phrase-consistent two/three-stab archetype within the existing harmony interlock, while maintaining original kick/bass/percussion/voicings and controlled native gain. Neither version is automatically a musical winner from technical gates.

## Native correction passed — matched-volume A/B prepared

A separate **real complete 128-bar SoundCraft native project**, full 48-kHz/24-bit stereo WAV and source-preservation receipt have now been verified at private `.local/full-song-jackin-G-harmony-duck-corrected-20261114/`. The original music remains unchanged; the independent diagnostic JSON was added to its folder during the render, so whole-directory inventory comparison alone is invalid. The original canonical project SHA256 is **315dcdda1dc04fc99b0c6466e474f5f4203949cd9bd84b948b742b91a5e18fd8** and original audio SHA256 still starts `cf3a6b754beaa43e60`. Original and corrected MIDI SHA256 are **both bc01560a35f0d94557941eb9f06365dc750e221b34edc10ed8ecd0f379364336**.

| Audio metric | Original A | Corrected B |
| --- | ---: | ---: |
| Musical duration | 128 bars / 241.890 s | Identical |
| WAV duration (including tail) | 253.890 s | 253.890 s |
| Raw integrated loudness | −26.707 LUFS | −26.611 LUFS |
| Raw oversampled true peak | −11.559 dBTP | −10.888 dBTP |
| Clipped samples | 0 | 0 |
| Actual chord kick duck | −5 dB | 0 dB |
| Bass kick duck | −5 dB, 420 ticks | −3 dB, 115 ms |
| Pad kick duck | −5 dB, 420 ticks | −1.25 dB, 143 ms |
| Native save/reopen | Passed | Passed |

The audio levels show a small overall loudness change, not proof that the music sounds rhythmically better. Both are genuine same-source/native real renders; changes are only the explicit known kick duck automation lanes, not chord onset MIDI, VST preset or FX.

Two paired original/corrected WAV excerpts are generated from **Groove A** and **Main Drop**, 16 bars per excerpt at 127 BPM. For each pair, integrated loudness was matched using *gain only* to **−22.00 LUFS**, without compression, limiting or clipping; corrected and baseline true peaks remain < −6.9 dBTP in these excerpts. Audition the pairs for chord rhythm, pocket stability and musical accents. Full corrected WAV is separately available.

At implementation completion, all 24 focused arranger, groove identity and harmony-interlock regression tests passed, including new **impact source policy / legacy source policy** checks. Original historical commits and outputs are preserved; correction remains in the experimental branch, not in main.

**Perceptual result: PENDING USER LISTENING.** If B resolves the unnatural pumping but still sounds rhythmically strange, the next isolated experiment should test a more phrase-consistent 2/3-stab pattern while leaving kick/bass, chords voicing, presets and corrected ducking locked.

