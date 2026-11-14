# Locked-MIDI House Palette Comparison (private native prototype)

## What this proves

Module: `kuang.house_palette_compare`.

This is a **bounded technical A/B of previously vetted private Vital instrument patches** over precisely the **same original generated house MIDI and drum kit**. It directly tests the general product hypothesis that alternate bass/chord sources can be assessed *without* rewriting the song, instead of letting different keys, arrangements, seed variations and sound sources contaminate comparisons.

- Original source song and alternate donor must both have independently verified SoundCraft native session + exact private Vital state/provenance; they must use the same audited local catalog and identical pinned plugin module hash
- The base song's **MIDI events, velocity, tempo, key, arrangement, original drum sample identities, unchanged instruments, FX, sends, automation and mixer controls** remain exactly preserved
- One source swap per run: `bass` or `chord`, not a blind arbitrary combination; source patches are isolated in private, unknown-license directories
- Each run renders three real isolated native role stems and a full alternative 16/32-bar mix, verifies native save/reopen and PCM/true-peak integrity, and computes beat-aligned compatibility from actual kick MIDI ticks, sub-band phase summation, mono fold-down, transient shape and frequency-resolved spectra
- Creates a **sample-aligned, attenuation-only LUFS-matched** A/B pair; never judges preference by gain or waveform. Output is new/private, and original files are unchanged before the report publishes
- `technical_status=PASS` means no *implemented technical* contraindications were detected. It is **not** a professional-mix approval, a musical ranking or validation of another genre. `subjective_winner: null` is mandatory

The protocol only accepts 16/32-bar source sessions to avoid repeatedly rendering four-minute songs for each candidate. It is a controlled engineering baseline from previously successful presets; **not yet a complete automatic search over arbitrary new source combinations.**

## Reproducible examples

```bash
cd /home/User
export PYTHONPATH=/home/User/Kuang-groove-harmony
HOST=/home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli
ROOT=/home/User/Kuang/.local/kuang-generalization-batch-20261113

python3 -m kuang.house_palette_compare \
  --base "$ROOT/deep-Dm-124-s17" \
  --alternate "$ROOT/jackin-Fm-126-s23" \
  --swap bass --soundcraft "$HOST" \
  --out-dir "$ROOT/new-private-baseline-bass-A-B" \
  --library /home/User/Kuang/.local/producer/libebur128.so
```

Changing `--swap bass` to `--swap chord` changes only the selected chord Vital preset; the code preserves the original song's **D-minor** MIDI events rather than transposing it to the donor session's F-minor key.

## Actual native validation, November 13, 2026

First measured pair uses a D-minor/124-BPM/16-bar original *deep house* track with exactly its original kick, chord and licensed five-drum CC0 kit. The original **Biow Bass** patch is replaced with the independently runtime-auditioned **LD Bass** patch from a *different* F-minor/126-BPM house seed.

| Metric | Original Biow Bass | Replaced LD Bass, same project |
|---|---:|---:|
| Entire original MIDI note events / arrangement / key | fixed | **identical (verified SHA)** |
| Native session save/reopen | previously passed | **passed, canonical SHA verified** |
| Integrated premix loudness | −25.651 LUFS | **−25.619 LUFS** |
| Bass energy at kick vs between beats | −10.316 dB | **−6.481 dB** |
| Hypothetical linear kick+bass sub interaction | +0.061 dB | **+0.123 dB** |
| Full-mix mono-fold-down sub loss | ~0 dB | **~0 dB** |
| Fit warnings | none | **none** |

The alternate was not clipped or unsafe in measured true-peak checks. Both aligned A/B WAVs were generated and verified at the same LUFS, yet **no subjective winner was selected**. The baseline and alternate had almost equal integrated loudness despite materially different beat-aligned bass dynamics; this is useful context-fit evidence not reducible to a volume comparison.

Private result: `/home/User/Kuang/.local/kuang-generalization-batch-20261113/deep-Dm-locked-LD-Bass-20261113/`.

### Second controlled source comparison: chord sound

With the **same deep-house D-minor MIDI**, Kuang replaced only `SNFKFutureBounce - Loaded Chords` with the independently verified `minimal house stab 09` patch while retaining the original bass, all five drums, sections, and mixer settings. The real 16-bar native render saved/reopened correctly, passed source-fit and clipping checks, and yielded an attenuation-only matched A/B. Its integrated premix changed **from −25.651 LUFS to −30.772 LUFS**, a **−5.121 LU** difference with identical notes and faders. This demonstrates why preset interchangeability must not be assumed from isolated plugin validation alone. No subjective winner was selected.

Private result: `/home/User/Kuang/.local/kuang-generalization-batch-20261113/deep-Dm-locked-minimal-stab-20261113/`.

The first actual chord experiment preceded the level-mismatch warning; its original immutable receipt says technical PASS on the implemented clipping/source-fit conditions. The updated comparison engine now adds **`large_premix_loudness_change_same_locked_midi`** as an explicit `REVIEW` flag when a replacement shifts integrated loudness by more than 3 LU with identical MIDI and mixer controls. **This is not an automatic rejection or a claim of worse artistic quality**—it is a reason to compare the sources at equal level and examine their differing timbres before selecting one for a full-length song.

## Product-readiness interpretation

The **generalized comparison technique works**. It provides a foundation to compare multiple source choices against the *same locked composition*, pre-screen hard technical failures and retain source provenance. It has a bounded candidate cost; it does not select a favorite sound based on one proxy.

Further work should make this a **program-level selection policy**, not a fixed donor song hack:

1. Evaluate 2–3 independently verified bass/chord candidates per role using the same short groove, perhaps with several drum-kit options, but cap the maximum total render evaluations
2. Fail closed on real phase cancellation, mono low-end loss, pitch/plugin mismatches and clipping; allow legitimate house-style dynamics to vary
3. Use real signal energy, attack, rhythmic density, chord spectral placement and genre requirements to form **auditable alternatives**, not an uncalibrated aggregate quality score
4. Cache verified source/plugin identities, process/reuse identical unaffected stems when possible, and perform the expensive full-length render **once** after accepting a source configuration
5. Keep the user's final creative listening decision separate and **deliver actual playable audio in chat**; the user cannot listen to private VPS-only render paths

**Do not copy or publish the patch contents:** third-party Vital states are license-unknown and remain in isolated, user-owned private directories. The GitHub PR contains only original analyzer code, tests and documentation. The approved older Phase43/44 song is untouched.
