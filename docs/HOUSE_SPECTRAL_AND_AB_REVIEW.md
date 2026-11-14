# House Mix: Frequency-Resolved Diagnostics and Matched Listening

**Status:** opt-in engineering instrumentation, **not** an automated professional-quality detector or finished house master. The user-approved Phase43/44 private song remains untouched. See [role calibration](HOUSE_MIX_ROLE_CALIBRATION.md) and [producer-ready product contract](PRODUCER_READY_TEMPLATE_PRODUCT.md).

## Why the old metric is inadequate

The original role-calibration experiment treated the entire Groove-section RMS of **a transient four-to-the-floor kick** as numerically comparable to the full-window RMS of **sustained chords**. Its provisional rule expected chord RMS to be -7 dB relative to kick RMS. On a real private 16-bar template, the chords were +5.52 dB over the kick and a bounded -4 dB move could not satisfy the provisional criterion. **That is not proof the chords are perceptually too loud.** It is evidence the metric alone cannot diagnose time/frequency masking.

Do **not** double the attenuation, run a global maximizer, or assert that the sound was fixed from this number. Groove and sound compatibility must be considered in timing and spectral context; default fader targets are merely conservative starting hypotheses.

## New spectral measurement: `kuang.house_mix_spectrum`

The module takes the **actual rendered 48-kHz/24-bit stereo WAV of one instrument**, and measures the **named, active Groove section**, with 4096-sample Hann analysis windows (11.72 Hz bin spacing), averaged over both channels. Sampled spectra use explicit window-power normalization; the output reports absolute RMS dBFS for:

| Band | Frequency | Intended engineering question |
|---|---|---|
| Sub | 20–120 Hz | Relative kick/bass sub energy; possible overlap and excessive fundamentals |
| Bass body | 120–500 Hz | Mid-bass audibility vs lower chord energy |
| Midrange | 500–2000 Hz | Bass upper harmonics versus chord body |
| Presence | 2000–8000 Hz | Chord attacks versus hats/claps and clarity |
| High | 8000–24000 Hz | Transient brightness and effects tails |

No band value proves perceptual masking. In particular, mono cancellation, onset alignment, frequency-dependent dynamics, playback-system translation, and bus nonlinearities require additional dedicated checks.

The named numerical diagnostics compare **bass versus kick within the sub band**, **chords versus bass in body and mid bands**, and **the fraction of chord power below 120 Hz**. They are explicitly marked `quality_improvement_established: false`.

### Bounded diagnostics-only native run

```bash
python3 -m kuang.house_mix_roles \
  --source .local/kuang-groove-sample-vital-five-hat-20261113 \
  --soundcraft /path/to/verified/soundcraft-cli \
  --out-dir .local/new-house-spectrum-audit \
  --diagnostics-only
```

This runs at most three isolated-role SoundCraft native renders, computes independent source-hashed role spectra, and outputs **one report**, `band-diagnostics.json`. It does not publish any new mix, modify the original project's notes or instrument states, or rerun private preset selection. Use an explicit shell timeout and low scheduling priority on a busy VPS.

## New loudness-matched A/B review: `kuang.house_mix_review`

This is the immediate producer-facing test, to determine if the role-calibrated candidate actually sounds preferable to the original at equal listening loudness:

```bash
python3 -m kuang.house_mix_review \
  --original .local/kuang-groove-sample-vital-five-hat-20261113/preview.wav \
  --candidate .local/kuang-groove-role-balanced-20261113/premix/output.wav \
  --out-dir .local/new-house-mix-listening-ab \
  --library .local/producer/libebur128.so
```

The two input files must have **exactly matching sample rate, channel count, bit depth, and frame count**; neither is resampled or time-shifted. Both are independently **attenuated** to 0.1 LU below the quieter source via Kuang's existing `match_lufs` engine, and equality is confirmed within 0.01 LU. Three files are published in a private new folder: `original-matched.wav`, `candidate-matched.wav`, `ab-evidence.json`. The evidence contains source hashes, LUFS/TP measurements, gain adjustments and a sample-aligned PCM difference check. No subjective preference is assigned and files cannot be treated as an endorsement of the candidate.

### Verified private A/B on November 13, 2026

The exact original/candidate private 16-bar render pair was prepared successfully. Both matched to **-25.9459315 LUFS**; the original was attenuated **-0.1000 dB**, and the candidate **-2.8618 dB**. Files are private at:

`/home/User/Kuang/.local/kuang-house-mix-ab-20261113/`

The result is **`NEEDS_LISTENING`**. Do not let loudness, source freshness or engineering targets substitute for actual listening preference.

## Next automation work

1. Compare alternative sources **over the same locked kick/bass/chord MIDI** with identical loudness, and collect user acceptance/rejection reasons, not fabricated quality scores.
2. Use measured band ratios and actual onset/decay profiles to propose conditional EQ or gain changes; keep every correction reversible and small.
3. Evaluate mono low-end interaction and kick/bass temporal overlap; separately handle percussion brightness versus chord transient masking.
4. Implement **native premaster and distinct master-preview** packaging once acceptable mix balance is established. Don't force any one LUFS level on all house arrangements.
5. Preserve the editability of sampled instruments, original Vital states, MIDI, FX, automation and section markers.

### Verified native spectral result — November 13, 2026

The diagnostics-only code rendered three real isolated SoundCraft/Vital streams from the **unchanged private 16-bar house template**, under a bounded low-priority process while another VPS task was heavily consuming CPU. It returned `NEEDS_LISTENING` and an actual source SHA in `band-diagnostics.json`.

| Role | 20–120 Hz RMS | 120–500 Hz RMS | 500–2000 Hz RMS | Share of energy below 120 Hz |
|---|---:|---:|---:|---:|
| Kick | -39.03 dBFS | -55.28 dBFS | -79.86 dBFS | 97.67% |
| Bass | -39.17 dBFS | -46.36 dBFS | -58.51 dBFS | 83.15% |
| Chords | -68.19 dBFS | -34.52 dBFS | -36.03 dBFS | 0.02% |

**Differences:** bass vs kick in 20–120 Hz: **-0.14 dB**. Chords vs bass: **+11.84 dB** in 120–500 Hz and **+22.48 dB** in 500–2000 Hz. This is *source spectral power*, not proof of musical dominance: equal time windows, sub-band FFT leakage, note density and transient variation matter. But it does make the likely engineering issue clearer: **a very sub-heavy kick and bass combination with little upper-bass articulation**, while the chords provide the lower mids and mids. This should motivate **alternate kick transient and bass preset audition** before blindly turning down chords. The provisional old -7 dB full-band chord-vs-kick target is therefore **not an appropriate automatically enforced quality gate**.

**Safe default changed:** `kuang.house_mix_roles` now defaults to `--diagnostics-only` behavior. The older full-band fader calibration is retained for reproducibility but requires an explicit **`--apply-fullband-heuristic`** option, and still reports `NOT_MET` when its own residual goal fails. No default automatic fader move is made without stronger evidence.

Private measured spectral file: `/home/User/Kuang/.local/kuang-house-spectrum-audit-20261113/band-diagnostics.json`.

**Safety/privacy:** the stereo previews contain unknown-license third-party Vital patch states and remain in the authorized user's private .local directories, not GitHub. This research produces new original code and documented metrics only.
