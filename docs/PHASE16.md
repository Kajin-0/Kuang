# Phase16 — pitch-correct original Vitalium sound design, same approved music

Base `bd96532a78f0d692c5db05d9fde06a95cdd79bcb`. The user preferred Phase15 B
after listening. It is the incumbent here; Phase14 remains musically rejected.
This experiment changes source sounds, not composition: exactly64bars,126BPM,
Cminor,six sections and1536 original note records, with byte-identical MIDI.
There are no pickups, voicing lifts, extra layers or altered velocities/timing.
Human judgement of the new palette is pending. No professional/Suno-class or
club-readiness claim follows from technical tests.

## Research and content decisions

The [Born To Produce tutorial](https://www.borntoproduce.com/pages/vital-wavetable-synth-free-tutorial-learn-synthesis-in-vital)
teaches role design through oscillators, filters, modulation, macros and example
patches. Its downloadable supersaw and future-pad examples were inspected
privately, including version, wave authors and modulation structure. Permission
to use a sound in a track does not establish raw preset redistribution rights.
Neither file nor its wavetable content is in Git, the wheel or listening pack.
No video listening or professional endorsement is claimed.

The [In The Mix lesson](https://www.youtube.com/watch?v=7qQX6YGBQEA), indexed by
the [provided tutorial page](https://audiobyray.com/producing/in-the-mix/vital-synth-full-tutorial-sound-design-fundamentals/),
provides the synthesis topics: spectral/phase shaping, envelopes, multioscillator
relationships, filters, stereo and matrix modulation. Those general concepts
inform independently authored settings; no serialized third-party patch is copied.

[alanjyu/vital_sounds](https://github.com/alanjyu/vital_sounds/tree/bc6f340915568e98fcf928c1697fff2aa44b4e25)
was pinned at `bc6f340915568e98fcf928c1697fff2aa44b4e25`. Its repository declares
CC BY-SA4.0, but actual1.5.5 presets embed waves credited to other creators,
including Echo SoundWorks and yunison, and sometimes noise/sample assets. The
repository-level license does not independently establish those embedded rights.
It was used for structural study only. The [tancla pack](https://tancla.dog/vital)
permits commercial/noncommercial use but has no verified raw-file redistribution
grant; it is not bundled or used. Neither bank is presumed high quality from
its description, license or popularity.

[Official Vital](https://vital.audio/) offers the free Basic full engine. Its
[Basic download route](https://account.vital.audio/basic) presents an account
login. No credentials, account creation or access bypass was used. This release
uses the previously validated, separately installed **DISTRHO Vitalium1.0.6**,
not current official Vital. Its GPL component and optional GPL Pedalboard host
remain external; original Kuang patch/code licensing stays MIT.

## Palette and producer decisions

The original Fourier waveframes remain independently authored, with no factory
wavetable/sample. Actual plugin enum readback establishes FM phase distortion7,
Bend4 and Pulse6; no guessed external preset controls or built-in oscillator LFO
claim is involved. Each prepared patch restores all771 mapped controls and full
component state in two independent real plugin instances.

| Role | Original patch design | Amp attack / decay / sustain / release |
|---|---|---|
| Bass | Mono sine/triangle carrier; octave sine FM exciter with zero direct level; envelope-shaped harmonic strike; keytracked filter; no pitch modulation | 2ms /145ms /.42 /26ms |
| Stabs | Integer-ratio FM tine/reed strike, filter/timbre envelope and note-dependent timbre; restrained release | 1.5ms /230ms /.13 /65ms |
| Lead | Focused phase-shaped original saw/triangle morph; short articulation and filter envelope; no unison beating or pitch envelope | 2ms /170ms /.30 /55ms |
| Pad | Two tuned original harmonic voices; wavetable/Pulse timbral LFO and slower filter envelope; inherited real native chorus/space | 420ms /1500ms /.62 /1450ms |

Envelope times above are physical times; patch serialization stores their fourth
roots. Filter controls inside the plugin are MIDI-note cutoff values; they are
not relabelled canonical Hz. Actual normalized bindings are captured from the
plugin. Native EQ automation retains legitimate Hz units. Pad LFO tempo7 is the
observed half-note division at126BPM; its destinations are timbral, never tuning.
All oscillators use deterministic phases and single unison voices, with no
random detune. Stereo depth comes from actual host chorus/reverb and independent
channel positions, keeping the centered bass/kick/sub path exact. The first
full mix did not improve width, so the pad was revised in a bounded isolated
probe: two differently shaped voices pan−.9/+.9 inside the synth, with a
deterministic25.2degree relative oscillator phase. This is editable source
state, not a hidden waveform widener or pitch detune. Patch output is reduced
by.45dB after that revision to retain pad balance; full mono/stereo and tuning
checks are repeated. The initial centered-pad candidate is not the delivery. The original approved pad was already wide.

First prototypes were too hot. A stem calibration reduced plugin output before
the inherited inserts, preventing extra compressor drive from becoming the
"improvement." The first lead was too fundamental-heavy and was revised toward
more upper harmonics. The new struck chord body was heavily cut by the inherited
280Hz high-pass; the final floor is150Hz,12dB/oct, low-mid cut−1.5dB. Existing
400..1000Hz tension points retain their values/timestamps and reset structure.
The existing stab compressor changes from.2ms/−32dB/+2dB to8ms/−28dB/0dB,
retaining release80ms and the actual host ratio; this protects the strike.

Final post-insert calibration offsets are bass−3.1077318064dB,
stabs−9.3041289158dB,lead−.6116083569dB,pad0dB. These are corrections after
patch output calibration, not extra boosts. Every existing gain-lane point moves
by the same track offset, keeping its precise timing, IDs, interpolation and
duck/release contour. Stabs intentionally target.5dB above their original drop
stem, still behind the main lead; the other roles target their original RMS.
Stereo center/spread becomes stabs−.12/.70,lead+.12/.55,pad−.12/.80. Existing
lead pan automation remains intact. All other inserts, source tracks, samples,
both real shared returns, sends and other automation remain exact. Full before/
after controls and lane records are in `production.json`.

The build adds one selected voice at a time into a fresh **full64bar** native
mix and measures each stage. Integrity gates reject tuning, clipping, mono-low
leakage, source drift and performance changes. They cannot choose musical taste.
Internal stems and bypass tests are evidence, not extra listening homework.

## Actual gates and deliverable

Final proof: **391/391 real-host methods pass**, zero failures/errors/skips, **2812.043s**. All377 earlier test files/methods remain exact;10new offline contracts and4new native lifecycle cases are included. The final10unit checks and wheel/install smoke also pass. **10295 historical artifact/example files** remain hash-exact. Full native state/PCM save/reopen and extracted frozen replay with original patch/session/plugin locations hidden pass. The first run had one incorrect fixture-root environment setting; the entire final suite was rerun with the corrected parent directory, without changing that test or product code. CI3.11/3.13 includes installed palette smoke; the exact post-push run is recorded in artifact `proof/release-summary.json`.

Both native and independent hosts test nine pitches across all four voices, three active windows per note, and actual simultaneous Cm9 partials for the polyphonic voices. Maximum native FFT error **0.5914cents**, independent **0.4734cents**; worst period estimate **2.2409cents**, within the5cent gate. Bass uses verified mono last-note priority. G4 sounds G4, C2 sounds C2; no MIDI transposition workaround.

Raw A/B LUFS **-25.172290/-25.094741**, both TP **-4.417381dBTP**, zero clipped samples,6091429frames each48k24stereo/126.9047708s including settled release. Matched both **-25.172290LUFS** with A0dB/B-0.077549dB constant attenuation. Bass/lead drop RMS stays at the original level; pad−.02348dB,stabs+.5dB. The main lead remains3.64dB above the stab stem RMS.

The initial pad revision widens the first prototype, but **not the approved original**: drop-pad high-band side fraction is21.62% versus23.80%; complete-mix side fraction4.62% versus4.67%. Full mono RMS loss improves from.0723dB to.0462dB; low-band mono energy remains over99.9999%. Width is a remaining limitation. Same-input oscillator-warp bypass RMS differences are bass64.13%,stabs137.65%,lead24.47%,pad35.71%; separate matrix ON/OFF controls are also nontrivial. These prove actual synthesis/processing, not preferred sound. Bass100–400Hz sampled mean-square power changes from.00021837 to.00034594 (1.584×), at unchanged full-drop RMS; sampled band fraction27.94%→44.54%. Complete diagnostics include absolute bands and onsets, not a quality score.

ZIP **63,455,805bytes**, SHA256 **`2519c9f2411c9324a7cbc030739b20f020159f152f47fafa6255609af4a6154d`**. Exactly two matched full-song listening files; editable A/B and all original/relative assets are included. [Machine verification](PHASE16_VERIFICATION.json).

The two complete matched records are in
`artifacts/phase16-house/phase16-house-listening.zip`, with editable A/B canonical,
MIDI, native sessions, relative licensed samples, original prepared patches and
frozen MIT replay source. No plugin binary, third-party bank or reference audio.
Raw mixes remain beside the ZIP. No waveform-only master is used. [Download and
portable replay instructions](PHASE16_LISTENING_README.md).

```powershell
scp User@YOUR_VPS:/home/User/Kuang/artifacts/phase16-house/phase16-house-listening.zip .
```

Reproduction from this checkout uses explicitly installed components:

```bash
python3 tools/phase16_prepare.py --out-dir .local/phase16/my-patches \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3 \
  --host-python /absolute/path/to/optional-host-venv/bin/python
python3 tools/phase16_pitch.py --out-dir .local/phase16/my-pitch \
  --source artifacts/phase15-house/B/project.kuang.json --patches .local/phase16/my-patches \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3 \
  --host-python /absolute/path/to/optional-host-venv/bin/python
python3 tools/phase16_house.py build --out-dir .local/phase16/my-song \
  --source artifacts/phase15-house/B --patches .local/phase16/my-patches \
  --pitch-report .local/phase16/my-pitch/verification.json \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

These commands create fresh outputs and never download anything. Preparation
requires the optional independent host; portable replay needs only the pinned
native stack. Official Vital eligibility would require a separate class/build/
parameter/state contract, lawful installation, actual cross-register/chord pitch
and restore/relocation tests. Renaming a plugin or downgrading a1.5.5 patch is
not compatibility. Arbitrary VSTs, channels beyond0, GUI/cross-platform editing,
true input-triggered sidechain and native master remain unverified/unsupported.
Meters are validated approximations, not formally certified. Human listening is
the final gate, and Phase15 remains the approved fallback.
