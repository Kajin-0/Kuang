# House Groove Standards and Locked-Pocket Production Policy

Status: research-backed engineering specification and groove-archetype catalog; **not** evidence that Kuang already implements these archetypes, tests or subjective evaluations. This complements `docs/HOUSE_PRODUCTION_PLAYBOOK.md`. Main song baseline is Phase43 pre-master and Phase44 club master; Phase45 remains a technically tested, not independently listening-approved alternative.

## Priority, execution sequence and scope

**Groove first.** The user's statement that groove is **80%+ of the project** is a qualitative priority, not a scientifically measured percentage or a license to make up an 80-point audio quality score. Treat groove as a *blocking gate* and allocate the largest early development/search effort to it. A technically passing groove that feels weak does **not** advance because its other stages score well.

**Production order:** (0) prompt constraints and sample provenance -> (1) select archetype and establish a strong **8–16 bar kick + bass + clap/hats/percussion pocket** using plausible real sources -> (2) add and test simple chord/harmonic structure -> (3) map a whole-song arrangement as track/automation activity over 4/8/16-bar units -> (4) select/replace/tune **compatible** bass/chord/pad and drum sounds in context, continuously guarding the groove -> (5) per-role balance, space, automation, transitions and dynamics -> (6) master and verify native deliverables.

Instrument choice is *not strictly a later stage*: an unsuitable kick or bass sample can make the groove impossible. Iterate source selection and MIDI pocket together in stage 1. Later preset search must protect that accepted pocket.

**Current melody policy:** no independently composed lead, topline, arpeggio substitute, ornamental call motif or synthetic counter-melody by default. Chord stabs, bass, pads and rhythmic FX are allowed to supply the hook. Requesting 'melodic' can select a harmonically rich chord arrangement but does not silently authorize a lead. Explicit melody work should remain a future, separately enabled and separately evaluated experiment. This is a proposed producer policy; legacy composer defaults are not automatically changed by this document.

**Freeze contract:** Once an 8–16 bar pocket is accepted, fingerprint kick/bass MIDI (positions, lengths, pitches and velocities), sample/patch identities, roles, microtiming and its control buses. Downstream stages can mute parts in arranged breaks or intentionally transpose bass with the chord roots, but may not rewrite the *groove timing identity* or silently change its sound sources. Any explicit groove edit requires a scoped reaudition and new acceptance receipt.

## Established house groove families — reusable patterns, not copied recordings

Common rhythmic **building blocks**, adapted rather than cloned. Use a 16-step bar, step 0 = beat 1 and each quarter note spans four steps. `K` = kick, `C` = clap/snare, `H` = offbeat/open hat, `h` = closed hat, `b` = bass, `p` = soft percussion. Examples are starting *templates*, not obligatory hits, licensed samples or proven quality scores.

| Archetype | Kick and snare foundation | Bass and top-layer feel | Expected changes to test |
| --- | --- | --- | --- |
| **Classic straight 4/4 house** | K at [0,4,8,12]; C at [4,12] | H at [2,6,10,14]; bass interlocks with kicks/offbeats | Kick/bass length, hat articulation, alternating velocity |
| **Deep-house offbeat bounce** | Stable 4/4 + backbeat | Bass at some upbeat eighths (e.g. [2,6,10] with rests), dark rounded tone; restrained soft shakers | Two-bar bass question/answer, ghost percussion, subtle swing |
| **Jackin/disco house** | Stable 4/4, strong backbeat; optional restrained ghost kick | Syncopated sixteenth hats/shakers; busier bass with deliberate rests | 2/4-bar accents and velocity groups; retain low-end clarity |
| **Swung/shuffle house** | Generally steady kick and clap | Uneven sixteenth subdivisions in selected hats/ghosts; offbeat bass remains anchored | Quantified grid vs shifted versions, verify swing not applied twice |
| **Afro/percussion-led house** | 4/4 foundation or supported variant | Layered conga/bongo/tambourine/crossrhythms; restrained backbeat | Interlocking percussion and swing/velocity; no indiscriminate density |
| **Minimal/stripped house** | Fewer active sound sources with a pronounced pulse | Sparse bass with space, distinctive short percussive accents | Check emptiness is purposeful, not unfinished |
| **Garage-inflected house (future scope)** | May use four-to-floor with shuffled tops, or broken kick rhythm | More aggressive swing, syncopated claps/ghosts | Require explicit support and acceptance; do not pretend every pattern is straight house |

Do not label a template 'industry standard' with a single mandatory tempo, 70% swing, note velocity or mix EQ. Industry instructional sources document recognizable conventions, but groove is style-specific. A reported DAW swing percentage is not interchangeable across every sequencer; Kuang should record **actual tick/time offsets** relative to the grid.

**Industry documentation to revisit when extending archetypes:**
- Ableton Learning Music, *Backbeats*: https://learningmusic.ableton.com/make-beats/backbeats.html — quarter-note kick plus beat-2/4 backbeat.
- Native Instruments, *How to make a deep house track*: https://blog.native-instruments.com/how-to-make-a-deep-house-track/ — kick, clap, shaker/open-hat and deliberately swung 16th percussion.
- Native Instruments interview with Saraga (2025): https://blog.native-instruments.com/saraga/ — sample design, pattern variation, humanized velocities/timing, long-loop development.
- Attack Magazine, *Dusted Deep House*: https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/ — deep-house kick and ghost-hit archetype with published example settings.
- Attack Magazine, *Drum Programming: Deep Afro House*: https://www.attackmagazine.com/technique/beat-dissected/deep-afro-house/ — syncopated percussion and offbeat bass.
- Sound On Sound, *Mix Rescue: Strong Arrangements*: https://www.soundonsound.com/techniques/mix-rescue-strong-arrangements — structural contrast through pruning/withholding parts.

## Reference-measured pocket fingerprint (do not hard-code into generator)

The approved Phase43 native canonical project, zero-based bars 32–34 (human bars 33–34), PPQ 960, BPM 126, contains:
- 8 quarter-grid kick events at beats 0–7; alternate MIDI velocities approximately 113/107.
- 4 main snare events on beats 2 and 4, plus two subsequent backbeats, offset **14 ticks** (~6.9 ms) behind grid.
- 4 sampled clap events with the same backbeat relationship, offset **24 ticks** (~11.9 ms).
- 7 closed-hat events near eighth upbeats with representative offsets from **-2 to +22 ticks** (~-1 to +10.9 ms); an open hat occurs near beat 8's approach.
- 7 bass notes over the two-bar window, mainly at eighth offbeats plus a later pickup, with intentionally absent notes.
- Chord stabs in multivoice groups, staggered voices by **4/10/16/22 ticks** within each event; bass/chord syncopation must be judged together.
- Additional shaker/bongo accents with intentional nonuniform timing and velocities.

These are directly inspected **MIDI events**, not isolated-stem subjective swing measurements or proof of an ideal house groove. They demonstrate that the quality reference's rhythmic character comes from interactions among kick, bass, claps, hats, shakers and chords—not just '4 on the floor'.

## Mandatory groove-first candidate test

1. **Generate archetypes rather than random patterns.** Select 2–4 distinctly different house groove structures appropriate to user intent, not arbitrary MIDI shuffles. Each has an explicit 1/2/4-bar bass response and a stable drum anchor.
2. **Select compatible sound sources immediately.** Audition multiple kick, bass and clap candidates in the actual rendered pocket, with consistent initial loudness and no heavy master. Replace poor source sounds before fine EQ or mastering.
3. **Do controlled percussion/timing trials.** At equal rendered loudness compare straight vs light shuffle, closed/open hat placements, 1–2 added ghost notes and minor multi-bar variation. Avoid multiple independent randomizations at once.
4. **Check pitch, phase and timing.** Native host: actual bass notes in tune, mono-compatible low band, no accidental double-kicks, plausible attack/release overlaps. Confirm that every intentional timing offset is in the canonical MIDI and survived rendering.
5. **Render 8–16 bars WITH context.** Audition kick+bass alone, full percussion, then chords against the same groove. The final pocket must be convincing *before* time-consuming full arrangement.
6. **Classify and correct failed properties.** If weak: audition kick replacement, bass timbre/envelope, bass rhythm, drum swing, clap timbre, percussion density, or chord syncopation separately. Never 'repair' via master loudness or random extra FX.
7. **Protect incumbent.** Compare candidate to best prior pocket at matched loudness and same timeline; accept only with supporting evidence. Technical acceptance cannot create a fake listening endorsement.
8. **Publish groove lock.** Freeze core MIDI/source hashes and measurable rhythmic diagnostics; pass the locked 8–16 bar nucleus to harmonic arranger and sound-selection search. For later chord changes, preserve rhythmic timing unless explicitly revisiting groove.

### Objective diagnostics (technical gating, not quality certification)

For each candidate, store:
- kick and snare/clap event count per bar, quarter/backbeat coverage, ghost-hit rate;
- kick-to-bass onset offset histogram (in ticks/ms), bass note duration and release-vs-kick overlap;
- hat/percussion onset offsets by role, velocity distributions, swing displacement and 2/4/8-bar variation rate;
- 0–20 ms / 20–100 ms kick and combined low-end onset-window statistics; kick+bass relative level by section;
- native bass tuning in cents across several registers, correlations and low-band stereo side fraction;
- stem and ensemble LUFS/RMS (matched for auditions), spectral masking over time, mono compatibility, clip/true peak;
- stem/source and MIDI hashes plus full native save/reopen and exact-note preservation checks.

No universal velocity, delay or swing limit is claimed. Calibrate ranges with *multiple approved and rejected* song examples, not a single Phase43 groove. Incorporate listener judgments or a properly evaluated perceptual model before assigning 'groove accepted'.

## Simple-song arrangement strategy

Once the groove and a functional 4–16-bar chord loop are credible, arrange the song by manipulating **part presence and section-level automation** rather than inventing unrelated melodic content.

Build an explicit grid of 4/8/16-bar blocks. For each block, specify active roles (K/C/H/percussion/bass/chords/pad), energy or density, harmonic bar, filter, room/plate/delay sends, breakdown treatment, transition cue and next-section reason.

The arranger should be able to:
- repeat a fixed approved groove nucleus while **add/remove/mute** roles in sections;
- change some bass roots as demanded by chord function without disrupting established timing;
- introduce roles gradually, maintain identifiable full groove for enough bars, then create meaningful contrast;
- create a **breakdown via subtraction**, with sparse chords/filtered tails as a bridge, and a return that feels earned;
- generate build-up using hats/percussion density, selective fills, FX throws and filter motion rather than unsupported melodies;
- protect the core motif/rhythm/patches in every full-groove section;
- preserve 4/8/16-bar phrase grammar but permit deliberate exceptions when a transition needs it.

**Arrangement test:** Blindly inspect the role/energy grid then audition actual full song. If bars are repetitive, change section treatment or phrase accent—not automatically harmony or lead. If section changes feel awkward, adjust entry/exit and density instead of adding new layers.

## Preset compatibility gate, after chord/arrangement map

A new preset is not promoted because it scores well alone. It must maintain the locked groove and serve the selected role in real rendered context.

- Bass: complements kick in timing, attack/release, tuning, harmonics and mono low-end.
- Chords: recognizable dry stab, correctly voiced progression, deliberate register and attack; syncopation doesn't erase bass groove.
- Pad: optional; quieter supporting bed with controlled tail, spectral density and intentional automation, never hiding the beat.
- Percussion: preserve transient hierarchy, prevent hats/claps from dominating, and test sampled sources before complex synthesis.
- FX: support phrase timing, space and movement. Effects do **not** justify a weak source sound.

For each contender, save provenance and native patch state; render an in-context 8–16 bar A/B at matched loudness; measure technical constraints; retain the existing sound if new preset does not produce a supported improvement. Retained accepted sources are not routinely re-randomized.

## Autonomous policy: quality gates and compute economy

**G0: source/intent sanity** -> **G1: groove locked** -> **G2: harmony/section map coherent** -> **G3: compatible sounds** -> **G4: production/mix transitions** -> **G5: appropriate master + verified editable deliverable**.

- G1 is **blocking**; G2–G5 cannot compensate for a failed G1. If no suitable groove can be established within the compute budget, report the best candidate honestly and stop without professional-quality assertion.
- G2 must verify chord/bass harmonic function, meaningful blocks, arrangement tension/release and the clear absence of unsupported melodic tracks.
- G3 compares selected *combinations* with protected groove, not independent preset proxy scores.
- G4 may revise source/preset choices if they are masking or muddying the groove, but must recheck G1 after changes.
- G5 optimizes the accepted mix, not melody or composition, and retains pre-master.
- Use bounded render lengths, user-approved asset directories, sample/hash provenance, opt-in real host, technical logs and explicit decisions.
- In initial versions, only technical outcomes are machine-certain; any purported perceptual promotion must be marked unverified or supported by human comparisons.

### Important negative lessons

- Melody failure was a recurring bottleneck in Phase21–23; do not defer the entire product until arbitrary autonomous toplines work.
- Phase14 demonstrated the importance of **actual host tuning**; structurally valid MIDI can sound about -200 cents off.
- Phase6/7 demonstrated that more pads and stereo layer volume can make the song worse.
- Phase18 demonstrated that a longer arrangement can become *less* DJ-friendly.
- Phase20 demonstrated that mastering cannot repair weak source composition/sound design.
- Phase42 demonstrated that tiny numerical change is not a meaningful auditory gain.
- Phase43/44 demonstrated that final sound benefits from controlled background pumping, layered short rooms and bounded mastering **after** a solid groove exists.
