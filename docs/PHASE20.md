# Phase20 — source-first groove and full-song production experiment

The user rejected the initial focus on mastering: the production sounded hollow,
dry and weak even when volume was disregarded. This release therefore starts
with a **16-bar main-groove source experiment**, then applies the selected
combination to the unchanged160-bar song. It is **not an established listening
win**. Phase17's approved palette remains the lineage; human preference for
Phase20 is unreviewed. No professional/club-ready claim.

## Research that changed the work

In Mike Senior's [Sound On Sound interview with Armin van Buuren](https://www.soundonsound.com/people/armin-van-buuren),
Armin says, “Usually we start with an eight-bar main theme”. His practical
advice centers on complementary kick/bass choices, knowing a few synths,
subtractive frequency roles, filtered delay, harmonic distortion and evolving
automation. He warns against trying to obtain a radio sound through excessive
multiband compression. This informed original Kuang designs; no recording,
melody, preset or factory wavetable was copied.

[SOS's separation article](https://www.soundonsound.com/techniques/how-achieve-better-separation-your-mixes)
reinforces separating source articulation and frequency roles before relying
on panning. [Ableton's effect manual](https://www.ableton.com/en/manual/live-audio-effect-reference/)
informs envelope/dry-wet decisions, while its
[sidechain discussion](https://www.ableton.com/en/blog/sidechain-compression-part-2-common-and-uncommon-uses/)
distinguishes kick-space ducking from simple compression. This host still has
no verified external detector route: Kuang retains scheduled MIDI-kick gain
curves and does not call them triggered sidechain.

[iZotope's stereo guidance](https://www.izotope.com/en/learn/6-tips-for-widening-the-stereo-image-of-a-mix)
supports a centered low end and filtered stereo ambience checked in mono.
[EDMProd's house workflow](https://www.edmprod.com/how-to-make-house-music/)
supports choosing the groove's ingredients and balance before polishing.
The private user-directed DJ-blend excerpts are imperfect directional context,
with transitions/crowd/lossy encoding; they establish neither original-track
settings nor a loudness/EQ target and are **not redistributed**.

## Actual source decisions, not insert counts

Five complete16-bar native prototypes compare the incumbent, two FM-bass
alternatives, a shorter kick and new chord/lead sources. The selected version
keeps the **approved FM bass and moving pad**. The alternate bass designs shifted
power toward the fundamental and reduced useful100–400Hz balance; adding more
sub was rejected. This is a selective change, not four simultaneous patch swaps.

| Role | Selected change | Intended purpose |
| --- | --- | --- |
| Kick | CC0 `house.kick.tight-02`, G1, approximately0.306s converted, replacing `punch-02` approximately0.46s | Shorter low-frequency tail and clearer space for the existing bass; unchanged trigger36, velocity, groove and one-shot semantics |
| Bass | Original prepared patch exact; native1000Hz LPF,450Hz−2dB shaping and relaxed insert envelope | Preserve recognizable FM foundation and useful harmonics, avoid another sub layer |
| Chord stabs | Original saw/triangle body plus quiet octave saw;1.5/180ms attack/decay,.22 sustain,85ms release | A warm struck chord distinct from the sustained pad; envelope-to-filter and gentle tempo-related wavetable movement |
| Lead | Original harmonic saw with mild integer FM; three modestly detuned voices;1.5/200ms attack/decay,.20 sustain,50ms release | More textured foreground articulation while preserving the exact G–Eb–F performance |
| Pad and other sources | Original patch/sample identities retained | Protect the user-approved sound hierarchy |

These are explicit Vitalium internal settings, not guessed normalized host
units. Original Fourier wave data and silent32-sample source remain; no factory
bank. The existing worker restores settings and771 actual normalized bindings
in two real plugin instances. Native EQ/FX controls use discovered physical
units; plugin filter cutoff and fourth-root ADSR storage are not relabelled Hz/ms.

The source-first mix also retains the previous experiment's calibrated role
processing, less destructive foreground compression, real drum-sum parallel
compression/color, and stronger filtered room/plate/phrase-echo paths. All edits
are in `B/production.json`, including the intermediate mix recipe and exact
before/after instruments. A declared−3dB output staging pass preserves detector
inputs. A narrow first-kick fader correction addresses a measured DSP-startup
spike without editing MIDI velocity. This is not a full-song loudness target.

The controlled native role bounces, excluding the startup bar, show the intended
change in emphasis. The kick's100–400Hz sampled band fraction changes roughly
.367→.497 and its2–8k fraction.001→.005; its sustained RMS is lower. The stab
changes from a bright thin spectrum toward lower chord body (.087→.870 in
100–400Hz), while the lead's2–8k fraction changes .072→.085. These are spectral
descriptions of this particular performance, **not better-sound scores**; the
new darker stab may still be a subjective tradeoff. Absolute band powers,
role levels and time windows are in `source-controls.json`.

## Music, tuning, editability and controls

All4596 MIDI note records, IDs, pitches, start times, lengths, velocities,
channels, clip ownership/order, all nine sections,126BPM,Cminor and160bars remain
exact. MIDI bytes and original SongSpec provenance remain exact. Only the kick,
stab and lead instrument identities change; bass/pad patches and five other
licensed drum assets remain exact. New independent profile modules do not
change default creation, earlier arrangers, schema0.1 or transactions.

Actual SoundCraft and independent Pedalboard/Vitalium renders test nine pitches
C2,G2,Eb3,G3,Bb3,D4,Eb4,F4,G4 plus held Cm9 partials. Pitch and period estimates
must remain within5cents, with stable periodicity; native save/reopen repeats
PCM exactly. Synthetic channel0 pitch control1835232641 remains neutral.5.
This directly guards the Phase14−200cent failure.

Same-MIDI dry native controls bypass only the new source modulation routes.
Relative ON/OFF difference RMS is approximately.213 for stabs and.689 for lead;
that proves the routing changes sound, not that listeners prefer it. Existing
real summed compressor, color and shared-space on/off evidence is retained
from the protected mix prototype. No new external-trigger sidechain is implied.

The main16-bar preview uses the same608 original events and a transparent−6dB
capture trim on both sides; its terminal has **no effects**. Fresh DSP resets
and five-second tails mean it is not an identical excerpt of running-song FX.
Only constant attenuation matches audition levels. The full B has **no master
EQ/compressor/limiter and no offline master**. The initial mix/master prototype
is protected privately as an experiment, not shipped as the quality milestone.

## Optional native terminal-bus infrastructure

The separate `MasterBusAdapter` was genuinely validated: native `track.output`
Bus routes from previous Main paths to one final stereo aux are transparent
with no processing. Additional sends failed transparency and were rejected.
Only bounded MIDI→one-level aux→terminal→Main routing is allowed, with full
state verification, no cycles, no double feed and no invented send trim. Native
EQ/glue/maximizer controls and scoped edit/inverse were tested separately.
A maximizer ceiling is measured with reconstruction oversampling, not falsely
advertised as a true-peak-aware DSP algorithm. This optional infrastructure is
not the basis for accepting the source-first groove or the primary listening B.

## Verification and listening

**473/473 tests pass with real SoundCraft and optional synth integrations enabled**, zero failures, errors or skips, **5220.376s**. All437 earlier methods/files and **11,262 historical files** remain hash-exact. Ten focused source unit tests and installed-wheel19/20 smoke pass. Full native save/reopen and extracted-ZIP replay with original libraries/plugin paths hidden reproduce raw B exactly. The new lead attack parameter changes actual PCM and its inverse restores exact full state/PCM.

Actual selected-source tuning in SoundCraft and the independent host stays within **1.2227cents** across nine notes; Cm9 partial error is at most **0.0284cents**. All four native external inputs retain neutral pitch bend.5. The requested608-event main16-bar A/B and complete4596-event full song remain exact performances.

Full48k/24bit stereo A/B are309.761896s,14868571frames, zero clips. Raw A/B are−24.431879/−28.569857LUFS,−4.268066/−8.139957dBTP, crest22.0417/22.4904dB. Listening copies use only attenuation to match overall integrated level; no master processing. B above500Hz side fraction is **5.7652%**,20–120Hz mono retention **99.999710%**, mono RMS loss **0.084505dB**. These checks describe integrity and changes, not musical preference.

ZIP **181,423,623bytes**, SHA256 **`338ec0ab4a110cf85dd8461206707d88cb308438be54d5e527100d44bd8497b5`**. Exactly two primary complete songs plus the requested short main-groove A/B. [Machine verification](PHASE20_VERIFICATION.json). Exact commit and post-push3.11/3.13 CI evidence are in artifact proof/release-summary.json. Human listening remains decisive.

Download `artifacts/phase20-house/phase20-house-listening.zip`. Start with the
requested **A/B main16-bar preview** in `groove-preview/`, then the two COMPLETE
matched songs in `listening/`. Editable original and candidate native/canonical/
MIDI, relative licensed assets, original patch states and frozen MIT replay are
included. Internal stems and commercial recordings are not in the pack.

```bash
python3 tools/phase20_sources.py build --out-dir .local/phase20/my-source-record \
  --patches /project/local/prepared-phase20-patches \
  --kick /project/local/reviewed-kick-asset \
  --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/to/vitalium.vst3 \
  --meter-library /optional/explicit/libebur128.so
```

Original `.vital` settings, prepared VST3 state and full normalized mappings are
portable. Rebuilding them uses `tools/phase20_source_worker.py` in the separately
installed optional GPL host; no plugin/host download is performed. The pinned
CC0 kick's source hash, license and best-sinc44.1→48k conversion are recorded in
its asset manifest. No converter binary, plugin, proprietary preset or account
is bundled. Runtime remains standard-library-only MIT.

Limits: other plugin builds, official Vital, other MIDI channels and GUI/cross-
platform behavior remain unverified. Metering is validated, not certified;
matching integrated level is an audition control, not a quality criterion.
Only human listening can decide whether this is the requested qualitative step.
