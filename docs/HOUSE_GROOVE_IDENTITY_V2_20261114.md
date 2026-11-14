# Kuang: groove identity V2 — additive, opt-in, multi-prompt native trial

## Trigger and actual objective

User judged the two previous E-major/B-flat bass +3 dB A/B tracks practically indistinguishable and the independent tracks essentially transpositions. The previous bass-fader change was **not** musically accepted. The goal is **different, compelling one-prompt house productions with groove quality at least approaching Phase44**. This feature does not claim to accomplish that without producer listening; it addresses an identified structural source of sameness.

## Root causes directly verified in the existing code

1. `house_template.template(..., impact_pocket=True)` previously unconditionally replaced the profile bass rhythm with the same 2/6/10 sixteenth-step offbeat sequence and occasional 13th-step octave pickup. Different styles were thus nearly indistinguishable in bass MIDI, despite different chord progression and tonal key.
2. `house_sources.prepare_kit(...,impact_pocket=True)` forcibly installed CC0 Punch-02 kick for straight/deep/jackin regardless of the style-specific sample candidates. This was a historical quality-reference experiment, not a required musical identity for all generated tracks.
3. The source selector's current isolated-Vital heuristic also selected the same Biow Bass 2 and Loaded Chords across two different prompts, despite shortlists with different sources. `house_one_prompt_context.py` correctly refuses to claim an alternative sounds better based on FFT metrics alone; a new stylistic preset choice requires actual listening.

## Change: opt-in groove identity

- Extend existing `house_template.template(..., groove_identity_v2=True)`, requiring `impact_pocket=True`. Only bass MIDI articulation is changed. Source pitches remain generated in the requested SongSpec key/progression and existing drum/chord/pad FX, source handling, harmony interlock, SongSpec and output schema remain.
- Four curated groove vocabularies rather than one reused C-minor pattern: **deep** uses sustained offbeat roots/occasional pickup, **straight** uses a regular driving offbeat root pulse with alternate pickup, **jackin** has short syncopation and chord fifth accents, **minimal** leaves pronounced gaps. Per-phrase seed determinism adds variation without a randomly new phrase every bar.
- New partial policy in `house_sources.prepare_kit(...,groove_identity_v2=True)` removes the *mandatory* Punch-02 kick **only for this option**. Select the existing style-conditioned, audited CC0 kick via `_source_candidates`. All source licensing, source hashes, amplitude staging and native samplers remain in force.
- `autonomous_create --groove-identity-v2` requires `--groove-impact --groove-template --sample-pack` and uses the original audited, bounded private one-prompt selection/host/render flow. Compose, harmony interlock, optional Musical Plan V2, SoundCraft and existing mastering are **not replaced**.
- A discovered minimal-house chord collision occurs when the interlock selects adjacent sixteenth-note chord positions with 300-tick durations. The interlock now excludes patterns with less than 330-tick onset spacing, rather than silently creating invalid overlapping MIDI. Old successful test cases remain valid.

## Planned native multi-prompt acceptance

Execute one freshly generated, independently keyed 16-bar native track per style:
- Deep / E major / 123 BPM / seed 67.
- Jackin / B-flat major / 128 BPM / seed 83.
- Minimal / F-sharp minor / 122 BPM / seed 29.

Run with opt-in `--groove-identity-v2 --musical-plan-v2 --groove-pocket-diagnostics`, CC0 source pack, pinned private Vitalium plugin and SoundCraft 0.11.0. Save three private native project bundles, licensed sample receipts, source preset identities, SHA256 fingerprints and actual WAVs; preserve the historical Phase44 and earlier one-prompt baselines.

**STOP/preserve:** native save/reopen mismatch, song-spec drift, asset SHA discrepancy, clipping, weird note overlap, excessive render costs or silent fallback. Existing standard-library FFT is a diagnostic. Do not claim three professional songs or distinct musical identities until matching-level listening verifies them.

### Current unclosed questions

- Different bass MIDI and kick sample are only two components of identity. The palette may still choose the same bass/chord Vital patches because scores are dominated by isolated-feature proxies. Avoid forcing random preset diversity or auto-choosing alternate patches without actual context hearing.
- Maintaining the original impact-mode +8 dB kick boost while changing the source may preserve the excessive kick dominance observed previously. Analyze actual fullmix kick/offbeat ratios and *listen*, then do one controlled native gain/envelope comparison rather than blindly boost bass or trim kick across all songs.
- Phrase-level harmonic/melodic identity and full-song arrangement development remain later gates after a convincing groove.

## Completed three genuinely independent native runs

The three previously proposed fresh independent one-prompt runs **completed successfully** with the exact existing private source-catalog/Vitalium 0.11 SoundCraft/sampler pipeline; 16 bars each; native save/reopen verified; no clipped samples. Recorded audio is 48 kHz stereo, 24-bit PCM. All original benchmarks and earlier generated releases remain intact.

| Style and prompt family | BPM/key/seed | CC0 kick | Verified private bass Vital | Private chord Vital | Musical Plan V2 degree sequence |
| --- | --- | --- | --- | --- | --- |
| Deep / warm | 123 / E major / 67 | house.kick.deep-01 | Biow Bass 2 | SNFKFutureBounce - Loaded Chords | [0,3,0,4] |
| Jackin / bright | 128 / B-flat major / 83 | house.kick.punch-01 | Biow Bass 2 | SNFKFutureBounce - Loaded Chords | [0,4,3,4] |
| Minimal / dark | 122 / F-sharp minor / 29 | house.kick.tight-01 | LD Bass | minimal house dub stab 23 | [0,6,0,5] |

**Real new audio measurements**, full-mix band energy around kick onsets minus energy 200–300ms afterward:

| Style | 25–90 Hz kick/offbeat | 90–250 Hz kick/offbeat |
| --- | ---: | ---: |
| New deep | +9.514 dB | +7.318 dB |
| New jackin | +12.165 dB | +4.718 dB |
| New minimal | +8.657 dB | +2.335 dB |
| Previously approved Phase44 (nonmatched sections/master; diagnostic only) | +4.329 dB | −6.228 dB |

The prior independent deep E-major example had +15.293 dB at 25–90 Hz, and the prior jackin B-flat example +14.525 dB. The new grooved versions reduce that specific imbalance by **5.779 dB** and **2.360 dB** respectively. This is informative but not a calibrated listening score; the low-mid (90–250 Hz) contrast is still notably different from Phase44. No automatic relative mastering, kick or bass gain tuning was used on the raw native projects.

**Actual identity diversity:** 3/3 distinct approved CC0 kick sample identifiers, 3/3 different bass note onset/duration/pitch-class patterns, 2/3 unique bass preset identities, 2/3 chord preset identities, three different progressions/key/tempo identities. **Still unresolved:** deep and jackin share the same bass and chord presets, and none is known to sound professional until human listening confirms it.

**Listener material:** three full 16-bar WAVs gain-only matched to −20.0 LUFS; all have true peaks safely below −1.9 dBTP, no clipping. VPS authoritative files under:
- `.local/three-grooves-deep-E-20261114/`
- `.local/three-grooves-jackin-Bb-20261114/`
- `.local/three-grooves-minimal-Fsharp-20261114/`
- `.local/three-grooves-listening-20261114/kuang-three-grooves-wav.zip`

The listening archive was shared externally at https://gofile.io/d/WRofVfRl (temporary external retention, original WAVs preserved privately).

**Acceptance state:** 56 focused regression tests passed (groove identity, source samples, native creator, harmony, interlock, prior V2 plan); all three newly generated native renders and source receipts passed. Human musical-quality approval pending. The mode remains explicitly opt-in; **not merged to main**.

## Recommended next step after hearing these songs

1. Treat their overall groove quality and *real* musical identity as the stop/go gate. If they still sound like transpositions, do not call this solved.
2. The existing native source-ranking evidence for the jackin song gives a substantive alternative: its independently verified **WIP-D - Reese Bass** source has stronger upper harmonic balance (approximately 48.8% of proxy spectral energy in the audit midband vs approximately 21.6% for Biow Bass 2) and substantially longer tail ratio. These are isolated-source descriptors, not guarantees of better groove; audition this candidate at **identical MIDI** in the actual jackin native mix using the existing `house_native_pair_audition`. Do not force it into every style.
3. In deep and jackin styles, evaluate tempo-aligned bass attack/release and kick decay against their actual chords, while preserving the improved separate riff families. When source pairs sound convincing, propagate bounded source selection into the one-shot path. Avoid chasing a single-song reference or using arbitrary diversity quotas.

**This experiment isolated MIDI articulation + style-driven CC0 kick source choice as the generator-level change. It did not claim that more kick boost or a +3 dB bass gain was appropriate.**
