# Kuang opt-in four-bar chord phrase coherence V2

Date: 2026-11-15. Branch: feat/phrase-coherent-chords-v2-20261115.
Status: symbolic implementation; native listening benefit NOT VERIFIED.

## Experimental hypothesis

The earlier groove-interlock chooses a new chord-stab pattern independently for each bar. A fixed four-bar phrase pattern may better support a repeating bass motif. This does not establish superior musicality: cohesive repetition and variety depend on musical context.

## Implemented scope

- New module kuang/house_phrase_coherence_v2.py: source-preserving, copy-on-write regularizer.
- Existing house_template.template accepts phrase_stable_chords_v2=True.
- Private autonomous_create CLI offers --phrase-stable-chords-v2, explicitly requiring --groove-template and --groove-impact.
- Only actual chord MIDI onset ticks may change. Chord pitches, velocity, duration, strum, instruments, FX, sends, other-role MIDI and all source assets are invariant.
- The four-bar candidate cannot increase near-simultaneous chord/bass attacks within 80 ticks relative to the established barwise interlock; rejected phrases retain legacy timing.
- Every decision is recorded with source/candidate hashes and NOT_EVALUATED quality status.
- Legacy/default output is unchanged; no PR merge or main-branch changes.

## Verification plan

Stage A: Cross-profile symbolic tests on eight keys/styles/seeds, exact other-role preservation, replay, invalid flags, source immutability and 128-bar arranger structural gates.

Stage B (not yet run): On a private pinned SoundCraft/Vitalium runtime, generate the same jackin G-major nucleus and complete 128-bar song with/without this opt-in. Compare native session save/reopen, full MIDI, sections, FX, routing, instruments, zero clips, -1 dBTP or safer, and gain-only matched 8-16 bar Groove and Main Drop excerpts. Preserve the original and the rejected experiment.

Stage C (not yet run): Listener verdict on chord/bass cohesion and 4/8-bar flow. If the candidate is musically worse, keep the old source. If better, test a second independent style/key before any general adoption. Do not mistake a lower rhythmic-collision metric for a professional-quality score.

The user-chosen song #05 chord patch A and song #07 provisional source-preserving -2 dB chord adjustment are outside this experiment and must not be replaced automatically.

## Actual private native A/B: November 15, 2026

Status: native validation PASSED; perceptual quality not evaluated. This
does not count as 128-bar or cross-style validation.

Source: existing independent 16-bar 128-BPM jackin-house G session.
Native host: pinned SoundCraft 0.11, private verified Vitalium and sampler
states, stereo 48 kHz PCM24. The original project and sound sources were
not overwritten. All outputs were placed in a fresh private directory.

- Original canonical SHA256: 0c06a198fea62961aa2cc5006f17e614fe12ec80ca9e3e5ab5d78de42d9edfb0
- Candidate canonical SHA256: 08b4e75c95623dea9b8af1adabc71225eed757028a9325b1972307581e450d7d
- Modified chord voice onsets: 33 in 2 accepted four-bar groups.
- Bass, drums, chord pitches, gates, velocity, patches and FX: unchanged.
- Chord/bass collisions inside 80 MIDI ticks: 0 originally and 0 candidate;
  this metric showed no improvement and is not evidence of better sound.
- Native export, save/reopen and canonical hash inspection: PASSED.
- Native WAV length: 42 seconds; no clipped samples.
- Original A loudness: -22.273835 LUFS; true peak -5.528280 dBTP.
- Candidate B loudness: -22.254244 LUFS; true peak -5.528280 dBTP.
- Gain-only A/B target: -22.373835 LUFS.
- Applied A gain -0.100000 dB; B gain -0.119591 dB.
- Playable matched PCM24 listening files:
  https://gofile.io/d/DsDvqZvK
- Private VPS results directory:
  /home/User/Kuang/.local/phrase-coherence-native-ab-20261115
- Updated local focused module: 7 tests PASS in 8.16 seconds.

Decision: retain incumbent as default, leave PR in draft, do not claim
musical preference or automate promotion on technical scores alone.
