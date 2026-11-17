# Kuang: Low-end and syncopated pocket native experiment — 2026-11-15

## Goal and decision context

The producer preferred the chord-phrase coherence **B**, but explicitly reported the low end and pocket felt weaker than the previous best House demos. This experiment keeps the preferred chord phrase candidate, vetted source presets and all non-bass tracks immutable, while testing bass-body recovery with bounded, independently verified SoundCraft native renders. Do not interpret a meter as human subjective preference.

## Private baseline and sources

- Experimental source: `Kuang/.local/gmi-v1-jackin-G-20261114` (16-bar 127 BPM jackin house, `groove_identity_v2`), and its chord-B candidate in `.local/phrase-coherence-groove-v2-ab-20261115/candidate-native`.
- Base canonical SHA256 `d132641726c51d56206a993d3c041439ea1619dfd72afc5a86d98f17c857f623`.
- Frozen external comparison: `Kuang/.local/phase44-experiment/release/B-Phase44-native-club-master.wav` (118 bars, 126 BPM), which is a **mastered, different-source and different-key production**, not a level-matched stem baseline.
- All variants are private immutable derivations, rendered with SoundCraft 0.11, private vetted Vitalium and sampler assets. Neither original sessions nor third-party patches were overwritten.

## Controlled candidates

| Candidate | Bass fader change | Bass note body | Bass MIDI onsets | Native save/reopen | Premix LUFS-I | True peak | Clipping |
|---|---:|---|---|---|---:|---:|---:|
| A: chord B + groove-v2 original | 0 dB | Original | Original | PASS | -28.044 | -5.634 dBTP | 0 |
| B: chord B + +3 dB bass | +3 dB | Original | Original | PASS | -27.563 | -5.634 dBTP | 0 |
| C: chord B + +3 dB bass, longer body | +3 dB | All 40 bass notes lengthened ~20% | Original | PASS | -27.536 | -5.634 dBTP | 0 |
| D: chord B + +6 dB bass | +6 dB | Original | Original | PASS | -26.766 | -5.634 dBTP | 0 |

The +3/+6 dB changes apply to the bass track and its own mixer-gain automation, preserving the duck envelope's relative gain shape. The 20% length variant is a separate, controlled test; it does not generate extra MIDI events or retime kick/bass attacks. The output peak staying unchanged is explained by kick dominance; this does not imply arbitrary boosts are safe.

## Prior-reference metric: beat vs offbeat, not a grade

A previously used audit samples 4096-sample (~85.3 ms) Hann/FFT windows just after onbeat kick arrivals and at half-beat offbeats over sixteen beats, measuring a 23–129 Hz band. The quantity is 10log10(onbeat/offbeat band energy). Lower ratios here mean greater *relative* offbeat low-band energy, not universally superior House. Same previous script, same window specification, no arbitrary post-hoc frequency split.

| Reference/candidate | Onbeat/offbeat 23–129 Hz | Onbeat/offbeat 140–492 Hz |
|---|---:|---:|
| Phase44 mastered, bars 32–35 | +1.629 dB | -8.389 dB |
| A original groove-v2 + chord B | +9.420 dB | -3.099 dB |
| B +3 dB bass | +6.841 dB | -4.757 dB |
| C +3 dB bass and longer notes | +6.881 dB | -4.327 dB |
| D +6 dB bass | +4.313 dB | -6.713 dB |

The +6 dB variant closes roughly 5.11 dB of the initial 7.79 dB measured gap in the low-band *ratio*, a directional change consistent with more offbeat bass body. The +20% duration candidate did not improve this ratio relative to +3 dB alone. The Phase44 master uses different sounds/arrangement/dynamics; DO NOT blindly optimize to match its number.

## Listening files: aligned LUFS, no processing other than gain

All four source WAVs were independently attenuated (no compressor, limiter, EQ or sample replacement) to -28.250 LUFS-I as separate 48 kHz/24-bit stereo PCM listening derivatives, checked to true peak ≤ -1 dBTP and zero clipping:

- [A original groove-v2 bass + preferred B chords](https://gofile.io/d/EyGtRBcJ)
- [B bass +3 dB](https://gofile.io/d/0z8aUO6Y)
- [C bass +3 dB + 20% note length](https://gofile.io/d/BeURUrB5)
- [D bass +6 dB](https://gofile.io/d/dEKvwEgo)

The common loudness is deliberately below typical finished masters because the calibrated native comparison workflow uses attenuation only. Increase monitoring volume consistently as needed. All original results and evidence remain on the user's VPS in `Kuang/.local/groove-bass-causal-ab-20261115`.

## Research applicability

The prior user-supplied House production research reported 179 participants in 20 original House excerpts and greatest groove ratings in strong low-frequency amplitude plus high bassline syncopation; moderate rhythmic complexity and a stable macro-grid have broader support, but random humanization has weak support. The newer dataset report identifies research-grade isolated drum references (IDMT), high-grade royalty-free House one-shots (MusicRadar, Samples From Mars), CC0 Freesound candidates and empirical HOTGAME features; their licensing and historical boundaries must be preserved.

## Engineering conclusion and stop gate

1. Chord B is the producer's selected chord-rhythm treatment; keep it.
2. The primary observed regression source was using an older 16-bar test session with a different kick and bass groove rather than the later `groove_identity_v2` source.
3. Original generator low-band beat/offbeat energy is strongly kick-dominated relative to the approved Phase44 audio. The **+6 dB** trial produces a meaningful directional improvement without clip/peak failure, but it is **not automatically approved**: bass could be excessive in a long-song arrangement and on full-range playback.
4. Increased MIDI note lengths yielded little additional low-band ratio improvement in this single song; do not elevate it to the default.
5. Next mainline engineering work: implement an audio-measured offbeat energy and kick/bass balance gate on multiple source/preset/keys, with bounded one-parameter source/gain selection and mono/phase checks. No arbitrary global +6 dB on all songs without native multi-song validation.
