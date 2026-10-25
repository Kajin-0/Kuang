# Phase16 — same music, original Vitalium palette

Start with the two complete WAVs in `listening/`: A is the user-approved Phase15
mix, B changes four synth voices and their stereo positions. Both have exactly
the same1536 MIDI notes,64bars,126BPM,Cminor and six sections. Integrated LUFS is
matched with constant attenuation only. There is no off-host master or hidden
audio correction. These are experimental sound choices; please judge the full
record. Full-mix >500Hz side fraction remains4.62% versus4.67% in A; a width
improvement over the approved baseline is not established. Technical gates do not establish better taste or professional quality.

The sampled drums, sub pulse, arp, air texture and both shared native returns
are retained. Existing automation keeps its IDs, timestamps and curve shapes;
calibrated gain offsets move each affected gain lane together. The stab HPF floor
changes280→150Hz with12dB/oct filtering, and its compressor changes to8ms attack,
−28dB threshold and0dB makeup. Other existing FX remain. Full before/after values
are recorded in `production.json`. Bass uses a controlled FM harmonic body;
stabs use an envelope-driven FM strike; the lead uses a focused phase-shaped
pluck; the pad uses slow wavetable/pulse movement and the existing native stereo
chorus/space. Notes, velocities, lengths, timing, phrasing and harmony are exact.

`A/` and `B/` contain canonical0.1, type-1 MIDI, source SongSpec and editable
SoundCraft sessions. B also contains original MIT `.vital`,`.vstpreset`, component
state and all771 normalized mapped parameters for each new voice. Waveforms are
original Fourier formulas; no factory or downloaded preset content is included.
The six inherited sample assets have relative paths and per-file legal provenance
in `licenses/`. No plugin binary or reference/Suno recording is included.

B needs separately installed **SoundCraft0.11.0, DISTRHO Vitalium1.0.6 Linux VST3
and bubblewrap**, with the reviewed binary fingerprints. A needs SoundCraft only.
Official Vital is not installed/tested: its Basic download requires an account;
no account was accessed. This is Vitalium, not a claim of current official Vital
compatibility. GUI/cross-platform and arbitrary plugin builds remain unverified.
Native synth edits stay live in SoundCraft; canonical snapshot recovery detects
host drift rather than silently reconciling arbitrary GUI edits.

For strict portable replay on the tested Linux stack, extract the ZIP inside a
workspace, then run:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
  --workspace /absolute/path/to/workspace --out /absolute/path/to/workspace/replay \
  --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/to/vitalium.vst3
```

Replay uses the included frozen MIT code and relative assets, with explicit
centered MIDI pitch bend. It verifies the full raw PCM hash. No Pedalboard,
downloads, credentials or original private source library is needed for replay.
The measurement reports describe tuning, timbre, mix and licensing checks;
they are not a perceptual quality score or certified metering claim.
