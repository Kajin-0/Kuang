# Phase22 — three independent musical directions, sixteen bars only

The user heard Phase21 and preferred its groove alone, while rejecting the
melodic/harmonic backing as weak. This is a controlled songwriting search,
not another full-song release or a mastering experiment. A is the exact
Phase21 B main-peak window, source bars33–48 (zero-based32–48). B/C/D are
independently composed alternatives. None is selected for a longer arrangement.

## The actual source and protected pocket

The source16 has611 MIDI events. Bass has74 notes, mainly C2 upbeats with
Bb/G/Eb pickups; sub pulse has60. All **six** sampled drum tracks
remain entire Track-equal, including the original shaker and ghost snare.
The source upper parts are112 short chord notes,44 lead notes,8 arp responses,
18 pad and18 air notes. The main lead is an eight-bar G–Eb–F-descended arch,
with related second-half colors. This audit is based on actual canonical data,
not a generic description of an assumed house loop.

Every candidate preserves drum note IDs/timing/velocity/gate/channel, six
samples, four prepared Vitalium states, faders, pan/spread, effects, actual
auxes/sends and automation. The same transparent−6dB capture trim remains on
all four short projects. No source patch, mixer or drum edit is used to sell
a compositional difference. B/C may change only bass/sub pitches; D keeps
the complete low tracks. All have the same16-bar section and126BPM.

## Authored directions

**B / Soulful / Amber conversation.** The keyboard part has an independent
top-note rhythm, short attacks and held responses. A two-bar Cm9–Fm9–Abmaj9
journey returns to C minor; the second eight reframes the order. A singing
lead answers across rests, ending lower on C4. Stab thirds/sevenths and a
held Eb pad inner voice spread harmony over roles rather than doubling a
four-note block everywhere. Roots and original pickup functions move together.

**C / Progressive / The long way home.** A longer melodic ascent reaches G5,
releases downward, then develops a related higher answer and C5 cadence.
Four-bar Cm9/Abmaj9/Ebmaj9 spans lead to a two-bar Bb9sus4 and C-minor return.
Connected inner voicings and repeated rhythmic shapes link the changing roots;
the lead is not independently transposed for each chord. The bass and pulse
retain all timing, accents and lengths, with root/third/fifth/seventh pitch
functions explicitly reinterpreted for major/suspended neighbors.

**D / Hypnotic / Afterimage.** C–G–Bb-based fragments, deliberate empty bars
and small responses leave the groove forward. The bass/sub are exact. A held
Eb4 inner voice supports G4→F4→Ab4→G4 middle movement against D5→F5→C5→D5:
opposing pad directions give background motion even when the lead rests.
The four-bar colors are Cm9→Cm11→Fm11/C→Cm9. The ninth/11th spelling is
deliberate: existing G/Bb bass pickups must remain supported, not ignored.

All new material is original Kuang MIT composition. None is a transcription
or derivative of tutorial/reference melodies. No random note churn or new
instrument is involved. Preference remains unreviewed.

## Research and what was applied

[Attack: Deep House Chords](https://www.attackmagazine.com/technique/passing-notes/passing-notes-deep-house-chords/)
informs seventh/ninth guide voices, inversion continuity and a melodic top
voice. Actual chord spelling is independently derived from root/interval
theory rather than copied from a tutorial diagram.
[Ensemble Voicings](https://www.attackmagazine.com/technique/passing-notes/massive-chords-with-ensemble-voicings/)
and [String Articulations](https://www.attackmagazine.com/technique/passing-notes/applying-string-articulations-to-synthesizers/)
inform distributing chord functions across registers and held/short playing.
Here this is MIDI gate/velocity performance on existing patches; native
synth ADSR automation is not invented.
[Contrary Motion](https://www.attackmagazine.com/technique/passing-notes/contrary-motion/)
informs the opposing pad lines, without borrowing its example melodies.
[Chord Stabs](https://www.attackmagazine.com/technique/passing-notes/levelling-up-your-chord-stabs/)
informs rhythmic top voices and varied articulation.
[Ableton: Mutation](https://makingmusic.ableton.com/creating-variation-2-mutation-over-generations)
informs recognizable internal phrase descendants, not random variation.
The requested Berklee page returned HTTP503 and is not claimed as read or
used as evidence. No tutorial downloads, presets, audio or project files used.

## Exact edit and native proof

`house_shortlist.py` is an opt-in library; schema0.1/default creation and all
earlier arrangers remain unchanged. It accepts the sealed main16 reference,
rejects locks/source drift/unknown directions and journals all old/new/pitch-only
notes. Source SongSpec remains ancestor metadata. `shortlist_audit.py` derives
chord pitch classes independently, audits every actual onset/offset and bar,
checks bass functions and exact drum/bass rhythm/mix preservation, and audits
pad color notes through a conservative1.65s dry release budget and air notes
through2.4s, covering the original native2200ms release. A pre-release C air
note was changed from G5 to shared F5 at the Ebmaj9→Bb9sus4 handoff after this
check exposed its tail. The first full regression was interrupted rather than
claimed successful; final verification uses the corrected score. Reverb/FX
tails and perceptual consonance are not transcribed or scored.

Actual SoundCraft exports use CLI operations only, with the original native
bus graph. Four external roles are tested in SoundCraft and independent
Pedalboard/Vitalium, including C2/G4/Eb4, new bass roots/registers and voiced
chord partials. Arp/air are tested natively. Synthetic channel0 pitch input
1835232641 stays.5; the Phase14 two-semitone initialization failure remains
guarded. Save/reopen, relative-media relocation and frozen extracted replay
must reproduce every raw PCM hash. Source reference A must reproduce the
existing Phase21 main16 PCM hash, not merely similar notes.

**513/513 real-host tests pass**, zero failures/errors/skips, 6792.063s. All493 earlier test methods/files and **11,858 historical files** remain exact. Thirteen focused composition methods, seven new native methods, independent-process score/MIDI/receipt checks and installed-wheel smoke pass. Current/installed/frozen runtime: 71 files exact.

All four isolated drum renders are **PCM-byte-identical**; A/D bass+sub renders are also identical. B/C change only documented low pitches, with exact note identity, onsets, gates, velocities, channels and clip order. New upper note counts are B=134, C=128, D=71; different density is intentional, never a quality score. Every authored/removed/pitch-only event is journaled; independent harmony/root/release errors: zero.

Actual new-register tuning passes in both hosts: maximum note 1.7583cents and voiced-chord partial 1.0259cents, below5cents. Complete native state and each raw PCM survive save/reopen and extracted-ZIP replay with all original project/plugin paths hidden. Four48k/24bit stereo mixes are unclipped and level-matched to within.001LU by constant attenuation only. Musical duration30.476190s plus5s release; no new160-bar arrangement or master processing.

ZIP **42,123,667bytes**, SHA256 **`d03e400acb4a03a07ba5bf52de9ff1235ca19ac9cccd1f56b996876c9140deca`**. [Machine verification](PHASE22_VERIFICATION.json). Exact commit and post-push Python3.11/3.13 CI evidence are in artifact proof/release-summary.json. None of B/C/D is human-selected; no professional/club-ready preference claim.

## Listening/reproduction

One pack: `artifacts/phase22-house/phase22-composer-shortlist.zip`, four full-mix
16-bar48k/24bit WAVs plus5s release, and four editable source/native/MIDI bundles.
There is no new160-bar song. [Listening instructions](PHASE22_LISTENING_README.md).

```bash
python3 tools/phase22_shortlist.py build --out-dir .local/phase22/my-shortlist \
  --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/to/vitalium.vst3 \
  --meter-library /optional/explicit/libebur128.so
```

Constant-gain matching is only an audition control; no loudness/brightness
target or master processor selects a winner. Pinned user-installed Linux
SoundCraft0.11.0/Vitalium1.0.6 remain separate from MIT Kuang. Other builds,
channels, official Vital and GUI/cross-platform behavior remain unverified.
The human selection is the quality gate before any full-song extension.
