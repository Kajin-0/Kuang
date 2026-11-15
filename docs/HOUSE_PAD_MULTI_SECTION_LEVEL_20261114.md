# Pad section level balance — native evidence and opt-in algorithm (2026-11-14)

## User feedback and source of the problem

The user said that the selected replacement pad in C still sounded too intense and asked specifically whether Kuang checked volume at different places and detected peak levels. The prior one-prompt selector focused on original preset features and lower-mid overlap in the Groove. In C, the pad has active MIDI in **Intro, Breakdown and Drop**, not Groove. A passing full-mix true peak of -5.204 dBTP is a headroom gate, NOT evidence that the pad is balanced or pleasant.

This is a general source-/arrangement-compatibility problem; no C-specific sound/preset should be forced globally. Preserve SongSpec, the existing groove-template composition and harmony, private Vital/SoundCraft pipeline, CC0 sample integrity, Phase44, and all prior original outputs.

## New real, full-gain, multi-section native measurements

Fresh native stems were exported from the exact final selected patch+gain+automation+FX settings, muting all other role MIDI tracks. Every comparison uses the same song timeline. New reusable 'kuang/house_section_levels.py' reports section RMS, PCM sample peak and p95 of 10/100/400ms RMS windows. PCM sample peaks are not oversampled true peaks; full-mix integrated LUFS and oversampled TP are measured separately in loudness.measure.

C selected pad (Strings of Cygnus) 400ms p95 vs native chords:

| Section | Pad dBFS | Chords dBFS | Pad louder |
| --- | ---: | ---: | ---: |
| Intro | -22.706 | -34.191 | +11.485 dB |
| Breakdown | -22.425 | -34.436 | +12.011 dB |
| Drop | -22.747 | -34.187 | +11.440 dB |

In the Breakdown, pad PCM sample peak is -10.332 dBFS vs chords -20.609 dBFS, a +10.277 dB difference. This is substantial pad dominance, not a clipping fault. The pad has no newly programmed note attacks in C's Groove.

**Independent references:** deep E-major pad is typically 5–8 dB below chord sustained-window p95 in pad-active sections. Jackin B-flat major pad is comparable or slightly below chords. Neither triggers the new bounded trim. Thus a universal -12 dB pad default would be wrong.

## New incremental optional algorithm

- Pure source-agnostic function: 'kuang/house_pad_level.recommend_trim'. It uses actual same-timeline 100ms and 400ms p95 windows and PCM sample peaks for all sections in which both pad and harmony have notes.
- Compares pad/chord RMS p95 and tolerates up to +1 dB pad-vs-chord PCM sample peak; recommends reduction for the largest section violation. A 1.5 dB deadband prevents trivial tweaking. The reduction is limited to **-12 dB**.
- Pure 'apply_trim' updates the existing editable pad fader and ALL matching pad gain automation events, preserving every other source, FX, track, MIDI, section and routing exactly.
- New 'kuang/house_pad_native_level.native_pad_balance' uses existing private SoundCraft adapter to render pad and harmony solo stems with native FX, measure every section, and independently render and save/reopen the exact full project after adjustment. Rejects new clipping, true peak above -1 dBTP, silence, mismatched native state or source drift.
- In existing 'kuang.autonomous_create', the new --pad-level-calibration flag requires --groove-template and is limited to short 16/32-bar nuclei; legacy behavior remains unchanged without the flag. No new composer, DAW, role or native plugin.
- A -12 dB ceiling is an experimental first safety bound, NOT a universal mixing standard, compressor or trained listener model. The receipt keeps the raw metrics, requested amount, applied bounded amount and pending listening status.

## Validation

Tests verify an exact 9.54 dB level step for a 3x sinusoidal amplitude change, reject invalid PCM/section windows, check the measured C requirement, preserve independent A/B with zero trim, and confirm unchanged MIDI/source and synchronized gain automation. New native run is required before asserting success.

Keep originals immutable. The fresh C-style native execution must pass real source verification, SoundCraft save/reopen, zero clipping and audio verification. Present matched-loudness original vs trimmed audio to the user, and preserve the alternative if the listening result is mixed. Extend to diverse new prompts before enabling by default.

**Known separate issue:** the existing *source-selection* native pad compatibility gate measures the Groove even if pad attacks are absent there. The new level policy measures pad-active sections correctly. Refine the source-selection gate separately with controlled tests rather than conflating the two changes.

Status: provisional, opt-in; listening and native evidence appended after completion.



## Verified one-prompt native run and output (November 14, 2026)

The new opt-in pipeline completed a **fresh full autonomous native C-style house generation** at F-sharp minor, 122 BPM, seed 29, 16 bars, using the already-tested contextual pad source rescue AND the new multi-section level calibration. Private output: /home/User/Kuang/.local/minimal-Fsharp-padlevel-autopad-20261114/. Original independent control: /home/User/Kuang/.local/minimal-Fsharp-autopad-rescue-20261114/ (preserved).

| Final private native result | Prior automatic pad selection | New with section-level balancing |
| --- | ---: | ---: |
| Vital pad | Strings of Cygnus | Strings of Cygnus |
| Pad mixer gain | -6.0 dB | -18.0 dB |
| First pad gain automation point | -7.25 dB | -19.25 dB |
| Integrated raw full-mix loudness | -23.748 LUFS | -28.105 LUFS |
| Oversampled raw full-mix true peak | -5.204 dBTP | -5.204 dBTP |
| Clipped samples | 0 | 0 |
| Native save/reopen | Passed | Passed |
| MIDI SHA256 | e6742007e8044b66c53cedf691fa1954bb618a36c1533ba45718eca89381d5ea | Exact same |
| Bass/chord/pad verified SHA source identities | Preserved | Exact same |

The source-independent level algorithm evaluated Intro, Breakdown and Drop as active pad/chord sections and requested 12.011 dB reduction. It applied the **bounded -12.000 dB** maximum, including all pad gain automation, and recorded that the request reached the ceiling. The actual native output was re-exported, saved/reopened and rendered again after this change; it passed true-peak, clipping and source-integrity gates. The global full-mix true peak remained exactly -5.204 dBTP because a different element sets that peak; the pad's intensity was not detectable from the absolute mix peak alone.

The source review was not reconfigured, no names or patch data were hard-coded, and the old C/cleaner C outputs remain immutable.

For controlled listening, two 16-bar 48-kHz/24-bit stereo WAV excerpts were matched to **-24.584 LUFS** using gain-only adjustments, and each confirmed zero clips and true peak <= -1.8 dBTP. The original matched sample TP was -6.083 dBTP, and the newly balanced sample -1.800 dBTP. This relatively low match level is intentional: preserving headroom without limiting is more important than a loud playback file. Verified user-facing share (external retention uncertain): https://gofile.io/d/BkoQqbsg . Private evidence: /home/User/Kuang/.local/padlevel-matched-listening-20261114/.

Across independent A/B native sources, this same algorithm recommended **0 dB pad trim** because their multi-section native 100/400ms and sample peaks were already comparable to or below chords. That is a symbolic role-level policy test using actual pre-rendered native measurements for each song; do not claim we re-rendered two fresh A/B releases with the flag.

The new optional level guard passed **83 focused tests** along with existing source-selection, groove, harmony and native-adapter tests. The user has not yet rated the balanced C output; keep the new option disabled by default, and run independent prompt listening before promotion.

### Next decision

The user should listen to the original-vs-balanced audio and judge the pad's audibility, body and placement in intro, breakdown and drop, including whether -12 dB is too much. Do not blindly lower every pad, raise all chord levels, or perform further expensive render sweeps unless new listening evidence indicates the most useful next step. A later independent audit should correct the context source-picker's reliance on Groove-only pad rendering when there are no new pad attacks there.



## User listening verdict — balanced version B preferred (November 14, 2026)

The user compared the gain-only loudness-matched 16-bar audio variants in `Kuang_AutoPad_SectionLevel_AB_20261114.zip` and explicitly said **"yes B is better"**. In that comparison **A** was the freshly generated automatic contextual pad selection before level calibration; **B** used the same verified Strings of Cygnus pad, identical MIDI and other instruments, with the new multi-section native pad-level policy applying **−12 dB** to the pad fader and matching pad gain automation. Both WAVs were gain-only matched near −24.584 LUFS, no clipped samples. **B is now the listener-preferred C reference mix.** Preserve A and the earlier original C projects and their evidence.

This is direct listening evidence for the measured correction **in this C-style production only**. Do **not** automatically make −12 dB the default trim, infer a general mixing law from this one example, or claim that the feature has been validated on independent prompts. Keep `--pad-level-calibration` opt-in pending an **unseen-prompt** generalization gate. A/B deep and jackin reference stem measurements predict no change; that is a useful negative control but not independent audio approval of the complete pipeline with this flag. The next substantive priority is Kuang's broader low-end groove and source-pair suitability; do not keep polishing C. Test genuine new prompts with matched-loudness listening and include positive/negative pad controls while measuring kick/bass temporal interaction and source suitability. Keep all earlier releases intact.
