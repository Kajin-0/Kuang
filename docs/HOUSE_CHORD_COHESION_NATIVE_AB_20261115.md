# Kuang House Chord Cohesion: verified native A/B, November 15, 2026

User feedback: #05 jackin C minor 126 BPM chords sounded "wonky," likely the preset; #07 minimal Db minor 127 BPM chords seemed too loud. This was prioritized over further barely audible bass variations. Long-song sections, drums, bass, other instruments, native effects and MIDI remain immutable. Source originals and private Vital patch states were not overwritten.

## Song #05 — source-timbre test on same real MIDI

A: incumbent WIP-D Retro Piano (verified, original).
B: SNFKFutureBounce - Loaded Chords (independently verified on song #10).
C: minimal house dub stab 23 (independently verified on song #07).

The existing house_palette_compare.substitute function guarantees changed chord instrument ONLY, with exact MIDI, original static gain, effects, other roles, timeline and routing. All source libraries/plugins were catalog/sha matched. Exported alternate real SoundCraft native projects saved/reopened with matching canonical hashes. The original, B and C were bounced through identical real native 16-bar Groove A SoundCraft paths (48 kHz 24-bit stereo).

| #05 | Source native LUFS | Native dBTP | Clipped samples |
|---|---:|---:|---:|
| A Retro Piano | -26.939 | -5.612 | 0 |
| B Loaded Chords | -24.347 | -5.612 | 0 |
| C Dub Stabs | -26.370 | -5.612 | 0 |

All gain-only listening versions matched to approximately -23.328 LUFS. B's +2.592 LU change without MIDI or gain changes shows large source-output differences, NOT a demonstrated quality preference.

- [A original](https://gofile.io/d/AE8ZOsAB)
- [B Loaded Chords](https://gofile.io/d/UA9T89a6)
- [C Dub Stabs](https://gofile.io/d/oHFFchj2)
- [All three original PCM WAVs, matched, with evidence](https://gofile.io/d/bUBlFLGc)

## Song #07 — keep source and trim chord gain

The original minimal house dub stab 23 patch, its exact notes, effects, other instruments and full arrangement are locked. Audition A untouched, B chord fader -2 dB, C chord fader -3 dB. The new reversible bounded operation house_chord_balance_review_v1 preserves any existing automation shape by offsetting all relevant chord gain automation values, leaving every other automation point and MIDI note intact. This project has no chord fader automation, so its trial changes only the fader.

| #07 | Source native LUFS | Native dBTP | Clipped samples |
|---|---:|---:|---:|
| A original | -27.183 | -5.225 | 0 |
| B -2 dB chords | -27.641 | -5.225 | 0 |
| C -3 dB chords | -27.815 | -5.225 | 0 |

All gain-only listening versions matched to approximately -24.590 LUFS. No added limiter/compressor. Native SoundCraft exports and save/reopen passed, original project unaffected.

- [A original](https://gofile.io/d/8ZPbsJtd)
- [B -2 dB](https://gofile.io/d/RC9yIv8a)
- [C -3 dB](https://gofile.io/d/nWBLmzhU)
- [All three original PCM WAVs, matched, with evidence](https://gofile.io/d/0jerceKH)

## Validation and future work

- Same-host exact 16 bar native mix bounce for every candidate, native 48k/24-bit stereo PCM, zero clipped samples and true peak safely below -1dBTP. All source inventories/hash snapshots preserved. Four alternate editable private native sessions were verified. Exact source and audio receipts remain at Kuang/.local/house-chord-cohesion-AB-song05-20261115 and song07-20261115, including reproducible script Kuang/.local/house-chord-cohesion-AB-20261115.py.
- Added tests/test_house_chord_balance_review_v1.py (2 tests); expanded 45 test production/arranger regression suite passed.
- No automatic musical winner: human preference pending. If song05 B or C improves timbre, generalize actual note register, attack/release and chord-bass overlap evaluation to independently generated contexts, rather than hardcoding the preset. If song07 B or C improves balance, allow conservative gain adjustment only with prompt and section context.
- Next independent milestone: compare style-aware pre-drop withdrawal and restoration in the existing full arranger. Previous ten song matrix found Main Drop/Groove A fullmix RMS almost identical. Do NOT simply add fixed drop gain or implement new composer. Preserve current sound A/B results separately.
