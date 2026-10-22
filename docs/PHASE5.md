# Phase 5: one house groove experiment

The user listened to Phase 4 and found better production but insufficient club appeal. This delivery focuses on **one continuous 16-bar pocket**, rather than another full-song arrangement. It is an original authored experiment. No claim of club readiness, professional quality or successful listening evaluation follows from its tests or measurements.

`kuang/groove.py::house_loop()` constructs a new project through the existing SongSpec/composer/production objects. The result is fixed at **126 BPM, C minor, 16 bars**, with seed 29 used for the delivered candidate. The seed shades velocities; it does not generate another musical identity. Previous composers, default create behavior, schema 0.1, SongSpec 1, IDs, operations and revision semantics are unchanged. Runtime remains Python standard library only.

## Musical decisions

- Keep all **64 four-on-floor kicks**. Four four-bar phrases (`Pocket`, `Answer`, `Lift`, `Return`) change hats, ghost notes, pickups and hook responses while retaining the pulse. No long intro, pad wash or breakdown.
- Use one short, single-oscillator bass voice with monophonic MIDI. Its C/Bb/G/Eb syncopation includes quieter sixteenth pickups; notes plus the 28 ms release end before the next kick. Programmed ducking leaves the kick attack clear. This is not audio-triggered sidechain compression or calibrated oscillator phase alignment.
- Use a small **G–Eb–F** call with a **Bb–G** response, in a lower register than the Phase 4 lead. Rootless Cm9 stabs answer the rhythm; the final bar of each phrase uses an F-minor voicing. Leave rests rather than running arpeggios across every beat.
- Keep kick on grid; clap is 18 ticks late (8.93 ms). Hat ghosts are delayed 40 ticks (19.84 ms); quiet ticks use 46 ticks (22.82 ms). Backbeats, accents and ghosts have separate velocity levels, plus only ±2 seeded shading.
- Separate kick/bass low-end roles through timing, short bass envelopes, HPF/low-mid shaping and modest saturation. The native kick ends near 48 Hz at its default tuning; no unsupported pitch unit or phase-reset parameter was invented.
- Calibrate using independent stems. An initial mix buried the music under the low end. A later dynamics setting mostly added makeup level and was rejected. The delivered setting controls short melodic attacks with fast local compression, then restores some hook level. Kick has a controlled attack and longer body. These are track inserts, not hidden waveform processing or a new master engine.
- Keep chorus on stabs, restrained modulated delay on call/response, short filtered room space, pan placement and slow tone/throw lanes. No native synth LFO/wavetable claim. No extra downloaded preset/sample content.

The candidate has **8 tracks, 488 notes, 21 inserts and 7 canonical automation lanes**. Every note, instrument control, insert, gain/pan value and lane remains a native editable SoundCraft object with a companion canonical snapshot and identity manifest.

## Surge XT feasibility gate: failed tested workflow

Examined the official [Surge XT 1.3.4 release](https://github.com/surge-synthesizer/releases-xt/releases/tag/1.3.4), released 2024-08-11, and its [GPLv3 license](https://github.com/surge-synthesizer/surge/blob/release_xt_1.3.4/LICENSE). Only `surge-xt-linux-1.3.4-pluginsonly.tar.gz` was downloaded, **97,294,804 bytes**. No factory content package, system packages or global plugin installation were used.

The archive matched the release's **official MD5** `0180f06ec7a8445b1c749471e29c702b`. No official SHA-256 was supplied in that release's asset metadata. Computed local SHA-256: `dd431b75f5fa197c4bffa6ca27ca46970f0a94c834119bb1db7decdeec4c28db`. Release metadata, checksum file, archive, extracted files and inspected upstream source remain ignored under `.local/phase5/` (extracted archive about 225 MiB).

Executed the real installed SoundCraft CLI in **bubblewrap**: root filesystem read-only except `/home/User/Kuang`, network unshared, project-local XDG config/cache/data/documents and TMPDIR. `CLAP_PATH` / `VST3_PATH` were set only for these sandboxed subprocesses. No home-root prompt/plugin/config files or system installation were created.

| Gate | Actual result |
| --- | --- |
| Discovery | Both formats found Surge XT 1.3.4 and Surge XT Effects |
| CLAP instrument ID | `clap:org.surge-synth-team.surge-xt` |
| VST3 instrument ID | `vst3:ABCDEF019182FAEB566D624153675854` |
| Instantiation/save | CLI returned success; external device and opaque numeric parameter map persisted |
| MIDI render | **Both formats produced exactly silent PCM**, peak/RMS 0, 96,000 stereo frames |
| Built-in control | Same MIDI through the built-in synth: peak **-22.8675 dBFS**, RMS **-35.5682 dBFS**, non-silent |
| Named parameter edit | `mix.instrument_param` rejected each external ID as “not a built-in instrument” |
| Parameter at instantiation | `mix.instrument` with `params: {cutoff: 1000}` rejected “has no parameter `cutoff`” |
| Full native reopen | Equality passed for both saved external sessions; repeat renders remained silent |
| Meaningful preset/patch state | **Not verified**. No valid patch capture/restoration or usable named parameter mapping established |

The gate stopped at those failures. Empty/silent state persistence is not working synth support. These results establish failure of this tested CLI workflow, **not** a general claim that Surge cannot work through any SoundCraft UI or other host. No numeric parameter meanings, control units, patch bytes or rendering support were invented, and the Kuang adapter was not loosened to accept external instruments. The production candidate uses only the proven built-ins.

Exact argv/stdout/stderr, discovery, native probe sessions and both silent/control WAVs are preserved in `artifacts/phase5-house-proof/surge-probe/`, `surge-discovery.json` and `surge-gate.json`. The gate report is also included beside the delivered candidate. Surge remains a separate optional GPL component, absent from Git, the wheel and the listening ZIP; see [license review](LICENSING.md).

## Listening package and editable session

Everything below is under `/home/User/Kuang/artifacts/phase5-house/`:

| Path | Purpose |
| --- | --- |
| `phase5-house-listening.zip` | **Single download**, 18.1 MB approximately: three audition WAVs, levels/readme and complete editable candidate bundle/MIDI/license. No Surge binaries or reference recording |
| `listening/phase4-baseline-matched.wav` | Fresh Phase 4 refined baseline, unchanged level |
| `listening/candidate-matched.wav` | New full candidate attenuated **3.7442 dB** to equal full-file RMS |
| `listening/candidate-4bar-loop.wav` | Bars 9–12 of matched candidate, **7.61904 s**, exact PCM slice without crossfade |
| `phase4-baseline.wav`, `candidate.wav` | Fresh raw full bounces, 16 bars plus one-second tail |
| `native/session.scraft` | New editable candidate; keep `manifest.json` and `project.kuang.json` beside it |
| `saved-native/session.scraft` | Another verified full-state save/reopen |
| `project.kuang.json`, `song.mid`, `song-spec.json` | Structured source, symbolic export and intent/provenance |
| `stems/kick.wav`, `bass.wav`, `drums.wav`, `music.wav` | Independent native renders with corresponding editable group bundles |
| `verification.json` | Full timing, transient, band/stereo, stem, source inventory and artifact hash evidence |

The ZIP's `editable/native/` has the complete candidate bundle, not just a detached `.scraft`. SoundCraft's Open session action exposes the notes, devices and automation. Canonical import remains verified snapshot recovery; manual host edits are not automatically reconciled. Parameter/note revisions retain the existing scope/lock/hash rules. Preview tail is one second; the short excerpt is not a mathematically periodic effect-state render or crossfade claim. Its sample-boundary jump is measured in the report; listen across repeats.

## Measurements, without a professional score

Both full WAVs: **48 kHz / stereo / 24-bit integer PCM, 1,510,857 frames, 31.4761875 seconds**, non-silent, **zero clipped samples**.

| Measurement | Phase 4 refined baseline | Candidate |
| --- | ---: | ---: |
| Peak dBFS | -8.7024 | -6.6538 |
| RMS dBFS | -29.6160 | -25.8719 |
| Crest dB | 20.9136 | 19.2181 |
| Estimated 20–120 Hz power | 24.35% | 68.49% |
| Estimated 120–500 Hz power | 48.05% | 16.47% |
| Estimated 500–2000 Hz power | 22.98% | 9.02% |
| Estimated 2000–8000 Hz power | 3.89% | 2.40% |
| Estimated 8000 Hz–Nyquist power | 0.72% | 3.62% |
| Stereo correlation | 0.995235 | 0.994165 |

The candidate is deliberately much more low-end-led and remains strongly stereo-correlated. Neither fact establishes club suitability. Band fractions are the existing sampled 64-window / 2048-frame Hann FFT estimates, with coarse 23.4375 Hz bins. RMS matching is not LUFS/perceptual loudness matching. Baseline includes a song breakdown; the candidate keeps its groove continuously, so this is not an isolated DSP or identical-arrangement comparison.

Four independent native stem groups sum back to the full candidate within **2 integer LSB peak error**, delta RMS **-142.85 dBFS**. There are no bus/master interactions hidden in those stems. Kick grid-window median RMS is **-18.88 dBFS** in 0–20 ms, **-23.20** in 20–100 ms, **-32.07** in 100–200 ms. Bass median RMS is zero in the first two windows; maximum observed 0–20 ms residue is about **2.82e-6**. This supports the intended transient separation; it is not a listening result.

After a one-pole 20 Hz HP / 120 Hz LP on mono kick/bass stems, correlation is **-0.01597** and summed-versus-independent energy change **-0.0642 dB**. This describes small average destructive interference in this render. It does not establish phase calibration, worst-case alignment or subwoofer translation. The native synth exposes no phase-reset control in the mapped catalog.

Candidate four-bar phrase RMS values are approximately **-25.725, -25.725, -25.749, -25.727 dBFS**: energy contrast comes from articulation, rests and percussion/hook variation, while average groove energy stays steady. There is no claim of mastered loudness, true peak, streaming normalization or playback-system compatibility.

## Reproduction and user-reference interface

From this checkout, using the existing Phase 4 bundle and installed free host:

```bash
python3 tools/phase5_house.py --out-dir artifacts/another-house-pocket \
  --soundcraft /absolute/path/to/soundcraft-cli
```

`--baseline PATH` selects another verified 16-bar/126 BPM Phase 4 bundle. `--symbolic` instead of `--soundcraft` writes deterministic canonical/MIDI and explicitly reports no native/audio proof. Outputs require a new project-local path. Scratch/staging stays under `.local/phase5/`; failed work is cleaned before publication. All prior source files are hashed before/after. Rendered native JSON is never patched to synthesize support.

**No independently sourced professional reference was downloaded or used.** No exact external recording/license/attribution was available to establish a comparison standard. A private user-supplied reference can be added later:

```bash
python3 tools/phase5_house.py --out-dir artifacts/house-with-private-reference \
  --soundcraft /absolute/path/to/soundcraft-cli \
  --reference .local/phase5/user-reference.wav --reference-start 60 \
  --reference-credit "Artist, title, source URL" \
  --reference-license "Exact supplied terms or permission"
```

Reference input must be project-local stereo integer PCM WAV with enough audio after the selected start. The tool records its hash, attribution and declared terms, measures the excerpt and writes a private equal-RMS pair under `private-reference/`. It performs no resampling/time stretching and does not establish professional status or license permission from those declarations. Reference audio is **excluded from the download ZIP**. Only original Kuang audio is packaged.

## Verification and remaining limits

The final full real suite passed **180 tests, zero failures/errors/skips, 143.627 seconds**, Python 3.13.7. It retains all **167** earlier test methods and adds **13**: musical/timing/harmonic invariants, stable IDs/determinism, explicit built-in mappings, ordinary exact scope/history, publication protection, known PCM transient/interference/stem math, and a real editable-FX/full-state/stem/reference/ZIP integration. That integration independently checks note pitch/timing/duration/velocity/channel, FX order, enabled automation, mono-bass settings, full save/reopen equality, exact unrelated native state around a chorus-wet edit, exact undo/redo and a measurable chorus audio delta.

Final test transcripts and build/install/CI proof are under `artifacts/phase5-house-proof/` (`verified-tests.log`). Real integration artifacts are under `artifacts/phase5-house-verification*`. The wheel is built and installed without dependency/build-isolation downloads; CI exercises Python 3.11/3.13 and the symbolic loop CLI. Tests never download Surge or SoundCraft. Earlier Phase 2/3/4 evaluation data and examples (**78 inventoried files**) remain byte-identical; the fresh Phase 4 baseline WAV again hashes to `539f9b7794ad13fd9ef779434212ef875a2a93383a054a93461c2b1c4b95afe4`. The corrected SongSpec explicitly records the authored Cm/Cm/Cm/Fm roots; this provenance correction left rendered PCM byte-identical. Compact hashes and measurements are in [PHASE5_VERIFICATION.json](PHASE5_VERIFICATION.json).

Human listening to the new candidate is still the final test. Remaining limits: the built-in drum/synth character (including a fixed native clap envelope), no validated Surge patch/control workflow, no independent professional reference, modest stereo spread, no true-peak/LUFS measurement or master bus, and unverified repeat-boundary audibility/club playback. The experiment provides a more focused groove design and actual editable audio evidence; whether it is compelling or club-playable remains unknown.
