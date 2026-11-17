# Kuang House — single-cause bass timing test on the failed deep E seed

**Date:** November 16, 2026 UTC. **Experiment:** source-aware bass/Kick coordination after the frozen one-prompt three-style batch returned 1/3 successful productions.

## Question and source reconstruction

The previous fresh one-prompt deep E minor seed 41 failed closed because its independently sandbox-verified gentle-pluck alternative did not pass the **actual native full-mix two-band offbeat improvement gate**. Test the narrowly defined hypothesis: could a small anticipation of the *existing* bass-note attacks resolve this rejection without changing kick, chords, bass timbre, bass note content or native FX?

The failed one-prompt run intentionally did not publish a native session. Consequently the experiment used **a separate controlled reconstruction**, not an exact replay of its calibrated output. The reconstruction used the same frozen prompt/seed, original `rules_plan + enrich_house_spec + house_template` implementation, profile `deep`, original `groove_identity_v2`, `phrase_stable_chords_v2`, the same privately audited CC0 house-core drum policy, and **the exact SHA256 bass/chord/pad preset identities** recovered from that seed's verified isolated palette receipt. Existing private native sessions supplied these identical pinned Vital patches. No preset names or raw preset/audio bytes were uploaded or committed.

The three reconstructed private canonical native SoundCraft 0.11 / Vitalium sessions:

- **A:** Biow Bass 2 from original seed-41 palette; unchanged generator bass timing.
- **B:** independently native-verified gentle pluck bass; unchanged MIDI/timing (one variable: bass patch).
- **C:** B's *identical patch*, all other instrument states and every pitch, velocity and note duration, but principal bass note attacks in Groove and Drop each shifted **120 ticks earlier** at 960 PPQ, **60.98 ms at 123 BPM**. This affects **24 existing notes**, with unchanged note count. Intro/breakdown and phrase-end pickups unchanged. The four-floor kick, chord-B rhythmic timing, source effects, gain staging, track automation, and complete song sections were locked.

These are **unmastered lower-gain reconstruction renders** (integrated loudness approximately **−33 LUFS**, true peak **−13.866 dBTP**), not the original failed production's premix gain calibration. **Do not compare their absolute loudness to the previous batch**. The *matched baseline/candidate relative measures* are the valid causal evidence here.

Each variant passed actual separate SoundCraft native export/save/reopen with canonical identity, full real 48k stereo PCM24 render with release tail, zero clipped samples, ≤−1 dBTP, native isolated bass and kick stems, phase/mono diagnostics, and unchanged source inventory. These are actual waveform measurements, not simulated mix estimates.

## Results

| Actual native variant | 25–90Hz fullmix beat/offbeat | 90–250Hz fullmix beat/offbeat | Isolated bass onset hard fault? | Source rescue result |
|---|---:|---:|---|---|
| A original Biow Bass 2 | +10.241 dB | +8.928 dB | **Yes** | Technical baseline deficient |
| B gentle pluck / intact timing | +6.731 dB | +7.978 dB | None | **Rejected:** only 0.950dB improvement in 90–250Hz |
| C gentle pluck / notes 61ms early | +5.396 dB | +8.470 dB | None | **Rejected:** only 0.458dB improvement in 90–250Hz |

Relative to A:
- B reduces the 25–90Hz ratio by **3.510 dB** and 90–250Hz ratio by **0.950 dB**; the native fullmix gate requires **≥1.000 dB in each band**.
- C reduces the 25–90Hz ratio by **4.845 dB** but 90–250Hz by **0.458 dB**. Compared **directly to B**, shifting the bass earlier *worsens* the 90–250Hz on/offbeat ratio by **0.492 dB**, while improving the sub-band ratio by **1.335 dB**.
- Neither candidate shows a new hard native note-onset fault, and the independent phase/mono gate reported no destructive cancellation warnings.
- The near-kick fullmix band power changed minimally versus A (**−0.213 and −0.009 dB** for both B/C), so the apparent sub-band benefit is not simply a weakened kick. The 90–250Hz absolute offbeat-energy gain versus A fell from **+0.941 dB in B** to **+0.449 dB in C**, explaining why C fails more decisively than B.
- The 1.000dB pass threshold was NOT relaxed because B missed it by just 0.050dB; the threshold remains provisional, not a validated perceptual-optimum value.

## Engineering decision and stop gate

**Reject fixed −120-tick bass-note anticipation as a global or deep-house default.** This is a concrete negative *independent audio* test, not a successful new composer feature, and therefore does not authorize automatic note rescheduling in Kuang.

The discrepancy is specific: the source swap clears isolated attack defects and increases low sub-band energy, but **the higher 90–250Hz offbeat-body response remains insufficient**. The controlled earlier-onset adjustment makes that body-band response worse.

The appropriate next discriminating test is source-aware **90–250Hz harmonic/body content** and the actual ducking/recovery envelope under an unchanged note grid, with narrow hypotheses and untouched kick/chords. Stop repeating timing shifts without independent signal evidence. One source context alone cannot establish general musical quality or determine a human listener's preference.

## Repeatability

Private generated artifacts and full numerical evidence reside at:
`/home/User/Kuang/.local/causal-deep41-onset-anticipation-20261116/complete-native-v1/`

The reproducible reconstruction driver lives privately at:
`/home/User/Kuang/.local/causal-deep41-onset-anticipation-20261116/run.py`

The source-anonymous, no-private-preset numerical fixture is committed as:
`tests/fixtures/house_deep_E41_native_timing_counterexample_20261116.json`

`tests/test_house_bass_fullmix_repair_v1.py` re-evaluates both actual native candidates against the existing strict production gate and asserts the counterexample cannot silently become an approved source repair. The source files and mixer defaults are unchanged; no end-user listening requested.
