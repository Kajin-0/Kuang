# House harmony interlock: generalization-first production gate (2026-11-14)

## The actual target

Kuang must produce **multiple distinct, professionally convincing house songs from independent one-prompt requests** with editable SoundCraft sessions. The user preferred candidate D (Deep-01 kick + Bass - Insanity) among four C-minor source pairs; this is useful *local listening feedback*, **not** a mandate to hard-code those samples or the C-minor chord layout in other productions. Phase 44 remains a stronger mix benchmark, not a song to copy.

## Why chord placement needs to be context-dependent

The source composer places some chord transients on the same offbeat as bass notes. Merely applying common fixed EQ, reverb, or a universal +240-tick shift can make a mix worse. Instead, this opt-in stage examines each already-generated bass MIDI grid and selects a chord-stab rhythmic pattern within the existing bar and harmonic progression.

New module: `kuang/house_harmony_interlock.py`, called from `house_template.template(..., impact_pocket=True)`. Existing `--groove-impact` one-prompt workflow invokes this stage automatically; `harmony_interlock=False` preserves the original chord timing as a rollback control.

This is not an AI critic or auditory model. It is an explicitly bounded *music-structure heuristic* whose outputs need listening approval.

## Transferable policies, not one-song knobs

- Four separately defined rhythmic families for deep/straight/jackin/minimal house. Candidate choice varies by user prompt style, actual bass onsets, bar and generation seed. The same approved preset or tonic is **not** required.
- Preserve all chord pitch classes, individual pitches, voices, original durations, channel and velocity; retain the chord harmonic progression.
- Preserve all bass, kick, snare, hats, percussion and pad MIDI; do not alter instruments, source presets, EQ, compressor, spatial processing, faders or sends.
- Reposition only existing grouped chord attacks, preserving intra-chord strum offsets. Keep chord notes in their original bar and clip; reject impossible bounds rather than silently truncate.
- Compare bass/chord attacks within a 80-tick proximity (~42 ms @ 126 BPM), then near-miss within 155 ticks. Select among *intentionally authored musical rhythms*, not arbitrary timing shifts. Tie-breaking varies by bar and seed.
- Report both collision counts and a MIDI fingerprint, but declare perceptual quality `NEEDS_LISTENING`, not a certified improvement.

## Independent tests and native checks

Regression tests in `tests/test_house_harmony_interlock.py` include 8 distinct style/key/tempo/seed cases:
deep/C minor/126/43; straight/A minor/125/41; jackin/F minor/129/51; minimal/G major/122/17; deep/E major/123/67; straight/D minor/128/19; jackin/Bb major/124/83; minimal/F# minor/127/29.

The suite checks deterministic regeneration, different chord MIDI fingerprints, non-identical rhythm-pattern choices, preserved instrument graph, unchanged rhythm-section notes, unchanged chord voicings and strums, and integrity/validation gates. No one style, key or seed constitutes the only tested result.

Two private *real SoundCraft 0.11.0 + verified Vitalium* controlled studies used previously generated independent music:

1. **Deep C minor, 126 BPM:** the user's preferred source pair D (Deep-01 + Bass - Insanity), only chord timing changed.
2. **Straight A minor, 125 BPM:** independent earlier source pair, only chord timing changed.

Both revised native projects saved/reopened and rendered without clipped samples or hash drift. Original and revised 4-bar Groove excerpts are normalized to the **same −17.5 LUFS** (gain-only, no added limiter); original recordings are retained. These examples are not independent new one-shot runs and **do not establish professional-quality audio**.

## Strict next acceptance gates

1. Compare the matched clips against each other and Phase 44. If the new chords sound artificial or obscure the bass, roll back the interlock for that style; do not stack unrelated FX changes.
2. Generate at least one *fresh* independent one-prompt result in another key/style, with source selection, native SoundCraft rendering, save/reopen and clipping gates. This tests the actual single-prompt pathway rather than replaying existing compositions.
3. Repeat across at least three independent one-prompt generated mixes over different keys/styles and source combinations. Require actual human listening approval for groove-forward balance, harmony, arrangement and spatial effects. A zero-collision score is neither necessary nor sufficient.
4. Only then integrate bounded kick-bass source-pair audition into the final one-shot decision engine. The four-way source-pair audition currently exists as a separate opt-in tool and does not automatically pick a human-quality winner.

All private audio/preset data remain under `.local/`, separate from the public repository; no approved source bundle or reference song is modified. The new interlock defaults only within explicit `--groove-impact` and has a documented opt-out.

## Completed fresh single-prompt native coverage

The following were **new independent one-prompt productions**, not replayed existing projects. Each performed the private native preset audition, built a new SongSpec, loaded third-party Vitalium, selected CC0 sampled drums, generated the whole 16-bar project, saved/reopened SoundCraft, and rendered a stereo 48-kHz/24-bit WAV. Results are in private VPS .local/ directories.

| One-prompt example | Key / tempo | Native sources selected | Integrated LUFS (unmastered) | True peak | Clipped samples |
|---|---|---|---:|---:|---:|
| Bright jackin house, seed 83 | B-flat major / 128 BPM | Biow Bass 2; SNFKFutureBounce - Loaded Chords; Strings of Cygnus pad | −22.274 | −5.528 dBTP | 0 |
| Warm deep house, seed 67 | E major / 123 BPM | Biow Bass 2; SNFKFutureBounce - Loaded Chords; minimal house pad 2 | −23.628 | −5.429 dBTP | 0 |

Both include the new house-harmony-interlock-v1 project receipt and distinct musical chord-timing fingerprints. Each changed 60 chord voice events while leaving bass/drum MIDI untouched; both passed the structural near-simultaneous-bass-onset gate (16/20 chord groups initially colliding, zero after the edit). **Zero collisions does not certify that the result sounds more musical.**

**Critical honest limitations:**
1. Both independent prompts selected **the same bass and chord Vital presets**, revealing weak sound-palette diversity in the currently isolated-heuristic one-prompt selector.
2. Both inherited the same **[0,4,5,3] four-degree chord-progression template**, transposed into different keys. Different keys and rhythms do not alone prove unique original compositions.
3. Neither fresh production has yet passed listener assessment against Phase 44 or a professional reference; LUFS, true-peak and structural passes are safety criteria, not quality certificates.
4. The 4-way kick/bass native contextual audition still runs as a separate validated utility, not as an autonomous music-quality selector inside a single-prompt run.

The complete new 16-bar audio renders are preserved under:
- .local/independent-jackin-harmony-20261114/
- .local/independent-deep-E-harmony-20261114/

Two cross-style controlled before/after native render sets are preserved under .local/harmony-generalization-native-20261114/. The shareable listening archives (audio only, not the original private preset states) were transferred to a private link-only guest folder for time-limited review; the authoritative originals remain on the VPS.

**Next priority after listening:** develop a *musical-plan diversity gate* (different style-dependent harmonic progressions, motifs, rhythmic archetypes and source palettes) in tandem with native contextual source audition. Do not replace the same preset with random alternatives just to raise diversity; every new candidate must remain musically compatible. Progression variety must also be harmonically coherent rather than seeded randomness. Then require multiple full one-prompt tracks with producer listening approval before announcing professional quality.
