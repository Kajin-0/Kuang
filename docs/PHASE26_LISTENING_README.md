# Phase26 — home and return

Listen to the TWO complete recordings in `listening/`:
A is the unchanged Phase25 recording with transparent scalar attenuation.
B is the single Phase26 composition, matched to the same integrated loudness.
Both contain 144 bars at126BPM, plus5 seconds of release, 48kHz/24bit stereo.
No mastering or new instrument is included. Human preference is unreviewed.

The first12 bars now introduce rhythm and bass before the upper bed arrives.
The original501-note anchor at bars16–32 retains its exact score, source
patches, performance and reset-render audio. The whole recording is not
claimed identical there, because its preceding tails and plugin history differ.

After the anchor, each extended phrase spends8 bars on C minor,4 on F minor,
2 on suspended G and2 on G7. B natural supplies the leading tone, resolving to
C in the chord voice while G remains common. Bass and sub pitches support
the new roots; their onsets, lengths and accents remain exact. Sustained pads
are rearticulated with explicit release clearance; the dominant pad holds D/G
rather than a long B. The four Phase25 ghost removals and corrected chord
onsets remain intact. There is no conventional lead or arpeggio.

The live project is `project/native/session.scraft`; canonical score, MIDI,
original Vitalium states, six relative CC0 drum samples, licenses and a complete
composition receipt are included. SoundCraft0.11.0 and separately installed
GPL Vitalium1.0.6 are required for verified native replay. Plugin binaries and
factory presets are not included. Linux CLI replay is verified; other builds,
GUI behavior and official Vital are not established by these tests.

After extraction inside a Kuang workspace:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
 --workspace /absolute/path/to/Kuang --out /absolute/path/to/Kuang/.local/phase26/replay \
 --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

Replay verifies raw and scalar-matched PCM hashes. Musical audits establish
explicit functional note relationships and dry-release clearance; they do not
certify the artistic consonance of every reverberant tail or listener preference.

The intro kick fader rises smoothly from−5 to−3dB over16 bars. This corrects a measured early energy plateau while retaining its exact notes and patch; the approved anchor starts at the original−3dB.
