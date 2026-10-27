# Phase25 — source-first production refinement

Base `f730da16f4396c614eeb7bc33a32d4176247bb84`. The user heard the Phase24
record as first full-song viability, with occasional awkward rhythm and an
early-house sonic character. They asked for one substantial production pass
with no melody, new song, drum kit, shortlist or mastering-only milestone.
Earlier releases/docs remain immutable; new listening preference is unreviewed.

The opt-in `production_refinement.py` keeps144bars,126BPM,Cminor, all8 sections,
15 tracks, six licensed sample assets and the approved bass/sub/kick sources.
No default composer, canonical0.1, SongSpec, transaction, host adapter or old
runtime/test file changes. Two source patches and existing EQ/return/lane values
supply the production change. No new insert or automation lane is added.

## Actual rhythm findings and narrow repair

The brief's8-added-ghost count was inaccurate. Phase24's collision guard skipped
four proposed later taps because original source ghosts already existed. The
actual additions are **four** p38 notes at3.277083beats, one each in zero-based
63,79,111,127. These sit about123ms after the original late clap at3.01875beats,
between the original2.789583/3.777083 source ghosts. That increases post-clap
chatter; it is a plausible trouble point, not a proven listening mistake.

Only those four newly added IDs are removed. The original later ghosts remain.
The four shifted three-note chord attacks are at2.625beats, not3.0:12 voices at
51,55,59,63 move120ticks/59.524ms earlier to the approved2.5beat pocket. The
four-tick hand-strum, pitches, gates, velocities, channels and surviving order
remain. Echo gates at55/63 follow those repairs. No hard quantization or new
rhythm is authored. Bass omissions near handoffs and the sparse rebuild are
intentional and remain unchanged. Kick presence/break lengths stay exact.

Private original-patch/FX four-bar native before/after windows cover62–66,
78–82,110–114,126–130. The preceding unaffected bar must be PCM-exact; the target
window must change. The full original501-note anchor MIDI at16–32 stays exact.
New chord/pad synthesis changes its upper AUDIO, explicitly. Its rhythm-only
reset render is independently required to remain exact.

## Source tone, role balance and real movement

All tables are original reviewed Kuang Fourier content. No downloaded preset,
factory table, new sample or pitch modulation. Both oscillators are single,
integer-tuned, same octave. Source controls use actual Vitalium1.0.6 INTERNAL
units: envelope fourth roots of seconds; filter cutoff MIDI-note units; volume
(80+dB)^2. Native EQ uses actual Hz/dB. No fake unit labels.

| Control | Phase24 | Phase25 |
|---|---|---|
| Chord amp ADSR |7ms/320ms/36%/170ms |5ms/280ms/34%/140ms |
| Chord Fourier frames |150/220 |206/96 |
| Chord filter base |92 internal MIDI units |96; stronger velocity response, shorter filter contour |
| Chord4-bar wave motion amount |.025 |.075 |
| Pad amp ADSR |750ms/2.8s/70%/1.8s |600ms/2.5s/68%/1.65s |
| Pad Fourier frames |130/190 |170/210 |
| Pad filter base |84 internal MIDI units |93 |
| Pad motion |one8-bar LFO, in-phase wave/filter routes |two real8-bar LFOs with vertically inverse original triangle shapes and complementary wave/filter routes |
| Chord role EQ |HPF100Hz,300Hz+.5dB |HPF floor140Hz,330Hz−1.25dB |
| Pad role EQ |HPF180Hz,450Hz0dB |HPF220Hz,450Hz−1.75dB |
| Pad native LPF |1–4kHz arc |same anchor arc; selectively opens to7.2kHz elsewhere |
| Dark plate |32ms predelay,450Hz lowcut |42ms,600Hz; same2.7s decay/recovered return level |

Actual plugin parameter-text probing verifies LFO2 Sync1/SyncType1/Tempo3=8/1;
its second shape and all modulation routes must survive actual saved component
readback and two-instance restoration. The motion-only bypass retains filter
and velocity envelopes: it disconnects ONLY slow LFO routes. No oscillator LFO
or ADSR automation claim is made for the builtin SoundCraft synth.

Pre-insert same-MIDI calibration restores the old instrument INPUT level before
judging the role EQ. The synth output's reviewed upper bound0dB is respected;
the pad's remaining2.283695dB correction uses real flat EQ input gain. The
initial out-of-range calibration was rejected, not silently accepted. Final
native pre-insert LUFS must match within.01LU. Full listening A/B uses constant
attenuation only and must match within.001LU. This prevents gain being presented
as a source quality improvement.

The dry pad already has scheduled beat ducking. The extra wet-return duck is
halved, preserving recovered levels and the calm kick-free break. This opens
space without a blanket wet-level increase. The dark return filters keep its
low midrange separate from the bass. Seven unchanged rhythm strips and all
bass event fields remain exact; only the four explicit p38 removals alter the
original percussion track. No input-triggered detector routing is claimed.

## Native master gate and proof boundary

Compressor, saturator and maximizer are physically probed on the actual terminal
stereo bus, with same-input controls, compressor envelope gain measurements and
save/reopen PCM equality. These optional probes do not enter the final record.
The final terminal retains its original transparent−6dB capture trim and zero
inserts. No consumer-master variant or arbitrary LUFS target.

Actual new-patch notes/chords are tested in SoundCraft and an independent
Vitalium host, with neutral synthetic MIDI pitch-bend.5. Source/body spectra,
matched-level source changes, motion on/off, wet-only return envelopes, raw
full PCM, source preservation and relocated replay are measured. These are
causal/integrity tests, not professional-quality or rhythm-preference scores.

Mandatory offline discovery: **568 methods,477 executed successfully,91 optional-host skips**, zero failures/errors (1189.535s). **Six new actual native production methods + four existing primary real-adapter methods pass**, zero skips. Thirteen focused unit methods and installed-wheel smoke pass. All **549 earlier test methods/files** and **12,495 historical files** remain exact. Current/installed/frozen runtime: **74 files exact**. Older native experiment suites were not regenerated.

The production has **3,800 notes**: four explicit extra ghosts removed,12 chord voice onsets repaired, all other surviving note fields/IDs/order exact. The501-note anchor MIDI and rhythm-only reset PCM remain exact; new upper synthesis changes its AUDIO. Native save/reopen and extracted relocated replay preserve complete native state and raw/matched B PCM. All original sample assets and bass source remain exact.

Actual pre-insert level errors: chord **-0.000056LU**, pad **-0.000380LU**. Same-MIDI equal-LUFS source deltas are **0.2651 chord / 0.2081 pad** relative RMS. Slow-LFO-only bypass differences are **0.0673/0.0724**. Wet-only return gets **2.302dB** less post-kick attenuation, recovered-level difference **0.000dB**. Four original-patch rhythm QA prefixes are PCM-exact. These are causal changes, not preference scores.

Real two-host tuning: maximum single-note **0.2034cents**, chord partial **0.3086cents**, below5cents. The bounded native terminal compressor/saturator/maximizer probes pass processing/state/reopen gates; final terminal still has zero inserts.

Both full279.285708s48k/24bit stereo recordings are unclipped. Raw A/B measure **-31.898/-32.812LUFS**; matched copies **-32.912462/-32.912462LUFS**, constant attenuation only. Raw B true peak **-8.660dBTP**, crest **26.435dB**, mono RMS loss **-0.093dB**, sampled low-band mono retention **99.9992%**. High-band side/mid ratio **0.04601** is lower than Phase24, so no numerical width improvement is claimed. No master or commercial loudness target.

ZIP **139,806,751bytes**, SHA256 **`9d23d15599f44a6f02c84b4e11b43146afbd7e118aec91b86295824451aa548a`**. [Machine verification](PHASE25_VERIFICATION.json). Exact commit/post-push Python3.11/3.13 CI evidence is in artifact `proof/release-summary.json`. Listening verdict remains unreviewed.

One ZIP: `artifacts/phase25-house/phase25-house-listening.zip`, TWO complete
matched A/B songs and the editable native B/canonical/MIDI, patches, relative
licensed media, source/journal/recipe, licenses and frozen MIT replay. Raw B is
also available separately in the artifact directory. No stems homework.
[Listening and replay instructions](PHASE25_LISTENING_README.md).

```bash
python3 tools/phase25_house.py build --out-dir .local/phase25/my-production \
  --patches /absolute/path/to/prepared/phase25-patches \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3 \
  --host-python /absolute/path/to/separate/plugin-host/python
```

Only pinned Linux SoundCraft0.11.0/Vitalium1.0.6 are verified. Official Vital,
other builds/channels and GUI/cross-platform behavior remain unverified. The
optional GPL plugin/test host are separately installed; core remains MIT and
stdlib only. Dry release audits do not transcribe FX tails or establish artistic
consonance. Human listening decides whether this production step is preferred.
