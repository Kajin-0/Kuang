# Kuang: incremental architecture and agent handoff (2026-11-14)

**Mandatory for the next agent:** Read this file, AGENTS.md, and docs/PRODUCER_READY_TEMPLATE_PRODUCT.md *before changing code*. The user's explicit direction: **build on the existing Kuang work; do not start over from scratch.** The purpose of research-driven upgrades is to strengthen its proven production pipeline, not replace it with a second composer, second DAW, new incompatible schema, or separate speculative V2 engine.

## Actual product objective

**One prompt -> a dependable, high-quality, mostly finished, fully editable house production/template.** The intended approximately 80%-complete outcome means a useful producer handoff, *not* a machine-generated quality score. The user wants **different strong-sounding songs across different prompts**, with a physically convincing kick/bass groove, harmonic clarity, varied but coherent musical identity, arrangement, sound sources, mix, and master-preview starting points. The authoritative existing product contract prioritizes reliability and editable producer templates over artificial novelty, arbitrary diversity quotas, forced standalone lead/vocals, or Suno-style waveform-only output. Producer editing afterward is part of the intended workflow.

### Preserve these proven components

| Existing module | Already working | Permissible incremental extension |
| --- | --- | --- |
| kuang/song.py, SongSpec, rules_plan | typed prompt/key/tempo/progression/energy planning | optional versioned musical-plan metadata; preserve explicit key, Roman progression, seed, no-lead intent and canonical schema |
| kuang/composer.py, kuang/production.py | composition, chord MIDI, existing effects and production roles | consume validated enrichment without rewriting the core composer |
| kuang/house_template.py | four genre profiles, existing groove/impact modes | bounded opt-in variation; maintain stable legacy path |
| kuang/house_harmony.py | simple/extended harmonic correctness | coherent progression/voicing/voice-leading enhancements |
| kuang/house_harmony_interlock.py | style/seed/bass-aware chord articulation | source-envelope-aware evaluation if native audio evidence supports it; keep opt-out |
| kuang/autonomous_palette.py, kuang/autonomous_create.py | private Vitalium source verification, selection, single-prompt orchestration | bounded context-aware source pairing, no weakened security or unlimited rendering |
| kuang/house_native_pair_audition.py and kuang/house_source_fit.py | real bounded 2x2 kick/bass mix auditions and diagnostics | reuse to compare *actual musical context*, never turn LUFS/FFT into a subjective winner |
| kuang/house_full_arranger.py | edit-preserving 96/112/128/160-bar arrangements | integrate richer theme/section plan, NOT another arranger |
| SoundCraft adapters, native project schema, sampled-instrument and Vitalium adapters | save/reopen/render, editable MIDI/FX/automation, source and host integrity | preserve host contracts, presets, asset hashes and project editability |
| kuang/house_master_preview.py, loudness and existing tests | peak/LUFS measurement, verified audio previews | keep safe delivery; mastering does not rescue a weak mix |

All relevant prior reports, code, tests, sample assets, phase releases and failure receipts stay in place. Do not overwrite them.

## Historical evidence: what works and what failed

- **Phase43/44 private mix** is the user's *approved quality reference*. Its successful sound evolved through many production phases; Phase44 terminal mastering alone did not create the groove/harmony balance. Never duplicate its score or force its effects values into every generated song.
- **Candidate D** (licensed CC0 Deep-01 kick + verified private Bass - Insanity Vital preset) was the user's preference **among four controlled C-minor pairings**, not a universal bass/kick default or a whole-song professional approval. Keep its native/audio evidence intact.
- A fixed Phase44-derived effects-policy experiment at commit c10dbd4 **sounded horrible** and was reversed by 5694cce. Do not silently reintroduce that FX/routing recipe.
- **Harmony interlock** at commit 89e07e2 produced an audible improvement reported by the user. The opt-in change passed 47 focused tests over eight style/key/seed combinations, plus two controlled native comparisons and two fresh single-prompt SoundCraft/Vitalium renders. This is encouraging but not a universal music-quality certification.
- **Generalization gap:** the two fresh independent one-prompt outputs (jackin in B-flat major, 128 BPM, seed 83; deep in E major, 123 BPM, seed 67) *both* selected Biow Bass 2 + SNFKFutureBounce Loaded Chords and *both* used the same four-degree [0,4,5,3] progression transposed to different keys. Their different MIDI timing does not establish genuinely diverse musical ideas. Improve source/progression choices *only when musically coherent*; never enforce diversity by random patch swaps or incoherent harmonic substitutions.
- Native SoundCraft/Vitalium, five separately selected CC0 sampled drum sources, deterministic manifests, native reopening and controlled mastering/level diagnostics already exist. **Do not rebuild this infrastructure.**
- The active development branch is feat/groove-first-template-mvp, and PR #1 is intentionally draft. Main and the original Phase44/45 releases must remain unchanged until broad musical acceptance.

## Implementation sequence: add, verify, preserve

1. **Inventory** the actual branch state, AGENTS.md, producer product contract, recent commits, current native orchestration, historical reports, existing source receipts, tests, and authorization/host constraints before touching code.
2. **Add a narrowly scoped versioned musical-plan layer** above existing SongSpec; do not introduce a breaking schema revision simply because planning is more sophisticated. Keep compatibility with explicit chord progression requests and earlier output files. Possible plan dimensions: coherent stylistic progression families, harmonic rhythm, voice-leading intent, recurring bass/chord identity, and section-development grammar. Do not force all these features into one change.
3. **Reuse current house_template and harmony_interlock** for rhythmic/groove construction; enrich the existing composer/harmony roles while retaining the prior MIDI version as an A/B and rollback control. Keep the Phase44 reference separate.
4. **Reuse native source audition and private adapters** to evaluate a few actual compatible kick/bass/chord combinations with *the notes and register of each generated song*. Cap candidate count, CPU time, and total renders. Preserve original selected sources as fallback and do not alter private-license constraints.
5. **Reuse house_full_arranger** to expand a genuinely good 8–16-bar nucleus into long-form structure. Do not start costly full-song renders until the short core passes independent listening.
6. **Test more than one song**: at least three prompts spanning different house styles, keys, tempos and seeds. Validate deterministic reproduction, musical-theory consistency, output editability, native save/reopen, original-source hashes, asset provenance, zero clipped samples, LUFS/true-peak safety, and actual musical variation. User listening at matched loudness determines musical quality; technical thresholds alone cannot.
7. **Promote conservatively**: new behavior should be opt-in/versioned, old behavior reproducible, and rejected/failed versions archived. Do not merge a draft branch or declare professional quality without cross-prompt listening evidence.

### Mandatory STOP gates

- Stop for any broken native reopen, changed locked MIDI/instrument state, incorrect pitch mapping, missing asset/rights verification, new unbounded processing, silent source fallback, clipping or other unexplained host drift.
- Stop if code changes replace established planning/arrangement/renderer internals without demonstrating a genuine need and preserving their contracts.
- Stop if progress is measured by phase/commit count, proxy metrics, or excellence of a single overoptimized reference instead of multiple independent musically convincing results.
- Do not claim a technical test, waveform metric, or frequency mask score proves sound quality. Keep old results and label all perceptual statuses accurately.

## Reading order and handoff

1. docs/PRODUCER_READY_TEMPLATE_PRODUCT.md (authoritative scope; templates/editability above novelty).
2. docs/HOUSE_PRODUCTION_PLAYBOOK.md, docs/HOUSE_GROOVE_STANDARDS.md, docs/HOUSE_STYLE_STANDARDS.md (existing researched production standards).
3. docs/HOUSE_HARMONY_INTERLOCK_GENERALIZATION_20261114.md (latest harmonic improvement and independent examples).
4. docs/HOUSE_NATIVE_KICK_BASS_CONTEXT_AUDITION_20261114.md (source-pair audition and candidate D).
5. docs/HOUSE_PRODUCTION_RESEARCH_AND_NEXT_GATES_20261114.md (previous FX failure and technical limitations).
6. docs/HOUSE_FULL_SONG_ARRANGER.md, docs/HOUSE_ONE_PROMPT_CONTEXT.md, docs/HOUSE_SOURCE_FIT_NATIVE.md (existing engine technical contracts).
7. AGENTS.md (historical operational ledger; preserve all content).

**One-line instruction for every future agent:** Improve the established modular Kuang engine toward reliable, *different*, high-quality one-prompt editable house productions through small validated extensions—**never start over, never tune only one song, and never confuse a successful render with an approved mix.**
