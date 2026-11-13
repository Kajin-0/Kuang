# Real-source house template integration: CC0 drums and private Vitalium

Status: **implemented opt-in technical path** on the development PR; **not yet a producer-approved mix/master**. No copyrighted presets or full song audio are committed to GitHub. The Phase43/44 approved song remains unchanged. See [product contract](PRODUCER_READY_TEMPLATE_PRODUCT.md), [groove template MVP](GROOVE_TEMPLATE_MVP.md), and [house harmony study](HOUSE_HARMONY_REFERENCE_STUDY.md).

## 1. Two independent real-source workflows

**A. Licensed native drum kit, without third-party synth:**

```bash
python3 -m kuang.house_sources \
  "warm deep house in C minor, 8 bars, simple triads, no lead" \
  --pack /path/to/verified/house-core \
  --soundcraft /path/to/reviewed/soundcraft-cli \
  --out-dir .local/new-cc0-sample-audition \
  --groove-profile deep --harmony-profile simple \
  --seed 17 --max-variants 2 --bars 8
```

This uses the **locally supplied audited Octal house-core CC0 sample kit**. It chooses two deterministic *genre-conditioned* kick, clap, closed-hat, open-hat and percussion sets, converts each original 44.1-kHz mono PCM16 file into 48-kHz PCM24 with a deterministic 16-source-sample-radius Hann-windowed sinc kernel and -1 dB safety attenuation, builds strict content-addressed assets with declared sample redistribution rights, binds them as real editable native SoundCraft Sampler instruments, saves/reopens sessions and renders two complete 8-bar audition previews with effects tails. Without `--no-render`, a real SoundCraft 0.11.0 binary is required. No new downloads.

Only drum roles are replaced; bass/chords/optional pad use the existing built-in synth here. Since the native sampler allows one sample per track, the system **now separates MIDI-42 closed hats and MIDI-46 open hats into distinct editable sampler tracks while preserving the combined original MIDI note events**. The two articulations have independent CC0 samples and mixer gain controls.

**B. Fully combined private experiment, with licensed drums AND auditioned Vitalium bass/chords/pad:**

```bash
python3 -m kuang.autonomous_create \
  "warm deep house in C minor, 16 bars, no lead, without pad" \
  --catalog /path/to/private/preset-library/reports/catalog.json \
  --plugin /path/to/pinned/vitalium.vst3 \
  --soundcraft /path/to/reviewed/soundcraft-cli \
  --out-dir /new/private/workspace-local-output \
  --private-third-party-presets --groove-template \
  --sample-pack /path/to/verified/house-core \
  --groove-profile deep --harmony-profile simple --drum-variant 0 \
  --per-role 1 --max-candidates 8 --timeout 12 --bars 16 --seed 17
```

This **extends the existing private-only license-unknown Vital audition/binding path**; it does NOT weaken or change the original/public adapter's existing policy. The full audio engine remains local. The high-cost private preset shortlist is not represented as an objective musical-quality winner, and full-context joint source selection remains future work. A minimum of one successfully independently verified preset **for each required chord/bass role** must be selected; some prompts also select pad. On incomplete selection, the project fails closed and does not publish. When combined with CC0, the final native bundle contains separately verified sampled drum assets and privately held Vital preset states.

**Important:** The combined output contains third-party preset states and must remain private. Do not publish a combined project or ZIP until the rights for every patch/resource have been verified. Separately authored CC0 drums can be redistributed under their declared source license; this does **not** confer rights to private Vital states.

## 2. Exact technical evidence, not a sound-quality claim

**VPS test A, November 13, 2026**: two complete 8-bar C-minor deep-house sample candidates from the installed house-core kit, seed 17, `simple` triads. Both exported editable native SoundCraft bundles, saved/reopened with exact project validation, rendered 48-kHz stereo 24-bit WAV with effects tail, 0 clipped samples and non-silent audio.

| Drum candidate | Kick | Clap | Closed hat | Open hat | Percussion | Sample peak | WAV length |
|---|---|---|---|---|---|---:|---:|
| 0 | house.kick.deep-01 | house.clap.classic-01 | house.hat.closed-06 | house.hat.open-03 | house.perc.shaker-02 | -7.84 dBFS | 20.24 s |
| 1 | house.kick.deep-02 | house.clap.classic-02 | house.hat.closed-01 | house.hat.open-01 | house.perc.shaker-01 | -7.62 dBFS | 20.24 s |

The candidates have different source selections, different WAV hashes and the same original MIDI groove and song harmony. The system **does not automatically claim either one is better** (`quality_winner: null`). Producer listening and contextual evaluation are still required.

**VPS test B, November 13, 2026**: one separate **16-bar**, seed-17 combined native session built *before the separate open-hat enhancement*, with the candidate-0 licensed kick/clap/closed-hat/shaker kit and successfully auditioned private Vital presets **Biow Bass** and **SNFKFutureBounce - Loaded Chords**. No pad and no lead. Native project saved and reopened; 48-kHz / 24-bit stereo, **42.4762 seconds**, **0 clipped samples**, RMS -30.53 dBFS, **integrated loudness -25.88 LUFS**, measured **4x FIR true peak -10.84 dBTP**, crest 19.57 dB. Measurement backend: Python windowed-sinc, **not certified**. The low level makes this a technically functional **pre-master demo**, **not** a polished club master or Phase44 quality match. The protected groove and harmonic gates passed; subjective status `NEEDS_LISTENING`.

A first attempt at private preset selection with only four candidates correctly failed closed. Its worker lacked NumPy because the standalone process did not inherit Kuang's existing optional packages. Using the already available project-local, **pinned Pedalboard 0.9.26**, NumPy 2.5.4 and SoundFile 0.13.1 (no downloads or installs) enabled selection within **two successful audits**, after 31 catalog preflight checks. For deployment, these dependencies need a documented single optional environment, not a broad system interpreter path. Do not silently install or run workers without the required versions.

## 3. Verification and quality gates

The sample pipeline checks:
- Local pack declares CC0; per-source manifest carries CC0 attribution, source identity and a bounded relative path under the pack. A catalog claiming CC0 is **evidence** but does not independently settle all possible third-party rights disputes.
- Source WAV is mono 44.1-kHz PCM16, bounded file size/duration and no symlink; deterministic resample produces non-silent, non-clipping PCM24 source.
- Content-addressed sample identity, mapping range, source sample hashes and exact audio readback.
- Real native `SoundCraft:sampler` mapping without changing MIDI notes; mixer controls stay editable.
- Actual native source reopens; render produces exact 48-kHz stereo PCM24, non-silence, zero clipped samples, preserved session state and 5 s effect tails.
- Groove template preserves source rhythmic events and supported harmonic relation; different source kit choices never silently regenerate percussion/bass MIDI.
- Private Vital workers run network-unshared and with strict plugin/source hashes and re-read their independently saved state before use.
- Song-specific gates and loudness reports explicitly say **`NEEDS_LISTENING`** until a producer approves the sound.

**Mix-staging follow-up:** [HOUSE_MIX_ROLE_CALIBRATION.md](HOUSE_MIX_ROLE_CALIBRATION.md) reports the opt-in native three-role stem-measured calibration experiment. It improved loudness on one reference template without clipping, but it **did not resolve chord dominance** within its bounded -4 dB correction; no subjective quality claim is made. The original private combined output remains unchanged.

## 4. Missing before the producer-ready 80% promise

1. **Contextual automatic ranking:** audition actual kick+bass+chord+pad **combinations**, compare reasonably loudness-matched clips and calibrate against approved/rejected producer preferences. These two CC0 candidates and the Vital source score do **not** constitute a validated winner.
2. **Per-role mixing:** the current private integrated mode begins with -15 dB global headroom and compensates conservatively. It cannot yet fix a relative kick/bass/pad imbalance or deliver a robust -14 LUFS/-1 dBTP master, and those values should not be universal requirements.
3. **Open/closed hi-hat distinction:** the current split preserves original note events and uses separately sampled articulation, but native host cross-track choke/mute groups and more sophisticated multi-sample kit layers are still future work.
4. **Arrangement length and variation:** this milestone remains 8/16/32 bars; no 118-bar original-song equivalent is inferred. Develop sectional role/FX grid and a configurable extended/radio form.
5. **Producer-facing stem/premaster/master packaging:** keep native session, editable patches, licensed audio and final mastering chain separate. No automatic "record ready" claim from purely technical checks.
6. **Resource limits:** currently the full private sample+Vital 16-bar experiment required about **93 s under concurrent VPS load**. Enforce explicit audition counts and timeouts; use short groove excerpts before any full song bounce; avoid repeated full renders.

**VPS test C, November 13, 2026:** the complete **five-drum-role** combined Vital source path also passed native save/reopen, source closure, 48-kHz/24-bit stereo rendering and all symbolic groove/harmonic gates. The private 16-bar preview was 42.4762 s, 0 clipped samples, -25.85 LUFS-I and -10.84 dBTP (non-certified measurement backend). Its editable native session has **7 tracks**: 5 distinct sampled drum/percussion instruments plus Vital bass and chord instruments. The selected samples were deep-01 kick, classic-01 clap, closed-06 hat, open-03 hat and shaker-02; the selected Vital patches were Biow Bass and SNFKFutureBounce - Loaded Chords. It remains **NEEDS_LISTENING**, not an approved finished mix/master.

The current deliverable is a **real-source technical proof**, deliberately isolated on the development branch and private user-controlled VPS paths. The selected virtual instrument, named source samples, waveform and session states in the private tests must not be copied to the public repository.
