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
