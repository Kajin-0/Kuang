# House low-frequency groove and native sound fingerprints V1

November 15, 2026 — experimental branch. Technical and native audio proof; no default behavior or source presets changed.

## Primary research and scope

Duncan & Orgs, Music Perception 42(2), 2024, DOI 10.1525/mp.2024.42.2.95: 179 participants listened to 20 new house clips. The condition pairing high bass low-frequency amplitude and high bass syncopation produced the highest groove ratings among TWO experimental levels of each variable. The study does NOT test unlimited bass level or maximum complexity. https://doi.org/10.1525/mp.2024.42.2.95

Witek et al., PLoS ONE 9(4), 2014, DOI 10.1371/journal.pone.0094446, found intermediate syncopation elicited the strongest desire to move among funk drum-break variations, suggesting a potential optimum rather than universal maximization. The genres, instrumentation and syncopation manipulations differ. https://pmc.ncbi.nlm.nih.gov/articles/PMC3989225/

Lustig & Tan, Psychology of Music, DOI 10.1177/0305735619836275, found higher groove and liking with bass filtering that preserved low frequencies in four EDM loop contexts tested by 102 listeners. A strong bass fundamental is important; the study does NOT prescribe fixed high bass gain across unrelated sources. https://doi.org/10.1177/0305735619836275

## Actual Phase44 vs generated MIDI, original eight active groove bars

| Project | Kick quarter-note coverage | Bass onsets/bar | Offbeat onset fraction | Coarse crossing anticipation fraction | Mean bass gate |
|---|---:|---:|---:|---:|---:|
| Phase44 gold | 100% | 3.5 | 100% | 0% | 150.86 ms |
| #01 straight F minor, 120 BPM | 100% | 4.0 | 100% | 12.5% | 163.41 ms |
| #05 jackin C minor, 126 BPM | 100% | 4.0 | 100% | 0% | 131.94 ms |
| #07 minimal Db minor, 127 BPM | 100% | 2.5 | 100% | 0% | 161.02 ms |

Important: existing Kuang bass and Phase44 are ALREADY offbeat-driven. Therefore simply increasing the percentage of offbeats is not a meaningful improvement criterion. The anticipation fraction tests a very narrow sustained-note crossing, not formal syncopation or perceptual groove; the superior Phase44 has a zero on that proxy. Relevant further variables include bass note attacks/gates, quiet rests, kick alignment, accent, harmonics and real signal levels.

## Implementation

New kuang/house_bass_syncopation.py measures MIDI role note placement, phrase anticipation, accent/velocity range, gate durations and kick grid. Opt-in propose_phrase_pickups retimes a maximum of one EXISTING step-14 bass note to step-15 on each selected 4/8-bar phrase end (no added notes, changed MIDI pitches, altered kick, routing, preset, other role or FX); preserves source and outputs exact provenance.

New kuang/house_sound_fingerprint.py uses standard library analysis of real 48kHz 24-bit stereo PCM to measure actual played role spectral energy fractions (30–120, 120–250, 250–1000, 1–4k and 4–12k Hz), RMS, side/mid and short-window dynamic range. Result is a descriptive input to source selection, NOT a psychoacoustic masking or musical-preference score. All descriptors depend on register, MIDI velocity, note length and source patch; individual preset labels are insufficient.

Extended existing opt-in native source-review probe to calculate these waveform fingerprints while SoundCraft already solos kick, bass and chord roles. It retains no raw private stem samples and uses actual output frames to handle 127BPM single-frame bounce rounding without accepting materially truncated audio. No additional full-song native render is required during the opt-in review; default user pipeline stays unchanged.

## Three different real native mix contexts — first 16 Groove A bars

Native mid-channel spectral fractions normalized over 30–12,000 Hz. Not integrated LUFS or relative loudness in ear.

| Song / role | 30–120 Hz | 120–250 Hz | 250–1000 Hz | 1–4kHz | Sampled RMS |
|---|---:|---:|---:|---:|---:|
| #01 kick | 95.28% | 4.21% | 0.50% | ~0% | -28.54 dBFS |
| #01 bass | 89.18% | 7.68% | 2.85% | 0.28% | -36.45 dBFS |
| #05 kick | 95.35% | 4.15% | 0.50% | ~0% | -28.37 dBFS |
| #05 bass | 72.49% | 19.34% | 8.01% | 0.16% | -36.79 dBFS |
| #07 kick | 91.25% | 7.48% | 1.25% | 0.02% | -29.43 dBFS |
| #07 bass | 96.48% | 3.51% | 0.01% | ~0% | -44.42 dBFS |

Substantial style and source differences: #05 has notably more bass upper-body energy than #01; the minimal #07 bass is almost entirely sub and very sparse/quiet by design. A universal low shelf, forced +10dB bass gain or hard-coded Phase44 fader relationship would be unjustified. The kick-bass low-band occupancy overlap proxies of 0.934, 0.766, 0.948 are NOT phase, masking or groove scores.

## Actual controlled user favorite #01 bass A/B

A: untouched original 16 bars from native session.
B: +2dB bass track gain and identical existing bass gain automation offset; same MIDI, drum/chord/pad presets, routing and FX.
C: B, plus only four existing bass notes retimed at 4-bar phrase endings (bars 20,24,28,32): 16th step 14 -> 15, with unchanged note pitch, gate and velocity. No new bass notes or altered kick.

The FIRST provisional A/B had a methodological failure: the original saved full-preview crop had a -11.68dBTP peak, but the newly exported host bounces had -5.64dBTP peaks. This difference came from incomparable output paths. Those provisional files remain archived as failed measurement evidence. We corrected it by re-bouncing A with exactly the same SoundCraft native excerpt procedure as B/C; the corrected original also peaks -5.637dBTP.

| Same-host 16-bar result | Native LUFS | Native true peak | Corrected level-matched LUFS |
|---|---:|---:|---:|
| A original | -27.599 | -5.637 dBTP | -23.962 |
| B bass +2dB | -27.221 | -5.637 dBTP | -23.962 |
| C +2dB plus four pickups | -27.219 | -5.637 dBTP | -23.962 |

Corrected listening clips are gain-matched without compression/limiting, zero clipped samples, true peak <= -2.0dBTP. The +2dB bass fader moves integrated mix loudness only +0.378 LU; the phrase movement is almost level-neutral. Neither is claimed musically better until actual user A/B listening.

- A original: https://gofile.io/d/6OIQx6dQ
- B +2dB bass: https://gofile.io/d/pRnh7J71
- C +2dB and sparse phrase-end pickup: https://gofile.io/d/DSIPM4Lz
- Corrected package with WAVs and evidence: https://gofile.io/d/uWsBy1w1

## Next stop gate

Technical milestones met: native source fingerprinting and role MIDI analysis on three independent songs, 16bar private real SoundCraft bass A/B on favorite #01, source hashes/patch states untouched, safe native save/reopen, same-host corrected listening audio, focused unit tests.

The remaining decisive issue is musical preference. If B/C sound better, generalize to two additional original songs using the original instrument and drum palette before enabling any default. If not, test verified bass sources with more appropriate upper harmonics/body and inspect the actual kick/bass interaction instead of accumulating gain or 16th notes. Extend the source fingerprint to a private cached preset/register/velocity database only after demonstrating it predicts useful candidate choices.
