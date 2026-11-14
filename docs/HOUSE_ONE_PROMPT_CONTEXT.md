# One-Prompt Native Contextual Source Selection — initial integration

**Status:** opt-in, short-groove technical integration; full-length contextual audition has not yet been verified. This module addresses the current product bottleneck: the private Vital palette selector formerly chose one isolated winner for each role and discarded independently audited alternatives. The new path keeps **at most one verified runner-up for bass and chords** from the *same original user prompt* and checks those sources against the actual generated house groove before final native publication. No previous donor songs are needed.

## Interface

```bash
python3 -m kuang.autonomous_create \
  "warm deep house in D minor, 124 bpm, 16 bars, no lead, without pad" \
  --catalog /private/preset-library/reports/catalog.json \
  --plugin /private/pinned/vitalium.vst3 \
  --soundcraft /path/to/pinned/soundcraft-cli \
  --out-dir /private/new-song-output \
  --private-third-party-presets --groove-template \
  --sample-pack /private/audited/house-core \
  --groove-profile deep --harmony-profile simple \
  --contextual-shortlist --max-candidates 12 --per-role 2 \
  --bars 16 --seed 51 --timeout 25 --master-preview
```

Defaults remain unchanged. The new opt-in source screen requires `--groove-template`, `--per-role` at least 2 and `--max-candidates` at least 4; prevents more than one runner-up per role. The backend retains exactly the source SHA, catalog/license reference, preview hash, role-feature vector, and verified plugin version for each shortlisted option. Unknown-license third-party Vital patches never enter GitHub or unrestricted host adapters.

Workflow:

1. Validate the user prompt; generate a deterministic house groove and independently audition up to the bounded number of real private Vital patches **for that same prompt**.
2. Build an editable SoundCraft native source with the original chosen bass/chord presets, separately sampled CC0 drums and conservative gain. Verify the original native preview and actual key/tempo/section locations.
3. Compute authentic three-role native stems and beat-aligned kick/bass and mono-fold-down source interaction diagnostics from the Groove section.
4. For at most one runner-up per bass/chord role, use the *same MIDI, drums, song structure and faders* but swap only that verified Vital patch. Render just the short excerpt, verify clipping/true peak, remeasure context fit and integrated loudness.
5. **Conservative deterministic decision:** initial independent palette selection remains unless the baseline has a severe measured sub cancellation or mono loss and an alternative resolves it **without** an unacceptably large (>3 LU) locked-groove level shift. Other cases are recorded as eligible/review/fallback; no subjective winner or fabricated musical score.
6. Construct the final editable SoundCraft session from the chosen patch identities, apply established conservative gain-staging, render and independently verify WAV and native project reopen. Optionally generate separate transparent and gentle preview-master derivatives. Output one `context-shortlist-evidence.json` receipt with all comparisons.
7. Discard unchosen foreign patches and isolated intermediate stems from transient private staging. Preserve the initial source session and all historical test artifacts.

**Current scope (updated November 14, 2026):** Source selection remains a bounded 16/32-bar nucleus with a valid native Intro/Groove audition project. The selected Vital patches now carry into an original 96–160-bar arrangement. **One 96-bar private-Vital full-length end-to-end native run has been verified**, but not every length/profile combination. Other lengths and broader multi-prompt quality remain unverified; do not infer producer-ready sound.

## Real native test and explicit STOP gate — November 13, 2026

One entirely new **deep-house D-minor 124-BPM seed-51** test used the user's existing audited CC0 house kit, privately vetted Vital catalog and SoundCraft 0.11.0. The isolated audition selected **LD Bass** and **SNFKFutureBounce - Loaded Chords** as its initial palette, and retained two independent verified runners-up for the *same prompt*: **WIP-D – Reese Bass** and **minimal house stab 09**. It evaluated both over identical MIDI using a fully valid eight-bar native Intro/Groove project (not an illegal partial native bounce).

| Alternative | Technical outcome | Selection |
|---|---|---|
| WIP-D – Reese Bass | No technical review warnings | Baseline LD Bass retained |
| minimal house stab 09 | REVIEW: >3 LU contextual loudness shift | Original loaded chord retained |

The actual final 16-bar SoundCraft output and MIDI survived native save/reopen and source-manifest hash checks. **Original premix:** −25.6177 LUFS / −10.6581 dBTP, **zero clipped samples**. The two final, source-preserving, independently measured *offline preview* derivatives were **transparent: −16.6596 LUFS / −1.700 dBTP** and **gentle compression: −17.1902 LUFS / −1.700 dBTP**, both **zero clipped samples**. The unknown-license Vital states stayed in the user-controlled private `.local` workspace.

**Critical runtime STOP:** The actual one-command generation was stopped at the **210-second bound**, after producing the complete native project, full WAV, MIDI and contextual evidence, but before mastering/packaging finished. Both the original host and state were independently verified and the offline master previews and final folder were recovered **without additional VST audition or SoundCraft rendering**. This is a technically valid *recovered artifact*, **NOT a passed one-command runtime gate**. A previous 260-second attempt also exceeded its cap while doing unnecessarily long role-stem renders; an intermediate attempt correctly failed because SoundCraft requires a native bounce to cover its full project length. Both architectural faults were addressed with a shorter validated eight-bar native audition project, but total end-to-end time remains too high and requires a focused performance improvement.

Recovered and verified private result (not for redistribution):

`/home/User/Kuang/.local/oneprompt-context-20261113-Dm-s51/`

It contains the original editable native session, its MIDI, 16-bar WAV, two master preview WAVs, `context-shortlist-evidence.json` and a separate explicit `recovery-evidence.json` recording the failed one-shot runtime gate. **Do not require the user to listen to this VPS-local test.**

The next development change should be limited to **measured performance and full-length integration**, eliminating duplicate native exports/slow independent role renders and caching unchanged source states before the final production render. Avoid more manual source tuning or new arbitrary audio-quality scores. This first version deliberately rejects opt-in contextual shortlist with 96–160-bar output until the same selected short-nucleus patch can be carried into a verified full-length native session.

## Verified optimization and full-length native integration — November 14, 2026

**Change:** A passing initial mix no longer causes expensive native rendering of bass/chord runner-ups whose technical results cannot change the chosen source. Verified preset runners-up remain in the source-selection ledger, but full native alternative renders run **only to address an actual severe technical compatibility fault**. Baseline groove analysis still uses genuine individually rendered kick and bass stems, not a fabricated subjective score. Original source and legacy workflows remain unchanged.

**Valid SoundCraft contract:** The source check always renders a complete native Intro/Groove audition project (8 bars for a 16-bar source, 16 bars for a 32-bar nucleus). No prohibited partial bounce or truncated MIDI. The final full arrangement is generated from the **selected, still intact 32-bar nucleus**, and receives the exact Vital and licensed CC0 sampler identities.

**New sampler regression:** The CC0 drum kit splits MIDI-42 closed and MIDI-46 open hats into separate editable `track-hats` and `track-open_hat` sampler roles. The full-length arranger previously omitted open hats from its role grammar and correctly stopped with `required instrument role is empty: track-open_hat`. A general role-presence correction now carries both hats through relevant sections. A self-contained CC0 fixture regression verifies a 32→96-bar arrangement with **nonempty open-hat MIDI, consistent exact pitch 46, original source immutability, original sample binding, and all arrangement technical gates**.

**Short-mode end-to-end acceptance:** One new D-minor / 124-BPM / seed-51 16-bar prompt with independently verified CC0 and private Vital assets **completed without recovery in 207.45 seconds** (configured 230-second cap), producing original native/session + MIDI, original 16-bar WAV (−25.6177 LUFS, −10.6581 dBTP, no clips), and two measured private mastering-preview WAVs (−16.6596 / −17.1902 LUFS, both −1.70 dBTP). Two vetted source runner-ups were recorded; both unnecessary native alternate renders were **skipped** because the original passed low-end hard technical checks. This supersedes the earlier failed 210-second runtime *for the revised conditional algorithm*, without overwriting historic failure evidence.

**First genuinely integrated long-form native acceptance:** A separate **96-bar**, D-minor / 124 BPM / seed-73 prompt independently auditioned private Vital patches from the same prompt, retained baseline **Biow Bass 2** and **SNFKFutureBounce – Loaded Chords**, and generated one fully editable **7-track, 8-section** SoundCraft native project. The one-command full-length native workflow completed successfully in **265.36 seconds** (500-second cap). Resulting stereo **48-kHz / 24-bit PCM** was **194.8571 seconds**, **−25.9370 LUFS**, **−9.7366 dBTP**, **zero clipped samples**. Exact native-project canonical identity, exported MIDI byte equality, plugin source manifest hashes, independent 76-note open-hat sampler role, zero-missing-assets, and every reported structural gate were separately verified. Two independently auditioned runner-ups were present in the decision record; **zero alternate native renders** were required, preserving the initial vetted palette as the deterministic fallback. **This was an original full-length native premix; mastering-preview derivatives were intentionally excluded from the full-length command** to isolate native performance.

Private reproducibility paths (presets/license-unknown states and WAV audio remain outside GitHub):

- `/home/User/Kuang/.local/oneprompt-conditional-Dm-s51-20261114/` — native 16-bar session + two mastered previews
- `/home/User/Kuang/.local/oneprompt-full96-Dm-s73-20261114/` — native 96-bar session and complete premix

**Verified separate full-length offline mastering (same 96-bar original, no new native render):** The `kuang.house_master_preview` standard opt-in utility used the untouched 194.857-second source WAV with independently measured original SHA and delivered two 48-kHz/24-bit stereo private derivatives. **Transparent gain-only: −17.900 LUFS / −1.700 dBTP, zero clipped samples, +8.0366 dB gain. Gentle real linked compression: −17.849 LUFS / −1.700 dBTP, zero clipped samples, +8.4564 dB gain after compression.** No subjective winner selected; these are listening previews rather than final club masters. Verified private sibling folder: `/home/User/Kuang/.local/oneprompt-full96-Dm-s73-20261114-master-previews/`. Source project and original premix remained unchanged. Master stage was offline **after** full-length native success, not part of the 265.36-second one-command generation; do not conflate these timing claims.

**Unverified:** actual subjective appeal of these tracks; comparable success across all house styles/seeds/arrangement lengths, completed in-command full-length preview mastering, and delivery of playable music through chat. This is an important engineering milestone but not a producer-quality release. Native/PCM pass is necessary but not sufficient.

**Next acceptance gate:** ensure the original generator's per-prompt source selection, mix, full-length output, and mastering form a bounded package across several independent prompts. Use the already tested offline mastering helper for existing valid full-length premixes; do not re-render SoundCraft merely to run mastering. Analyze actual failures only; avoid further infrastructure or house-theory expansion.

## Technical versus perceptual acceptance

The native screen is designed to prevent measurable faults, not determine what sounds exciting. No zero-warning source can automatically be called a producer-preferred instrument. An initial source that passes technical gates stays the fallback and may remain selected, despite an alternative having a different bass ducking response, because available evidence does not substantiate a musical winner. The source-selection workflow is now self-contained per prompt, but **a validated automatic producer-quality preference model remains a separate research and listening-validation requirement**.

Additional acceptance work: verify multiple distinct prompts and seeds; implement full-length contextual audition using the identical short nucleus, then arrange/finish the full track exactly once; compare actual accessible previews with the user's production judgment rather than continuing to expand the metrics and checklists. Native and PCM success are necessary, not sufficient.

The user is not expected to access VPS audio or listen to each engineering trial. If final artistic review is requested, provide truly playable audio in chat, not only a remote filesystem path.
