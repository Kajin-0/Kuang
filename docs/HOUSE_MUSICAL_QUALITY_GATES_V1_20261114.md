# Kuang — Musical Quality Gates V1 (executed November 14, 2026)

## Scope

This milestone implements source-only symbolic quality checks. It does not alter song generation, import private Vital presets, invoke SoundCraft audio, or certify audible musical quality. Claude evaluated legacy sketch/refined on main; the experimental groove-first template remains a separate development path.

Implemented:
- kuang/house_gates.py: versioned pure canonical-project evaluator.
- tools/house_gates.py: deterministic seed/key/profile/length matrix, explicit immutable output and reproducible JSON/Markdown receipts. It exits nonzero for generator exceptions or hard failures.
- tests/test_house_gates.py: nine adversarial tests for missing kick, prohibited kick in breakdown, optional roles, incorrect chord duck automation, velocity-only false variety, pitch changes, deterministic benchmarking, section contrast and legacy compatibility.
- .github/workflows/test.yml: bounded offline scorecard smoke under Python 3.11 and 3.13.

## Seven executable HARD structural gates

H01: 4/4 and 960 PPQ.
H02: contiguous complete section partition.
H03: both bass and harmony have note events.
H04: all quarter-note kick onsets in an explicitly named active Groove/Main section.
H05: no kick or bass in a named Breakdown/Break section.
H06: no lead/arp only where groove-template policy explicitly requests their absence; N/A for legacy.
H07: when groove-impact metadata promises dry chords, no unintended kick-triggered chord-gain duck lane; N/A for legacy.

A missing/nonapplicable gate is not counted as a pass.

Eight *diagnostic*, NON-hard groups measure unrequested lead/arp prevalence, matching core Groove/Drop rhythms, drop-vs-groove onset counts, outro thinning, chord median pitch, 8-bar phrase repetition, duck automation in sections without kicks, and minor raised-leading-tone presence. These are not universal musical laws; a great house song may legitimately use repetition, an unconventional outro, or natural minor without V major.

Core musical fingerprint uses exact (note onset, duration, pitch) for kick/snare/hats/bass/harmony; independent rhythm-only fingerprint uses onset and duration. Both EXCLUDE note IDs, velocity jitter, effects and sample hashes. Groove/Drop compares at most the first eight corresponding bars, not extra lead/arp notes or arbitrary unequal section lengths. No frequency/audio/loudness/perceptual success is measured.

## Frozen actual matrix

Four profiles (deep, straight, jackin, minimal), two keys (C major, D minor), two short lengths (16,32 bars), THREE varied seeds (17,18,19), three composers (legacy sketch, legacy refined, current experimental Groove V2 with Musical Plan V2, Harmony Interlock V1), and eight extra full 128-bar Groove V2 arrangements (one seed per profile/key).

Critical benchmark fix: initial proposed seeds 17,29,41 were all identical modulo 3, aliasing the three-way rhythmic choices and artificially hiding diversity. Those provisional private results are not the final frozen baseline. The final seed set 17,18,19 samples distinct rhythmic branches.

TOTAL: 152 symbolic projects, zero generation errors, 100% pass of narrow applicable hard invariants.

| Generator | Cases | Hard pass | Distinct musical and rhythm identities / 3 seeds | No lead/arp | Bass Groove/Drop exact bar match |
| --- | ---: | ---: | --- | ---: | ---: |
| Legacy sketch | 48 | 100% | 1 / 3 | 0% | 100% |
| Legacy refined | 48 | 100% | 1 / 3 | 0% | 100% |
| Experimental Groove V2 short | 48 | 100% | 3 / 3 | 100% | 0% median |
| Experimental full 128-bar | 8 | 100% | N/A: only one seed per profile/key | 100% | 100% |

These structural passes do NOT mean professional-quality musical composition. See full per-case evidence for all applicable checks, failures (none), counts and diagnostics.

Additional observed results:
- The 128-bar arranger copies first-eight-bar kick/snare/hats/bass/chord patterns (onset, pitch, duration) 100% between Groove A and Main Drop.
- Its Outro is 7 core-role note onsets per bar thinner than Groove A by median.
- 0% of sampled minor harmonies contain the raised-leading-tone pitch class. This suggests an unimplemented harmonic option, NOT a mandatory requirement for every minor-key track.
- This C-major/D-minor matrix is NOT a same-mode C-vs-B transposition/register drift assessment. That should be tested separately before making any pitch-range claim.
- The legacy CLI still defaults to sketch. The new experiment's improvement must not be described as current default-user experience.

Immutable artifacts:
- docs/baselines/HOUSE_MUSICAL_GATES_V1_20261114.json — 152 complete case receipts.
- docs/baselines/HOUSE_MUSICAL_GATES_V1_20261114.md — concise report.
- tools/house_gates.py — executable benchmark definition and user-controlled output path.
Private earlier provisional seed matrix remains preserved independently under the VPS project .local tree.

## What next — concrete, no churn

The largest *verified* structural deficiency is the long arranger's exact Groove A / Main Drop duplication, rather than the short composer lacking any seed variation. Improve the EXISTING house_full_arranger.py with coherent 4/8-bar musical variations and stronger section identities while protecting original kick/bass pocket, harmonic progression, editable native project and no-lead policies.

Future acceptance: clear drop-vs-groove core-role phrase differences across independent keys/profiles/seeds; H01–H07 still pass; repeatability and source immutability; short gain-only level-matched listening tests confirm genuine musical improvement before promotion.

Retain the complete original 4:02 WAV, the harmony-automation corrected native copy, the Phase44 groove reference and all previous successful/failed experiments. Do not build a second composer or overfit the C-minor reference.

Status: executable structural scorecard and baseline complete. Perceptual quality not measured.
