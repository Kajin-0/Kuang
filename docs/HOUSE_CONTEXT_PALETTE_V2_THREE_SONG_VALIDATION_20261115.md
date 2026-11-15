# Kuang Context-Aware Instrument Selection V2 — three native songs

Date: November 15, 2026. Development branch only. This milestone adds a conservative audibility-based shortlist decision, not autonomous artistic ranking or unattended LLM optimization.

## Problem

Ten full 128-bar house productions were judged listenable, with #01 the user favorite; they remain below the Phase44 production reference and user's preferred ChordChord quality target. A prior same-MIDI audition exposed song #01's exceptionally quiet actual string-stabs chord Vital source. It is important to identify that mismatch without forcing every other song to use a stronger chord instrument.

## Implemented pipeline

- kuang/house_context_palette_v2.py: prompt-dependent chord-role expectation plus actual verified SoundCraft isolated kick/bass/chord role levels; detects a severe audibility mismatch and authorizes at most two alternate verified-source *auditions*, with no automatic source replacement.
- kuang/house_context_palette_native_probe.py: scratch-copy isolated role bounces from the genuine native host; meters actual 48k/24-bit PCM; checks immutable canonical source integrity and deletes scratch role WAVs.
- tools/house_context_palette_v2.py: post-generation private diagnostics on existing verified native projects, requiring exact source-hash-linked independently measured native stems.
- kuang/autonomous_create.py: opt-in --context-palette-v2, available only for full-length groove-template songs. The actual native generation, save/reopen and complete WAV are verified before the real 16-bar isolated role review. The resulting receipt and decision are written separately, with no unapproved preset replacement. Legacy behavior and all defaults remain unchanged.
- Tests check source authenticity, MIDI immutability, prompt specificity, appropriate no-change outcomes, native true-peak/clipping and no quality claims.

The provisional -24 dB chord-versus-kick full-window RMS threshold is only a trigger for further source audition when the user explicitly requests sustained/spacey/wide chords. It is not a suggested output fader, EQ compensation or mastering target. Short stabs may intentionally be quieter, and spectral differences are not musical taste metrics.

## Three independent actual native SoundCraft audits

All three sources are original verified editable 128-bar private projects with identical Groove A first-16-bar measurement protocol. Original native projects, private Vital states and audible WAVs were not edited.

| Song | Intent | Native kick RMS | Native bass RMS | Native chord RMS | Chord vs kick | Review decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| #01 straight F minor 120 BPM | wide sustained chords | -29.643 dBFS | -36.064 dBFS | -64.065 dBFS | **-34.422 dB** | AUDITION verified chords |
| #05 jackin C minor 126 BPM | short piano stabs | -29.436 dBFS | -36.534 dBFS | -39.583 dBFS | -10.147 dB | KEEP current source |
| #07 minimal Db minor 127 BPM | spacey sustained chords | -30.980 dBFS | -39.580 dBFS | -35.785 dBFS | -4.805 dB | KEEP current source |

All three pads were silent inside this particular Groove A passage by arrangement; no erroneous pad replacement was triggered. Stem-level differences quantify sound audibility, not subjective groove appeal.

## Existing actual same-MIDI source audition for #01

Two alternate private Vital sources were already independently runtime-verified and bounced through the actual SoundCraft session with identical #01 note timings, drum/bass instruments, gains and FX. V2 re-evaluated the historical native audio receipts as technically eligible for gain-matched listening, **without selecting an automatic winner**.

| Band/stereo contrast | Original string stabs | B Loaded Chords | C Retro Piano |
| --- | ---: | ---: | ---: |
| 1–4 kHz / 30–250 Hz | -15.671 dB | -6.889 dB | -13.770 dB |
| 250 Hz–1 kHz / 30–250 Hz | -12.014 dB | -4.148 dB | -8.790 dB |
| Stereo side/mid | -37.874 dB | -22.214 dB | -28.832 dB |

B's +8.782 dB presence and +15.660 dB side/mid changes are substantial audio-level differences, not a verified music-quality improvement. Both candidates passed real native save/reopen and no-clipping checks. Source preset B was verified in a separate song, not generated in #01's own single-run shortlist. A usable broader candidate discovery process remains future work.

Gain-only matched listening links (about -23.278 LUFS, no limiter):
- Original A: https://gofile.io/d/s3hJKQOI
- Loaded Chords B: https://gofile.io/d/xJ3OsNVv
- Retro Piano C: https://gofile.io/d/9rRElP0N
- All three WAVs and technical evidence: https://gofile.io/d/NMpmh8oP

## End-to-end fresh native pipeline smoke

A separate fresh 96-bar minimal-house project was generated through the full private one-prompt workflow with the explicit --context-palette-v2 flag. Actual SoundCraft session, Vital instrument patches, CC0 samples, native Save/Reopen, 96-bar real WAV, and three new isolated 16-bar native role bounces were verified. The resulting report declared context_palette_v2_requested true, actual_project_bars 96, native_save_reopen_equal true, 0 clipped samples and true peak -11.147 dBTP. Its standalone context-palette-v2-evidence.json reported chord-vs-kick -32.219 dB RMS, AUDITION_VERIFIED_CHORD_ALTERNATIVES, source_preserved=true, actual_native_host=true, automatic_source_replacement=false. The private smoke output is stored separately from all ten original songs and is NOT a preferred music candidate. Its new audio requires no delivery or user listening for this technical gate.

Regression suite (including earlier core native/composer/source operations) ran 76 tests successfully. Basic V2 module adds 6 direct tests and the create preflight adds the seventh gate.

## Stop gate

Neither #05 nor #07 needs a second preset merely to satisfy a diversity score; a source that is working should be preserved. For #01 the next action is listening approval of the alternative before promoting any source into a default. The code supports an opt-in post-generation audit, **not yet a neural composer/producer that can judge artistic quality or finalize mastered releases**.

The next high-impact milestone, after musical preference is validated across independent contexts, is to make the private candidate source pool broader and acoustically competitive, then improve section energy development and actual final native mastering. Avoid another rewrite of the composition engine or repeated full-length audition sweeps.
