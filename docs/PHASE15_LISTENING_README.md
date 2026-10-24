# Phase15 — musical repair and conservative rollback

Phase14 B was **rejected by the user**. Controlled tests found its four
Vitalium voices playing two semitones flat in SoundCraft while remaining
built-in parts stayed at their intended pitches. The same presets are tuned
in the independent host. This is a real playback fault, not an incorrect
C-minor MIDI key-signature annotation or proof that every ninth is dissonant.

Start with the two complete files in `listening/`:

- **A-Phase13-incumbent-full-LUFS-matched.wav** — unchanged preferred incumbent.
- **B-Phase15-repaired-full-LUFS-matched.wav** — all original Phase13 notes,
  instruments, inserts, faders, pans and automation, plus an actual gentle
  summed drum compressor and quiet shared short room.

Both are the same64-bar126BPM C-minor composition,48k/24bit stereo PCM,
126.9047708seconds including settled release. Matching uses constant attenuation
only; there is no off-host master, limiter, note correction or hidden processing.
All1536 original note IDs/fields survive. No Phase14 octave lifts, velocity
changes, pickups, new pad or Vitalium source replacements are retained.

This is deliberately a **safe rollback candidate**, not a claimed quality
upgrade. Phase13 remains incumbent until a new human preference is recorded.
The additional processing is restrained; this is not another source makeover.
`production.json` states every allowed change. `pitch-verification.json` records
the actual multiple-note/window/native/off-host tests and exact root-cause probe.
Internal stems and diagnostic tones are excluded from this listening download.

## Edit and replay

`A/native/session.scraft` and `B/native/session.scraft` are live editable
SoundCraft projects, with adjacent canonical0.1, type-1 MIDI, original SongSpec,
identity/asset manifests and complete relative sample media. B needs only the
separately installed **SoundCraft0.11.0**. It has **no Vitalium dependency**.
The source samples remain the same six declared-CC0 original octal one-shots,
with their original provenance/licenses and hashes. No factory content, plugin
binary, Suno recording or reference audio is included.

Extract inside a project workspace and use Python3.11+:

```bash
python3 -I reproduce.py --source . --out ./replayed \
  --workspace /absolute/path/to/your/project \
  --soundcraft /absolute/path/to/soundcraft-cli
```

The explicit workspace must contain the extracted files/output. The new target
must not exist. Frozen MIT source in `reproduction/` rebuilds B from A, exports
through real host commands, reopens/renders and requires the exact raw PCM hash
in `recipe.json`. It needs no plugin, source sample library, converter, account
or download. Manual DAW changes are detected as drift, not auto-reconciled.
GUI/cross-platform operation itself remains untested on the headless VPS.

## Separate experimental Vitalium fix

The optional tuned backend initializes SoundCraft's reviewed synthetic channel-1
MIDI pitch-bend slot1835232641 to normalized.5. It changes no MIDI pitches,
oscillator transpose, preset/component payload or ordinary771 synth controls,
and preserves the2-semitone bend range. This is a pinned Vitalium1.0.6/
SoundCraft0.11.0, MIDI-channel0 calibration, not generic VST compatibility.
Legacy exact-replay mode remains unchanged so historical files reproduce;
it is not suitable for new musical decisions without tuning calibration.
A separately tested alternative disables bend range entirely, losing bend
expression. Neither corrected experiment is substituted into this safe B.

Your listening decides whether B's small shared-processing changes are useful.
State equality, key membership, LUFS matching and pitch accuracy are necessary
checks and do not establish professional quality or musical preference.
