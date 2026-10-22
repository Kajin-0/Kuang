# Phase 6 — sonic depth over the exact house pocket

This experiment responds to the user's Phase 5 audition: the groove improved, but lacked sustained pads, audible space, modulation and width. It extends the existing **16-bar, 126 BPM C-minor** loop. It does not replace its melody or rhythm. The new candidate has not been human-auditioned in this development run; club suitability and listener preference remain unknown.

## Preservation and musical decisions

`kuang/depth.py` accepts only the released Phase 5 seed-29 canonical fingerprint, `3fe734a568b0d715890a382159fcacea58a1c770b8b50d0dda8bbeb3e6c0d311`. It copies that source and retains **all 488 original notes**, including IDs, clip placement/order, pitch, duration, velocity and channel. Kick and bass tracks are entirely unchanged, including synthesis, insert chains, gain/pan and bass ducking. All original automation lanes, sections and SongSpec provenance remain exact. A fresh Phase 5 bounce equals every historical PCM frame; both new full-file bounces include the same additional tail allowance.

The added body is a sustained, rootless **Cm9 → Fm9** pad above the bass register. Cm voicings contain Eb/Bb/D, with G added in denser phrases; Fm voicings contain Eb/Ab/G, with C in denser phrases. The high texture answers with D/G/Bb and Eb/G/C. Four-bar densities differ deliberately: body 9/12/9/12 notes, air 2/4/6/6. All pitches belong to C natural minor. Slow notes and rests expose the existing hook rather than add another busy motif. There are **60 added notes**, 548 total.

The main synth uses triangle/saw at 34% oscillator mix, amp ADSR **650 ms / 950 ms / 70% / 1000 ms**, filter envelope **1100 / 1600 / 55% / 1000 ms**. Air uses saw/triangle at 24%, amp **260 / 600 / 38% / 650 ms**, filter **450 / 1200 / 42% / 650 ms**. These are separate native instruments with static envelopes, not automated synth parameters. Main/air highpasses are **400/1000 Hz**, pans **-0.58/+0.62**; gentle native beat gain lanes give them space around attacks.

Existing inserts stay in order. Only the stab room's wet/decay/predelay change: **8→22%, 550→1250 ms, 12→22 ms**. A **20%**, 1450 ms plate follows the existing lead chain, with 28 ms predelay and 500 Hz lowcut. No original MIDI or other original mix scalar changes.

## Actual native capabilities used

The existing catalog and real CLI capability validation pin SoundCraft **0.11.0**. Binary SHA-256: `84466d199a6cb4d4924a9179fdf36b0c6d1ab3a0082b60ceed50d06f09f0b130`. Existing discovery/contract pin is preserved. The small new phaser fixture records actual parameter descriptors, not DSP code.

| Device/control | Native contract | This experiment |
| --- | --- | --- |
| Subtractive synth | Saw/Square/Sine/Triangle integer choices; amp/filter ADSR in ms and percent | Two different editable sustained voices; normalized choices map to integer selectors |
| Chorus | Rate 0.05–5 Hz, depth/spread/mix 0–100% | Body 0.32 Hz / 65% depth / 40% wet; air 0.63 Hz / 58% / 44%; both spread 100% |
| Phaser | Rate 0.02–5 Hz, depth/mix 0–100%, center 100–4000 Hz, feedback ±95% | Body 0.126 Hz, 72% depth, 950 Hz center, 28% feedback, 38% wet; default six stages |
| EQ LPF | On/off plus continuous **1000–20000 Hz** | Native linear lanes: body 1200–6500 Hz; air 2400–14000 Hz, repeated opening/closing gestures with phrase variation |
| Plate | Mix/width percent, decay 0.1–20 seconds, predelay ms, lowcut/damping Hz | Body 28% / 1800 ms / 38 ms; air 24% / 1300 ms / 32 ms; width 100%, lowcuts 500/650 Hz |
| Mixer | Native gain lanes and linked stereo pan mapping | Centred unchanged kick/bass; distinct harmonic track pans; measured stereo rather than assumed spread |

Canonical `soundcraft.decay_ms` converts to native seconds. Percent controls remain normalized canonically, and Hz/ms keep their real units. Phaser center adds a legitimate Hz registry entry; no schema migration or unit relabelling. Continuous native FX/mixer lanes, point IDs and values persist through save/reopen and scoped edits.

There is **no exposed synth oscillator LFO, wavetable matrix or supported ADSR automation**. Chorus/phaser have their own real modulation; moving EQ is insert-filter automation. This is not an oscillator LFO substitute in every synthesis sense. Stereo delay/pan-mode support was not invented. SoundCraft's existing adapter links both native stereo panners, which limits preservation of intrinsic effect spread; opposite harmonic-track positions provide useful measured width. No adapter contract or host JSON was changed to manufacture support.

Surge was **not retried**. Phase 5's discovered CLAP/VST3 instruments rendered silence; no new specific fix was established. No downloads, paid services, models, samples or third-party presets/plugins are required or bundled. Original code/music remains MIT, runtime stdlib-only.

## Listening files and reproducibility

The release is **`artifacts/phase6-house/`**:

- `A-phase5-unchanged.wav`, `B-phase6-depth.wav`: native 48 kHz, stereo, 24-bit PCM, **34.4761875 s** each: 16 bars plus four seconds of tail, sample-zero alignment.
- `listening/A-phase5-unchanged-matched.wav`, `listening/B-phase6-depth-matched.wav`: full-file RMS matched by constant attenuation only. Both measure **-26.267258 dBFS RMS**; B gain **-1.142111 dB**, A unchanged. This is not LUFS matching.
- `listening/*-bars9-12.wav`: corresponding four-bar highlights using the same gains, no extra normalization/crossfade. They are excerpts, not certified seamless loops.
- `native/session.scraft`, companion manifest/canonical snapshot; `saved-native/` full-state verified reopen; top-level canonical, SongSpec and MIDI.
- `stems/`: independently rendered kick, bass, other drums, original music, body, air and combined pads, with editable native bundles. `controls/`: same-input reverb dry, modulation depth zero and static-filter native/audio controls.
- `verification.json`: source/asset hashes, exact note fingerprints, full PCM/section/band/spatial metrics, control deltas, capabilities and ZIP inventory. `proof/` holds independent real-host tests, release measurements and build/install evidence.
- **`phase6-house-listening.zip`**: matched full A/B, both highlights, levels/readme and complete editable candidate native/canonical/MIDI/license. ZIP integrity and embedded native bytes are independently checked; no external binaries or references.

Download in one command, substituting your server account:

```bash
scp USER@HOST:/home/User/Kuang/artifacts/phase6-house/phase6-house-listening.zip .
```

Open `editable/native/session.scraft` from the ZIP in SoundCraft 0.11.0; keep its manifest and snapshot together. Every note, native ADSR, insert and lane remains editable. Manual host changes are not automatically reconciled into canonical state.

Reproduce from the checkout, with a new output directory:

```bash
python3 tools/phase6_house.py --source artifacts/phase5-house \
  --out-dir artifacts/phase6-house-reproduction \
  --soundcraft /absolute/path/to/soundcraft-cli
python3 tools/phase6_house.py --symbolic --out-dir artifacts/phase6-house-symbolic
```

Native proof requires the unchanged Phase 5 source directory and its original `candidate.wav`. Symbolic mode can regenerate the fingerprinted source internally and produces no false audio/native success. Output publication stages under `.local/phase6/`, reserves a new destination, rejects existing/racing paths and cleans failed private staging. Historical files are inventoried before/after. No overwrite option exists.

## Measurements and what they establish

| Full native render | Phase 5 unchanged | Phase 6 depth |
| --- | ---: | ---: |
| Peak dBFS | -6.653822 | -6.369014 |
| RMS dBFS, including four-second tail | -26.267258 | -25.125147 |
| Crest dB | 19.613435 | 18.756133 |
| Clipped samples | 0 | 0 |
| Stereo correlation | 0.994165 | 0.930405 |
| >500 Hz side/mid power ratio | 0.010956 | 0.096209 |
| >500 Hz mono energy retained | 98.9163% | 91.2234% |
| 20–120 Hz mono energy retained | 99.99934% | 99.99941% |
| Full mono-sum RMS loss | -0.012949 dB | -0.166116 dB |
| Estimated band fraction 20–120 Hz | 71.8195% | 56.9197% |
| Estimated band fraction 500–2000 Hz | 6.7712% | 18.7337% |

The changed duration/tail and sampling windows mean these full-file RMS/band figures differ from Phase 5's historical one-second-tail report. The actual baseline PCM prefix is identical. Sampled band estimates use the existing 64 × 2048 Hann-window stereo-power method. Frequency-resolved mid/side uses up to 96 × 4096 Hann FFTs, **11.71875 Hz** bins, `M=(L+R)/2`, `S=(L-R)/2`. Mono retention is `E_M/(E_M+E_S)` in each band. These are sampled diagnostics, not perceptual scoring, phase alignment, LUFS or intersample true peak.

Body/air/combined-pad RMS: **-31.9581/-39.5118/-31.2209 dBFS**; unchanged kick/bass **-28.7996/-32.5976 dBFS**. Body is roughly 3.2 dB below the kick RMS. Independent stems recombine within **3 24-bit LSB**, delta RMS **-141.7254 dBFS**. Kick and bass stems have exactly zero side energy. The final 250 ms of both full renders is digitally silent. Isolated pad RMS after its last note is **-38.8934 dBFS** (30.02–30.25 s), and after the arrangement end **-63.9817 dBFS** (30.526–30.876 s): release/tails exist and are not chopped at the song boundary.

Controls retain identical note fingerprints and instrument parameters:

| Same-input change | Whole-context delta RMS | Isolated pads delta RMS / ratio to wet pads |
| --- | ---: | ---: |
| Reverb wet → 0 on new pads/lead and changed stab room | -38.0185 dBFS | -38.2427 dBFS / 44.56% |
| New chorus/phaser **depth → 0**, same wet mix and rate | -29.5499 dBFS | -29.5499 dBFS / 121.21% |
| New LPF lanes held constant at 4000/9000 Hz | — | -49.8436 dBFS / 11.72% |

Whole-context reverb/modulation difference is **22.66%/60.08%** of candidate RMS. These nontrivial, deterministic PCM differences establish active DSP and movement from the same MIDI input. They do not prove pleasantness or perceived loudness. Modulation-depth zero retains the effect's static delayed/allpass component; it is a stronger movement control than merely removing the entire insert. No hidden render mastering or waveform-only replacement is used.

## Verification and remaining limits

The full suite retains all **180 earlier methods** and adds **14** focused checks: exact groove preservation/source drift, diatonic ninth voicings/register/density, contrasting ADSRs, real parameter bounds, movement lanes, same-input controls, deterministic canonical/MIDI, staging/races/no-clobber/failure cleanup, known mono/antiphase analysis, and independent real native note/FX/lane/save/reopen/audio/ZIP/scoped-edit checks. See [STATUS.md](STATUS.md) and [machine-readable release verification](PHASE6_VERIFICATION.json) for actual final results, packaging and CI evidence.

The palette is still the host's basic subtractive synth and drums; there is no new oscillator architecture, audio-triggered sidechain, master bus, LUFS/true-peak certification or independently licensed professional reference. Distinct static envelopes and native effect/filter movement address a useful subset of sonic depth. Human audition must decide whether reverb/pads balance against the hook and whether the increased movement serves the groove. No new-candidate human listening or club-readiness claim is made.
