# Bounded house palette shortlist: identical-MIDI native comparison

**Status:** reusable *technical* candidate triage; **not an automatic artistic quality selector**. The source project, verified proprietary Vital patch states, and user-approved references remain private and unchanged. The user is not being asked to listen to inaccessible VPS audio.

## Product engineering contract

Kuang should not have to choose a bass/chord preset because it scored highest in isolation. The new `kuang.house_palette_shortlist` constructs a small, strictly bounded list of independently audited private Vital patches and tests each against **one fixed house groove**. It accepts a maximum of **three alternatives**, each expressed as a role (`bass` or `chord`) and a previously verified private donor session. Bass, chord, drum, key and arrangement from the donor song are **never** imported—only its chosen Vital preset state.

Prior to any render, the planner verifies donor catalog identity, plugin binary identity, independently audited source preset hashes, differences in the requested role, exact canonical substituted-project identity and a unique selected source per role. Existing hash-verified A/B results may be reused to reduce CPU cost; otherwise an independent SoundCraft source-specific 16/32-bar comparison runs serially. No 128/160-bar render is allowed in this evaluation phase.

Each comparison enforces:
- identical source MIDI and section boundaries, tempo, key, drums, mixer, unchanged instruments, FX and automation;
- genuine native SoundCraft alternate session save/reopen and 48-kHz/24-bit WAV, no clipping or unsafe measured true peak;
- kick-timed bass activity, hypothetical sub-band summation, mono fold-down, FFT role spectra, source and donor hash stability;
- **attenuation-only matched-loudness A/B**, so louder is not automatically judged better;
- no subjective winner or unlicensed preset redistribution.

The result is classified as **TECHNICALLY_ELIGIBLE**, **REVIEW**, or **REJECT**. REVIEW includes a significant same-MIDI loudness shift over 3 LU or a source-fit advisory warning. REJECT is reserved for the currently implemented severe low-frequency cancellation/mono-loss signals or unsafe true peak. These thresholds are **engineering heuristics**, not a validated psychoacoustic preference standard, and the baseline remains the deterministic fallback, even if an alternative is technically eligible.

The output includes `shortlist-evidence.json` and, for newly rendered candidates, their privately stored native A/B evidence. Cached comparisons remain referenced to the prior private authorized files and are never duplicated into a public repo. No expensive whole-song reconstruction or full 4-minute render is performed during this phase.

## Reproducing the actual shortlist

```bash
cd /home/User
ROOT=/home/User/Kuang/.local/kuang-generalization-batch-20261113
export PYTHONPATH=/home/User/Kuang-groove-harmony
python3 -m kuang.house_palette_shortlist \
  --base "$ROOT/deep-Dm-124-s17" \
  --donor "bass:$ROOT/jackin-Fm-126-s23" \
  --donor "chord:$ROOT/jackin-Fm-126-s23" \
  --donor "bass:$ROOT/minimal-Gm-122-s31" \
  --existing "1:$ROOT/deep-Dm-locked-LD-Bass-20261113" \
  --existing "2:$ROOT/deep-Dm-locked-minimal-stab-20261113" \
  --soundcraft /home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli \
  --library /home/User/Kuang/.local/producer/libebur128.so \
  --out-dir "$ROOT/a-new-private-technical-shortlist"
```

The example contains **one original D-minor 124-BPM fixed groove** and three source alternatives across two roles. The independent donor originals differ in key/tempo/style/seed, demonstrating that only verified sound sources, not musical content, transfer between songs. Two already measured comparisons are cached with source/audio hash checks; at most one new native alternate is rendered.

## Verified native production matrix — November 13, 2026

The shortlist program was run against **two different base compositions** (not just two donors). Both use independently audited and source-hashed private Vital presets with real licensed CC0 sampled drums, and each generated alternative retained the base groove's exact MIDI, key, FX and arrangement:

| Base style, key / tempo | Only changed preset | New native render? | LUFS shift | Technical disposition |
|---|---|---:|---:|---|
| Deep, D minor / 124 BPM | Bass: LD Bass | Cached, SHA-verified | +0.033 LU | **TECHNICALLY_ELIGIBLE** |
| Deep, D minor / 124 BPM | Chords: minimal house stab 09 | Cached, SHA-verified | −5.121 LU | **REVIEW** (level change >3 LU) |
| Deep, D minor / 124 BPM | Bass: Biow Bass 2 | **Fresh native + actual A/B** | +0.01 LU | **TECHNICALLY_ELIGIBLE** |
| Jackin, F minor / 126 BPM | Bass: gentle pluck bass | **Fresh native + actual A/B** | −0.25 LU | **TECHNICALLY_ELIGIBLE** |

The new Biow Bass 2 change yielded a bass near-kick versus between-beat ratio of **−1.443 dB** and kick+bass linear sub-band summation of **+0.266 dB**; the jackin replacement measured **−5.554 dB** and **−0.539 dB** respectively. Both preserved measured mono-sub energy, passed native reopen and render safety checks, and produced verified loudness-matched audio. Neither has been subjectively reviewed.

The deep-house program evaluated **3 options** with just **1 new native alternate render**, because two audited A/Bs were reused without changing any original private source. The jackin program evaluated **1 option**, requiring **1 new native alternate render**. The combined technical statuses were **3 eligible, 1 review, 0 rejected**, and **0 automatically chosen musical winners**.

Private evidence files:

```
/home/User/Kuang/.local/kuang-generalization-batch-20261113/deep-Dm-technical-shortlist-v1/shortlist-evidence.json
/home/User/Kuang/.local/kuang-generalization-batch-20261113/jackin-Fm-technical-shortlist-v1/shortlist-evidence.json
```

These records establish the **operational feasibility, source-varying measurements and bounded CPU behavior** of short-excerpt alternative screening. They do not prove any candidate sounds better than the original. Human feedback is not required for internal engineering checks, and the user cannot listen to VPS-only files.

## Limitations

This is a *first usable bounded evaluator*, not the complete automatic sound selection in the one-prompt generator: selecting the source candidates still uses previously validated external audition sessions. A future integration should generate/evaluate several candidate presets during the **same user prompt**, cache their native audition artifacts, compare them within one locked generated groove and only render the final full song once.

The technical flags cannot detect all instances of ugly timbre, weak groove, too much chord reverb, or unsuitable drum sound. A large level shift can be legitimate; a zero-warning low-end comparison can still sound poor. Use measured receipts to exclude objectively unsafe combinations, then validate practical listening quality on a small *accessible* collection of user-reviewed examples—not an invented numeric quality score.
