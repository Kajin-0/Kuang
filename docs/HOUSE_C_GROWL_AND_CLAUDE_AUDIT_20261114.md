# Kuang source-identity diagnostics and external architectural review — Nov 14, 2026

## User feedback / highest-priority gate

The user judged three independently generated 16-bar house tracks A (deep E-major), B (jackin B-flat major), C (minimal F-sharp minor) as improved overall, but C has an unpleasant strange growling sound and less energy. **Do not claim to have identified the growl solely from FFT statistics** or manually "fix" just C. Kuang's actual product objective is reliable different, high-quality editable productions from *one prompt*, with strong kick/bass physical groove. The existing `house_template`, `house_harmony_interlock`, `house_musical_plan`, vetted private Vitalium palette, CC0 source pack, SoundCraft host, `house_full_arranger`, prior phases and listening records are retained. Neither the experimental A/B replacement nor the new review diagnostic changes their defaults.

## Native locked-C diagnosis (completed)

C original output: `.local/three-grooves-minimal-Fsharp-20261114`. Private, verified source identities:
- Bass: **LD Bass** (SHA256 starts `6e4e22594400`)
- Chord: **minimal house dub stab 23** (`99798d814d60`)
- Pad: **In the Dark** (`4898097f6b0d`)
- Kick: audited CC0 **house.kick.tight-01**.

A real SoundCraft native rendered solo of each role, retaining its original effects/routing but muting other MIDI instruments, was produced; it is **not** a clean pre-effect or dry synth oscillator isolation. The original project, its MIDI and original patches are unchanged.

Active-Groove 32-window, stereo 4096-point Hann spectra from the *native* isolated renders:

| Native stem | RMS, dBFS | Fraction in 20–120 Hz | Fraction in 120–500 Hz | Fraction in 500–2000 Hz |
|---|---:|---:|---:|---:|
| Kick | −31.27 | 94.60% | 5.33% | 0.07% |
| Bass | −39.30 | 74.28% | 22.91% | 2.74% |
| Chord | −35.85 | ~0.001% | 24.26% | 73.61% |
| Original pad, In the Dark | −33.99 | 0.372% | 88.49% | 10.49% |
| Alternate pad, Strings of Cygnus | −41.24 | 0.01% | 64.18% | 35.71% |

**Important revision to isolated preset feature proxy:** The private palette audition had reported original pad `low_fraction=0.2797`. That refers to the *isolated Vital audition's own spectral band grouping*, **not** to the native rendered sub-120 Hz band. Native solo shows *only ~0.37%* under 120 Hz, but a strong 120–500 Hz body, which can congest the lower-mid mix and make the tone seem growly. The source is not proven responsible for the user's subjective growl; LD Bass and the chord's long tail remain candidates.

One *locked-F-sharp-minor* pad-only substitution was rendered using the existing preset verifier and private SoundCraft host. Verified runner-up `Strings of Cygnus` (`66edec10234d`) was independently accepted/runtime-verified and is roughly 7.25 dB quieter than original pad in native Groove RMS, with ~12 dB less measured 120–500 Hz energy. In the full native short mix, swapping just the pad lowered integrated loudness from **−20.895 to −24.158 LUFS** at identical MIDI/faders, while the true peak remained −5.204 dBTP. **This is not proof it is a better pad or better groove**; both rendered full mixes were gain-only matched to about **−22.01 LUFS** for listening, no clipping.

Private artifacts:
- `.local/minimal-growl-roles-20261114/diagnostic.json` (native region measurements, source hashes, integrity and provisional quality status)
- `.local/minimal-growl-roles-20261114/C-matched-pad-comparison.zip` (two matched-loudness native full-mix excerpts)
- `.local/minimal-growl-roles-20261114/C-isolated-source-stems.zip` (five isolated original kick/bass/chord/pad/alternate-pad WAVs, each independently level-matched for *timbre recognition*, **not** cross-stem contribution ranking)
- Original and alternate verified native project copies under the private `.local/` tree. External listening shares (may expire): [C pad A/B](https://gofile.io/d/ccpW0Q7w), [isolated source roles](https://gofile.io/d/8TNCMhSp).

The role solo results have independent loudness normalization in the listening package. To infer which stem actually dominates the original mix, use the unnormalized RMS/band data above instead.

## New reusable, non-prescriptive algorithm diagnostic

`kuang/house_timbre_suitability.py` provides conservative *review flags* for private runtime-verified bass/chord/pad feature records, with deterministic validation and no source replacement. Example flags: strong low-band/high-RMS pad; high stereo side fraction in bass **requiring sub-specific mono checking**, not claiming a bad bass; long chord tail; extremely short bass tail or lack of harmonics. Provisional thresholds **have not been trained or validated against listening**. Explicit `perceptual_quality=NOT_EVALUATED`, `winner=None`, and no automatic source discard.

The existing private one-prompt creator optionally writes `timbre-source-review.json` using `--timbre-source-review`. It does not replace the source-selection heuristic, add plugin renders, or alter the current project's MIDI/mixer. Future one-prompt sessions can use it to **prioritize a small number of actual native comparisons**, but not to assert a musical winner from isolated spectral metrics. The current flag surfaces 2 pad review warnings for C but not for A/B, along with all three bass sources' high stereo fractions requiring a more specific sub-band mono test.

## External Claude code review — dispositions after checking *this* branch

Claude's report primarily analyzed the older default `sketch/refined` and historical hash-pinned Phase13–26 scripts. The PPQ correction (960 ticks/quarter) in its own report was appropriate. Its offline symbolic findings are useful but must not be attributed wholesale to the current opt-in native groove-template engine:

| Critique | Status in current branch | Response and priority |
|---|---|---|
| Old authored phases are C-minor/126BPM hash-pinned while default `create` still uses sketch | **Valid architectural/product warning.** The current native private `autonomous_create --groove-template` is separate and uses newly generated SongSpec/Groove Identity V2, but the public canonical `create` defaults to `sketch` | Keep old releases untouched. Later unify user-facing default onboarding around the *existing successful* groove-template production path; not another replacement composer. P1 after low-end review. |
| Few distinct outputs across old sketch/refined seeds | **Valid for legacy path, not an accurate count for V2** | New 36-seed symbolic checks yielded just **3 unique bass onset/duration rhythmic structures per style** across deep/jackin/minimal, plus 4 different harmonic progression families each. Full MIDI hashes vary on every seed in 12/12, but that alone can reflect velocity and is insufficient to certify musical diversity. Expand **curated musical phrase archetypes** when groove quality is accepted; do not use random jitter. |
| Groove and Drop identical | **Partly remains.** In an opt-in 16-bar generated Deep E example, Groove/Drop kick events 16 vs 15, bass 16 vs 16, chord 40 vs 40; near-identical role density, pad absent in Groove but 8 notes in Drop. Current hashes differ, not necessarily meaningfully audible. | Valid later arrangement development, but avoid weakening Groove/Drop anchor before current groove works. Existing `house_full_arranger` already creates 96–160-bar named sections; improve its role/FX tension grammar rather than write second arranger. |
| Non-kick-aligned intro pumping | **Legacy-only concern** for `sketch/refined`. `groove_template --groove-impact` uses actual kick MIDI onsets for bass/pad ducks and no dry-chord duck. | Test the legacy path separately before changing its defaults; preserve current working groove rules. |
| Register shifting by tonic | **Plausible unresolved melodic/register issue**, particularly in the legacy lead/arp. | Need a validated register-window test across keys, not an abrupt universal pitch fold; prioritize when autonomous lead/melody is in-scope. |
| Automatic lead/arp violates no-melody preference | **Legacy-path mismatch.** The current private native groove-template track list contains no lead or arp, and keeps harmony/pad/drum/bass instrumental roles only. | User-facing default and prompt parsing should eventually match authoritative producer-ready product contract. |
| Thin prompt understanding | **Valid in the current rules parser** for nuanced wording, although the groove-template has additional profile/harmony selectors and full-song minute parsing | Add explicit `recognized/ignored prompt clauses` receipt and bounded semantic profile fields instead of silently claiming full natural-language comprehension. |
| Kick velocity jitter, kick anchors, intro and ends | **Valid in parts**; current groove-template still jitters role note velocity by ±2 even for kick, and short loop ends with prescribed fade behavior | Consider stable kick accents/consistent transition gates after the low-end sound-quality milestone. Do not change Phase44 or current accepted native runs without A/B proof. |
| 40 standards registry not executable | **Correct:** `docs/HOUSE_STANDARDS_REGISTRY.json` status remains `reference-only-not-executed`. | Implement a small set of cheap symbolic gates on the actual **current** groove-template output first (e.g., no unauthorized lead/arp, kick anchors, explicit A/B contrast), then expand gradually. Don't report all 40 as automatically verified. |
| Proposed new house-refined-v2 replacement | **Not accepted** | Keep and extend existing groove-template, SoundCraft native host, vetted private Vitalium source selector, interlock and arranger. No new standalone engine, new incompatible project schema or discarded historical results. |

## Acceptance and next actions

1. **User listening:** identify whether C's original isolated bass, chord, pad or its mixed interaction causes the growl. Compare the pad-only swapped *full mix* before deciding. No automated replacement from this diagnostic.
2. **Low-end generalization:** test candidate source choice and groove-body preservation on at least one other independent key/style if a particular source warning correlates with audible failure. Sustain energy and instrument role matter; cannot cure weak groove with preset variety alone.
3. **Structure and prompt coverage:** after source quality is improved, add meaningful variation gates and coherent main-drop/tension development inside existing modules with old-output rollback.
4. **Never infer professional quality from technical scores.** Require matched-loudness producer listening, locked-MIDI native safety, and preserved baseline evidence.

**Status:** diagnostic prototype and one real C pad-only controlled A/B complete. Suspect identified for review, but causal attribution and musical improvement remain open.
