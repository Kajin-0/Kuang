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
