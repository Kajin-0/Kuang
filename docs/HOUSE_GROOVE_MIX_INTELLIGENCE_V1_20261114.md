# Kuang Groove and Mix Intelligence V1 — engineering record (November 14, 2026)

## Goal

One prompt must produce a convincing and fully editable house production with a physically felt kick/bass pocket and sensible level balance. This work extends, and does not replace, the existing SongSpec, house_template, Groove Identity V2, Musical Planning V2, private Vitalium source selection, CC0 sample kit, SoundCraft native host, harmony interlock and prior Phase44 evidence.

## Implemented native algorithm

Added house_groove_body.py to analyze exactly time-aligned genuine native kick and bass SoundCraft stem WAVs in the active Groove section. Window origin is each real programmed kick MIDI event, not a fixed 126BPM clock. Hann FFT integration over two bands (25–90 Hz sub; 90–250 Hz upper-bass) gives three linear-power-normalized observations per beat: kick 0–100ms, bass 150–250ms and bass 250–350ms. The report stores bass early/late relative to kick and bass late relative to early. It refuses malformed, silent or misaligned audio. This is a spectral source-context diagnostic, not musical taste or a calibrated commercial reference.

Integrated optional --groove-body-review with the already established --contextual-shortlist in autonomous_create/house_one_prompt_context. Uses existing native source-fit kick/bass stems and adds no new default render. The existing source and composition are unchanged unless the old hard safety rescue already independently authorizes a repair.

Added --groove-body-audition, requiring review, to render at most one independently runtime-verified alternate Vital bass candidate when its audited isolated-source upper-band energy fraction differs by at least +8 percentage points. This difference is a conservative compute-eligibility heuristic ONLY; it does not imply the new bass is better. The alternate uses exactly the same MIDI, kick, harmony, other patches, FX, fader gains, time grid and source provenance. Real native save/reopen and final true-peak/clipping gates apply. The candidate and original mix WAV are retained privately, and their sub and upper-bass ratios are compared. No automatic source winner is asserted.

The user previously said simply increasing bass level +3dB did not clearly improve the groove. Consequently this system does not boost all bass tracks, replicate Phase44 mixer gains, or force a particular Vital preset.

## Native independent three-prompt test

Three completely new source prompts were started sequentially in private experiment directory, no duplicate compute:
1. Deep D minor / 124 BPM / seed 118; warm rolling offbeats.
2. Jackin G major / 127 BPM / seed 217; syncopated funk with strong kick.
3. Straight A major / 125 BPM / seed 313; driving groove and wide chords.

Each opts in to Groove Identity V2, Musical Plan V2, verified sample-pack, contextual shortlist, additional groove-body source analysis/candidate audition and previously user-approved section-aware pad level calibration. The full native output must remain editable with a verified host save/reopen, zero clips, known CC0 samples, unchanged private licenses and a clearly marked music-quality listening gate. The original approved C balanced-pad variant and prior A/B songs remain immutable.

## STOP and acceptance

Never claim a source is musically preferable on spectral proxy alone. Retain original bass unless the user explicitly approves an independent matched-volume source audition. Run regression tests on source safety, mode preflight, envelope/frequency logic, no unintended auto-switch, legacy compatibility, source integrity and native export. If a prompt fails in the private pipeline, stop and report it rather than silently substituting weaker audio. Three new valid outputs do not, by themselves, certify studio-grade groove or producer readiness.

Status: implementation underway; actual native three-prompt receipts and listening archive to be added after verified completion.

 
## Completed three fresh native one-prompt outputs and quality gates

The complete three-prompt pilot finished with three independent **new**, verified native SoundCraft projects and 16-bar stereo 48-kHz/24-bit WAVs. All three confirmed native save/reopen equality, zero clipped samples and true peak below -1 dBTP. No previous source output or Phase44 reference was modified.

| Independent prompt | Key/tempo/seed | Actual Vital bass | Actual chord source | CC0 kick | Actual pad | Automatic pad attenuation |
| --- | --- | --- | --- | --- | --- | ---: |
| Deep | D minor / 124 BPM / 118 | Biow Bass 2 | string stabs | deep-01 | Strings of Cygnus | -12.000 dB |
| Jackin | G major / 127 BPM / 217 | Biow Bass 2 | WIP-D - Retro Piano | punch-01 | Strings of Cygnus | -12.000 dB |
| Straight | A major / 125 BPM / 313 | LD Bass | key to my heart | punch-01 | Strings of Cygnus | -9.927 dB |

Each song has a distinct generated bass note onset/duration/pitch-class fingerprint, different harmonic progressions and distinct native chord source identities. Two of three use the same bass and ALL three use the same pad: **source identity diversity remains inadequate** despite different genre and musical structure. The pad-level system found significant imbalances in all three, but there is **no listener approval** for the large attenuation in these new songs. This should NOT trigger automatic promotion to defaults.

### Actual native spectral groove evidence

Ratios are mean measured bass band energy in 100ms windows relative to the *same song's kick energy during the first 100ms following a kick*:

| Track | 25-90Hz early / late offbeat vs kick | 90-250Hz early / late offbeat vs kick | Bass late vs early, 90-250Hz |
| --- | --- | --- | ---: |
| Deep Dm | -15.79 / -9.62 dB | -16.13 / -7.08 dB | +9.05 dB |
| Jackin G | -14.17 / -11.13 dB | -8.64 / -2.89 dB | +5.75 dB |
| Straight A | -17.61 / -13.05 dB | -17.19 / -5.04 dB | +12.15 dB |

All candidate comparisons reported **SKIPPED_ALTERNATIVE_NOT_UPPER_BASS_DISTINCT**: the sole prequalified runner-up in each verified per-role-2 shortlist was not at least 8 percentage points richer in isolated 90-250Hz spectral proxy, or showed a decrease. Consequently, **no bass-source candidate A/B WAV was rendered and no bass source changed automatically**. This is the intended conservative CPU safety rule, but it demonstrates a larger algorithmic gap: broadening the *verified* source candidate pool is necessary before conditional native sound selection can materially improve groove on diverse prompts.

Raw full-song final mix measurements:
- Deep: -27.24 LUFS / -5.90 dBTP / 0 clips.
- Jackin: -28.04 LUFS / -5.63 dBTP / 0 clips.
- Straight: -26.89 LUFS / -5.34 dBTP / 0 clips.

Three native outputs were prepared as **gain-only** 16-bar listening excerpts at -24.169 LUFS each; true peaks -2.85, -1.80, -2.65 dBTP; no clipping. Private VPS archive: .local/gmi-v1-listening-20261114/Kuang_GMI_V1_Three_Songs.wav.zip. Verified external listening link: https://gofile.io/d/2NlZq7xV (temporary host retention; WAVs preserved privately). Private source outputs: .local/gmi-v1-deep-Dm-20261114, .local/gmi-v1-jackin-G-20261114, .local/gmi-v1-straight-A-20261114.

**Engineering test result:** 88 focused tests passed, including synthetic native 48k PCM signal tests, band/beat spectral change checks, strict source timeline validation, fail-closed CLI preflight and existing groove/harmony/pad/Source safety regressions. Algorithm code delivered in commit 83b8026. Native rendering passed for all three songs.

**Musical status:** NEEDS USER LISTENING. The new module can quantify and prioritize bass-pocket problems and safely propose a conditional A/B, but the three-song run did **not** demonstrate an accepted source-swap improvement. Keep new controls optional. Next priority: broaden suitable verified bass candidate selection across the original role catalog (without random diversity quotas), evaluate exact MIDI and register before release, render short native mix candidates, compare at matched loudness and only promote changes that repeatedly improve groove. Do not chase individual Dm/G/A song master settings or arbitrarily crank bass.
