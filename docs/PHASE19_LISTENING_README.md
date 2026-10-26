# Phase19 — club continuity editorial A/B

Play the TWO complete WAVs in `listening/`:

- A = Phase18 reference, the version the user heard as promising but awkward.
- B = Phase19 editorial revision. Preference is UNREVIEWED.

Both are160bars,126BPM,Cminor,48k/24bit stereo,5:04.76 of music plus5s release.
Both complete songs are integrated-LUFS matched by constant attenuation only.
There is no mastering, limiter or hidden rendered-stem replacement.

B preserves the Phase17 sound/production palette inherited by Phase18: four
pitch-correct Vitalium voices, six licensed CC0 drum samples, all base mixer/
insert/send settings and the four actual native aux buses. No new instrument,
patch, sample, FX insert or countertheme. MIDI/automation intentionally changes.

The edit addresses continuity:

- Bass/drums establish at zero-based bar8; the complete G–Eb–F signature at16.
- The bridge stays on the C pedal: four bars of familiar Fm9/C color, then home.
- The main kick-free break is only80–87. Quiet offbeat hats keep time.
- Firm kick/clap/hats/bass return at88. Every kick beat remains through88–111.
- High points use the recognizable signature rather than independent melodies.
- The two608-note approved statements and the original DJ mix-out stay exact.

Display bar numbers are machine zero-bars plus1. The audit is explicit: Phase18
already contains a full MIDI hook teaser at26, while the full approved pocket
waits until32; MIDI presence is not a claim of perceived prominence.

`composition-receipt.json` records exact retained/removed/updated/added events,
source lineage, reasons and complete before/after automation. It is an editorial
composition receipt, not a revision-1 transaction. `flow-audit.json` contains the
per-bar kick grid, hook arrivals, bass/chord concurrency, transition note windows
and exact replay of the note journal. These are engineering evidence, not taste
scores or a claim that C-minor membership alone establishes consonance.

`B/` contains live editable canonical0.1, MIDI, original SongSpec provenance,
native SoundCraft session, relative licensed sample media and the unchanged
original MIT `.vital`/VST3 state. `source/` contains the Phase18 reference
canonical/MIDI. Licenses and per-file sample identities are in `licenses/`.
No plugin binary, factory bank, Suno recording or other reference audio is bundled.

Extract inside a workspace and reproduce B:

```bash
python3 -I reproduce.py --source /absolute/path/to/extracted \
  --workspace /absolute/path/to/workspace --out /absolute/path/to/workspace/replay \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

The frozen original MIT code reconstructs and verifies the exact editorial
receipt and full raw PCM hash. Required separate stack: reviewed Linux
SoundCraft0.11.0, DISTRHO Vitalium1.0.6 VST3 and bubblewrap. Neutral synthetic
channel0 MIDI pitch input1835232641=.5 is retained with the original bend range.
Native notes, instruments, FX, buses, sends, lanes and markers remain editable.
Official Vital/current banks, GUI/cross-platform editing and arbitrary native
reconciliation remain unverified. Gain ducking is scheduled MIDI automation,
not audio-triggered sidechain. Metering is validated, not formally certified.
Phase17 is approved for sound/production; neither Phase18 nor this Phase19
candidate is claimed club-ready. Human full-song listening decides preference.
