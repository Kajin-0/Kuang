# Phase18 — a developed extended house record from the approved Phase17 B

Base `e3eecbdfb770c7c27cc05cc134ecbba796f11074`. The user listened to Phase17 B
and explicitly approved its better sound/production, while hearing a demo rather
than a finished song. **Phase17 B is the musical incumbent.** Phase18 is an
unreviewed arrangement proposal. Earlier release documents retain their original
listening status as historical records; no old release is rewritten.

This is an independent `house_composition.py` arranger, not another sounds-only
pass or a change to default `create`, SongSpec, schema0.1 or transactions. It builds
160 bars at126BPM/Cminor: 5:04.7619 of score plus5s of release. The instruments,
prepared patches, six CC0 samples, mixer/insert/send graph and four real native
aux buses are exact Phase17 B. Only clips/notes, sections, arrangement metadata
and automation change. No new synth/FX/plugin, model, download or paid dependency.

## Research and actual musical decisions

[EDMProd's house guide](https://www.edmprod.com/how-to-make-house-music/) supports
long DJ bookends, phrase-based development and kick/bass cooperation. This record
uses16-bar mixable bookends and16/32-bar larger sections, with two-bar questions
and eight-bar developments inside them. These are chosen functions, not a claim
that every house record must follow one template.

Dennis DeSantis's official *Making Music* chapters
[Dramatic Arc](https://makingmusic.ableton.com/dramatic-arc),
[Arranging as a Subtractive Process](https://makingmusic.ableton.com/arranging-as-a-subtractive-process),
[Unique Events](https://makingmusic.ableton.com/unique-events) and
[Mutation Over Generations](https://makingmusic.ableton.com/creating-variation-2-mutation-over-generations)
inform the recognizable return, authored answer contours and sparing one-time
fills/rests. The provided public23MB PDF exceeded the browser reader; the same
author's official online chapters were read. No book text, musical example or
waveform is copied into Kuang.

[MusicRadar's club-intro tutorial](https://www.musicradar.com/how-to/how-to-create-the-perfect-intro-for-your-club-track)
informs filtered bass teases, eight-bar percussion handoffs and gaps before a
return. No tutorial sample, proprietary preset or reference recording is used.
No Suno audio is included or copied. The actual human-approved source is Phase17.

## The composed arc

| Display bars / start time | Musical function beyond layer count |
|---|---|
| 1–16 /0:00 | Clean kick and shuffled hat exchange, filtered Cm9 replies; bass teases in13/15, no foreground lead. |
| 17–32 /0:30.48 | Establish short bass/body, two-note G–Eb question, then full G–Eb–F teaser; changed stab answers and a one-beat turn. |
| 33–64 /1:00.95 | First16 bars preserve the approved608-note statement exactly. Next16 develop G–F–Eb/F–Eb–G answers, F-root turnarounds, chord articulation and small fills. |
| 65–80 /2:01.90 | Abmaj9→Ebmaj9→Fm9→Bbadd9, two bars per chord, explicitly paired bass roots Ab1/Eb2/F2/Bb1; two different eight-bar melodic responses. |
| 81–96 /2:32.38 | No kick, bass or pulse. Four-bar Ab/Fm/Eb/Gm breathing, augmented familiar contour, descending answer, and a full note-free bar96 before rhythm resumes. |
| 97–112 /3:02.86 | Offbeat rhythm before kick returns at105; rising LPF/HPF performance, deliberate ghost fills, D–Eb–F pickup, then a note-free last beat before113. |
| 113–144 /3:33.33 | Exact translated608-note approved return, followed by a different F–G–Eb response and an eighth-shifted final hook. |
| 145–160 /4:34.29 | One quiet farewell fragment, chord/bass withdrawal; last eight bars contain only the established drum palette for a usable mix-out. |

The source16-bar pocket appears once with its original IDs, clips and absolute
note fields at32..48 (zero-based). Its later literal return is translated by80bars
with new identities. The remaining phrases are source descendants or explicitly
authored material. The20 eight-bar phrases have18 distinct pitch/rhythm signatures
when velocities and IDs are ignored. Two pairs are intentional literal returns;
there is no claim that all repetition is undesirable in house music.

The final record has4160 MIDI events. **MIDI bytes are not preserved.** Every
note has provenance, destination tick/display bar/beat, actual fields and musical
reason in `composition-receipt.json`. Copied/revoiced events identify the exact
original source event; authored responses/pads/fills have explicit authored
origins rather than invented source IDs. This document is not a generic
transaction/undo receipt. Original SongSpec and all historical arrangement
metadata remain source provenance; `phase18_arrangement_spec` describes160bars.

The approved C-pedal Fm7/C turnarounds, short Bb/G/Eb pickups and ninth colors
remain explicit inherited vocabulary. New B roots are actually paired with
voicings, not blanket-transposed voices over a C pedal. Its upper voices move
at most three semitones between neighboring two-bar chords. Pads use spread
chord tones rather than new tight adjacent-note clusters. Rootless chords,
minor seconds/ninths and a diatonic melodic11th/13th are not automatically
wrong-key notes: the audit separates planned root, chord membership and melody.

## Native production and evidence

The approved synth component bytes, instruments, faders, pans, insert settings,
sends and bus graph remain exact. Twenty explicitly chosen source automation
windows retain Phase17's actual envelopes/production character. Filters have
section-specific performance; echo throws and wet-return breathing are re-keyed
to the new actual MIDI. Kick/bass/sub remain centered. Ducking is scheduled MIDI
gain automation, not detector-input sidechain. No wavetable/LFO control is invented.
No master bus or offline mastering stage is introduced.

All symbolic note-on/off and bar boundaries are swept: no sparse chord sampling.
The complete harmonic audit has zero out-of-key intervals, unexplained harmonic
layer/bass intervals or wrong B roots. It explicitly labels melodic color tones.
This does not transcribe release/reverb tails or establish perceived consonance.
Actual dry new-note and poly-chord rendering is required in addition.

The short pulse has0 sustain and110ms decay. A sustained-note late-window probe
correctly found silence; this is not a wrong pitch. Its actual short body is
verified using observed zero-crossing periods, validated on independent decaying
C2/F2 vectors, without changing its envelope. Actual F2 measured−.0035cents in the
initial transient check. Other new notes use both FFT and period estimates over
three active windows. Six unique simultaneous chord voicings are rendered.

A first filter counterfactual removed automation but left the LPF at its closed
1kHz base. That was not an open bypass reference. The corrected same-input control
holds LPF14kHz and the original resting HPF, documenting the difference explicitly;
no candidate mix setting was changed to make the test pass.

Final proof: **420/420 tests pass with real-host integration enabled**, zero failures, errors or skips, **3667.333s**. All402 previous test methods/files remain exact, plus13 new unit and5 native record methods. Wheel/install and installed profile smoke pass. **10,964 historical files** remain hash-exact. Full160-bar native state and PCM survive save/reopen; extracted ZIP replay with original B media and plugin paths hidden produces exact full raw PCM. A separate replay also hides the original Phase17/Phase16 native libraries and raw sample source pack and remains PCM-exact. Exact commit and post-push Python3.11/3.13 CI evidence are in artifact `proof/release-summary.json`.

The4160-event record retains608 original statement notes and608 translated return notes with exact performance fields. All20 eight-bar functions have music;18 pitch/rhythm signatures remain distinct after ignoring velocities/IDs. All3,289 symbolic active-note intervals are audited, with zero unexplained key/chord/bass flags or wrong B roots. Neighboring B voicings move at most3semitones per voice. The actual new-note maximum error is **0.3569cents**; six actual polyphonic voicings have maximum partial error **0.0232cents**. Unchanged synthetic pitch initialization is.5, not the rejected legacy0.

| Complete record | A: approved Phase17 | B: Phase18 extended |
|---|---:|---:|
| Bars / duration including5s release | 64 /126.904771s | 160 /309.761896s |
| Raw integrated LUFS | -24.988128 | -24.644595 |
| Raw true peak dBTP | -4.268066 | -4.122286 |
| Raw crest dB | 22.7402 | 22.6785 |
| Listening attenuation dB | 0.000000 | -0.343533 |

Both complete auditions match **-24.988128LUFS** within.000001LU, with constant attenuation only. Raw and matched files are48k/24bit stereo with zero clipped samples. B has14868571frames; last250ms are digital zero. Its above500Hz side fraction is **5.4144%**, low20–120Hz mono energy retention **99.9995291%**, full mono RMS loss **0.050624dB**. The longer DJ bookends change aggregate width compared with Phase17's7.06%; no same-length spatial improvement is claimed.

The breakdown RMS is **-36.173dBFS**, final-return RMS **-25.568dBFS**. The last pre-return beat has **0.002082** of the next bar's mean-square power; tails remain musical, not hard waveform edits. Performed rebuild2–8kHz power is **0.548586** of the explicit open-filter counterfactual. These are actual native signal checks, not a musical quality score. Full absolute section bands, concurrent intervals and causal-control hashes remain in the release.

ZIP **110,755,755bytes**, SHA256 **`bdb38b9c64d9b9c93a6b7c1ed7b3e7ea2bfc7f866cf9eae8a13bb7511344b769`**. Exactly two complete primary listening WAVs. [Machine proof](PHASE18_VERIFICATION.json). Human listening has not selected Phase18; approved Phase17 remains protected.

## Listening and reproduction

One ZIP: `artifacts/phase18-house/phase18-house-listening.zip`. Exactly two primary
COMPLETE matched48k/24bit WAVs: A=approved Phase17 B64bars, B=new Phase18 record160bars.
They have different lengths. Matching integrated LUFS does not make them an
aligned same-length mix A/B. No diagnostic stems are listening homework.
The pack includes editable B canonical/MIDI/native, original patch state, relative
licensed samples, original SongSpec, source canonical/MIDI, note receipt, harmonic
and pitch/gesture verification, frozen MIT replay and README. No plugin binary,
factory bank, Suno recording, extra radio edit or consumer master.

```powershell
scp User@YOUR_VPS:/home/User/Kuang/artifacts/phase18-house/phase18-house-listening.zip .
```

```bash
python3 tools/phase18_house.py build --out-dir .local/phase18/my-record \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
python3 tools/phase18_verify.py pitch --root .local/phase18/my-record \
  --out .local/phase18/my-pitch --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/to/vitalium.vst3
python3 tools/phase18_verify.py gestures --root .local/phase18/my-record \
  --out .local/phase18/my-controls --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/to/vitalium.vst3
```

Use new destinations. Native replay needs the separately installed pinned Linux
SoundCraft0.11.0 and GPL Vitalium1.0.6; no binary is bundled or installed by Kuang.
All external exports explicitly retain neutral synthetic channel0 MIDI input
1835232641=.5 with the original2-semitone bend range. Official Vital, other builds/
channels, GUI/cross-platform editing and arbitrary native reconciliation remain
unverified. MIT core/schema0.1/default SongSpec paths are unchanged. Validated
metering is not certification; human full-record listening decides musical success.
