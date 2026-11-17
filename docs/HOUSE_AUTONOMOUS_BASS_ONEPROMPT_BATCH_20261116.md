# Autonomous House low-end production: fresh multi-seed acceptance gate

**Date:** November 16, 2026 (UTC). **Branch:** `feat/phrase-coherent-chords-v2-20261115`. **Frozen experiment code:** `cc136f442253846a0da48f97db4278b3b1adefb0`. **Status:** acceptance **FAILED**. No production defaults promoted, no existing songs or private source states overwritten.

## Goal

Determine whether the independent, source-aware native bass-rescue system works **during fresh one-prompt production**, rather than only on controlled source-swap experiments. The producer requested **no intermediate listening approvals**. Source rejection, waveform integrity, physical kick/bass response, and generation success are evaluated automatically. This does not invent a subjective taste oracle or claim studio-quality mastering.

The batch was pre-frozen before native generation: three independent seeds / three different styles and keys, same pinned SoundCraft 0.11/Vitalium 1.0.6 worker, locally audited CC0 Octal house-core samples, one 16-bar nucleus each, opt-in groove identity V2, musical plan V2, producer-preferred four-bar chord timing and native bass-onset/fullmix rescue. Each attempt used at most 12 sandboxed preset auditions (at most three accepted per role) and one contextual bass runner-up. Runs were **sequential** to protect VPS CPU and sound-engine reproducibility. Every attempt, including failures, counts in the denominator.

## Frozen actual results

| Independent production | Seed | Tempo | Result | Output |
|---|---:|---:|---|---|
| Deep House, E minor | 41 | 123 BPM | **FAIL CLOSED** | Severe bass-onset fault without successful verified fullmix rescue |
| Jackin House, G minor | 83 | 127 BPM | **FAIL CLOSED** | Severe bass-onset fault without successful verified fullmix rescue |
| Minimal House, F♯ minor | 97 | 122 BPM | **PASS** | Real native repair using independently verified `gentle pluck bass` |

**Observed complete one-prompt technical yield: 1/3 = 33.33%.** The preregistered release-readiness screen requires at least 90% technical completion over multiple independent styles and seeds; hence **this run FAILS**. Two safe refusals count as product failures, not success. The 3-song batch is intentionally small: its estimate is a diagnostic, **not a statistically reliable fleet-wide rate**.

For the one fully completed minimal F♯ production:
- Native edit/save/reopen **PASS**, final stereo **48 kHz/24-bit PCM**, zero clipped samples.
- Integrated loudness **−26.623 LUFS**, true peak **−4.000 dBTP**. This is an unmastered technical preview.
- Final rendered Groove beat/offbeat ratio: **+10.329 dB at 25–90 Hz** and **+3.691 dB at 90–250 Hz**.
- The initial severe bass-onset source fault was repaired and the replacement passed `TECHNICAL_REPAIR_ELIGIBLE`, with the independently rejected growling source not selected.
- The existing preview auditor separately flagged **low near-finished-preview loudness and high fullmix crest factor**. These are warnings, **not proof of unacceptable musical quality** or a reason to master harder before correcting sources.
- No artistic or listener-preference result is claimed.

## Diagnostic correction: selection versus contextual rejection

The original post-batch hypothesis was that the single alternate source was insufficiently varied. An actual independent **pinned Vitalium preset preflight on the failed deep-E seed** disproved the simplest version of that hypothesis: the selected baseline was `Biow Bass 2`, and the **already independently sandbox-auditioned runner-up was `gentle pluck bass`** (the same source that had technically repaired other controlled songs). It did not need to be added to the source pool.

An exact-prompt/seed diagnostic re-run, with a **status-only safe failure message**, returned:

`REJECT_NO_MEANINGFUL_FULLMIX_OFFBEAT_REPAIR`

Thus the first fresh deep-house failure was an **actual source-and-arrangement contextual failure**, not a missing candidate, corrupt Vitalium state or plugin crash. The alternate could not meet the strict double-band complete-mix offbeat-improvement criterion. The jackin failure has only the less-specific `NO_SAFE_BASS_REPAIR` result; its individual rejection cause is **not independently established**. Do not assume it is the same failure type without evidence.

The previously considered fixed extra-bass-shortlist feature was **discarded** when the preflight contradicted its causal rationale. The exact waveform/energy thresholds and the producer's rejection registry remain unchanged. This prevents tuning to a single successful sound and calling it generalized quality.

## Reusable automated gate

An existing module, `kuang/house_batch_acceptance.py`, was improved instead of creating a separate music-quality scorer:

- Correctly extracts actual CC0 kick/snare/hat identities when `sample-selection.json` includes nested `groove_impact_pocket` metadata. Its previous comprehension treated this metadata as a drum source and could crash.
- Verifies the selected bass source against the persistent producer rejection registry.
- Verifies a published repaired song actually has a severe original onset fault, one native-approved complete-mix source replacement and no unresolved onset fault; a rejected repair may not be misreported as a successful publication.
- Provides `audit_autonomous_attempts()` to include **failed and timed-out generations**, ensure different seeds and styles, verify each successful song against its actual source/native MIDI/selection/PCM receipts, and calculate the complete technical pass fraction. No cherry-picked successes and no automatic artistic winner.
- Preserves the default no-promotion status irrespective of technical scores. Existing artist references and full songs are untouched.

Private reproducible batch log, generated WAV/native session for the one success, and numerical audit summary remain under:
`/home/User/Kuang/.local/autonomous-bass-batch-20261116/`.

The failed diagnostic preflight and rerun outputs are separate private paths. No preset bytes, sampled drum files or audio are committed.

## Next stop gate

The correct next engineering target is **song-context bass/kick compatibility**, not a general gain increase or arbitrary expansion of preset pools. The same bass source can improve the pocket in one arrangement and fail in another.

Before another expensive batch:
1. Preserve a **sanitized failure reason and both measured band deltas** before native temporary-state cleanup. Without the deltas, each failed seed requires another full render just to diagnose.
2. Take **one** failing seed and compare fixed-source alternatives with a *bounded bass-pattern envelope/phase/rhythmic-placement* intervention that retains the four-on-floor kick and chord B, and does not use an extra preset search.
3. Check attack/body, **absolute** offbeat low-band increase, near-kick energy, mono/phase, fullmix true peak and clipping. Do not pass a ratio by weakening the kick.
4. Only then repeat a fresh frozen multi-seed batch. Do not enable normal one-prompt bass rescue until the batch yield and quality criteria are actually met.

**No intermediate producer listening requested.** Current result is a valid *failed* acceptance gate that narrows the causal work, not a claim that the final Kuang objective has been reached.

## Failure observability patch (after frozen batch, no new music claims)

The batch uncovered a further efficiency defect: the one-prompt pipeline removed temporary native A/B renders after refusing an unsafe bass rescue, while its exception contained only the high-level refusal class. This made an identical multi-minute rerun necessary to determine **which measured low-frequency condition failed**.

The opt-in private contextual rescue now writes a bounded **source-anonymous** numerical failure reason into its fail-closed status. Per attempted bass source it records at most one whitelisted source-repair status, the two-band *relative* kick-window/offbeat changes, the two-band **absolute offbeat energy changes**, the two-band near-kick energy changes and the number of known onset faults when present. Values are rounded to 0.001 dB. It excludes preset names, paths, raw samples, private patch bytes and audio. Invalid/untrusted statuses become `UNKNOWN`. A failure still refuses the track; this patch merely makes engineering analysis reproducible without an unnecessary second native render.

This status format was added **after** the frozen 3-song acceptance run and therefore **does not retroactively change its outcomes or assert unmeasured values**. The exact diagnostic replay that identified `REJECT_NO_MEANINGFUL_FULLMIX_OFFBEAT_REPAIR` on deep seed 41 occurred before numerical failure reporting; its precise deltas remain unknown and are not fabricated.

The next experiments can now distinguish a relative offbeat failure from an absolute-power or kick-preservation failure using one original native render, improving Kuang's autonomous diagnostic efficiency.
