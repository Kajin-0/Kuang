# Kuang — autonomy policy and first evidence-gated arrangement experiment

Date: November 15, 2026. Branch: feat/groove-first-template-mvp. Explicit goal change: **the user does not want to manually review routine A/B variants**. Prior user feedback should inform autonomous producer decisions; the agent should run cheap decisive technical tests and conservatively reject unproven or ineffectual changes. Continue improving without requesting approval after every small experiment.

## User's latest direct verdicts and decisions

User **explicitly preferred song #05 A**, the original WIP-D Retro Piano over alternate Loaded Chords and Dub Stabs. The earlier complaint that #05 sounded 'wonky' does not override the user's explicit comparative preference. Retain #05's original native source. Do not automatically change it to the loudest or most spectrally separated preset.

For #07, the user said they **cannot distinguish** A/-2dB/-3dB on their listening equipment. Earlier they said the chords seemed too loud. The conservative evidence-based autonomous fallback chooses **B, original patch with -2dB chord fader**, over a more aggressive -3dB or an unsupported source swap. This is a reversible **provisional agent decision**, not a claimed human-proven musical improvement. Original song #07 remains unchanged and the variant lives in the separate private native A/B folder. Neither choice becomes a universal house preset/fader default.

New \`kuang/house_producer_evidence_policy_v1.py\` provides fail-closed, source-hash-linked evidence policy:
- Explicit per-song listener preference outranks spectral metrics.
- If user identifies "chords too loud" but cannot distinguish safe options, choose the smallest source-preserving tested attenuation.
- Otherwise keep the verified original instead of guessing or invoking an unsupported quality oracle.
- Exclude clipping, unverified host paths, missing source provenance and level-mismatched A/Bs.
- Report decision class separately: USER_APPROVED_FOR_THIS_SONG vs PROVISIONAL_AGENT_CHOICE vs NO_CHANGE.

Private machine decisions: \`Kuang/.local/house-chord-cohesion-AB-song05-20261115/agent-decision-v1.json\` and \`...song07.../agent-decision-v1.json\`. User feedback itself established #05's choice; #07 fallback is an assistant rule, not a listening study.

## P1 arrangement research: contrast via subtraction, not blanket gain

Prior ten-song audit: Main Drop and Groove A RMS nearly identical across the original full song structures. Investigated whether **pre-drop drum withdrawal** could establish perceptual tension and restoration while preserving the drop's actual mixer level, other instruments, source groove, native patches and 128-bar form.

Implemented \`kuang/house_predrop_tension_v1.py\`:
- Reversible deep-copy from already validated full-house native project.
- Remove only existing MIDI kick/snare/hats/open-hat/percussion attacks in the last 1/2/4 beats of the Build, never invent new notes or change bass/chord/patches/FX/source/harmony.
- Rebuild existing kick-aligned duck and known filter automation against updated actual kick onsets, so removed kicks cannot continue triggering virtual sidechain dips.
- Hard-check other sections, original Groove A MIDI, native source and stage metadata. The full song form remains fixed. No drop master gain boosting.
- Review two actual SoundCraft native 48kHz PCM24 transition excerpts using **identical** host bounce path, identical original sources, actual WAV metering, zero clipped samples, -1dBTP native headroom and verified alternate save/reopen.
- \`decide_native_predrop\` refuses candidate selection if measured additional drop-versus-gap contrast is <2 dB, the first drop bar differs by >0.25dB RMS or upstream Build level changes by >0.15dB; candidates are only technically eligible trials, never declared musical winners.

### Native same-source A/B outcomes

| Context / candidate | Last pre-drop region | Contrast gain vs original | First drop bar RMS drift | Agent verdict |
|---|---|---:|---:|---|
| #05 jackin, two-beat gap | -26.022 dBFS RMS vs original -24.681 | **+1.344 dB** | +0.003 dB | **REJECT**: below 2dB gate |
| #05 jackin, full one-bar gap | -28.174 dBFS RMS vs original -25.931 (full-bar window) | **+2.247 dB** | +0.003 dB | **TECHNICALLY ELIGIBLE**, opt-in only |
| #07 minimal, one-beat gap | -25.367 dBFS RMS vs original -24.371 | **+0.999 dB** | +0.003 dB | **REJECT**: below 2dB gate |

Every row was measured on real SoundCraft alternate/untouched project PCM. The code and exact hashes/metrics are in the private failure logs and \`agent-decision-v1.json\` receipts. The failed two-beat jackin and one-beat minimal variants were preserved, not silently overwritten or reclassified as wins.

The one-bar jackin experiment changed actual transition-window integrated loudness from -25.497 to -25.764 LUFS and native true peak from -10.989 to -11.892 dBTP. The following drop remained almost identical in amplitude, so its contrast increase was achieved through subtraction rather than a gain boost. That still does **not prove** an artistically better transition; a human-level groove preference model is not present.

Verified corrected *same-host* 8-bar (last four bars of Build + first four bars of Drop) listening:
- [Original #05 transition](https://gofile.io/d/SQMvarzf)
- [One-bar jackin withdrawal](https://gofile.io/d/Dkz9MfS6)
- [Matched WAVs and technical evidence](https://gofile.io/d/3J3kfmmo)

## Deployment and stop gates

- The new \`--predrop-tension-v1\` one-prompt flag is **opt-in** and explicitly **restricted to jackin** at source planning, because the one-bar jackin case is the only style/duration combination that cleared the native gate. The generator does not apply the transition by default. Other styles can be tested through the reversible editing function but may not be automatically promoted.
- Do not treat a single accepted jackin transition as proof of across-song generalization. For future automation, make a two-candidate short native excerpt measurement a hard precondition before adoption, with no-change as a normal, acceptable outcome.
- New code and documentation do not change existing \`main\`, full-song defaults, private Vital sources, approved Phase44 or the original ten full tracks. No source project was overwritten.
- Phase44 remains gold standard; external ChordChord remains the user's preferred first-pass competitive target. Do not conflate a 2.247dB *contrast* improvement with achieving professional audio quality.
- Next independent high-impact work: instrument attack/release and register-sensitive source fitness; genre-conditioned arrangement contrast with actual auditory impact; optional native mastering only after mix quality and structure. Use bounded local evaluations without repeated requests for human A/B verdicts. Do not waste compute on tiny differences or pass/fail results that do not alter a production decision.

## Scope of autonomous decision-making

Kuang now has a **conservative deterministic producer evidence policy**, not yet a listening-capable neural agent or fully autonomous artistic assessment engine. Stronger autonomy requires a learned audio preference evaluator calibrated on the user's trusted musical references, paired with the current strict host/render/rollback process. Until then, prioritize verified safety + clear objective effect + explicit prior feedback, and classify uncertain aesthetics honestly as provisional.
