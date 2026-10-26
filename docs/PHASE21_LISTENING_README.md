# Phase21 — melody, harmony and backing; the preferred pocket stays

Start with the same16-bar passage in `main16/`:

- A: Phase20 preferred sources and existing music.
- B: Phase21 connected melody, voice-led harmony, sustained backing and counterline.

Then play the TWO complete160-bar songs in `listening/`. A is the untouched
Phase20 B recording; B develops the new theme through the same five-minute
structure. Both are126BPM,Cminor,48k/24bit stereo, plus5s release.

The kick, clap, closed/open hats, shaker, ghost snare, bass and quiet sub-pulse
are preserved EXACTLY, including notes, velocities, timing and gates. Actual
isolated16-bar drum and bass PCM also match byte-for-byte. All instruments,
samples, synth states, faders, effects, sends, buses and automation stay exact.
This is intentionally **new upper MIDI**, not an unchanged-MIDI claim.

The familiar G–Eb–F seed now opens a longer question/answer theme: an upward
Bb–G–C answer, a higher melodic turn and a C cadence. Related C-pedal Cm9,
Cm11,Abmaj9/C and Fm9/C colors share voices; existing F-bass moments are
supported without changing the bass. Short/held stabs, common pad tones,
release-aware color voices and a quieter counterline fill the backing.
The first theme, contrasting bridge/break, rebuild and payoff use related
phrases. DJ bookends and the eight-bar kick-free break remain.

Playback level is matched by constant attenuation only. **No master chain,
new plugin, extra track or hidden audio processing.** Loudness/spectrum are
not quality scores. New preference is unreviewed; human listening decides.

`B/native/session.scraft` is live editable SoundCraft: MIDI, original Vitalium
states, relative live sampler WAVs, inserts, real auxes/sends and automation.
Canonical0.1, MIDI, original SongSpec provenance, a complete note-origin receipt
and independent active-interval harmonic audit are included. `source/` contains
editable original A. Original CC0 drum notices and MIT patch/source licenses
remain; no plugin binaries, factory presets or reference recordings are bundled.

The short native projects include a common transparent−6dB capture trim and
fresh DSP reset plus tails, without terminal effects. They are not exact slices
of the running full-song ambience. Note fields in the protected rhythm section
are identical on both sides; melodic/harmonic note fields intentionally differ.

To reproduce raw full B after extracting under a workspace:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
  --workspace /absolute/path/to/workspace --out /absolute/path/to/workspace/replay \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

The frozen MIT source checks the exact source, composition receipt, prepared
media and output PCM hash. Separately installed Linux SoundCraft0.11.0,
GPL Vitalium1.0.6 VST3 and bubblewrap are required. No accounts/downloads.
Channel0 synthetic pitch input1835232641 stays neutral.5; actual new notes and
chords are measured in SoundCraft and a separate VST3 host, with extra native
built-in tests. Official Vital/other builds/channels and GUI/cross-platform
behavior remain unverified. MIDI-active harmony does not transcribe reverb
tails or certify consonance. No professional/club-ready preference claim.
