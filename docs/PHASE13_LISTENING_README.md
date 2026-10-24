# Phase13 — full-song drum-palette listening experiment

Start with the two WAVs in `listening/`: A is the preferred Phase10 song;
B uses a complete, selected CC0 sample drum palette in that same song.
Both are stereo 48 kHz / 24-bit PCM, aligned, with matched integrated loudness
and natural release tails. The only audition processing is labelled constant
attenuation. There is no new master, limiter, or hidden waveform production.

This is an explicitly requested **unreviewed A/B experiment**, not a recorded
human preference or a professional/club-readiness claim. Phase10 stays incumbent
until listening decides. Compare the complete records; no stem homework is
included. `selection.json` explains the source shortlist and choice.

The tempo, C-minor key, six sections, 64 bars and all 1536 original note fields
remain. Only drums change. Clap/snare and closed/open hats are partitioned into
clearly labelled live sampler tracks; notes keep their original IDs, pitches,
timing, velocities, durations and channels. Non-drum instruments and their
effects, mixer and automation remain exact. Projected per-role inserts are
copies of the original chains, not a claimed drum bus.

Open `A/native/session.scraft` or `B/native/session.scraft` in the separately
installed SoundCraft 0.11.0. Keep the complete adjacent directories, including
`assets/` and `Audio Files/`. B is live editable MIDI + native sampler, not
frozen stems. Original canonical projects and MIDI are beside each bundle.
The native mix uses raw source levels; external listening attenuation is
reported in `verification.json`.

The selected one-shots come from octalmusic/octal-samples commit
22d222ce36e290ba3792c776811aa9c69dcc8776, dedicated CC0-1.0. They are the
publisher's synthesized drum samples, not recorded vintage machines or an
independently certified professional library. The original 44.1k WAVs,
per-file origins, publisher license and processing notes are in `licenses/`.
No ride/crash, factory material, plugin binary or Suno recording is included.

Imported sounds use explicitly documented libsamplerate 0.2.2 best-sinc
conversion to 48k/24bit, source headroom and a zero drain; all original and
converted hashes are pinned in the asset manifests. Native sampler trims and
gate envelopes are in `production.json`. Open hats release before the next
closed hit using their own MIDI duration and a native gate; there is no
cross-track choke, multi-zone SFZ, round robin or true triggered sidechain.

Reproduce the raw B from the extracted assets inside your explicit project
workspace. The ZIP carries Kuang's own MIT source in `reproduction/`, so this
requires Python 3.11+ and the separately installed host, without a pip install:

```
python -I reproduce.py --source . --out reproduced-native \
  --workspace /absolute/path/to/your/project --soundcraft /path/to/soundcraft-cli
```

The recipe checks canonical identity and requires byte-identical full PCM.
No converter or original library location is needed for this replay. Native
GUI behavior has not been exercised on the headless VPS. Human listening is
the final musical quality test.
