# Native Context-Aware House Source Fit — November 13, 2026

**Status:** implemented and verified against **two independent real-source test songs**, not yet a statistically calibrated producer-quality classifier. The engine operates on genuine **isolated native SoundCraft renders**, evaluated at **actual programmed kick onsets**. No full-song master, preset library or previously approved private track is changed.

## Why this exists

Earlier preset selection used independent Vital patch audition, semantic tags and isolated FFT ratios. Early mixed results exposed highly variable sub-bass/mid energy, high crests and some level inconsistencies. One standard kick, chord and bass gain target cannot reliably solve the interaction among **different house source combinations**. In particular, a transient kick's full-section RMS should not be equated to a sustained chord's RMS. Source compatibility should be checked *before* rendering a 4-minute song, over its original locked 8–16 bar groove.

## New reusable diagnostics

Module `kuang.house_source_fit`, integrated into the existing **diagnostics-only** `kuang.house_mix_roles` native stem audit. The input is a validated private session with exact native project and independently verified source assets, *three genuine SoundCraft role stems* (kick, bass, chords), and its independently verified full-mix WAV. Source and output WAVs are 48kHz/24-bit stereo with identical frame counts and fixed bar-time alignment. The code does not derive or redistribute third-party Vital states.

Computed evidence:

| Field | Interpretation |
|---|---|
| `bass_on_kick_vs_between_power_db` | Bass energy in 0–100 ms of actual kick onset versus 150–350 ms afterward, averaged over up to 16 verified MIDI-onset events |
| `linear_sum_kick_bass_sub_interference_db` | 23.4–117.2 Hz FFT energy of the **hypothetical sum of the native isolated** kick+bass stems versus the incoherent power sum, reported as signed dB. Negative = more cancellation in those windows; positive = constructive summing. It is **not** a substitute for native mix-bus measurement |
| `full_mix_sub_mono_retention_db` | Full-mix sub-band power retained in mid=(L+R)/2 compared with stereo-channel average; a negative number indicates potential **stereo low-end** loss on mono fold-down |
| `kick_early_peak_vs_late_rms_db` | Max kick amplitude during the first 35 ms of actual onset compared with its 35–120 ms body RMS. It is a source/FX transient descriptor, not a judgment of musical punch |
| `warnings` | Advisory, inspectable flags for severe cancellation, 6-dB mono low-end loss or bass activity unusually concentrated at kick onset. These are **review prompts**, not calibrated house-music quality laws |

All fields retain sampling algorithm assumptions, selected kick MIDI ticks, number of measured hits, source hashing from the already existing band evidence, and `perceptual_quality: NOT_EVALUATED`.

The path is executable with:

```bash
cd /home/User
# In a private workspace, preserving pinned host and optional private libs.
PYTHONPATH=/home/User/Kuang-groove-harmony python3 -m kuang.house_mix_roles \
  --source /home/User/Kuang/.local/kuang-generalization-batch-20261113/deep-Dm-124-s17 \
  --soundcraft /home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli \
  --out-dir /home/User/Kuang/.local/new-house-source-fit-audit \
  --diagnostics-only
```

Three native stems are rendered **serially**, exactly one 16-bar candidate per call. No additional private preset audition or full-length arrangement is required. The resulting JSON-only report is `band-diagnostics.json`, now containing `context_fit` and the previous fullband/FFT fields. Private rendered stems are discarded after analysis; only the source project remains.

## Two real native-source tests

| Measurement | Deep D minor, 124 BPM | Jackin F minor, 126 BPM |
|---|---:|---:|
| Actual kick onsets | 16 | 16 |
| Bass at kick vs. 150–350 ms later | **−10.316 dB** | **−4.846 dB** |
| Linear hypothetical kick+bass sub interference | **+0.061 dB** | **−0.006 dB** |
| Full mix mono sub-bass retention | ~**0.000 dB** | ~**0.000 dB** |
| Kick attack peak vs. body RMS | **+12.252 dB** | **+13.824 dB** |
| Automatic source-fit warnings | None | None |

These are real, separately rendered Vital + licensed CC0-drum native stems from different **independently prompted house tracks**, not invented profiles. Both have negligible observed destructive sub summation and mono-fold-down losses in the sampled windows, despite **~5.5 dB** difference in their bass-on-kick dynamics. That is evidence for **style-dependent source and sidechain behavior**.

Do **not** infer either source pairing is superior, automatically reduce the jackin bass by a fixed 5.5 dB, or claim both sound excellent merely because the warnings are empty. The original three-prompt batch already showed large differences in full-mix spectral balance and output loudness. Low-frequency compatibility is necessary engineering information but not sufficient musical quality.

Real reports were verified on the private VPS:

```
/home/User/Kuang/.local/kuang-generalization-batch-20261113/deep-Dm-context-fit-20261113/band-diagnostics.json
/home/User/Kuang/.local/kuang-generalization-batch-20261113/jackin-Fm-context-fit-20261113/band-diagnostics.json
```

## Technical tests and next steps

Synthetic tests deliberately construct **identical-phase and inverted-phase 60-Hz tones** to prove the analyzer distinguishes the +3 dB coherent addition from deep cancellation. Separate antiphase stereo tests verify that mid/mono fold-down truly detects loss; the end-to-end synthetic aligned native-format WAV regression checks multi-file time alignment, actual kick MIDI tick/sample conversion, and correct warning generation. Unsupported PCM formats and untrusted symlinks fail closed.

Future source selection should compare **several verified candidate presets against the same locked drum groove**, by bounded *native audition excerpts*. Re-use band and kick-event evidence to screen technical failures, then keep non-failing candidates available for actual musical comparison. Final selection requires stronger reproducible acoustic criteria and eventually a small portfolio of human-reviewed examples; until then, never use a made-up aggregate 'quality' rating or silently promote a single technical metric to a professional listening verdict.

The user is not required to listen to files on the VPS. Human review should be the **last accessible product test**, with audio actually playable in chat, after the system passes its repeatable technical and source-compatibility gates.
