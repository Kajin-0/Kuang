# Refined electronic house production

`create --production refined` is an opt-in production profile on the existing SongSpec → composer path. It creates editable symbolic/native music with a more developed arrangement, sound design and mix. The default sketch composer and Phase 0 fixtures remain unchanged. Canonical schema **0.1**, SongSpec **1**, transaction operations and provider boundary are unchanged. No runtime dependencies, external plugins, samples, model calls, paid services or DAW UI were added.

```bash
python3 -m kuang create "uplifting house, 126 bpm, C major, 16 bars" \
  --production refined --seed 29 --out-dir artifacts/my-refined-house \
  --soundcraft /absolute/path/to/soundcraft-cli --render
```

Omit the host/render flags and unset `KUANG_SOUNDCRAFT` for canonical/MIDI only. Refined supports house with song arrangement, 8/16/32 bars, major/natural minor and requested tempo/key/seed. Other genres fail explicitly. The original SongSpec stays in provenance; the expanded seventh voicings, additional pad derived from the harmony role and production controls are canonical project objects. Requested drum/lead omissions and dry space are honored. Same inputs/code produce the same canonical/MIDI bytes; cross-build audio determinism is not promised.

## Arrangement and mix decisions

The 16-bar reference has four four-bar sections:

| Section | Musical purpose |
| --- | --- |
| Intro | Filtered seventh stabs and breathing pad; hats establish pulse; kick enters halfway through |
| Groove | Bass on complementary offbeats, clap/ghost notes, lead calls leaving space for answering plucks |
| Breakdown | Kick/bass leave; pad and sustained stabs retain harmony; plucks and rising snare density build into an automated filter opening |
| Drop | Full rhythm, varied answering pluck order, added pad in the second half, resolving lead variation and final beat space |

Harmony moves every two bars through the supplied progression. Four diatonic voices use deterministic nearest voicings; small strums separate chord attacks. Bass adds fifth/octave pickups. Kick stays on grid; sixteenth percussion/plucks use a 30-tick delay (53.1% swing) and controlled velocity accents. This is intentional template writing, not a learned composition model or artist imitation.

Separate bass, stab, pluck, lead and pad voices have explicit oscillator blends, velocity sensitivity and distinct amp/filter envelopes. The bass combines sine and saw; pads use triangle/saw. EQ removes unneeded lows and reduces low-mid overlap. Light saturation and compression serve kick/bass/stabs and clap dynamics. Chorus adds movement to stabs/pad; tempo-derived dotted-eighth delay answers plucks/lead; high-passed plate reverb adds space. Dry requests omit delay/reverb. The reference has **8 tracks, 392 notes, 23 inserts, 11 canonical lanes and 845 points**.

Track gains were calibrated with isolated real host renders. Initial nominal settings left melodic voices far below the kick; those renders were rejected as the reference. The delivered balance raises the synth/percussion layers, preserves peak headroom, and does not use a master maximizer. Programmed beat gain envelopes duck bass/stabs/pad around kicks and disengage during the breakdown. These are explicit linear gain lanes, not audio-triggered sidechain compression. Slow EQ low-pass sweeps, pan movement and delay-wet throws are separate editable lanes. No arbitrary FX were inserted to imply quality.

## Pinned actual host capabilities

Audited the installed **SoundCraft CLI 0.11.0**, `describe`, `engine.plugins` (27 built-ins), real command probes and saved native projects. The complete live parameter descriptors and command contract are in `artifacts/phase4-house-reference/pinned-capabilities.json`; the tracked fixture adds only the five newly used FX descriptors to the original recordings.

| Pin | SHA-256 |
| --- | --- |
| Executable | `84466d199a6cb4d4924a9179fdf36b0c6d1ab3a0082b60ceed50d06f09f0b130` |
| Existing discovery contract | `5af7ed8eed0e51a251da6dee6f57a9b83ac6ae004c70b13a96416cdee4ad49f7` |

The discovery contract is unchanged, so prior verified bundles still load. New parameter conversions do not relax old pin/drift checks.

| Actual built-in / parameters | Discovered native units / ranges | Kuang profile and boundary |
| --- | --- | --- |
| `subtractive_synth.osc1_wave`, `osc2_wave` | Choice 0–3: Saw, Square, Sine, Triangle | Normalized canonical positions 0, 1/3, 2/3, 1; converted to integer selectors. Fractional choices rejected |
| `osc_mix` | Percent 0–100 | Normalized blend; explicitly configured per voice |
| `osc2_semitones`, `osc2_detune` | Semitones -24–24; Cents -100–100 | Native editable; no matching canonical 0.1 pitch unit. Defaults retained (0 semitones, 7 cents); no invented unit aliases |
| `cutoff`, `resonance` | Hz 20–20000; Percent 0–100 | Existing cutoff/normalized resonance mappings |
| `filter_env_amount` | Percent -100–100 | Signed normalized envelope amount; actual filter envelope, no LFO claim |
| Amp/filter attack, decay, sustain, release | Attack 0.5–5000 ms; decay 1–5000 ms; sustain 0–100%; release 1–10000 ms | Explicit voice-specific ms/normalized controls |
| `velocity`, `level`, `glide` | 0–100%; -48–6 dB; 0–1000 ms | Velocity/level configured; glide left at zero, not presented as pitch-slide support |
| `drum_synth` | Kick decay 50–2000 ms; hat 20–500 ms; open hat 100–3000 ms; snare decay 50–1000 ms; snappy 0–100% | Short controlled drum decays; standard MIDI percussion notes. Pitch tune controls remain native-only |
| `eq_7band` | HPF 10–2000 Hz; LPF 1000–20000 Hz; gain -24–24 dB; on/off toggles | HPF, low-mid reduction, high shelf and automated LPF. Q/unitless controls omitted; no fake Hz/Q mapping |
| `compressor` | Threshold -60–0 dB; attack ~0.01–300 ms; release 5–3000 ms; makeup 0–40 dB; ratio 1–100 | Threshold/attack/release/makeup mapped. Ratio uses discovered 4:1 default; no ratio unit added to schema. No external sidechain routing |
| `saturator` | Drive 0–36 dB; output -24–12 dB; tone 1000–20000 Hz; mix 0–100% | Modest parallel drive with output compensation |
| `chorus` | Rate ~0.05–5 Hz; depth/mix/spread 0–100% | Genuine built-in effect modulation; pad/stab depth and spread explicitly configured |
| `mod_delay` | Time 1–2000 ms; feedback -99–99%; modulation rate ~0.01–10 Hz; depth/mix 0–100%; LPF 500–20000 Hz | Tempo-derived time; restrained modulation; automated wet throws |
| `plate_reverb` / `room_reverb` | Decay ~0.1–20 seconds; pre-delay 0–250 ms; damping 1000–20000 Hz; low cut 20–1000 Hz; width/mix 0–100% | `soundcraft.decay_ms` explicitly converts ms to seconds. Profile uses plate with low-cut and pre-delay |
| Flanger / phaser / maximizer | Present in live catalog, including their modulation controls | Available engine features; omitted from this arrangement. No master insert/bus mapping added |

`mix.instrument_param` edits a single native instrument parameter. Two real tests change filter decay, compare every other native field exactly and save/reopen again. Kuang native apply continues to support mixer/FX scalars and existing supported lanes; canonical instrument/note edits use fresh export. Manual host edits remain deliberate drift, not automatically imported changes. The tests retain original sources and do not patch `.scraft` JSON to manufacture support.

`automation.set_point` supports mixer/plugin insert addresses. Real probes of `instrument:cutoff` and `instrument.cutoff` returned unknown-parameter errors. No synth LFO, modulation matrix or wavetable appears in the audited instrument descriptors. The delivered profile uses the real filter envelope, effect modulation and EQ/gain automation. It does not claim these replace every use of an instrument LFO. Discrete plugin automation and FX bypass automation are rejected. Existing requirements for tick-zero starts, interpolation shapes, bounds, locks, scopes and hashes remain enforced.

## Listening files and reproducible evidence

On the evaluation machine, all new files are under `/home/User/Kuang/artifacts/phase4-house-reference/`:

| File / directory | Purpose |
| --- | --- |
| `A-original.wav` | Fresh full render of the unchanged Phase 2 house baseline |
| `B-refined.wav` | Full refined reference, 16 bars + one-second tail |
| `RMS-matched/A-original.wav`, `RMS-matched/B-refined.wav` | Audition at equal full-file RMS; refined attenuated by **7.3523 dB** |
| `sections/original-*.wav`, `sections/refined-*.wav` | Intro, groove, breakdown and drop excerpts with original PCM and timing |
| `A-original/native/session.scraft` | Verified saved baseline clone |
| `B-refined/native/session.scraft` | Editable refined project, companion canonical snapshot and identity map |
| `B-refined-saved/session.scraft` | Another verified full-state save/reopen |
| `verification.json` | Complete measurements, aligned difference, source before/after inventories and artifact hashes |

Open both native sessions with SoundCraft's Open session action. Instruments, ordered inserts, MIDI notes, gain/pan/FX lanes and section markers are native editable objects. Keep each bundle's canonical snapshot and manifest. For typed revisions, refined sections are `Intro`, `Groove`, `Breakdown`, `Drop`; use those exact names. Automated base gain/filter parameters require lane edits rather than base-only prose revisions. Lead reverb/gain revisions and exact compound undo/redo were also exercised through the public CLI.

The prior baseline remains at `artifacts/phase2-house-final/preview.wav`; its complete directory, `artifacts/phase3-house-release/` and all original examples were hashed before the work and remained byte-identical (**40 files**). Fresh A has the same SHA-256 as the historical baseline render.

To reproduce using an existing house `create` output and the installed host:

```bash
python3 tools/phase4_reference.py \
  --baseline artifacts/phase2-house-final \
  --out-dir artifacts/another-house-reference \
  --soundcraft /absolute/path/to/soundcraft-cli \
  --preserve artifacts/phase3-house-release --preserve examples
```

The tool requires a new output directory, hashes sources, saves native clones, renders both references freshly, checks non-silence/no clipping, compares full native saved state, creates equal-RMS audition copies and PCM excerpts, and removes its owned output on failure. It never downloads a backend or edits native JSON. Create directories and baseline inputs are user-supplied; no home-root prompt files are needed.

## Measured result and remaining limits

Both full WAVs are **48 kHz, stereo, 24-bit integer PCM, 1,510,857 frames / 31.4761875 s**, with **zero clipped samples**.

| Measurement | Original | Refined |
| --- | ---: | ---: |
| Sample peak dBFS | -17.1733 | -8.7024 |
| RMS dBFS | -36.9684 | -29.6160 |
| Crest factor dB | 19.7951 | 20.9136 |
| Intro RMS dBFS | -35.7659 | -31.4193 |
| Groove RMS dBFS | -35.4634 | -28.5943 |
| Breakdown RMS dBFS | -54.3924 | -31.3750 |
| Drop RMS dBFS | -35.5696 | -27.7454 |
| Estimated 20–120 Hz power | 79.34% | 24.35% |
| Estimated 120–500 Hz power | 18.59% | 48.05% |
| Estimated 500–2000 Hz power | 1.57% | 22.98% |
| Estimated 2000–8000 Hz power | 0.40% | 3.89% |
| Estimated 8000 Hz–Nyquist power | 0.10% | 0.72% |
| Stereo correlation | 0.999717 | 0.995235 |
| Side RMS | 0.000169 | 0.001670 |

Band power uses 64 equally spaced 2048-frame Hann-window FFTs, both channels, 23.4375 Hz bins; fractions exclude DC and frequencies below 20 Hz. Short windows give coarse sub-band resolution. These are sampled estimates, not integrated LUFS, true peak, a perceptual mastering meter or proof of audibility. Crest is higher in the refined mix; there is no claim that it has been made commercially dense or mastered. The mix remains strongly correlated and its stereo spread is modest, despite increased side energy. The supplied equal-RMS pair avoids confusing the raw 7.35 dB level change with a preference judgment.

An otherwise identical real automation-on/off render has a measured delta RMS of **-45.2706 dBFS**. This establishes that persisted automation affects rendered PCM, beyond merely counting saved points. A/B full-file difference is **-30.4225 dBFS RMS**; differing notes/timbres make this a change measurement, not a quality score.

Human listening to this refined reference has **not** been performed or claimed. The user previously heard the baseline; their evaluation of the new matched A/B is still needed. The deliverable improves arrangement/timbre/balance by explicit design and measurable evidence. Free built-in synth/drum character, modest stereo image, limited transition vocabulary, no exposed synth LFO/wavetable, one-second preview tails, no bus/master processing, no LUFS/true-peak certification and no automatic host reconciliation remain limitations. No external plugin evaluation or download was necessary for this compatible subset.

## Verification

- **167 tests, 0 failures/errors, 0 skips**, Python 3.13.7, real SoundCraft enabled; 77.106 s. This retains all 149 prior methods and adds 18. Tests cover musical invariants, determinism, exact transposition, omissions, bounds/units, discrete-selector rejection, known-tone spectral analysis, two real refined variants, direct native instrument editing, FX/lane edits, exact state preservation, save/reopen, rendered automation and audio format/level checks.
- Real variants: 16-bar C-major / 126 BPM bright house and 8-bar D-minor / 122 BPM dark house. Existing trap/house Phase 3 integrations, 20-edit regression and exact history replay also pass.
- Complete transcript: `artifacts/phase4-house-proof/real-suite-final.log`; native production results: `artifacts/phase4-house-integration-final-phase4/verification.json`; previous integration results in `artifacts/phase4-house-integration-final/`.
- Wheel build/install succeeded using existing setuptools/wheel and no downloads. Installed CLI created refined house from a directory outside the import root; packaged Lua resource checked. Build/install logs and wheel are in `artifacts/phase4-house-proof/`.
- Public CLI demo → proposal → apply → exact undo/redo, deterministic refined creation and reviewed compound refined revision replay passed; logs under `artifacts/phase4-house-proof/cli-smoke.log`.
- CI matrix remains Python 3.11 / 3.13 and now exercises refined CLI determinism. Python 3.11 is not installed locally; its execution is checked remotely after push. Host tests opt in and never download SoundCraft.

Compact checked-in measurements/hashes are in [PHASE4_VERIFICATION.json](PHASE4_VERIFICATION.json). Full generated audio/projects and scratch stay Git-ignored in `artifacts/` and `.local/`.
