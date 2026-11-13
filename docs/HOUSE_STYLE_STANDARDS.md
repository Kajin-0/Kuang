# House-Style Standards and Production Gates

**Status:** sourced reference profile for future producer automation, not an implemented perceptual evaluator. The product goal is a **one-prompt editable, producer-ready house template**, not a self-contained AI chart hit; see [PRODUCER_READY_TEMPLATE_PRODUCT.md](PRODUCER_READY_TEMPLATE_PRODUCT.md). Last research review: November 2026. Read alongside [House Production Playbook](HOUSE_PRODUCTION_PLAYBOOK.md) (75 stage checks) and [House Groove Standards](HOUSE_GROOVE_STANDARDS.md) (archetypes and measured Phase43 reference groove). The 40 entries below are **cross-cutting standards, not 40 additional mandatory effects or scores**. A machine-readable, source-linked mirror is in [HOUSE_STANDARDS_REGISTRY.json](HOUSE_STANDARDS_REGISTRY.json).

**Commercial evidence library:** [HOUSE_REFERENCE_CASE_STUDIES.md](HOUSE_REFERENCE_CASE_STUDIES.md) captures FISHER's *Losing It* and a qualitative Disclosure counterexample; [HOUSE_REFERENCE_TRACKS.json](HOUSE_REFERENCE_TRACKS.json) records the source type and confidence of each observation. Its XR01–XR10 items are *candidate cross-reference tests*, not automatically enforced standards. In particular, a third-party DAW reconstruction does not establish the original recording's exact devices, keys or MIDI.

## Why standards help without overfitting

House has recognizable defaults (4/4, roughly 120–130 BPM, four-on-the-floor, clap on 2/4, offbeat hats, 4/8/16/32-bar phrasing), but no universal chord progression, swing percentage, reverb ratio, frequency curve, track duration or LUFS. A drum hit pattern can be technically standard and still sound lifeless. The user's priority remains **groove-first with a blocking quality gate**, then functional chords and an explicit arrangement, then compatible presets, and finally detailed production. **Standalone melody generation remains disabled by default.**

### Four tiers, no invented quality percentage

1. **HARD:** implementable invariants of timeline, native state, source licensing, user exclusions or technical QA. Failure should block, or be marked unsupported. A hard gate never asserts that the song *sounds* professional.
2. **HOUSE CONVENTION:** an expected genre starting point, waived when the user chooses another substyle, time signature, unusual tempo or supported groove family; never silently override the user's request.
3. **STRONG DEFAULT:** a well-supported production practice that can be omitted/altered after justified evidence; technical measurements are diagnostics rather than quality certificates.
4. **OPTIONAL TECHNIQUE:** only apply if musically useful and compatible with selected roles; its absence is `NOT_APPLICABLE` rather than a failure.

A full gate record requires `applicability`, `status`, `inspection`, `evidence`, `waiver_reason`, and `revision_scope`. Gate status can be `PASS_TECHNICAL`, `NEEDS_LISTENING`, `ACCEPTED`, `FAILED`, `WAIVED` or `NOT_APPLICABLE`. `WAIVED` must not be scored as an error. A user cannot be told professional quality is achieved from technical gates alone.

## Standards register (40 gate candidates)

### 1. Tempo, drums and the rhythmic nucleus

| Gate / tier | Genre standard and when it matters | Inspection → corrective action |
|---|---|---|
| **S01** · convention · G1 | Default to 4/4 for conventional house; 120–130 BPM is a common starting envelope, not a rigid classifier. | Check meter/tempo against explicit brief and selected house subtype; log any justified deviation. **If deficient:** Keep specified unusual tempo/meter and adjust groove mapping rather than coercing 126 BPM. _Sources: [NI](https://blog.native-instruments.com/how-to-make-a-deep-house-track/)._ |
| **S02** · invariant · G1 | Maintain one canonical beat grid and reproducible timebase in every MIDI, sample-trigger and native export. | Inspect time signature, tempo, PPQ conversion, start/end ticks and host render alignment. **If deficient:** Correct the timeline/export mismatch before assessing feel. _Sources: [AB](https://learningmusic.ableton.com/make-beats/backbeats.html), [AG](https://www.ableton.com/en/manual/using-grooves/)._ |
| **S03** · convention · G1 | Use quarter-note four-on-the-floor kick for classic/deep/minimal house unless a groove-family exception is intentional. | Verify expected kick accents at four quarter-note positions per active full-groove bar, not during breaks. **If deficient:** Change the archetype/profile or repair missing/extra kicks; do not patch arranged breaks. _Sources: [AB](https://learningmusic.ableton.com/make-beats/backbeats.html), [NI](https://blog.native-instruments.com/how-to-make-a-deep-house-track/), [NID](https://blog.native-instruments.com/saraga/)._ |
| **S04** · convention · G1 | Use clap/snare backbeat on beats 2 and 4 for conventional house; layer only if compatible. | Measure backbeat hit coverage, offset vs kick, and transient collision by full-groove section. **If deficient:** Repair phase/timing or select a more compatible clap; allow percussion-led exceptions. _Sources: [AB](https://learningmusic.ableton.com/make-beats/backbeats.html), [AT](https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/)._ |
| **S05** · convention · G1 | Use offbeat hats as a foundational pulse; closed hats/shakers may add eighth or sixteenth subdivisions. | Measure open/closed hat onset pattern, choke/tail conflicts and velocity hierarchy. **If deficient:** Test sparse offbeats vs more subdivided alternatives in context; avoid constant high-hat density. _Sources: [NID](https://blog.native-instruments.com/saraga/), [AT](https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/), [AM](https://www.attackmagazine.com/technique/beat-dissected/minimal-house/)._ |
| **S06** · default · G1 | Select a kick whose attack/body/decay leaves room for the intended bass line. | Compare combined kick+bass attack/tail overlap, crest and low-band energy across actual pattern. **If deficient:** Re-audition real kick samples or adjust envelope; do not rely on master EQ. _Sources: [SO](https://www.soundonsound.com/techniques/mixing-bass), [AT](https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/)._ |
| **S07** · convention · G1 | Compose bass in conversation with the kick: offbeat eighths, syncopated sixteenths, selected downbeats and rests are archetypes. | Measure onset-offset and duration-overlap distributions across 2–4 bars in the full rendered groove. **If deficient:** Change bass note duration/syncopation or select complementary patch; do not blindly add more sub. _Sources: [SO](https://www.soundonsound.com/techniques/mixing-bass), [EP](https://www.edmprod.com/how-to-make-house-music/), [AA](https://www.attackmagazine.com/technique/beat-dissected/deep-afro-house/)._ |
| **S08** · default · G1 | Make bass notes rhythmically legible and harmonically pitched, including mid-bass articulation on small playback systems. | Verify rendered fundamental, note onset and useful upper harmonics, and compare low-end with kick. **If deficient:** Change source timbre/register/envelope or harmonic saturation before changing master loudness. _Sources: [SO](https://www.soundonsound.com/techniques/mixing-bass), [SM](https://www.soundonsound.com/techniques/better-bass)._ |
| **S09** · default · G1 | Add controlled per-role timing accents/velocity to hats, claps and ghost percussion; preserve stable kick anchor where appropriate. | Record actual per-note tick offsets, velocities, grid resolution and groove-template identity. **If deficient:** Test straight vs swung render; remove unintentional jitter and duplicate swing application. _Sources: [AG](https://www.ableton.com/en/manual/using-grooves/), [NID](https://blog.native-instruments.com/saraga/), [AT](https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/)._ |
| **S10** · invariant · G1 | Never apply swing twice to events whose timing was already shifted, and never extrapolate DAW swing-percent to a universal millisecond offset. | Compare original MIDI positions to final sample-accurate output and timing-transform provenance. **If deficient:** Undo stacked timing transformations and quantify actual per-role ticks/ms. _Sources: [AG](https://www.ableton.com/en/manual/using-grooves/)._ |
| **S11** · default · G1 | Use ghost notes as quiet structural accents rather than a random high-density layer. | Inspect ghost-to-main velocity/level, event density and masking of clap/kick. **If deficient:** Remove redundant ghosts; compare with the stripped pocket. _Sources: [AT](https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/), [AA](https://www.attackmagazine.com/technique/beat-dissected/deep-afro-house/)._ |
| **S12** · default · G1 | Make a 2/4/8-bar rhythmic call/response with small, deliberate turnarounds; maintain a clear anchor. | Compare bar-by-bar onset fingerprints and variation/recurrence; check phrase-end variation context. **If deficient:** Rework 1–2 event placements rather than recomposing the whole pocket. _Sources: [AT](https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/), [EP](https://www.edmprod.com/how-to-make-house-music/)._ |

### 2. Harmonic loop and chord rhythm

| Gate / tier | Genre standard and when it matters | Inspection → corrective action |
|---|---|---|
| **S13** · default · G2 | Choose a concise 2–8-bar core chord loop; extend to 16 bars if function and pacing warrant it. | Check consistent pitch classes, harmonic duration and recognizable return across repeated cycles. **If deficient:** Simplify meandering progression or correct inconsistent roots. _Sources: [AP](https://www.attackmagazine.com/technique/passing-notes/levelling-up-your-chord-stabs/), [MR](https://www.musicradar.com/news/house-music-2023)._ |
| **S14** · invariant · G2 | Keep bass pitch and chord roots/function coherent in the actual chosen harmony; explicitly allow intentional inversions, pedals and suspensions. | Check each audible bass note against local chord function and note exceptions. **If deficient:** Correct conflicting bass root, voicing or intentional passing-tone labeling. _Sources: [AP](https://www.attackmagazine.com/technique/passing-notes/levelling-up-your-chord-stabs/), [MH](https://www.musicradar.com/how-to/classic-dance-sounds)._ |
| **S15** · optional · G2 | Use rootless chord voicings where bass owns the low root, reducing redundant low-mid energy. | Compare rootless vs rooted voicings in complete bass/chord context. **If deficient:** Restore a voiced root where the harmonic identity disappears. _Sources: [AP](https://www.attackmagazine.com/technique/passing-notes/levelling-up-your-chord-stabs/)._ |
| **S16** · optional · G2 | Use sevenths, ninths, sixths or other extensions as appropriate; not all house needs complex harmony. | Inspect consonance/tension, voice range and root/third/seventh clarity; compare simple vs extended. **If deficient:** Remove cluttering extensions or widen voicing; never require sevenths by default. _Sources: [AP](https://www.attackmagazine.com/technique/passing-notes/levelling-up-your-chord-stabs/), [MH](https://www.musicradar.com/how-to/classic-dance-sounds)._ |
| **S17** · default · G2 | Prefer intentional voice leading and common tones between successive chords when natural. | Calculate voice movement, shared pitch classes and awkward register jumps; audition the actual preset. **If deficient:** Test different inversions or durations; preserve deliberate discontinuities. _Sources: [MH](https://www.musicradar.com/how-to/classic-dance-sounds)._ |
| **S18** · default · G2 | Treat chord stabs as rhythmic instruments: offbeat syncopation and varied lengths can create the hook without a lead. | Inspect chord attacks relative to kick/bass/clap and note lengths/voicings in 4–8-bar loop. **If deficient:** Move/re-voice stabs or change envelopes; no automatic extra melody. _Sources: [AP](https://www.attackmagazine.com/technique/passing-notes/levelling-up-your-chord-stabs/), [AT](https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/)._ |
| **S19** · invariant · G2 | Verify actual plugin-rendered pitch in the native host, not merely the written MIDI key. | Render at multiple octaves; check cent deviations, pitch-bend initialization and exact saved patch state. **If deficient:** Reject or repair mis-tuned native adapter before arranging or mixing. _Local source: [Kuang Phase15 pitch-repair postmortem](PHASE15.md); not an external genre standard._ |
| **S20** · invariant · G2 | No automatically composed separate lead, arp, topline or ornamental melody in the current Kuang target. | Check role set, track audibility and all sections against prompt and configured no-melody scope. **If deficient:** Delete the unauthorized part and recheck full arrangement; future melody requires separate opt-in. _Local source: [current user no-melody requirement](HOUSE_GROOVE_STANDARDS.md); not an external genre standard._ |

### 3. Arrangement, phrasing and transitions

| Gate / tier | Genre standard and when it matters | Inspection → corrective action |
|---|---|---|
| **S21** · convention · G2 | Use 4/8/16/32-bar phrasing as a strong structural prior, with clear section boundaries and exceptions recorded. | Inspect bar-level section markers, phrase lengths and downbeat alignment. **If deficient:** Align entrances/turnarounds or explain deliberate displacement. _Sources: [MC](https://www.musicradar.com/how-to/song-sections-explained-intro-verse-chorus-middle8-outro-tag-bridge), [EP](https://www.edmprod.com/how-to-make-house-music/)._ |
| **S22** · default · G2 | Create A and B treatments of one strong nucleus without unnecessarily adding a new musical hook. | Compare part presence, groove fingerprints, chord rhythm and density of two sections. **If deficient:** Vary source/role/FX treatment, not core pocket; make contrast audible. _Sources: [MR](https://www.musicradar.com/news/house-music-2023)._ |
| **S23** · default · G2 | Build arrangement by additive/subtractive layering of existing material, plus selective like-for-like substitutions. | Validate role-presence matrix and automation against planned arrangement; track source-to-section mappings. **If deficient:** Remove or replace parts; don't build unrelated MIDI in every section. _Sources: [MR](https://www.musicradar.com/news/house-music-2023), [EP](https://www.edmprod.com/how-to-make-house-music/)._ |
| **S24** · default · G2 | Ensure the intro establishes a recognizable pulse or identity promptly, appropriate to the release profile. | Inspect first 8/16 bars, bar-wise role entry and energy curve; audition immediate listener engagement. **If deficient:** Introduce a core element earlier or reduce dead space; avoid blindly copying one reference intro. _Sources: [MR](https://www.musicradar.com/news/house-music-2023), [MC](https://www.musicradar.com/how-to/song-sections-explained-intro-verse-chorus-middle8-outro-tag-bridge)._ |
| **S25** · optional · G2 | For DJ/extended mix, allow 16/32-bar relatively sparse beat intros/outros for phrase mixing. | Check configured release type, minimum usable beat-only window and neighboring FX tails. **If deficient:** Generate a dedicated DJ mix or adjust section lengths; don't force long intros into radio edit. _Sources: [EP](https://www.edmprod.com/how-to-make-house-music/), [MC](https://www.musicradar.com/how-to/song-sections-explained-intro-verse-chorus-middle8-outro-tag-bridge)._ |
| **S26** · optional · G2 | For radio/streaming edits, shorten beat-only sections while preserving main groove, harmonic identity and meaningful contrast. | Inspect target duration and introduction-to-hook time, compare edited section mapping. **If deficient:** Produce a separate shorter edit without corrupting extended mix. _Sources: [EP](https://www.edmprod.com/how-to-make-house-music/), [MC](https://www.musicradar.com/how-to/song-sections-explained-intro-verse-chorus-middle8-outro-tag-bridge)._ |
| **S27** · default · G2 | Create release through subtraction: a reduced-energy breakdown followed by a perceivable re-entry or peak. | Inspect role-count/energy changes and actual kick/bass absence/re-entry; audition transition. **If deficient:** Make the break genuinely different or simplify excess layers. _Sources: [MR](https://www.musicradar.com/news/house-music-2023), [EP](https://www.edmprod.com/how-to-make-house-music/)._ |
| **S28** · default · G2 | Mark important transitions with a restrained cue: fill, silence, filtered echo or automation at a meaningful phrase boundary. | Locate cues relative to 4/8/16-bar boundaries and check sample/FX tail continuity. **If deficient:** Move, thin or delete overused cues; preserve DJ-mix continuity. _Sources: [MR](https://www.musicradar.com/news/house-music-2023), [MC](https://www.musicradar.com/how-to/song-sections-explained-intro-verse-chorus-middle8-outro-tag-bridge)._ |
| **S29** · default · G2 | Avoid automatic cymbal/fill on every four- or eight-bar boundary: variation should express phrase and tension. | Count identical repeated fills and automation gestures; sample-compare consecutive blocks. **If deficient:** Remove mechanical pattern repeats or reduce density. _Sources: [MR](https://www.musicradar.com/news/house-music-2023), [EP](https://www.edmprod.com/how-to-make-house-music/)._ |
| **S30** · default · G2 | Verify full-song pacing; repeated groove should be recognizable but not stagnant, and complexity should not destroy dance continuity. | Check role/energy matrices by section then actual full-song playback; compare A/B section identity. **If deficient:** Rebalance part entries/mutes and phrase dynamics before adding new instruments. _Sources: [MR](https://www.musicradar.com/news/house-music-2023), [AL](https://makingmusic.ableton.com/catalog-of-attributes)._ |

### 4. Contextual source selection

| Gate / tier | Genre standard and when it matters | Inspection → corrective action |
|---|---|---|
| **S31** · default · G3 | Audition real kick/bass/chord/pad presets with the actual MIDI and surrounding parts, not just isolated descriptive features. | Compare level-matched full-context 8–16-bar alternatives, actual plugin version and source state. **If deficient:** Retain incumbent or replace weak sample/patch; never use semantic filename as proof of fit. _Sources: [AT](https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/), [SO](https://www.soundonsound.com/techniques/mixing-bass), [MH](https://www.musicradar.com/how-to/classic-dance-sounds)._ |
| **S32** · invariant · G3 | Make fader, automation and FX operating levels agree: no hidden lane should silently override intended gain. | Inspect base fader and same-parameter automation; render spot checks. **If deficient:** Edit authorized automation values together with gain or revert inconsistent state. _Local source: [Kuang Phase7 fader-automation override](PHASE7.md); not an external genre standard._ |

### 5. Mix and spatial treatment

| Gate / tier | Genre standard and when it matters | Inspection → corrective action |
|---|---|---|
| **S33** · default · G4 | Preserve kick and clap transients when compressing or saturating drums; use controlled attack and wet ratios. | Compare onset windows and transients before/after, with level-matched playback. **If deficient:** Reduce gain reduction, slow attack or re-audition a more suitable source. _Sources: [SC](https://www.soundonsound.com/techniques/how-when-use-mix-compression)._ |
| **S34** · default · G4 | Keep critical sub/low bass mono-compatible, while allowing musically justified side information above. | Measure frequency-dependent side power, L/R correlation, mono sum loss and phase of kick/bass. **If deficient:** Repair low-band cancellation or reduce problematic width; do not force all mids mono. _Sources: [SO](https://www.soundonsound.com/techniques/mixing-bass)._ |
| **S35** · invariant · G4 | Protect headroom and avoid digital clipping; kick and bass are often the principal LF headroom bottleneck. | Check per-bus peak/RMS, full-mix true peak, clipped samples and low-end overlap. **If deficient:** Repair balance, dynamics or source envelope before aggressive maximization. _Sources: [SO](https://www.soundonsound.com/techniques/mixing-bass)._ |
| **S36** · optional · G4 | Use foreground dry chords and controlled shared-room/pad/plate depth where it clarifies space. | Compare wet vs corresponding return-muted rendering and in-context mono/stereo clarity. **If deficient:** Shorten/filter/reduce tails or remove needless effect layers. _Sources: [MR](https://www.musicradar.com/news/house-music-2023)._ |
| **S37** · optional · G4 | Tempo-sync rhythmic delays to beat subdivisions; use selective phrase-end throws rather than permanently high wet mix. | Verify delay time from BPM and actual native effect return automation; measure audible sections. **If deficient:** Correct subdivision/routing or strip redundant throws. _Sources: [MR](https://www.musicradar.com/news/house-music-2023)._ |

### 6. Quality comparison

| Gate / tier | Genre standard and when it matters | Inspection → corrective action |
|---|---|---|
| **S38** · invariant · G4 | Compare candidates against the incumbent at matched loudness and identical musical context when making quality claims. | Record A/B audio, matching method, level difference, source hashes and explicit reviewer/evaluator outcome. **If deficient:** Mark quality PENDING unless comparison/acceptance exists; never select from louder sound alone. _Local source: [Kuang Phase43/44 private matched-level A/B receipts](HOUSE_PRODUCTION_PLAYBOOK.md); not an external genre standard._ |

### 7. Mastering

| Gate / tier | Genre standard and when it matters | Inspection → corrective action |
|---|---|---|
| **S39** · default · G5 | Master only after the song and mix are accepted; set deliverable-dependent loudness and true-peak limits. | Check integrated/section LUFS, true peak, LRA, crest and original/matched A/B before promotion. **If deficient:** Revert excessive limiting, reconsider mix; avoid fixed house-EQ or loudness targets. _Sources: [SO](https://www.soundonsound.com/techniques/mixing-bass), [SC](https://www.soundonsound.com/techniques/how-when-use-mix-compression)._ |

### 8. Editable delivery

| Gate / tier | Genre standard and when it matters | Inspection → corrective action |
|---|---|---|
| **S40** · invariant · G5 | Deliver an authorized reproducible editable native project, licensed source closure and verified final audio. | Validate patch and sample hashes, asset licenses, MIDI, native save/reopen, exact role exclusions and render specs. **If deficient:** Reject incomplete bundle or source drift; do not redistribute unlicensed preset states. _Local source: [Kuang native adapter/asset licensing contract](../AGENTS.md); not an external genre standard._ |

## Concrete starter pattern (NOT mandatory)

For a typical 4/4 straight-house bar in a 16-step grid (0-based): kick [0,4,8,12]; clap [4,12]; open hat [2,6,10,14]. Bass may use offbeats and rests; chord stabs can sit between bass and drum events. This is **an archetype**, not a proof of feel, a drum MIDI file, or a recommendation to use all notes at the same velocity. Do not copy this as the only possible house groove. See [House Groove Standards](HOUSE_GROOVE_STANDARDS.md).

**Timing formulas (use the song's actual BPM, PPQ and host):** one quarter note lasts `60,000 / BPM` ms; for a 960-PPQ timeline a sixteenth-note spans 240 ticks; `offset_ms = offset_ticks * 60,000 / (BPM * PPQ)`. A straight eighth-note delay is `30,000 / BPM` ms; a dotted eighth is `45,000 / BPM` ms. The groove pool's 'swing percentage' is DAW-dependent and **cannot** be converted to one universal tick offset; inspect rendered note timings. Avoid double-swing.

## Style-profile exceptions and decision rules

- **Deep/mellow house:** Usually prioritizes subtle bass articulation, harmonic warmth, patient space and less dense percussion. A minimal pad is optional; a lead is not required.
- **Classic/Chicago/piano house:** More pronounced syncopated piano/organ or minor-seventh stabs and strong backbeat may be appropriate; use its actual sample/patch character, not a fixed EQ curve.
- **Disco/jackin house:** More lively percussion, syncopated bass and short accent ghosts; keep a stable kick and do not saturate every bar with fills.
- **Minimal house:** Greater negative space and precise sparse accents; lack of a pad is not a quality defect.
- **Percussion-led/Afro-derived house:** Permit more varied kick/percussion syncopation and interlocking hand drums; standard straight-house hat coverage can legitimately be waived.
- **Garage-influenced and broken-beat profiles:** Treat as an explicit later supported style and test its own rhythm grammar; do not silently impose the straight-house kick/backbeat matrix.
- **DJ extended vs shorter release:** Intro/outro beat-only length is profile-dependent. A 16/32-bar DJ-friendly window is a useful convention, not a mandatory 118-bar or 6-minute song. Many house records use substantially different forms. Main song Phase43/44 remains the user-quality reference, not a rigid arrangement template.

## What to automate vs what remains perceptual

**Automatable:** parsing constraints, 4/4/grid/onset coverage, phrase boundaries, repeated-role activity matrix, chord/bass pitch consistency, multi-register native tuning, audio clipping, low-band mono cancellation, mixer lane override, source/asset hash/rights checks, timing conversion, BPM-relative effects, MIDI event fingerprint stability, and all deliverable integrity checks.

**Human/validated-model judgment still needed:** whether the groove *feels* compelling, bass sounds musical on multiple systems, a chosen chord voicing evokes the intended mood, A/B arrangement is engaging, pads are tasteful rather than strange, and the full mix seems professionally balanced. Objective signals can flag risk, but must not promote songs on their own.

**Optimization order:** if groove fails, revise its sample/bass/MIDI/timing. If chord movement fails, revise voicing/progression **without changing groove timing**. If preset selection fails, re-audition whole-mix combinations and preserve incumbent. If arrangement is dull, use subtraction/addition/contrast **not obligatory melody**. If the mix is poor, repair level, sound sources, masking and space before mastering. Release only the selected, technically verified editable project with a candid quality status.

## References: independently published practice, not rigid specifications

- **NI — Native Instruments — How to Make a Deep House Track**: https://blog.native-instruments.com/how-to-make-a-deep-house-track/
- **NID — Native Instruments — Saraga on Drum Programming in House**: https://blog.native-instruments.com/saraga/
- **AB — Ableton Learning Music — Backbeats**: https://learningmusic.ableton.com/make-beats/backbeats.html
- **AG — Ableton — Using Grooves**: https://www.ableton.com/en/manual/using-grooves/
- **AT — Attack Magazine — Dusted Deep House**: https://www.attackmagazine.com/technique/beat-dissected/dusted-deep-house/
- **AM — Attack Magazine — Minimal House**: https://www.attackmagazine.com/technique/beat-dissected/minimal-house/
- **AA — Attack Magazine — Deep Afro House**: https://www.attackmagazine.com/technique/beat-dissected/deep-afro-house/
- **AP — Attack Magazine — Levelling Up Your Chord Stabs**: https://www.attackmagazine.com/technique/passing-notes/levelling-up-your-chord-stabs/
- **MR — MusicRadar — Definitive Guide to House**: https://www.musicradar.com/news/house-music-2023
- **MH — MusicRadar — Classic Dance Sounds**: https://www.musicradar.com/how-to/classic-dance-sounds
- **MC — MusicRadar — Song sections and club structure**: https://www.musicradar.com/how-to/song-sections-explained-intro-verse-chorus-middle8-outro-tag-bridge
- **EP — EDMProd — House production**: https://www.edmprod.com/how-to-make-house-music/
- **SO — Sound On Sound — Mixing Bass**: https://www.soundonsound.com/techniques/mixing-bass
- **SC — Sound On Sound — Compression**: https://www.soundonsound.com/techniques/how-when-use-mix-compression
- **SM — Sound On Sound — Better Bass**: https://www.soundonsound.com/techniques/better-bass
- **AL — Ableton — Catalog of Attributes**: https://makingmusic.ableton.com/catalog-of-attributes

### Provenance qualification

Sources are instructional production articles and manuals; they describe customary musical practices, not formal measurement standards or acceptance thresholds. Some individual example swing settings, levels and timings are *specific to those demonstrations* and must never be copied as universal requirements. The main Phase43/44 reference is a user-approved production lineage; its exact MIDI/presets, 118-bar duration, and -13.9 LUFS club-master measurement are not mandatory genre parameters. Third-party recorded material and private presets are not bundled in this registry.
