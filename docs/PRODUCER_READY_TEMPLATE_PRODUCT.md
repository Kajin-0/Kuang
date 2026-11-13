# Kuang Product Contract: One-Prompt Producer-Ready House Templates

Status: **product direction and acceptance specification**, not a claim that these features are currently implemented. November 2026. Primary development goal supersedes earlier interpretations of Kuang as a self-sufficient autonomous composer striving for unique Suno-style songs. See also [HOUSE_PRODUCTION_PLAYBOOK.md](HOUSE_PRODUCTION_PLAYBOOK.md), [HOUSE_GROOVE_STANDARDS.md](HOUSE_GROOVE_STANDARDS.md), and [HOUSE_STYLE_STANDARDS.md](HOUSE_STYLE_STANDARDS.md).

## 1. The actual product

**Kuang is a reliably high-quality, partly randomized house music template generator. A single prompt should do most of the repetitive production work so a human producer can concentrate on the remaining artistic decisions.**

The user describes the output as **about 80% of a song already complete**. This is an *intended producer-experience outcome*, **not** a numerical similarity metric, labor estimate or subjective quality proof. Generic, recognizable house structures are acceptable—and often desirable—if the tracks sound cohesive, groove effectively, mix well and open as editable sessions. Unique songwriting and unprecedented sounds are not primary goals.

**Product promise to work toward:** Prompt → complete instrumental house arrangement → producer-ready, well-organized native DAW session with actual editable instruments/MIDI/mixer/FX/automation → reliable premix and master starting points → authorized assets and cross-DAW continuation options where supported. No false implication that SoundCraft `.scraft` sessions can already be opened natively in Ableton, FL Studio, REAPER or Logic.

**Human retains control:** Producers should be able to change kick sample, bass preset, chord voicing, harmony, part timing, effect sends, filter automation, track arrangement, transitions and final master without rebuilding the track. Favor intelligible and conventional instrument organization over clever custom automation that is difficult to edit.

**Deferred features:** Standalone lead melody, topline, arpeggio hook and vocals. No generative "novelty" requirement. Do not make Kuang a waveform-only prompt-to-audio generator.

## 2. Production hierarchy — nonnegotiable

1. **Genre-profile selection and GROOVE FIRST.** Prompt chooses deep, classic, funky/jackin, minimal, percussion-led and other specifically supported house profile. Generate 2–4 *coherent* rhythmic archetype candidates with actually usable kick/bass/clap/hat sources. Audition in true native mix; groove is a blocking quality gate, not a weighted component that can be offset by fancy effects.
2. **Simple musical skeleton.** Pick compact chord progression/voicings and the 4/8/16-bar phrase grammar. The harmonic rhythm should serve the existing bass and groove. An independent lead is deliberately absent.
3. **Arrangement as part-presence automation.** Use the locked 8–16 bar nucleus to map an entire song by introducing/muting/extending the SAME musical roles, with breaks, builds, returns, intro/outro and deliberate variation. Avoid inventing new melodies in each section.
4. **Context-compatible sounds.** Automatically shortlist and audition real, accessible, rights-compatible instruments/samples/presets. Evaluate combinations, not isolated timbral proxies. Preserve the rhythmic identity of the approved nucleus when replacing sounds.
5. **Premix and production polish.** Role-specific gain staging, group/bus layout, kick/bass articulation, chord/pad balances, shared room, tempo-synced delays, subtle throws, controlled dynamics and automation. No preset library without license/source checks.
6. **Master and packaging.** Prepare an editable pre-master plus a controlled mastered preview; verify true peak, no clips, native reopen, MIDI, exact instruments and effect state, licensing and all audible sections. Mastering never repairs a fundamentally weak groove.

Once the groove is selected, later stages must **recheck it after any patch, bass note, effect or automation change**; a dull new preset or "improved" master is not allowed to silently degrade it. Use small, bounded revision loops with a preserved incumbent and source hashes.

## 3. Target experience: one prompt and a useful, completed arrangement

Example: `"Make a warm deep-house track at 124 BPM, 4/4, about four minutes, punchy offbeat bass, spacious chord stabs, subtle percussion and no lead."`

Kuang should:
- Understand the stated tempo, style, mood and no-lead constraint once and keep one validated musical specification throughout composition, preset audition, FX and export.
- Select a recognizable groove family, compare a few coherent kick/bass/percussion combinations, and lock a good 8–16 bar pocket.
- Compose accessible chord stabs/voicings, lay out a full house structure and transition grid, and introduce/retract existing parts to keep development musical.
- Pick and validate appropriate kick/clap/hat samples and bass/chord/pad instruments, preserving real plugin pitch and patches. A producer may have to supply/install their own preset library; unknown-license plugin states must stay private.
- Make an **artistically usable rough-to-finished mix**: intelligible kick/clap/bass, balanced chords, depth/FX, section automation, sensible pre-master headroom and a non-clipping mastered preview.
- Export a complete, editable native session and explain clearly which controls remain readily adjustable.
- Preserve a deterministic seed: the same prompt/seed/asset versions reproduce the same creative decisions (subject to declared audio-render tolerances); new seeds offer *reliably coherent* alternatives within the same quality envelope.

**Do not ask users to guide 45 serial production revisions before they get a workable template.** Those 45 experiments were the development/training process for Kuang's **first-pass competence**, not the end-user workflow.

### The important usability test

A competent house producer should be able to open the session and make high-leverage changes:
- swap the kick or clap sample;
- replace a bass or chord Vital preset;
- revise two or four chord voicings;
- rearrange a break, entry, or build with the existing tracks;
- tune one reverb/delay return or pump depth;
- adjust the master to taste.

All such actions should be possible without flattening the project, reconstructing synth state, manually realigning stems, or correcting broken routing. The producer's subsequent creativity is **the product's intended use**, not an indication that Kuang failed.

## 4. Minimum output contract

**Primary:** one verified, editable and clearly named native SoundCraft `.scraft` session (until other DAW native adapters are genuinely implemented), with exact preset/asset references and authorization rules, plus canonical project snapshot and type-1 MIDI.

**Listening:** full rendered stereo WAV and separate **unmastered / pre-master** and master-preview versions. Specify actual format, duration, sample rate, bit depth, clipping, true peak, loudness metrics and rendering provenance.

**Producer handoff:**
- organized named tracks and groups such as KICK, CLAP/SNARE, HATS, PERCUSSION, BASS, CHORDS, optional PAD, DRUM BUS, SPATIAL RETURNS, MASTER;
- intentional send/return topology and editable FX/automation, not hidden destructive processes;
- clear section markers, tempo/key, chord chart and part-presence grid (intro, main groove, breaks, builds, return, outro);
- optional aligned **per-role stems** and MIDI for use in other DAWs, with a declaration of dry, wet, send/return or master processing so their combination is understood; this is *portability of material*, not proof of native project interchange;
- preset/sample provenance and license limitations; absent/unverified third-party assets are disclosed, never silently bundled;
- reference/seed/groove-archetype settings and a concise decision report that distinguishes objective validation from subjective evaluation.

**No false portability claims:** External VSTs and third-party samples may need separate installation, just as in commercial DAW template workflows. If plugin resources are unavailable, use a clearly labeled preview/stem route without pretending plugin parameters are editable in an unrelated DAW.

## 5. Quality means reliability across MANY independent generations

A single polished historical reference is a quality anchor but does not show that the prompt-to-template generator is reliable. Evaluate a **matrix of fixed prompts and seeds** rather than one continually polished song. Useful profiles: straight/deep/funky/minimal/percussion-led house; low/medium/high energy; no-pad/with-pad; multiple keys and tempos; 16-bar and full-song outputs; alternate kick/bass sound combinations.

### Hard acceptance and reproducibility (must be tested in future engine)
- 100% of *published successful* templates have validated source/licensing policy, no crashes, no broken song roles, consistent tempo/key/seed and a native session that loads/saves/reopens and renders; failures should be explicit, not silently published.
- 100% of published templates retain all promised editable roles; no unsupported lead/arp/vocal appears in the no-melody default.
- 100% of published final outputs pass configured PCM format, clipped-sample and true-peak limits; pre-master/master differ intentionally with separate receipts.
- User-protected groove MIDI/patch/sample identities remain stable unless an authorized revision documents exactly why they changed.
- All timing/swing transforms are traceable; all source sample/preset hashes and dependencies are known; missing assets and license uncertainties trigger a safe, explicit result.
- Every attempt has a bounded number of candidate evaluations, finite subprocess timeout and resource budget, with no uncontrolled large renders or repeated full-song rebuilds.

### Musical and producer-experience evaluation (requires auditions)
- **Groove satisfaction:** blind or level-matched comparison against approved pocket exemplars and deliberately weak controls; evaluate separately from loudness and source-timbre novelty.
- **Template readiness:** independent human producers rate how usable each output is *before edits* and identify what correction work remains. Report pass rate, median edit time or count, severe-fix count and confidence intervals only after collecting actual test data.
- **Mix quality:** representative sections judged for kick/bass, harmonic clarity, FX depth, balance and mono/speaker translation; compare both full mix and premaster/master against reference.
- **Diversity within quality:** multiple seeds should not all sound identical, but a small number of familiar high-quality house formulas is acceptable. Distinct seeds must not produce obviously incoherent combinations.
- **Customization burden:** identify the ten most common manual interventions from producer sessions and automate the repetitive ones if they do not restrict artistic control.

**Do not translate the user's '80%' phrase into a fake machine score.** An eventual empirical proxy could be the reduction in human edit operations or median producer minutes-to-satisfactory-edit compared with a blank DAW session, but such numbers must be measured—not fabricated. A template passing file/loudness tests is not automatically professionally mixed.

## 6. Build for controlled randomization and first-pass success

Randomization should be applied **within a curated, compatibility-tested musical grammar**:
- house groove archetypes (kick/snare/hat/bass rhythm relationships);
- 2/4/8/16-bar variants that preserve a compelling pulse;
- sensible chord-progression families and close/sparse/inverted chord voicings;
- role-compatible and licensed drum samples, bass presets and chord/pad patches;
- measured arrangement treatment choices (entrances/withdrawals/fills/returns);
- safe delay/room/plate profiles and restrained FX automation patterns.

Random seed should choose meaningful combinations, not independent uniform random values for every parameter. Use constraints and conditional compatibility (e.g. bass patch tail vs kick decay; chord attacks vs clap; pad release vs arrangement break; reverb decay vs tempo). Reduce the number of generated alternatives when existing curated patterns repeatedly work.

**Prefer safe generic but professionally coherent over adventurous but weak**. New creative algorithms are permitted only when they repeatedly improve level-matched producer evaluations, not because they are more original. Keep the incumbent and rollback mechanism.

## 7. Implementation roadmap (order of real leverage)

- **P0 — Product handoff contract:** Freeze the explicit editable-template output shape and the 45-phase reference evidence. Add section role/FX maps, pitch/role/source receipts and a producer-facing setup/compatibility statement. Separate editable native session from portable MIDI/stems.
- **P1 — Reliable groove generator:** Curated 8–16-bar groove library, compatible kick/clap/bass sources, multiple sample/patch candidates, real native audition and a blocking groove gate. Groove is the highest-priority human-evaluated dimension.
- **P2 — Chord/arrangement template engine:** 2–8-bar chord loops or justified longer phrases, role-based section activity maps, 4/8/16/32-bar structure, no standalone melody, readable DAW markers.
- **P3 — Sound compatibility + per-role mix:** Contextual VST/sample audition, native tuning checks, kick/bass masking, pre-fader/stem calibration, reliable role balance.
- **P4 — Repeatable house production techniques:** Safe bus/FX routing, real controlled reverb/delay returns, intentional section automation, kick-onset pumping, transitions/turnarounds and robust premaster/master rendering.
- **P5 — Multi-prompt reproducibility matrix:** Fixed prompt/seed suites, native reopen, profile exceptions, independent producer ratings and regression tests against the Phase43/44 benchmark. Measure template usefulness rather than file-only pass rate.

This direction reuses Kuang's typed schema, transaction/locks system, real SoundCraft export and pitch-correct Vitalium adapter. It does **not** authorize replacing those components, adding web SaaS services, claiming other DAW native support or publishing private patches.

**Commercial-house evidence:** consult [HOUSE_REFERENCE_CASE_STUDIES.md](HOUSE_REFERENCE_CASE_STUDIES.md) and [HOUSE_REFERENCE_TRACKS.json](HOUSE_REFERENCE_TRACKS.json). *Losing It* (FISHER, 2018) is a useful example of strong core rhythmic recurrence plus part-subtraction, related bass variation and selected percussion entrances. The documented deconstruction is a third-party remake: use genre grammar, not proprietary musical content, and keep user-approved Phase43/44 as the primary sound-quality anchor.

## 8. External workflow analogues (research, not implementation dependencies)

- [Ableton: Default Set and Template Sets](https://help.ableton.com/hc/en-us/articles/209067189-Default-Set-and-Template-Sets): producers use pre-routed, preset-loaded sessions as editable time-saving starting points.
- [Ableton: Live 12 exporting audio/stems](https://www.ableton.com/en/manual/managing-files-and-sets/): separate aligned tracks/returns, export with or without processing, and separate native session and render deliverables.
- [Ableton: Collect All and Save](https://help.ableton.com/hc/en-us/articles/209775645-Collect-All-and-Save): self-contained project samples while external plugins still require separate installation.
- [iZotope Neutron 5 assistant](https://www.izotope.com/en/products/neutron/features/mix-assistant): automatic per-audio initial mix chain plus producer adjustment; a useful precedent for treating automated mixing as an **editable starting point**, not a closed final verdict.

No external software or paid plugin is required to adopt this product specification.
