# Phase25 — source, space and transition refinement

Play the TWO complete files in **listening/**:

- **A-Phase24-reference-MATCHED.wav** — the unchanged incumbent recording.
- **B-Phase25-production-MATCHED.wav** — the single revised production.

Both are the same144-bar,126BPM,C-minor record:4:34.286 music plus5s release,
stereo48kHz/24bit PCM, matched integrated loudness by transparent constant
attenuation only. No new master, limiting, normalization dynamics or third
consumer version. New arrangement preference remains unreviewed.

The source notes, bass/kick pocket, sections and melody-free identity remain.
All501 anchor notes at0:30.476–1:00.952 are exact. The chord/pad SOUNDS in that
anchor change; its complete audio is not falsely claimed identical. The eight
rhythm roles alone remain PCM-exact under the same reset-anchor render.

Rhythm repairs are small and explicit:

- Remove ONLY four Phase24-added post-clap ghost snares at zero-based bars
  63,79,111,127. Keep the approved source ghost at3.777beats.
- Restore four late chord strikes (12 note voices) from2.625 to2.5beats, keeping
  the original4-tick voice strum. Related echo gates move with the attacks.
- Keep all original bass/sub events and intentional transition omissions.

There is no lead melody, arp answer, new instrument or new sample library.
Two original, live Vitalium patches change. Chords gain a more defined strike,
complementary bright/soft Fourier oscillator body, filter-envelope/velocity
response and stronger slow timbral motion. The pad has a clearer upper register,
shorter engagement and two actual counter-phase8-bar LFO shapes controlling
waveform/filter motion, with no pitch modulation or detuned stack.

Patch output is calibrated on identical MIDI before inserts. The pad uses the
reviewed synth's0dB output ceiling plus explicit2.284dB EQ input makeup to match
its OLD input level; this is not an overall audition gain boost. Role EQ makes
small low-mid cuts, the pad opens selectively at peaks, and the existing dark
plate gets42ms predelay and600Hz lowcut. Its recovered level is retained while
extra post-kick return ducking is reduced: the dry pad already ducks. Ducking
is scheduled native gain automation, not input-triggered sidechain compression.

Open **project/native/session.scraft** with separately installed Linux
SoundCraft0.11.0 and GPL Vitalium1.0.6. Editable canonical0.1, MIDI, all patch/
component states, six relative CC0 drum assets, licensing and explicit source/
edit provenance are included. No plugin binary, factory content or reference
recording. Official Vital, other builds/channels and GUI/cross-platform editing
remain unverified.

Reproduce the raw native B and its exact matched audition after extraction:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
  --workspace /absolute/path/to/workspace --out /absolute/path/to/workspace/replay \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

Frozen MIT code verifies score, receipts, media and both PCM hashes. The existing
optional host path requires bubblewrap. There are no downloads/accounts. Native
pitch-bend center stays.5. Private stems and probe WAVs are excluded; only the
complete A/B songs are listening material. Terminal-bus FX were physically
probed, then omitted from this production. Technical tests do not establish
professional quality or that the repaired rhythm is preferred.
