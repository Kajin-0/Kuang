# Kuang — Ten independent full-length house productions: variation audit

Date: November 15, 2026. Experimental branch only; no core generator changes or main-branch promotion.

## Listening recordings

**[All ten lossless, loudness-matched full songs](https://gofile.io/d/18tJioFp)** (about 389 MB; 48 kHz/24-bit FLAC).

All songs are original 128-bar editable native SoundCraft/Vitalium house productions generated through the **same** current one-prompt workflow, with the opt-in full phrase-development policy. The FLAC listening derivatives use only gain-only normalization to about −21 LUFS and remove the otherwise digitally silent tail; all original WAVs and private SoundCraft/Vital states remain untouched on VPS.

| ID | Style | Key | BPM | Bass preset | Chord preset | Pad preset | Full-song FLAC |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| 01 | straight | F minor | 120 | LD Bass | string stabs | minimal house pad 2 | [Listen](https://gofile.io/d/hOlZ3VoC) |
| 02 | jackin | G minor | 122 | Biow Bass 2 | SNFKFutureBounce - Loaded Chords | minimal house pad 2 | [Listen](https://gofile.io/d/b4ftUypb) |
| 03 | jackin | E major | 127 | Biow Bass 2 | WIP-D - Retro Piano | minimal house pad 2 | [Listen](https://gofile.io/d/keFpysex) |
| 04 | deep | B minor | 126 | Biow Bass | string stabs | minimal house pad 2 | [Listen](https://gofile.io/d/xX6mtU9t) |
| 05 | jackin | C minor | 126 | Biow Bass 2 | WIP-D - Retro Piano | Strings of Cygnus | [Listen](https://gofile.io/d/Kskuku7w) |
| 06 | deep | Bb major | 130 | gentle pluck bass | SNFKFutureBounce - Loaded Chords | minimal house pad 2 | [Listen](https://gofile.io/d/aDF83bZM) |
| 07 | minimal | Db minor | 127 | gentle pluck bass | minimal house dub stab 23 | Strings of Cygnus | [Listen](https://gofile.io/d/PsUXU2it) |
| 08 | minimal | Gb major | 120 | Biow Bass 2 | minimal house dub stab 23 | In the Dark | [Listen](https://gofile.io/d/CxsnmOSM) |
| 09 | deep | A major | 123 | gentle pluck bass | minimal house dub stab 23 | minimal house pad 2 | [Listen](https://gofile.io/d/6UjystYW) |
| 10 | straight | D major | 128 | Biow Bass 2 | SNFKFutureBounce - Loaded Chords | minimal house pad 2 | [Listen](https://gofile.io/d/8Vb1TOip) |

## Frozen randomization and reproducibility

- Ten unique tonic names, five minor and five major, randomized 120–130 BPM, independent seeds; profiles: three deep, three jackin, two straight, two minimal.
- Original manifest was frozen BEFORE rendering and retains every intended case; there was no selection based on sound quality.
- One deterministic prompt validation mismatch occurred: song 04 said "extended chords" but randomly supplied "simple" harmony profile. The failed preflight created no song; its same prompt, key, BPM, seed and style were rerun with the explicitly requested extended harmony. The correction and original manifest are preserved privately.
- All ten final renders passed actual SoundCraft save/reopen, non-clipping and true-peak safety gates.

## Objective result: compositional and source diversity

| Measured property | Ten-song result |
| --- | ---: |
| Distinct first-eight-bar bass rhythm fingerprints (velocity and note IDs excluded) | 7/10 |
| Distinct first-eight-bar chord rhythm fingerprints | 10/10 |
| Distinct tonic-relative bass note/duration/onset fingerprints | 9/10 |
| Distinct four-chord progressions | 8/10 |
| Distinct selected bass/chord/pad presets | 4 / 4 / 3 |
| Distinct kick samples | 4/10 |
| Pairwise repeated bass source among 45 comparisons | 28.9% |
| Pairwise repeated pad source among 45 comparisons | 48.9% |

Every song has a distinct tonic and seed, but those alone are not evidence of musical originality. The audit therefore compares key-normalized note/duration/onset motifs and role source identities. Differences in chord attacks and bass articulation are real symbolic changes; perceptually different musical identities still require producer listening. Seven of the ten songs use "minimal house pad 2", indicating a persistent tendency to reuse the same pad.

## Mix structure and frequency/stereo profile

| Measured quantity | Result |
| --- | --- |
| Main Drop vs Groove A section RMS | **+0.007 dB median**, range -0.073 to +0.225 dB |
| Breakdown vs Groove A RMS | **-1.053 dB median**, 3/10 breakdowns louder than Groove A |
| Full-track stereo side/mid energy | **-27.34 dB median**, range -37.23 to -21.63 dB |
| Mid-channel 25–250Hz spectral energy in sampled FFT blocks | 64.2% median, range 40.6–88.3% |
| Native unmastered integrated loudness | -28.16 to -23.02 LUFS |

The most generalizable issue is the near-flat **main drop energy**, which repeats across every instrument/key/profile configuration despite different bass and chord motifs. The breakdown variance is much larger: some breakdowns are very quiet while three are actually louder than Groove A. Stereo remains mostly narrow in every song. These measures independently reinforce, but do not blindly adopt, Claude’s single-song audit observations.

**Important measurement limits:** The section figures here are unweighted fullmix RMS (dB relative), not gated EBU integrated loudness; stereo width is an energy ratio, not an image-quality verdict; low-frequency spectral distribution is not an equal-loudness perceptual score. No claims of audible groove quality, studio readiness or a universal mastering target are made from these numbers.

## Product decision / stop gate

Ten songs are **meaningfully different in MIDI phrase, progression, key and tempo**, but sonic-source vocabulary is still limited and section-energy shape is highly repetitive. Do NOT respond by forcing random notes, adding unverified presets, making the drop arbitrarily +3 dB or trying to master away the issue.
The most defensible next milestone is a **source-aware, section-controlled arrangement energy arc**, including independent intro/break/build/drop/outro role levels and transition moves, stereo width above the low-frequency mono region, and per-section chord/pad balance — tested on independent songs without changing their core MIDI.
First ask the producer to listen to the provided ten level-matched recordings and identify whether they feel like ten distinct musical ideas and which have the strongest groove.

Full sanitized per-song diagnostics and source-note fingerprints: [JSON baseline](baselines/HOUSE_TEN_FULL_SONG_VARIATION_20261115.json).

Status: ten real full native songs complete; measured variety and shared weaknesses established; perceptual preference pending.
