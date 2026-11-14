# Native kick × bass context audition — 2026-11-14

## Goal

Replace isolated-source technical pass/fail as a *substitute* for listening with a bounded, repeatable, **actual native mix** comparison. This is the next groove-quality gate in `docs/HOUSE_PRODUCTION_RESEARCH_AND_NEXT_GATES_20261114.md`. The established Phase 44/45 releases remain references, never edited by this workflow.

## Reproducible CLI

Run from the original private Kuang workspace (not a worktree); the new Python module may be supplied from the checked-out branch via interpreter search path. The runtime requires the existing pinned SoundCraft binary, vetted private Vitalium module and preset catalog, Octal CC0 sample pack, and the previously generated private 16-bar source bundle with exactly one verified bass runner-up.

```bash
python -m kuang.house_native_pair_audition \
  --source .local/phase-reference-pocket-20261114/deep-Cm-126-s43-impact \
  --pack .local/sample-library/collections/octal-house-cc0 \
  --soundcraft /home/User/kuang-eval/soundcraft-0.11.0/soundcraft-0.11.0-linux-x86_64/bin/soundcraft-cli \
  --out .local/context-pair-audition-20261114-v1 --profile deep
```

The CLI is opt-in and does not change the existing `autonomous_create` default or its source-selection heuristics. Use the project's pinned Python environment and dependency paths; no installation is triggered. All third-party synth component states and native DAW bundles stay private under `.local/` and are not redistributed.

## Exact experiment

One **verified** native C minor / 126 BPM / 16 bar seed-43 project is shortened to its original Intro + Groove (8 bars). Only its selected kick source (CC0 native sampler asset) and bass source (verified private Vital preset) may change. The original one-prompt mix is an accepted **technical baseline**, not a human-approved production. Chord timbre, MIDI and effects are unchanged in every variant.

Four combinations are rendered and saved as independently editable SoundCraft sessions:

| Candidate | CC0 kick | Private Vital bass |
|---|---|---|
| A | house.kick.punch-02 | WIP-D - Reese Bass |
| B | house.kick.deep-01 | WIP-D - Reese Bass |
| C | house.kick.punch-02 | Bass - Insanity |
| D | house.kick.deep-01 | Bass - Insanity |

The tool renders **four complete native mixes and four role-isolated native stems** (two independent kick + two bass). It does *not* apply inferred bass EQ or fader moves. Stem FFT and kick-aligned transient/energy diagnostics are computed for all four pairs. All four WAV excerpts are gain-only normalized to the same LUFS using a safe true-peak ceiling; no dynamics processing or limiter is introduced. Native save/reopen consistency, MIDI hash equality, source inventory immutability, verified asset provenance and no-clip output are required.

## First private run results

- Generated at `.local/context-pair-audition-20261114-v1/` on the authorized VPS (not in the public Git repository).
- Rendered **4 native mixes + 4 isolated stems**, with **4 candidate native-save/reopen passes**.
- All **4 matched listening WAVs** at **−17.5 LUFS**, and each measured true peak was below −3.5 dBTP; no clipping.
- Original-vs-alternative bass late-to-early offbeat power: **+0.557 dB** versus **+7.029 dB**, respectively, across kick-relative 150–250 ms and 250–350 ms windows.
- None of four pairs triggered existing hard warnings for sub destructive summation or mono fold-down loss. That is **not** a musical-quality verdict.
- Result audio has independent SHA256 receipts and private native session copies. The original source inventory did not change. The four audio SHA256 values differ.
- No automatic winner is declared: `perceptual_winner: null`.

**Status:** completed *controlled comparison*; listening approval remains unestablished. The measurable difference is source character, not evidence that any candidate achieves Phase 44 quality.

## Follow-on engineering

1. Listen at matched loudness. Approve a kick/bass pair based on pulse, sub weight, mid-bass articulation, kick attack and the interaction with existing chords. If none works, reject all four and widen source search, not preset FX copying.
2. Once an appropriate combination has been found, add that **bounded** source-pair audition into the opt-in one-prompt nucleus workflow, with explicit cost caps and persisted candidate receipts, preserving original-only adapter security and private provenance.
3. Work next on intentional chord rhythmic placement and role-aware fader gain. Test effects routing only after the dry rhythm/chord nucleus is convincing.
4. Do not render new multi-minute songs or claim musical convergence until an independent 8–16-bar nucleus earns a listening approval.
