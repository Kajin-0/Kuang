# Phase 12: an eight-bar producer experiment

The source is the **user-preferred Phase 10 D**, not the Phase 11 Vitalium sounds. This experiment stays at eight bars of its main drop: human bars **33–40**, **126 BPM, C minor**. It changes the supporting pocket and articulation while retaining the kick anchor, melodic hook, pads, pulse and sound hierarchy. A listening win is **not established** by technical validation; no full-song expansion is included.

| Variant | MIDI | Sound and mix |
| --- | --- | --- |
| A — frozen Phase 10 source | Original 296 selected notes | Original instruments, inserts, mixer and cropped automation |
| B — groove only | 186 explicit edits to existing notes | Exactly A, including every automation point |
| C — sound only | Every A note/clip field and MIDI byte exact | Existing envelope/processing changes, calibrated native faders |
| D — combined | Exactly B | Exactly C |

All 296 note IDs, pitches, channels and track/clip membership survive. No notes, tracks or inserts are added or removed. The 32 kick notes retain their exact positions, velocities and durations. The lead, two-note answer, both pad voices and sine pulse retain their complete original tracks in every variant. Schema **0.1**, SongSpec provenance, locks, transaction semantics and legacy creation defaults are unchanged.

As in earlier exports, SoundCraft's MIDI importer merges each track's clips and sizes the native region to its last note-off using the MIDI file's integer-microsecond tempo. Groove edits can therefore change that derived native region length. Independent checks permit only this calculated extent and the exact authorized note fields; mixer, FX, automation and all other native state remain exact. Original canonical clip boundaries/IDs remain in the snapshot and manifest.

## Production reasoning and original authorship

Read the project-local `house-production-audit.md` first. The relevant research is about relationships between a few sounds, accents and envelopes. Ableton separates timing, velocity and randomization in its [Groove Pool documentation](https://www.ableton.com/en/live-manual/12/using-grooves/); here, role timing is authored directly into editable MIDI without new random perturbations. Attack's [Deep Tech House](https://www.attackmagazine.com/technique/beat-dissected/deep-tech-house/) discusses offbeat hats, short percussion articulation and velocity hierarchy. These inform the supporting accents; its beat grid and samples are not imported.

Brikha's [Ableton interview](https://www.ableton.com/en/blog/aril-brikha-remaking-groove-la-chord-with-live-and-note/) emphasizes the relationship between a chord's filter/envelope, performance and effects. That motivates a better-defined existing stab, rather than a replacement palette. The interview's downloadable sets are restricted to educational use; none is downloaded, sampled or redistributed. No reference recording, commercial preset, Suno audio, Vitalium patch or external account is used. Notes and sounds remain original Kuang material; core license remains MIT.

These sources guide decisions; they do not prescribe one universal swing, EQ curve, loudness target or definition of professional quality.

## Actual groove edits

One tick is **0.496031746 ms** at 126 BPM / 960 PPQ. `provenance.json` enumerates all 186 before/after note records, including IDs, absolute ticks and onset deltas; `event-map.json` lists every event in all variants.

| Role | Authored decision |
| --- | --- |
| Kick | All 32 anchors unchanged on the quarter-note grid |
| Main clap | Retain its existing **18-tick / 8.929 ms** late backbeat; stronger beat-two accent, quieter beat-four, stronger four-bar turnaround |
| Ghost snare | Existing ghosts only; **56 ticks / 27.778 ms** late relative to their sixteenth, velocities 30/34 |
| Offbeat hats | Open accents 8 ticks late, principal closed hats 10 ticks late; different strengths rather than identical offbeats |
| Ghost hats / ticks | Supporting sixteenths 60 ticks / **29.762 ms** late, substantially below main accents; four-bar turnaround accent |
| Bass | Preserve all pitches and positions within the motif; stronger long offbeat bodies, shorter/quieter syncopations and pickups; deliberate 8/48/60-tick role offsets |
| Chord stabs | Preserve the rootless Cm9/Fm voicings and 4-tick upward voice roll; onset 24 ticks / **11.905 ms** earlier, longer accented calls and short, quiet responses |

Bass durations become **330/115/90/285/165/85 ticks** by existing sixteenth position. Their amplitudes and native releases are considered together; the combined candidate has over **20 ms** of post-release room before the following kick, including the shortest pickup gap. This is an authored timing constraint, not a claim that an electrical oscillator phase was aligned. No uniform global shuffle is applied to the kick, hook or pads.

## Actual sound edits and level control

All changes address existing controls; no insert is added. Full numerical operations and reversible receipts are included.

| Source | Before → after |
| --- | --- |
| Kick | Native decay **280 → 225 ms**; compressor attack **8 → 12 ms**, release **75 → 65 ms**; existing high-mid emphasis **2600 Hz / +1.5 dB → 2200 Hz / +2 dB** |
| Bass | Same single saw, filter and chain; amp decay **160 → 125 ms**, sustain **.24 → .18**, release **28 → 22 ms**; cutoff **650 → 780 Hz**, filter envelope amount **.18 → .23** |
| Ghost snare / clap room | Snare decay **110 → 85 ms** affects pitch-38 ghosts. The pitch-39 clap's internal 250 ms envelope is fixed. Its room **550 → 380 ms**, predelay **12 → 8 ms**, wet **.04 → .065** |
| Hats | Closed decay **55 → 40 ms**, open **210 → 155 ms**; shorter noise wash preserves the gaps |
| Stab | Amp attack **8 → 2.5 ms**, decay **145 → 110 ms**, sustain **.04 → 0**, release **75 → 45 ms**; filter decay **125 → 95 ms**, amount **.18 → .28**, cutoff **2200 → 1800 Hz** |
| Stab processing | Existing compressor attack **.2 → 4 ms**, threshold **−32 → −27 dB**, makeup **2 → 1 dB**; room **1250 → 600 ms**, wet **.22 → .13**; chorus wet **.15 → .10** |

The initial untrimmed sound prototype lowered bass RMS about **1.49 dB** and raised stab RMS about **2.93 dB**. It was rejected as an unbalanced comparison. The chosen C/D apply explicit **native post-FX** trims: kick **+.75 dB**, bass **+1.5 dB**, clap **+.3 dB**, hats **+1.3 dB**, stabs **−2.9 dB**. Automated bass/stab base gain and every existing volume breakpoint receive the same trim; point IDs, times, shapes and programmed ducking contours remain intact. Pad, lead, answer and pulse levels are unchanged.

Same-MIDI C/A stem measurements must stay within **.25 dB active RMS**, and a least-squares gain fit must leave more than **1% residual RMS**. Thus a mere gain change cannot pass as the source/processing experiment. This is a causal waveform check, not a perceptual quality score. More sharply defined attacks can still sound louder at equal RMS; separately matched stems and the full context are supplied for judgment.

The synth changes are static native ADSRs. Existing EQ sweeps, delay throws, effect modulation, stereo positions and programmed gain ducking remain. There is no claim of oscillator LFO, audio-triggered sidechain, master bus processing or new synthesis capability.

## Frozen source versus running DSP history

A is exactly `crop(atmosphere_house(), 32, 8, all_track_ids)` with canonical SHA-256 **`0010864525aaae998a4a768ad99ab730955a22b855f4f5076c3254146d4b8e08`**. Inspection confirms **no note is actually clipped at these boundaries**: all 296 note fields remain original, with clip time origins moved back 32 bars. Automation is the original continuous window with explicit boundary values. The full Phase 10 source hash is **`dad1db280f798fdf07ab4b0243bcc6e528f680b30f32b8a5e92104a94ce640b1`**.

Each native eight-bar project starts its synth/FX from rest. A fresh standalone bounce cannot reproduce the already-running full song's reverb/voice memory at bar 33. All four comparison variants use the **same reset policy**. The separate `phase10-D-exact-historical-drop8.wav` is a byte-exact frame cut from the untouched released full D, SHA-256 **`0d4183170fedec89a14d7fb087e44735889b5da5a4b84bcc46b657d7d793012a`**. It is an archive reference, not substituted for A in the controlled comparison. Neither old source nor old audio is rewritten.

Raw native bounces contain **731,429 active frames + 384,000 tail frames**, stereo **48 kHz / 24-bit**, approximately **23.238104 s**. The musical window is exactly eight bars to sample-frame precision. Audition gain is calculated from the **first 731,429 frames only** using the Phase 9 K-weighted/gated integrated-LUFS meter, then applied as one constant attenuation to the entire WAV, including its unchanged release. Tail-inclusive readings are reported separately. No limiting, normalization boost, compression or other hidden waveform processing is applied.

## Bus/send feasibility result

**Native SoundCraft post-fader send → bus → aux reverb works** in a bounded independent prototype. It is created only through actual `mix.new_bus`, `track.new(kind=aux)`, `track.input/output`, `mix.send`, `mix.insert` and mixer commands. The prototype has a strict schema-0.1 canonical graph, exact unrelated original native state, full save/reopen equality, byte-identical repeated PCM and byte-identical dry versus muted-send PCM. Enabled-send waveform difference is about **6.37%** of the dry RMS, with a measured return tail.

This does **not** make general routing available through Kuang's production adapter. Bus/output/send mapping, scoped routing transactions, feedback rules, automation and broader lifecycle cases are not implemented there. It correctly continues to reject this graph. The prototype and gate report are separate from A/B/C/D, which retain their original insert routing; no fake parallel processing or extra bus is implied.

```bash
python3 tools/phase12_routing.py --out-dir .local/phase12/my-routing-proof \
  --soundcraft /absolute/path/to/soundcraft-cli
```

## Reproduction and listening

From the checkout, using the already installed pinned host and a **new** destination:

```bash
mkdir -p .local/phase12/tmp
export TMPDIR="$PWD/.local/phase12/tmp"
python3 tools/phase12_house.py --out-dir .local/phase12/reproduction \
  --source artifacts/phase10-house \
  --soundcraft /home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli
```

Optionally pass `--meter-library /project/local/libebur128.so` for the existing reviewed MIT reference meter; the default is the validated stdlib meter. Neither route downloads anything. `--symbolic --out-dir .local/phase12/symbolic` produces all four canonical/MIDI variants without the host or historical audio assets. The new profile functions are also available from the installed wheel as `kuang.pocket_production.experiment()`; normal `create` is unchanged.

The release is **`artifacts/phase12-house/phase12-house-listening.zip`**. Start with `listening/A..D`; these four have matched active integrated loudness. Diagnostic A/D stems are separately matched by role. Every letter includes editable canonical/MIDI plus `native/session.scraft`, snapshot and identity manifest. Open the native session in the separately installed SoundCraft editor. Audition attenuation is external and labelled; native mix levels are those of the raw source project. Source notes/presets remain editable, rather than frozen audio clips.

```powershell
scp User@YOUR_VPS:/home/User/Kuang/artifacts/phase12-house/phase12-house-listening.zip .
```

## Verification and limits

Measured raw results over the eight active bars (peak includes the natural release):

| Variant | Integrated LUFS | Active RMS dBFS | Active crest dB | True peak dBTP |
| --- | ---: | ---: | ---: | ---: |
| A | −23.8129 | −25.3574 | 21.4545 | −3.8867 |
| B | −23.8146 | −25.3810 | 21.4781 | −3.8867 |
| C | −23.7599 | −25.3701 | 22.0489 | −3.3051 |
| D | −23.7605 | −25.3890 | 22.0678 | −3.3051 |

All four listening copies measure **−23.8145743 LUFS** on the aligned active window, error below **.001 LU**; only attenuation is used. All raw mixes/stems are non-silent, have zero clipped samples, and the final 250 ms of the release is digital zero. Independent six-part native stem sums differ from their mix by at most **3 24-bit LSB**.

At essentially unchanged active RMS, A→D kick onset mean-square energy changes **.0223106 → .0252803** in 0–20 ms, **.00377006 → .00307789** in 20–100 ms and **.0000638267 → .0000198832** in 100–220 ms: a more front-loaded envelope, not a sub boost. Sampled absolute bass **100–400 Hz** power stays **.000218388 → .000218330**. The stab's onset-to-late-window energy ratio rises **31.90 → 43.07 dB** while its active stem RMS is about **.28 dB lower** in D; this describes shorter articulation, not better music. The clap's relative tail remains almost unchanged, a limitation of the fixed native clap voice.

Active high-band (>500 Hz) side/(mid+side) energy is **6.5623% / 6.4873% / 6.6789% / 6.5558%** for A/B/C/D using the sampled 16384-frame analysis. Width is effectively maintained; no widening achievement is claimed. A/D low-band mono retention is **99.9978% / 99.99994%**, full-bounce mono RMS loss **.0912 / .0882 dB**, active stereo correlation **.9590 / .9603**. The descriptive kick/bass 20–120 Hz interference changes **+.0160 → −.00029 dB**, with no material low-end cancellation. The report distinguishes full-tail spatial sampling from active-window band sampling.

`verification.json` contains full native save/reopen and PCM proof for all four variants, independent six-part stem summation, kick/bass interference diagnostics, absolute/fractional band powers, actual MIDI-onset attack/body/tail windows, full crest/RMS/peak, mono sum and frequency-resolved mid/side measurements. `provenance.json`, `receipts.json`, `event-map.json` and the artifact hash inventory accompany it. The compact committed [verification summary](PHASE12_VERIFICATION.json) records final measurements/checks; [STATUS](STATUS.md) records the final test and CI outcome.

The meter is not formally EBU certified. Sampled FFT energies do not establish perceived bass weight, groove, depth or professional quality. The basic native drum/synth palette and existing eight-bar motif still impose limits. No GUI/listening claim is made. The user must decide whether B, C or D improves on A; a null or negative listening result remains valid evidence. No new full 64-bar arrangement is shipped in this milestone.
