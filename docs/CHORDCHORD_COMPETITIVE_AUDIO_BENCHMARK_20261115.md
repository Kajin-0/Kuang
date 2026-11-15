# ChordChord competitive audio benchmark — Kuang's quality floor

Date: November 15, 2026. Status: research-backed product-quality benchmark and experimental plan, **not evidence that Kuang already passes**. This document supplements `docs/PRODUCER_READY_TEMPLATE_PRODUCT.md`; it does not change default composer behavior, historic phase references, or the private preset library.

## Why the target changed

The user tested ChordChord.com in November 2026 and reports its generated songs sound **substantially better** than the ten recent full-length Kuang house productions. User previously called those ten Kuang productions listenable and liked #01 most, but this new direct comparison raises the minimum acceptable level. Kuang must **substantially exceed ChordChord in audible production quality**, rather than merely generate a useful editable scaffold. Ultimately it should produce extremely high-quality mixed **and mastered** house tracks from one prompt.

This is a **user listening observation**, not yet a reproducible blind comparative dataset. Preserve that distinction. The goal is an objectively documented improvement in human listening preference and finished production readiness, not a made-up similarity percentage or higher output gain.

## Verified competitor facts — public sources (November 15, 2026)

- [ChordChord official site](https://chordchord.com/) shows editable chord loops, genre/mood selection, keys/instrument and bass/drum additions, editable melody/drum/chord/instrument editors, and AI Settings.
- [Official product/pricing feature documentation](https://chordchord.com/pricing) describes AI prompt-to-demo chord suggestions, genre-matched accompaniment, style templates, swapping voicings and tempo, MIDI / WAV stems / MP3 / PDFs and DAW import. ChordChord advertises AI. **Its private architecture, actual share of deterministic vs. model generation, sound libraries, mix-bus implementation, and automated mastering algorithm are not publicly verified.**
- [ChordChord's official AI drum-machine explanation](https://chordchord.com/drum-machine) describes an AI drum pattern control, editable kick/snare/closed/open hi-hat grid and transfer to the main ChordChord workspace.
- [ChordChord product landing](https://chordchord.com/welcome) advertises instant editable melody, bass, chords and drums loops for techno, hip-hop and other genres.
- The public marketing pages do **not demonstrate** a verified autonomous native DAW chain capable of context-sensitive full-track mix iteration or release mastering. This absence of public proof is **not** proof that the service lacks those features.
- **No actual user's ChordChord WAV/MP3/MIDI export or direct private share URL was provided for this research.** No ChordChord loudness, stereo, timbre or genre superiority metrics have been measured. The user's qualitative judgment is the correct current verdict.

## Existing Kuang evidence and central failure modes

Existing first-party experimental assets and audits:
- `docs/HOUSE_TEN_FULL_SONG_VARIATION_20261115.md`: 10 user-listenable 128-bar songs, 7/10 independent bass rhythm fingerprints, 7/10 polyphony-collapsed chord stab onset patterns, only four bass/chord and three pad preset identities. All ten main drops have RMS within -0.073 to +0.225 dB of Groove A. Median stereo side/mid -27.34 dB. Unmastered integrated loudness -28.16 to -23.02 LUFS. These are *Kuang-only*, not measured ChordChord values.
- `docs/HOUSE_PHASE44_PRODUCTION_INTELLIGENCE_FORENSIC_20261115.md`: the older hand-developed Phase44 gold reference is more fully produced (independent buses/returns, automation, stereo and mastering); it took 45 controlled production phases and is **not** proof of prompt-to-master reliability.
- `docs/HOUSE_PRODUCER_BRAIN_FIRST_VERTICAL_SLICE_20261115.md`: in user-favorite #01, real isolated native chord RMS was -64.07 dBFS, 34.43 dB lower than kick. Adding a wet aux or +3 dB gain produced almost no effect, whereas a verified alternate compatible Vital chord source improved real relative 1–4kHz spectral energy by **+8.78 dB** and side/mid power by **+15.66 dB**. The musical preference has **not yet** been decided, and an improved spectrum does not guarantee a better song.

**Practical conclusion:** the first-pass *instrument pairing, actual audibility and arrangement grammar* are still more consequential than sophistication of symbolic metrics. The AI producer must learn when to change SOURCE rather than reflexively add EQ, bus effects or make the master louder.

## Fair product-level benchmark: beat the actual ChordChord sound

### Evidence capture / no cherry-picking

Prepare 12 pre-registered prompts in supported house/EDM-adjacent contexts: deep/straight/jackin/minimal, three independent musical intents per profile. Fix requested BPM/key/time feel and no vocals/lead preference as far as both tools support. Generate at least two independent outputs per prompt/platform (24 first-pass candidates per platform). Archive all original generated audio files and settings, including mediocre and failed cases, with dates, prompt text, preset or style choices, source hashes and any interventions. DO NOT secretly select the best Kuang generation, rework one track for 45 phases, or include manually edited ChordChord outputs in a nominally automatic comparison.

If ChordChord cannot accept an exactly matching prompt/key/tempo or seed, record those differences explicitly. Evaluate comparable auto-generated **8–16 bar coherent groove excerpts** as the primary sound-quality contest, since ChordChord's official sources emphasize instantaneous editable loops. Separately evaluate 96–160 bar form/energy development and mastered delivery as Kuang's *extra* differentiator, not as an unfair way to dilute a strong ChordChord groove.

### Audio and listening

- Collect original downloaded ChordChord WAV/stems or best available lossy file, **never synthesize imaginary reference tracks**. Native precision/codec are recorded. Preserve originals.
- Compare **user-facing default exports** as both users would actually hear them; independently make **gain-only loudness-matched** audition copies with a common safe integrated-LUFS target (determine from the actual sources), <0.2 LU residual mismatch and enough true-peak headroom. No limiter or EQ on reference or comparison files. Record every applied gain.
- Randomize/obscure A/B identity. Record groove drive, chord/pad sound quality, drum transient hierarchy, low-end coherence, harmonic presence, image/spatial depth, musical intent and a single overall preference. Headphones and representative speakers/mono are separate checks.
- For the first small milestone, accept **no claim of victory** without repeated blind audible comparisons. A prospective graduation goal: >=65% independent overall Kuang preferences across >=24 prompt/seed pairs with at least 3 experienced listeners; report listener-wise and prompt-clustered uncertainty, and require the confidence interval to exclude 50%. This is an **acceptance target**, not a measured existing score; adjust sample count to the precision actually achieved.
- Use signal metrics as diagnostic controls, **not as a musical-quality reward function**: LUFS-I, 4x oversampled dBTP, crest, band-limited kick/bass alignment, 100/400ms short-term peaks, section loudness arcs, spectrogram, 30–120/120–250/250–1k/1–4k/4–16k band energy, mid/side spectra by frequency, mono fold-down and dynamic masking. True-peak/no-clipping hard safety checks do not substitute for preference.
- Do not label an arbitrary blind A/B as a strict ITU MUSHRA test unless it actually meets the requirements of [ITU-R BS.1534-3](https://www.itu.int/rec/R-REC-BS.1534-3-201510-I/en). Loudness measurement can use [EBU R128](https://tech.ebu.ch/publications/r128) methods; its -23 LUFS broadcast reference is **not** a mandatory house master level.

### Bounded prioritization after recordings exist

| Rank | Proposed production improvement | Cheap decisive validation before expanding |
| --- | --- | --- |
| 1 | **Context-compatible sound selection** with isolated-role audibility, suitable registers/voicings, loudness- and timbre-normalized in-song alternatives | 8–16bar same-MIDI and mix-level A/B, measured full/stem balance, blind listening; preserve all source VST states |
| 2 | **Groove and rhythmic orchestration**: better kick/bass pocket and samples, ghost notes/velocity, hats/percussion and cross-phrase variations without adding lead by default | Same preset/kick source randomized 8–16bar A/B; compare on groove only |
| 3 | **Chord and harmonic musicality**: voice-leading, inversions, lengths, staccato/sustain contrast, syncopation locked to bass pocket, 7th/9th/sus handling where compatible | Frozen chord sources, compare two played phrases, avoid vertical "more notes" metric |
| 4 | **Shared production signal flow**: source-aware EQ, harmonic layering, bus glue, delay/room sends, stereo width/mono safety, articulation and arrangement energy arc | Actual native SoundCraft A/B; reject changes that are inaudible or blur attacks |
| 5 | **Arrangement diversity and transitions**: DJ club vs hypnotic/deep vs jackin/shorter form grammars, breakdown and drop contrasting roles, not generic 8-section copy | 2–3 distinct forms on frozen 8bar groove; compare whole-song pacing without reselecting sounds |
| 6 | **Actual mastering**: dedicated bounded compressor/maximizer/limiter candidate evaluation after the mix is production-ready | Preserve premaster and mastered native projects; LUFS, oversampled dBTP, LRA, PLR, groove preservation and human audition |

Kuang's initial 3-stage architecture remains: deterministic scaffold -> standard production -> **context-aware iterative producer brain**. Its advantage should be that the model can diagnose *this particular song*, test source/arrangement/mix decisions, discard failed trials, choose instrument context wisely and produce a polished full-length editable master. The word "AI" alone is not a quality benefit, and current code has **no unattended model-driven perceptual optimizer**.

## Stop gates

1. **Before expensive refactors:** get one or more of the user's actual better-sounding ChordChord generated WAV/MP3 exports plus the approximate chosen genre/style/BPM/key. Listen/measure against Kuang's #01 and Phase44. Without those bytes, any claim that a 4dB EQ change closes the ChordChord gap is speculation.
2. Establish an actual comparable 8–16bar quality target. If the sound/instrument layer is deficient, do not compensate by endlessly increasing song-form complexity, chasing a mastering LUFS, or writing more symbolic diversity tests.
3. First candidate should be a **sound-selection and groove-preservation** change with a clearly audible improvement across two independent musical contexts. If the user does not prefer it, retain the rejection and revise the hypothesis.
4. No default upgrade, main-branch merge, third-party preset sharing, or unbounded background compute before validated human-listening preference plus native safety gates.
5. After first-pass groove quality closes the competitor gap, add finish-quality intelligent bus/automation and a reproducible master that **substantially exceeds** its beat-demo level.

**Current competitor verdict: user reports ChordChord ahead. Kuang has NOT passed this benchmark.**
