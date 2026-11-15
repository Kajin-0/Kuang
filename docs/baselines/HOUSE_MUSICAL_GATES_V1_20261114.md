# Kuang: Symbolic Musical Quality Benchmark V1

These are **symbolic MIDI gates**, not audible-quality claims. Hard failures and musical diagnostics are separate.

| Version | Songs | Hard pass | Musical seed uniqueness (median) | Rhythmic seed uniqueness (median) | No lead/arp |
|---|---:|---:|---:|---:|---:|
| groove-full-128 | 8 | 100.0% | 1.0 | 1.0 | 1.0 |
| groove-v2 | 48 | 100.0% | 3.0 | 3.0 | 1.0 |
| refined | 48 | 100.0% | 1.0 | 1.0 | 0.0 |
| sketch | 48 | 100.0% | 1.0 | 1.0 | 0.0 |

## Core-role Groove/Drop identical-bar fraction (first 8 corresponding bars)

| Version | Kick | Snare | Hats | Bass | Harmony |
|---|---:|---:|---:|---:|---:|
| groove-full-128 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| groove-v2 | 0.8125 | 1.0 | 1.0 | 0.0 | 0.5 |
| refined | 0.8125 | 0.8125 | 1.0 | 1.0 | 1.0 |
| sketch | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

## Scope and interpretation

- H01–H03: valid 4/4/960PPQ, contiguous section partition, active bass and harmony.
- H04: every quarter-note kick during named active Groove/Groove A/Main. N/A without such a section.
- H05: no kick or bass during a named Breakdown/Break. N/A otherwise.
- H06: disallow lead/arp ONLY when explicitly required for current groove templates. N/A legacy composer.
- H07: preserve dry-harmony policy in groove-impact projects; N/A legacy composer.
- D01–D08: lead/arp prevalence, groove/drop core-role bar similarity, onset density, outro thinning, chord register, eight-bar repetition, kick-free gain automation and minor leading-tone presence. Diagnostics are NOT pass/fail musical law.
- Musical core fingerprints capture exact time, duration and pitch; rhythm captures time and duration only. Velocity and note IDs excluded to avoid false seed diversity.
- The leading-tone check measures a pitch class, not harmonic dominant-function certainty.
- Chord range, drop intensity, and outro thinning can be artistically valid exceptions. No threshold was retrofitted to make a variant look good.
- Actual sound, mix quality, groove feel, perceptual arrangement contrast, and user preference remain unmeasured.

Generator exceptions: 0

