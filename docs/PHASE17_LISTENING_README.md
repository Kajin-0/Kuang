# Phase17 — full-song mix experiment on the approved Phase16 palette

Play the two complete WAVs in `listening/`: **A=approved Phase16 B**,
**B=Phase17 mix proposal**. Both are48k/24bit stereo,64bars at126BPM Cminor,
with exactly the same1536 MIDI notes, timing, velocities, durations and sections.
Integrated LUFS is matched by constant attenuation. No offline master or hidden
waveform correction is used. Human preference for B remains untested.

B retains every approved instrument/patch and all six CC0 drum sample assets.
It replaces overlapping individual long spaces with a genuine shared2.4s dark
plate and separate filtered dotted-eighth echo throws, while retaining a shorter
shared room. Wet returns breathe around actual kick MIDI onsets; the approved bass channel
and gain curve remain exact. An extra bass duck was rejected as effectively
inaudible. Return ducking is scheduled gain automation,
**not audio-triggered sidechain compression**. The existing actual drum-sum
compressor gets a restrained parallel-blend/attack adjustment. Higher harmonic
chorus/pan and filtered returns provide space; kick/bass/sub remain centered.

These are production choices, not an automatic quality score. Technical tests
establish actual signal processing, pitch, persistence, mono safety and unchanged
music. Please judge the complete record; isolated diagnostic stems are excluded
from this listening pack. Phase16 B remains the approved fallback.

`A/` and `B/` contain canonical0.1, MIDI, original SongSpec and complete native
SoundCraft bundles, relative sample media and original MIT `.vital`/VST3 patch
state. Required external stack: separately installed reviewed Linux SoundCraft
0.11.0, DISTRHO Vitalium1.0.6 VST3 and bubblewrap. Official Vital/current builds,
GUI and cross-platform editing remain unverified. No plugin binary, factory bank,
third-party tutorial preset or reference/Suno audio is included. Sample license
and per-file provenance are in `licenses/`.

Extract inside a workspace and reproduce the raw native B with:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
  --workspace /absolute/path/to/workspace --out /absolute/path/to/workspace/replayed \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

The included frozen MIT code verifies the exact source, patch manifests and full
raw PCM hash. Replay needs no original private library, account, network, model,
converter or independent plugin host. It initializes the proven native synthetic
channel0 MIDI pitch input to neutral.5. Native notes and synth/FX state are live,
editable objects; canonical recovery detects external drift rather than silently
reconciling arbitrary GUI edits. Metering is validated, not formally certified.
