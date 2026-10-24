# Phase14 postmortem — human rejection and an actual pitch failure

**The user rejected Phase14 B. Phase13 remains the musical incumbent.**
The complaint that B sounded strange and might lack a coherent key was justified
by a playback defect. The363 passing Phase14 tests did not test the fundamental
frequencies produced by an external instrument. We treated native state equality,
preset restoration, non-silent PCM and MIDI key membership as stronger evidence
than they were. That was a validation failure in Kuang's production workflow.

## Controlled evidence

The original90ms Goertzel observation was a clue, not the diagnosis. Phase15
rendered10 isolated held-note cases across four voices, each with three separate
400ms active windows, removing inserts, sends and overlapping notes. A Hann FFT
with sub-bin interpolation reports full-band peaks as well as the fundamental
neighborhood; an independent normalized time-domain period estimator cross-checks
pitch. A stronger harmonic is not automatically labelled the fundamental.

| Input / expected equal-tempered frequency | Phase13 native control | Phase14 native legacy mode | Same Phase14 preset off-host |
| --- | --- | --- | --- |
| G4 MIDI67 /391.9954Hz | approximately392Hz | approximately349.228Hz,F4:−200cents | approximately392Hz |
| F4 MIDI65 /349.2282Hz | approximately349Hz | approximately311.127Hz,Eb4:−200cents | approximately349Hz |
| Eb4 MIDI63 /311.1270Hz | approximately311Hz | approximately277.183Hz,Db4:−200cents | approximately311Hz |
| C2 MIDI36 /65.4064Hz | approximately65.407Hz | approximately58.270Hz,Bb1:−200cents | approximately65.406Hz |

The other bass/register/chord/pad cases show the same native legacy offset.
Phase13's30 FFT windows range approximately−3.04..+1.78cents; the independent
Pedalboard host's30 Phase14 windows range−.31..+.38cents. The large native error
persists after the attack and without track FX. It is not explained by reverb
tails, note overlap, a changed MIDI pitch, oscillator transpose or ordinary
unison beating. The saved component has voice transpose/tune0, oscillator1
transpose0, and intentional oscillator2 octave settings; its pitch wheel is
centered internally. All notes used MIDI channel0.

## Exact native input responsible

The771 ordinary synth controls are not SoundCraft's complete2851-parameter
VST3 list. The other2080 are16×130 synthetic MIDI-controller slots, all initially
recorded as0. The synthetic channel1 pitch-bend input **1835232641** is one of
these. Its0 is the negative extreme, not neutral. The ordinary synth's named
Pitch Wheel control being normalized.5 did not prevent the synthetic input
from driving it down by the default2-semitone bend range.

An actual CLI-created same-note/same-preset counterfactual changes only this
native input, with the bend range still2:

| Synthetic input value | Measured G4 offset |
| --- | ---: |
| 0 | approximately−200.00cents |
| .5 | approximately+.02cents |
| 1 | approximately+200.00cents |

The [pinned SoundCraft0.11.0 VST3 wrapper](https://github.com/storytold/soundcraft/blob/v0.11.0/crates/vst3-host/src/plugin.rs)
resends stored values and handles MIDI controller/pitch-bend mappings. Kuang
copied the entire defaults table without classifying these MIDI inputs or
calibrating played pitch. This combination reproduced a wrong but perfectly
stable result. A separate zero-bend-range experiment also restores pitch,
confirming the pitch-bend path; it loses bend expression and is not the preferred
technical fix. No global MIDI transpose is appropriate: the same presets already
play correct notes in the independent host.

Phase15 adds an **explicit opt-in** native MIDI initialization convention:
`center_pitch_bend=True` /CLI `--center-pitch-bend`. It sets the verified synthetic
channel1 input to.5, leaves the771 synth controls and original component bytes
unchanged and retains the2-semitone bend range. The capability fingerprint records
this mode. Ten native note cases, the actual four-note upper Cm9 voicing and
save/reopen PCM are tested. Other MIDI channels or different host/plugin binaries
fail the scoped contract. This is not generic current-Vital/VST compatibility.

Legacy mode is retained for exact historical reproduction and existing tests.
**Do not use its old non-silent/state-equal result as a new musical compatibility
claim.** Historical projects, WAVs, tests and frozen replay sources are untouched.
The corrected palette remains unapproved by human listening and is not used in
the conservative Phase15 full-song candidate.

## Why MIDI key checks missed the mixed harmony

The preferred rootless upper voicing Eb3/G3/Bb3/D4 over C bass describes Cm9.
D is a ninth; D/Eb proximity or the Eb–D major-seventh span is not automatically
a wrong key. Phase14's octave lifts also retain pitch classes. Its added eight
pickups and velocity changes were unproven artistic choices, not evidence of
the two-semitone fault, and are all reverted in Phase15.

The real problem was a **mixed playback map**. Four replaced voices shifted
by−2semitones while the built-in response/air/sub pulse stayed at their intended
pitches. C bass became Bb, and the upper Eb/G/Bb/D became Db/F/Ab/C, consistent
with a different tonal center. The unshifted C pulse and responses then overlapped
unintended notes. Symbolic C-minor membership remained true while some sounding
Db notes were outside that collection. Applying the measured−2semitone map to
the exact active-note events flags131 out-of-scale note records, versus zero
in either unshifted symbolic project. The machine report records exact
MIDI-active overlap intervals with the independently measured offsets; it does
not pretend to transcribe every reverb tail or score dissonance as bad taste.

## Repair and prevention

The primary Phase15 B rebuilds from **Phase13**, not the rejected project. It
retains all1536 original note records, original instruments/inserts/faders/pans,
original automation and the full64-bar form. No external synth, octave lift,
pickup or new pad is used. Only a gentle actual summed drum compressor and quiet
shared room are added. The ZIP remains an unreviewed safe rollback comparison,
not a claimed production-quality win. Phase13 remains incumbent.

New tests require actual controlled pitch across registers, harmonic-aware and
period estimates, four-note chord playback, exact original MIDI/source identity,
real FX on/off, state/PCM reload and relocated replay. New backend/sound selection
must pass these before it informs a full production. Human listening remains
necessary after tuning, because correct pitch and technically valid routing do
not establish good timbre, phrasing, balance or emotional coherence.
