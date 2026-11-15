# Cross-Style Kuang House Portfolio — Native Acceptance, November 14, 2026

## Purpose and immutable test contract

Test whether Kuang's currently implemented **one-prompt house template generator** actually generalizes beyond the previously used D-minor deep-house candidate. Do **not** optimize individual songs, adjust their seeds, substitute hand-picked presets, or call metered WAVs professional mixes. Each candidate uses **the same repository commit** `6688efd6060f85eff88ea5e7626ea1f690abe39a`, verified source library, private Vitalium plugin, SoundCraft 0.11.0, CC0 drum pack, and existing bounded conditional source-selection mode.

Three **fresh** 16-bar prompt/seed tests were run sequentially, with a **235-second upper execution bound per case** and **no retries**. The previously completed 96-bar D-minor deep-house track serves as a fourth **context reference**, not as a new contemporaneous prompt within this batch.

No preview mastering was requested for the three new runs: this isolates native source selection, groove structure, sampler/editability, output balance and actual rendering cost. Existing 96-bar work already verified a separate safe offline preview mastering stage.

## Exact fresh inputs

| Style | Prompt | Seed | BPM | User requested bars |
|---|---|---:|---:|---:|
| Straight | punchy straight house in A minor, 125 bpm, 16 bars, no lead, without pad | 41 | 125 | 16 |
| Jackin | funky jackin house in F minor, 127 bpm, 16 bars, no lead, without pad | 83 | 127 | 16 |
| Minimal | tight minimal house in G minor, 122 bpm, 16 bars, no lead, without pad | 97 | 122 | 16 |

All calls used `--groove-template --contextual-shortlist --groove-profile [style] --harmony-profile simple --max-candidates 12 --per-role 2 --timeout 25 --private-third-party-presets` with the same pinned native host and real sample pack, using `--bars 16`. Each was isolated in a separate private workspace. Original source libraries and prior approved music were not changed.

## Results — all three independently passed native technical gates

| Metric | Straight | Jackin | Minimal |
|---|---:|---:|---:|
| Seed | 41 | 83 | 97 |
| Native command exit | **0** | **0** | **0** |
| Wall-clock generation time | **135 s** | **134 s** | **122 s** |
| Original premix integrated loudness | **−31.30 LUFS** | **−25.09 LUFS** | **−30.57 LUFS** |
| Original premix true peak | **−13.34 dBTP** | **−9.20 dBTP** | **−11.50 dBTP** |
| Clipped samples | **0** | **0** | **0** |
| Independently pre-auditioned same-prompt Vital runner-ups | 2 | 2 | 2 |
| Native alternate mixes rendered unnecessarily | 0 | 0 | 0 |
| Native-project canonical SHA and MIDI-byte identity | **PASS** | **PASS** | **PASS** |
| Native plugin preset/source SHA identity | **PASS** | **PASS** | **PASS** |
| CC0 drum manifests and separate open-hat binding | **PASS** | **PASS** | **PASS** |
| No independent melody/lead or unwanted pad | **PASS** | **PASS** | **PASS** |
| Subjective listening quality established | **NO** | **NO** | **NO** |

All had genuine native editable SoundCraft sessions and actual 48-kHz/24-bit stereo PCM renders. The auditable tests also verify correct requested tempo, generated 16-bar four-section structure, source manifests, and no sample clipping or unsafe true peak. This is not a statement of **musical** or commercial master quality.

### Exact selected sources

| Role | Straight | Jackin | Minimal |
|---|---|---|---|
| Vital bass | **Biow Bass 2** | **Biow Bass 2** | **Biow Bass 2** |
| Vital chords | minimal house dub stab 23 | SNFKFutureBounce - Loaded Chords | Pluck |
| CC0 kick | punch-01 | punch-01 | tight-01 |
| CC0 clap | classic-01 | classic-03 | classic-01 |
| CC0 closed hat | closed-01 | closed-02 | closed-01 |
| CC0 open hat | open-02 | open-02 | open-03 |
| CC0 auxiliary percussion | tick-01 | shaker-02 | omitted by minimal profile |

These are private locally available assets. **Do not publish any unknown-license Vital preset states, private WAVs, or absolute private file contents to the public repo.**

## Generalization evidence and important failures of product consistency

**Strong engineering result:** All **3/3 unseen prompt/seed/style combinations** independently completed the bounded 16-bar source-to-SoundCraft pipeline and the strict host/source/audio integrity gate. The previously verified deep-house 96-bar output separately passed full-length native and offline preview-mastering integrity. Together these cover the four targeted *style families*, but represent only **one deep long-form result**, not 96–160-bar acceptance across all styles or seeds.

**Musical/source risk 1 — bass selection collapsed:** All three fresh samples chose the same `Biow Bass 2` patch; the prior deep-house 96-bar output also used it. This is not an automatic defect: one versatile bass patch can be good in many house songs. But it may indicate a strong isolated-audition/semantic score bias and **lack of conditioned source variety**. Do not inject random alternatives or a mandatory diversity quota. Diagnose from the existing audition ranking/feature vectors and compare in context **only when the difference could improve a demonstrated problem**.

**Musical/source risk 2 — mix/loudness spread:** The three independently generated **original premixes** range from −31.30 to −25.09 LUFS, **6.21 LU maximum difference**, while true peak ranges from −13.34 to −9.20 dBTP. All have zero clips and ample headroom, but loudness stability differs materially with selected chord timbre and source dynamics. This is likely a source/mix calibration issue but **does not by itself prove** incorrect balance, bad bass, masking or a worse song. Applying a single master gain cannot fix track-level timbre or relative source balance. The next important engineering diagnosis should measure **existing gain-staging/individual role RMS and instrument-level dynamics**, especially the minimal house stab / Pluck chords, using cheap native source excerpts. Only adjust a general mix algorithm after the specific interaction is reproducibly identified.

**Other limitations:** The first trials use only 16-bar source loops. They do not establish a pro-quality 3–4 minute house arrangement, full mastering, repeated reliability under adverse prompts, a subjective groove winner, or a user-acceptable mix. These three user-unheard private audio files **are not accessible in the chat**; do not ask the user to assess inaccessible VPS paths or claim the assistant heard the results.

## Private reproducibility and evidence

One private batch directory contains the exact pinned inputs, per-prompt logs, native project/MIDI/WAV/source receipts and independent SHA checks:

`/home/User/Kuang/.local/house-portfolio-20261114/`

- `run.sh`: all three bounded original commands, no hidden retries
- `portfolio-run.log`: objective wall-clock exits / timestamps
- `audit.py`: independent native/save/source/audio contract audit
- `portfolio-evidence.json`: machine-readable result and exact selected source identities

These private files remain untracked and outside the public repo. The historical 96-bar private Deep reference remains `/home/User/Kuang/.local/oneprompt-full96-Dm-s73-20261114/`, itself subject to the earlier standalone native and premix/master receipt.

## Stop/go recommendation

**PASS** the **short native technical generalization milestone** for 3 unseen prompts, 3 styles, and the existing fourth-style reference. **Do not pass** the **consistent producer-ready audio** milestone because it has never been human reviewed and the source/gain-stage variability remains significant.

**Do not churn:** Freeze genre research, new arrangement profiles, unrelated diagnostics, arbitrary LUFS targeting, and repeated full-length renders. Highest-value next change: examine existing preset-audition source rankings and native mixer balance for the already-generated straight and jackin songs. If there is a concrete measurable role-specific error, implement **one bounded general fix**, rerun regression tests and only **two fresh representative prompts** to prove improvement. Otherwise avoid replacing a technically working system to optimize metering alone. The final creative evaluation must use user-accessible real audio, not VPS-only paths.
