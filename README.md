# Kuang — local prompt to editable music

Kuang turns a musical description into a short editable instrumental sketch. Its source of truth is a DAW-agnostic structured project, with MIDI and optional native SoundCraft sessions and measured WAV previews. Everything runs locally. Python 3.11+, standard library only; no subscriptions, API keys, required proprietary components or bundled model/audio downloads.

**Working today:** one-command rules or optional local Ollama planning; distinct trap, house and ambient composition templates; key/tempo/seed controls; free built-in synths, EQ, reverb, mixer and gain automation; native SoundCraft 0.11.0 export/save/reopen and non-silent WAV checks. Phase 0/1 strict canonical JSON, MIDI, scoped atomic transactions, locks, exact undo/redo and the optional REAPER Lua adapter remain available.

**Limits:** template-based instrumental sketches, constant tempo, 4/4, major/natural minor, 8/16/32 bars. No vocals, acoustic instrument emulation, pitch-slide 808, external presets, sidechain compressor or automatic host reconciliation. No GUI/listening tests or professional composition/mastering claim. SoundCraft is the human editor; Kuang does not implement another DAW UI.

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

Optional experimental local LLM **plan** generation, using an already installed Apache-2.0 model and local `ollama serve`. Small 3–4B models are not assumed to provide Kuang's primary musical intelligence or better composition; this path is for experiments and eventual A/B benchmarks:

```bash
python3 -m kuang create "ambient cinematic, 72 bpm, D minor, spacious pads" \
  --model ollama --ollama-model qwen3.5:4b --seed 7 \
  --out-dir out/local-model \
  --soundcraft /absolute/path/to/soundcraft-cli --render
```

Only loopback Ollama is contacted; no model is downloaded. Invalid/unavailable model results fail with an actionable error, without silent rules fallback. The composer remains deterministic templates. `qwen2.5:3b-instruct` is rejected because its license is Qwen Research, not unrestricted Apache; FIRM/cloud models are also rejected. See [workflow and plan contract](docs/PHASE2.md), [recorded verification](docs/STATUS.md) and [license review](docs/LICENSING.md).

Future optional stronger planners (for example Codex CLI `codex exec` or another provider) must use the same strict SongSpec/typed-operation validation. They are not implemented in Phase 2. Provider accounts, inference costs and terms remain separate from the MIT core and are never required for local use. See the [proposed benchmark](docs/PHASE2.md#future-planner-benchmark-not-implemented).

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

See [architecture and edit semantics](docs/ARCHITECTURE.md), [current status](docs/STATUS.md), and [MIT license](LICENSE). No third-party plugins, presets, samples, models or credentials are bundled.
