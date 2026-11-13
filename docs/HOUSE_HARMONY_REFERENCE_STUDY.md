# House Harmony Reference Study — Hooktheory

Status: source-qualified research reference, not a production engine, licensed reference-audio corpus, or professional-quality certification. This supplements [House Reference Case Studies](HOUSE_REFERENCE_CASE_STUDIES.md), [House Production Playbook](HOUSE_PRODUCTION_PLAYBOOK.md), and the user-approved Phase43/44 production baseline. See also [structured profiles](HOUSE_HARMONY_REFERENCES.json).

## What this source does and does not establish

[Hooktheory TheoryTab](https://www.hooktheory.com/theorytab) contains crowdsourced, editable analyses of chord functions, tonal centers, melody, and some user-labeled musical sections. Its scale-degree system is valuable for comparing harmonic functions across songs and transpositions. The site's complexity metrics are referenced to its entire catalog (50 is its database average), NOT objective quality scores, percent correctness, or measures of musical success.

Hooktheory's "Verse," "Chorus," "Bridge," and "Instrumental" labels do NOT tell us exact 4/8/16-bar phrase lengths, drum arrangement, part entrances, mix, sample selection, VST state, sidechain or mastering settings. Only source-backed harmonic/section observations should be transferred. Avoid importing original melody MIDI, audio or other transcriptions.

## Curated cross-reference corpus: seven dance recordings

These are deliberately selected popular dance / house-related songs, NOT a random genre survey. Scores reflect **all analyzed sections**, even if a page contains only a chorus. Historical classics are included to diversify harmonic grammar. Numbers below were recorded from the listed source pages in November 2026.

| Recording | Tempo | Hooktheory key/mode | Chord complexity | Chord progression novelty | Section coverage |
|---|---:|---|---:|---:|---|
| [One Kiss — Calvin Harris & Dua Lipa](https://www.hooktheory.com/theorytab/view/calvin-harris-and-dua-lipa/one-kiss) (2018) | 124 | A Phrygian | 83 | 83 | Verse/pre-chorus, chorus, bridge |
| [Feel So Close — Calvin Harris](https://www.hooktheory.com/theorytab/view/calvin-harris/feel-so-close) (2011) | 128 | G major | 65 | 81 | Verse, chorus, instrumental |
| [Latch — Disclosure](https://www.hooktheory.com/theorytab/view/disclosure/latch) (2012) | 123 | A-flat major | 97 | 98 | Verse, chorus |
| [One More Time — Daft Punk](https://www.hooktheory.com/theorytab/view/daft-punk/one-more-time) (2000) | 123 | B minor | 71 | 41 | Verse, chorus, bridge |
| [How Deep Is Your Love — Calvin Harris & Disciples](https://www.hooktheory.com/theorytab/view/calvin-harris-and-disciples/how-deep-is-your-love) (2015) | 122 | E minor | 99 | 89 | Chorus only |
| [Music Sounds Better With You — Stardust](https://www.hooktheory.com/theorytab/view/stardust/music-sounds-better-with-you) (1998) | 124 | A minor | 90 | 63 | Verse, chorus |
| [Head & Heart — Joel Corry x MNEK](https://www.hooktheory.com/theorytab/view/joel-corry-x-mnek/head-and-heart) (2020) | 123 | A-flat major | 15 | 6 | Chorus only |

All seven are labeled 4/4; BPM range 122–128, median 123. The recorded chord-complexity span is 15–99. **These statistics describe only these seven handpicked entries and must not become absolute genre constraints or success probabilities.** They DO show why requiring complex seventh/ninth voicings in every house template would be inappropriate. Basic harmony can work, while sustained extensions and modal sonorities can provide a very different sonic identity.

## Detailed case: “One Kiss”

- Hooktheory calls the track **A Phrygian, 124 BPM, 4/4** and assigns section-specific chord-complexity values of **71** for verse/pre-chorus, **68** for chorus and **94** for bridge. These are Hooktheory's analysis, not a machine-verified transcription.
- A [published sheet-music arrangement](https://bach.oktav.com/nl/04e293c2.pdf) uses a **one-flat key signature** and 124 BPM, consistent with the pitch collection of F major, D minor and A Phrygian.
- [Asaf Peres's independently reasoned tonal analysis](https://www.top40theory.com/blog/calvin-harris-and-dua-lipas-one-kiss-is-ambiguous-af) hears an **A-minor-centered progression**, emphasizing bass motion, the strong-position return chord and ambiguous suspended upper harmonies. This is a disagreement over perceived tonic/harmonic function, not necessarily the available notes.

**Generalizable lesson:** A producer may create compelling tension with simple recurring bass motion, a flat-second/modal color, ambiguously voiced suspensions, and sectional variations in harmonic tension. Chord identity depends on BOTH bass and upper voices. A seven-note collection can support more than one tonal-center interpretation. Do not silently force an explicitly modal user prompt into major or natural minor; current Kuang SongSpec does NOT yet represent Phrygian and should disclose unsupported mode rather than claim it.

Keep the key/mode uncertainty in the source record and never use it as a hard judgment against a legitimately ambiguous progression. Native MIDI-to-rendered-pitch consistency, on the other hand, remains a strict engineering requirement (see Kuang Phase15 pitch-bend repair).

## The reusable harmony + arrangement grammar

**Simple chord cell:** two to eight bars of stable major/minor movement, useful for accessible/classic house. The very low Hooktheory complexity score for Head & Heart contradicts a mandatory sophistication quota.

**Extended-color cell:** sevenths, ninths, suspended/add tones, rootless voicings or inversions when musical/sonic context justifies them. Compare against simple chords at matched loudness WITH the actual bass and preset. Such extensions are not automatic improvements.

**Modal-color cell (future support):** altered scale degrees or center ambiguity as an opt-in harmonic profile. Keep the scale pitch collection, tonic hypothesis, chord function and actual rendered note tuning separate.

**Repeated material, changing presentation:** maintain one concise harmonic nucleus while changing chord attack rhythm, note duration, chord extensions/inversions, pad register, bass root phrasing, and occasional bridge/turnaround. Hooktheory's section labels support harmonic comparison, NOT precise bar-length/role-presence inference. Use the existing commercial arrangement breakdowns and Kuang's Phase43/44 reference for detailed track-arrangement techniques.

**Bass as harmonic anchor:** rootless upper chords, suspended voicing or bass pedal can be correct. A rigid "bass must always equal chord root" validation is musically harmful. Assess intended chord function and passing tones, and preserve locked kick/bass onset groove.

**Melody deferred:** Although TheoryTab analyzes vocal melody, Kuang's current target remains original, editable *instrumental house templates* with no independently generated lead/arp/topline. Chords, bass, rhythm and sound design must provide musical personality.

## HX01–HX12 candidate engineering gates (not implemented)

| Gate | Applicability | Test and revision behavior |
|---|---|---|
| HX01 — Recognizable harmonic nucleus | Default | Coherent two/eight-bar cell returns; waivable for static/minimal harmony |
| HX02 — Simple-harmony support | Hard future capability | Do not force sevenths/ninths; allow plain triads in suitable styles |
| HX03 — Extended voicing option | Optional | Compare inversions/7ths/9ths/sus in bass/chord context; omit if masking rises |
| HX04 — Bass/chord functional compatibility | Default | Verify intended root, pedal, inversion or passing-tone relationship, not just equality |
| HX05 — Tonal-center uncertainty | Hard evidence | Distinguish actual pitch set from tonic hypothesis; record source disagreements |
| HX06 — Section harmonization | Default | Track voicing/chord rhythm by section without inventing bar lengths from labels |
| HX07 — Chord-stab rhythmic placement | Default | Verify chord attacks relative to protected kick/bass groove and rendered tails |
| HX08 — Efficient voice leading | Default | Inspect leaps and common tones; allow deliberate larger motion |
| HX09 — No extra melody | User-scope invariant | No new lead, arp or topline in current default template |
| HX10 — Provenance and statistics | Hard evidence | Source URLs, date, coverage, uncertainty, no population claims from chosen sample |
| HX11 — Dynamic chord density | Optional | Develop same cell by changing rhythm, duration, register and role placement |
| HX12 — Unsupported modes fail honestly | Future hard technical gate | Do not claim Phrygian/borrowed-chord support before implementation and validation |

## Next technical implementation

1. Add distinct **simple**, **extended** and eventually **modal** harmonic-profile options, but only for actually supported musical data representations.
2. Couple the harmonic planner to the groove engine without changing the accepted rhythmic timing: fit bass roots, chord voicings, rhythmic stabs and phrase markers.
3. Build section-specific **harmonic treatments** on top of the producer's part-presence arrangement map.
4. Validate the real native synth's tuning, chord/bass interaction and mix masking, and compare producer-rated A/Bs before claiming quality improvement.
5. Preserve the primary product: a **single-prompt, editable, mostly finished house template**, not a copy of any commercial recording.

This is research guidance only. The opt-in groove-engine [draft PR #1](https://github.com/Kajin-0/Kuang/pull/1) remains a separate unverified implementation.
