# Phase20 — source-first groove and full song, preference unreviewed

First hear `groove-preview/A-MAIN16-MATCHED.wav` and `B-MAIN16-MATCHED.wav`.
These compare the same608-event main16-bar groove. B has a shorter kick,
warmer original Vitalium chord strikes and a richer articulated lead, keeping
the approved FM bass and pad. No new melody, rhythm or master chain.

Then play the TWO complete songs in `listening/`:

- A: untouched Phase19 full160-bar reference.
- B: Phase20 source/role production candidate, **not yet preferred by the user**.

Both are126BPM,Cminor,48k/24bit stereo,5:04.76 of music plus5s release.
Constant attenuation matches overall integrated loudness; every section and
transient need not have identical perceived loudness. Raise playback volume
for BOTH equally if needed. No louder consumer master is presented as a win.

All4596 original note fields, IDs, timing, durations, velocities, channels,
clips and sections stay exact. Only kick/stab/lead source identities change.
The approved bass/pad patches and five other CC0 drum assets stay exact.
The bass-source alternatives were rejected; no extra sub track is added.
Native tonal carving, foreground articulation, summed parallel drum dynamics
and filtered shared room/plate/echo shape the production before any mastering.
**Full B has no master processor or hidden offline processing.**

`B/native/session.scraft` is a real live editable native project: MIDI,
Vitalium patch state, relative live sampler WAVs, inserts, actual aux buses,
sends and automation. `B/project.kuang.json`, `song.mid`, original SongSpec and
`production.json` retain strict canonical/provenance data. `source/` contains
the original editable A as well. `licenses/` and per-asset manifests record
CC0 source identity and original MIT patch content. No plugin binary, factory
bank or commercial DJ recording is bundled.

The16-bar native preview has the same transparent−6dB capture trim on both
sides, with no terminal effects. Its DSP starts afresh and includes5s tail;
it is not an exact slice of the running full-song ambience. Preview native
projects are included. Source/control and pitch reports are engineering
proofs, not a listening vote. Darker stabs and shorter kick may be taste
tradeoffs; do not assume a higher spectral number means a better sound.

Extract under a workspace and reproduce the full raw native B:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
  --workspace /absolute/path/to/workspace --out /absolute/path/to/workspace/replay \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

The frozen MIT source verifies the exact production receipt, patch/sample
manifests and full raw PCM hash. Separately installed Linux SoundCraft0.11.0,
GPL Vitalium1.0.6 VST3 and bubblewrap are required. No download or account.
Channel0 synthetic MIDI pitch control1835232641 remains neutral.5; actual
nine-note/Cm9 tuning tests pass in two hosts. Official Vital/current builds,
other channels and GUI/cross-platform editing remain unverified. No real
input-triggered sidechain claim; existing ducking is scheduled from MIDI.

Human listening decides whether B is better. No club-ready/professional claim.
