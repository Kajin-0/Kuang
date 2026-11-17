# House Production Research — Evidence-to-Engineering Decisions

Review date: 2026-11-15. Source supplied by user: `deep-research-report.md`, *Professional House Music Production: Technical Research Review* (185 lines). This document is a **distilled actionable interpretation**, not a reproduction of the entire third-party research report and not evidence that all claims in it have been independently validated.

## Priority reset: high-impact House production before more bass micro-optimization

**Decision:** The user's supplied independent architecture review is directionally supported by the frozen ten-song native audit. Stop prioritizing marginal bass note-onset, fader, and tiny-parameter changes while full-song role presence, stereo space, energy arc and master are deficient. Keep the producer's rejected-growling-preset veto absolute. This review is a design critique, **not** an independent listening certification.

**Measured baseline:** The ten full songs have Main Drop vs Groove A median **+0.007 dB RMS**, Breakdown vs Groove A **−1.053 dB RMS**, whole-song side/mid **−27.34 dB**, and unmastered integrated loudness **−28.16 to −23.02 LUFS**. The 3-seed independent opt-in source-rescue batch completed only **1/3** productions. Compare Phase44 and Kuang in *matching music windows*; do not equate premaster with mastered LUFS or whole-track side/mid with groove-only side/mid. Claude's numerical chord-presence and register claims require independent same-method confirmation.

**Architecture correction:** `production_host.py` already implements auxiliary buses, post-fader sends and send automation; `master_bus.py` implements a terminal stereo bus; `house_master_preview.py` has peak-safe gain and restrained compression candidates. The deficiency is the lack of a high-quality **default usable House production recipe** connecting these capabilities. Avoid unnecessary new host abstractions.

### Ordered roadmap and measurable stop gates

**P0 — Reference fingerprint, no new DSP yet.** Compose the existing section/RMS, loudness, spectral and stereo analyzers into one reproducible CLI. On the **ten frozen native songs and Phase44**, report identical 4/8-bar windows for Groove, Breakdown and Main Drop: short-term LUFS plus RMS, 25–250Hz power, side/mid **by band**, mono fold-down below ~120Hz, role-stem 1–4kHz chord/pad audibility *when stems are verified*, true peak and crest. Keep premaster/master separate. ChordChord export comparison is worthwhile once a controlled same-prompt audio sample exists; it is a **product/workflow comparator**, not an assumed professionally mastered quality reference.

**P1 — High-effect native space and presence scene.** On **three existing frozen songs**, retain original kick, bass, MIDI, chord timing and source choices and test genuinely audible native shared-room/plate and chord echo/width scenes, rather than only very quiet −19/−15dB sends. Measure dry/wet levels, chord presence, stereo side/mid per band, onset smear and sub mono compatibility. No blind sub widening. **Stop after at most three qualified scene pairs** if none has demonstrably better signal behavior or if masking/phase loss dominates. No global default until cross-style evidence.

**P2 — Measured section energy and multiple forms.** The existing eight-section arranger is a baseline, not an adequate energy arc. Develop independent intro/build/break/drop/outro role scenes, pre-drop withdrawal where stylistically justified, actual hat/percussion/fill changes, and 2–3 arrangement grammars. Aim for *meaningful* breakdown withdrawal and a measurable drop step, subject to style and matched native short-term loudness. Do not treat a fixed LU target as a musical law.

**P3 — Premaster and master as separate verified artifacts.** Extend existing terminal bus and safe preview DSP to source-aware mix/master decisions; retain both, measure true peak, gated LUFS, crest/PLR, short-term dynamics and mono compatibility. Phase44 is a quality reference, not an EQ curve or universal LUFS preset. Loudness alone never certifies quality.

**P4 — Qualification and consolidation.** Release candidate remains opt-in `house-v3`, leaving legacy untouched. Use a fixed independent batch of at least 15 complete songs across multiple House styles/keys/seeds and report **all** attempts, failures, mix metrics, source diversity and section arcs. Keep corrupted project/asset violations, rejected-source identities, clipping and unsafe audio as hard failures; produce a **flagged draft** instead of no audio for unproven musical preference thresholds. Proposed exit criteria: at least **90% technically complete** and **80% acceptable in a separately calibrated consolidated listening review**. The producer should not be asked to judge intermediate variants.

**Bass subproject is parked unless a reference-calibrated mix demonstrates a dominant failure.** Preserve its strict safety checks, negative examples, native receipts and validated source rejection. No further arbitrary millisecond, fader or note-length sweeps to optimize a narrow ratio. Avoid another standalone document for every small change; update this roadmap and one scoped release report.

**Immediate next task:** run the common fingerprint on the ten frozen full tracks plus Phase44, then choose the largest demonstrated production gap for a bounded native 3-song A/B. Do not enable new defaults merely because software tests pass.

---

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


### P2 opt-in drum section-scene implementation — November 17, 2026

The existing 128-bar phrase-development arranger still cloned principal Groove A hats and snare throughout Main Drop even when bass/chord phrases changed. The new **opt-in** source-preserving `kuang/house_drum_scenes_v1.py` layer acts on the assembled full-house MIDI arrangement after existing phrase development. It does not modify original kick/bass/harmony tracks, their mixer/FX/automation, source samples, Vital presets, or the default arranger.

The bounded recipe: Groove B withdraws existing hats during the final beat of every second 4-bar phrase; Build uses two short pickups from the **already-selected snare voice** in its last bar; Main Drop adds sparse late-bar hat pickups and bounded accents, using its existing hat instrument and pitch. Section records explicitly count added, removed and accented notes. The recipe is exposed as `--drum-scenes-v1` for full-length groove-template one-prompt creation and rejects duplicate application. No independent melody is added.

**Test evidence:** The focused local `tests.test_house_full_arranger` suite passed **12/12** on the authorized VPS immediately before desktop-tool quota exhaustion, including a three-seed/four-style matrix, source immutability, locked kick/bass/harmony, valid MIDI and deterministic non-default behavior. Independent quick checks on four styles showed identical Groove A/Main Drop **hat-bar fraction falling from 1.00 to 0.75**, while kick remained **1.00**, bass/chord phrases were unchanged, and the build's two snare pickups were inserted. This measures *structural contrast*, not production quality or listener preference. Newly published GitHub CI must independently confirm the committed copy.

**Native gate still open:** A controlled SoundCraft eight-bar Main Drop test was attempted on frozen jackin #03, but its test-harness crop retained silent optional MIDI tracks, then orphaned automation targets after removing them; native graph validation correctly refused those attempts before rendering any candidate. A corrected version of the harness was prepared locally, but Remote Desktop Commander reached its monthly access limit before it could run. **Do not claim native audio success or promote the drum-scenes default.** The private experiment and failed attempts remain on the authorized VPS under `.local/house-v3-drum-scenes-native-20261117/`. Once runtime access resumes, retest the cropped excerpt using a proper owner/automation filter, compare native A/B WAV hashes, kick/bass stem invariance, clipped samples, true peak and short-term loudness, then proceed to multi-song arrangement scenes only if that test passes.

**Stop gate:** No additional fill or percussion complexity until actual audio demonstrates a changed, non-clipping Main Drop without damaging kick/bass groove. This is the first concrete opt-in P2 drum-scene implementation, not the complete House-v3 P2 arrangement system.

---



### P2 native excerpt crop repair and reproducible SoundCraft A/B — November 17, 2026

The last attempt to natively compare the new drum scene on frozen jackin #03 was blocked by the native host's intentional requirement that *every MIDI channel must have sounding notes*. Cropping Main Drop left silent optional roles, and the first attempted cleanup forgot automation lanes aimed at their effect instances. Neither attempt produced a successful native-render comparison.

That harness defect is now addressed in the **reusable, tested** `kuang/house_native_excerpt.py` helper: use Kuang's canonical `gestures.crop`, delete silent MIDI roles, filter automation against **retained track IDs and retained effect IDs**, remove orphan locks, revalidate, run `production_host.graph_contract`, check active kick and bass, and prove the frozen parent project hash is unchanged. Explicit crop receipts distinguish DSP reset from a continuous full-song bounce. New `tests/test_house_native_excerpt.py` covers deep/minimal/jackin crops and compares actual protected-role MIDI events between opt-in drum scenes and original.

The new `tools/house_v3_drum_native_ab.py` is an **opt-in native SoundCraft runner**, not a successful completed render. On the authorized workstation/VPS with existing private audio assets, run from the Kuang workspace:

```sh
python -m tools.house_v3_drum_native_ab \
  --source .local/ten-song-v1-03-jackin-20261115 \
  --out .local/house-v3-drum-main-drop-native-20261117 \
  --soundcraft /home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli \
  --library .local/producer/libebur128.so
```

The runner refuses overwrite, verifies each canonical session after save/reopen, retains unchanged private source inventory, proves kick/bass/chord/snare event signatures match A/B, requires hat MIDI to differ, requires native WAV checksums to differ, checks peak/clips and compares relative LUFS. It stores complete A and B recordings separately, plus a finite audit summary. It does **not** label music as listener-approved or enable `house-v3` automatically.

**Status:** the earlier committed P2 symbolic regression CI passed. The new crop helper, test and A/B runner were published to the experimental branch; their fresh CI status must be checked separately. The actual native A/B still requires authorized VPS access, which is unavailable in this conversation because Desktop Commander reached its monthly usage limit. The next engineer/agent should *run that exact tool first* before new arrangement complexity, then continue only if native validation and groove-preservation checks pass. No intermediate producer listening request is required.

---

