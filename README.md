# Kuang — Phase 1

Kuang is the foundation of an AI-native, native/local-first, professionally editable DAW. The source of truth is a versioned structured music project. AI engines propose typed edits to it; humans retain editable notes, controls, automation, instruments and routing.

**Working today:** Python 3.11+ package/CLI, strict canonical JSON, seeded composition, MIDI, scoped atomic transactions, locks, exact undo/redo, and verified native SoundCraft 0.11.0 sessions with built-in synthesis, mixer/FX/automation edits and measured WAV export. SoundCraft is the primary optional executable backend; REAPER remains an optional legacy Lua adapter. Python runtime dependencies: standard library only.

**Not yet delivered:** Kuang's own desktop editor/audio engine, real model inference, professional music quality, automatic host reconciliation, or REAPER/Vital host validation. Real SoundCraft CLI integration and offline WAV measurements are verified; native GUI operation and listening quality are not claimed.

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

Run from the repository, or install locally with `python3 -m pip install --no-deps --no-build-isolation -e .` in your own virtual environment. The installed command is `kuang`. Outputs are protected from replacement unless `--force` is specified.

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

See [architecture and edit semantics](docs/ARCHITECTURE.md), [current status and next milestone](docs/STATUS.md), and [license decision](LICENSE). No third-party plugins, presets, samples or credentials are bundled.
