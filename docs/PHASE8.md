# Phase 8: production gestures on the same house song

Implemented from clean main `e2a6dda`, following the user's Phase 7 audition. The result is an opt-in native production experiment over the **same 64-bar, C-minor, 126 BPM song**. No new composition generator, plugins, samples, models, services, dependencies or schema migration. The earlier composers, adapters, transactions, fixtures, tests and artifact trees remain unchanged. Original Kuang code/music remains MIT.

`kuang/gestures.py` accepts only the exact Phase 7 canonical fingerprint `6e22ce487c5fd3453b8d26d4e8387e1238284248fa7335a9dfc3528e68e3f88a`. It constructs ordinary schema **0.1** objects and existing native automation. SongSpec **1** stays the unmodified 16-bar source provenance; the separate arrangement document remains 64 bars. Source drift, changed locks and unsupported control types fail closed.

## What changed musically

Every kick, bass and main-hook note/clip ID, timing, duration, velocity and pitch remains exact across the whole song. The **entire original drop MIDI at bars 33–48 remains exact on all tracks**. Kick/bass instruments, effects, mixer and existing bass automation are also unchanged. The only MIDI deviations are five removed percussion notes in the final beat before bar 33: clap `song-snare-07-003`, snare pickups `song-snare-pickup-7-2/3`, hat `song-hats-07-015`, tick `song-percussion-07-003`. Their complete original fields and absolute ticks are recorded in canonical metadata and verification JSON. Reverb/echo releases continue through that pause; it is not a forced digital-silence edit.

The six-section form remains Intro 1–8, Groove 9–16, Build 17–24, Breakdown 25–32, Main Drop 33–48, DJ Outro 49–64. Musical development comes from repeated closure/opening gestures, frequency subtraction before the drop, alternating phrase-ending echo responses and the contrast between freely sustained breakdown pads and rhythmically ducked drop pads. There is no extra stack of new instruments.

| Native control | Phase 7 | Phase 8 |
| --- | --- | --- |
| Harmonic/percussion EQ LPF | Mostly 2–16 kHz, default 12 dB/oct | Static **24 dB/oct**; intro 1→12 kHz; build 1.6→12 kHz; breakdown 1.1–2.8 kHz; final closure 1.1 kHz, **14 kHz on drop beat one**; phrase dips at bars 40/48 |
| Stab/call/answer and clap HPF | Fixed 280/220 Hz | **24 dB/oct**, build 280/220→400→600→**1000 Hz**, late-break rise, reset to 280/220 Hz at drop; kick/sub excluded |
| Lead/answer delay | Dotted eighth 357.143 ms, wet .13→.26 on mostly empty last beats, feedback .22 | Lead **357.143 ms dotted eighth**, answer **238.095 ms eighth**, feedback **.46**, filter 6.5 kHz, modulation depth zero; wet **.035→.48**, **.58** in late breakdown, aligned to last actual note of each two-bar call/response, held for echoes and faded |
| Lead/answer reverb | Short room/1.45 s plate and modest wet variation | **3.2 s**, 48 ms predelay, 500 Hz lowcut, width .8; wet .58–.66 in breakdown, **.10 on drop** |
| Pad plates | 2.8/2.4 s, wet ~.34–.48 | **3.4 s**, 42 ms predelay, 650 Hz lowcut, width .8; wet **.60–.64 breakdown**, **.22 drop** |
| Pad/harmony beat gain | Pad 3 dB breath, stab 4 dB duck | **11 dB pad / 7 dB stab** programmed duck; hold ~45 ms, curved-by-linear-points release to base at ~337 ms; **disabled during breakdown** |

The cutoff reset ramps during the final 12 ticks (~5.95 ms) before beat one and reaches its reset value exactly at the drop, avoiding a mathematical step. Base pad faders **-2/-4 dB**, instrument trims, oscillators, static ADSRs and gentle modulation remain Phase 7's corrected values. No louder-pad compensation or master limiting. Native mix controls, not hidden waveform processing, produce the candidate. Constant PCM attenuation is used only for the clearly labelled RMS-matched audition copies.

## Pinned capability boundary

SoundCraft **0.11.0**, installed executable SHA-256 `84466d199a6cb4d4924a9179fdf36b0c6d1ab3a0082b60ceed50d06f09f0b130`, adapter discovery/contract `5af7ed8eed0e51a251da6dee6f57a9b83ac6ae004c70b13a96416cdee4ad49f7`. The captured actual `engine.plugins` catalog is `.local/soundcraft-plugin-catalog.txt`; runtime discovery validates the selected executable again.

| Operation | Discovered native types/ranges | Mapping and limit |
| --- | --- | --- |
| EQ7 HPF/LPF | HPF **10–2000 Hz**, LPF **1000–20000 Hz**; cutoff Log taper, continuous Hz | Canonical `soundcraft.hpf_freq/lpf_freq`, linear interpolation in legitimate Hz; static toggles already enabled |
| EQ slopes | Choice integer 0/1/2/3 = 6/12/18/24 dB/oct | New registry entries normalized 0..1; **1 maps to integer 3**; never automated or fractionally selected |
| Mod delay | Time 1–2000 ms; feedback ±99%; mix/depth 0–100%; LPF 500–20000 Hz | Existing ms/normalized mappings; tempo converted explicitly to ms, not a claimed host tempo-sync mode |
| Plate/room | Decay .1–20 s; mix/width %, lowcut 20–1000 Hz, predelay 0–250 ms | Canonical decay_ms converts milliseconds→native seconds; wet/width ×100 |
| Mixer volume | Existing native dB lane, canonical -90..12 dB | **Programmed tempo-synced gain ducking, not input-triggered sidechain**; post-insert mixer also ducks tails |
| Chorus/phaser | Native rate/depth/mix/spread, existing mappings | Existing gentle modulation preserved; an isolated on/off native control measures its output |
| Compressor | Existing threshold/attack/release/makeup; native default ratio 4:1 | Existing local stab compression retained; diagnostic makeup zero in both active/bypass inputs proves changing gain reduction; no ratio/Q unit invention |

There is no verified send bus or external kick-input sidechain path in Kuang's adapter. A compressor's internal detector HPF is not external routing. No oscillator LFO/wavetable/matrix or direct ADSR automation. Continuous native FX/mixer lanes and static instrument controls remain fully editable. Both native stereo panners follow canonical pan; width therefore remains modest. Surge's earlier silent renders are not retried.

## Actual audio evidence

Candidate canonical fingerprint: **`22a3d95c5479dbdd312db6aefe803e0e600ba7ecd62350060c2e1880759ca2a7`**. Independent release/test builds have identical hashes for **22** canonical/MIDI/full/matched/context/control files.

Full fresh Phase 7 and Phase 8 renders: **48 kHz, stereo 24-bit PCM**, **6,091,429 frames / 126.9047708 s**, comprising exactly 64 bars (**121.9047619 s**) plus five seconds of tail. Phase 7 rerender equals the historical full WAV **byte for byte**. Native export checks every MIDI field, all inserts/parameters, every converted automation point and six section markers, followed by full save/reopen comparison. Independent integration additionally rerenders the saved session and requires identical full PCM hashes.

| Full native render | Phase 7 | Phase 8 |
| --- | --- | --- |
| Peak dBFS | -6.795137 | -5.495356 |
| RMS dBFS | -27.012844 | -27.075596 |
| Crest dB | 20.217707 | 21.580240 |
| Clipped samples | 0 | 0 |
| Breakdown RMS dBFS | -34.989899 | -36.705758 |
| Main drop RMS dBFS | -25.477961 | -25.436518 |

Equal-RMS full pair: **-27.075596 dBFS**, A attenuated **0.062752 dB**, B unchanged. This is whole-file RMS, not LUFS/perceptual matching. The candidate is not made louder at average level. Intro/build/breakdown/drop/outro still have distinct native notes and measured energy; the breakdown/drop difference is **11.269241 dB**.

The controls are fresh short native sessions, with identical MIDI/ADSR/pan and unaffected FX/automation inside each pair. Their DSP state resets at the window start; they are labelled diagnostics, not exact running-full-bounce excerpts. `C/D/E` listening excerpts, separately, are exact slices of the full candidate PCM.

| Same-input diagnostic | Measured result |
| --- | --- |
| Eight-bar build HPF vs 10 Hz static-open control | Late-build **120–500 Hz power -24.259255 dB** |
| Eight-bar build LPF vs 20 kHz static-open control | Early-build **2–8 kHz power -10.916094 dB**, late-build **-0.058572 dB** |
| Single existing phrase-ending lead note, throw vs dry | Three real post-note echo windows RMS **.00500478 / .00155452 / .000081114**, dry **digital zero**; measured envelope-peak spacing **357.145833 / 357.145833 ms** (configured **357.142857 ms**) |
| Drop pad/stab pump vs duck off | Postkick **-10.280329 dB**, recovery **-4.677142 dB**, open phase **-0.000033 dB** same-input energy ratio |
| Breakdown pad reverb vs wet zero | Aligned difference RMS **-37.321952 dBFS**, **127.48%** of wet-stem RMS; released-tail RMS **-76.423760** vs **-115.031250 dBFS** 1.5–2.5 s after note-off; both synth releases unchanged |
| Native chorus/phaser vs wet zero | Aligned difference **-39.411042 dBFS**, **56.30%** of modulated-pad RMS |
| Existing stab compressor, active vs bypass, makeup zero in both | Peak **-7.925020 dB**, RMS **-8.181709 dB**; 20 ms active-window gain varies **-9.669929..0 dB**, excluding input below -80 dBFS |

Spectral results use **absolute** window-power-normalized 4096-frame Hann mean squares, both channels, up to 32 windows per local region (11.71875 Hz bins). They are not just relative band fractions or preset values. The echo probe has other spatial FX dry and retains one original note. Measured peaks use a 20 ms RMS envelope with 2 ms search hop; spacing must be within 10 ms of the tempo value. These tests establish actual DSP action, not listener preference. Wet/dry difference includes both wet signal and wet/dry crossfade; it is not a reverb loudness score.

Full stereo correlation **0.984585**. Phase 8 >500 Hz side/mid power **0.02646435** (Phase 7 **0.02578426**), high-band mono energy retention **97.4218%**, low 20–120 Hz retention **99.999996%**, mono RMS loss **0.034246 dB**. Final 250 ms are digitally silent, mono sum unclipped. Width changed only slightly; no dramatic stereo improvement is claimed. Detailed correlation, absolute band powers, region levels, timestamps, source inventories, exact note deviations and file hashes are in the release `verification.json` and [PHASE8_VERIFICATION.json](PHASE8_VERIFICATION.json).

## Listen, edit and reproduce

One download: **`artifacts/phase8-house/phase8-house-listening.zip`**. It includes matched full A/B; eight-bar build, breakdown/drop and call-response context excerpts; short filter/delay/reverb/pump/modulation/compressor control pairs; complete editable candidate canonical/MIDI/native bundle and baseline native/canonical snapshot; levels, DSP report, README and MIT license. No lossy audio or external binaries/assets. All controls also have editable sessions.

```bash
scp YOUR_HOST:/home/User/Kuang/artifacts/phase8-house/phase8-house-listening.zip .
```

Open `editable-phase8/native/session.scraft` after extraction with installed SoundCraft 0.11.0, keeping companion files together. Raw full WAVs remain `A-phase7-original-64bars.wav` and `B-phase8-motion-64bars.wav`; matched pair is under `listening/`; candidate session is `native/session.scraft`. No hidden audio processing is needed to reproduce B.

```bash
mkdir -p .local/phase8/tmp
export TMPDIR="$PWD/.local/phase8/tmp"
python3 tools/phase8_house.py --symbolic --out-dir .local/phase8/my-symbolic
python3 tools/phase8_house.py --source artifacts/phase7-house/song \
  --soundcraft /absolute/path/to/soundcraft-cli --out-dir artifacts/my-phase8
python3 tools/phase8_house.py --package --out-dir artifacts/my-phase8

KUANG_SOUNDCRAFT_INTEGRATION=1 \
KUANG_SOUNDCRAFT=/absolute/path/to/soundcraft-cli \
KUANG_SOUNDCRAFT_ARTIFACTS="$PWD/.local/phase8/new-integration/real-host" \
python3 -m unittest discover -s tests -v
```

Use fresh paths. Native failures/source drift/negligible **measured DSP action** publish nothing; symbolic builds explicitly report no audio/native verification. ZIP creation verifies all recorded asset hashes, CRC and exclusive creation. Full integration staging stays in `.local/phase8/` because the unchanged legacy Phase 6 harness protects other artifact directories; completed proofs can be moved to the release after all tests finish. Logs/scratch/build/install stay project-local.

Final suite, preservation, deterministic-repeat, wheel-install and remote Python 3.11/3.13 checks are recorded in STATUS and the machine-readable verification. The agent has no human listening result for this candidate. Basic subtractive/drum timbres, simple original harmony and linked stereo panners remain limits. There is no professional/club-ready, LUFS, true-peak or perceptual crackle-free certification.
