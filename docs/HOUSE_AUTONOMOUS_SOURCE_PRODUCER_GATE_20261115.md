# Kuang objective source-selection decision loop — November 15, 2026

## User-specified autonomous operating contract

Do not ask the producer to listen to intermediate A/Bs. Kuang must use native rendering and explicit evidence gates to select, reject or retain sources without repetitive human intervention. A user review is reserved for a **consolidated near-final full-song outcome**, not source/preset/gain micro-experiments. The user explicitly rejects the recurring growling minimal-house bass and wants physically strong kick/bass syncopation as the first blocking production priority.

This is a **technical production decision loop**, not a claim that spectral metrics can understand aesthetic quality. Software correctness, source suitability, perceived groove and mastered output remain distinct acceptance layers. A verified native session alone cannot be labeled professional.

## Root-cause investigation on real private sound sources

The previously disliked 122 BPM minimal F-sharp-minor song selected private Vitalium **LD Bass**, audited source hash `6e4e2259440015123c1f5670b2991674638c00f0ed198119dd20f3fb97cd918c`, along with the lower-frequency-heavy **In the Dark** pad. The producer's negative opinion of the growling timbre is a documented **identity-level veto** for this bass source, NOT a numerical FFT-derived definition of “growl”.

Earlier native pad A/B had demonstrated that replacing *In the Dark* with *Strings of Cygnus* improved the problematic minimal pad context. Thus avoid reintroducing a pad whose isolated low-band fraction is 0.2797 versus ~0.0013 in the verified Strings source.

The original one-prompt selector used an isolated source feature proxy to rank otherwise verified patches. It can select sources that are individually legal, non-silent, and mono-safe but create a poor bass groove in the song.

## Implemented source-policy stage

New `kuang/house_source_policy.py`, integrated directly into `kuang/autonomous_palette.py`:

1. **Producer-negative hard veto:** reject the exact previously disliked LD Bass hash before costly runtime evaluation; reject attempts to force it as preferred bass. This is an explicitly grounded user preference, not generalized style censorship or by-name filtering.
2. **Low-dominant, wide bass preflight:** for verified isolated-source low_fraction >=0.80 AND stereo_side_fraction >=0.65, withhold the patch from default selection pending true native sub-mono review. A provisional technical compatibility constraint, not quality preference.
3. **Low-heavy pad preflight:** if isolated pad low-band fraction >=0.20, withhold the patch from unreviewed selection pending actual pad/bass masking analysis. Existing lower-mid-heavy pad examples justify a conservative *review trigger*, not a universal pad EQ policy.
4. Preserve rejected reasons, original SHA256 identities, runtime assay results, patch licensing, original source libraries and no-network private worker.
5. Candidate selection always fails closed if no complete vetted palette can be found. No permanent audio source files or third-party patches committed to Git.

A real 122 BPM minimal-F-sharp/seed-29 Vitalium audition with the correct pinned worker and private catalog passed: the selector excluded LD Bass and In the Dark, and selected **Biow Bass 2**, **Strings of Cygnus** and the existing minimal dub-stab chord.

## Critical failure discovered in the full native output

That initially selected new source was **not** good enough to produce a convincing bass pocket, despite passing native save/reopen, true peak (−5.204 dBTP), zero clips, and the approved coherent chord-B algorithm (9 chord-voice retimings). The fullmix 25–90 / 90–250 Hz kick-window to offbeat ratios worsened from +8.657/+2.335 dB in the earlier minimal source to **+24.496/+16.513 dB** with Biow+Strings. The independent old LD+Strings pad rescue was +8.672/+3.271, confirming the problem cannot be attributed solely to the pad change. The initial Biow song was **rejected**, not silently accepted as an improvement.

The earlier `house_source_fit` kick-relative 150–250 ms “early offbeat” window can begin before the actual eighth-note bass attack (~246 ms at 122 BPM). This is not a valid measure of how quickly a bass patch speaks. Avoid interpreting it as a bass attack metric.

## New actual-MIDI-onset-aligned audio analyzer

`kuang/house_bass_onset_audio_v1.py` uses the canonical bass MIDI onsets to align **actual isolated native bass stems** to:
- attack: 0–40 ms after MIDI bass note-on;
- body: 40–140 ms;
- late: 140–220 ms.

A 48kHz stereo PCM24 Hann-windowed FFT examines 25–90, 90–250, 250–1000 Hz and low-band mono retention, with **actual isolated kick MIDI onset** windows as reference. Stems must be precisely frame-aligned. This is not a timbre classifier; a strong bass onset can still sound unpleasant, and an acceptable soft bass may have a slower attack in some genres.

The resulting verified attack measurements for the **same 122 BPM minimal note grid** were:

| Exact private Vital source | Bass attack 25–90Hz relative to kick attack | Bass attack 90–250Hz relative to kick | Interpretation |
|---|---:|---:|---|
| LD Bass | −7.503 dB | −12.919 dB | Technically audible but producer-rejected growling source: veto |
| Biow Bass 2 | **−34.742 dB** | **−48.440 dB** | Fails joint severe onset-attack deficiency |
| gentle pluck bass | **−1.198 dB** | **−10.386 dB** | Clears severe deficit, conditional native candidate |

The provisional technical fault requires **both** the 25–90Hz attack >24dB below the kick and the 90–250Hz attack >30dB below the kick. There are separate zero/near-silent and severe mono-loss flags. This joint condition is a conservative engineering screen to avoid arbitrary fader changes; NOT a listening-preference optimum.

A **locked-MIDI real native swap** of the Biow bass for independently verified gentle pluck bass from existing source session `ten-song-v1-07-minimal-20261115` passed SoundCraft native save/reopen, no clipping/peak problems and fullmix mono/phase checks. Fullmix near-kick/offbeat 25–90 / 90–250Hz ratios improved from +24.496/+16.513 to **+12.061/+6.288 dB**, still not a universal Phase44-level target. The alternate actually attacks when the note triggers.

## Autonomous rescue decision pathway

New opt-in `--native-bass-onset-rescue` requires `--contextual-shortlist` and existing one-prompt native source resources.

1. Select only vetted non-rejected bass and pad sources.
2. Render short real SoundCraft bass/kick stems from the user's actual MIDI and patches.
3. Evaluate the bass note onset windows; if no hard issue, **retain source** without expensive alternate trial.
4. If a severe onset deficiency exists, consider **at most one** previously verified bass source runner-up, *without changing MIDI, kick, chords, pads, effects, BPM, or sample pack*.
5. Export/save/reopen/check native state for alternate, render fullmix+isolated bass, check clipping, true peak, mono/interference and level change, and rerun the note-aligned onset gate.
6. **Choose alternate only if** the baseline has a demonstrable technical fault and the candidate clears it safely. Otherwise fail closed instead of publishing a weak audio mix or inventing a quality claim.
7. Write source/candidate and negative decision evidence. Never infer that a passing instrument is a human-preferred sound. Do not globally change baseline production or Phase44.

The first end-to-end native automatic rescue verification is recorded separately when completed. All private presets/WAVs stay under the user's VPS `.local`, not the public repo.

## Production acceptance and remaining open gaps

This is the first concrete AI/algorithmic production **self-correction**, not a solved one-shot professional House system. Full closure needs multi-key/style native cross-validation, explicit style-dependent bass articulation expectations, diverse *qualified* bass presets (some low-pass plucks may sound dull), a learned preference model calibrated on real professional stems/references, arrangement and mix/master tests. Avoid relying on a single bass energy scalar to rank aesthetic quality. Preserve the original and negative examples as regression fixtures, not “wins”.

**No intermediate user listening requests.** Only report consolidated milestones, with evidence and failures.

## Completed fresh end-to-end native automatic rescue

The first FULL fresh one-prompt source-selection recovery **completed successfully**, with real pinned Vitalium, SoundCraft 0.11, verified private presets, audited CC0 kicks and the user-preferred coherent four-bar chord rhythm. Source session: `/home/User/Kuang/.local/source-policy-native-auto-rescue-minimal-Fsharp-20261115`. A new output directory was used and original songs were preserved.

The selector excluded user-rejected `LD Bass` and the previously problematically low-heavy `In the Dark` pad. It initially selected `Biow Bass 2` and `Strings of Cygnus` for this 122 BPM minimal F-sharp-minor seed-29 song. The native isolated-stem stage automatically detected `bass_onset_attack_severely_masked_by_kick` on the actual Biow notes.

The pipeline then evaluated the one independently verified bass runner-up `gentle pluck bass` on **exactly the same MIDI**, preserving kick, chords, pad, processing, timing and note pitches, and verified native candidate save/reopen, peak, clipping and source-fit integrity. The candidate note-aligned gate returned `hard_flags=[]`. The one-prompt system automatically selected it with `TECHNICAL_BASS_ONSET_RESCUE` and completed the final production render. No human audition was required.

Final canonical project SHA256: `2bd0055e1c5c7a2ff2d0dd3488b51523584a6415fc6710fb670ba563ab3e57c5`. `native_save_reopen_equal=true`. Final bass = gentle pluck bass, chord = minimal house dub stab 23, pad = Strings of Cygnus. Final WAV: integrated −23.774453 LUFS, true peak −5.204235 dBTP, zero clipped samples. The bass has two offbeat notes/bar and 100% offbeat onset fraction, unchanged from its composition.

The rejected Biow+Strings complete native mix was +24.496 dB (25–90 Hz) / +16.513 dB (90–250 Hz) kick-window to offbeat power. The **automatically rescued final mix** was +12.061 / +6.288 dB on these same bands (relative reduction 12.435 dB / 10.225 dB). This is a substantial physical/temporal improvement *within the same song*, not a claim of human-preferred sound or a professional mastered result. The previous LD+In the Dark source may show lower ratios but remains rejected on explicit growling timbre feedback.

Full evidence JSON (private VPS): `/home/User/Kuang/.local/source-policy-native-auto-rescue-minimal-Fsharp-20261115/native-auto-rescue-final-evidence.json`. The complete source receipt records baseline hard fault, candidate cleared faults, chosen source identity and native roundtrip status. **92 focused and related regression tests passed** on the VPS, followed by a clean code commit `d9079f7` pushed to the draft experimental branch. No mainline/default change.

**Next acceptance gate:** broader multi-key/style checks of the source policy and native onset rescue; verify that a soft bass with legitimate slow attack is not incorrectly rejected across deep-house contexts. Improve bass source diversity and harmonic translation using professionally grounded references and hard stop conditions before full-song output. Do not ask the user to listen to intermediate samples; provide only a consolidated result near final-quality acceptance.
