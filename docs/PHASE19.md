# Phase19 — editorial restraint and dance-floor continuity

Base `5de7df075fba34d5f7c57b86a80303d72edf7bfd`. The user heard potential in
Phase18, but described its flow as awkward, amateur and confusing for dancers.
**Phase18 is not an approved club song.** Phase17 B remains the approved sound/
production baseline. Phase19 is a new unreviewed editorial arrangement.
No older release/doc is rewritten to imply a different listening verdict.

The non-default `club_flow.py` editor starts from the exact4160-event Phase18
canonical source. It retains160bars,126BPM,Cminor, the four prepared Vitalium
patches, six licensed CC0 samples, instrument parameters, base mixer/insert/send
settings and four real native aux buses. It edits clips/notes, sections, explicit
performance lanes and new metadata. Default creation, schema0.1, original SongSpec
provenance, transactions, earlier arrangers and existing runtime files are intact.
No new instrument, preset, sound library, plugin, model, service or master stage.

## Source diagnosis before editing

Actual per-bar note analysis confirms24 consecutive kick-free bars80–103. The
first complete G–Eb–F MIDI pattern is at26, not32: Phase18 has full teasers at26
and30, but the full608-event approved pocket arrives at32. This distinction is
recorded rather than repeating an inaccurate onset claim. Musical identity being
perceptually weak until32 is compatible with a sparse/filtered teaser at26.
Initial bass/drums first establish at12. The bridge rotates Ab/Eb/F/Bb roots with
two new independent lead responses; the later payoff also changes the foreground
contour. Counting18 different fingerprints did not establish good dance flow.

These findings motivate restraint, not a new theory/palette showcase. The source
velocities, kick anchors, late claps, shuffled hats and offbeat bass are inspected
and reused. Fewer foreground ideas and a reliable meter take priority over novelty.

## Concrete editorial decisions

| Zero-based bars | Function |
|---|---|
| 0–8 | Existing clean four-floor mix-in and familiar filtered stab hint. |
| 8–16 | Familiar bass pocket establishes alongside clap/hats; one G tease at12 and G–Eb at14. |
| 16–32 | Complete G–Eb–F calls and original Bb–G responses establish the song. |
| 32–64 | Original608-note statement remains exact; developed half repeats its signature over the retained bass/stab/percussion performance. |
| 64–80 | C-pedal bridge: Cm9, only68–71 carry familiar Fm9/C color, then Cm9; original call every four bars, no rotating bass roots/new bridge melody. Open hats hand back energy at72. |
| 80–88 | Exactly eight kick-free bars, home Cm9 and familiar augmented hook; quiet quarter-spaced offbeat hats keep time. |
| 88–96 | Actual kick/clap/hats and the signature recover together; bass density grows within the same pocket. |
| 96–112 | Continuous four-floor rhythm, familiar bass/stabs/call; gradual filter performance. A brief harmonic space leaves the kick intact before112. |
| 112–144 | Original translated608-note high point remains exact; developed half uses the same signature rather than another countertheme. |
| 144–160 | Original Phase18 note content and clean DJ mix-out remain exact; existing musical withdrawal continues. |

The editor preserves3695 original note records without a field change and retains
3824 original note IDs. It removes336 events, revoices129 in place, and adds772
source-linked descendants, producing4596 events. More total events chiefly restore
kick/bass/clap/hat continuity; this is not a claim that fewer total notes is always
better. Foreground pitch vocabulary contracts from seven lead pitches to the
three-note signature. Two608-event high points retain exact original fields/IDs.

Every removed/revoiced/added event has an exact old event, destination, reason and
lineage in `composition-receipt.json`; unchanged records are reconciled too. An
independent replay of the complete journal must reproduce the entire note state.
Surviving note order/IDs stay intact; no automatic IDs are regenerated on load.
This composition journal is explicitly not a generic revision-1 undo receipt.

## Harmonic and production restraint

The bridge's Fm9/C color uses the original Fm7 upper voicing F3/Ab3/C4/Eb4, with
G ninth color in the familiar lead/pad, over an explicit C bass pedal. It is not a
blanket transpose or a forced C under unrelated harmony. The other bridge bars
return to Cm9. Original G/Bb/Eb bass pickups are labelled chord-tone passing
material; a valid inversion/pickup is not automatically a wrong-key note.
Every symbolic note-on/off and bar boundary is audited, including actual bass/
upper intervals and transition windows. `harmonic_audit.context` records close
intervals without declaring all minor seconds/sevenths errors. Synth release and
reverb tails are not falsely transcribed by this symbolic sweep.

The approved608-event statements at32–48 and112–128 are protected. All base
instrument/mixer/insert/send state and parameter registry remain exact. Existing
native EQ envelopes reveal the theme earlier, compress the break to eight bars
and retain low-mid body through the recovered groove. Harmonic HPF performance
is gentler until the final two bars; kick/sub filtering is not changed. Pad/air/
stab scheduled gain breathing resumes with the actual kick at88. Echo gates are
re-keyed to new notes with fewer throws outside the protected statements. Wet
returns use actual kick onsets, including the eight-bar gap; no audio-triggered
sidechain, oscillator-LFO or native/offline-master claim is introduced.

Fresh actual native G4/Eb4/F4 lead, C2 bass, home/color stab voicings and pad
voicings must pass pitch gates. External synthetic channel0 input1835232641
remains neutral.5 with the original2-semitone range; no global transpose or
unverified legacy mode. The prior Phase14 incident remains a regression lesson.

## Verification

**437/437 tests pass with real-host integration enabled**, zero failures, errors or skips, **4218.835s**. All420 earlier test methods/files remain exact, plus12 new unit and5 native methods. Installed-wheel smoke passes. **11,112 historical files** are hash-exact. Full160-bar native state and PCM survive save/reopen; actual extracted-ZIP replay with original Phase19/Phase18 native libraries and plugin path hidden reproduces exact raw PCM through relative extracted media and a relocated plugin. Exact commit and post-push Python3.11/3.13 CI evidence are recorded in artifact `proof/release-summary.json`.

The full note journal independently reconciles4160 source events into4596 candidate events:3695 unchanged records,3824 retained IDs,336 removed,129 revoiced,772 added source-linked descendants. Both608-event approved peaks retain exact fields/IDs. All3,561 symbolic active-note intervals are audited, with zero unexplained key/chord/bass flags or failed C-pedal anchors. Actual note pitch error is at most **0.1071cents**, polyphonic partial error **0.1232cents**. Four original external patches and neutral synthetic MIDI input.5 remain exact.

| Complete160-bar record | A: Phase18 reference | B: Phase19 revision |
|---|---:|---:|
| Duration including5s release | 309.761896s | 309.761896s |
| Raw integrated LUFS | -24.644595 | -24.431879 |
| Raw true peak dBTP | -4.122286 | -4.268066 |
| Raw crest dB | 22.6785 | 22.0417 |
| Listening attenuation dB | 0.000000 | -0.212716 |

Both complete auditions match **-24.644595LUFS** within.000001LU, with constant attenuation only. Each is48k/24bit stereo,14868571frames, zero clips; final250ms digital zero. B sampled above500Hz side fraction is **5.1223%**, low20–120Hz mono retention **99.9995564%**, full mono RMS loss **0.047175dB**. No spatial superiority or louder-master claim is made.

Actual isolated native kick attacks in88–112 increase **31→96/96** on the unchanged sample/drum-bus path. Every candidate bar there has all four kick beats; the longest wholly kick-free span contracts **24→8bars**. Complete MIDI signature arrives26→16; initial bass/drum establishment12→8. These facts support the intended continuity edits, not dance-floor approval. B breakdown/recovered-groove/final-payoff RMS is **-35.933/-26.360/-25.569dBFS**; full section/band/transition details are in the machine reports.

ZIP **160,489,993bytes**, SHA256 **`3588cc23c55c84eb516a8ae6df6f2cc46c2636e7027f559e95705f8597e3c170`**. Exactly two complete primary listening WAVs. [Machine proof](PHASE19_VERIFICATION.json). Phase19 preference remains unreviewed; human listening decides whether this flow is better.

The arranger audit is available in the release `flow-audit.json`: all160 kick
counts/offsets, longest kick-free streak, first complete duration/timing-matched
signature, bass/drum establishment, lead vocabulary, harmonic concurrency,
transition notes and complete journal replay. No requirement to maximize phrase
fingerprints is used. The PCM kick control renders the actual isolated kick
through its unchanged native drum-sum path and checks all96 intended attacks in
88–112, versus31 in Phase18. This is timing evidence, not a nonlinear full-mix
stem reconstruction or a musical quality score.

## Listening and reproduction

One ZIP: `artifacts/phase19-house/phase19-house-listening.zip`. Exactly two primary
COMPLETE48k/24bit stereo records, both160bars and integrated-LUFS matched:
A=the Phase18 reference the user heard; B=the Phase19 continuity revision.
No isolated tracks as listening homework. B remains unreviewed until listening.
The pack contains editable B canonical/MIDI/native, relative CC0 media/notices,
unchanged original patch state, original SongSpec, source canonical/MIDI,
editorial/flow/pitch/pulse verification, frozen MIT replay and README. No plugin
binary, factory bank, proprietary recording, Suno audio or louder master version.

```powershell
scp User@YOUR_VPS:/home/User/Kuang/artifacts/phase19-house/phase19-house-listening.zip .
```

```bash
python3 tools/phase19_house.py build --out-dir .local/phase19/my-edit \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
python3 tools/phase19_verify.py pitch --root .local/phase19/my-edit \
  --out .local/phase19/my-pitch --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/to/vitalium.vst3
python3 tools/phase19_verify.py pulse --root .local/phase19/my-edit \
  --out .local/phase19/my-pulse --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/to/vitalium.vst3
```

Use fresh destinations. Native replay requires separately installed reviewed
Linux SoundCraft0.11.0, GPL Vitalium1.0.6 and bubblewrap. No binary is installed or
bundled. Official Vital/current builds, other MIDI channels, GUI/cross-platform
editing and arbitrary native reconciliation remain unverified. MIT core and
standard-library runtime remain unchanged. Validated metering is not formal
certification. Technical correctness and repetition counts do not establish
club readiness or human preference.
