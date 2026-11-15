# Kuang Full-Song Phrase Development V1 — verified experiment (2026-11-15)

## Purpose and technical scope

The user approved the baseline 4:02 house track as "pretty good" but wants more convincing musical development. Claude's structural critique, independently confirmed by our frozen 152-project symbolic scorecard, identified a concrete problem: the existing long-form arranger simply repeats the same eight-bar Groove source in Main Drop for all core roles.

This experiment does NOT create another composer, change the SongSpec schema, alter source preset selection or master levels, or claim objective results automatically imply professional musical quality.

## Reusable implementation

Existing house_full_arranger.arrange_full_song now accepts opt-in phrase_development_v1=False. This is exposed in both existing local create pathways as --phrase-development-v1 and requires explicit full-song-bars plus groove-template production.

The existing 32-bar nucleus already includes two musically related authored eight-bar phrases called Groove and Drop. In previous long song the alternate Drop was discarded. This optional feature reuses that existing source material:

- Groove A stays exactly unchanged for every instrument.
- Groove B uses the alternate Drop bass/chords as a coordinated pair only in its second eight-bar block.
- Main Drop uses that Drop bass/chord pair for its first two eight-bar blocks and returns to Groove for its last block.
- Kick remains fixed four-on-floor across the active song, with no changed kick source or sample.
- Some percussion/tops reuse alternate existing source material; no new pitches or invented melodic lines.
- The original source project is immutable; evidence records which eight-bar source motif was selected per active section and role.
- No default behavior changed. Long-form source note IDs and exact provenance are retained.

This creates a simple recognizable call-and-response, NOT a claim that all eight-bar sections are newly composed.

## Actual objective evaluation

The frozen original benchmark remains unchanged at docs/baselines/HOUSE_MUSICAL_GATES_V1_20261114.json (152 original cases). A separate new matrix contains 160 cases: original 152 plus eight new developed 128-bar forms over deep, straight, jackin, minimal profiles and C major/D minor.

| Metric | Existing 128-bar forms | Developed 128-bar forms |
| --- | ---: | ---: |
| Hard structural gates | 100% pass | 100% pass |
| Bass first-eight-bar Groove A/Main Drop identical | 100% | 0% |
| Harmony first-eight-bar Groove A/Main Drop identical | 100% | 62.5% median |
| Kick/snare/hats first-eight-bar identical | 100% | 100% |
| Outro - Groove A core density | -7 events/bar | -7 events/bar |
| Extra lead/arp | None | None |
| Generator errors in 160-case matrix | — | 0 |

This uses exact onset/pitch/duration fingerprints. MIDI identifiers or velocity jitter cannot fake the improvement.

76 focused regression tests passed, including newly added cases for source immutability, unchanged Groove A, unchanged kick, paired bass/chord phrase maps, supported bars 96/128/160 across all four profiles and two keys, strict CLI opt-in and regression compatibility.

## Genuine full-length same-source SoundCraft A/B

Incumbent is the earlier **corrected dry-harmony duck** full 128-bar native song, G major, 127 BPM, seed 217:
- Private incumbent: .local/full-song-jackin-G-harmony-duck-corrected-20261114
- Private developed candidate: .local/full-song-jackin-G-phrase-development-v1-20261115

For controlled audio testing, the source nucleus was reconstructed from the actual saved SongSpec using existing jackin, simple harmony, groove-impact and groove-identity options; the resulting source kick/bass/harmony/snare Groove A MIDI was compared to the original actual native MIDI and was **exactly equal**. We then applied ONLY the new arranger's bass/harmony clips for Groove B and Main Drop to a deep copy of the existing 128-bar native project.

Thus the audio source, drum samples, private verified Vital instruments, effects, all mixer values and automation, original kick, pads, all Groove A MIDI, and every other section remain identical. Bass and chord MIDI in just those two sections differ. No extra preset audition was run.

New native SoundCraft full session was saved and reopened (canonical state hash equality). Its true peak is -10.888 dBTP and integrated loudness -26.613 LUFS, with zero clipped samples, versus corrected incumbent -10.888 dBTP / -26.611 LUFS / zero clipped samples. Both real musical arrangements last about 241.89 seconds plus ~12 seconds tail.

The controlled four WAV excerpts in the A/B archive cover the first sixteen bars of Groove B and Main Drop for both variants, gain-only matched individually at -22.0 LUFS, no limiting or clipping. The sound of the two versions can therefore be compared without confounding level, sample or FX changes.

A/B audio: https://gofile.io/d/z9qpqyrL

Complete developed four-minute WAV: https://gofile.io/d/35Os4Vcg

Original corrected full song remains immutable. Third-party share retention is not guaranteed; originals remain private on VPS. The candidate's editable SoundCraft native session and canonical score remain in its private directory.

## Explicit stop and next quality gate

Passing the objective comparison is *not* an audible improvement verdict. Several eight-bar sections continue to repeat musical source cells, and some house tracks appropriately repeat their kick and harmony for dancefloor cohesion. The feature stays disabled by default.

User should first listen to same-gain Groove B and Main Drop A/B, prioritizing melodic/rhythmic cohesion, chord/bass alignment, bass pocket, section identity and payoff. If B sounds better, advance the next controlled phase; if worse, preserve the incumbent. Do not add random complexity, a new framework, or change sound design before that decisive listening judgment.

Status: implementation, independent symbolic matrix, native render, safety checks and matched audio complete. Listener preference pending.
