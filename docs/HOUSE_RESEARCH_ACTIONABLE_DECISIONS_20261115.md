# House Production Research — Evidence-to-Engineering Decisions

Review date: 2026-11-15. Source supplied by user: `deep-research-report.md`, *Professional House Music Production: Technical Research Review* (185 lines). This document is a **distilled actionable interpretation**, not a reproduction of the entire third-party research report and not evidence that all claims in it have been independently validated.

## Product objective and most recent listening context

Kuang is a local-first, one-prompt, native-editable house producer. The desired workflow is deterministic musical scaffold -> standard production -> context-aware producer analysis and reversible candidate adjustment -> genuine mix/master verification. First-pass sound quality must substantially exceed the user's perceived quality of ChordChord and approach the user-approved, painstakingly developed Phase44 sound **without requiring 45 manual phases**.

User judgment so far:
- Ten random complete 128-bar house songs were listenable; #01 straight F minor was favorite. Song #01 **bass A/B/C variant C was expressly preferred** (+2 dB bass plus four existing late-sixteenth phrase pickups). That preference is specific to #01.
- Cross-style bass A/B/C for #05 jackin C minor and #07 minimal Db minor sounded broadly similar on low-end-limited headphones. **Do not promote the bass gain/pickup recipe as a global default.** User prefers a strong rather than underpowered low end, subject to real kick/mix safety.
- More recent priority: **#05's chords sound wonky** (suspected preset), while **#07's chords seem too loud**. Do not burn compute on tiny low-end movements before resolving sound and role balance.
- Phase44 remains the professional production reference but is not a universal parameter template. Its bus routing, spatial sends, automation, phrase structure and final mastering were individually developed.

## Source credibility and limitations

Strong or directly checkable:
- Duncan & Orgs (2024), *Music Perception*, doi:10.1525/mp.2024.42.2.95 — 179 participants, 20 novel house excerpts, **two manipulated levels each** of low-frequency amplitude and bass syncopation. High/high had the highest groove perception among *tested* conditions. **No support for unlimited bass level or maximum possible syncopation.** https://doi.org/10.1525/mp.2024.42.2.95
- Sioros et al. (2014), *Frontiers in Psychology*, doi:10.3389/fpsyg.2014.01036 — moderate syncopation outperformed zero and maximal conditions on simplified synthesized music examples. Not a learned optimal count for commercial house. https://doi.org/10.3389/fpsyg.2014.01036
- Senn et al. (2016), *Frontiers in Psychology*, doi:10.3389/fpsyg.2016.01487 — expert/performance microtiming not inherently superior to quantized performances; amplified deviations can reduce groove. Source material is swing/funk, not a house-derived exact-ms policy. https://doi.org/10.3389/fpsyg.2016.01487
- Danielsen et al. (2023), *Popular Music*, doi:10.1017/S0261143023000041, discusses tight EDM grids and perceived timing shaped by **sound attack, envelopes, intensity and relative onsets**. Primary publisher page: https://www.cambridge.org/core/journals/popular-music/article/shaping-rhythm-timing-and-sound-in-five-groovebased-genres/BBC410F9849DB982AEBFACEA14D38F32
- Wichern, Robertson & Wishnick (2016), AES 141, Paper 9646 — multitrack **loudness loss** and problematic masking outliers; *some masking is intentional or musically acceptable*. https://aes.org/publications/elibrary/elibrary-page/?id=18450
- Smith (published online January 2025), *Twentieth-Century Music*, "Breakdowns and the Aesthetic of Disorientation in Festival-House Music": breakdown's **withdrawal of metrical/layer information** and subsequent restoration can create climactic impact. This is especially applicable to festival/club forms; not a mandatory dramatic break in minimal/deep. https://doi.org/10.1017/S1478572223000087
- De Man, McNally & Reiss (2017), JAES doi:10.17743/jaes.2016.0062 — relative wet loudness and early decay help predict perceived reverb amount; do not equate "more decay" with more professional depth. https://doi.org/10.17743/jaes.2016.0062
- Huang et al. (ISMIR 2025), `Aligning Text-to-Music Evaluation with Human Preferences`: MAD-vs-FAD reported **0.62 vs 0.14** correlations on their MusicPrefs test; these numbers are dataset/metric-specific, not Kuang's predictive quality. https://arxiv.org/abs/2503.16669

**Limitations:** References shown in the uploaded report use the original research agent's temporary citation IDs and cannot serve as independent source references here. Certain practitioner values (swing ~22–40% of a knob range; 20–30ms reverb pre-delay, genre BPM bands) are **contextual examples, not scientifically established optima**. Other 2026 wave-generative model claims are background rather than a demonstrated path to improvement for this editable deterministic DAW.

## What is already implemented — do not rebuild

| Report insight | Existing Kuang mechanism and evidence | Decision |
| --- | --- | --- |
| Stable 4/4 kick, offbeat bass, deliberate phrase pickup | `house_template`, `house_bass_syncopation`, `house_bass_producer_v2`; Phase44 and #01/#05/#07 sampled bass onsets already 100% offbeat; #01 user preferred C | **Retain**. Do not maximize offbeat count, randomize kick or auto-promote cross-style C. |
| Sound spectral fingerprints from actual notes | `house_sound_fingerprint`, `house_context_palette_native_probe`, `house_context_palette_v2`; actual kick/bass/chord 48k/24bit native stems | **Extend**, don't replace. Present implementation is a small-window FFT descriptor, not a perceptual audio/timbre model. |
| Prompt-aware source audibility | #01 original chords -34.42dB relative to kick; #05 -10.15dB and #07 -4.81dB; V2 requested alternative only for #01 | **Retain**. Quiet is not globally "bad" and loud is not globally "good." User now reports #07 chords too loud, #05 awkward. |
| Sidechain, filter, producer candidates | existing `house_full_arranger` kick-aligned bass/pad duck, `house_producer_review` and full-song opt-ins | **Refine conditionally**. Actual source #01 wet-only attempts changed midrange <0.2dB: rejects more reverb as a generic repair. |
| Native section-level analysis / pattern alternatives | `house_section_levels`, `house_full_arranger`, opt-in phrase development | **Use baseline**, not a new arranger. Ten-song audit had Main Drop-Groove A fullmix RMS confined to -0.073 to +0.225dB. |
| Mastering reference workflow | original Phase43->44 same-source compressor/maximizer optimization; Phase44 approved -13.91 LUFS/-1.41dBTP | **Generalize later**, after source and arrangement quality; no universal club LUFS target. |

## Ranked missing capabilities and actionable tests

### P0 — Source-aware chord/pad articulation **(next inexpensive decisive experiment)**

Primary evidence from user listening: #05 "wonky" chords and #07 chords too loud. Do not assume the diagnosis from RMS alone.
- #05: audit actual chord isolated note register, onset rise, note gate/release tails, sustained overlap, harmonic source content, and chord-on-bass transient collisions. Compare original preset to **at most two already runtime-verified** alternatives on identical chord MIDI and original other roles; independently compare if musical voicing or performance is the true cause. Do not blindly swap the preset or move bass and chords simultaneously.
- #07: retain original preset and MIDI; compare **−2dB and −3dB** bounded chord-fader+gain-automation offsets against untouched, in actual 8–16bar identical-native renders, gain-only fullmix LUFS-matched. Check chord audibility and pad relation across active sections, not just absolute RMS against the kick.
- Source-level features worth adding to existing fingerprint: attack 10–90% rise and time-to-peak relative to note-on; weighted transient crest 0–50/50–150ms; release/tail after note-off; onset-to-kick displacement including **effective acoustic attack**, not just MIDI timestamp; spectral body 120–1000Hz, presence 1–4kHz, stereo/mono energy. Compute on actual triggered notes with stem/clip alignment. No fixed "ideal attack" or source-name rule.
- Stop gate: no changes to other MIDI, bass/kick, patch library or original session; 0 clipping, native roundtrip, source hash, <0.2LU audition level discrepancy. Human groove/chord compatibility decides preference; descriptive FFT scores do not.

### P1 — *Earned* drop / section energy and diverse musical form

Most striking existing systemic weakness: all ten Main Drops measured nearly equal fullmix RMS to Groove A; form very similar. The report emphasizes **withdrawing rhythmic certainty** before restoring it, not merely boosting gain.
- Extend the existing long arranger rather than create another full-song composer. Add 2–3 *style/intent-conditioned* form policies varying break length/depth, 1–2bar pre-drop withdrawal, build release, percussion re-entry, outro decline. Preserve a clear DJ meter when appropriate; minimal/deep need not imitate festival-house disorientation.
- Automated measures per 4/8bar: kick-active fraction, bass-active fraction, layer count, 100/400ms p95 amplitude, short-term loudness, presence and stereo movement, gap duration, and musical boundary clicks. Distinguish contrast caused by **subtraction in build/break** from arbitrary +dB on the main-drop bus.
- Cheap test: freeze the chosen 8–16bar Groove A pocket and all source patches; compare two existing forms on #01 and one independent minimal/jackin case, not ten full renders. Listen for tension/release, not RMS alone.
- Critical safeguard: no long automation overlap/transition bug, no sudden unauthorized song end, no fixed "drop must be +3LU" invariant.

### P2 — Perceived-onset-aware groove and source synergy

The paper's most differentiating *new* idea for Kuang: actual sound morphology determines perceived onset. The stable macro-grid can sound loose/tight without jittering all note times.
- Extend existing sound fingerprint and producer review with role-specific envelope fit: MIDI note-on -> observed audio attack rise; note-off -> release energy; combined kick/bass beat overlap in 0–50/50–150/150–350ms windows; per-phrase velocity and rests.
- A timing decision must use a *directional specific hypothesis* (e.g. slow-attack shaker feels late and weak, dub stab smears syncopated pattern), not random ±ms humanization.
- Optional A/B: only **one** controlled note-envelope alteration or one relative percussion offset; fixed kick and source MIDI otherwise. Preserve original / inverse test and ask if the change is audible and musically better.
- Longer-term: conditional kick/bass harmonic reinforcement on small-system translation, checking inter-sample true peak, mono summation, source masking and no over-saturation. Bass "too sub-only" is a *hypothesis*, not a reason to impose a high-pass filter.
- Do not infer a single perfect phase offset: frequency-sweeping kick and layered synth bass have time-varying phase.

### P3 — Intelligent spatial/masking and master decisions

- Learn instrument function: sounds intentionally fused (pad+chord) vs distinct (kick+bass attacks). Replace raw FFT overlap with conditioned stem loudness-loss/active-window *outlier* heuristics and preference evidence. Masking reduction is not the whole creative objective.
- Reverb/delay design: dry-source audibility first, then actual wet/direct loudness, early decay, pre-delay, filtered tails, and transient smearing in the 100ms following notes; source-dependent shared buses. Do not copy the Phase44 wet chain onto everything (previous controlled transplant failed).
- Stereo width: measure by low/mid/high band and mono fold-down; prioritize clarity and robust club translation. Do not assert low frequencies physically lack localization or force every band mono.
- Mastering: **separate native premaster and editable compressor/maximizer/limiter candidates**; measure ITU/EBU-compatible LUFS-I, oversampled dBTP, LRA/PLR, 100/400ms crest/transients, sub-harmonic stability. Phase44 values are reference observations, not universal targets; EBU -23 LUFS is broadcast normalization, not dance music delivery target.
- Gain-only listening A/B across original and candidate required. An objective metric is an eligibility/diagnostic tool; human preference remains the quality gate.

## Research suggestions to defer / reject

- **Do not** maximize offbeat fractions, syncopation indices, stereo width, bass fader, compressor gain reduction, master LUFS, or low-frequency mono summation as single-goal objectives.
- **Do not** add blanket random humanization. Swing examples (55–60% of eighth-position vs 50%) illustrate substantial timing changes but are not source-independent optimum settings.
- **Do not** adopt MAD, FAD or another embedding metric as a stand-alone reward for "professional house" without validation on **Kuang's actual native multitrack music** and blinded listening. A text-to-music generative benchmark does not directly judge mix engineering, punch, sidechain or phrase structure.
- **Do not** train a new waveform-generation neural model or re-architect the native DAW. The research section on codec models/diffusion is valuable context but not evidence that it would beat the present sample/Vital/SoundCraft workflow more quickly than fixing source choices and mix/arrangement.
- **Do not** prescribe a single BPM, drop architecture, reference EQ curve, -14LUFS target, reverb predelay or frequency crossover for all house subgenres.

## Evidence and success protocol

All future experiments retain original projects, provenance, earlier failed outputs and private third-party states; use actual same-host SoundCraft native 8–16bar excerpts first. Prefer **one changed dimension at a time**, with reference and candidate using the same bounce path (the prior #01 bass A/B revealed a false peak delta when output paths differed). Normalize fullmix gain without limiting to <=0.2LU difference while retaining >=1dBTP safety. Distinguish hard integrity/safety gates from source-fitness diagnostics and *subjective listening*.

Any approved technique must be tested on at least one independent genre/key/song context before general default promotion; exceptions should stay opt-in. The user evaluated #05/#07 bass A/B as nearly indistinguishable on weak headphones; treat that as *inconclusive*, not a win or a loss.

**Recommended next task:** P0 cross-style chord source/level A/B on original #05/#07, before attempting new full-song mastering or additional bass-note complexity. P1 deliberate pre-drop withdrawal/return is next because its problem is already demonstrated across all ten songs.

## Notes for future AI producer integration

Structured intent -> native source fingerprints (register, onset envelope, note-off release, band/stereo energy) -> role-compatible source shortlist -> actual mix and section evidence -> bounded typed change proposals with explicit expected audible outcome -> safe real-native excerpt render -> reject null/unsafe interventions -> gain-matched producer listening -> full-song recheck -> separate mastered release.

Every proposed production operation should carry `why_this_source`, `musical_role`, `target_section`, `observable_hypothesis`, `changed_fields`, `source_hash`, `safety_checks`, `human_verdict`. No autonomous "better" label can be inferred from lower overlap or louder LUFS alone.
