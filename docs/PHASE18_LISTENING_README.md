# Phase18 — Return to the room, extended house arrangement

Play the two COMPLETE WAVs in `listening/`:

- A = human-approved Phase17 B, 64 bars / 2:06.90 including release.
- B = new Phase18 extended record, 160 bars / 5:09.76 including release.

Both are 126 BPM, C minor, 48 kHz/24-bit stereo and matched to the same integrated
LUFS by constant attenuation. These are different-length records, not an aligned
mix/null comparison. No limiter, offline mastering or hidden waveform correction.
Phase17 B remains the approved incumbent until you judge the complete new record.

B keeps the four original tuned Vitalium patches, six licensed CC0 drum samples,
all original mixer/insert/send settings and four real native aux buses. It changes
MIDI and automation to create a complete arrangement. MIDI bytes are NOT identical.
The original 608-note statement at bars33–48 is exact; its 608-note translated
return at113–128 retains all note performance fields. The other phrases develop
the pocket, hook, chord articulation and responses. No vocals or reference audio.

| Display bars | Function |
|---|---|
| 1–16 | DJ intro, filtered harmony/bass teases, foreground lead absent |
| 17–32 | Pocket establishes, two-note question then full hook teaser |
| 33–64 | Approved statement, G–F–Eb/F–Eb–G answers and first peak |
| 65–80 | Abmaj9/Ebmaj9/Fm9/Bbadd9 with matching bass roots and two responses |
| 81–96 | Kick/bass-free harmonic breakdown, augmented hook, breathing/rest |
| 97–112 | Rhythm rebuild, actual filter performance, D–Eb–F pickup and gap |
| 113–144 | Approved return, F–G–Eb payoff and displaced final hook |
| 145–160 | Withdrawal/resolution, eight clean percussion-only mix-out bars |

`composition-receipt.json` documents every note's destination, reason and original
source event where copied; new authored notes are explicit. It is an arrangement
receipt, not a revision-1 transaction. `harmonic-audit.json` covers every symbolic
active-note interval; it does not transcribe synth-release or effect tails or
pretend that key membership alone establishes musical quality.

`B/` contains canonical0.1, MIDI, original SongSpec provenance and complete live
native SoundCraft state, relative sample media and unchanged original MIT
`.vital`/VST3 prepared state. `source/` contains the approved source canonical/MIDI.
No plugin binary, factory bank, third-party tutorial preset or Suno recording is
included. Licenses and per-file sample identities are in `licenses/`.

Reproduce the complete raw B after extracting inside a workspace:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
  --workspace /absolute/path/to/workspace --out /absolute/path/to/workspace/replay \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

Required external stack: separately installed reviewed Linux SoundCraft0.11.0,
DISTRHO Vitalium1.0.6 VST3 and bubblewrap. Frozen original MIT code reconstructs
and verifies the exact composition receipt, relative assets, patch identity and
full raw PCM. It initializes the proven synthetic channel0 MIDI pitch input to
neutral .5. Native notes, samples, synths, FX, sends, lanes and markers remain
live/editable. Official Vital/current banks, GUI/cross-platform editing and
arbitrary native reconciliation remain unverified. Return/pad attenuation is
scheduled from MIDI, not an audio-triggered sidechain; no native master claim.
Human listening is the final musical gate. Metering is validated, not certified.
