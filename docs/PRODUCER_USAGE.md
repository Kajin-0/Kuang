# Producer foundation: licensed samples and listening decisions

This implements the first slice in [PRODUCER_ARCHITECTURE.md](PRODUCER_ARCHITECTURE.md): a live editable sampler for **user-selected licensed WAVs**, full-project instrument/context auditions and an explicit human preference ledger. It does not implement professional musical judgment or establish a better song. Python 3.11+, standard library only; SoundCraft 0.11.0 remains separately installed. Scratch belongs in `.local/producer`, results in `artifacts/producer`; output paths must be new.

## Import a licensed sound

Prepare `.local/producer/credit.json`:

```json
{
  "creator": "Original creator's name",
  "source": "Publisher URL, exact file/version, and any explicit conversion",
  "license": "CC0-1.0",
  "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
  "notice": "Original publisher's dedication/credit record",
  "redistribution_permitted": true
}
```

Prepare `.local/producer/mapping.json`:

```json
{
  "root_note": 36,
  "key_low": 36,
  "key_high": 36,
  "velocity_low": 1,
  "velocity_high": 127,
  "key_tracking": false,
  "playback": "one_shot"
}
```

Supported declarations are CC0-1.0, CC-BY-4.0 and MIT, with their recognized license URLs. MIT assets must retain the complete supplied copyright/permission/disclaimer in `notice`. Attribution/source records are required even when not legally required, for inspectable provenance. **The importer validates declarations and data; it cannot authenticate ownership or grant permission.** “Free download” and “royalty-free” are insufficient. Do not submit unlicensed factory content or sounds whose raw files cannot be redistributed.

```bash
mkdir -p .local/producer/tmp
export TMPDIR="$PWD/.local/producer/tmp"
python3 -m kuang.sampled_instrument asset \
  --source .local/producer/my-kick.wav \
  --provenance .local/producer/credit.json --mapping .local/producer/mapping.json \
  --out .local/producer/library/my-kick
```

Input is mono/stereo **48 kHz 16/24-bit integer PCM WAV**, at most 30 seconds/32 MiB, non-silent and without full-scale clipped codes. Other formats/rates require an explicit conversion to a new project-local file first; record its origin and conversion. The importer never silently normalizes/resamples. It copies the original WAV byte-for-byte and records file SHA, exact normalized float32 PCM identity, mapping and license in `asset.json`. Changed/missing/extra files/directories and symlinks fail validation.

This is **one sample per track**. `one_shot` plays through regardless of MIDI note-off; `gate` follows note duration and ADSR. Key tracking transposes around the declared MIDI root. Bounds must cover every existing note/velocity. Conservative 32-voice and playback-step bounds prevent known native clamping/voice stealing. SFZ regions, velocity layers, round robins, choke groups, loops, cents and semitone-offset controls are unsupported. A mixed clap/snare track cannot silently become a single-key sound: use a deliberate map or a future explicit multi-zone/split-track workflow.

## Export and edit a live instrument

```bash
python3 -m kuang.sampled_instrument export \
  --source artifacts/phase10-house/project.kuang.json \
  --asset track-kick=.local/producer/library/my-kick \
  --out .local/producer/my-native --soundcraft /absolute/path/to/soundcraft-cli
python3 -m kuang.sampled_instrument save --source .local/producer/my-native \
  --out .local/producer/reopened --soundcraft /absolute/path/to/soundcraft-cli
python3 -m kuang.sampled_instrument render --source .local/producer/reopened \
  --out .local/producer/full.wav --soundcraft /absolute/path/to/soundcraft-cli
```

Multiple `--asset TRACK=ASSET_DIRECTORY` assignments are supported. Other tracks currently use the verified built-ins; mixed Vitalium/sampler projects and bus/send graphs fail explicitly. The original adapter still rejects samples; this is an opt-in backend. Schema stays **0.1**. `plugin_ref` is `soundcraft:sampler`; `preset_ref` pins the asset manifest. Root/key/velocity integers are semantic MIDI metadata, never falsely labelled Hz or normalized units.

Canonical controls are `sample.attack_ms`, `sample.decay_ms`, `sample.sustain`, `sample.release_ms`, `sample.velocity_sensitivity`, `sample.start` and `sample.level_db`. Other native controls must remain at verified defaults. For example:

```bash
python3 -m kuang.sampled_instrument edit --source .local/producer/reopened \
  --track track-kick --parameter sample.attack_ms --value 2 \
  --out .local/producer/edited --soundcraft /absolute/path/to/soundcraft-cli
```

Edits use ordinary scopes/locks/hash preconditions and exact reversible receipts. A fresh staged export is compared against the entire prior native state outside authorized scalar paths, then published. Other operation types fail closed; canonical music edits can use the existing transaction engine before a fresh export. Import remains verified snapshot recovery, not reconciliation of arbitrary GUI changes.

Open `session.scraft` in SoundCraft and retain the whole bundle. MIDI, sampler/mapping/controls, inserts and lanes remain native editable objects. `assets/` contains the original licensed WAV; `Audio Files/` contains the host's serialization. SoundCraft writes decoded **float32 WAVE_EXTENSIBLE**, so validation compares exact decoded PCM and separately hashes files, rather than falsely requiring identical source/native WAV headers. All dependencies are relative and hashed. GUI operation itself has not been tested on this VPS.

Rendering checks that the requested end covers the full song and the conservatively calculated active sample voices, then checks the final 250 ms for a settled release. Use `--end-seconds` for longer sample/effect tails. The renderer rejects truncation instead of fading it away or hiding it in a waveform edit.

## Full-project audition and human gate

```bash
python3 -m kuang.producer audition --source artifacts/phase10-house \
  --asset track-kick=.local/producer/library/my-kick \
  --hypothesis "This selected kick should leave space for the bass while keeping its driving body" \
  --out .local/producer/kick-audition --soundcraft /absolute/path/to/soundcraft-cli
```

Optional `--meter-library` explicitly selects the existing reviewed MIT libebur128 shared library; nothing is downloaded or loaded automatically. Default measurement is the previously validated stdlib meter, without formal EBU certification.

The full supplied arrangement is the context. A is unchanged; B changes only selected instrument bindings and asset provenance. Every note/clip field, MIDI byte, section, mixer, FX, lane and original SongSpec is preserved. Outputs include native A/B, full raw renders, separately LUFS-matched full-context and instrument-solo pairs, independent unchanged-context stems and reconstruction checks. Candidate save/reopen and repeated PCM must match exactly. Audition gain is labelled constant attenuation only; native source gain is separate.

This first audition command starts from an ordinary verified built-in-instrument bundle. When several tracks are selected, its instrument view is their combined solo group. Repeated incumbent replacement across sampler/Vitalium backends and general instrument-rebinding transactions are still future work. An already-bound canonical project can be freshly exported with the matching assets and its seven sampler controls can be edited; the binding command refuses to reset an existing sampler's controls implicitly.

Passing technical checks leaves `audition.json` **unreviewed**, with `quality_improvement_established: false`. Solos explain behavior; full context decides suitability. Sound envelopes can alter perceived phrasing with identical MIDI. Numeric diagnostics never promote a candidate.

To record feedback, supply a JSON file with exactly `audition_sha256` (SHA of `audition.json`), `reviewer`, `decision` (`preferred`, `rejected`, `no_preference`), `reason` and `listened_files` (the complete four-file path→SHA dictionary in `audition.json`):

```bash
python3 -m kuang.producer review --source .local/producer/kick-audition \
  --review-file .local/producer/my-listening-feedback.json
```

The append-only hash-linked chain checks actual audition and solo/context file identities and uses an exclusive writer lock. It records an explicit declaration; it cannot prove someone listened or authenticate identity. Rejection/no preference preserves the incumbent. Do not forge a “human” record for an automated release.

Only after an actual preferred review:

```bash
python3 -m kuang.producer package --source .local/producer/kick-audition \
  --out artifacts/producer/my-reviewed-listening.zip
```

The ZIP includes matched full/solo pairs, both editable projects, original licensed assets, native `Audio Files` and review provenance. No plugin binary is included. Latest rejection, drift, an active writer or an existing ZIP blocks publication. This is the requested musical quality gate, not a permission prompt for routine development.

This is a compact listening/editing publication, not a replacement for the original audition workspace: raw full/solo/context bounces are omitted. Its `audition.json` retains their original hashes as provenance. Keep the complete original audition directory to append further reviews or run `read_audition`; the extracted native bundles retain their own complete, independently verified media closure.

## Actual milestone evidence

`tools/producer_reference.py` creates three small **original diagnostic drum fixtures** and exercises one in the complete preferred Phase 10 song. They demonstrate the mechanism, not a curated professional library. Full A repeats the released Phase 10 D PCM exactly. B preserves all **1536 notes** and six markers, with live MIDI/sampler, exact native state/repeated PCM and original SongSpec. Independently rendered instrument plus unchanged context reconstructs each full mix within **1 24-bit LSB**. Native float32 sample PCM is exactly the original normalized PCM.

Reproduce into a new scratch directory, with the existing Phase10 source available:

```bash
python3 tools/producer_reference.py --out-dir .local/producer/reproduced-proof \
  --source artifacts/phase10-house --soundcraft /absolute/path/to/soundcraft-cli
```

No plugin or sample library is downloaded. The optional `--meter-library` must be supplied explicitly; otherwise the stdlib meter runs. Run `python3 -m unittest discover -s tests -v` for offline regression, or set the real-host opt-ins documented in [AGENTS.md](../AGENTS.md). The released full-run environment and outcomes are retained under `artifacts/producer/proof/`.

Native tests additionally cover mono24/stereo16 assets, multiple tracks, root/key tracking, relocation with original library/bundles hidden, exact scalar edits and receipt replay, missing sources and unsafe paths. Full raw A/B: **−25.0503/−24.6543 LUFS**, true peaks **−5.3397/−3.3411 dBTP**, zero clips; full audition copies match **−25.0503 LUFS**. These establish technical eligibility, not better music.

Proof is **`artifacts/producer`**, candidate **`full-song-audition/B/native/session.scraft`**. It remains infrastructure-only and **unreviewed**. No promoted production listening ZIP is shipped: replacing a kick with a diagnostic waveform does not establish studio quality. The importer now supports real human-selected licensed sources and an ear-focused loop before promotion. [STATUS](STATUS.md) and `artifacts/producer/proof/release-summary.json` record final tests, preservation, build and CI outcomes.
