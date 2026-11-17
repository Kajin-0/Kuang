# House-v3 P0: frozen audio fingerprint and scope of the first high-effect mix trial

**Date:** 2026-11-16 UTC. **Status:** matched-native-audio baseline established. This report is *measurement*, not a new production winner or a blind listening assessment. No song source, preset, or musical code was changed.

## Exact sources and method

- Approved producer reference: `/home/User/Kuang/.local/phase44-experiment/release/B-Phase44-native-club-master.wav`, 118 bars, 126 BPM, **mastered**.
- Frozen generator baseline: all ten `ten-song-v1-XX-*-20261115/preview.wav` original real SoundCraft 128-bar **unmastered** outputs. No subsets were selected after seeing results.
- New reusable CLI: `tools/audio_fingerprint.py`. It reads canonical section boundaries, measures the same **eight-bar active** interval per passage using **actual PCM24 48k stereo**, 128 equally spaced 4096-sample Hann FFT windows for band-resolved mid/side, full-window RMS and mono loss, 400ms RMS distribution, and independently metered short-region ITU/BS.1770-style LUFS and dBTP through the installed local libebur128 reference backend.
- Kuang sections: first eight bars of **Groove A**, **Breakdown**, **Main Drop**. Phase44: first eight bars of **First groove**, **Breakdown**, **Late climax**. These are equivalent *musical passage roles*, **not** identical musical phrases or time placements. Comparisons are not normalized to identical source instrumentation and Phase44 is mastered; therefore the loudness comparison is descriptive, not a mix acceptance target.
- Note: breakdown RMS is independently measured **on the exact same eight-bar window**; it is not the same as the longer earlier aggregate. `short_region_integrated_lufs` is integrated LUFS *over an eight-bar excerpt*, **not** momentary LUFS.

## Whole-sample producer baseline (ten independent full songs)

| Matched-window metric | Median | Observed range |
|---|---:|---:|
| Main Drop minus Groove A RMS | **+0.0075 dB** | −0.158 to +0.118 dB |
| Main Drop minus Groove A integrated 8-bar LUFS | **+0.0395 LU** | −0.106 to +0.194 LU |
| Breakdown minus Groove A RMS | **−1.0075 dB** | −10.714 to +5.045 dB |
| Breakdown minus Groove A 8-bar LUFS | **+0.424 LU** | −9.561 to +5.577 LU |
| Groove fullmix side/mid | **−25.9218 dB** | −37.905 to −22.1879 dB |
| Groove 2–8 kHz side/mid | **−22.9543 dB** | −24.9326 to −18.303 dB |
| Groove 500–2000 Hz side/mid | **−19.5333 dB** | −41.4345 to −18.6893 dB |
| Groove 20–120 Hz side/mid | **−79.0106 dB** | −117.5554 to −56.1703 dB |

The last row is substantial mono retention and **should not be widened** just to raise the whole-track side/mid number. Breakdown amplitude is variable: a few sources withdraw significantly; minimal songs #07 and #08 instead get louder in the breakdown than their Groove A reference. The near-zero Main Drop lift is the consistent cross-style energy weakness.

## Approved Phase44 matched sections (different mastering stage)

| Same-section metric | Phase44 Groove | Phase44 Breakdown | Phase44 Late climax |
|---|---:|---:|---:|
| Section RMS dBFS | −15.833 | −17.708 | −15.585 |
| Eight-bar integrated LUFS | −13.702 | −14.608 | −13.288 |
| Fullmix side/mid dB | **−18.200** | −14.649 | −15.766 |
| 2–8 kHz side/mid dB | **−8.918** | −4.449 | −9.869 |
| 500–2000 Hz side/mid dB | **−13.491** | −9.450 | −12.321 |
| 20–120 Hz side/mid dB | **−64.663** | −62.213 | −64.672 |

Phase44 late climax vs first groove: **+0.248 dB RMS / +0.414 LU**. Phase44 breakdown vs first groove: **−1.875 dB RMS / −0.906 LU**. A large drop/breakdown gain swing is therefore **not** a universal prerequisite even in the user-approved master; arrangement dynamics and timbral contrast must be judged in context, not solely by a large RMS step.

The most defensible **first substantial native mix experiment** is upper-band spatial production, not bass timing: Phase44 has ~**14.04 dB greater** 2–8kHz side/mid energy than the ten-song median on these musical windows. This gap is a hypothesis for an A/B processing trial, **not** a fixed stereo-width target or evidence of human preference. The space/role scene must preserve low-end mono translation and avoid obscuring short chord attacks.

## Decision gates for P1

On **three frozen source-locked styles**, test real native 100%-wet short-room/dark-plate/filtered-echo returns, independently rendered via verified SoundCraft project graphs and equal-length audition windows, with source faders, MIDI, samples, Vital patches, groove, bass, and existing track FX held constant. Inspect actual upper-band side/mid change, mono sub retention, true peak, clipping, chord-onset smearing and integrated level difference. Require a material improvement across multiple sources and reject if any technical safety check fails. Do **not** equate extreme stereo width with mix quality or approve a candidate without reference-calibrated subjective evidence.

The exact machine-readable baseline is private, preserved at:
`/home/User/Kuang/.local/house-v3-reference-fingerprint-20261116/report.json`.
No private user-approved music, third-party presets, or drum sample bytes are committed. This report and the executable CLI/tests are versioned with the repository. Reproduction uses the existing, separately installed NumPy/SoundFile and libebur128 packages; no downloads were needed.

## P0b: per-bar and sliding 8-bar energy measurement (external review correction)

A review identified selection bias in measuring only the **first eight bars** of a section. The reusable CLI now calculates **every complete musical bar's unweighted stereo RMS** plus the RMS of every consecutive eight-bar interval advanced by one bar. An eight-bar minimum overlapping a breakdown is identified as a **cross-boundary interval** when it includes Build or Groove bars. These data are not labeled LUFS; 8-bar excerpts remain independently metered for gated integrated LUFS, and a per-bar waveform RMS dip must not be misreported as a 3–6 LU dip.

Fresh re-analysis of the exact same frozen eleven WAVs:

- **Phase44:** deepest individual Breakdown bar is zero-based bar **61** at **−39.795 dBFS RMS**. The lowest eight-bar interval overlapping the Breakdown starts at bar **60** and is **−5.018 dB RMS** relative to the mean-power eight-bar Groove benchmark; it crosses into **Rebuild**. The fixed within-Breakdown window remains **−1.875 dB RMS** relative to the originally selected Groove. The former is a separate rolling analysis and not a new claim about LUFS.
- **Kuang straight #01:** deepest overlapping interval **−7.140 dB RMS**, crosses boundary; **jackin #02** **−0.589 dB**, wholly within Breakdown; **minimal #08** **+0.978 dB**, crosses boundary and is *louder* than the reference Groove. This variation confirms that blanket section-level gain offsets are inappropriate.
- The frozen source references, section mappings, and previously published P0 results remain unchanged. The additional bar and rolling data are saved separately at `/home/User/Kuang/.local/house-v3-reference-fingerprint-sliding-20261116/report.json`.

The next P2 section-arc study should use both fixed named passages and bar-wise/rolling profiles to distinguish dramatic local withdrawal from whole-section loudness.
