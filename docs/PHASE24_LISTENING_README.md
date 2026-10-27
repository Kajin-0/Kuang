# Stay in the pocket — extended house

Play **Phase24-melody-free-extended-native.wav**. ONE complete instrumental
record: 144 bars, 126 BPM, C minor, 4:34.286 music plus five seconds of natural
release. Stereo 48kHz/24-bit PCM. No lead, arp, solo answer or vocal.

Phase23 is the human-approved musical foundation. Its entire 16-bar score,
source patches, samples, mixer graph and automation are intact at **0:30.476–
1:00.952**, bars 17–32. The rest develops the same identity; no new instrument,
factory preset, sample library or mastering stage is introduced.

| Time | Zero-based bars | Musical function |
|---|---|---|
| 0:00 | 0–16 | DJ mix-in; bass at8, filtered chord hints, percussion handoffs |
| 0:30.476 | 16–48 | Exact approved anchor, then held chord replies/filter reveals |
| 1:31.429 | 48–64 | Rootless inversions, negative space, a prepared ghost-snare handoff |
| 2:01.905 | 64–72 | Only eight kick-free bars; hat clock and harmonic breathing |
| 2:17.143 | 72–80 | Kick/bass recover, short chord anticipation, tonal handoff |
| 2:32.381 | 80–112 | Familiar full return, longer pad sustain, developed guide voicings |
| 3:33.333 | 112–128 | Lower Bb/Eb pad support and familiar chord rhythm |
| 4:03.810 | 128–144 | Staged bass/chord withdrawal; last8 bars unpitched DJ mix-out |

The kick remains four-on-floor outside the single eight-bar breakdown. Every
retained bass/sub event keeps its source pitch, gate, velocity, channel and
position within the bar; documented omissions shape the form. The foreground
hook remains three-note chords, with shared C-pedal colors and release-aware
handoffs. Long pad voices and slow native filter/gain performance develop the
background without a hidden melody.

The approved original Vitalium patches remain exact, including 7ms chord and
750ms pad attacks. Actual synced wavetable/filter motion remains inside those
patches. New native performance uses supported EQ/gain/send lanes, filtered
plate tails and dotted-eighth phrase throws. Ducking is scheduled automation,
not an input-triggered sidechain. The raw native recording has no new master,
normalization or loudness target.

Open **project/native/session.scraft** with separately installed Linux
SoundCraft0.11.0 and GPL Vitalium1.0.6. Canonical0.1, MIDI, component/preset states,
relative CC0 drum assets, licenses and complete source/event provenance are
included. No plugin binary or reference recording. GUI/cross-platform editing,
official Vital and other plugin/host builds remain unverified.

Portable replay after extracting inside a workspace:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
  --workspace /absolute/path/to/workspace --out /absolute/path/to/workspace/replay \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

The existing optional host path requires bubblewrap. Frozen MIT code checks
score, event journal, media, native state and the reproduced PCM hash. No
downloads/accounts. The original SongSpec is ancestor provenance, not a claim
that the default sketch composer authored this record.

The 16-bar anchor is PCM-exact when rendered with the same fresh DSP reset as
Phase23. Incoming whole-song FX history is intentionally not claimed identical
to a reset preview. Full-song save/reopen/relocated replay is verified separately.
Audits and measurements establish integrity, not musical preference. This new
arrangement awaits human listening; no professional/club-ready claim is made.
