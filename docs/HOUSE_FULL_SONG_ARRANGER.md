# Full-Length House Template Arrangement — Reusable Engine (MVP)

**Scope:** generic, prompt-driven **96/112/128/160-bar** arrangements for Kuang's original groove-first house templates. This feature lives on the draft development PR. It does **not** require a user's per-song listening feedback; any human listening request will be an explicit product-evaluation exercise, not a dependency for routine testing. The reference Phase43/44 private song is left unchanged.

The goal is the user's **mostly-complete, producer-editable song template**, not a unique self-contained hit. A reliable, intentionally generic structure is preferred to risky novelty or 45 manually directed revisions.

## 1. Full song from one prompt

### Symbolic and native-ready producer session

```sh
python3 -m kuang create \
  "warm deep house in C minor, 128 bars, without pad, no lead" \
  --production groove-template --full-song-bars 128 --seed 17 \
  --out-dir .local/a-new-full-house-song
```

By default this creates **full editable canonical MIDI/session data** and machine-readable arrangement evidence without requiring proprietary sample packs. To use the existing reviewed SoundCraft host for an editable native session, add `--soundcraft /path/to/reviewed/soundcraft-cli`. Audio rendering additionally requires `--render`; files produced without it are **not** audio-verified.

### Combined licensed samples and privately auditioned Vital instruments

```sh
python3 -m kuang.autonomous_create \
  "warm deep house in C minor, 128 bars, without pad, no lead" \
  --catalog /path/to/private/preset-library/reports/catalog.json \
  --plugin /path/to/pinned/vitalium.vst3 \
  --soundcraft /path/to/reviewed/soundcraft-cli \
  --out-dir /path/to/new/private-output \
  --private-third-party-presets --groove-template \
  --sample-pack /path/to/audited/house-core \
  --full-song-bars 128 --groove-profile deep \
  --harmony-profile simple --seed 17 \
  --max-candidates 8 --per-role 1 --timeout 12
```

This second mode is an **integrated code path**, but a complete 128-bar **private Vital plugin render has not yet been verified in this milestone**. Prior 16-bar CC0+Vital integration did pass real native export/reopen and audio verification. Do not infer full-length third-party plugin reliability or subjective quality from the shorter experiment. All unknown-license third-party preset states remain private.

### One source-spec detail

The current `SongSpec` schema intentionally supports 8/16/32-bar *composition nuclei* only. The full-song arranger accepts a validated, original **32-bar groove-first source** (four eight-bar sections), preserves its valid source note identity and expands it to the requested full length in the **canonical Project**, which supports longer timelines. Thus `song-spec.json.bars == 32` means *source nucleus*, not final duration. Read `report.json.actual_project_bars` and `arrangement-evidence.json.output_bars` for the actual full song. **Do not accidentally treat the 32-bar source count as the exported song length.**

Prompts containing `96/112/128/160 bars` or `full-length` / `complete song` / `extended mix` activate full-form behavior **only** in the opt-in groove-template mode. A minute-based request is mapped to the nearest supported genre-phrase-aligned form using the stated BPM, with explicit unsupported/conflicting lengths rejected. The existing `sketch` and `refined` workflows are unchanged.

## 2. Repeatable arrangement grammar

Form blocks are quantized in units of eight bars (strong genre prior, not music theory law):

| Section | 96 bars | 112 bars | 128 bars | 160 bars | Reusable decision |
|---|---:|---:|---:|---:|---|
| Intro | 8 | 16 | 16 | 16 | Establish pad/chord/hat identity, then introduce DJ-friendly kick |
| Groove A | 16 | 16 | 24 | 32 | Establish reliable kick/clap/offbeat hat/bass/chord pocket |
| Groove B | 16 | 16 | 16 | 24 | Bring auxiliary percussion selectively; retain core pocket |
| Breakdown | 8 | 8 | 8 | 8 | Withhold kick and bass; maintain harmonic identity |
| Build | 8 | 8 | 8 | 8 | Restore hats/snare activity, automate filter rise, then kick |
| Main Drop | 16 | 16 | 24 | 32 | Bring back original groove, bass and selective extra percussion |
| Return | 16 | 16 | 16 | 24 | Reduce/recombine percussion while groove stays established |
| Outro | 8 | 16 | 16 | 16 | Subtract harmonic and bass parts while preserving useful beat structure |
| **Total** | **96** | **112** | **128** | **160** | Constant 4/4, original prompted BPM |

A generic full song may re-use eight-bar cells extensively. This is **intentional**: the user wants an editable starting point that has already done the repetitive work. Fresh creative melodic writing, vocals, sampled signature hooks and exotic production structures are deferred.

The arranger:
- **preserves** the original source project, source MIDI pitch content, plugins, drum sample identity, sound settings, native track controls, routing and instrument FX;
- creates new uniquely identified note/clip/section objects, with exact section bar boundaries and role/section activity matrix;
- varies controlled hat/percussion velocity by seed, while retaining exact kick/bass note timing/pitch and no independent lead;
- recomputes programmed gain ducking from **actual** new kick onsets, so a breakdown without kick cannot trigger rhythmic pump events;
- rebuilds filter automation by new section boundaries rather than accidentally looping 32-bar automation in the wrong song locations;
- removes optional **percussion or pad instruments only when entirely silent**, so the native host never receives invalid empty instrument tracks;
- validates original eight-bar groove identity, full-groove kick, bass return, breakdown silence, non-empty sections, main drop density relative to breakdown, no separate melody and source immutability.

These are **technical, repeatable structural acceptance gates**. A gate pass does **not** establish professional mix sound, reference-song equivalence, perceptual groove quality or full-master acceptance.

## 3. Evidence and automated generalization

The deterministic `tests/test_house_full_arranger.py` test suite evaluates a **32-combination matrix** (4 style families × 2 keys × 4 full-song lengths), plus explicit other-seed reproducibility/variation, no-pad/minimal handling, unsupported cases and prompt-resolution checks. Every matrix case must validate schema, section partitioning, MIDI export and gate evidence. `tests/test_house_full_create.py` tests end-to-end one-prompt canonical/MIDI publishing, source-spec versus final project length, conflicts and fail-closed private preset selection.

**Verified VPS tests, November 13, 2026:**
- Full arrangement matrix: 32 structural configurations passed with no technical gate failures; five test methods passed in ~23 seconds.
- A **96-bar minimal house** canonical project exported through real SoundCraft 0.11.0, saved/reopened and matched the original canonical project. Entirely silent optional percussion was removed automatically. This test did **not** render audio.
- A **128-bar deep-house** project with **five real, separately editable locally CC0-sourced drum roles** and built-in SoundCraft bass/chords successfully exported/reopened as a native session, with **2,997 MIDI events**. Full WAV rendered to **253.8095 seconds**, **48 kHz / 24-bit stereo**, **−8.2471 dBFS sample peak**, **zero clipped samples**, non-silent. It is a *technical reference render*, not a human-approved professional mix or master. This output is **not** the private Vital-preset route.
- The shorter 16-bar CC0+Vital combined source and native mix experiments remain separately documented in [HOUSE_REAL_SOURCES_MVP.md](HOUSE_REAL_SOURCES_MVP.md) and [HOUSE_SPECTRAL_AND_AB_REVIEW.md](HOUSE_SPECTRAL_AND_AB_REVIEW.md).

All output artifacts are kept in ignored `.local` workspace folders, not published in this repo. The user is **not** required to listen, approve, or operate their VPS to let the automated engineering checks continue. If a user-facing demonstration is ever required, deliver an authorized playable file through chat rather than asking them to listen on the VPS.

## 4. What still separates this engine from consistently excellent one-prompt templates

**(a) Source and mix intelligence.** Real drum/Vital integration exists, but preset scoring remains isolated and tag-based, not a joint producer-calibrated contextual comparison. Initial actual stem analysis found a very sub-heavy kick/bass combination and a midrange-dominant chord preset; future automatic selection should improve those *source choices* instead of treating full-band RMS or any single LUFS number as musical quality.

**(b) Reusable sound-quality guardrails.** Reject genuine technical faults (clipping, bad plugin pitch, missing assets, low-end mono cancellation, timing drift) automatically. Do not invent a pseudo-objective "sounds like hit song" 100-point score or blanket -7 dB chord requirement from a single experimental rendering. Use a small portfolio of approved/rejected comparisons if and when such references become available, but user review is not a prerequisite to running Kuang.

**(c) Native template polish and mastering.** The full song needs an editable premaster and separate mastered preview, mix-bus/preset-safe gain staging and return routing, and predictable packaging. A native 128-bar file merely proves full-length arrangement support.

**(d) Independent variability.** Profile/form/seed should yield coherent but distinct song templates, not randomly unbalanced source combinations. Continue testing a **matrix of prompts and seeds**, not polishing one fixed 128-bar example.

**(e) Reproducibility and runtime.** Keep expensive VST audition short, cache source and seed decisions, and run full-length native rendering **once** after the arrangement and source selection have passed. Bound CPU time, output size, candidate counts and local staging writes. Never mutate or publish another project's private assets.

**Production goal:** a user prompts for house music, Kuang makes a coherent 80%-complete house arrangement with a sensible mix/master starting point and editable native controls. The remaining musical personalization belongs to the producer, and ordinary successful generation should not depend on a human reviewing every iteration.
