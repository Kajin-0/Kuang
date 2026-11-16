# House bass-pocket native cross-style gate — 2026-11-15

## Outcome and scope

Producer preference: chord phrase-coherence candidate B was preferred, but low-end groove was judged weaker than Phase44. This experiment preserves that preferred chord treatment, native kick/bass sources, exact bass onset pattern and note durations. Only bass track gain and its mixer-gain automation are changed in trial copies. There are **no changes to production defaults**, no unverified source substitution, and no auto-approved musical winner.

The new opt-in source-aware engine is in kuang/house_bass_audio_gate_v1.py. It checks exact canonical source/candidate project state, MIDI identity, independent native export/save/reopen status, 48 kHz PCM24 file alignment, nonclipping and ≤−1 dBTP true peak. It then uses the already established house_groove_pocket algorithm on the actual SoundCraft render.

### Measurement definition

The beat/offbeat low-band comparison uses the first 100 ms after each MIDI kick versus 200–300 ms after that kick, over a real active Groove section. Separate bands are 25–90 Hz and 90–250 Hz. A smaller beat/offbeat ratio means more offbeat low-band energy relative to the kick window, **not necessarily a stronger subjective groove**.

The provisional screen requires a reduction of at least 1.0 dB in the 25–90 Hz ratio AND 0.5 dB in the 90–250 Hz ratio, no clipped samples, and ≤−1 dBTP. These are explicitly *experimental thresholds*, not formal psychoacoustic optima. The smallest passing gain is shortlisted for subsequent stem and listening review; this is never a default.

## Three independent real native 16-bar House sources

| Style / source | Baseline 25–90 Hz beat/offbeat | Baseline 90–250 Hz beat/offbeat | +3 dB reduction 25–90 / 90–250 | +6 dB reduction 25–90 / 90–250 | Technical outcome |
|---|---:|---:|---:|---:|---|
| Jackin G, 127 BPM | +12.176 dB | +9.057 dB | 1.883 / 2.465 dB | 4.011 / 4.794 dB | +3 shortlisted |
| Minimal F♯, 122 BPM | +8.656 dB | +2.317 dB | 2.810 / 2.085 dB | 5.534 / 4.407 dB | +3 shortlisted |
| Deep E, 123 BPM | +9.508 dB | +7.407 dB | 0.507 / 0.117 dB | 1.253 / 0.411 dB | No gain shortlisted |

Native source identifiers: gmi-v1-jackin-G-20261114; three-grooves-minimal-Fsharp-20261114; three-grooves-deep-E-20261114. All use the pre-existing groove_identity_v2 and the preferred B chord timing. All new deep/minimal outputs and the prior jackin variants passed actual native export/save/reopen, rendered without clipping or true-peak violations, and preserved private source inventories. The deep-house negative result is a concrete counterexample to globally hardcoding +3 dB or +6 dB.

Source baseline premix LUFS-I / dBTP: jackin −28.044 / −5.634; minimal −20.911 / −5.204; deep −23.432 / −5.889. The raw sessions must not be compared at unmatched loudness.

## Independent native kick/bass stem interaction

Only the two shortlisted +3 dB sources advanced to costly isolated-stem review. The native SoundCraft instrument, bus and processing graph was preserved. The kick stem is identical between A and B. The source-fit diagnostics use matched WAV frame counts and actual project kick MIDI positions.

| Actual native measurement | Minimal original / +3 dB | Jackin original / +3 dB |
|---|---:|---:|
| 23–117 Hz linear kick+bass sum vs independent stem power | +0.144 / +0.199 dB | +0.195 / +0.266 dB |
| Full-mix sub-band mono fold-down loss | ≈0 / ≈0 dB | ≈0 / ≈0 dB |
| Bass-on-kick vs between-kick source power | −5.820 / −5.820 dB | −3.842 / −3.842 dB |
| Destructive sum / mono warnings | None / none | None / none |

These are linear source-sum diagnostics, not a recreation of a nonlinear native master bus or a human listening result. No destructive interference or sub-mono loss was flagged on the evaluated samples. The deep-house source never reached this test because its gain-only spectrum did not qualify.

## Level-matched listening assets

The minimal A/B is independently matched with attenuation only to −21.011246 LUFS-I; native stereo 48-kHz PCM24, unclipped:

- [Minimal F♯ A — original bass with B chord timing](https://gofile.io/d/vbRpGjqw)
- [Minimal F♯ B — bass +3 dB with B chord timing](https://gofile.io/d/npsJVttt)

The earlier jackin A/B is matched within that pair to −28.250 LUFS-I:

- [Jackin G A — original bass with B chord timing](https://gofile.io/d/EyGtRBcJ)
- [Jackin G B — bass +3 dB with B chord timing](https://gofile.io/d/0z8aUO6Y)

Compare within each style's A/B; the minimal and jackin pairs are **not at the same target loudness**.

## Engineering verdict and next experiment

1. The reviewer and its six-module related regression suite passed **29/29** local tests. All described private native renders have been completed.
2. +3 dB is a technically viable, source-specific audition candidate for two songs. No generalized gain setting is supported.
3. Deep-house failure indicates the gain lever alone is inadequate for that bass/source/mix context. The next targeted hypothesis is **native bass source envelope and upper harmonics**, with unchanged bass MIDI and chord-B source.
4. Retain original Phase44 and the vetted private samples as comparison references, but do not enforce any global Phase44 fader, LUFS or spectral target.
5. Automatic production promotion remains blocked pending repeated source-aware phase/spectral checks and human listening; this code **does not modify the one-prompt generator by default**.

Private output evidence is stored under /home/User/Kuang/.local/bass-audio-cross-style-20261115, including canonical source hashes, rendered native bundles, raw WAVs, gate JSON, and actual isolated-stem analysis.

## Deep-house follow-up: reject simple note shortening

The deep-house source used the **same verified bass patch** as the jackin G source, but the bass MIDI distributions differed. Deep E has four offbeat notes/bar with leading beat positions 0.5, 1.5, 2.5 and 3.25; its principal long notes were 420 ticks (0.4375 quarter note), leaving roughly 30 ms before the next kick, excluding synth release. Jackin instead has an early accent at 1.25 beats and shorter 342-tick principal notes. Both have exact quarter-kick coverage 1.0 and no bass onsets directly coincident with the kick.

Actual isolated deep-house native stems (SoundCraft, original chord B and groove-v2): kick RMS −28.744 dBFS, bass RMS −36.303 dBFS, kick sub-band −29.781 dBFS, bass sub-band −36.695 dBFS. The bass near-kick vs between-kick power was −1.696 dB, compared with −3.842 dB for jackin and −5.820 dB for minimal. Kick+bass linear sub summation +0.030 dB, fullmix mono loss approximately zero. Thus there is no evidence of substantial destructive low-frequency phase cancellation in the tested windows; the poor responsiveness to gain suggests temporal or spectral context.

A separate, single-variable private candidate shortened the 10 existing principal 420-tick bass notes to 342 ticks (same MIDI note onsets, pitches, velocities, FX, sample/patch and all other tracks), with zero gain change. Native export, save/reopen, full WAV render, clipped-sample and true-peak checks all passed. Measured beat/offbeat 25–90 Hz ratio changed from +9.508 to +9.429 dB (only 0.079 dB improvement) and 90–250 Hz from +7.407 to +7.261 dB (only 0.146 dB improvement). Near-kick bass versus between-kick power changed from −1.696 to −1.675 dB, **not an improvement**. Sub-band summation after shortening was −0.106 dB with no warning; source inventory remained intact.

**Decision:** reject principal-note shortening as an effective low-end fix for this source. The next bounded experiment should examine actual native patch envelope/ducking and spectral harmonic balance, one factor at a time, before adding MIDI complexity or boosting its fader again. No automatic defaults changed.
