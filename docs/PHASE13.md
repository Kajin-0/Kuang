# Phase13 — a complete sampled drum palette in the preferred full song

Baseline: clean **b32f2eb3725d1655cc53447bfaa4a0b047ec0a63**, full Phase10 D,
**64 bars / 126 BPM / C minor / six sections**. The user preferred this music
to Phase11 and did not hear a clear benefit from the Phase12 eight-bar study.
This release changes the actual drum sources across the complete record. It
does not replace the bass, stabs, hook, pads, sine pulse or musical arrangement.
All **1536 original note IDs, pitches, velocities, channels, durations and
clip-relative/absolute positions** survive. Original SongSpec remains provenance.

## Listen to the record

One download: **`artifacts/phase13-house/phase13-house-listening.zip`**, about
59.4 MB. Its `listening/` folder has exactly two complete 48k/24bit stereo WAVs:

- `A-Phase10-original-full-LUFS-matched.wav`
- `B-Phase13-sampled-drums-full-LUFS-matched.wav`

Both last **126.9047708 s**, including the original five-second release window.
Their integrated loudness is **−25.0623993 LUFS**. A receives **−.0121078 dB**
constant attenuation; B receives none. No limiter, new master, EQ or compression
is applied to the listening WAVs. Raw native A/B are labelled at the release root;
raw A is byte-identical to the untouched Phase10 D recording. This deliberately
does not chase the different Suno song's LUFS or copy its vocals/audio/motifs.

```powershell
scp User@YOUR_VPS:/home/User/Kuang/artifacts/phase13-house/phase13-house-listening.zip .
```

This is the user's explicitly requested **unreviewed full-record A/B**, not a
fabricated preferred review. The incumbent remains Phase10 pending listening.
The generic producer preference ledger and its promotion guard are unchanged.
Internal stems and bypass experiments are verification material, not listening
homework, and are excluded from this ZIP.

## Actual sources and independent license audit

The separately cloned [octal-samples repository](https://github.com/octalmusic/octal-samples/tree/22d222ce36e290ba3792c776811aa9c69dcc8776)
is pinned to **22d222ce36e290ba3792c776811aa9c69dcc8776**. Its [CC0 dedication](https://raw.githubusercontent.com/octalmusic/octal-samples/22d222ce36e290ba3792c776811aa9c69dcc8776/LICENSE)
and [per-file origins/processing](https://raw.githubusercontent.com/octalmusic/octal-samples/22d222ce36e290ba3792c776811aa9c69dcc8776/LICENSES.md)
were inspected alongside the manifest, generator and relevant kick/hat/clap/
percussion DSP. No npm script, dependency install or generator was executed.
All **44 committed WAV identities**, their formats and **24 reviewed source/
license/manifest file hashes** are checked by `octalsamples.inspect_pack()`
against the small reviewed catalog shipped in `kuang/data/`.

This is a small new repository. CC0 and descriptive tags do not establish
professional quality, actual listening curation or authenticated ownership.
The selected sounds are the publisher's **original synthesized one-shots**,
not recordings of vintage drum machines. The source code corroborates seeded
synthesis without sampled external inputs for these six voices. Authorship
remains a publisher declaration, not a legal chain-of-title guarantee.

The pack's unused ride/crash derive from [uzu-drumkit](https://github.com/tidalcycles/uzu-drumkit/tree/2f3e05c70ab4d73ad053a1467adec89bd27377a0)
under [The Unlicense](https://raw.githubusercontent.com/tidalcycles/uzu-drumkit/2f3e05c70ab4d73ad053a1467adec89bd27377a0/LICENSE).
Its two original source WAVs and license were independently fetched from that
pinned upstream and match the pack's local copies and published SHA-256 values.
They are **not used or redistributed** here. The listening bundle includes
the six actually selected original WAVs, converted assets, publisher license,
per-file processing/attribution and complete native `Audio Files` closure.
No factory presets, plugin binary, copyrighted reference recording or GPL
implementation is bundled with MIT Kuang.

All source WAVs are mono **44.1 kHz PCM16**. Explicit conversion uses the
public API of separately extracted [libsamplerate 0.2.2](https://github.com/libsndfile/libsamplerate),
**BSD-2-Clause**, `SRC_SINC_BEST_QUALITY`. The 1,343,954-byte Ubuntu package
`libsamplerate0_0.2.2-4build1_amd64.deb` matches the repository metadata SHA-256
`8a389d1cae81860c9fb7cd9641c3f9d38815e80c0379b3181b4317489126f738`.
It is extracted only in `.local/phase13/resampler/`, with no system install.
The library is neither bundled nor needed to render/replay prepared projects.

Conversion produces **48k PCM24**, with explicitly recorded **−12 dB source
headroom**, no normalization/dither/retuning, and 256 zero input drain frames
to retain interpolation tails. This container does not invent source resolution.
Original, converted and normalized host float32 PCM hashes travel with each
asset. A first trial with only −3 dB source headroom produced **50 clipped
sample values** through the inherited kick path and was rejected. The final
source gain and separately calibrated native sampler trims keep zero clips;
no hidden waveform master fixes the result.

Actual stereo 1/18 kHz analytical conversion errors are about **5×10⁻⁸ RMS**;
the tested 21.9k image is below the **−95 dB** acceptance limit. A 50ms impulse
stays at frame2400 after conversion, and repeated PCM is exact. These are
specific conformance checks, not universal/formal resampler certification.

## Selection and musical balance

Three complete source sets—**punch, round, tight**—were rendered in the actual
64-bar composition. Their raw integrated readings were **−25.0948 / −25.2323 /
−24.7727 LUFS** after controlled role-level calibration. They are source
alternatives, not automatic quality rankings. `selection.json` records the
full-song measurements, chosen hypothesis and rejected first trial.

The chosen set avoids the longest kick/roomiest clap and the hardest short
kick/brightest clap combination. G1 is a fifth of the existing C-minor bass
root; it is the sample's natural tail pitch, not a rewritten MIDI note. Darker
metallic closed hats provide a separate articulation from the open-hat wash.
The selected sources and **native** level controls are:

| Role / original trigger | CC0 source | Native sample level | Articulation / balance |
| --- | --- | ---: | --- |
| Kick36 | `house.kick.punch-02` | −3.339804 dB | Natural G1,85ms body time constant; same isolated drop RMS within .04dB |
| Clap39 | `house.clap.classic-01` | −9.918617 dB | Three separated bursts,60ms tail constant; same old backbeat balance |
| Ghost snare38 | `house.snare.snap-01` | −8.058021 dB | Original note gate +35ms release;1dB below old role |
| Closed hat42 | `house.hat.closed-06` | −4.663100 dB | Darker metallic bank;2.5dB above previously buried closed-hat role |
| Open hat46 | `house.hat.open-01` | −7.208790 dB | Original note gate +70ms release;1dB below old wash |
| Percussion44 | `house.perc.shaker-02` | −18.376444 dB | Existing shuffled onsets/left pan;3dB above old quiet tick role |

All sample patches use **.1ms attack,1ms decay,100% sustain,100% velocity
sensitivity**; original MIDI velocity accents remain. One-shots ignore
MIDI note-off; snare/open-hat patches explicitly
use gate mode. These are editable native controls, not rendered full-track stems.

The kick is **fuller-bodied, not objectively more sharply attacked** than A.
Actual MIDI-onset mean squares A→B are **.021388→.011978** at0–20ms,
**.003747→.005246** at20–100ms and **.0000640→.0006408** at100–220ms. This
redistributes energy toward body/late decay at essentially unchanged stem
level. It can improve perceived weight or produce unwanted masking; the
musical preference remains unknown. The measured broad20–120Hz kick/bass
interference is **+.0109→−.0196dB**, not an oscillator-phase calibration.
No full-range sub boost or ideal spectral target is asserted.

## Editable partition and preservation

`drum_palette.split_by_pitch()` is an explicit new-export operation. Clap39
and closed-hat42 retain the old track/device/clip IDs. The secondary snare38
and open-hat46 receive deterministic `.p38`/`.p46` identities; **note IDs never
change**. Empty projected clips retain timing, and the provenance receipt
records original tracks, original automation and every note's partition.
The type-1 MIDI track count changes; independently parsed note-on/off multisets
are exact. This is not falsely claimed byte-identical whole MIDI.

All source FX, faders, pans and automation are projected faithfully, including
cloned device lanes and point shapes/endpoint values. No note or full signal
is duplicated between roles. These are per-role insert copies, **not a summed
drum bus**. General sends/buses, parallel drum compression and true input-triggered
sidechain remain unsupported by this adapter. No bus rewrite blocks the song.
The original timed ducking and FX gestures remain. Locked tracks/children,
uncovered pitches, identity collisions, sends/non-master routing and unsupported
instrument automation fail closed before publication. Original files stay intact.

The open-hat envelope ends at least **23.254ms** before the next closed onset
with the actual MIDI. A same-note/same-source control measures the gate tail
**−139.109dBFS** versus **−42.972dBFS** for one-shot,100–220ms after note-off.
There is no claimed cross-track choke, SFZ multi-zone, round robin or velocity
layering. Source choice can change perceived phrasing despite identical MIDI;
this remains a listening question, as Phase11 demonstrated.

## Reproduce and verify

The ZIP contains canonical/MIDI and native A/B, original SongSpec, relative
licensed media, recipe, SHA inventory and Kuang's own frozen MIT source.
Its actual extracted `python -I reproduce.py` is tested with the original
sample library, source checkout and original B native directory hidden.
It reproduces raw B byte-for-byte without pip, libsamplerate or external
source locations. Python3.11+ and separately installed SoundCraft0.11.0 remain
required. GUI operation itself is untested on the headless VPS.

To prepare the source library afresh, manually obtain the pinned repository
in `.local/phase13/octalsrc` and supply an explicit reviewed converter:

```bash
mkdir -p .local/phase13/tmp
export TMPDIR="$PWD/.local/phase13/tmp"
python3 tools/phase13_house.py --prepare-library --pack .local/phase13/octalsrc \
  --converter-library .local/phase13/resampler/unpacked/usr/lib/x86_64-linux-gnu/libsamplerate.so.0.2.2 \
  --out-dir .local/phase13/my-library
python3 tools/phase13_house.py --source artifacts/phase10-house \
  --pack .local/phase13/octalsrc --library .local/phase13/my-library \
  --selection artifacts/phase13-house/selection.json --out-dir .local/phase13/my-release \
  --soundcraft /absolute/path/to/soundcraft-cli
```

The default meter is validated stdlib code; `--meter-library` can explicitly
select the existing reviewed libebur128 reference. No tool/test downloads
anything automatically. New destinations are required. Source/library overlap,
unsupported mappings, stale assets, clipping and truncated releases reject.

Raw A/B: **−25.050292 / −25.062399 LUFS**, **−5.339738 / −4.014405dBTP**,
crest **21.7158 /23.0039dB**, RMS **−27.0555 /−27.0286dBFS**, zero clips.
The same independently rendered musical stem plus two drum groups reconstructs
each full mix within **2 24-bit LSB**. Full native state and repeated PCM are
exact on save/reopen. Final250ms is digital zero. Whole-file high-band side
fraction is **5.2521→4.9619%**: slightly narrower, not a width improvement.
Low-band mono retention is **99.999991/99.999992%**; mono RMS loss is about
**.0711/.0707dB**. Breakdown/drop RMS contrast remains about12.4/12.3dB,
with all original section notes and markers exact.

`verification.json`, `production.json`, `selection.json` and internal diagnostic
records provide the measured transcript. [PHASE13_VERIFICATION.json](PHASE13_VERIFICATION.json)
and [STATUS](STATUS.md) record final regression, wheel, preservation and CI results.
Human full-song listening must decide whether B improves the recording. No
studio/professional/club-readiness or certified-meter claim follows from tests.
