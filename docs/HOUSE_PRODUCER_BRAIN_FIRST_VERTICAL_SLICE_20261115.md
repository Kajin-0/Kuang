# Kuang — staged producer brain: first real native review (November 15, 2026)

## User-specified architecture

1. Deterministic scaffold: key, BPM, song structure, groove/harmony, initial instruments.
2. Sensible common production: kick/bass pocket, basic EQ/dynamics, appropriate MIDI-kick-aligned sidechain, restrained panning, initial sound safety.
3. AI producer: inspect the actual generated song and full-mix/stems; form a source-aware hypothesis; audition bounded, undoable parameter/source changes in real SoundCraft; evaluate the effect and revise or reject it; proceed to section energy, stereo and real mastering only after the musical mix works.

The existing Kuang groove-template and full-song generation remain unchanged. This first slice adds a source-hash-bound producer-review protocol, real measured native context and safe edit proposals. It **does not yet embed a continuously operating LLM or perceptual audio judge**. In this first experiment ChatGPT supplied the producer reasoning; Kuang's private SoundCraft tools implemented and measured the candidates. A future provider/agent orchestrator must turn this into unattended one-prompt execution.

## Implemented code

New kuang/house_producer_review.py:
- diagnose: requires actual mix and reference measurements, produces evidence-linked hypothesis or no-change decision.
- candidate: reversible native wet-only chord send+filtered delay/room bus, or a second bounded chord-body/spread variant, with MIDI/kick/bass/FX source preservation.
- evaluate_candidate_effect: rejects a real native candidate with negligible measured improvement. No automatic aesthetic preference.
- revise_from_native_stems: conditioned on user prompt emphasizing harmony and previous failed parameter auditions, identifies a very recessed actual native chord role and recommends a verified source A/B instead of larger ungrounded gain boosts.
- producer_context_packet: instrument, effects, routing, full structure, automation, metrics and previous trials, without copying private Vital patch bytes.
- validate_producer_proposal: strictly validates a future model/human proposed action against immutable context fingerprint, actual evidence and bounded candidate choices; arbitrary DAW instructions or hallucinated controls fail closed.
- Seven new adversarial tests. Original SongSpec, main branch, Phase44, all ten full native source songs and private instrument files remain unchanged.

## Actual Phase44 vs generated song01 (first 16 bars Groove A)

Phase44 comparison uses actual 16 bars in its authored groove, not the same composition or mastering stage.

| Metric measured in real 16-bar stereo PCM | generated #01 | Phase44 |
| --- | ---: | ---: |
| 250Hz–1kHz / 30–250Hz power | -12.014 dB | -5.696 dB |
| 1–4kHz / 30–250Hz power | -15.671 dB | -5.737 dB |
| Stereo side/mid power | -37.874 dB | -17.570 dB |

First hypothesis: add one restrained high-passed chord-delay/reverb aux return with unmodified dry chords. Real native candidate A/B verified exact source MIDI, native save/reopen, zero clipping. Two variants moved 1–4kHz only +0.12 dB and side/mid about +0.05 dB. **Technical result: ineffective.**

Second hypothesis: increase dry chord +3 dB, add bounded spread plus the return. Real native 16-bar review moved 1–4kHz only +0.126 dB and side/mid +0.58 dB. Also insufficient. Both negative results were retained, not promoted.

Third hypothesis: measure isolated actual SoundCraft role audio, not just the fullmix.

| Isolated real native source, same Groove A | RMS | Sample peak |
| --- | ---: | ---: |
| Kick | -29.64 dBFS | -5.65 dBFS |
| Bass | -36.06 dBFS | -15.10 dBFS |
| Harmony | **-64.07 dBFS** | -45.88 dBFS |
| Hats | -49.40 dBFS | -20.81 dBFS |
| Snare | -44.99 dBFS | -22.99 dBFS |

The original "string stabs" Vital chord source is -34.43 dB RMS relative to the kick. The pad was deliberately absent in Groove A, therefore its silence is not a defect. The user's actual song01 prompt requests *wide sustained chords*, so the chord output deficit justified auditioning more appropriate, already-verified source states before further effect moves.

Fourth hypothesis: retain ALL source song01 F-minor MIDI, kick/bass/drums, sends, static faders, EQ, other FX and arrangement. Replace ONLY the chord instrument with the verified Vital patches already used in independent native songs 10 or 03, from the same vetted library and pinned plugin. The existing house_palette_compare.substitute enforces unchanged MIDI, controls, effects and layout. Real SoundCraft native save/reopen and sample-accurate 16-bar bounce passed for both donors.

| Actual 16-bar, same MIDI/FX/gain | Original string stabs | Loaded Chords donor #10 | Retro Piano donor #03 |
| --- | ---: | ---: | ---: |
| 1–4kHz / 30–250Hz | -15.671 dB | **-6.889 dB** | -13.770 dB |
| 250Hz–1kHz / 30–250Hz | -12.014 dB | **-4.148 dB** | -8.790 dB |
| Side/mid | -37.874 dB | **-22.214 dB** | -28.832 dB |
| Native true peak | no clipping | -5.637 dBTP | -5.637 dBTP |
| Host save/reopen | verified | verified | verified |

The Loaded Chords patch changes midrange +8.78 dB and side/mid +15.66 dB relative to the original. This is a substantial *real audio change*, not guaranteed improved musical taste. The three groove excerpts are gain-only matched to approximately -23.278 LUFS without any limiter.

## Listening package and acceptance

- [Original A: string stabs](https://gofile.io/d/s3hJKQOI)
- [Candidate B: Loaded Chords](https://gofile.io/d/xJ3OsNVv)
- [Candidate C: Retro Piano](https://gofile.io/d/9rRElP0N)
- [All three native WAVs and evidence](https://gofile.io/d/NMpmh8oP)

Original source session, earlier failed wet-only versions and both editable alternate native sessions remain in separate private VPS locations. Third-party patch component states were not shared publicly.

**Perceptual decision pending.** User chooses whether B/C fits the song better, not the spectral-score script. If B is genuinely better, generalize the bounded source audibility/prominence gate across two independent songs, then implement mix-aware section development and optional verified native mastering. Do not swap all chords to one patch, apply a fixed Phase44 compressor, or declare an AI music judge operational.

This experiment is proof of the intended production-decision workflow: deterministic scaffold, modest conventional mix, AI-style analysis of real music, falsifiable parameter proposals, rejection when ineffective, native role inspection, revised source choice, and controlled A/B.
