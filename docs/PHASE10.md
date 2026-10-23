# Phase 10: pad space, envelopes and a quiet mono pulse

Built from clean main **`dd79840098d067b94d74cec40e1789c5f5a4a472`**. The user listened to Phase 9 A/B/C, liked all three, and preferred C's bass balance. Phase 9 B and C have the same native bass; C adds gentle off-host compression/gain. Phase 10 keeps that native bass and tests pad entry/release, spatial tails and a separate quiet sine. This is an authored progression of the existing song, not a new composer or DAW. New listening preference is unknown.

`kuang.atmosphere.atmosphere_house()` accepts only exact Phase 9 native canonical **`209b21e6b58283237ebaf3f29e56e7af6d2d0f6b8f267bff855663267e7c17ef`**. Combined D is **`dad1db280f798fdf07ab4b0243bcc6e528f680b30f32b8a5e92104a94ce640b1`**. All **1446 original notes**, clip fields, IDs, timings, pitches, velocities and channels remain exact. Tempo **126 BPM**, C minor, **64 bars**, six sections and original SongSpec provenance remain exact. D adds one native track with **90** notes: **11 tracks / 1536 notes**. Canonical schema 0.1, transactions, adapter, previous profiles and previous tests are unchanged. Core/runtime remain MIT/standard-library-only, with no new dependencies, plugins, samples, models, system installations or service calls.

## Listening labels and files

| Label | Contents | Editable native |
| --- | --- | --- |
| A | Unchanged **Phase 9 B native pre-master**, byte-identical fresh full bounce | Yes |
| B | A plus optional sine pulse only; all ten original tracks/lanes unchanged | Yes |
| C | A plus pad/envelope/space revisions only | Yes |
| D | Combined B+C, primary candidate | Yes |
| E | D through the existing gentle off-host compression/gain recipe | **No**, reproducible WAV derivation |

These labels are specific to Phase 10; C is **not** the previous Phase 9 master. Start with `A-full-LUFS-matched.wav` versus `D-full-LUFS-matched.wav`, then matched D/E. Full raw A/B/C/D/E remain at the release root. `listening/` has full A/D/E and independently matched eight-bar drop A/B/C/D. `variants/A,B,C/` and root D contain complete canonical/MIDI/native bundles. `native/session.scraft` is the main editable D; preserve its companions. `saved-native/` is a separately saved/reopened copy.

The **163,432,574-byte** `artifacts/phase10-house/phase10-house-listening.zip` contains matched full A/D/E, matched drop A/D, same-input lowend OFF/ON and pad wet/dry controls, editable D and variants A/B/C, raw D/E for frozen replay, measurements, MIT notices and standalone master code. Full pulse-only/space-only WAVs and extra diagnostics remain on the server to keep the download below 180 MB. ZIP SHA-256: **`6484dfb795cca2e10c09f3e4d83f1b53d2b71b368c311dc22d18ac341066e135`**.

```bash
scp YOUR_HOST:/home/User/Kuang/artifacts/phase10-house/phase10-house-listening.zip .
```

## Exact pad and space changes

Pad **faders -2/-4 dB and every existing gain-lane point remain exact**. Sustains are reduced; native instrument trims compensate for the changed envelope/wet blend. The final combined pad stem averages **1.216799 dB quieter** over the active eight-bar drop than the original. An initial more recessed trial was rejected. No hidden waveform gain/EQ is used in native A–D.

| Native control | Phase 9 | Phase 10 |
| --- | --- | --- |
| Body amp attack / decay / sustain / release | 850 / 950 ms / .55 / 1250 ms | **320 / 850 ms / .42 / 1900 ms** |
| Air amp attack / decay / sustain / release | 500 / 600 ms / .32 / 1100 ms | **620 / 1000 ms / .24 / 2200 ms** |
| Body filter attack / decay / release | 1400 / 1900 / 1250 ms | **650 / 1500 / 1900 ms** |
| Air filter attack / decay / release | 900 / 1400 / 1100 ms | **1100 / 1400 / 2200 ms** |
| Body / air instrument level | -9 / -6 dB | **-7 / -3.5 dB**, measured envelope compensation |
| Body / air pan | -.44 / +.48 | **-.72 / +.78** |
| Body / air chorus depth; wet | .24 / .26; .28 / .30 | **.28 / .30; .32 / .34**; rates/spread unchanged |
| Body phaser depth / wet | .22 / .10 | **.14 / .06**, reduced |
| Body / air plate decay | 3400 / 3400 ms | **3800 / 3600 ms** |
| Plate lowcut; width; base wet | 650 / 650 Hz; .8; .25 | **600 / 700 Hz; .95; .31** |
| New body / air delay | Absent | **476.190476 / 357.142857 ms**, quarter/dotted eighth; feedback **.30/.26**, LPF **4500 Hz**, modulation depth **0** |
| Lead / arp delay feedback; base wet | .46; .035 | **.48; .06** |
| Lead plate / arp room decay; width; base wet | 3200 / 3200 ms; .8; .10 | **3600 / 3400 ms; .9; .135** |
| Stab pan | -.48 | **-.60**; answering arp +.60 and lead pan lane unchanged |

Body/air oscillator choices, filter sustain and prior musical notes remain unchanged. Static ADSRs are distinct from effect tails; direct synth ADSR automation is unsupported. Existing chorus/phaser provide effect modulation, not oscillator LFO/wavetable synthesis. Native track panning alone does not independently widen one voice; width is measured from the actual separate pad/air/harmonic pans and effects.

All **23 original lane IDs/targets/parameters, point IDs/times/shapes/order** remain. Only existing wet values at **six effects** change: body/air plates, lead plate, arp room, lead/arp delays. Delay points gain **.025** when below .1, otherwise **.04**, capped at .62. Body/air plate points add **.06×(1−wet)**, capped at .68; lead/arp reverb points add **.035×(1−wet)**, capped at .68. Thus pad plate wet is **.295 initially / .2668 at drop / .6616 in breakdown**; base .31 is not the effective automated value. No gain/filter/duck lane is discarded.

Two new stable pad-delay wet lanes each have ten points at zero-based bars **0,20,24,30,31.9,32,40,48,56,64**. Body values **.12,.14,.22,.22,.16,.08,.10,.12,.08,.08**; air **.10,.14,.20,.22,.16,.07,.10,.12,.08,.08**. The drop becomes drier after the spacious breakdown. Delay is inserted before plate; all old effect IDs and their relative order remain, with native automation slots mapped by stable effect identity. Including the pulse duck, D has **26 lanes / 7380 points**, versus A's **23 / 6079**.

## Sine feasibility, phase and rejected notes

The actual pinned catalog selects **Sine native index 2** (canonical normalized **2/3**), both oscillators, mix **0**, no detuned second sub. Pulse synth cutoff **120 Hz**, resonance **0**, filter-envelope amount **0**, amp/filter **8 ms attack / 110 ms decay / 0 sustain / 24 ms release**, velocity response .25, native level **-4 dB**, fader **-18 dB**, pan **0**. Synth voice state is tested with one real note then silence: both pre-onset and released 1–2 second windows are digitally zero. Maximum adjacent sample step on the pulse stem is **.00026691**; this is a discontinuity diagnostic, not an audibility guarantee.

**EQ7 LPF cannot do 140 Hz:** its minimum is 1000 Hz. The actual existing **EQ1** exposes Low Pass choice **4** of 0..6, cutoff **20–20000 Hz**. The new registry uses normalized **4/6 → native 4**, frequency **140 Hz**. Q stays at the native default; its missing canonical unit is not relabelled. EQ7 separately provides **30 Hz / 12 dB/oct HPF**, with its LPF off. Full native state, named parameters, exact note fields, all automation and a scoped EQ1 cutoff edit/save/reopen/undo/redo are tested against the pinned host.

Pulses occur only in **bars 9–16 and 33–48** (one-based); no new sine in intro/build/break/outro. Each starts **592 ticks / 293.651 ms after kick**, lasts **180 ticks / 89.286 ms**, and releases before the next kick with about **69 ms** remaining. Pitch follows the actual existing bass root, not an invented lower octave. The new lane ducks to **-34 dB** at kick, holds through tick120, rises through **-21 dB at420**, **-18 dB at560**, holds to900, then returns on the next kick. This is **programmed ducking**, not input-triggered sidechain. No mapped phase-reset control is claimed.

The first 96-note pulse candidate had positive aggregate energy but **-1.297198 dB local cancellation** at Bb1 turnaround beats. The final removes only those **six new Bb1 pulses**; all original bass notes remain. **90 C2/G1 pulses** pass the same-input gates. Rejected/pruned audits are retained under release `proof/`; the negative result is part of the decision, not hidden by averaging.

Eight-bar isolated native kick/bass/pulse controls use fresh DSP state and eight seconds of tail. Pulse RMS is **16.659438 dB below bass**. Bass/pulse one-pole 20–120 Hz interaction is **+.306871 dB**, correlation **.235476**; this is not oscillator phase calibration. Lowend ON/OFF pulse-window minimum is **0.000000 dB** after pruning. Large positive ratios over bass rests are accompanied by absolute RMS values and do not describe whole-mix gain.

| Absolute sampled low-band power, ON vs OFF | Change dB |
| --- | --- |
| 20–40 Hz | **-.113017** |
| 40–80 Hz | **+.281053** |
| 80–120 Hz | **+.041006** |
| 120–250 Hz | **+.010292** |
| Supplemental 20–60 Hz | **+.087573** |

Absolute mean-square powers, fractions and per-window results are in `verification.json`. Spectra use 16 aligned **16384-frame Hann windows / 2.9296875 Hz bins**; supplemental 20–60 is measured directly, not inferred from the 40–80 split. It overlaps other bands and must not be summed into their partition. The **120 Hz high-pass small-speaker approximation changes only +.008503 dB RMS** with pulse on: negligible translation benefit. It is a diagnostic approximation, not a speaker model or production processing. Original upper-harmonic bass remains exact. The sine is retained as optional subtle low-end support; human preference can still favor C without it.

## Actual effects, spatial field and levels

Same revised pad MIDI/ADSR/pan with **only delay/reverb wet disabled** produces a wet/dry difference **-45.837127 dBFS RMS**, **49.31%** of the enabled pad RMS. Chorus/phaser remain identical in both. A separate original chord with all wet controls at zero and gain lanes removed in both isolates ADSR: new entry-window RMS **-32.768029** versus old **-41.276654 dBFS** (**+8.508625 dB**); a late 1.35–1.75-second release window **-79.648387** versus **-101.261070 dBFS**. The latter is very quiet and is not presented as proof of prominent audible tails in context. Reverberant tails and static synth release are reported separately.

A single unchanged short lead note has actual echo peaks **357.145833 ms apart**, configured **357.142857 ms** (error **.002976 ms**). Three post-note windows have wet RMS **.005307 / .001801 / .000151** while corresponding dry is digitally zero. These demonstrate non-inert rhythmic echoes; listening decides whether the amount is tasteful.

Full D >500 Hz sampled **side/mid power .055433**, versus A **.027258**. Expressed as **side/(mid+side)** these are **5.2521% vs 2.6535%**. High-band mono retention **94.7479%**, low-band **99.999991%**; mono RMS loss **.071086 dB**, no fold-down clipping. Full correlation **.967779**. Breakdown RMS **-37.822688 dBFS**, main drop **-25.435581 dBFS**; structural contrast remains. These are energy/window diagnostics, not perceptual scores.

All full WAVs: **48 kHz stereo 24-bit PCM**, **6,091,429 frames / 126.9047708 seconds**, exactly 64 bars (**121.9047619 seconds**) plus five seconds of release tail. No clipped samples; final 250 ms are digitally zero.

| Raw full file | Integrated LUFS | True peak dBTP | RMS dBFS | Crest dB |
| --- | --- | --- | --- | --- |
| A unchanged native | -25.058235 | -5.357554 | -27.000852 | 21.643298 |
| B pulse only | -25.018212 | -5.357554 | -26.962299 | 21.604746 |
| C space only | -25.077169 | -5.339738 | -27.094918 | 21.755180 |
| D combined native | -25.050292 | -5.339738 | -27.055525 | 21.715788 |
| E off-host master | -22.194591 | -2.922605 | -24.199081 | 21.276475 |

D's native loudness differs from A by only **+.007944 LU**, RMS **-.054674 dB**. Full A/D/E audition copies match **-25.058235 LUFS** through constant attenuation only: **0 / -.007944 / -2.863644 dB**. Drop A/B/C/D independently match **-23.895547 LUFS**: **-.161945 / -.210494 / 0 / -.050380 dB**. All match errors are below **.001 LU**. Causal wet/dry and pulse OFF/ON controls retain identical native input/fader levels and are not independently normalized, so their changes remain measurable.

E reuses the verified Phase 9 **linked 1.3:1, -20 dBFS, 15/150 ms** compressor, maximum reduction **.940387 dB**, then frozen **3 dB** gain chosen from measured true-peak headroom. No limiter, master EQ/saturation, commercial LUFS target or native master-bus support is claimed. Replaying the **actual extracted ZIP** script gives bit-identical E. Measurement reuses the Phase 9 K-weighted/gated meter, optional explicitly supplied MIT libebur128 1.2.6 backend and golden/analytical vectors. Finite FIR true peak is **not formal EBU certification**; see [PHASE9.md](PHASE9.md) for its algorithm, licensing and limits.

## Reference boundary

The project-local numeric guide arrived at `.local/phase10/reference-guide.json`, SHA-256 **`ca87f8ed06a38a2d7ca49d1b76a249df3404836dc620b919cf7f3247679b34c0`**. It supplies approximate Suno **-15.1 LUFS / .937 correlation / 14.2% >500 Hz side fraction**, and Phase 8 **-25.6 / .985 / 2.5%**. These are user-supplied directional measurements of different duration/arrangement/vocals, with potentially different measurement windows. They are not a one-to-one mastering target or a requirement to reach that stereo fraction. This implementation loads numeric metadata only; no Suno recording, MP3, vocal, motif, stem, API or proprietary asset is accessed/copied/redistributed. The guide is optional and does not alter generation. A later user-licensed reference can use the private Phase 9 numeric comparison interface.

## Reproduce and verify

```bash
mkdir -p .local/phase10/tmp
export TMPDIR="$PWD/.local/phase10/tmp"
python3 tools/phase10_house.py --symbolic --out-dir .local/phase10/new-symbolic
python3 tools/phase10_house.py --source artifacts/phase9-house \
  --out-dir artifacts/my-phase10 --soundcraft /absolute/path/to/soundcraft-cli \
  --reference-guide .local/phase10/reference-guide.json
python3 tools/phase10_house.py package --out-dir artifacts/my-phase10
```

Use new paths. `--meter-library .local/phase10/libebur128.so` explicitly selects the already locally built optional fast backend; no tool/test downloads/builds it. Without it, Python-only measurement is slower. From the extracted ZIP, reproduce E without host/reference library:

```bash
python reproduce/master.py D-phase10-combined-native.wav new-E.wav \
  --recipe reproduce/master-recipe.json
```

The frozen input hash rejects audition copies or stale source files. Native A–D have no hidden postprocessing; only E and the clearly labelled small-speaker diagnostic are off-host DSP. Matching/cutting is explicitly labelled.

SoundCraft remains pinned to **0.11.0**, executable SHA-256 **`84466d199a6cb4d4924a9179fdf36b0c6d1ab3a0082b60ceed50d06f09f0b130`**, contract **`5af7ed8eed0e51a251da6dee6f57a9b83ac6ae004c70b13a96416cdee4ad49f7`**. New tests cover causal deterministic variants, original notes/lanes, source locks/drift/no-clobber, exact Choice/Hz units, same-input controls, synthetic cancellation/HP diagnostics, full independent native export/save/reopen/every note/FX/lane/marker, identical repeated full D/pulse PCM, remeasured matching, native scoped EQ edit/undo/redo and extracted-ZIP master replay. Offline suite: **261 methods, 248 passed / 13 host opt-ins skipped**. Full real suite: **261/261 passed**, zero skips/failures/errors, **1329.580s**, Python **3.13.7** with pinned SoundCraft. All **246** old methods and **6652** historical artifact/example files remain unchanged. The installed wheel reproduces E exactly outside checkout imports. Full evidence is recorded in [STATUS.md](STATUS.md), [PHASE10_VERIFICATION.json](PHASE10_VERIFICATION.json) and release `proof/`; post-push Python **3.11/3.13** CI results are in `proof/release-summary.json`. No test result establishes human preference or club readiness. Native timbre breadth, static synth envelopes, missing phase-reset/true-sidechain/canonical sampler/master mapping and limited stereo complexity remain constraints.
