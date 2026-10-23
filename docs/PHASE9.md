# Phase 9: source translation mix and a measured optional master

Implemented from clean main **`7552c6236a353f7629161cf1ec1909851be7f384`**, following the user's actual Phase 8 audition. The user reported better production but uncertain perceived low-end weight, possibly affected by headphones. Sampled sub-power fraction alone cannot establish perceived weight. This candidate tests **upper bass harmonics, kick attack/tail balance and low-mid separation**, with comparable stem/mix RMS, rather than a broad sub boost. No professional reference audio is included and no ideal EQ curve is asserted.

One opt-in profile, `kuang/translation.py`, takes only exact Phase 8 canonical **`22a3d95c5479dbdd312db6aefe803e0e600ba7ecd62350060c2e1880759ca2a7`** and produces **`209b21e6b58283237ebaf3f29e56e7af6d2d0f6b8f267bff855663267e7c17ef`**. All **1446 notes**, IDs, clip fields, timings, velocities, channels, **23 automation lanes / 6079 points**, six sections, tempo **126 BPM**, C minor and **64 bars** remain exact. There are **no note exceptions**. Only the MIDI conductor project-name annotation changes alongside the new project name. The original 16-bar SongSpec remains unmodified provenance; the separate arrangement remains 64 bars. Canonical **0.1**, transactions, host adapter and earlier profiles/tests remain unchanged.

## Native sound/mix controls

| Control | Phase 8 A | Phase 9 B |
| --- | --- | --- |
| Kick native level / decay | -6 dB / 400 ms | **-7 dB / 280 ms** |
| Kick EQ | HPF 28 Hz, low-mid -2 dB at 300 Hz | HPF **30 Hz**, low-mid **-3.5 dB at 240 Hz**, presence **+1.5 dB at 2600 Hz** |
| Kick compressor | Threshold -24 dB, attack .25 ms, release 60 ms, makeup 3 dB | **-20 dB / 8 ms / 75 ms / 1 dB**; retain more initial transient |
| Kick saturation | Drive 3 dB, wet .32, output -1.5 dB | **5 dB / .36 / -2 dB** |
| Bass oscillator / filter | Single square, 340 Hz cutoff, filter-envelope amount .22 | **Single saw**, **650 Hz**, **.18**; adds even harmonics without a detuned second sub |
| Bass envelope / native level | Decay 135 ms, sustain .28, level -6 dB | **160 ms / .24 / -7 dB**; attack **1.5 ms** and release **28 ms** unchanged |
| Bass EQ | Low-mid -1 dB at 300 Hz | **0 dB at 180 Hz**; no sub shelf boost |
| Bass compressor | -24 dB / 8 ms / 85 ms / makeup 2 dB | **-25 dB / 12 ms / 95 ms / 1 dB** |
| Bass saturation | Drive 3 dB, wet .32, output -1.5 dB, tone 7 kHz | **7 dB / .45 / +1.5 dB / 4 kHz** |
| Stab EQ / pan; answer pan | Low-mid -2 dB; -.40; +.50 | **-3 dB; -.48; +.60** |

The bass output trim is measured compensation for a quieter patch, not an unreported level trick. An initial -3.5 dB output trial increased harmonic *fraction* but lost **.94 dB absolute harmonic power** and **5.27 dB stem RMS**; it was rejected. The final +1.5 dB trim restores comparable average level and must still pass absolute-band and RMS gates. Base bass/kick faders, all native beat-duck/filter/delay/reverb/pan lanes, lead, drums and **entire corrected pad/air tracks** stay unchanged. No new tracks or extra effect inserts. Two new registry entries expose the discovered EQ high-mid **Hz/dB** controls without changing schema units.

Kick tuning stays at the native default. The catalog labels it **Semitones**, unsupported by canonical 0.1's unit set; it is not relabelled Hz or normalized. Synth pitch/detune, direct ADSR automation, oscillator LFO/wavetable and a true external kick-triggered sidechain remain unsupported. The earlier tempo-programmed gain ducking remains exactly intact.

## Bounded host/source gate

SoundCraft **0.11.0**, executable SHA-256 **`84466d199a6cb4d4924a9179fdf36b0c6d1ab3a0082b60ceed50d06f09f0b130`**, existing adapter contract **`5af7ed8eed0e51a251da6dee6f57a9b83ac6ae004c70b13a96416cdee4ad49f7`**. Extra commands were discovered through actual `commands`/`describe`, not assumed or added to the production adapter's whitelist.

`mix.sampler_load` **works** with an original, self-generated 220 Hz decaying calibration pulse. The CLI saves `sources[].path` as **`Audio Files/original-pulse.wav`**, with a native sampler source ID. Copying only the WAV next to `.scraft` fails: it renders silence and warns of missing media. Copying the **complete relative Audio Files folder**, hiding both original asset locations, and reopening gives **exact full native state and identical non-silent 48k/24-bit PCM**, 240,000 frames, zero clips. `tools/phase9_host_gate.py` reproduces the bounded gate. Only native CLI operations generate/save the project; JSON is read for comparison, never edited to invent support.

**This does not establish canonical sampler support.** The current adapter still rejects sampler assets, and no robust canonical asset/manifest/root-note binding is introduced in this milestone. B uses only the existing subtractive/drum synths. No sampled instrument, Surge retry, paid plugin, GPL component or external audio asset is required/bundled.

The catalog has compressor/maximizer/saturator and a bus-creation command. It has no discovered dedicated master-insert operation; bounded `mix.insert` probes for `track:"master"` and `track:0` fail with **no track named master / no track with id 0**. General bus existence does not establish a complete routed master path through Kuang. The adapter's no-bus invariant remains. **B is native editable; C is an off-host reproducible WAV derivation.**

## Meter algorithm, independent validation and limits

`kuang/loudness.py` is runtime-stdlib-only. It implements mono/stereo **K weighting**, complete **400 ms blocks, 100 ms hop (75% overlap)**, absolute **-70 LUFS** then relative **-10 LU** gating, and optional 3-second maximum short-term reading in the Python path. Incomplete final gating blocks are discarded. Mono counts once, stereo sums two equal-weight channels. Silence/below-gate/incomplete-block integrated values are `null`, not invented finite LUFS.

True peak is a **polyphase Hann-windowed sinc reconstruction FIR**, not sample peak or linear interpolation: **4x / 49 taps**, configurable **8x / 97 taps**, both with 12 input-sample support, original-sample maximum and explicit zero-padded filter drain. The finite FIR has frequency/band-edge uncertainty; this is **not formal EBU certification**, a complete EBU Mode meter, or a universal bound on every possible continuous-time peak. Multichannel/LFE weighting, LRA and loudness normalization to a broadcast delivery target are not claimed.

The algorithm/validation follows [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770/en) and [EBU Tech 3341](https://tech.ebu.ch/docs/tech/tech3341.pdf). Test recipes are **original synthetic signals**, including short steady 1 kHz mono/stereo tones, silence, -80 dBFS absolute gating, changing-level/relative-gate segments, incomplete blocks and the analytically specified tapered true-peak tone conditions from Tech 3341 cases 15–19. They are not redistributed official test audio or a claim of completing the full conformance suite.

Independent reference: **MIT [libebur128 1.2.6](https://github.com/jiixyj/libebur128/tree/v1.2.6)**, official tag commit **`67b33abe1558160ed76ada1322329b0e9e058b02`**, downloaded source tar SHA-256 **`baa7fc293a3d4651e244d8022ad03ab797ca3c2ad8442c43199afe8059faa613`**. It was compiled with the already installed `cc` under `.local/phase9/`, with no system installation. Its implementation uses a different C filter/state path from the Python cascade. Frozen recipe/PCM-hash/golden results are committed at `tests/fixtures/loudness-golden.json`; tests do not download or need the library. All **12 vectors** agree with **.01 LU / .01 dBTP** tolerances. The true-peak tone checks also compare directly against known analytical amplitude with the stated **±.4 dB** bound, so reference agreement alone is not the only check.

Examples: 1 kHz stereo at -23 dBFS gives **-22.993332 LUFS**, mono **-26.003632 LUFS**; the 12 kHz/45° .5-amplitude intersample vector has sample peak about **-9.03 dBFS** but true peak **-6.053409 dBTP**; the 1.41-amplitude variant exceeds **+2.95 dBTP** while its samples remain below 0 dBFS. This explicitly distinguishes sample and true peaks. A real one-bar C excerpt also agrees across Python 4x, Python 8x and C-reference 4x: LUFS about **-20.442843**, true peak **-5.646952 dBTP**. Full-song sample/true maxima happen to coincide; that is an observed result, not a substituted measurement method.

The optional explicit `--meter-library` backend is pinned to **libebur128 1.2.6, 48k/4x** and fails if unavailable/incompatible; it is never fetched, bundled or silently selected. Python is the dependency-free fallback. The interpolator/design attribution and MIT permission are retained in the Python source and [license notice](licenses/libebur128-MIT.txt). Kuang core remains MIT; no runtime dependency was added.

## Native stems and mix evidence

Same-MIDI native eight-bar drop stems, fresh DSP state, 3 seconds of release tail; no EQ/gain changes to audio after rendering. Spectra use **16384-frame Hann windows**, **2.9296875 Hz bins**, 16 equally spaced windows, both channels, absolute window-power-normalized mean squares **and per-window powers/fractions**. Eight bands partition 20 Hz–Nyquist: **20–40, 40–80, 80–120, 120–250, 250–500, 500–2000, 2000–8000, 8000–Nyquist**. The supplemental **100–400 Hz** diagnostic overlaps those bands and must not be added to the partition fractions. These are sampled comparisons of aligned windows, not a continuous whole-song spectrum or an ideal EQ curve. The user's earlier 77.9% estimate used different windows/resolution; do not compare it directly to this drop audit.

| Measured native stem | A | B | Change |
| --- | --- | --- | --- |
| Bass RMS dBFS | -32.829041 | -33.099752 | **-.270711 dB** |
| Bass 100–400 Hz absolute mean square | .0000856990 | .0002183884 | **+4.062540 dB** |
| Bass 100–400 Hz sampled fraction | .103270 | .279376 | Harmonic redistribution, not a standalone quality score |
| Kick RMS dBFS | -29.022586 | -28.775975 | **+.246611 dB** |
| Kick first 0–20 ms median RMS dBFS | -18.874564 | -16.726879 | **+2.147685 dB** |
| Kick 100–200 ms tail median RMS dBFS | -32.066654 | -41.154467 | **-9.087813 dB** |

The full B audition is additionally attenuated .486633 dB for equal integrated loudness with A; the bass's measured 100–400 Hz gain remains about **3.58 dB** after that global compensation. No source notes/timing were moved to manufacture the transient result.

Independent B kick+bass stem sum differs from a combined native bounce by at most **1 integer LSB**, RMS **-149.08 dBFS**. Mono 20–120 Hz interaction is **+.015990 dB**, correlation **.004134** under the explicitly documented one-pole diagnostic; this is no significant destructive cancellation, not oscillator phase-reset calibration. The host exposes no verified phase-reset control. Bass saturator enabled/bypass uses identical input/MIDI: aligned difference **-39.739150 dBFS RMS**, **46.56%** of the enabled stem's RMS. That comparison includes the saturator's output trim as well as nonlinear processing; it is not labelled a pure distortion-only difference.

## A, B and C: measured levels and honest mastering

All full files: **48 kHz, stereo 24-bit PCM**, **6,091,429 frames / 126.9047708 s**, exactly 64 bars (121.9047619 s) plus five seconds of tail, **zero clipped samples**, silent final 250 ms. A is a fresh native rerender, **byte-identical** to historical Phase 8 B. B's full native state survives save/reopen; independent integration rerenders the saved project and compares full PCM hashes.

| Full raw file | Integrated LUFS | True peak dBTP | RMS dBFS | Crest dB |
| --- | --- | --- | --- | --- |
| **A: Phase 8 pre-master** | -25.544868 | -5.495356 | -27.075596 | 21.580240 |
| **B: Phase 9 native pre-master** | -25.058235 | -5.357554 | -27.000852 | 21.643298 |
| **C: Phase 9 off-host master** | -22.204615 | -2.911396 | -24.141741 | 21.230345 |

B's whole-file RMS rises only **.074744 dB**. C uses a **linked stereo peak compressor**, threshold **-20 dBFS**, ratio **1.3:1**, exponential **15 ms attack / 150 ms release**, no makeup, followed by **3 dB** constant gain. Maximum actual gain reduction is **.940387 dB**, active above .1 dB for **11.09%** of frames; compressor-only RMS change **-.140889 dB**. Gain is selected from **75% of the compressed signal's measured headroom to -1.2 dBTP, capped at 3 dB**. Its actual final -2.91 dBTP is conservative. There is **no limiter, master EQ, hidden saturation or claimed native master insert** in C. No commercial LUFS target was invented. Dynamics remain substantial; C is intentionally a gentle experiment, not loudness-maximized mastering.

`master-recipe.json` freezes all controls, input SHA-256 and selected gain. `kuang/mastering.py` reproduces the two explicit 24-bit quantization stages deterministically with Python alone. It rejects wrong input hashes, extra recipe actions, unsupported values, clipping and existing outputs. B remains native editable; C is a labelled derivation. A future revised B requires a new measured recipe, not reuse of a stale hash.

Full audition A/B/C: **-25.544868 LUFS**, by **constant attenuation only** (A 0, B -.486633, C -3.340253 dB), tolerance **.001 LU**. The eight-bar drop comparisons are measured/matched again independently at **-24.075560 LUFS**; whole-song matching is not assumed to match each section. Matched full B/C still have a measurable aligned PCM delta, **-60.097164 dBFS RMS / 2.34%** of matched B RMS. This isolates the small compression change from C's gain increase. LUFS matching is not a human preference or perceptual identity test.

Spatial audit: B >500 Hz side/mid power **.027258** versus A **.026464**, mono energy retention **97.3465%**, low-band retention **99.999992%**, mono RMS loss **.037640 dB**; C high-band retention **97.1964%**, low **99.999992%**, loss **.038728 dB**. Mono fold-down is unclipped. Width changes only modestly; no dramatic spatial improvement is claimed. Pad levels remain exact Phase 8. All six sections/energy contrasts, native automation, note fields and tails are checked.

## Listen, edit, reproduce and supply a reference

One download: **`artifacts/phase9-house/phase9-house-listening.zip`**. It contains full integrated-LUFS-matched A/B/C, separately matched eight-bar drops, raw B and raw C, complete editable B canonical/MIDI/native files, measured levels, MIT notices and the actual standalone frozen master script/source. Raw A remains at the release root; its matching gain is zero. Isolated native stems/saturation control and proof reports remain outside the ZIP to avoid dozens of redundant listening files.

```bash
scp YOUR_HOST:/home/User/Kuang/artifacts/phase9-house/phase9-house-listening.zip .
```

Open `editable-B/native/session.scraft` after extraction, retaining companions. Compare matched B/C first; raw C is intentionally louder. To reproduce C without any host/library dependency, from the extracted ZIP directory:

```bash
python reproduce/master.py B-phase9-premaster.wav new-C.wav \
  --recipe reproduce/master-recipe.json
```

The raw B is required because the frozen input hash correctly rejects an attenuated audition copy. Bit-identical C reconstruction is checked both through the core function and the **actual extracted ZIP script**, away from checkout imports. Linux Python versions/host builds are recorded; this is not a cross-platform floating-point certification.

```bash
mkdir -p .local/phase9/tmp
export TMPDIR="$PWD/.local/phase9/tmp"
python3 tools/phase9_house.py --symbolic --out-dir .local/phase9/new-symbolic
python3 tools/phase9_house.py --source artifacts/phase8-house \
  --out-dir artifacts/my-phase9 --soundcraft /absolute/path/to/soundcraft-cli
python3 tools/phase9_house.py package --out-dir artifacts/my-phase9
python3 tools/phase9_host_gate.py --out-dir .local/phase9/new-host-gate \
  --soundcraft /absolute/path/to/soundcraft-cli
```

For the explicitly optional faster validation backend, obtain the pinned official MIT source **inside `.local/phase9/`**, inspect its COPYING, then use the installed compiler (no system installation):

```bash
cc -O3 -fPIC -shared .local/phase9/libebur128-1.2.6/ebur128/ebur128.c \
  -lm -o .local/phase9/libebur128.so
python3 tools/phase9_meter_check.py --out-dir .local/phase9/new-meter-check \
  --library .local/phase9/libebur128.so
```

Use `--meter-library .local/phase9/libebur128.so` on the build for the explicit fast backend. No tool/test automatically downloads or builds it. Without it, the same standalone Python measurement runs more slowly.

Private future reference interface (license/attribution required, **no reference audio copied into a ZIP**):

```bash
python3 tools/phase9_house.py reference \
  --candidate artifacts/phase9-house/B-phase9-premaster.wav \
  --reference .local/phase9/user-licensed-reference.wav \
  --reference-credit 'Exact artist/title/source attribution' \
  --reference-license 'Exact license or permission supplied by the user' \
  --out-dir .local/phase9/reference-comparison.json
```

This records hashes, supplied rights/credit, LUFS/TP and absolute/fractional bands; it asserts no universal target curve. The current release makes **no professional-reference matching claim**.

Use fresh output paths. Full suite fixtures are staged in `.local/phase9/` and relocated only after all checks complete, preserving the legacy Phase 6 historical-output guard. Tests, build/install, source fingerprints and remote Python 3.11/3.13 results are recorded in STATUS, [PHASE9_VERIFICATION.json](PHASE9_VERIFICATION.json) and the release proof. **Only human listening can decide whether B/C improve the music.** The basic native palette, original simple harmony, modest width, finite-FIR true-peak uncertainty and lack of canonical sampler/master-bus mapping remain limits.
