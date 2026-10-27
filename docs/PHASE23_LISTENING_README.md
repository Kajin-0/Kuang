# Phase23 — one groove, no lead melody

Play **Phase23-no-melody-native.wav**. This is the only new finished full mix:
16bars at126BPM, Cminor,30.476s plus5s natural tail,48k/24bit stereo.

The conventional lead, arp answers and ornamental air track are deleted.
There is no quieter lead or replacement single-note counterline. A restrained
three-note chord figure carries the hook. A sustained three-voice pad supplies
common Eb/G body and slow extended-chord colors over the unchanged bass.

All six drum tracks and bass/sub notes, timing, velocity, duration, IDs, samples,
patches, routing, processing and automation remain exact. Their isolated native
rhythm render must match the approved Phase21 main16 byte-for-byte.

Two original Vitalium source patches change:

- Chords: softer7ms attack, a longer body and170ms release; two single tuned
  soft/saw-morph oscillators at the same octave, without FM/phase-warp bite.
  A filter envelope, velocity response and subtle4-bar timbral motion.
- Pad:750ms attack, sustained body and1.8s release; two tuned single oscillators
  with modest pan separation. Actual8-bar synced wavetable/filter movement and
  native4/8/16-bar tone/dynamic expression. No pitch modulation or unison stack.

Existing upper chorus is reduced; no extra reverb, plugin, bus or master chain.
The existing shared returns are retained. New pad releases stop before the
chord handoffs; common inner voices connect them. This is harmonic backing,
not another melody hidden in the pad.

The WAV is the unprocessed native bounce, preserving the original common−6dB
capture trim. No limiter, loudness target or hidden master. The existing
reference path and the constant player-gain offset needed for a fair comparison
are in verification.json. No new reference song or alternative palette is
rendered for listening. Raw level differences do not establish better quality.

Open **project/native/session.scraft** with separately installed Linux
SoundCraft0.11.0 and GPL Vitalium1.0.6. Canonical0.1, MIDI, original prepared
patches, relative licensed CC0 drum assets, source manifests and complete note
provenance are included. No plugin binary, factory pack or reference recording.
The original SongSpec remains ancestor provenance, not the new score's prompt.

Replay the same raw PCM after extracting inside a workspace:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
  --workspace /absolute/path/to/workspace --out /absolute/path/to/workspace/replay \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

Frozen MIT code checks the exact score, patch recipe, media, receipts and raw
PCM hash. No downloads/accounts; bubblewrap is required by the existing optional
host path. Channel0 pitch bend stays neutral.5. Other plugin builds/channels,
official Vital and GUI/cross-platform behavior remain unverified.

Listening verdict is pending: **does this sound substantially richer without
a melody?** No professional-quality claim is inferred from technical checks.
