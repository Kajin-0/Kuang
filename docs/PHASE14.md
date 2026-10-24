# Phase14 — an authored full-song ensemble and real shared production paths

Baseline **7e50935bbf8c694418861b68b33c59bbdae37b11**. The user heard Phase13:
its kick was substantially better, while the rest remained too similar and
amateur. This proposal addresses the bass, stabs, hook and pad **together in
the complete preferred song**. It is a new production direction for listening,
not a claimed professional result or a meter-driven promotion.

The full **64 bars /126 BPM /C minor /six sections** remain. Phase13's six
licensed live sampler drums stay, including their original sample identities,
triggers, velocity, timing, envelopes and per-role trims. Bass and main-call
MIDI also remain exact. All1536 original note IDs survive;54 stab note records
have explicitly listed upper-voice/velocity edits, and eight response pickups
are added. Original SongSpec is retained as provenance, not silently rewritten.

## Listen to the complete record

`artifacts/phase14-house/phase14-house-listening.zip` contains exactly two
complete **48k/24bit stereo PCM** listening files:

- `listening/A-Phase13-original-full-LUFS-matched.wav`
- `listening/B-Phase14-ensemble-full-LUFS-matched.wav`

Both are **126.9047708s**, including the same five-second settled release.
Both measure **−25.0623993 integrated LUFS**. A receives0dB; B receives only
**−.3218003dB** constant attenuation. No added master, limiter, EQ, audio shift
or reference recording is hidden in the audition. Adjust playback volume for
both together. Raw native mixes remain at the artifact root; fresh A is
byte-identical to Phase13 B. Internal stems/controls are excluded from the ZIP.

```powershell
scp User@YOUR_VPS:/home/User/Kuang/artifacts/phase14-house/phase14-house-listening.zip .
```

B remains **unreviewed**. Neither PCM difference nor the synth brand proves
better musical taste, studio quality, club readiness or a match to Suno.
The user's different3:36 vocal reference is not copied, included or used as
an ideal LUFS/spectral target. No external model/service/download was used.

## Coordinated source decisions

The [production audit](PRODUCER_ARCHITECTURE.md#what-professional-practice-changes-in-the-design)
prioritizes articulation, role hierarchy, performed tone and shared depth.
[Ableton's Brikha interview](https://www.ableton.com/en/blog/aril-brikha-remaking-groove-la-chord-with-live-and-note/)
informs the chord-envelope/filter/shared-return approach; none of its audio,
MIDI, samples or presets are reused. [Groove Pool](https://www.ableton.com/en/live-manual/12/using-grooves/)
and [Attack's house dissection](https://www.attackmagazine.com/technique/beat-dissected/deep-tech-house/)
inform the already preferred role-specific pocket. This phase preserves that
pocket rather than adding random microtiming or redoing the arrangement.

Four original, deliberately distinct **DISTRHO Vitalium1.0.6** designs replace
four built-in voices. This is the already verified optional GPL synth,
**not official Vital**, a downloaded factory preset, or Phase11's generic
three-patch bulk replacement. The only waveframes are Kuang's original
Fourier sine/soft-triangle/saw formulas; the unused sample field is zeroed.
All internal reverb/delay/chorus are disabled, so shared native returns supply
the depth. Real independent plugin readback restores each setting, all771
mapped controls, wavetable/LFO shape, component payload and second-instance
preset state before export. No plugin implementation/binary is bundled.

| Role | Concrete production decision | Real amp envelope A/D/S/R | Native balance against previous role, first8 drop bars |
| --- | --- | --- | ---: |
| Bass | One centered saw voice plus quieter same-octave sine; fixed phase, short filter envelope and release; retained native EQ/saturation and timed ducking | 3ms /160ms /.32 /25ms | −.0203dB RMS |
| Stabs | Short articulated saw/triangle chord body; modest3-voice detune; restore lower chord fundamentals and perform phrase tone | 1.8ms /230ms /.18 /90ms | +2.9871dB RMS |
| Main call | Separate2-voice softer-wave hook with quiet octave harmonic; shorter release, restrained shared space | 2ms /190ms /.22 /65ms | +.0774dB RMS |
| Pad | Restrained3+2 voice texture, gentle real internal LFO→waveframe/filter; shorter dry release followed by shared dark tail | 260ms /1.6s /.58 /1.25s | −.9992dB RMS |

These envelope numbers describe verified **plugin internal patch state**;
canonical live VST controls remain honest normalized values captured by the
plugin. They are not relabelled native Hz/ms controls. Original patch volume
calibration is bass−.8,stab−11.2,lead−5.1,pad−.8dB; original role faders and gain
lanes retain their contour. A first common−18dB prototype buried bass/lead/pad
by13–18dB and was rejected. Context calibration restores the established
hierarchy, rather than calling a quieter or louder replacement superior.

The old stab **HPF280Hz** attenuated Eb3/G3/Bb3 fundamentals. B uses **150Hz**,
shallower verified slope selector0 and a−1.5dB low-mid cut. PadHPF falls400→240Hz
with a−2dB low-mid cut; pad level remains behind the foreground. Individual
room/plate/chorus/phaser/delay stacks on the new harmonic voices are removed.
The old bass compressor is removed; its native saturation is drive3dB,
wet.25,output−1dB. The new bass's sampled100–400Hz power is actually **3.316dB
lower** at almost identical role RMS, while2–8k power rises5.283dB. This is
an alternative articulation/spectrum, **not proof of heavier or better bass**.
Restored chord100–400Hz power rises4.563dB; that tradeoff needs ears in context.

## Musical performance, not just layer entrances

The six original section boundaries remain:8-bar intro,8-bar groove,8-bar
build,8-bar breakdown,16-bar main return,16-bar outro. Every original kick,
bass and main-call note/clip field is protected. In the second four bars of
each8-bar drop phrase, upper D/Eb chord voices move one octave, with+4/−3
velocity accents at the relevant phrase edges. Eight short original pickups
answer at bars16,24,40,48, on the last beat/eighth subdivision. They retain
C-minor harmonic membership and do not collide with existing notes.
`production.json` lists every old/new note field and added ID; nothing is
removed or silently renamed.

Actual native EQ7 LPF/HPF lanes perform the stab/bass/pad tone across phrases,
build and return. LPF uses its **verified1000Hz lower bound**—an initial650Hz
proposal was rejected instead of weakening the registry. Main-call/answer
phrase endings receive separate send-level throws to **357.142857ms dotted
eighth delay at126 BPM**, feedback.32,LPF5200Hz. Return automation ducks the
long tail by5dB per beat, with more space in the breakdown. This is scheduled
gain shaping, not input-triggered sidechain or external oscillator automation.
The pad's internal LFO is a real plugin modulation connection preserved in
component state; its isolated ON/OFF control changes PCM by21.5359% relative
RMS on identical MIDI/mixer/FX. That establishes activity, not preference.

## Real routing and spatial behavior

`production_host.ProductionAdapter` is a new **opt-in composed adapter**.
Legacy SoundCraft, sampler and external-synth adapters retain their strict
routing limitations and defaults. Canonical schema0.1 already models sends
and bus tracks, so no migration, DAW engine or invented routing JSON is needed.
Only actual SoundCraft commands create/save the following17 native strips:
13 original MIDI tracks, including6 samplers/4 Vitalium instances, plus4 auxes.

| Shared path | Real routing/controls |
| --- | --- |
| Drum sum | All6 drums direct Main disabled;0dB post-fader sends into one actual summed compressor aux;22ms attack,110ms release,−27dB threshold,wet.35,makeup0; native ratio stays4 |
| Short room | Clap/ghost/open hat/stabs/call/answer sends;100% wet room650ms,predelay11ms,lowcut500Hz,damping5600Hz,width.82 |
| Dark plate | Pad/air/call sends;100% wet plate2600ms,predelay35ms,lowcut650Hz,damping4700Hz,width.80; scheduled return ducking |
| Dotted echo | Independent call/answer sends, static−12dB base plus explicit channel-owned−60..0dB trim lanes;357.142857ms,feedback.32,LPF5200Hz,mod depth0 |

Send trim means exactly **native send dB=Send.gain_db+track trim dB**. Its
ParameterSpec is a track-owned dB control, not a fader alias, invented ratio
or schema extension. Routing validates destinations, cycles, slots, supported
units, scalar bounds, linear lanes, file closure and full native state.
One-level post-fader MIDI→aux routes only; pre-fader/custom-send pan/nested
buses, arbitrary structural transactions and external instrument automation
fail closed. Existing static parameter transactions retain scopes/locks/hash
preconditions, exact inverse receipts and full unrelated native comparison.
Automated bases reject scalar edits; edit the lane canonically and export fresh.
A static spread change on a channel with an active center-pan lane also requires
a fresh canonical export rather than the narrow static native-edit API.

Native `mix.pan` has two channel positions. The optional normalized
`mixer.stereo_spread` maps them to **center−spread /center+spread**, with strict
[−1,1] bounds, including existing center-pan automation. It is actual channel
panning, not a phase widener. Stabs use0±.75; pad−.15±.80; call uses its
preserved center-pan lane±.65. Bass/kick/sub remain[0,0]. FX/drum auxes use
[−1,+1]. An aux at these endpoints has a different gain convention than two
centered native pans; the explicit **+6.0205999dB nominal path compensation**
is part of the saved aux fader state, with additional−3/−2dB dark/echo offsets.
It is not hidden listening gain or asserted perfect unity on every pan setting.

The first bus probe was invalid: `track.output` ignored a scalar plural
`tracks` selector and left dry sources on Main. Strict graph validation caught
it. Fresh proof uses the working singular `track` selector, verifies all six
source outputs=None and actual aux Bus inputs/Main outputs, then renders causal
controls. A first audio match alone was deliberately not accepted as routing proof.
No .scraft JSON is rewritten to manufacture support; JSON projections are
read-only verification against the established note/sample/FX verifier.

## Evidence and limits

| Full raw measurement | A Phase13 | B ensemble |
| --- | ---: | ---: |
| Integrated LUFS | −25.062399 | −24.740599 |
| True peak,dBTP | −4.014405 | −4.42226 |
| RMS,dBFS | −27.02856 | −26.77462 |
| Crest,dB | 23.00388 | 22.33732 |
| >500Hz side/mid power ratio | .052210 | .065202 |
| >500Hz side fraction,S/(M+S) | 4.9619% | 6.1211% |
| 20–120Hz mono energy retention | 99.999992% | 99.999998% |
| Clipped sample values /last250ms peak | 0 /0 | 0 /0 |

Sampled FFT values are diagnostics, not perceptual ratings or a target curve.
The complete raw waveforms differ70.55% relative RMS, with no alignment shift.
Shared-space bypass changes6.6713%, summed drum-compressor bypass3.5018%, and
static versus performed stab LPF5.0385%. The same six-drum input's measured
compressor attenuation is−.189dB at0–20ms after kicks,−.446dB at20–100ms,
−.302dB at100–200ms: restrained body control with no makeup claim. Six independent
native groups—including genuinely summed drums—reconstruct full B within
**3LSB**. Broad kick/bass interference is+.0727dB, not oscillator phase alignment.
Both mono folds remain unclipped; the final250ms are silent after settled tails.

`docs/PHASE14_VERIFICATION.json` and artifact `verification.json` record final
checks, file identities, real native save/reopen/repeat PCM, relocated assets
and original patch state. The actual extracted ZIP's `python -I reproduce.py`
is exercised with original media/patch locations hidden and the separately
installed plugin copied to a new temporary location. It rebuilds canonical
state from A plus the prepared original patches and requires exact raw B PCM.
The ZIP includes all relative media/preset/control/provenance dependencies,
original SongSpec, licenses and frozen original MIT replay source. It includes
no plugin binary, converter, factory content, GPL implementation or Suno audio.

Final local regression: **363/363 real-host methods pass**, zero failures/errors/skips, **2107.610s**, including all **337 earlier methods unchanged**,20new symbolic/source-contract tests and6new native lifecycle tests. A fresh offline discovery passes337 methods with26 explicit optional-host skips; fresh20unit+6native checks also pass. The installed wheel/CLI exact apply/undo/redo, full native/PCM relocation and **9670 historical example/artifact hashes** pass. Python3.11/3.13 CI retains all prior workflows and adds graph/patch/wheel checks; exact post-push results are recorded in `artifacts/phase14-house/proof/release-summary.json`.

## Reproduce

Prepared assets and plugin stay project-local. No installation/download occurs:

```bash
python3 tools/phase14_house.py build --out-dir .local/phase14/new-release \
  --source artifacts/phase13-house/B --patches .local/phase14/patches-balanced \
  --plugin .local/phase11/vitalium/usr/lib/vst3/vitalium.vst3 \
  --soundcraft /absolute/path/to/soundcraft-cli \
  --meter-library .local/producer/libebur128.so
python3 tools/phase14_house.py package --out-dir .local/phase14/new-release
python3 -m kuang.production_host inspect --source .local/phase14/new-release/B/native \
  --workspace "$PWD" --plugin .local/phase11/vitalium/usr/lib/vst3/vitalium.vst3 \
  --soundcraft /absolute/path/to/soundcraft-cli
```

The meter library is an optional explicitly supplied MIT reference backend;
Kuang retains its tested stdlib LUFS/true-peak implementation. No certification
claim. `tools/phase14_patch_worker.py` prepares the four authored voices with
an explicit reviewed Pedalboard0.9.26 interpreter and original controller
metadata; ordinary replay only needs prepared patches and the external synth.
See [listening/replay instructions](PHASE14_LISTENING_README.md),
[producer architecture](PRODUCER_ARCHITECTURE.md) and [licenses](LICENSING.md).
GUI operation, cross-platform plugin migration, latest official Vital, a
commercial-quality sound catalog, generalized editable instrument automation,
true sidechain and a native master bus remain unverified or unsupported.
Human listening is the final musical quality gate.
