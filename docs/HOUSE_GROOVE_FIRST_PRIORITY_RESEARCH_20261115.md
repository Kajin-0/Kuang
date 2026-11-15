# Kuang: Groove-first baseline and reference data review — 2026-11-15

## User evaluation / acceptance priority

- User explicitly selected **chord phrase-coherence B** as sounding much better than the original chord timing in the 16-bar native A/B. Preserve this as a positive local listening result for the chord treatment, not as automatic approval of all future songs.
- User simultaneously reported the **low end and groove as weaker** than earlier music. Most important House quality priority: strong audible kick/bass and musically controlled bassline syncopation. This outweighs continued chord-pattern polish.
- Keep the earlier Phase44/45 stronger low-end reference frozen. Do not overwrite it or globally copy its settings; previous copying experiments were unsuccessful.

## Specific root cause established from private source files

The chosen A/B used `independent-jackin-harmony-20261114`, 16 bars, 128 BPM, with **no `groove_identity_version` metadata**. The stronger later source `gmi-v1-jackin-G-20261114`, 16 bars, 127 BPM, includes **`style-dependent-bass-pocket-v2`**. The bass Vital preset hash and bass fader -12 dB are the same, but the kick sample changed and the bass rhythmic MIDI differs.

In the old reference Groove, the first bar of bass onsets (beats) is `[0.5, 1.5, 2.5, 3.25]` with 0.34-beat principal notes; the later groove-v2 first bar is `[0.5, 1.25, 2.5, 3.25]`, with 0.356-beat long notes and 0.198-beat short notes. This is a meaningful rearrangement of offbeat energy, not a fader change. Distinct kick sample SHA references, both kick faders -10 dB. Chord B itself only changed harmony MIDI; it did not touch bass/drums. Therefore the user's report cannot be attributed to a new bass gain reduction caused by the phrase-coherence code. The A/B was taken from an older source.

Native premix measured loudness is substantially different too: legacy-source A/B `-22.274/-22.254 LUFS` vs groove-v2 A/B `-28.041/-28.044 LUFS`; different sources and levels must be gain-matched before evaluating the two grooves. Do not interpret LUFS difference alone as a bass strength measurement.

## Verified native follow-up

- Separate copy-on-write native candidate generated from later groove-v2 with the B chord algorithm: 21 chord-voice retimings, two coherent 4-bar phrases, zero other-role changes.
- Native export, save and reopen passed; 42.236-second 48 kHz stereo PCM24 render passed, zero clipped samples, both A/B true peak `-5.6342 dBTP`.
- Three separate attenuation-only listening derivatives were metered to `-28.200 LUFS` each; no limiter, EQ, patch selection or irreversible processing.
- A **older groove + preferred chord B**: https://gofile.io/d/cDzK9m2k
- B **newer groove-v2 + legacy chords**: https://gofile.io/d/VVKw47fb
- C **newer groove-v2 + preferred chord B**: https://gofile.io/d/wNCe7UQZ
- Interpretation: C is the engineering candidate combining the two developments; it is not yet an independently listened user-approved winner. Keep all three.

## Recovered prior research: professional House groove

User-supplied `deep-research-report.md` (prior conversation) reports a 2024 experiment on 179 listeners and 20 newly composed House clips: greatest groove when **high low-frequency amplitude and high bassline syncopation occur together**. Broader studies suggest moderate rhythmic surprise with stable beat/meter, not random jitter. The empirical implication is a stable four-on-floor kick, structured offbeat bass attacks with enough physical energy, transient-envelope compatibility and musical role interactions.

Guidance for an evaluable next change:

1. Preserve the same vetted kick and bass sound sources and the 4-bar core motif. Run a **maximum of 3** bounded bass-pattern/envelope alternatives in an existing 8–16-bar native session, with B chord treatment fixed.
2. Record source hashes, bass note onset/duration/velocity changes, kick anchoring, actual isolated kick/bass and full-mix waveforms, phase interactions (23–129 Hz), first 0–120 ms attack, offbeat 120–300 ms energy, mono fold-down loss, spectral energy 40–80 Hz and 80–240 Hz, sidechain duck envelope, true peak, and clipping.
3. Change **one** causal factor per A/B (groove rhythm, note length, kick sample, bass harmonics or duck timing). No blind global bass boost. Maintain original 4/8-bar coherence and source artifacts.
4. Use calibrated loudness matching before judgement. Leave no-change as valid where a candidate fails on actual low-end impact.
5. Compare the best candidate with the frozen Phase44 audio reference **by listening and windowed low-band dynamics**, not merely a spectral/LUFS scalar.

## New reference dataset report: actionable and legal boundaries

User-supplied `deep-research-report (2).md` maps a fragmented reference ecosystem. It identifies:

- Cambridge Mixing Secrets authentic House multitracks, e.g. Galias *Horizon* (20 tracks/363 MB): useful for manual multitrack analysis, but **educational only; research permissions advised; AI training prohibited without separate licensing**.
- IDMT-SMT-Drums (608 44.1 kHz/16-bit WAV; TechnoDrum02/WaveDrum02 true isolated kick-snare-hat stems): useful for non-commercial research diagnostics, **CC BY-NC-ND** so not suitable as commercial sample/training pool.
- MusicRadar House (338 24-bit WAV) and Retro House (330 WAV), Samples From Mars, and 99Sounds: royalty-free use in production where terms permit; **raw sample redistribution prohibited**. Vet exact license before use.
- Freesound original lossless individual **CC0** clips: best potential for redistribution/permissive sourcing; CC BY may require attribution, and per-file generative training preferences must also be respected.
- HOTGAME early 1984–1994 House/Techno: 9,029 tracks and 21 extracted features (bass 20–150 Hz, mid 150–2000 Hz, high 2–10 kHz); **CSV features, not source WAVs**, ~10.4 GB, historic not contemporary mastering norm.
- Modern commercial House and Tech House loudness surveys cited in the report are useful **descriptive** benchmarks, not rules or a reason to maximize LUFS. The survey reports medians ~-9.63 and -8.66 LUFS-I respectively, but that is not a licensed audio dataset or a club-master specification.

Priority for next experiment: **use existing original Phase44 and vetted private Kuang stem WAVs first**, then license-audited CC0/royalty-free kick/bass source alternatives. Do not download 10 GB of features or use restricted Cambridge/IDMT assets to train the commercial app. Research reference measurements remain separated from production assets.

## Stop gate

No promotion of this chord rhythm algorithm to the default based on one song; the user clearly prefers B but also demands recovery of the low-end groove. Give low-end restoration priority; preserve the positive chord preference and evaluate it jointly on stronger rhythm sections.