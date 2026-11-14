# Low-end groove-pocket diagnostic and bounded native experiment — Nov 14, 2026

## Why this gate precedes further harmonic development

The user accepts recent harmony-plan and interlock improvements but explicitly says newer autonomous mixes still lack the **physically felt low-end groove** established through the original Phase44 production and the Suno reference. The engineering response is **not** to rebuild Kuang, increase every kick, or copy a reference preset. Preserve all existing Kuang modules, one-prompt SongSpec, certified private Vital/CC0 source handling, SoundCraft, earlier MIDI, Phase44 approved audio and the current Musical Planning V2 output. This gate only evaluates an existing mix.

The Suno reference original MP3 and five-stem source have a prior complete report, `Suno_Stem_Production_Audit.md`, also described in `docs/HOUSE_SUNO_PHASE44_GROOVE_PRIORITY_20261114.md`. Historical notes indicate an approximately 126 BPM kick, frequent bass onsets about half a beat after the kick, focused low-frequency mono and complementary sub/upper-bass contribution. These are **descriptive properties, not targets automatically imposed on unrelated songs**. The original Suno MP3/stems were **not newly located and decoded for this exact experiment**; do not characterize the current ratio measurements as direct Suno-vs-Kuang waveform measurements.

## A new cheap native full-mix pocket measurement

New additive module `kuang/house_groove_pocket.py`, exposed as optional `--groove-pocket-diagnostics` in the existing private `autonomous_create --groove-template` pathway. It operates **after** the established native WAV render and safety checks. No source/FX/MIDI/engine parameter is adjusted, and the existing default generator is untouched.

For actual MIDI kick positions in a recognized active Groove section, it reads 48 kHz, two-channel, 24-bit PCM. For each kick it calculates Hann-windowed FFT band energy for two equivalent-length windows (first 100 ms and 200–300 ms after kick). Report bands: 25–90 Hz and 90–250 Hz. Reported quantity is:

`10 log10(mean near-kick band power / mean offbeat band power)`.

Positive means kick-position energy exceeds offbeat-position energy **in the full mix**, not that the kick stem itself is louder. Negative means offbeat energy predominates. The estimator is not a bass-stem isolation, a perceptual groove metric, or a calibrated psychoacoustic score. The finite FFT window, masters, chord content, section length and melody can all affect it. It uses the repository's existing **standard-library** FFT/PCM tools and does not add NumPy or SciPy as mandatory dependencies. Every report carries `perceptual_quality=NOT_EVALUATED`.

## Existing real WAV results (no edits)

| Source | Groove-section 25–90 Hz near kick / offbeat | 90–250 Hz near kick / offbeat |
|---|---:|---:|
| Original approved Phase44 native club master | +4.329 dB | −6.228 dB |
| Listener-preferred source pair D, real matched 4-bar excerpt | +8.717 dB | +5.410 dB |
| Independent E-major deep-house Musical Plan V2 | +15.293 dB | +4.737 dB |
| Independent B-flat jackin-house one-prompt mix | +14.525 dB | +7.593 dB |

These compare technically different releases and passage positions. They are **observational, not a causal proof** that a specific source, gain or parameter produces a better groove. Nevertheless, the large differences between strong human-approved Phase44 offbeat 90–250 Hz and the two recent autonomous outputs are credible evidence to justify a specific controlled experiment.

## Controlled native counterfactual

Test **the two independent generated E-major deep / B-flat jackin mixes**, never just the old C-minor D test. Keep complete original MIDI, source identities, kick/hat/chord/pad/FX, time map and native SoundCraft structure unchanged. Render a bounded **bass fader +3 dB** counterfactual to test whether extra bass presence reduces the measured transient/offbeat imbalance, without asserting that +3 dB is universally correct. Bass gain automation tracks the same shift. Preserve original render as the incumbent. If it clips, destroys native roundtrip, changes secure source identity, or worsens listener groove, reject this candidate.

Run this experiment as a **private script under .local**; it is not wired as an automatic one-prompt bass adjustment and must never become a default just because spectral ratios shift. After both native projects pass source/provenance and PCM checks, compare gain-only matched active 8–16 bar WAVs through listening.

Next experiment, if simply raising bass does not help: a small, bounded **real kick/bass source-pair and note-envelope** audition at actual generated notes/registers, using the existing house_native_pair_audition and source-fit tools. Avoid a Suno-style fixed mix curve or any hard-coded Phase44 fretboard/MIDI recipe.

## Technical tests

New `tests/test_house_groove_pocket.py` runs three tests: deterministic near-equal bandpower for constant input, negative ratios for controlled stronger offbeats, and fail-closed invalid section/WAV/window. All tests are signal-processing checks, **not musical approval**. Existing house template/autonomous source tests also continue to run.

**Acceptance:** a substantially stronger low-end groove across at least two independent one-prompt songs, as judged at matched loudness by the user. Recording another passing metric or a successful PCM render does not close the music-quality gate.
