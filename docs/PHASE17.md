# Phase17 — coordinated space and dynamics on the approved Phase16 palette

Base `1a7f296110e886506502c085df2d641b6f072e3a`. The user listened to Phase16 B
and reported an unmistakable qualitative step-change. **Phase16 B is the new
musical incumbent.** Phase17 B is an unreviewed mix proposal. Its technical
measurements do not establish another musical win.

The exact64bar/126BPM/Cminor source has1536 MIDI notes and six sections. All
note fields, clip ownership/order, track IDs, sections, SongSpec and MIDI bytes
stay exact. All13 original instrument objects and every prepared Vitalium patch
and CC0 sample asset remain unchanged. No new notes, pickups, source palette,
composition, synth tuning or wavetable content. The canonical schema stays0.1;
default creation/revision and all earlier releases remain unchanged.

## Research applied to actual supported controls

[Ableton's compressor reference](https://www.ableton.com/en/manual/live-audio-effect-reference/)
distinguishes a detector/trigger path from the audible signal path. Its
[sidechain production article](https://www.ableton.com/en/blog/sidechain-compression-part-2-common-and-uncommon-uses/)
discusses kick space, pumping chords and ducking large reverberant clouds.
The useful production decision here is protecting transients while allowing
tails to bloom. SoundCraft's verified adapter has no external detector-input
route. Its compressor detector high-pass is not proof of such routing. Phase17
therefore uses explicitly scheduled gain attenuation from immutable kick MIDI
onsets, including dropouts; it is **not audio-triggered sidechain compression**.
No Ableton software, example audio or third-party musical material is used.

iZotope's [stereo-image guidance](https://www.izotope.com/community/blog/6-tips-for-widening-the-stereo-image-of-a-mix)
and [mono/stereo discussion](https://www.izotope.com/community/blog/mono-vs-stereo)
inform the division of centered foreground/low-end and wider filtered ambience.
Mono fold-down is measured alongside width. No Haas offset or phase inversion is
applied to kick, bass or sub. Its [mastering discussion](https://www.izotope.com/community/blog/how-loud-should-my-master-be)
supports level-matched evaluation: this experiment compares equal integrated
LUFS with constant attenuation, rather than treating a loudness target as quality.
No vendor plugin, reference recording or proprietary content is bundled.

## Concrete production proposal

The existing native drum-sum and shared-room graph remains. The old shared
room used800ms decay,15ms predelay,550Hz lowcut,5kHz damping and width.8;
its sends were clap−18,stabs−22,lead−24 and pad−26dB. Two actual stereo aux
strips are added, bringing13 MIDI source strips plus4 auxes to17:

| Path | Controls and musical purpose |
|---|---|
| Short shared room | 650ms,14ms predelay,650Hz lowcut,6kHz damping,width.85. Clap−18,stabs−17,lead−22,arp−24dB post-fader sends; pad moves to the dark return. |
| Dark shared plate | Input EQ650Hz–4.8kHz, restrained slow stereo chorus,2400ms plate,32ms predelay,650Hz lowcut,4.8kHz damping,width1,100%wet. Sends pad−9,air−15,lead−26dB. |
| Phrase echo | Input EQ550Hz–4.8kHz;357.142857ms dotted eighth at126BPM,feedback.28,100%wet; restrained chorus spreads the filtered tails. Selected two-bar phrase-ending existing onsets open post-fader sends briefly. |
| Existing drum sum | Parallel compressor wet.25→.35,attack22→28ms,release110→125ms,threshold−27→−25dB,makeup0. Actual host ratio4 retained. |
| Bass pocket | Approved bass channel, envelopes and gain automation remain exact. A130ms extra duck was rejected: it mostly attenuated silent gaps and changed only.01596% relative PCM RMS. |
| Wet-return breathing | Dark plate up to6dB and echo up to4dB scheduled attenuation,25ms hold/165ms release; breakdown and drop use different return levels. |

Native stereo bus pan positions retain the proven6.0205999dB nominal path
compensation, not an extra master boost. Every bus uses actual native Bus/Aux
objects and post-fader sends. Nested buses, arbitrary send pan, input-triggered
sidechain and native master processing remain unsupported/unverified.

Overlapping individual room/plate/delay/phaser inserts on the five harmonic
tracks are removed with their owned automation lanes. EQ and foreground
compression stay; the quiet snare inserts remain. Stab/pad chorus changes are
small role-specific adjustments, with wider legal native channel positions for
stabs/lead. After measured role calibration, pad shifts−3.35485297dB,air−2dB,stabs+.33997910dB and lead+.27556805dB, including constant offsets on owned gain lanes. These compensate changed dry/return interaction; the musical gain-curve timing remains. Bass is exact. The before
track/lane snapshots, removed IDs, send levels, gate windows and kick onsets are
recorded in `production.json`. There is no hidden rendered-stem replacement.

Echo sends close to a−60dB trim over their declared base send gain. This is very
quiet, not mathematically zero: actual closed-send leakage is measured. Tail
energy after a closed gate is intentional feedback, not an open send. A short
G4 control verifies distinct rhythmic repeats separately from the full record.
The full-source dark/echo/room ON/OFF controls, summed-compressor bypass and
bass PCM identity check establish real processing instead of inert inserts.

## Evidence and listening

Final local proof: **402/402 real-host methods pass**, zero failures, errors or skips, in **3208.101s**. All391 prior methods and test files remain exact. Seven new offline contracts and four native integration methods are included. Wheel/install smoke and frozen-source checks pass. **10,773 historical artifact/example files** remain hash-exact. Full native state and PCM survive save/reopen. An extracted ZIP replays exact full-song PCM with original B session/media and plugin locations hidden, using only relative assets and a separately relocated plugin. Post-push Python3.11/3.13 CI evidence is recorded in artifact `proof/release-summary.json`.

Fresh native G4/Eb4 lead and C2 bass each pass three active audio windows; maximum combined FFT/period error **0.1071 cents**. Actual Cm9 upper-voice partials on stabs/pad have maximum error **0.2424 cents**, below the5-cent gate. All four unchanged patches retain synthetic MIDI pitch input1835232641=.5. The full regression also repeats the prior nine-pitch/four-voice/two-host gate on the unchanged patches. No transposition workaround.

| Full native track | A: approved Phase16 B | B: Phase17 proposal |
|---|---:|---:|
| Integrated LUFS | -25.094741 | -24.988128 |
| True peak dBTP | -4.417381 | -4.268066 |
| Crest dB | 22.7515 | 22.7402 |
| Above500Hz side/mid power ratio | 0.048426 | 0.075988 |
| Above500Hz side fraction | 4.6189% | 7.0622% |
| Mono sum RMS change | -0.046244dB | -0.074411dB |

Both raw files are6091429frames,48k/24bit stereo,126.9047708s including5s of settled release, with zero clipped samples. B's low20–120Hz mono energy retention is **99.99998885%**. Both auditions match **-25.094741LUFS**: A0dB, B-0.106613dB constant attenuation; measured mismatch is below.000001LU. Last250ms are digital zero. Source bass PCM is exact; calibrated pad/stab/lead drop-stem RMS differs by less than.000001dB. In the matched full-song comparison, main-drop RMS changes by **-0.0233dB**, while the deliberately more spacious breakdown changes by **+3.3452dB**. This local energy change is disclosed rather than hidden behind full-song level matching. Full section energy, absolute bands and spatial diagnostics are retained in `verification.json`; these are not perceptual scores.

Same-input full-mix aux ON/OFF relative PCM RMS differences are dark plate **4.307%**, echo **2.242%**, short room **2.259%**. The summed compressor bypass difference is **1.981%**. An isolated native kick-through-bus control changes by **1.166%** relative PCM RMS, with **0.000ms** attack-peak displacement across the tested32 drop hits. Its absolute band powers and attack/body windows are retained. Full-kit nonlinear interaction is checked separately by the summed bypass. These prove processing, not preference. Dark-return scheduled ducking reduces selected-window power to **0.392877** of control and recovers to **0.994259**. Actual echo repeats occur357.142857ms apart and decay over three measured windows. Closed-send RMS is **0.001901** of the active echo, not zero. Maximum PCM error against the idealized declared gain model is reported separately; native smoothing is not claimed sample-exact.

ZIP **64,928,467bytes**, SHA256 **`b0951cb2f22d6a96c4ff51d2bd5e1c4f8d5795c4dbc760d90b4afe93f36a75ff`**. The actual tested replay payload is unchanged except final verification metadata. [Machine proof](PHASE17_VERIFICATION.json). Human full-song listening has **not** selected Phase17; approved Phase16 remains protected.

The final listening ZIP is `artifacts/phase17-house/phase17-house-listening.zip`:
exactly **two complete matched listening WAVs**, A (the approved Phase16 B) and the
Phase17 B proposal, plus complete editable A/B native/canonical/MIDI, unchanged original
patches, relative licensed sample media, source SongSpec and frozen MIT replay.
Internal controls/stems are excluded from the listening pack. No offline master
or third consumer version, plugin binary, factory bank, Suno audio or external
model. [Listening/replay instructions](PHASE17_LISTENING_README.md).

```powershell
scp User@YOUR_VPS:/home/User/Kuang/artifacts/phase17-house/phase17-house-listening.zip .
```

```bash
python3 tools/phase17_house.py build --out-dir .local/phase17/my-mix \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
python3 tools/phase17_verify.py pitch --root .local/phase17/my-mix \
  --out .local/phase17/my-pitch --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/to/vitalium.vst3
python3 tools/phase17_verify.py controls --root .local/phase17/my-mix \
  --out .local/phase17/my-controls --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/to/vitalium.vst3
```

Use fresh destinations. No download/account is needed. All new external exports
explicitly retain the proven neutral synthetic MIDI input1835232641=.5 on
channel0, with the original patch tuning and bend range. Actual G4,Eb4,C2 and
polyphonic Cm9 audio are tested, not inferred from MIDI state. Official Vital,
other plugin builds/channels, GUI/cross-platform editing and arbitrary native
reconciliation remain unverified. The separately installed GPL Vitalium1.0.6
component stays outside MIT Kuang and the archive; the existing six sample
licenses/identities travel unchanged. Metering is validated, not certified.
Human full-song listening decides whether to adopt B; approved Phase16 remains
protected regardless of this experiment's outcome.
