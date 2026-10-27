![Kuang — Prompt to Editable Music](docs/assets/kuang-banner.webp)

# Kuang — local prompt to editable music

Kuang turns a musical description into a short editable instrumental sketch. Its source of truth is a DAW-agnostic structured project, with MIDI and optional native SoundCraft sessions and measured WAV previews. Everything runs locally. Python 3.11+, standard library only; no subscriptions, API keys, required proprietary components or bundled model/audio downloads.

**Working today:** one-command creation and iterative revision/audition of existing songs; distinct trap, house and ambient composition templates; opt-in refined house production with oscillator/filter-envelope sound design, seventh voicings, call/response, swing, EQ/dynamics/modulation FX and evolving automation; native SoundCraft 0.11.0 export/save/reopen and measured A/B WAV checks. Phase 0/1 strict canonical JSON, MIDI, scoped atomic transactions, locks, exact undo/redo and the optional REAPER Lua adapter remain available. Rules need no model; local Ollama creation is an optional experiment.

**Limits:** template-based instrumental sketches, constant tempo, 4/4, major/natural minor. `create` supports 8/16/32 bars; the separate authored house expansion supports 64 bars. No vocals, acoustic instrument emulation, pitch-slide 808, arbitrary third-party preset import, true input-triggered sidechain compressor or automatic host reconciliation. No GUI verification or professional composition/mastering claim; new-candidate listening quality requires human audition. SoundCraft is the human editor; Kuang does not implement another DAW UI.

**Phase25 — source and depth refinement:** one full144-bar A/B preserves the melody-free record and anchor MIDI, removes four added transition ghosts, restores four delayed chord strikes and develops the two live synth voices with calibrated tone, role EQ and real counter-phase movement. Transparent matched auditions; no new master. Listening preference pending. [Decisions/proof](docs/PHASE25.md); `artifacts/phase25-house/phase25-house-listening.zip`.

**Phase24 — extended melody-free record:** the user-approved Phase23 foundation develops into ONE144-bar record with the exact original16-bar anchor, a single eight-bar breakdown, kick-led rebuild, chord/pad performance and DJ bookends. Source patches, drums, bass identity and real returns stay intact. New arrangement preference pending. [Decisions/proof](docs/PHASE24.md); download `artifacts/phase24-house/phase24-melody-free-house.zip`.

**Phase23 — no melody:** one16-bar groove removes lead, arp answers and ornamental air, preserves the exact approved drums/bass/sub and shared processing, and writes a restrained chord hook with a sustained evolving pad. Two original editable synth patches develop body/articulation; no new shortlist, full song or master. Listening verdict pending. [Decisions and proof](docs/PHASE23.md); download `artifacts/phase23-house/phase23-no-melody-groove.zip`.

**Phase22 musical shortlist:** the user preferred the groove but found the upper music weak. Three independently authored16-bar options—soulful, progressive and hypnotic—keep exact drums and the existing palette/mix. Only the first two move bass/sub pitches; the hypnotic low tracks remain exact. Four matched full-mix auditions and editable sources; no new160-bar song before human selection. [Decisions and proof](docs/PHASE22.md); download `artifacts/phase22-house/phase22-composer-shortlist.zip`.

**Phase21 melody and harmony:** the preferred Phase20 drum/bass pocket and complete source/mix state remain exact. A new connected theme develops G–Eb–F through question/answer phrases, C-pedal related chord colors, sustained pad support and a quieter counterline. The same16-bar A/B precedes two complete160-bar records; preference remains unreviewed. [Musical decisions and proof](docs/PHASE21.md); download `artifacts/phase21-house/phase21-house-listening.zip`.

**Phase20 source-first production:** the requested main16-bar A/B gate precedes a full160-bar candidate: shorter CC0 kick, original Vitalium chord/lead redesigns, retained approved bass/pad, deliberate spectral roles, articulation and shared depth. All4596 MIDI events remain exact. No master chain in the listening candidate; new preference remains unreviewed. The pack contains main-groove A/B, two complete matched songs and live editable sources. [Source decisions and proof](docs/PHASE20.md); download `artifacts/phase20-house/phase20-house-listening.zip`.

**Phase19 editorial continuity:** the user heard potential in Phase18 but found the dance-floor flow confusing. The independent editor retains the approved Phase17 sound/mix graph, brings the complete signature to bar16 and bass/drums to8, replaces the rotating bridge with one familiar C-pedal color, and limits the kick-free break to8bars. Actual four-floor rhythm continues through88–112. Two complete160-bar records are LUFS-matched; no new sound palette or master. Phase19 preference remains unreviewed. [Editorial decisions and actual note/PCM audit](docs/PHASE19.md); download `artifacts/phase19-house/phase19-house-listening.zip`.

**Phase18 extended record:** the user approved Phase17 B's sound/production and asked for a complete record. The new independent arranger develops that exact palette/mix into160bars (5:04.76 plus release), with a real harmonic bridge, authored responses, breakdown/rebuild, recognizable return and DJ bookends. It changes MIDI with complete note provenance; original608-note statements remain exact at two salient peaks. Two full different-length records are LUFS-matched for listening. Phase17 remains the incumbent until audition. [Musical decisions, pitch/harmony evidence and replay](docs/PHASE18.md); download `artifacts/phase18-house/phase18-house-listening.zip`.

**Phase17 mix experiment:** the user approved Phase16 B as a clear sound-quality step-change. It is the new musical incumbent. Phase17 retains its1536-note full song, all prepared patches and sampled drums, and tests coordinated native shared space, filtered phrase echoes and kick-derived wet-return ducking. The approved bass signal/dynamics remain exact; a practically inaudible extra bass-duck experiment was rejected. Two full-song equal-LUFS WAVs and editable A/B sources are in `artifacts/phase17-house/phase17-house-listening.zip`. New preference remains unknown until listening. [Controls, causal audio evidence and limitations](docs/PHASE17.md).

**Phase16 sound-design experiment:** the user-approved Phase15 full song now has an opt-in original, pitch-centered Vitalium palette. All1536 MIDI note records and the64-bar arrangement remain exact; four new synth roles are integrated one at a time, keeping the CC0 drums and two real shared returns. Actual cross-register/chord tuning, state/PCM reload and causal modulation tests precede the matched full-song A/B. Human listening still decides whether these sounds are preferable. [Controls, licensing, evidence and reproduction](docs/PHASE16.md); download `artifacts/phase16-house/phase16-house-listening.zip` and start with its **two complete WAVs** in `listening/`. B needs separately installed reviewed Vitalium1.0.6; current official Vital is untested. No factory preset, plugin binary or reference recording is bundled.

**Phase13 full-song listening:** the preferred Phase10 arrangement now has a complete, selected **CC0 sampled drum palette**: kick, clap, ghost snare, closed/open hats and shuffled shaker. Every original note field survives; mixed-pitch drums become explicit live sampler tracks. Bass, hook, pads and their production stay exact. The two complete records are matched in integrated LUFS, with editable A/B projects and a self-contained MIT reproduction script/source. Download `artifacts/phase13-house/phase13-house-listening.zip`; start with its two `listening/` WAVs. This is an unreviewed musical candidate, not an established listening win. [Source choices, licensing, controls and evidence](docs/PHASE13.md).

```bash
# Inspect deterministic full-song partitioning without samples or a host:
python3 tools/phase13_house.py --symbolic --out-dir .local/phase13/my-symbolic
# From the extracted listening ZIP, reproduce the actual native B:
python3 -I reproduce.py --source . --out reproduced-native \
  --workspace /absolute/path/to/your/project --soundcraft /path/to/soundcraft-cli
```

The earlier producer foundation provides a **generic licensed sample-asset importer, live native sampler backend and full-song audition/review loop**. It preserves MIDI, effects, mixer, automation and SongSpec while opening the palette to explicit user-selected WAVs. Original samples and native `Audio Files` travel in a hash-verified editable bundle; mono/stereo relocation, state and actual PCM are tested. This is infrastructure, not a claim of Suno-class production or a better song. See the [research-driven architecture](docs/PRODUCER_ARCHITECTURE.md) and [CLI workflow, licensing and actual evidence](docs/PRODUCER_USAGE.md). Normal creation and previous releases stay unchanged.

```bash
python3 -m kuang.sampled_instrument --help
python3 -m kuang.producer --help
```

**Phase 12 listening experiment:** eight bars from the user-preferred Phase 10 D drop, with **A=frozen source, B=groove only, C=sound only, D=combined**. The kick and hook notes stay exact; supporting rhythm gets authored accents, ghost-note timing and bass/stab articulation. Existing envelopes/processing are adjusted with measured native gain compensation. No new inserts or required plugins. All four have editable native/canonical/MIDI bundles and active-eight-bar LUFS-matched WAVs with natural release tails. A separate exact historical PCM cut documents the difference between a running song and a fresh DSP-reset excerpt. Human preference remains unknown. See [Phase 12 controls, evidence and reproduction](docs/PHASE12.md).

```bash
python3 tools/phase12_house.py --out-dir artifacts/phase12-house \
  --source artifacts/phase10-house --soundcraft /absolute/path/to/soundcraft-cli
# Or reproduce only the four canonical/MIDI variants, without any host:
python3 tools/phase12_house.py --symbolic --out-dir .local/phase12/my-symbolic
```

Use a fresh destination. The listening download is `artifacts/phase12-house/phase12-house-listening.zip`. At Phase12, routing was a bounded native prototype and is absent from those four comparisons. The later scoped production adapter verifies real one-level post-fader aux buses/sends; see the Phase15/16 evidence.

## Quick start

From this checkout, use an already installed free [SoundCraft 0.11.0](https://github.com/storytold/soundcraft/releases/tag/v0.11.0) CLI:

```bash
python3 -m kuang create \
  "dark atmospheric trap, 140 bpm, A minor, heavy 808, spacious pads, haunting lead" \
  --out-dir out/my-trap --seed 17 \
  --soundcraft /absolute/path/to/soundcraft-cli --render
```

This writes `project.kuang.json`, `song-spec.json`, `song.mid`, `native/session.scraft`, `preview.wav` and JSON verification/provenance reports. It renders all 16 bars plus one second of tail and refuses silence/clipping. Existing output directories are never replaced. Open `native/session.scraft` with SoundCraft's Open session action; notes are native MIDI clips, and instruments, FX inserts, mixer and automation are native editable objects. Save manual work to a new `.scraft`. Keep the companion canonical snapshot/manifest: automatic import of manual native changes is deliberately unsupported.

Omit `--soundcraft` and `--render` (and leave `KUANG_SOUNDCRAFT` unset) for fully offline canonical/MIDI generation without a host. Try `"uplifting house, 126 bpm, C major"` or `"ambient cinematic, 72 bpm, D minor"`. Rules mode is heuristic and reports `ai_plan: false`.

For the electronic house production profile:

```bash
python3 -m kuang create "uplifting house, 126 bpm, C major, 16 bars" \
  --production refined --seed 29 --out-dir artifacts/my-refined-house \
  --soundcraft /absolute/path/to/soundcraft-cli --render
```

This adds Intro/Groove/Breakdown/Drop sections, distinct bass/stab/pluck/pad voices, shaped envelopes, ghost fills, beat gain ducking, filter sweeps, delay throws and pan movement. It uses the installed free built-ins. The default `--production sketch` preserves the original composer. Refined currently supports house only; gain ducking is programmed rather than audio-triggered sidechaining. MIDI contains notes; sound design and automation live in canonical/native sessions. See [Phase 4 capabilities, listening files and reproducible A/B](docs/PHASE4.md). New output has measured balance changes; human preference is still unverified.

Phase 5 is a separate **16-bar house groove experiment**, with a continuous pocket, a small call/response hook and a downloadable equal-RMS listening ZIP. It is not certified as club-ready. Run from this checkout with the installed free host:

```bash
python3 tools/phase5_house.py --out-dir artifacts/my-house-pocket \
  --soundcraft /absolute/path/to/soundcraft-cli
```

This compares against the existing `artifacts/phase4-house-reference/B-refined` bundle; use `--baseline PATH` for another Phase 4 16-bar/126 BPM bundle. `--symbolic` instead of `--soundcraft` creates canonical/MIDI without a host. Surge XT was sandbox-tested but did not pass the render/control gate; it is optional and absent from the candidate. See [Phase 5 evidence and private user-reference comparison interface](docs/PHASE5.md).

Phase 6 is an opt-in **depth experiment over that exact Phase 5 groove**. It preserves every original note, the centred kick/bass and existing movement, and adds sustained rootless ninth pad/air layers, contrasting static ADSRs, chorus/phaser modulation, moving insert lowpass filters and more reverb on the unchanged stabs/call:

```bash
python3 tools/phase6_house.py --out-dir artifacts/my-house-depth \
  --source artifacts/phase5-house \
  --soundcraft /absolute/path/to/soundcraft-cli
```

The source must match the released Phase 5 fingerprint and contain its verified `native/` and `candidate.wav`. The new directory contains aligned 16-bar A/B WAVs with four seconds of tail, equal-RMS listening copies, isolated stems, same-MIDI reverb/modulation controls, complete editable native/canonical/MIDI bundles and **`phase6-house-listening.zip`**. Use a new destination each time. `--symbolic` without `--source` reproduces the exact notes/layers offline; it does not claim audio proof. No new plugin or model is needed. Movement comes from native effects and EQ automation, with distinct ADSRs on separate instruments; it is not oscillator LFO or ADSR automation. [Phase 6 measurements, reproduction and limitations](docs/PHASE6.md) document the verified release at `artifacts/phase6-house/`. Human listening remains the quality gate.

Phase 7 first corrects that pad mix, then expands the pocket into an editable **64-bar house song**: 8-bar DJ intro, 8-bar groove, 8-bar build, 8-bar breakdown, 16-bar main drop and 16-bar DJ outro. The drop preserves the original 16-bar MIDI motifs and IDs. Pads are quieter, softer and less heavily modulated, with longer reverb. Song structure lives in canonical sections and native markers; the original 16-bar SongSpec remains valid source provenance.

```bash
python3 tools/phase7_house.py pads --out-dir artifacts/my-phase7/pad-fix \
  --source artifacts/phase6-house --soundcraft /absolute/path/to/soundcraft-cli
python3 tools/phase7_house.py song --out-dir artifacts/my-phase7/song \
  --source artifacts/my-phase7/pad-fix --soundcraft /absolute/path/to/soundcraft-cli
python3 tools/phase7_house.py package --out-dir artifacts/my-phase7
```

`phase7-house-listening.zip` contains matched A/B pad excerpts, the full song at its native level and both editable bundles. The full 64-bar song is **not** RMS matched to the 16-bar comparison. Use new output paths; `--symbolic` instead of `--soundcraft` generates editable canonical/MIDI without audio claims (packaging requires real proof). No downloads or new plugin are required. See [Phase 7 controls, section measurements, limitations and reproduction](docs/PHASE7.md). Width is still modest; technical tests do not establish musical preference or club readiness.

Phase 8 keeps that **same 64-bar song** and adds deliberate native production gestures: steep HPF/LPF sweeps, note-aligned tempo delay throws, a spacious breakdown and an audible programmed pad pump. Every kick, bass and main-hook note is unchanged; five pre-drop percussion notes make a one-beat pause. This is an opt-in experiment, with same-input native effect controls and measured audio evidence.

```bash
python3 tools/phase8_house.py --out-dir artifacts/my-phase8 \
  --source artifacts/phase7-house/song --soundcraft /absolute/path/to/soundcraft-cli
python3 tools/phase8_house.py --package --out-dir artifacts/my-phase8
```

Download `artifacts/phase8-house/phase8-house-listening.zip` for the released full Phase 7/8 equal-RMS pair, short context excerpts, isolated effect controls and complete editable native/canonical/MIDI bundles. Both full songs have identical length: 64 bars plus five seconds of tail. The pump is **tempo-programmed gain ducking**, not an input-triggered sidechain. `--symbolic` generates the deterministic project without a host or audio claim. New paths only; no downloads, services or extra plugins. See [Phase 8 controls, measurements and limits](docs/PHASE8.md). Human listening decides whether it sounds better.

Phase 9 is one **sound-design/translation mix of the exact Phase 8 notes and automation**: shorter kick decay with a clearer attack, single-saw bass harmonics with calibrated output, small complementary EQ and upper-part pan changes. Pads and prior production gestures remain. It adds a validated mono/stereo LUFS/true-peak file meter and an optional, explicitly **off-host** gentle master; the native SoundCraft session is the editable pre-master.

```bash
python3 tools/phase9_house.py --source artifacts/phase8-house \
  --out-dir artifacts/my-phase9 --soundcraft /absolute/path/to/soundcraft-cli
python3 tools/phase9_house.py package --out-dir artifacts/my-phase9
```

The standalone meter needs only Python; the explicit optional `--meter-library .local/phase9/libebur128.so` uses the separately built MIT reference backend for faster analysis. Neither tests nor the tool download it. The released **`artifacts/phase9-house/phase9-house-listening.zip`** contains integrated-LUFS-matched A/B/C, matched drop excerpts, raw B/C, the complete editable B bundle and a frozen, reproducible master script. C is not claimed to be native editable. No fixed commercial loudness target or formal EBU certification is claimed. [Phase 9 source controls, licensing, measurement validation, limitations and reproduction](docs/PHASE9.md) include the private user-licensed reference interface.

Phase 10 develops the **same 64-bar Phase 9 song** with clearer pad envelopes, longer plate/tempo-delay tails, independent higher-part pans and a very quiet, late-offbeat mono sine pulse. All **1446 original notes** stay exact; the optional pulse adds 90 notes in the groove/drop. Pad faders and gain lanes remain unchanged, and measured average pad level is lower. Pulse trials with local cancellation were pruned before release.

```bash
mkdir -p .local/phase10/tmp
export TMPDIR="$PWD/.local/phase10/tmp"
python3 tools/phase10_house.py --source artifacts/phase9-house \
  --out-dir artifacts/my-phase10 --soundcraft /absolute/path/to/soundcraft-cli
python3 tools/phase10_house.py package --out-dir artifacts/my-phase10
```

Download **`artifacts/phase10-house/phase10-house-listening.zip`**: full integrated-LUFS-matched **A=unchanged Phase9 native**, **D=combined Phase10**, **E=optional off-host master**, matched drop A/D, causal pulse/pad-space controls, all four editable native/canonical/MIDI variants and the frozen E reproduction script. B=pulse only and C=space only are separate controls, unrelated to Phase 9's B/C labels. `--symbolic` instead of `--soundcraft` needs no host; `--reference-guide` accepts the optional strictly numeric local guide. No reference recording, external plugin, model or download is included. The new >500 Hz side fraction measures **2.65% → 5.25%**, with **94.75%** high-band mono energy retention; native loudness changes only **.008 LU**. These are DSP observations; human listening decides preference. See [Phase 10 exact controls, rejected trials, measurements and reproduction](docs/PHASE10.md).

Phase 11 proves a **live external wavetable instrument**: separately installed **DISTRHO Vitalium 1.0.6 VST3**, original Fourier-table pad/bass/pluck patches, internal oscillator/filter LFOs and envelopes, **771 explicitly normalized controls**, exact native save/reopen and repeated PCM. It preserves the complete Phase 10 MIDI. **Official Vital itself remains untested:** its free Basic download route requires an account; no login/credentials or unofficial binary mirror was used. Vitalium is an older GPL fork, not current official Vital. Legacy defaults/adapter remain unchanged.

```bash
mkdir -p .local/phase11/tmp
export TMPDIR="$PWD/.local/phase11/tmp"
python3 -m kuang.external_synth capabilities \
  --plugin .local/phase11/vitalium/usr/lib/vst3/vitalium.vst3 \
  --soundcraft /absolute/path/to/soundcraft-cli
python3 -m kuang.external_synth edit --source artifacts/phase11-vital/native \
  --track track-bass --parameter 'Filter 1 Cutoff' --normalized-value .8 \
  --out-dir artifacts/my-vitalium-edit \
  --plugin .local/phase11/vitalium/usr/lib/vst3/vitalium.vst3 \
  --soundcraft /absolute/path/to/soundcraft-cli
```

The adapter fails closed without the exact reviewed Linux plugin/host. Only optional patch preparation uses a separate user-installed Pedalboard/NumPy interpreter; normal Kuang and rendering prepared native bundles remain stdlib-only. `artifacts/phase11-vital/phase11-vitalium-listening.zip` contains full/drop LUFS-matched built-in/Vitalium comparisons, matched stems, internal-LFO controls and the complete live native/canonical/MIDI/original-patch bundle. No plugin/host binaries, factory content or reference recording is bundled. [Phase 11 availability, licensing, exact installation/preparation/reproduction and limitations](docs/PHASE11_VITAL.md) explain what was actually verified. GUI editor and official Vital/Windows patch compatibility remain unverified; human listening decides preference.

Optional experimental local LLM **plan** generation, using an already installed Apache-2.0 model and local `ollama serve`. Small 3–4B models are not assumed to provide Kuang's primary musical intelligence or better composition; this path is for experiments and eventual A/B benchmarks:

```bash
python3 -m kuang create "ambient cinematic, 72 bpm, D minor, spacious pads" \
  --model ollama --ollama-model qwen3.5:4b --seed 7 \
  --out-dir out/local-model \
  --soundcraft /absolute/path/to/soundcraft-cli --render
```

Only loopback Ollama is contacted; no model is downloaded. Invalid/unavailable model results fail with an actionable error, without silent rules fallback. The composer remains deterministic templates. `qwen2.5:3b-instruct` is rejected because its license is Qwen Research, not unrestricted Apache; FIRM/cloud models are also rejected. See [workflow and plan contract](docs/PHASE2.md), [recorded verification](docs/STATUS.md) and [license review](docs/LICENSING.md).

Future optional stronger planners (for example Codex CLI `codex exec` or another provider) must use the same strict SongSpec/typed-operation validation. They are not implemented in Phase 2. Provider accounts, inference costs and terms remain separate from the MIT core and are never required for local use. See the [proposed benchmark](docs/PHASE2.md#future-planner-benchmark-not-implemented).

## Revise and audition an existing song

```bash
python3 -m kuang revise out/my-trap \
  "make the bass more aggressive, simplify the drums in Main, keep everything else unchanged" \
  --out-dir out/my-trap-revised \
  --soundcraft /absolute/path/to/soundcraft-cli --render
```

The new directory contains `change-plan.json`, scoped receipts, the revised canonical/MIDI/native session, `original.wav`, `preview.wav` and an exact comparison/A/B report. Listen to both WAVs in any player or open `native/session.scraft` in SoundCraft. Every source file stays unchanged. Revise the resulting directory again to continue; no paid model, new DAW UI or model inference is required.

The rules grammar fully matches each clause: bass aggression, drum thinning in an existing section or inclusive bar range, existing-track reverb wetter/drier, and gain up/down by an explicit 0–6 dB delta (nonzero). Combine intents; `keep the lead unchanged` enforces preservation. Unsupported clauses, missing/ambiguous targets, locked edits, stale hashes and automated base-parameter edits fail the entire request. Phase 2 has `Main`; requesting `verse` on that song returns available section names. See [revision grammar, artifacts and limitations](docs/PHASE3.md).

Review a machine-readable plan before publishing, then apply that exact validated plan:

```bash
python3 -m kuang revise out/my-trap "make the bass more aggressive" \
  --plan-only > out/bass-plan.json
python3 -m kuang revise out/my-trap --plan out/bass-plan.json \
  --out-dir out/bass-revised --soundcraft /absolute/path/to/soundcraft-cli --render
python3 -m kuang undo out/bass-revised/project.kuang.json \
  out/bass-revised/revision-receipt.json out/bass-undone.kuang.json
python3 -m kuang redo out/bass-undone.kuang.json \
  out/bass-revised/revision-receipt.json out/bass-redone.kuang.json
```

Omit the backend/render flags (and unset `KUANG_SOUNDCRAFT`) for canonical/MIDI revisions. Existing SongSpec and canonical metadata remain original provenance; the revision plan/receipts describe current edits. Native manual changes still require explicit reconciliation and are rejected as drift. Audio metrics prove a measured signal difference, not human listening quality.

## Original demo and exact edits

```bash
git clone https://github.com/Kajin-0/Kuang.git
cd Kuang
python3 -m unittest discover -s tests -v
python3 -m kuang demo --seed 7 --out-dir out
python3 -m kuang validate out/demo.kuang.json
```

The demo contains 32 bars at 124 BPM in A minor: kick, snare/clap, hats, bass, chords, pad, arp and lead. It writes `demo.kuang.json`, `demo.mid`, `import_demo.lua` and an inspectable import plan. Committed session/MIDI examples live in [examples/](examples/).

Exercise the model boundary and exact saved undo/redo:

```bash
python3 -m kuang propose out/demo.kuang.json out/request.json \
  --track track-arp --clip clip-arp-hook-a --seed 17
python3 -m kuang apply out/demo.kuang.json out/request.json out/edited.kuang.json \
  --receipt out/receipt.json
python3 -m kuang undo out/edited.kuang.json out/receipt.json out/restored.kuang.json
cmp out/demo.kuang.json out/restored.kuang.json
python3 -m kuang redo out/restored.kuang.json out/receipt.json out/redone.kuang.json
cmp out/edited.kuang.json out/redone.kuang.json
```

Run from the repository, or install locally with `python3 -m pip install --no-deps --no-build-isolation -e .` in your own virtual environment. The installed command is `kuang`. Legacy canonical commands allow explicit `--force`; `create` and native SoundCraft outputs always require new paths.

Use your already installed SoundCraft 0.11.0 CLI; Kuang downloads nothing:

```bash
export KUANG_SOUNDCRAFT=/absolute/path/to/soundcraft-cli
python3 -m kuang soundcraft capabilities examples/soundcraft-demo.kuang.json
python3 -m kuang soundcraft export examples/soundcraft-demo.kuang.json out/sc-original
python3 -m kuang soundcraft apply out/sc-original examples/edit-soundcraft-mix.json out/sc-edited
python3 -m kuang soundcraft import out/sc-edited out/restored-from-soundcraft.kuang.json
python3 -m kuang soundcraft render out/sc-edited out/soundcraft-demo.wav
```

Each native bundle contains `session.scraft`, its canonical snapshot, identity manifest and verification reports. Original sources are retained; existing outputs are rejected. Import restores an unchanged verified snapshot and rejects external host drift. The original Phase 0 demo is preserved; the separate SoundCraft example explicitly selects free built-in synths, reverb and bass EQ. See [SoundCraft contracts and real validation](docs/SOUNDCRAFT.md) for supported mappings, losses and opt-in integration tests.

For optional REAPER import, run `out/import_demo.lua` in a **new empty project tab**, assign local instruments and save `.RPP`. See [REAPER and Vital validation](docs/REAPER.md); real REAPER execution remains unverified.

See [architecture and edit semantics](docs/ARCHITECTURE.md), [current status](docs/STATUS.md), and [MIT license](LICENSE). The wheel bundles no third-party plugins, presets, samples, models or credentials; optional listening releases carry explicitly licensed media with their own notices.

### Full-song ensemble production and shared native paths (Phase14)

[Phase14](docs/PHASE14.md) is an **unreviewed full-record production proposal**
against Phase13: four coordinated original Vitalium voices, preserved sampled
kick/groove/main call, documented chord/response performance and real shared
room/plate/echo plus summed drum compression. Canonical0.1, live samples,
original presets, all native lanes and six markers remain editable. The new
opt-in mixed-source adapter supports one-level post-fader aux paths and strict
scoped static edits; legacy creation/default adapters remain unchanged.

```bash
python3 -m kuang.production_host --help
python3 -m kuang.production_host inspect \
  --source artifacts/phase14-house/B/native --workspace "$PWD" \
  --plugin .local/phase11/vitalium/usr/lib/vst3/vitalium.vst3 \
  --soundcraft /absolute/path/to/soundcraft-cli
```

Listen to the two complete equal-LUFS files in
`artifacts/phase14-house/phase14-house-listening.zip`. The ZIP also carries
editable A/B, relative licensed media, original patch/control state and a tested
isolated replay recipe with frozen MIT source. Vitalium1.0.6 Linux VST3 remains
an optional **separate GPL component**, not official Vital or a bundled binary.
No factory presets/reference audio/services are included; no professional-quality
claim follows from render tests. [Listening/replay guide](docs/PHASE14_LISTENING_README.md).

### Phase15: musical repair and the Phase14 pitch postmortem

**The user rejected Phase14 B; Phase13 remains the musical incumbent.** Actual
controlled audio tests found the Phase14 VST voices200cents flat in SoundCraft
legacy mode, despite correct MIDI and state restoration. A synthetic MIDI
pitch-bend input was initialized to its negative extreme. The opt-in calibrated
backend centers that input, with unchanged notes/presets and actual cross-register
and chord tests. [Postmortem](docs/PHASE14_POSTMORTEM.md).

The [Phase15 listening repair](docs/PHASE15.md) is deliberately conservative:
all original Phase13 notes/sounds/inserts/mixer/automation, no lifted voicings or
pickups, and only restrained real shared processing. Its editable A/B ZIP needs
SoundCraft alone, **no Vitalium**. It is not a claimed quality upgrade.

```bash
python3 tools/phase15_house.py build --out-dir .local/phase15/new-repair \
  --soundcraft /absolute/path/to/soundcraft-cli
# Separate optional Vitalium musical-correctness gate, not a source substitution:
python3 tools/phase15_pitch.py --out-dir .local/phase15/new-pitch-gate \
  --plugin /absolute/project-local/path/to/vitalium.vst3 \
  --soundcraft /absolute/path/to/soundcraft-cli
```

`--center-pitch-bend` on `kuang.production_host` explicitly selects the reviewed
channel0 calibration. Legacy mode remains available for historical exact replay;
its earlier non-silence/state checks do not establish correct musical pitch.
[Listening/replay instructions](docs/PHASE15_LISTENING_README.md).
