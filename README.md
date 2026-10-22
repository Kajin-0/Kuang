# Kuang — Phase 0

Kuang is the foundation of an AI-native, native/local-first, professionally editable DAW. The source of truth is a versioned structured music project. AI engines propose typed edits to it; humans retain editable notes, controls, automation, instruments and routing.

**Working today:** Python 3.11+ package/CLI, strict canonical JSON, deterministic symbolic composition, type-1 MIDI, scoped atomic transactions, locks, exact undo/redo receipts, and a generated Lua importer for editable REAPER tracks. Runtime dependencies: Python standard library only.

**Not yet delivered:** a desktop DAW UI, real model inference, synthesis/rendering, professional music quality, bidirectional host synchronization, or validation inside real REAPER/Vital. The demo is symbolic orchestration, with no rendered master or audio analysis.

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

For REAPER, run `out/import_demo.lua` through Actions → ReaScript → Load in a **new empty project tab**. Assign local instruments to MIDI tracks and save as `.RPP`. The importer creates native items directly from the same canonical notes; separately importing the `.mid` would duplicate them. Read [REAPER and Vital validation](docs/REAPER.md) before evaluating host behavior.

See [architecture and edit semantics](docs/ARCHITECTURE.md), [current status and next milestone](docs/STATUS.md), and [license decision](LICENSE). No third-party plugins, presets, samples or credentials are bundled.
