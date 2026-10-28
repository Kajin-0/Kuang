# Phase26 — harmonic direction and a staged introduction

Phase25 is the source sound and groove incumbent. The user found its sound
credible but its harmonic movement ambient and meandering, and its opening
abrupt. This separate opt-in composer preserves144 bars,126BPM, the8 sections,
all instruments and native processing, and the melody-free identity.

## Musical decisions

The exact501-note anchor occupies zero-based bars16–32. After it, six extended
phrases use eight tonic bars, four subdominant bars, two suspended-dominant bars
and two dominant bars. The existing section activity, short break and performance
arcs give these cadences different contexts: first development, harmonic break,
full return, later peak and withdrawal. Bars48 and80 land on C minor. The outro
returns to tonic and retains the original withdrawal of the rhythm section.

| Function | Stab voices | Bass root | Sustained pad |
|---|---|---|---|
| C minor | G3,C4,Eb4 | C2 | Bb3,D4,G4 |
| F minor | Ab3,C4,F4 | F2 | C4,Eb4,Ab4 |
| G7sus4 | G3,C4,F4 | G2 | D4,G4 |
| G7 | G3,B3,F4 | G2 | D4,G4 |

The leading tone B resolves upward to C, F resolves to Eb, and G stays common.
Each stab voice moves at most two semitones at successive functional changes;
the musical direction comes from the root and guide tones, not large chord jumps.
Bass/sub root and pickup pitches support each function; every original onset,
velocity, duration, channel and ID is retained. This intentionally introduces B
natural in the dominant. A natural-minor pitch-class whitelist would wrongly
reject that function, so the audit uses the actual chord at each moment.

Pads are rearticulated at functional boundaries with two seconds of dry-release
clearance. The dominant pad holds only shared D/G, avoiding a long B through the
tonic arrival. The dry-release sweep is not a transcription or certification of
the complete reverberant tail. The existing musical echo/plate graph remains.

The intro keeps the kick and offbeat timekeeping, adds backbeat/percussion,
reveals bass at8, then introduces the upper bed at12. Open hats wait until12.
Chord/pad gain and existing filters gradually open before the untouched anchor.
All later automation points remain exact. There is no added melody, arpeggio,
instrument, sample, master chain or new effect. The Phase25 ghost removals and
corrected chord timing remain.

## Implementation and verification

`kuang/groove_direction.py` requires the exact unlocked Phase25 source and
produces a new project plus explicit event lineage. The strict0.1 schema,
SongSpec/default composers and earlier runtime/tests are unchanged. Native
construction uses real host commands; no SoundCraft JSON is synthesized.

Mandatory offline discovery: **580 tests, 485 executed successfully and 95 optional-host skips**. **Four new real-host tests and four existing primary-adapter tests pass**, with zero skips. Installed-wheel smoke passes; **75 runtime files** match current, installed and frozen code. All **568 earlier test methods/files** and **12,668 historical files** remain exact. Older optional native experiments were not regenerated.

The new score contains **3,788 notes**. The complete 501-note anchor reset render, native save/reopen, and extracted relocated raw/matched replay are PCM-exact. Source patches, sample assets and signal graph remain exact. Every later bass/sub onset, gate and accent is retained; only the documented functional pitches change.

The four intro blocks measure **-41.07, -40.68, -37.50, -35.76 dBFS RMS**. Both complete 48kHz/24-bit stereo recordings have zero clipped samples. The scalar-matched copies measure **-33.295045/-33.295045 LUFS**. These measurements establish the staged energy change and level parity, not listener preference.

[Machine verification](PHASE26_VERIFICATION.json). Exact commit and post-push Python 3.11/3.13 CI evidence are stored in artifact `proof/release-summary.json`. Musical preference remains unreviewed.

The listening ZIP contains exactly two full scalar-matched recordings: Phase25
A and Phase26 B. Native B, canonical/MIDI, original prepared synth states,
relative licensed drum assets, source score, receipt and frozen MIT replay are
included. No plugin binaries, third-party factory presets or outside music.
Pinned Linux SoundCraft0.11.0 and separate GPL Vitalium1.0.6 are the verified
host/plugin pair. Human preference remains unreviewed.

Reproduction and listening instructions: [README](PHASE26_LISTENING_README.md).

```bash
python3 tools/phase26_house.py build --out-dir .local/phase26/my-record \
 --soundcraft /absolute/path/to/soundcraft-cli \
 --plugin /absolute/path/to/vitalium.vst3 \
 --host-python /absolute/path/to/independent/plugin-host/python \
 --meter /absolute/path/to/libebur128.so
```

The intro kick fader rises smoothly from−5 to−3dB over16 bars. This corrects a measured early energy plateau while retaining its exact notes and patch; the approved anchor starts at the original−3dB.
