# External House audio reference audit (opt-in, local only)

**Status (2026-11-16):** Source catalog and offline analysis CLI delivered. **No external audio archives were downloaded or auditioned and no empirical quality pass is claimed.** This is an additive measurement utility, not a new production default or a license to bundle third-party audio. It complements the existing `tools/audio_fingerprint.py` and the private Phase44/ten-song section comparison; those references and all historical failures are unchanged.

## Source inventory

`HOUSE_AUDIO_REFERENCE_CATALOG.json` separates three MusicRadar sample collections (371 + 267 + 338 = **976 advertised files**, **729 MB** total advertised archive sizes) from Cambridge's 20-track, single-song multitrack and Fraunhofer's generic drum-isolation evaluation set. Counts are **not independent track/sample counts**. Processing treatments, constituent layers and multiple files from the same kit are correlated observations. Source statements are publisher claims; format, fidelity, licenses and acoustic quality remain unaudited until the relevant audio is checked. Read the per-source usage conditions at the original pages. Neither MusicRadar royalty-free status nor free Cambridge downloads permit us to redistribute files or assume generative-AI-training rights.

## Measure local WAVs

Keep any legitimately acquired WAVs under ignored `.local/house-references/` on the authorized machine. **Do not commit or upload them.** Verify licensing/permission for the proposed activity before acquiring or analyzing a restricted collection. The instrument/production sample importer is a different workflow and only accepts certain redistributable licenses; do not misrepresent these packs as CC0 or repackage them into Kuang native asset ZIPs.

From the repository root (no third-party dependency required):

```bash
python3 tools/house_reference_collection.py \
  --input-root .local/house-references/vintage/kick \
  --source-id musicradar-vintage-house-techno-371 \
  --role kick --group-id vintage-kit-A \
  --out .local/house-references/reports/vintage-kick-a.json
```

`--role` is **an explicit user label**, not inferred automatically from filenames. Group comparisons should be performed on directories of homogeneous source roles. Use `--role drum_loop --loudness` or `--role mix --loudness` for files containing enough continuous audio to calculate approximate gated integrated LUFS and true peak; this uses Kuang's existing stdlib BS.1770-style meter and is slower. Short one-shots do **not** receive misleading LUFS targets. `--max-files` defaults to 50 (up to 2000 explicitly) to avoid blindly processing large archives; an over-limit input fails rather than sampling selectively. Invalid files are reported as rejected; the CLI writes the report, then exits nonzero. Never put `--out` under the input tree, never overwrite a previous report, and never publish raw audio through this tool.

The output includes relative paths only, WAV SHA-256, format, RMS/peak dBFS, crest factor, digital clip counts, band-power fractions, dominant **spectral bin** within 30–150 Hz (not an asserted kick fundamental), and optional non-certified loudness/true-peak metrics. Zero-data or shorter-than-2048-frame sources have null spectra. Spectral resolution is explicitly reported as `rate / fft_size`; 20–40 Hz estimates from very short windows are poor. For credible kick fundamental or tail-pitch trajectories, a separate sufficiently long event-aware estimator must be validated. Frequency-band fractions cannot be used interchangeably with a calibrated PSD or physical sound pressure.

**No automatic musical winner:** the report is descriptive. Files may be production layers, processed samples or artist multitracks rather than mastered reference tracks. Comparing differently mastered tracks, differing gain stages or different roles is not an acceptance test. Only select independent kit/song groups for group-level distributions; avoid reporting 976 independent professional examples. Ratings require human audition and role-in-context A/B, not peak/RMS maximization. Do not train any model on these WAVs without a separate affirmative rights audit.

## Qualification gates before a professional reference claim

1. Reconfirm publisher terms and any contributor permissions for the actual use. Retain source URLs, release/version, pack and kit identities.
2. Verify all archive bytes and per-WAV identities, decode errors, sample formats, silence, clipped PCM, and high-frequency bandwidth; inspect concerning files directly.
3. Compare like roles and processing stages. Establish independent kit/song groups, minimum number of examples, and avoid treating Neutral/Tape/Room/Comp as independent songs.
4. Measure loop/full-mix loudness separately from event-window kick attack/tail features. Level-match only for listening copies, retaining untouched originals and method settings.
5. Publish only permitted metadata or aggregate measurements; preserve raw source audio locally. A source does not become an approved production sample simply because it measures similarly to a commercially successful reference.

## Checks and scope

`python3 -m unittest tests.test_house_reference_collection -v` exercises a synthetic mono kick, stereo loop loudness, short-sample abstention, source validation, non-overwriting and symlink defenses. CI runs the full repo suite on the feature branch; none of the tests need commercial audio. The utility neither downloads samples nor modifies SongSpec, VST/preset selection, mix/master defaults or existing `.local` reports.
