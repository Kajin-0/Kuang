# Phase23 — one melody-free harmonic groove

The user rejected all three Phase22 melodies and still found the instrumental
quality weak. They asked for ONE16-bar candidate without a lead melody, keeping
the approved Phase21 drums/bass exact. No further shortlist or160-bar expansion.

The source is the sealed Phase22 A window: the exact Phase21 B main-peak bars
33–48 (zero-based32–48), including its original transparent−6dB capture trim.
The611 source MIDI events include277 drum and134 bass/sub events. Every field
and device on those eight rhythm tracks remains unchanged. Shared return/bus
state and rhythm expression lanes remain unchanged too.

## One musical decision

The lead, two-note arp responses and ornamental high-air track are removed as
actual tracks, instruments, notes and owned automation. No muted placeholder
or new solo line replaces them. Remaining musical parts are:

- A28-strike, three-note chord hook: short/held attacks interlock around the
  original bass and percussion. Connected rootless guide voicings supply
  Cm9→Cm11→Abmaj9/C→Cm9 over four-bar spans, with no changed bass root.
- A three-voice sustained pad: common Eb/G inner voices and quiet embedded
  D/F/C/D chord colors. Those are long polyphonic harmonic voices, not an
  independent melodic answer. Two-second release clearance covers the actual
  new1.8s amp release at chord changes.

The candidate has501 events: the411 original protected rhythm events and90
authored harmonic notes. More notes is not a goal. New performance has explicit
source-role lineage; all removed events are inventoried. Original SongSpec is
preserved as ancestor metadata. Canonical0.1 and all default compilers remain.

## Actual sound design

The original chord source had a sharp1.5ms attack,180ms decay,22% sustain and
85ms release, a bright saw-morph plus a quiet octave layer. The new original
patch uses7ms/320ms/36%/170ms articulation, two same-octave single oscillators
at softer Fourier morph positions150/220, and reduced chorus. Its filter
envelope and velocity response shape the chord strike/body. No pitch drift,
FM exciter, broad detune or hidden octave layer.

The original pad used420ms/1.5s/62%/1.45s, phase-warp motion and strongly
opposed oscillator pan. The new source uses750ms/2.8s/70%/1.8s, softer original
Fourier morph positions130/190 and two modestly separated, exactly tuned single
oscillators. Slow filter/wave movement gives sustained depth with existing
returns. Internal reverb/delay/chorus remain off; native chorus wet falls
40%→18%, the pad HPF240→180Hz and its450Hz−1dB cut becomes0dB. No bass/sub EQ
or shared return is altered. Harmonic dynamics and LPF performance vary slowly
through4/8/16bars, retaining the original beat ducking underneath.

Vitalium INTERNAL units are explicit: envelope knobs are fourth roots of
seconds; cutoff is MIDI-note units, not a canonical Hz relabel. The actual
1.0.6 parameter-text probe reports tempo enum3=8/1, enum4=4/1 and Sync Type1=Sync.
The pad uses8-bar sync; chord timbre uses4 bars. Connections target waveform/
filter, never pitch. Native EQ lanes use validated Hz and gain lanes dB.
This is actual Vitalium modulation, not a claim about builtin oscillator LFOs.

Both patch states and every normalized binding must restore in TWO real
Vitalium instances before export. Original Fourier tables remain byte-equal
to the reviewed Kuang formulas; no factory preset/sample or new download.
GPL plugin/test host stay separately installed; core runtime remains stdlib MIT.

## Verification and listening boundary

The full mix is rendered once as one authored waveform. Save/reopen and replay
create temporary byte-identical verification copies, never alternate musical
versions. Private stems isolate the protected rhythm, old/new source states on
the SAME new MIDI, and evolving/static native pad filtering. Equal-LUFS source
differences are measured with an analysis-only scalar, not another processed
listening file. Band/body measures describe a source change, not warmth/taste.

The source reference recording is already available; it is read for player-gain
comparison only, never newly rendered. The candidate remains a raw native
bounce with no master chain. No recording-quality claim follows from loudness.

Mandatory offline discovery: **531 methods, 451 executed successfully, 80 optional-host skips**, zero errors/failures (1045.829s). **Five new real single-candidate methods and four existing primary real-adapter methods pass**, zero skips, plus 13 focused unit methods and wheel/install smoke. All **513 earlier methods/files** and **12,171 historical files** are unchanged. Current, installed and frozen runtime: **72 files exact**. The historical multi-candidate/full-song native suites were not regenerated.

Protected eight-role rhythm audio is **PCM-byte-identical**. Complete native state and the finished waveform survive save/reopen and extracted ZIP replay with original source/plugin paths hidden. Two new source states restore in two real plugin instances. Native and independent pitch tests cover both new harmonic voices and unchanged C2 bass: maximum note error **0.3189 cents**, chord partial **0.1425 cents**, below 5 cents.

On identical new MIDI and inserts, the new vs old source-state deltas after equal-LUFS normalization are **0.525 chord / 0.494 pad** relative RMS. Evolving vs static native pad filtering changes relative RMS by **0.222**. These prove causal sound changes, not better taste.

The one raw native mix measures **-31.039 LUFS**, **-8.660 dBTP**, zero clipped samples; mono RMS loss **-0.114 dB**, below-120Hz mono energy retention **99.9948%**. The existing reference needs **+3.015dB player gain** for equal-level comparison; the new WAV has no master or normalization. The average level difference is not a quality claim.

ZIP **10,614,252 bytes**, SHA256 **`cc0d0669177d205c0ae640b013c4e364938cf639c9200574b2ba974532623065`**. [Machine verification](PHASE23_VERIFICATION.json). Exact commit and post-push Python3.11/3.13 CI evidence are recorded in artifact `proof/release-summary.json`. Listening verdict remains pending.

Mandatory offline discovery preserves all513 earlier methods. Focused real-host
integration covers this one candidate and the primary adapter, rather than
recreating the old multi-candidate/full-song experiments. Optional historical
plugin/audio suites skipped by the offline run are reported explicitly; an
aborted/failed run is never counted as passing.

One compact ZIP: `artifacts/phase23-house/phase23-no-melody-groove.zip`.
One new main WAV plus live native/canonical/MIDI, relative media, original
patches, licenses, full provenance and frozen replay. [Listening instructions](PHASE23_LISTENING_README.md).

```bash
python3 tools/phase23_groove.py build --out-dir .local/phase23/my-groove \
  --patches /absolute/path/to/prepared/phase23-patches \
  --soundcraft /absolute/path/to/soundcraft-cli --plugin /absolute/path/to/vitalium.vst3
```

Only pinned Linux SoundCraft0.11.0/Vitalium1.0.6 are verified. GUI/cross-platform
editing, other builds/channels and official Vital remain untested. Harmonic
audit covers MIDI plus conservative dry releases, not transcription of reverb
tails or artistic consonance. No triggered sidechain claim. No winner/long song
is generated: user listening decides whether this is richer without a melody.
