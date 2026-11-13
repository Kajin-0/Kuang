# Cross-prompt house generation acceptance batch (13 November 2026)

**Purpose:** test Kuang as a *general-purpose, autonomous, editable house-template generator*, not to tune the earlier ~45-iteration reference song. Three independent, original prompts were run with different groove families, keys, tempos and seeds. All third-party Vital presets and source WAVs remain **private** on the user's VPS.

**User involvement:** none is required at this technical stage. The user cannot listen to files left on the VPS, so a future requested listening test **must provide chat-playable audio** (or a genuinely accessible private transfer). These three candidate previews have *not* been listened to by a human producer or by the assistant; inspecting their code, waveforms, frequency content and DSP meters is **not equivalent** to hearing them. Do not solicit subjective judgment until the output is viable and transferable.

## Procedure

All three used the same reviewed, pinned SoundCraft 0.11.0 host, pinned Vitalium private plugin, audited local CC0 house-core drum kit, deterministic 16-bar groove template, simple harmony, no melody/lead, no pad, one independently auditioned bass preset and chord preset; drums were five real independently editable sampler tracks except the intentionally silent auxiliary-percussion role in minimal. Each run used a local private output, *one concurrent Kuang run at a time*, 8 maximum initial preset candidates, 1 per role, 25-s worker timeout and hard 165-s outer limit. A concurrent unrelated VPS Blender video render heavily loaded CPU; one initial 12-s worker timeout and one incorrect working-directory invocation failed closed before success. Neither failure was silently counted as a passing production.

| Candidate | Profile | Key | BPM | Seed | Selected bass | Selected chords |
|---|---|---|---:|---:|---|---|
| deep-Dm-124-s17 | Deep house | D minor | 124 | 17 | Biow Bass | SNFKFutureBounce - Loaded Chords |
| jackin-Fm-126-s23 | Jackin house | F minor | 126 | 23 | LD Bass | minimal house stab 09 |
| minimal-Gm-122-s31 | Minimal house | G minor | 122 | 31 | Biow Bass 2 | minimal house pluck 4 |

Preset decisions differ in all three scenarios; the drum source combinations and MIDI groove fingerprints also differ. This establishes *basic cross-prompt variation and successful native integration*, not the correctness of the chosen sounds.

## Objective technical results

These are **premix** results from the actual native engine, not mastered/signed-off songs.

| Test | Deep | Jackin | Minimal |
|---|---:|---:|---:|
| Native SoundCraft save/reopen | Pass | Pass | Pass |
| Groove structural gates | Pass | Pass | Pass |
| 48-kHz 24-bit stereo render | Pass | Pass | Pass |
| Clipped samples | 0 | 0 | 0 |
| Duration incl. effects tail | 42.968 s | 42.476 s | 43.475 s |
| Integrated loudness | **−25.65 LUFS** | **−30.58 LUFS** | **−28.01 LUFS** |
| True peak | −10.58 dBTP | −12.68 dBTP | −9.12 dBTP |
| Full-clip crest | 19.84 dB | 22.02 dB | 24.11 dB |
| Unused peak headroom (>6 dB) | Warning | Warning | Warning |
| Near-finished preview loudness (<−23 LUFS) | Warning | Warning | Warning |
| Very high crest (>20 dB) | No warning | Warning | Warning |

The values in the final three warning rows are **engineering defaults for near-finished previews, not universal house music laws**; the technical program does not fabricate a psychoacoustic winner or use these as irreversible DSP commands. It will report `NOT_READY` rather than claim a finished output on this evidence.

### Groove-section full-mix spectral distribution

Frequency energy is from 4096-point stereo Hann windows, 8 sampled windows within each actual Groove section, not a human assessment of bass punch or treble clarity:

| Band | Deep | Jackin | Minimal |
|---|---:|---:|---:|
| 20–120 Hz | 25.4% | **53.0%** | 18.6% |
| 120–500 Hz | 41.5% | 22.6% | 25.2% |
| 500–2000 Hz | 19.8% | 19.8% | **54.3%** |
| 2000–8000 Hz | 11.7% | **2.9%** | **1.1%** |
| 8000–24000 Hz | 1.6% | 1.7% | 0.7% |

This does not establish a source is unsuitable, but it reveals a **large tonal difference among automatically selected combinations**. The jackin candidate is strongly sub-dominated; the minimal candidate is mid-dominated with very little measured presence-band power. A consistent near-finished template workflow needs sound selection that considers these genre/role interactions, plus bounded output processing and automated rejection of clearly unviable source combinations. Do **not** respond by forcing the same FFT shape on every style.

## New repeatable evaluator

`kuang.house_batch_acceptance` reads **2–8 already generated private candidates** without modifying them, verifies native evidence, MIDI identity, actual sample and frame format, no clipping, groove fingerprints and distinct source choices, measures a consistent Groove-section spectrum, and records explicit non-final preview warnings. It writes JSON suitable for regression comparison. It does **not** claim to listen, select a subjective winner or redistribute copyrighted sounds.

```sh
cd /home/User
PYTHONPATH=/home/User/Kuang-groove-harmony python3 -m kuang.house_batch_acceptance \
  /home/User/Kuang/.local/kuang-generalization-batch-20261113/deep-Dm-124-s17 \
  /home/User/Kuang/.local/kuang-generalization-batch-20261113/jackin-Fm-126-s23 \
  /home/User/Kuang/.local/kuang-generalization-batch-20261113/minimal-Gm-122-s31 \
  --out /home/User/Kuang/.local/kuang-generalization-batch-20261113/acceptance-next.json
```

The first actual evaluation returned:
- **3/3 native/render technical gates pass**.
- **3/3 independent drum source choices, groove fingerprints and bass/chord preset combinations**.
- **0/3 near-finished preview readiness** based on the defined conservative warnings.
- **no producer-ready claim**, no subjective ranking, no human user review requested.

The private structured record is `/home/User/Kuang/.local/kuang-generalization-batch-20261113/acceptance-v1.json`.

## Engineering decision and next steps

**Do not ask for the user's final listening test yet.** The technical MVP can create varied samples, but output level consistency and source-combination tonal variance are not controlled. The next generic iteration should implement a **two-stage routine**: (1) select and audit a compatible bass/chord/drum palette over an 8–16 bar groove excerpt; (2) once accepted, produce the chosen full-length arrangement exactly once and package an independently measured premaster and a separate bounded master preview. Use early rejection conditions, no endless iteration or repeated 4-minute renders.

Sound-level normalization should not alter relative gain blindly. A full song still requires bass/kick temporal/mono checks, practical dynamic control, master/limiter readback and transparent measurement to make a near-finished level target plausible. The previously approved house reference is a *product-quality aspiration*, not an instruction to keep changing that one file.

**Known limitation:** A subjective review cannot be made through the current remote terminal, and the user should never be told that their own ears have been replaced by LUFS/FFT calculations. Deliver finished candidates into chat before requesting a final listening judgment.
