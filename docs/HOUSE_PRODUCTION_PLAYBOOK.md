# Kuang House Production Playbook — Reference-derived master checklist

Status: reference specification / proposed producer architecture, **not** evidence that these gates are implemented. **Product priority:** [PRODUCER_READY_TEMPLATE_PRODUCT.md](PRODUCER_READY_TEMPLATE_PRODUCT.md) defines the goal as a **reliable, high-quality, mostly finished editable house template from a single prompt**. Routine production labor should be automated; producer customization is the intended final stage, not a system defect. Generic house forms are acceptable, reliability outranks novelty, and no standalone melody is required.
Established November 12, 2026 from `docs/PHASE2.md`–`PHASE26.md`, the local Phase27–Phase45 release README, production/composition/mastering receipts, and the user's listening feedback. The newest Phase45 sound-design variation has technical verification but **no independently recorded listening approval**. Phase43 is the approved pre-master mix lineage; Phase44 is the separately approved club-master reference. The main song is a **quality and process reference**, NOT a melody, arrangement, timbre, or LUFS template for every generation.

## Priority override — user-directed development order

**This is NOT a flat 75-point checklist.** Follow: **GROOVE (blocking)** -> **CHORDS/HARMONIC STRUCTURE + ARRANGEMENT MAP** -> **COHERENT SOURCES/PRESETS** -> **PRODUCTION DETAIL** -> **MIX/MASTER/VERIFICATION**. Source selection is interleaved with groove construction when needed (kick/bass/clap quality determines groove); final preset refinement occurs after the musical/section plan. The user's '80%+' figure describes the *priority of a convincing groove*, not a calibrated scoring weight. A bad groove must fail even if all other gates pass.

**Melody is deferred** in the current target. No default leads, arps, standalone hooks or automatically generated toplines; the main house song can derive its identity from bass, rhythmic chord stabs, percussion, space and arrangement. A future melody engine requires a separately enabled, evaluated milestone; existing legacy composer behavior is not silently changed by this written specification.

**Reusable house foundations and reference measurements:** see [HOUSE_GROOVE_STANDARDS.md](HOUSE_GROOVE_STANDARDS.md), which documents conventional kick/backbeat/hat archetypes, microtiming, bass syncopation, groove locking, conditional acceptance and external practical references. See also [HOUSE_STYLE_STANDARDS.md](HOUSE_STYLE_STANDARDS.md) for **40 separately sourced cross-cutting genre conventions, strong defaults, optional techniques and hard technical gates**. Its structured [HOUSE_STANDARDS_REGISTRY.json](HOUSE_STANDARDS_REGISTRY.json) is intended for a future gate engine, not claimed to be executed today. Generalize rhythmic rules; do not duplicate historical reference MIDI or any third-party recorded loop.

**Execution dependency:** A (constraints) -> B01–B05 and B09 (groove selection/approval) -> B06–B07 and F (chord structure plus arrangement plan) -> C (context-compatible presets; retest groove) -> D/E/G (processing, effects and mix, retest groove) -> H/I (master and native technical delivery). Other numbered checks remain accessible by subject rather than their alphabetical presentation.

## 0. End state and decision model

One prompt should produce an **original, complete, technically valid, musically coherent, polished, fully editable native house record**. Every meaningful decision is auditable, revisable and preserved if already approved. Human feedback during development calibrates the eventual automatic evaluator; a preset feature score or successfully saved session is not a substitute for listening.

**The producer is a constrained state machine, not a list of mandatory effects.**

- `NOT_APPLICABLE`: style/instrumentation does not require this feature (e.g., no pad, no melody, no vocal).
- `PENDING`: not measured or not yet reviewed; **never** silently interpreted as passing.
- `TECHNICAL_PASS`: exact construction, timing, pitch, routing, signal and file requirements proven.
- `QUALITY_CANDIDATE`: passed objective diagnostics; preference/quality unverified.
- `ACCEPTED`: validated by a calibrated perceptual or explicit human preference process for the intended context.
- `REJECTED`: an unacceptable regression, regardless of loudness, format or metric improvements.

For each step store: input assets and license; source state hash; intent; alternatives; measured diagnostics; audition excerpts; decision and reason; optional protected-region invariants; wall time/CPU cost; resulting native state hash. No unsupported quality claims.

## 1. Source-of-truth listening benchmark

Use `.local/phase43-experiment/release/` for the preferred mix; `.local/phase44-experiment/release/` for the selected louder club master; `.local/phase45-experiment/release/` for an **unreviewed** expression candidate. Never mutate or redistribute the original private Qub1t/Vitalium source states; redistribution rights were not established.

| Reference property | Verified historical value | Meaning |
| --- | --- | --- |
| Main reference duration | 118 bars at 126 BPM, about 224.76 s score + tail (~227.76 s measured) | One successful form, not a mandatory duration |
| Meter and rendered format | 4/4; 48 kHz, 24-bit stereo | Actual reference export conditions |
| Musical identity | Repeating C-minor / A-flat / F-minor / G harmonic family; rhythmic chords, deliberately no prominent lead | Distinctive reference choice, not universal house grammar |
| Kick events in Phase43 | 423 saved kick onsets | Accurate pump anchors, not generic 4-on-floor assumptions |
| Phase43 mix | -16.3945 LUFS-I, -2.0465 dBTP | Approved mix lineage, not a mastering target |
| Phase44 club master | -13.9066 LUFS-I, -1.4132 dBTP; no clipped samples; LRA about 4.96 LU | Selected club-master comparison, not a universal loudness goal |
| Fair historical A/B | Both attenuated to about -17.600 LUFS-I | Consistent comparison methodology; match within a small LU tolerance |
| Phase45 alternative | -16.4230 LUFS-I, -2.0520 dBTP | Technical proof only; human listening result not established |

**Important:** Pitch, arrangement, sound balance, and quality cannot be certified by these whole-song figures. A reference comparison should be loudness matched *and* compared by musical section, e.g. full groove, intro, breakdown, build and climax. Avoid copying exact waveform, melody, preset, or Suno content.

## 2. Stage-by-stage production checklist

Mark every item with applicability, pass evidence and an explicit correction action. Numbers below are **initial engineering checks or audition starting ranges**, not magic quality targets. House subgenres may require different results.

### A. Decode the prompt into a single production contract

- [ ] **A01 — Style and intent:** House subtype (deep, soulful, melodic, minimal, funky, progressive, club), energy, mood, intended listening environment, instrumental/vocal status, desired length, references and exclusions. Do not infer a prominent lead from the word 'house'.
- [ ] **A02 — Musical constants:** One validated tempo, meter, tonic, mode, approximate harmonic language, rhythmic feel and explicit arrangement constraints; parse once and pass **the same spec to auditions, composer, mixer and exporter**. Reject contradictions. Current native SongSpec only supports limited modes/durations; label unsupported intent.
- [ ] **A03 — Instrument roles:** Choose kick, clap/snare, hats, percussion, bass, chord foreground, optional pad/atmosphere and transition effects for the style. **Standalone lead, arp and melody generation are disabled in the current target**; a future explicit opt-in is a separate milestone. Do not force an instrument to satisfy a fixed template.
- [ ] **A04 — Source/provenance budget:** Identify sample, patch, plugin and model provenance; choose only accessible/compatible sources; respect private preset distribution rights. Cap candidate count, runtime and memory before search.
- [ ] **A05 — Reference profile:** Determine which qualities are being targeted (kick articulation, bass movement, chord space, percussion groove, arrangement density), not reference audio transcription or global EQ copying.
- [ ] **A06 — Acceptance brief:** Define expected structure, defining hook/identity, emotional movement, loudness context, prohibited material, human or model evaluation availability and fallback criteria.

### B. Build the 8–16-bar musical nucleus BEFORE the full song

- [ ] **B01 — Kick candidate:** Compare **real samples** or physically appropriate designed kicks in context. Check attack, tonal body, low-frequency decay, tail length, click balance and peak. Phase13's sampled kick was a decisive improvement over earlier artificial percussion.
- [ ] **B02 — Kick/bass joint pocket:** Compose bass onset/offset **around actual kick onsets**, not independently. Test offbeat notes, rests, pickup notes, shared sub-band energy, pitch stability, envelope overlap and audible weight on headphones and small speakers.
- [ ] **B03 — Bass sound source:** Audition real Vital/Vitalium presets and original patches with *the actual bass MIDI*, including root and upper notes; verify patch pitch across registers, low-end mono compatibility, transient attack and mid-bass audibility. Phase32 used new bass/keys/pluck sources; Phase39/40 refined upper harmonics.
- [ ] **B04 — Percussion hierarchy:** Clap/snare backbeat, closed/open hats, shakers, bongos and ghost layers must interlock without busy, high-frequency clutter. Preserve kick anchors. Phase39 made selective **6–8 ms** hats/shaker/bongo shifts; don't double-swing an already shifted pattern.
- [ ] **B05 — Groove variation:** Apply small, intentional velocity, silence, pickup and articulation changes. Stable 4-on-floor is a *reference*, not a requirement to place every instrument on every beat.
- [ ] **B06 — Harmonic basis:** Choose a 4–16-bar progression whose functional motion actually serves the style. Check inversions, voice leading, chord-register overlap and transitions. Earlier Phase26 harmonic motion was perceived as meandering; Phase34/37 restored a more directed Cm–Ab–Fm–G family.
- [ ] **B07 — Chord foreground:** Select a punchy and identifiable stab/electric-key/pluck source. Design attack, body, release, register, velocity, saturation and filtering around the groove; don't depend on wash/reverb to create an interesting core tone.
- [ ] **B08 — No-lead musical identity:** Do **not** compose a separate lead/melody/arp in the current production scope. The user rejected multiple melodic alternatives in Phases21–23 and approved a melody-free groove. Use bass movement, chord stabs, percussion, filters, space and arrangement as the musical identity. Revisit melody only as a separately enabled and evaluated future capability.
- [ ] **B09 — Pocket audition gate:** Compare at least one complete 8–16-bar section with balanced monitoring. If kick, bass or harmony is weak, **repair the sound or performance**, not the master. Do not expand an unconvincing loop into 120 bars.

### C. Design and verify the instrument palette

- [ ] **C01 — Source selection over generic presets:** Prefer a genuinely suitable sample/preset over extensive EQ on an unsuitable one. Earlier hand-built synths reached a plateau before Phase16 and the Phase30–34 VST improvements.
- [ ] **C02 — Independent pitch calibration:** Test rendered fundamentals/known MIDI notes at several registers in the **target native host**. Phase14's Vitalium host had about **-200 cents** detuning despite correct MIDI and saved state; Phase15 centered the actual native pitch-bend input. Reject out-of-tune candidates; never 'solve' host tuning by transposing the score.
- [ ] **C03 — Audition real articulations:** Bass with kick, chords with exact stabs, pads sustaining across changes; listen to attacks, envelopes, tails and the way the actual patch interacts with tempo and note velocity.
- [ ] **C04 — Role separation:** Choose foreground/body/halo layers intentionally. Central chord attack with softer stereo doubles can work; Phase29 used delayed **~11/22 ms** left/right doubles. Require mono compatibility and avoid phasing and gratuitous duplicate layers.
- [ ] **C05 — Spectral arrangement:** Use HPF/LPF, shelving and complementary register design where justified; evaluate masked notes by section and source. Do **not** copy a Suno 25–90 Hz energy fraction as a target EQ curve.
- [ ] **C06 — Dynamic envelopes:** Set amp/filter attack, decay, sustain, release; avoid the Phase6/7 failure of overbearing, unnatural pads. Pads support dry foreground; they do not replace it.
- [ ] **C07 — Contextual preset combination:** Compare complete **kick+bass+chords+pad** candidate sets, not four independent isolation scores. Assess kick/bass envelope complement, chord/pad masking, effects buildup, stereo translation and the joined musical texture.
- [ ] **C08 — Patch reproducibility:** Verify version, exact plugin binary/hash, component state, controls, discrete choices, embedded wavetable contents, missing samples and native reopen. Separate technical validity from perceived quality.

### D. Groove processing, arrangement dynamics and sound placement

- [ ] **D01 — Instrument calibration:** Render stems/subsets under actual host and MIDI, set **per-role gains** and headroom. Equal global gain compensation alone cannot fix a dominant pad or buried bass.
- [ ] **D02 — Kick transient management:** Preserve kick definition. Use compressor/saturator selectively; Phase31 and Phase40 improved some combinations through less-wet/slower drum-bus compression and revised clap presence. Don't maximize first.
- [ ] **D03 — Bass translation:** Make the bass present as pitched movement—not just subsonic energy—using patch harmonic structure, duration, gain, saturation and mid-bass EQ. Assess kick and bass together in mix.
- [ ] **D04 — Programmed kick pumping:** Generate dB automation from **actual kick-note onsets** and the musical intent; choose depth/recovery by source. Phase43 used approximately **1.25 dB pad dip / 2 dB plate-return dip**, ~143 ms recovery; their post-fader combination produced ~3.25 dB wet reduction at kick. This is MIDI-timed ducking, not proof of external audio sidechain.
- [ ] **D05 — Gain and automation consistency:** When changing a track's operating gain, update matching automation base and points where required. Phase7 showed that base-fader changes can be inaudible because existing automation overrides them.
- [ ] **D06 — Low-frequency geometry:** Keep sub/bass predominantly central unless an explicit verified creative exception; inspect side-energy and correlation **by band**, not just global correlation. Stereo width should be selective, not indiscriminate.

### E. Build musical depth as a deliberate system

- [ ] **E01 — Dry foreground first:** Keep rhythmic chord/kick/clap attacks intelligible. Add space behind identifiable source notes; avoid a uniform distant wash.
- [ ] **E02 — Shared short room:** Send related instruments into a controlled common room for cohesion. Phase17 established native aux routing; Phase31/41 adjusted room pre-delay, width, filtered tails and level.
- [ ] **E03 — Sustained background plate:** Use longer pad/atmospheric plate as separate depth plane. Phase30/31's revised pad and Phase43 pump improved the perceived bed. Test return filtering, release tail and post-fader interaction.
- [ ] **E04 — Rhythmic dual delays:** Use tempo-aware **eighth (~238.1 ms at 126 BPM)** and **dotted eighth (~357.1 ms)** with contrasting filters and position if useful. Phase34 introduced distinct editable delay returns. They are **not automatically ping-pong**.
- [ ] **E05 — Echo throws:** Automate return gain selectively near phrase endings or transitions, not constant high wetness. Phase39 reduced chord-delay returns by ~2.5 dB on chord attacks and restored them over ~333 ms, with selective +2 dB phrase throws.
- [ ] **E06 — Post-delay tail treatment:** A very short reverb after individual delays can soften echo repetition and make space feel continuous. Phase43 placed **~850/1000 ms** short reverb after existing chord delay+chorus chains.
- [ ] **E07 — Slow spatial evolution:** Carefully automate return filtering, modulation, width/pan and pad/plate level over sections. Phase41–42 explored this, but Phase42 changes were relatively small in measured full-mix difference (~0.01 relative RMS); tiny measurable changes do not guarantee audible artistic progress.
- [ ] **E08 — Phase45 optional expression:** Native EQ LPF and chorus automation on chords/pad, subtle delay modulation and selected hat development; **not yet an approved quality win**. Never mislabel native FX automation as actual unverified VST-internal modulation.
- [ ] **E09 — Spatial control audition:** Compare wet versus muted-*specified* returns, preserving all remaining internal/plugin effects. Do not describe such controls as fully dry if they are not.

### F. Construct the full song without losing the pocket

- [ ] **F01 — Arrangement map:** Plan phrase lengths, sections, entrances, contrasts, breaks, returns, peak and outro before multiplying loops. Phase18's longer arrangement was judged awkward despite adequate sounds; Phase19 imposed restraint. Phase24's 144-bar viability was an important intermediate step.
- [ ] **F02 — Establish musical identity early:** Phase38 corrected an overly restrained intro by using kick from the first beat, hats near bar 3, bass+chords near bar 5 and clap near bar 9, with a rising mix level. The correct entrance schedule is style-specific.
- [ ] **F03 — Preserve a defined anchor:** One compelling 8–16-bar groove should retain recognizable timing, sound and harmonic identity across the record; vary presentation rather than continuously replacing its foundation.
- [ ] **F04 — Harmonic narrative:** Build an intelligible relationship among tonic, departure, tension and resolution. Test the actual harmonic voices against bass roots. Phase36 made one 16-bar score with 8 bars C minor, 4 F minor, 4 G dominant; Phase37 aligned bass to Phase34's Cm/Ab/Fm/G chord family.
- [ ] **F05 — Role density by section:** Intro, groove, development, break, build, main peak and outro should differ in *what plays*, frequency activity, note density and ambience. Changing a label without changing events or automation does not create an arrangement.
- [ ] **F06 — Tension and release:** Use intentional bass/kick withdrawals, brief rests, filtered throws, pad holds, drum fills and pre-drop silence. Contrast is more important than continuous additional layers.
- [ ] **F07 — Locked melody-free sections:** Preserve the no-lead and no-new-arp policy throughout the arrangement; avoid rebuilding every climax with an unsolicited melody. Build interest with chord voicings, rhythmic variation, subtraction/entrance, bass response and controlled spatial effects.
- [ ] **F08 — Organic section development:** Alter a few meaningful parameters (chord voicing/timbre, hat subdivision, return level, phrase endings) in targeted 4/8/16-bar windows. Keep material outside the edited region untouched.
- [ ] **F09 — DJ-flow review:** Check that sectional energy is legible, the beat stays danceable, breaks are proportionate and transitions announce rather than confuse. Phase18's failure was **flow**, not merely duration.
- [ ] **F10 — Outro/resolution:** Finish with an intentional winding down, short reprise or clean tail; don't merely stop a loop. Preserve effects tails in the verified render.
- [ ] **F11 — Reference-form review:** The eventual main reference uses 118 bars at 126 BPM and an active intro, long no-lead groove, supporting ambience, repeated harmonic foundation, meaningful breaks and controlled climax. Treat this as **one accepted arrangement class**, not a default for all house songs.

### G. Mix without attempting to rescue bad composition

- [ ] **G01 — Gain staging and headroom:** Verify no inadvertent clipping in any audible stage, native fader/FX automation consistency and sufficient pre-master headroom; loudness is not source quality.
- [ ] **G02 — Kick vs bass balance:** Listen on repeat to the actual composite. Check 0–20 ms attacks, 20–100 ms bodies, note release overlap and low-end spectral occupancy *by section*. Whole-song spectral proportions are only descriptive.
- [ ] **G03 — Chord/pad balance:** Dry chord presence, body, pad bed and echo tail should each occupy a deliberate depth position; avoid the early loud/strange pad failure.
- [ ] **G04 — Transient hierarchy:** Kick, clap/snare and hat/shaker attacks should remain identifiable under the full chorus and late peak; compressor attack/wet blending changes can help without replacing the samples.
- [ ] **G05 — Midrange density and warmth:** Preserve audible fundamentals and useful harmonic body without boxiness or mask. Phase39–40 restored chord low-mid body and clarified bass in the full mix.
- [ ] **G06 — Stereo and mono:** Verify centered foundation, helpful side information in mid/presence bands and graceful mono sum. Monitor correlation, frequency-dependent side energy and subjective center stability.
- [ ] **G07 — Dynamics and space:** Compression, subtle saturation and shared room/plate/delay must complement, not conceal, the groove. Compare dry/source, FX-only and full-mix contexts where practical.
- [ ] **G08 — Arrangement-level mix automation:** Automation should differentiate sections (intro lift, break recession, delayed returns and pad width) without destroying the approved overall balance.
- [ ] **G09 — Translation:** Monitor headphones, speakers and small-device emulations; bass audibility and low-end weight are perception questions, not simple 30–90 Hz power targets.
- [ ] **G10 — Full-song context check:** Re-evaluate first groove, main peak, breakdown, return and ending. A full-master LUFS meter can conceal weak sections.

### H. Master only a good mix

- [ ] **H01 — Freeze the composition/sound balance:** Have a satisfactory mix candidate before optimizing delivery loudness. Phase20 showed that mastering hollow/dry sources doesn't make them professional.
- [ ] **H02 — Keep the editable master chain separate:** Store pre-master and editable native master; use only supported effect controls. Protect all non-master notes/instruments/routing during a mastering-only iteration.
- [ ] **H03 — Compare several bounded master candidates:** Test on representative dense and quiet sections before costly full-length renders. Phase44 evaluated candidates, rejected a true-peak failure, and selected the intermediate candidate.
- [ ] **H04 — Meter properly:** Compute LUFS-I (EBU R128), measured true peak with declared oversampling, clipped samples, crest/PLR, LRA and representative section dynamics. Validate exact 48 kHz / 24-bit stereo export when that deliverable is selected.
- [ ] **H05 — True-peak compliance:** For the current reference delivery the Phase44 result was **-1.413 dBTP**, zero clipped samples; a conservative delivery goal such as at or below -1 dBTP is a useful configurable starting gate, not genre law.
- [ ] **H06 — Loudness with restraint:** The approved Phase44 master was **-13.91 LUFS-I**; do not force every record to it or claim higher LUFS means higher quality. Select a target from distribution, sound and intended use.
- [ ] **H07 — Equal-loudness preference:** Compare approved mix and master using attenuation-only integrated loudness matching where appropriate, including representative musical sections; check bass and transient preservation.
- [ ] **H08 — Preserve both releases:** Store pre-master mix, selected master, project, receipts, audition comparisons and human/evaluator decision.

### I. Native audit, copyright and packaging

- [ ] **I01 — Canonical validity:** Strict schema, all notes/events, section coverage, licensed samples, registered parameters, no routing cycles, hash-stable snapshots.
- [ ] **I02 — Real plugin state:** Independent restore/readback with pinned binaries; patch and audio asset closure verified; native pitch calibration—not merely symbolic MIDI theory.
- [ ] **I03 — Native load and save:** Session opens/reopens, renders with exact routing/patch/automation semantics; no direct native JSON fabrication.
- [ ] **I04 — Immutable historical baseline:** Compare the intended change region and require unchanged source notes/FX/regions everywhere else. Preserve source and rejected candidates for regression.
- [ ] **I05 — Render consistency:** Frame count, sample rate, bit depth, non-silence, clipping, file hashes, FX tails and exact or bounded deterministic repeatability as appropriate.
- [ ] **I06 — Licenses:** Separate original content, documented CC0 drums and private third-party Vital presets. Never redistribute preset/component states without sufficient rights, even if rendered audio use is permitted.
- [ ] **I07 — Complete artifact:** Native `.scraft`, `.kuang.json`, MIDI, permitted patch/sample assets, pre-master/master WAV, report, quality-ledger, cue-point/excerpt audits, version/host provenance.
- [ ] **I08 — No false certification:** Technical gates can pass while listener quality is unknown; any subjective quality verdict requires suitable evaluation evidence.

## 3. Recovery and failure-routing decision table

| Failure observed | Likely correction scope | Do **not** reflexively do this |
| --- | --- | --- |
| Kick weak or plasticky | Substitute/retune source sample; adjust transient/tail in full pocket | Boost master, maximize or blindly lift all sub |
| Bass audible only on large speakers | Select harmonically richer patch; tune register/saturation, note length, bass/kick overlap | Copy someone else's sub-power percentage |
| Pad too loud, strange or dissonant | Re-audition patch, attack/release, actual pitch, base AND automation gain | Stack another reverb or pad |
| Track feels musically wrong despite correct key | Check **native** synth pitch-bend and real fundamental measurements; verify bass root/chord voicing | Assume correct MIDI means correct audio |
| Melody sounds weak/awkward | Recompose or remove it; compare no-lead arrangement | Add more notes or artificial ornamentation |
| Groove sounds stiff | Inspect velocity, ghost notes, swing, late/early percussion, kick/bass pockets | Randomize every note or double-swing |
| Mix flat/dry | Rework **source** and contrasting foreground/body/halo, shared room, filtered echoes and phrase throws | Loudness processing first |
| Mix muddy/washed out | Shorten/filter tails, reduce pad/return levels, protect dry attacks | Add more wet effects |
| Arrangement feels amateur/confusing | Simplify form; restore groove anchor, meaningful entrances and breaks | Add eight more sections/layers |
| Intro loses listener | Enter with musical identity earlier; stage kit and harmonic introduction | Always start all drums on bar 1 |
| Effects feel mechanical | Duck return at dry attacks; automate selected throws, modulation and return filters | Keep permanent maximum wet mix |
| Master louder but worse | Revert; compare matched; adjust dynamics with limited compression or revisit mix | Decide by LUFS alone |
| Technical proof passes but track sounds inferior | Keep reference incumbent; record qualitative rejection and diagnose category | Promote based on SHA, peak or spectral proximity |

## 4. How Kuang should actually execute this checklist

**Producer state machine:**

1. **Understand:** `ProductionBrief` with one key/tempo/role plan, user intent and restrictions.
2. **Research/select groove archetype:** Select a recognized house rhythmic family and build 2–4 contrasting *rhythmically coherent* kick/bass/clap/hat/percussion pockets, already using workable source sounds.
3. **Verify the groove's physical correctness:** Real host pitch, kick/bass onset and release, drum timing, low-end balance, source integrity, intentional microtiming and actual native playback. Invalid MIDI/host tuning cannot pass.
4. **BLOCKING GROOVE GATE:** Audition 8–16 bars and compare the groove incumbent at matched loudness. If it fails, revise rhythm/sample/patch/envelope and repeat; **do not proceed** to full-song work.
5. **Lock groove and design harmony:** Protect kick/bass/percussion rhythmic identity. Choose 4–16-bar chord motion and verify chord/bass roots, voicing and syncopation, with no generated lead/melody/arp.
6. **Map arrangement before expansion:** Draft 4/8/16-bar section grid of roles, breaks, builds, drops, transitions and outro. Expand by track removal/entry and production automation, not repeated recomposition.
7. **Audition compatible presets in context:** Test bass/chord/pad combinations over the locked nucleus. Preserve the groove; if swapping a sound weakens it, revert and recheck the groove gate.
8. **Produce and mix:** Calibrate stems by role; implement controlled room/plate/delay, phrase throws, sections and dynamics; audit both groove and song flow after the FX pass.
9. **Run a small bounded corrective loop:** Classify a failed dimension; modify only related variables; rerender the affected 8–16 bar region with tail; compare **at equal loudness**; keep/revert based on verdict.
10. **Master separately:** Evaluate 2–3 safe settings against representative excerpts. Do one full verified render of selected master, with configurable deliverable limits.
11. **Full-song final QA:** Audition/check intro, groove, breakdown, final peak and outro; verify complete artifact and exact native replay.
12. **Publish/learn:** Preserve editable private output and a machine-readable ledger of choices, failed candidates, runtime and quality evidence. Human feedback in development should improve the future evaluator rather than rewrite the reference.

**Revision loop invariants**

- Every trial names a *hypothesis* and one isolated editable scope; don't simultaneously replace synth, bass MIDI, compressor, reverb and master.
- Keep an incumbent. Reject a candidate when evidence is lacking or quality worsens. No automatic 'last candidate wins'.
- Use cheap symbolic/spectral screening **before** real VST audition; do not use synthetic tests to claim subjective listening quality.
- Cap number of candidates per role and per stage, native render duration, subprocess timeouts and total resource use.
- Allow a gate to return `UNKNOWN`/`NEEDS_LISTENING`. Until the model's perceptual evaluator is validated against human decisions, automatic 'professional quality achieved' is unsupported.
- Stop when all required stages are technically valid **and** the selected candidate passes the calibrated quality acceptance process; otherwise deliver the best technically sound candidate with explicit limitations.

## 5. Technical signals to collect by stage

| Stage | Useful measurements and objective evidence | Interpretation limit |
| --- | --- | --- |
| Planning | Genre/role consistency, tempo/key constraints, schema validity, source/license budget | No quality score |
| Groove | Kick/bass onset offsets, overlap times, note/velocity distributions, tempo grid, microtiming and syncopation | Human groove feel remains subjective |
| Pitch and harmony | Real audio fundamentals at reference MIDI pitches; cents deviation by register; chord/bass voice-leading, dissonance | Correct tuning does not guarantee good harmony |
| Sound selection | Stem loudness, attack/tail ratio, band-energy fractions, spectral centroid, width/correlation, normalized audition | Isolated spectral similarity does not rank musical compatibility |
| Ensemble | Time-frequency mask overlap, concurrent transient energy, role-specific prominence, section-dependent balance | A scalar 'unmasking score' is not sufficient to assert preference |
| Space | Wet/dry residuals, tail decay, effect return gain/automation, time alignment, mono correlation | More side energy or reverb does not imply better depth |
| Arrangement | Section event counts, changes per 4/8/16 bars, duration of drops/breaks, rhythmic continuity, harmonic cadence, cue points | Novelty is not automatically compelling |
| Mix | Section LUFS/RMS, peak/crest, low/mid/high energy, stereo/mono compatibility, onset-window profiles | No universal band energy or level curve |
| Master | EBU R128 LUFS-I, true peak, LRA, PLR/crest, clipping, loudness-matched A/B | Loudness cannot replace musical quality |
| Native deliverable | Canonical/native hashes, exact note and asset closure, save/reopen, PCM format and authorized edits | Byte equality cannot prove audience approval |

**Calibration rule:** Choose tolerances only after measuring a corpus of approved and rejected tracks plus deliberately damaged examples. Reference values above are descriptive, not universal acceptance thresholds. Build separate tests for quiet deep house versus dense club/peak-time styles. Avoid overfitting to the 118-bar reference.

## 6. Historical learning ledger (what actually happened)

These are **documented development events**, not 45 automatically verified listener wins.

| Phase | Lesson captured |
| --- | --- |
| 2–4 | Strict prompt→SongSpec→editable composition, native production/refinement. Composition and parameter validity are foundational, not quality proof. |
| 5 | Focus on a compelling 16-bar groove before building a record. |
| 6–7 | The additional pads and width were not automatically beneficial; user heard loud/strange pad balance. Tune envelope and automation, not just pad counts. |
| 8–10 | Real performance gestures, upper-bass harmonics, kick/bass translation and spatial development; user preferred Phase9 C bass and Phase10 D lineage. |
| 11 | Establish real live Vitalium native plugin workflow; never assume mere Vital binding example proves host support. |
| 12–13 | Short factorial groove/sound experiment did not clearly improve listening; sampled drums made the kick substantially better. |
| 14–15 | Real -200 cent native plugin pitch fault produced musical incoherence; fix host pitch initialization, preserve source, verify audio. |
| 16–17 | Original pitch-correct Vital sound palette was a qualitative leap; human approved subsequent coordinated mix/space improvement. |
| 18–19 | Expanded long arrangement lacked dancer-friendly flow; editing/restraint was needed, not unlimited sections. |
| 20 | Mastering an unconvincing hollow/dry source is ineffective; source-first production. |
| 21–23 | Groove proved stronger without the unwanted lead; repeated alternative melodies rejected; Phase23 no-lead bed approved. |
| 24–26 | Long melody-free groove became viable; fix awkward moments and direct harmonic cadences and intro instead of endlessly adding layers. |
| 27–29 | Better sampled clap/bongo/percussion; fully editable native integration; stereo-doubled sounds with differentiated time/pan/EQ and center attack. |
| 30–31 | Qub1t pad source, pad/side-blend, room space, kick transient management and low-mid translation. |
| 32–34 | Original coherent bass/keys/pluck pocket, more economical arrangement, two different tempo-locked delays, extended harmonies and phrase effects. |
| 35 | Source-pitch-grid interpretation remained uncertain; don't treat automated extraction as verified MIDI transcription. |
| 36–37 | Directed 16-bar score within a 118-bar production; align bass roots to retained chords; lead-free mix preferred. |
| 38 | Active intro with staged kick/hats/bass/chords/clap replaced a low-energy opening. |
| 39–40 | Modest percussion microtiming, brighter clap, differentiated EQ, controlled dynamics and delay attack duck/throws. |
| 41–42 | Shared room width, return filtering, subtle spatial motion, selective echo throws; avoid mistaking minuscule measured differences for meaningful wins. |
| 43 | Approved pulsing pad/plate space, actual 423 kick onset envelopes, and short room behind chord echoes. |
| 44 | Separate, selected native club master; bounded candidate tests, reject unsafe true peak, preserve pre-master. |
| 45 | Fully editable FX filter/chorus/delay modulation experiment; technical proof only. **Awaiting human listening decision**, so do not overwrite the approved reference. |

## 7. Implementation milestones, in dependency order

- **M0 — Freeze the reference and ledger.** Hash and inventory Phase43, Phase44 and optional Phase45, preserve originals, transcribe approved/rejected *listening* decisions separately from technical reports. Add this playbook as engineering guidance.
- **M1 — Single musical intent and role contract.** Build on the existing shared `SongSpec` fix; add future explicit role fields without changing canonical 0.1 until justified.
- **M2 — Groove archetype library and blocking gate.** Implement established 4/4, offbeat, shuffle, minimal, jackin and percussion-led *original* rhythm templates. Compare real kick/bass/clap/hat source combinations in 8–16-bar context. Record groove/timing fingerprints, accepted versus rejected examples and strict revision budgets. Never auto-promote an unverified subjective score.
- **M3 — Harmonic loop and arrangement mapper.** Compose compatible chord structures and an explicit 4/8/16-bar track-presence/FX plan before expensive full-song rendering; preserve the accepted groove and do not generate a standalone lead.
- **M4 — Context-compatible preset audition.** Compare actual Vital/Vitalium bass/chord/pad candidates in locked-groove context and retain incumbent sources when alternatives do not improve the ensemble. Build technical/quality evidence separately.
- **M5 — Coordinated FX/mix.** Reusable shared return graph, send duck/throws, pad/plate movement, per-role gain staging, attack preservation and section automation.
- **M6 — Bounded automatic revision.** Gate→diagnose→propose scoped change→render targeted comparison→evaluate→keep/revert; resource budget enforced.
- **M7 — Native master and release audit.** Measured final master with immutable pre-master and exact editable output, full-song test suite, license compliance and objective/subjective caveats.

## 8. Key rule for Kuang agents

**Do not treat the existence of an effect or a passing technical test as the completion of a musical stage.** The objective is to make a consistently compelling house song. The reference offers *specific reusable ideas* and *hard failure lessons*, not a magic preset, exact EQ profile, standardized 118-bar form or fixed score. New songs should be distinct, but achieve comparable confidence in groove, sound identity, harmony, depth, arrangement, balance and delivery.
