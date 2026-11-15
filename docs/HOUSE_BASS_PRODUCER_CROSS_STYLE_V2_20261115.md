# Kuang Bass Producer V2 — approved C cross-style evaluation

November 15, 2026. Development branch only. Source preserving, no default change.

## Listener preference and experimental method

The user explicitly approved corrected same-host song #01 C with the verdict "C sounds great." Song #01 C used +2dB bass and shifted four original phrase-ending notes one sixteenth later. That preference is supported for #01 only, not a universal bass setting.

To test generalization, generated actual SoundCraft 16-bar A/B/C Grooves for two independent original 128-bar songs: #05 jackin C minor 126 BPM and #07 minimal Db minor 127 BPM. A is untouched. B applies a provisional +1.5dB source-aware bass gain and offsets the existing gain-envelope values equally, preserving envelope shapes. C applies B plus retiming TWO existing bass phrase-ending note onsets from step 14 to step 15 at bars 24 and 32. No new notes, pitch changes, kick changes, drum samples, FX or VST preset changes. All were real same-path native SoundCraft renders, with true-peak/no-clipping checks and actual alternate editable native session save/reopen. All originals and earlier negative experiments remain untouched.

New implementation: kuang/house_bass_producer_v2.py. It requires actual canonical-hash-matched native role-stem evidence, chooses a bounded audition gain (not a target balance) and records source verification and exact note movement. If there are no eligible original phrase pickups, it preserves the source notes rather than creating new ones. Three focused tests and 58 expanded regression tests passed. No automatic musical winner or global default.

## Song #05: jackin C minor, 126 BPM

Isolated bass vs kick RMS -7.098dB; provisional +1.5dB bass candidate; two existing note pickups moved, bars 24/32. Same native host render path, gain-only listening match -23.3276 LUFS, no limiting or clipping.

| Version | Native integrated LUFS | Native true peak dBTP | Matched LUFS |
| --- | ---: | ---: | ---: |
| A original | -26.9394 | -5.6118 | -23.3276 |
| B gain-only | -26.7611 | -5.6118 | -23.3276 |
| C gain + two phrase pickups | -26.7639 | -5.6118 | -23.3276 |

- A original: https://gofile.io/d/lQGx26i4
- B gain-only: https://gofile.io/d/cy3SroeW
- C gain and phrase: https://gofile.io/d/gECCzvdB
- Full three-audio WAV archive + measured evidence: https://gofile.io/d/ZmiiZEsZ

## Song #07: minimal Db minor, 127 BPM

Isolated bass vs kick RMS -8.600dB; bounded +1.5dB bass candidate; exactly two eligible original phrase pickups moved on bars 24/32. No change in bass-note density (original 2.5 notes/bar). Same native host render path, gain-only listening match -23.9586 LUFS, no limiting or clipping.

| Version | Native integrated LUFS | Native true peak dBTP | Matched LUFS |
| --- | ---: | ---: | ---: |
| A original | -27.1835 | -5.2249 | -23.9586 |
| B gain-only | -27.0961 | -5.2249 | -23.9586 |
| C gain + two phrase pickups | -27.0974 | -5.2249 | -23.9586 |

- A original: https://gofile.io/d/0sSRWjWb
- B gain-only: https://gofile.io/d/h00x498M
- C gain and phrase: https://gofile.io/d/l1G5SItZ
- Full three-audio WAV archive + measured evidence: https://gofile.io/d/rjiMNF1s

## Interpretation and stop gate

The changed bass volume has a modest effect on full-mix integrated LUFS; the late phrase pickups have almost none, as expected. Both styles have different rhythmic templates from approved #01, so do not transplant #01 notes or infer quality from objective onset count.

Only #01 C has an approved human listening verdict. #05 and #07 remain listening candidates. If the new C variants also win, generalize selectively to other musical contexts; if not, preserve the failure and reconsider bass source harmonics, transient dynamics, bass/kick masking and phrase vocabulary. The larger ambition remains an autonomous AI producer that exceeds ChordChord in sound quality and reliably delivers mixed/mastered editable full tracks.
