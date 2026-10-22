# Phase 7 — pad balance first, then a house song

The user auditioned Phase 6 and found its pads strange, too loud and poorly integrated, with insufficient stereo depth and song structure. This release first compares a targeted pad correction on the **identical 16-bar groove**, then expands that corrected snapshot into a **64-bar, C-minor, 126 BPM house song**. The user has not auditioned this candidate here. Technical verification establishes editable state and measurable changes, not professional quality, preference or club readiness.

## Targeted pad comparison

`corrected_pads()` in `kuang/house_song.py` requires the exact released Phase 6 canonical hash, `6d5aba34cdc0dbf6401b3d1e4f6526e716dfcddaee192f7c12a7b0283e933e3b`. It preserves all **548 notes**, IDs, timings, durations, velocities, clip placement, sections and non-pad tracks/lanes. It updates both pad faders **and their existing read automation**; changing only the base fader would be overridden during playback.

The first -4.5 dB fader attempt failed the measured level gate and was not published. Gentler modulation restored dry-path energy, offsetting much of that nominal reduction. The final correction uses **-6 dB on both faders/gain lanes**, plus a **-3 dB native body-instrument trim** and softer sustain. These are explicit editable native controls, not audio postprocessing.

| Control | Body: Phase 6 → corrected | Air: Phase 6 → corrected |
| --- | --- | --- |
| Base gain dB | +4 → -2 | +2 → -4 |
| Beat gain lane range dB | +1…+4 → -5…-2 | -1…+2 → -7…-4 |
| Pan | -0.58 → -0.44 | +0.62 → +0.48 |
| Instrument level dB | -6 → -9 | -6 unchanged |
| Oscillator 2 / mix | Saw → Sine / 34→20% | Triangle unchanged / 24→18% |
| Synth cutoff Hz / resonance | 3400→2800 / 16→8% | 8500→5500 / 12→8% |
| Filter envelope amount | 24→10% | 16→8% |
| Amp attack / sustain / release | 650→850 ms / 70→55% / 1000→1250 ms | 260→500 ms / 38→32% / 650→1100 ms |
| Filter attack / decay / release | 1100→1400 / 1600→1900 / 1000→1250 ms | 450→900 / 1200→1400 / 650→1100 ms |
| Chorus rate / depth / wet | 0.32→0.17 Hz / 65→24% / 40→28% | 0.63→0.24 Hz / 58→26% / 44→30% |
| Phaser rate / depth / wet / feedback | 0.126→0.09 Hz / 72→22% / 38→10% / 28→12% | No phaser |
| Plate wet / decay | 28→38% / 1800→2800 ms | 24→34% / 1300→2400 ms |
| Plate width / predelay | 100→75% / 38→28 ms | 100→75% / 32→28 ms |
| Plate damping Hz / lowcut Hz | 6500→5500 / 500 unchanged | 9000→7000 / 650 unchanged |
| Moving insert LPF range Hz | 1200…6500 → 1600…4200 | 2400…14000 → 2500…9000 |

Amp decay and filter sustain remain unchanged. Chorus spread remains 100%, phaser center 950 Hz, and EQ highpasses 400/1000 Hz. The exact scalar changes and **every changed lane point** are recorded in `pad-fix/verification.json` and [PHASE7_VERIFICATION.json](PHASE7_VERIFICATION.json). Normalized Choice values still map to native integer selectors; reverb milliseconds map to seconds. No unsupported units or controls were added.

Both preview bounces are **35.4761875 s**, 48 kHz stereo 24-bit PCM: 16 bars plus five seconds of tail. The fresh A equals every historical Phase 6 PCM frame, with an additional silent allowance. All non-pad state is unchanged.

| Measurement on equal-duration native stems | Old pads | Corrected pads |
| --- | ---: | ---: |
| Combined-pad RMS dBFS | -31.3450 | -36.8937 |
| Combined-pad peak dBFS | -11.2545 | -15.5879 |

Pad RMS falls **5.5486 dB**. Corrected pad peak is **3.0457 dB below** the unchanged lead peak (-12.5422 dBFS); pad RMS is **8.8100 dB below** the other-drum/kick group. Full-file lead RMS is lower because the hook is sparse; it is not a useful direct balance target for a sustained layer. Over the exact union of lead MIDI spans plus its 75 ms release, pad/lead RMS is **-36.8557/-32.7900 dBFS**, pads **4.0657 dB lower**. These are signal relationships, not a prediction of perceived masking or preference. See `proof/lead-active-balance.json`.

Same-MIDI corrected wet-versus-dry reverb renders differ by **-40.2389 dBFS RMS**: **68.04%** of isolated pad RMS and **19.64%** of full-context RMS. Dry controls change only the pad plate mix to zero; notes, synths, envelopes, other effects and mixer remain identical. The 2.8/2.4 second decay, lowcut and width values persist in the native session. This demonstrates substantial active reverb, without claiming how pleasant or audible its balance will be to the user.

The full 16-bar pair under `pad-fix/listening/` measures **-26.102773 dBFS RMS** after attenuating A by **0.853449 dB**, leaving B unchanged. ZIP four-bar excerpts are independently attenuated to **-25.453746 dBFS RMS** (A receives another 0.023566 dB attenuation); the full-pair gains and excerpt gains are explicit in `levels.json`. C is never matched against that differently arranged A/B.

## Authored 64-bar form

`arrange_house()` accepts only that corrected snapshot. Track/instrument/FX IDs remain stable. **Bars 33–48 contain all 548 source notes, clip IDs, note IDs and velocities unchanged**, shifted by 32 bars. Other clips have deterministic new IDs and note-origin provenance. There are **1451 notes** total, 10 tracks, 17 canonical automation lanes and 4327 points. Source harmony remains the Cm/Cm/Cm/Fm cell, rootless sevenths/ninths and the existing G–Eb–F call/Bb–G answer.

| Bars | Native marker | Musical function | Start seconds | Section RMS dBFS |
| --- | --- | --- | ---: | ---: |
| 1–8 | DJ Intro | Grid kick; closed hats, clap and quiet ticks enter in stages; two final stab hints; no bass/lead/pads | 0.000 | -27.9329 |
| 9–16 | Groove | Bass pocket and answer enter; call appears in the second half; sparse pad support late | 15.238 | -25.9835 |
| 17–24 | Build | Brighter hats/stabs, full pad colour; last four bars halve kick density and thin bass; snare pickup, final bass dropout | 30.476 | -26.5464 |
| 25–32 | Breakdown | No kick or bass for all eight bars; first half pad-led breathing, late quiet hook/hat hints and a snare pickup | 45.714 | -34.9899 |
| 33–48 | Main Drop | Exact original 16-bar MIDI pocket returns on beat one; four phrase variants retained; filter/reverb settle then evolve | 60.952 | -25.4780 |
| 49–64 | DJ Outro | Call exits, answers/stabs/pads thin; last eight bars lose pads/harmony, final four lose bass and clap; predictable kick/closed hats remain | 91.429 | -26.7373 |

The build leads to a contrasting breakdown; the latter's late pickup prepares the main return. There are no fake risers, arbitrary note piles or new sample assets. Every section differs in actual notes, held-note activity, timbre/FX trajectories and measured energy. The breakdown is **9.5119 dB** below the main drop. Intro/outro retain a useful kick rather than being artificially normalized quieter. Build/outro levels are fairly close; their arrangement and frequency balance differ.

`activity.json` supplies per-bar track activity, sounding-note counts, every note onset/pitch/velocity/ID; `arrangement_origin_notes` maps reused motifs. Source SongSpec 1 remains **valid 16-bar provenance** and is saved as `source-song-spec.json`. The separate `arrangement.json` describes the authored 64-bar expansion. Canonical schema **0.1**, SongSpec enums, original composers and transaction/host semantics are unchanged.

Native automation opens/closes higher EQ LPFs by phrase, brightens/thins percussion, increases pad/lead space in the breakdown and settles wet mix at the drop. Stabs pan -0.40, answers +0.50; the lead moves by phrase between approximately ±0.26. Kick/bass instruments, FX, central pan and bass duck shape remain the source settings. Synth ADSRs are **static per instrument**. Effect modulation and EQ lanes are not oscillator LFOs or ADSR automation.

## Real audio and stereo limits

`song/C-phase7-house-64bars.wav` is a native **126.9047708-second**, 48 kHz stereo 24-bit PCM render: 121.904762 seconds of arrangement plus five seconds of release allowance. Peak **-6.795137 dBFS**, RMS **-27.012844 dBFS**, crest **20.217707 dB**, zero clipped samples. The final 250 ms is digitally silent. No normalization, limiting, waveform replacement, crossfade or mastering affects C.

Per-section spectra use up to 32 equally spaced 2048-frame Hann FFTs per section, summing stereo power and excluding <20 Hz. The DJ intro's estimated 20–120 Hz fraction is **95.67%**, build **70.61%**, breakdown **0.000599%**, main drop **64.70%**, outro **77.80%**. The sparse DJ sections are intentionally kick-led. These sampled fractions describe balance, not quality. Full/section RMS, peak, correlation and all five frequency bands are in machine reports. No LUFS or true-peak claim is made.

**Width remains limited.** On the same 16-bar A/B, >500 Hz side/mid power falls **0.10172 → 0.02860**, correlation rises **0.930405 → 0.982437**, and high-band mono retention improves **90.767% → 97.220%**. The louder, more phase-active pads supplied much of Phase 6's apparent width; lowering/calming them narrows the mix. The full song is also mostly correlated: **0.983805**, >500 Hz side/mid **0.025784**, high-band mono retention **97.4864%**, low-band **99.999963%**, mono-sum RMS loss **0.03577 dB**. Full-song and 16-bar ratios involve different material and sampling windows and are not a one-to-one width score.

The harmonic pan placement and native chorus spread are real and editable, but the existing adapter links both native stereo panners, limiting preservation of intrinsic effect width. No hidden stereo processor or unvalidated pan mode was introduced. Kick/bass stay centered, and measured low-band mono retention is effectively complete. This release prioritizes the requested pad integration and structure; it does **not** claim to solve thin stereo or enrich the underlying oscillator architecture.

## Files, reproduction and download

Release directory **`artifacts/phase7-house/`**:

- `pad-fix/`: unchanged 16-bar A, corrected B, full RMS-matched pair and excerpts, isolated pads/lead/music/drums, same-MIDI wet/dry native controls, editable corrected project and saved clone, exact control differences/source hashes.
- `song/`: full C WAV, editable canonical/MIDI/native project, saved clone, six markers, arrangement/activity maps and section/audio/spatial verification.
- **`phase7-house-listening.zip`**: named A old-pad/B corrected-pad equal-RMS excerpts, C complete song at native level, readme/levels/license and complete `editable-song/` plus `editable-pad-fix/` bundles. No lossy codecs or external assets.
- `proof/`: independent checks, active-lead balance, wheel/install evidence, release hash checks and CI evidence. Development logs/scratch remain under `.local/phase7/`.

ZIP: **33,700,762 bytes**, SHA-256 **`774941aae61c42c40daf1eb72abe931d68e69bb490c52a49af0dcc64be8f6cc5`**.

```bash
scp USER@HOST:/home/User/Kuang/artifacts/phase7-house/phase7-house-listening.zip .
```

Open `editable-song/native/session.scraft` or `editable-pad-fix/native/session.scraft` in the already installed SoundCraft **0.11.0**. Keep each companion manifest/canonical snapshot together. Notes, FX, mixer, static envelopes, automation and section markers are native objects. Automatic reconciliation of manual host edits remains unsupported.

Reproduce from the checkout, using **new** output paths:

```bash
export TMPDIR="$PWD/.local/phase7/tmp"
mkdir -p "$TMPDIR"
SC=/absolute/path/to/soundcraft-cli
python3 tools/phase7_house.py pads --source artifacts/phase6-house \
  --out-dir artifacts/my-phase7/pad-fix --soundcraft "$SC"
python3 tools/phase7_house.py song --source artifacts/my-phase7/pad-fix \
  --out-dir artifacts/my-phase7/song --soundcraft "$SC"
python3 tools/phase7_house.py package --out-dir artifacts/my-phase7
```

Use `--symbolic` instead of `--soundcraft` for offline canonical/MIDI only. Symbolic pads can reproduce Phase 6 internally without saved artifacts; symbolic song accepts the symbolic corrected directory or its deterministic default. Native song requires the verified corrected pad directory first. Packaging requires both real proofs and verifies every recorded file hash before publication. Existing/symlink/escaped/racing outputs and drift fail closed; failed staging is private and removed. No overwrite flag exists.

## Validation and remaining quality gate

See [STATUS.md](STATUS.md) and [machine-readable verification](PHASE7_VERIFICATION.json) for actual final test counts, timing, preservation and packaging checks. New focused coverage includes the exact 64-bar form, note boundaries/harmony, full original drop identity, entrances/exits/pickup, distinct section patterns/activity, pad scalar/lane changes, supported units/capabilities, locks/scopes/exact receipt replay, deterministic output, publication protection, known PCM section spectra and full independent real native notes/FX/lanes/markers/save/reopen/edit/audio/ZIP checks. All 194 prior test methods are retained. CI covers Python 3.11/3.13 and installed-wheel smoke; the local real-host suite uses the exact pinned executable without downloading it.

The first CI run passed tests/CLI checks on both versions but Python 3.13 lacked `setuptools.build_meta` for the no-download wheel step. CI now builds the universal wheel with the image's already cached Python 3.11 setuptools/wheel environment, with `--no-index --no-build-isolation`, then installs/runs it under the selected 3.11/3.13 matrix interpreter. No runtime dependency or package download was added.

No previous composers/schema/adapters/fixtures or Phase 2–6 artifacts are rewritten. Runtime remains stdlib-only and MIT core unchanged. No downloads, models, paid services, external plugins, samples or new GUI were used; the failed Phase 5 Surge gate was not retried. The basic subtractive/drum palette, static ADSRs, linked stereo panners, no audio-triggered sidechain/master bus, and missing professional reference remain limits. Only the user's listening can decide whether these quieter, softer pads, longer space and musical form are an improvement.
