# Commercial House Reference Tracks — Practical Case Studies

**Purpose:** supplement [Kuang's user-approved Phase43/44 house reference](HOUSE_PRODUCTION_PLAYBOOK.md) with publicly documented musical practices used in commercially successful house releases. This is **not** an invitation to copy a recording, melody, bass line, sample, preset, mastering curve, or original composition. The first detailed case is *FISHER — Losing It* (2018). A deliberately less detailed qualitative comparison is *Disclosure — When a Fire Starts to Burn* (2013). The parallel machine-readable record is [HOUSE_REFERENCE_TRACKS.json](HOUSE_REFERENCE_TRACKS.json).

**Source hierarchy:** artist/label/retailer metadata and first-hand producer information > published third-party remake with a declared workflow > general music-press criticism > unsourced BPM/key extraction. Source authority is claim-specific. A third-party Ableton remake is **not** verified access to the original artist's DAW session.

## Case 1 — FISHER, *Losing It* (2018): sparse tech-house groove and sectional recombination

**Why it matters:** The track was nominated for Best Dance Recording at the 2019 Grammy Awards. Its teaching value is the repeated pulse, compact 2–4-bar rhythmic material, four-bar bass variations, selective auxiliary percussion, and repeated breakdown/build/drop changes without endlessly replacing the underlying groove.

**Sources**
- [Top Music Arts — *Fisher – Losing it Deconstructed and How to make in Ableton*](https://topmusicarts.com/blogs/news/fisher-losing-it-deconstructed-and-hot-to-make-in-ableton), Esteban Miranda, November 25, 2018. **Third-party remake**, made with Ableton Live 10, Ableton stock effects, and Sylenth1 v3. Its screenshots, MIDI, effect values and instrument choices are **remake details**, not confirmed settings of FISHER's original project.
- [Beatport — *Losing It (Extended)*](https://www.beatport.com/track/losing-it/10766349): 125 BPM, 6:40, listed G major, Catch & Release.
- [Beatport — *Losing It (Original Mix)*](https://www.beatport.com/track/losing-it/15719012): 125 BPM, 4:08, listed G major. This explains the apparent duration discrepancy; **different commercial versions** exist.
- [Recording Academy — 2019 Best Dance Recording](https://www.grammy.com/awards/categories/best-dance-recording/2019/): nominated.
- [edjing Mix — *Losing It* audio analysis](https://edjing.com/track/losing-it-fisher/ca5kr1821202): another analysis labels G minor and treats the shorter version. **Key is source-dependent**, so it must not become a normative harmonic gate.

### Observed in the tutorial REMAKE (source-specific, not universal rules)

| Component | Documented reconstructed behavior | Reusable house-template technique |
|---|---|---|
| Tempo / form | 125 BPM; the tutorial discusses the 6:40 version | Support DJ-length and short-edit profiles, not one mandatory duration |
| Main kick | Mostly quarter-note four-on-the-floor; some faster variations around later builds/drops | Make kick pulse dependable; use rare, phrase-located variations |
| Hi-hats | Offbeat eighth-note pulse from a four-bar idea, removed in builds | Treat offbeat hats as a core texture that can be *withdrawn* |
| Claps | Short repeating backbeat idea; absent during some build-ups | Maintain an intelligible backbeat and deliberately subtract it to expose transitions |
| Rimshots | Four-bar decorative sixteenth-note response, especially in some drop halves | Optional higher percussion belongs to selected sections, not all bars |
| Ride | Late-drop additional layer, not constantly active | Increase drop energy by selective percussion entry |
| Snare rolls | Sixteenth-note build textures; other percussion drops out around many rolls | **Trade density** between roles rather than stack all percussion during a fill |
| Bass | One four-bar nucleus with approximately four related variants; removed for tension, restored in drops | One recognizable bass groove plus controlled variation and intentional absences |
| Extra sub channel | Remake adds a parallel sub in some drop sections | Optional and conditional: verify phase/mono/low-end headroom; never mandate bass layering |
| Signature lead | One repeating four-bar lead-like phrase with effects/automation variations | **Not transferred into current Kuang defaults.** Kuang's independent melody engine remains deferred; the lesson is stable musical identity plus FX variation |
| Arrangement | Filtered rhythmic opening; multiple breakdown → buildup → drop cycles, final differentiated return and outro | Make a section-role matrix, contrast by absence/re-entry, annotate native markers |
| FX | Source-dependent filtering, kick-based ducking on some auxiliary percussion and selective automation | Audition simple source choices and controlled role-specific processing before elaborate chains |

**Interpretation caution:** The tutorial's mentions of a "2 beats bar," "second beat of every bar," and a bassline around G/G♯ describe screenshots or loops within a reconstructed arrangement, not a definitive 4/4 time-signature change or authoritative note-for-note transcription. Do **not** derive exact note positions, diatonic rules, original VSTs or mastering targets from this prose. In particular, apparent chromatic bass notes are a reminder that **controlled non-diatonic notes can be musically valid**; a harmonic gate must recognize user-approved passing/neighbor notes instead of blindly banning them.

### Derived reference tests for Kuang (candidate gates; not yet implemented)

| ID | Gate candidate | Pass evidence | When waived / corrective action |
|---|---|---|---|
| XR01 | **Core rhythm anchors survive full-groove sections.** | Kick/backbeat/hat expected-pattern coverage and actual rendered pocket | Waive for a named break or supported non-straight substyle; correct missing role or timing |
| XR02 | **Main bass identity persists through variations.** | 2–4-bar onset-family recurrence plus controlled deviations; tonal and timing consistency | Intentional completely new bass B section allowed; otherwise simplify unrelated phrases |
| XR03 | **Auxiliary percussion is role- and section-aware.** | Rim/ride/ghost density and effect level by section | Minimal/percussion-free profiles waive optional layers; remove redundant accents |
| XR04 | **Builds substitute rather than merely accumulate.** | Role-presence matrix: build roll, filtered drum, FX or silence versus removed hats/clap as appropriate | Waive an uninterrupted/rolling build; fix overcrowded transitions |
| XR05 | **Break/drop has perceptible contrast and groove return.** | Difference in active rhythm/bass roles, arrangement map, section-level rendered A/B | Waive for ambient/minimal arc; strengthen reduction/return without unnecessary melody |
| XR06 | **Repeated sections develop economically.** | Recurrence of groove/bass fingerprint; selective 4/8/16-bar automation and part entry | Distinct song-form prompt can override; undo gratuitous added layers |
| XR07 | **Intro/outro are fit for version.** | Version-specific presence of recognizable pulse, markers and editable outro tail | Short edit vs extended DJ version differ; no mandatory 8- or 32-bar opening |
| XR08 | **Signal chain serves source selection.** | Contextual listening of sampled kick, hats/claps and supporting FX; no uncontrolled stacked low-frequency sources | Use more layers only if phase/headroom/quality checks justify it |
| XR09 | **Groove remains dominant over a novelty hook.** | Stable pocket on hook removal; full-mix acceptance; no lead role by default | Explicit future melody opt-in only; don't turn lead from original track into required feature |
| XR10 | **Provenance and tune/length claims are qualified.** | Metadata names exact version; remake notes marked source-specific; source URLs and uncertain key preserved | Reject misleading "original producer used..." assertions without primary evidence |

**Practical generalization:** a high-quality, producer-ready template can contain a core kick, clap, offbeat hats, bass and chord stab, with occasional rim/ride/roll layers and a controlled FX graph. The record's energy can emerge predominantly from a *part-presence matrix and selective automation*. That is compatible with the user's preference for **generic but consistently excellent editable house templates** and the current no-melody policy.

## Case 2 — Disclosure, *When a Fire Starts to Burn* (2013): classic/garage-inflected counterexample

[Pitchfork's contemporaneous track review](https://pitchfork.com/reviews/tracks/15525-disclosure-when-a-fire-starts-to-burn/) describes a strong house groove, rolling bass, organ stabs and garage-style swinging hi-hats, with rhythmic speech/vocal sample phrasing contributing to the feel. This is **qualitative music criticism**, not an instrument stem analysis or production session. No exact kick MIDI, swing percentage, note register, synth preset, BPM or bus processing is inferred.

**Transferable cross-genre lesson:** Kuang should **not** learn from FISHER alone. A sound template can lean on swung tops, rolling bass and short organ/chord stabs instead of a peak-time tech-house build/drop formula. Vocals and standalone melodic hooks remain outside the current target, but house chords and bass can supply a convincing musical identity. No obligatory huge riser or snare roll.

## Complementary harmony corpus — Hooktheory

The [Hooktheory study](HOUSE_HARMONY_REFERENCE_STUDY.md) and its [structured seven-track profile collection](HOUSE_HARMONY_REFERENCES.json) compare commercially recognizable dance music for tonal interpretation, chord simplicity versus extension, voice leading and section-specific harmonic variation. They complement FISHER's groove/arrangement reconstruction rather than replace it: TheoryTab's section titles are crowdsourced harmonic analysis, **not** documented original DAW structure or exact section durations. Its *One Kiss* entry is notably disputed between A Phrygian, a one-flat written key signature and an A-minor-centered interpretation; source certainty must be retained. The HX01–HX12 checks are proposed for later implementation, not proven sound-quality criteria.

## How to use external references safely

1. Maintain several **distinct archetypes** with a source link, release/version identity, declared analysis method, observation confidence and applicability. A template library made from one record will overfit and become repetitive.
2. Extract **abstract production techniques**, not copied transcriptions: pattern families, timing relationships, variation rates, phrase lengths, part-presence matrices, source-hierarchy and FX-role separation.
3. Inspect a reference **by section and at matched listening loudness** when licensed access is available. Recording loudness, spectral fingerprint and popularity alone are not a quality score.
4. Keep the user-approved private Phase43/44 record as the *production-quality anchor* and commercial recordings as *genre-grammar examples*. Do not claim equivalence without a repeated multi-prompt human evaluation.
5. Store no copyrighted reference audio, samples, Sylenth/Vital preset states, commercial remake files, lyrics or transcribed signature melodies/bass loops in this repository. Links and brief independently paraphrased observations are sufficient.
6. Mark every gate as `INVARIANT`, `HOUSE_CONVENTION`, `DEFAULT` or `OPTIONAL`, with a justified waiver and relevant prompt/subgenre. XR01–XR10 are **candidate reference-specific tests**, not extra universal hard requirements.
7. Before automatic enforcement, validate an entire **corpus of approved and deliberately weaker** tracks; technical correctness can be proven without a professional-sounding groove.

The companion [machine-readable record](HOUSE_REFERENCE_TRACKS.json) preserves source type, confidence and gate IDs for later integration with the producer's selection/quality evaluator.
