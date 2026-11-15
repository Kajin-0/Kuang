# Kuang: Phase44 forensic production audit — November 15, 2026

Status: completed source audit and prioritized implementation plan; no composer, audio or default settings were changed in this step.

## Scope and actual source artifacts

The user approved all ten randomly drawn, complete 128-bar house demos as listenable and prefers #01 (straight house, F minor, 120 BPM). The older Phase44 C-minor 126-BPM 118-bar master remains the stronger *audible* gold standard. The supplied gold_vs_generated.png figure compares energy arc, stereo width and low-end-normalized spectrum.

Inspected actual private VPS assets: phase43-experiment/release/project.kuang.json; phase44-experiment/release/project.kuang.json; the Phase43 and Phase44 generation scripts, mastering receipts and report; current ten-song-v1-01-straight-20261115/project.kuang.json; source histories of Phases 33, 35, 36, 39–43; current generator docs and the ten-song diversity experiment. Keep all third-party Vital preset states private, original file hashes unchanged, and the public main branch intact.

## Conclusive findings

**Phase44 is a master-only change to Phase43's already developed song.** The native projects have identical nonmaster tracks, MIDI, section markers and 22 automation lanes; only terminal master settings/metadata differ. Therefore Phase44's rich arrangement, bus effects and width were built in the *preceding* phases. Copying its final compressor/maximizer cannot supply missing chord body or orchestration.

| Actual native project metric | Approved Phase44 | Ten-song #01 |
| --- | ---: | ---: |
| Music bars | 118 | 128 |
| Tempo BPM | 126 | 120 |
| Tracks / bus tracks | 22 / 8 | 8 / 0 |
| Sends / routing edges | 31 | 0 |
| Automation lanes | 22 | 5 |
| Separate wet chord delay/room buses | 2 | 0 |
| Distinct shared room/dark space/delay returns | yes | no |
| Master dynamics bus | compressor + maximizer | no dedicated native mastering bus |
| Stereo spread on chords/pad and return pan automation | yes | no comparable independent returns |
| Lead instruments actively audible | no; 2 tracks muted | none |

The gold production's 22-track architecture includes a drum sum bus with parallel processing, authored clap/bongo/sweep support, a shared reverb room, dark plate space, modulated echo, dotted echo and independently panned eighth/dotted chord delay+room paths. It has phrase-programmed bass kick-pocket gain (1,223 points), breathing pad (1,272 points), plate pumping (1,275 points), separate chord throw lanes (614 each), stereo return motion and several outro-specific fades. In comparison the generated direct inserts, 3 coarse filters and bass/pad duck lanes are less diverse in how they shape the musical message; a large raw breakpoint count alone does not establish good production.

Gold sequence demonstrated by inspecting actual scripts:
- Phase33 reworked form/phrase routing and documented rhythm decisions.
- Phase35 introduced separate musical chord echo return architecture.
- Phase36 intentionally retained the chord bus architecture while preserving authored C minor / F minor / G dominant 16-bar response, bass-pocket gain and outro role fades.
- Phases39–40 refined transient-aware drum bus, bass harmonics, chord warmth, snare and auxiliary percussion.
- Phases41–42 added section-aware shared space and panning/width movement.
- Phase43 selectively added short room after chord delays and controlled 1.25dB pad / 2dB plate kick-synchronous pumping, leaving previously approved drum/bass MIDI unchanged.
- Phase44 only selected a new terminal master compressor/maximizer candidate.

### What Phase44 mastering actually contributed

| Meter (libebur128, 4x true peak) | Phase43 original | Phase44 club master |
| --- | ---: | ---: |
| LUFS integrated | -16.3945 | -13.9066 |
| True peak dBTP | -2.0465 | -1.4132 |
| Loudness range LU | 5.84 | 4.96 |
| Peak-to-loudness ratio dB | 14.35 | 12.49 |
| Clipped samples | 0 | 0 |

The master increased loudness by +2.49 LU while reducing PLR by about 1.85dB. The initial louder Phase44 candidate was **rejected** for exceeding the -1dBTP safety limit; a different bounded candidate was chosen. This proves a productive producer workflow: propose candidates, meter/compare, retain best *safe* candidate, save editable full native session and untouched premaster. Loudness alone did not produce the earlier song's harmonic presence and stereo space.

### The user-supplied comparative figure

Kick+bass level-matched band graph: gold vs generated relative to kick+bass energy:
- 120–250 Hz: gold -3.2dB, generated -2.6dB (generated +0.6dB)
- 250 Hz–1kHz: gold -3.9dB, generated -8.6dB (generated **4.7dB weaker**)
- 1–4kHz: gold -4.1dB, generated -12.7dB (generated **8.6dB weaker**)
- 4–16kHz: gold -11.0dB, generated -12.9dB (generated **1.9dB weaker**)

In its groove, the graph shows gold stereo side/mid approximately 10–15dB stronger than generated and a much more visible energy arc, withdrawal and drop-rebuild. Those observations are source-derived from the supplied figure, not separately repeated measurements of the same master at equal LUFS. The two songs have different keys, tempos, form and mastering, which precludes a causal attribution to any one difference. Never apply +8.6dB fixed EQ to the whole midrange; the deficit could be source, timing, processing, or instrument balance.

The ten independent generated songs support a systematic issue: all 10 have Main Drop vs Groove A fullmix RMS within -0.073 to +0.225dB, three breakdowns louder than Groove A, median stereo side/mid -27.34dB, only 4 bass/4 chord/3 pad preset identities, with the same pad in 7/10. Bass rhythm and chord-stab onset groups each had 7/10 distinct variants. The bottleneck has moved from simply making complete songs to producing dynamic mix cohesion/space and a purposeful energy progression.

## Critical negative precedent

A prior attempt to copy Phase44's exact fixed EQ/saturation/compressor parameters onto arbitrary new presets was rejected by user listening and reverted (c10dbd4 -> 5694cce). DO NOT blindly import Phase44 exact faders, 22 tracks, fixed saturation parameters, preset names, one C-minor chord progression or a universal master LUFS goal.

## Ranked implementation strategy

**P0 — source-aware presence + independent space returns, short native A/B first.**
Use user-preferred #01 as frozen incumbent and preserve all 128-bar original music/audio. On **only 8–16 bars**, lock kick, bass, chords and private verified source patches. Compare incumbent against 1–2 restrained, **wet-only** chord echo/room return candidates, with independently adjustable gain/stereo/highpass and no re-ducking the dry chord attacks. For each candidate, measure the 250Hz–1kHz and 1–4kHz relationship *to the existing kick/bass anchor*, mono-fold-down, true peak, transient crest and selected stereo side-band energy. Level-match the complete mix with gain only; user listens for improved warmth, rhythmic articulation, cohesion and width. Do not pursue added reverb if masking/blur rises or user dislikes it. This tests a real Phase44 production difference while minimizing compute and not swapping instruments simultaneously.

**P1 — section-dependent energy, not generic gain boosts.**
From an accepted groove, choose a section/energy plan with different plausible arrangement classes instead of only one fixed 128-bar eight-section form. Program selective kick/bass withdrawal, muted gap/transition cues, changing chord/pad bus and reverb gains, rebuild filtering, drum fills and a gradual DJ outro. Drive the controls with a structured production hypothesis; no invariant "drop must be 3dB louder". Evaluate measured sectional LUFS, spectral/side energy, transition click/silence integrity and user listening. Retain current kick/bass pocket when unchanged.

**P2 — contextual drum/bass/harmonic processing.**
Use real composite-stem measurements and conditional source-specific drum transient glue, upper bass harmonics, auxiliary percussion and stereo-safe harmonic role separation. Preserve mono foundation while shaping 150–1000Hz articulation. Reject the old fixed one-source effect transplant.

**P3 — actual editable mastering candidate generation.**
Once good musical mix is confirmed, propose bounded SoundCraft compressor/maximizer configurations in a separate native master bus and audition short dense/quiet excerpts. Meter integrated LUFS, LRA, true peak, PLR, crest, and sub preservation; reject clipping, over-limiting and severe pumping. Produce both verified premaster and master, never describe +9dB gain-only matching as mastering. The Phase44 -13.91LUFS is a reference point, not an invariant.

## Intelligent producer decision loop

Prompt -> style/intent + source and arrangement grammar -> contextual first-mix audio -> relevant producer hypotheses (kick/bass conflict, weak chord body, narrow stereo, uncontrolled pad, absent energy arc) -> bounded native effect/send/gain candidates -> short verified audio + objective analysis -> preference-guided choice -> long-form arrangement and energy automation -> bounded master candidates -> verified native project, original premaster, final mastered release, and immutable receipts.

This is **not yet an AI listening/evaluation system**. Numerical DSP metrics enforce safety and reveal specific contrasts; they cannot certify subjective musical quality. A model can choose and revise hypotheses but must be evaluated against actual audible results and rejected candidates. Reproducing Phase44's **source-aware decisions** across diverse songs matters more than adding randomness or literally cloning one fixed Phase44 project.

## Stop gate

Next small, decisive test: **preferred generated #01** 8–16 bars with same MIDI/sources/mix; A current / B one restrained context-aware chord-space variant. Only after equal-gain real native listening improvement should the workflow generalize to an independent song, then section automation, then mastering. No 10 full-length rerenders before the first result.

Overall verdict: high-confidence structural/source/master provenance; medium-confidence causal claims that any single spatial effect is aesthetically responsible; needs controlled A/B.
