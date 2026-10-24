# Phase15 — musical repair, pitch diagnosis and safe full-song rollback

Base **0239d757ae6ae6c42b8e904ad261d8a7536ba681**. The user rejected Phase14 B as
strange and possibly incoherent in key. [The postmortem](PHASE14_POSTMORTEM.md)
records a real native external-instrument tuning fault: all ten controlled
Phase14 cases sound about200cents flat in SoundCraft legacy mode, while the same
saved presets play correctly in the independent host. State equality and MIDI
key membership were insufficient. We did not compensate by transposing notes.

The exact native synthetic MIDI pitch input1835232641 yields−200/0/+200cents
at0/.5/1 with the default2-semitone bend range. The new opt-in initializer centers
it at.5, with unchanged component state, ordinary synth controls and MIDI. It is
pinned to the reviewed SoundCraft0.11.0/Vitalium1.0.6 binaries and channel0 notes.
This compatibility repair does **not** establish that the Phase14 palette is
musically preferable. Legacy exact-replay mode remains unchanged and quarantined
from new musical conclusions. Official Vital and other plugin builds are untested.

## Primary listening candidate

**A=unchanged Phase13 B**, the human-preferred incumbent.
**B=conservative repaired full song**, built directly from A:

- Exact64bars,126BPM,Cminor,six sections, all1536 note IDs/fields and byte-identical
  type-1 MIDI. All Phase14 lifts, pickups and velocity changes are absent.
- All13 original source instruments, inserts, mixer controls and automation stay
  exact. The sampled kick and full licensed drum palette are retained.
- Six drums feed a genuine stereo compressor aux with their direct Main paths
  disabled.22ms attack,110ms release,−27dB threshold,wet.25,makeup0; native ratio4.
- One quiet shared800ms100%-wet room receives clap−18,stabs−22,lead−24,pad−26dB
  post-fader sends;15ms predelay,550Hz lowcut,5000Hz damping,width.8. Original
  per-track effects remain. No wholesale sound replacement or new performance.

The two auxes use real Bus/Aux objects and the previously verified native pan
convention, with explicit6.0205999dB nominal path compensation. There is no fake
parallel bus, waveform master, real input sidechain or hidden audio correction.
This is deliberately a **safe rollback candidate**, with restrained processing;
Phase13 remains incumbent pending a new listening decision.

Download **`artifacts/phase15-house/phase15-house-listening.zip`**. Exactly two
complete listening files are in `listening/`; editable A/B canonical0.1,MIDI,
SoundCraft native, relative sample media, original SongSpec, licenses and frozen
MIT replay source accompany them. Both are48k/24bit stereo,126.9047708s including
settled release. B needs **no Vitalium**, just the separately installed host.
No plugin binary, proprietary preset, reference/Suno audio or diagnostic-stem
homework is included. [Listening/replay instructions](PHASE15_LISTENING_README.md).

```powershell
scp User@YOUR_VPS:/home/User/Kuang/artifacts/phase15-house/phase15-house-listening.zip .
```

## Evidence and reproduction

Artifact `pitch-verification.json` includes multiple dry one-note windows,
independent FFT/period estimates, actual independent-host measurements, exact
synthetic-MIDI counterfactuals, corrected native chord peaks and symbolic overlap
audits. Polyphonic context uses measured per-source offsets, not a guessed
single Goertzel peak. It records minor-second/seventh relationships without
labelling every such interval a mistake. Effects/tails are excluded from the
controlled notes; full-song tails are measured separately.

```bash
python3 tools/phase15_pitch.py --out-dir .local/phase15/new-pitch-gate \
  --plugin .local/phase11/vitalium/usr/lib/vst3/vitalium.vst3 \
  --soundcraft /absolute/path/to/soundcraft-cli
python3 tools/phase15_house.py build --out-dir .local/phase15/new-repair \
  --soundcraft /absolute/path/to/soundcraft-cli \
  --meter-library .local/producer/libebur128.so
```

The optional meter library is explicit; stdlib measurements remain available.
Prepared listening packaging also requires the included pitch report, listening
README and frozen source; the shipped isolated `reproduce.py` is the simplest
complete replay path. No download, account, system install or paid dependency.
`zero_pitch_bend_operations()` also produces strictly scoped typed edits for the
separately tested range-zero workaround; that disables expression and is not
the default repair. Native source JSON is never rewritten to manufacture support.

Final local proof: **377/377 real-host methods pass**, zero failures/errors/skips, **2430.167s**. All **363 earlier methods and files** remain unchanged, with10new unit methods and4new native cases. Focused10unit/3native checks, installed-wheel smoke, actual cross-register/chord DSP, native state/PCM save/reopen and extracted frozen replay with original locations hidden pass. **10132 historical artifact/example files** remain hash-exact. CI Python3.11/3.13 retains all previous workflows and adds installed musical-repair/pitch smoke; exact post-push result is recorded in `artifacts/phase15-house/proof/release-summary.json`.

Raw A/B LUFS **−25.062399/−25.172290**, TP **−4.014405/−4.417381dBTP**, zero clips. Both listening files match **−25.1722902LUFS**, A attenuated **.1098908dB**, B unchanged. Same-input shared-processing bypass changes **3.1047%** relative full-mix PCM RMS. This establishes actual processing, not a quality win. ZIP **61,350,981bytes**, SHA256 **`0466dfb6fcf5f416228031e440e83fdf3562cb0eae437a5561832009afc831b1`**. [Machine verification](PHASE15_VERIFICATION.json) and the artifact reports contain exact controls, pitch windows, note context, measurements and file identities.

GUI/cross-platform operation, arbitrary VSTs/channels, true input-triggered
sidechain and a native master bus remain unverified/unsupported. Matching uses
constant attenuation only. Loudness/true-peak meters are not formally certified.
Correct notes are necessary, not a claim of professional music or a preferred
production. The final musical judgement belongs to human listening.
