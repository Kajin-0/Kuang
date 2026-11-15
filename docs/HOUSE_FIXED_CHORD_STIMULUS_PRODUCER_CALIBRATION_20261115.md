# Native fixed-voicing chord audition — source fitness and autonomous production calibration

Date: November 15, 2026. Experimental branch only. Originals, private Vital preset bytes and full song audio untouched.

## Major measurement bug corrected

The house chord engine deliberately strums notes by 5 PPQ ticks each: four-note groups have offsets [0,5,10,15] ticks. The old analysis counted each voice as a separate musical chord attack. That falsely produced zero isolated eligible chord onsets for #05 and #07, despite both sounding in their full native mixes.

Updated kuang/house_note_envelope_v1.py groups *distinct MIDI pitches* into polyphonic chord stabs only if they occur within 24 ticks of the **first** voice. The grouping is anchor-bounded, not chained, and never merges a repeated same-pitch note. Preserves original note velocities/gates, chord arpeggiation/stagger and other-role onsets.

Actual native 8-bar Groove A remeasurement:

| Original song | Chord note-on events | Chord attack groups | Qualified events | Median MIDI-to-90% attack | Post-noteoff signal change |
|---|---:|---:|---:|---:|---:|
| #05 jackin | 80 | 20 | 20 | 50ms | -4.841dB |
| #07 minimal | 80 | 20 | 19 | 25ms | -4.736dB |

Earlier bad zero-coverage evidence remains preserved, not overwritten. Updated actual native data:
- Kuang/.local/house-note-envelope-grouped-v2-song05-20261115/actual-native-waveform-features.json
- Kuang/.local/house-note-envelope-grouped-v2-song07-20261115/actual-native-waveform-features.json

## Controlled native source-stimulus module

New kuang/house_chord_stimulus_v1.py extracts the exact first suitable four-voice chord from actual source #05: pitches [51,55,58,60], velocities [57,61,59,58], note gates 300 ticks each, original strum offsets [0,5,10,15] ticks. It makes an isolated 8bar private test with four identical chord events two bars apart, preserves chord instrument settings, fader, effects, bus routing and source automation, and mutes other MIDI roles in the disposable diagnostic copy. The original 128bar song remains identical.

Three independently runtime-verified native Vital source presets used **exactly the same original song-05 voicing, note length, velocities, fader and FX**, with actual SoundCraft native export/save/reopen and 8bar 48kHz PCM24 bounce. All source hashes/catalog compatibility and original asset inventories checked. No sample library/patch bytes shared.

| Fixed-source diagnostic | A: WIP-D Retro Piano | B: Loaded Chords | C: Dub Stabs |
| --- | ---: | ---: | ---: |
| Eligible isolated chord groups | 4 | 4 | 4 |
| Median MIDI-to-90% attack | 42.5ms | 27.5ms | 2.5ms |
| Median 10–90% attack rise | 37.5ms | 27.5ms | 2.5ms |
| Median post-noteoff energy delta | -5.037dB | -16.971dB | -4.386dB |
| Isolated 8bar integrated level | -40.445 LUFS | -26.518 LUFS | -37.446 LUFS |
| True peak | -26.048dBTP | -11.118dBTP | -20.946dBTP |
| Clipped samples | 0 | 0 | 0 |

Important limits: these audio excerpts are isolated, effects-processed chords with intentional long silent gaps, so their LUFS are not normalized timbre preference scores or useful fixed gain targets. Previous **actual fullmix human listening explicitly preferred A**, despite B being 13.927LU louder in this isolated stimulus and C having the quickest rise. This is direct counterevidence to a selector maximizing speed, presence, level or minimized tail.

The controlled audios and sanitized technical JSON (no private VST patch bytes):
https://gofile.io/d/JXAzsVCn

Private source reproducibility:
- Kuang/.local/house-chord-fixed-source-probe-20261115.py
- Kuang/.local/house-chord-fixed-source-probe-20261115/evidence.json

## Safety and validation

New and existing tests exercised:
- 5-tick strum clustering and anti-chaining/same-pitch controls
- Deterministic four-style actual-project 8bar chord stimulus using source register/velocity/gate
- MIDI/project immutability, source-identity preservation, invalid/silent PCM abstention and fast/slow synthetic envelope discrimination
- 62 total focused/regression tests passed
- Three real SoundCraft patches exported, rendered, saved/reopened with canonical hash validation; originals, source catalogs and private patch inventories unchanged

Only the opt-in context-palette-v2 review benefits from corrected chord grouping. No global source or mix default, no artistic-quality oracle and no user approval required to retain the already approved song05 original A.

## Next step

Use the accurate acoustic descriptor as a *filter and explanation*, not a musical winner. Apply it to future genuinely problematic source cases with exact prompt intent and held-out song context. When evidence is insufficient, retain existing source. Focus next substantial production work on full-song tension/arrangement, role interaction and native final mastering rather than endless minor sound swaps on an already preferred song.
