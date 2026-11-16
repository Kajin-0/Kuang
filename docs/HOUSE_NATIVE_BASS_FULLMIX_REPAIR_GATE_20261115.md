# Kuang: automatic bass-source full-mix repair gate — November 15, 2026

## Motivation and scope

Producer prioritizes kick/bass physical impact, offbeat syncopation, and rejection of unpleasant growling sources. No intermediate listening requests. Prior code detected an isolated native bass MIDI-onset fault and could switch to a verified pluck, but it did **not** require a prospective alternate to actually improve the **rendered combined mix**. This could overpromote a patch that passed note attack while masking the kick, losing offbeat energy, or disrupting the low-band balance.

New independent deterministic gate: `kuang/house_bass_fullmix_repair_v1.py`. Integrated with the existing opt-in `--native-bass-onset-rescue` in `kuang/house_one_prompt_context.py`; there is **no default selection change**.

The source must have a real, verified hard attack fault. For one independent vetted candidate with locked MIDI/kick/FX/pads/chords:
1. Its real native SoundCraft project must save and reopen with exact canonical identity, and its actual native render must be nonclipped and below the -1 dBTP peak safety ceiling.
2. Candidate isolated actual-MIDI-aligned note onset must clear all hard technical faults. Independent native phase/mono compatibility and excessive loudness-change checks remain mandatory.
3. The candidate source SHA256 must not appear in the user-rejected source registry.
4. On real complete source and alternative Groove WAVs at identical tempo, kick positions and section, calculate the existing *25–90 and 90–250 Hz* first-100ms kick versus 200–300ms offbeat full-mix power ratios. Require **at least 1.0 dB reduction in both bands**. This is a deliberately conservative experimental technical *repair screen*, not a perceptual quality optimum or a universal Phase44 reference level.
5. Reject or fail closed when any requirement fails, preserving the incumbent/artefacts and reporting the cause; no automatic musical winner or claimed professional quality.

A passing alternative is a technically justified resolution to a measured defect in this specific source context. No favorite preset, style, or fader value is inferred. Deep/jackin sustained-context rules remain opt-in; any deferred review flag is not silently treated as a pass. These thresholds require future validation on many independently judged songs.

## Fresh end-to-end private native test: same-song 122 BPM minimal F-sharp minor

A new independent one-prompt 16-bar SongSpec run was performed under the real private vetted Vitalium 1.0.6 and SoundCraft 0.11.0 hosts with the existing audited Octal CC0 drum kit, source policy, groove identity V2, musical plan V2 and producer-preferred four-bar coherent chord treatment. All original reference sessions were preserved. The separate private result directory:

`/home/User/Kuang/.local/source-policy-fullmix-gate-minimal-Fsharp-20261115`

The initial bass source failed the actual-note-onset severe mask check. The algorithm considered one vetted runner-up and selected **gentle pluck bass** only after the real native save/reopen, isolated-onset, source veto, phase/mono, loudness, peak/clipping **and new comparative full-mix improvement gates** passed. Its chord remained **minimal house dub stab 23** and its pad **minimal house pad 2** (the final complete source selection is independently recorded; do not confuse this with the earlier Strings of Cygnus session).

| Full-mix beat/offbeat power ratio | Initial source | Rescued source | Relative reduction |
|---|---:|---:|---:|
| 25–90 Hz | +24.494 dB | +12.064 dB | **12.430 dB** |
| 90–250 Hz | +18.507 dB | +6.458 dB | **12.049 dB** |

This is a strong objective offbeat-energy improvement under the exact same song MIDI, not a subjective groove score. Comparison result `TECHNICAL_REPAIR_ELIGIBLE`; source veto `null`; candidate isolated hard faults `[]`. Chords were not automatically reselected during bass repair.

Final native WAV: **43.475417 s**, 48-kHz stereo 24-bit PCM, **-27.705826 LUFS-I**, **-5.204235 dBTP** and **0 clipped samples**. The canonical native save/reopen check passed. Production result quality remains `unreviewed; no professional audio quality established`.

Full reproducible private receipts:
- `context-shortlist-evidence.json`, including `bass_onset_baseline_fullmix_pocket` and `native_fullmix_bass_repair`;
- `groove-pocket-evidence.json`, `palette/selection.json`, `report.json`, native session and `preview.wav`;
- no private Vital preset bytes or WAV assets published in Git.

## Test policy and stop gate

`tests/test_house_bass_fullmix_repair_v1.py` covers a correct technical rescue, producer veto superseding gains, inadequate/offbeat-worsening changes, active onset and mono faults, unverified native state, mismatched kick timebase and corrupted/silent metrics. Companion existing native-source, bass-onset and autonomous integration suites must pass before promotion.

This milestone is **source-context technical validation only**. Do not claim the whole track is professional or ask the producer to approve short A/B files. Next work should generalize native source and contextual comparisons across independent keys and bass roles, including negative/no-improvement cases, before attempting a complete final House track quality audit.

## Bounded real native cross-style expansion: independent source-swap A/B

The source-aware gate was independently evaluated against two further **existing real native 16-bar SoundCraft productions** with different tempi, keys, arrangements and drum sounds. These two are *controlled replacement experiments*, not fresh one-prompt generations; the fresh end-to-end minimal-F♯ case above remains the sole one-prompt case in this milestone.

The verified, previously selected `gentle pluck bass` Vital source from the fresh minimal song was applied as a *single* bass-source replacement to deep E and jackin G. The source `Biow Bass 2` was the original in both. Other canonical tracks, kick/drums, chord-B note timing, bass MIDI note onsets, pitches, durations, velocities, faders and effects stayed identical; all source presets remained on the private VPS. Before any selection, the real original native onset stems confirmed a hard attack deficit in each source. Both candidates passed actual native export, save/reopen, full 48-kHz/24-bit rendered WAV, zero clipping, true peak safety, separate bass stem MIDI-onset measurements, and fullmix phase/mono warning screens. Both original sources and the replacement source were inventoried before and after.

| Native, source-locked real case | Initial bass-onset fault | Replacement fault | Fullmix 25–90 Hz ratio improvement | Fullmix 90–250 Hz ratio improvement | Complete LUFS A / B | Gate |
|---|---|---|---:|---:|---:|---|
| Deep E, 123 BPM | Yes | None | **2.738 dB** | **1.210 dB** | −23.432 / −23.453 | Technical eligible |
| Jackin G, 127 BPM | Yes | None | **1.425 dB** | **4.561 dB** | −28.044 / −28.206 | Technical eligible |
| Minimal F♯, 122 BPM (fresh one-prompt) | Yes | None | **12.430 dB** | **12.049 dB** | Complete final −27.706 LUFS | Technical eligible |

**Important refinement:** reducing onbeat/offbeat ratio is not enough if this occurs by attenuating the kick. Each candidate now also needs a **≥1.0 dB increase in ABSOLUTE offbeat band power** in each band and **no more than 1.5 dB loss in near-kick band power**. The gate uses the independent native `near_mean_power` and `offbeat_mean_power` measurements and checks that these reconcile with the reported band ratio within 0.01 dB. The source preserves the kick MIDI and sampler; this final waveform condition protects against bus-level changes.

| Real source swap | Absolute offbeat 25–90 / 90–250 Hz gain | Near-kick 25–90 / 90–250 Hz change |
|---|---|---|
| Deep E | +2.570 / +1.101 dB | −0.169 / −0.108 dB |
| Jackin G | +1.112 / +4.209 dB | −0.314 / −0.352 dB |
| Minimal F♯ one-prompt | +21.374 / +20.327 dB | +8.944 / +8.277 dB |

These are **signal energy measurements**, not human groove ratings. The minimal source's near-kick energy increased strongly despite the same kick source, so this result must *not* be taken as evidence that the kick itself became stronger or that bass/kick masking is subjectively optimal.

### Negative controls and quality safeguards

The earlier **real native gain-only deep E +3 dB trial** had only 0.507/0.117 dB improvements in the two relative beat/offbeat ratios, with only 0.701/0.211 dB absolute offbeat increases. Even in the intentionally favorable **counterfactual assumption** that its isolated onset hard fault cleared (not measured for this control), the fullmix reviewer rejected it as `REJECT_NO_MEANINGFUL_FULLMIX_OFFBEAT_REPAIR`. It is **NOT** a real preset swap or an end-to-end repair, and should never be labeled as one. This makes explicit the earlier determination that gain-only is not the right lever for every source.

Separately, synthetic adversarial unit cases explicitly reject (i) a seemingly improved ratio achieved by reducing both near and offbeat energy, (ii) a near-kick energy collapse greater than 1.5 dB even with absolute offbeat gain, (iii) inconsistent reported ratio versus power, (iv) any producer-vetoed source identity, (v) unresolved sustained-source review, (vi) mono/phase faults, (vii) remaining onset faults, and (viii) stale or missing native provenance.

The quantitative native receipts from all three source contexts, plus the exact **negative real WAV-derived spectra**, have been preserved as a **no-private-audio numeric regression fixture**:
`tests/fixtures/house_bass_native_fullmix_crossstyle_20261115.json`.
The fixture documents its negative source as a gain-only counterfactual and contains no redistributable or license-unknown Vital source bytes.

All private real native WAVs, session files, and full evidence JSON remain separately under the VPS:
`/home/User/Kuang/.local/bass-fullmix-source-crossstyle-20261115/`,
`/home/User/Kuang/.local/bass-audio-cross-style-20261115/`,
and the original fresh minimal one-prompt directory. None are published externally.

**Exit decision:** the fullmix technical repair gate now has a verified source-locked positive example in **three different House styles**, explicit negative examples, and waveform-level anti-metric-gaming tests. It still does not assert that Kuang understands or can independently guarantee the aesthetic quality of House music. The producer-rejected growling source remains vetoed, and the new gate remains **opt-in with default generation unchanged**. A wider independent multi-seed production-batch evaluation and reference-calibrated source/articulation scoring are required before promoting this to the standard one-shot creator. No intermediate human audition is requested.
