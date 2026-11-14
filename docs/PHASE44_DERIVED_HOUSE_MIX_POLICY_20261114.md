# Phase 44–derived editable house mix policy (2026-11-14)

## Scope and evidence

This is a transfer of techniques from the approved private Phase39–44 house production, **not** a copy of its score, licensed synth preset or waveform. It is enabled only with `groove_impact=True` / `--groove-impact` in the groove-template workflow. Legacy paths and prior listening artifacts remain unchanged. The new policy improves engineering control but has **not** been approved through human listening.

Independent history inspection:

- Phase39: drum color, bass upper harmonics, independent filtered chord-delay return automation, percussion microtiming.
- Phase40: 150-Hz bass vs 330-Hz chord frequency differentiation, 600-Hz bass harmonic lift, slower drum-bus glue compressor attack, filtered chord delays.
- Phase41–42: distinct moving spatial returns with controlled break/transition throws.
- Phase43: kick-timed 1.25-dB pad and 2-dB plate-return ducks (approximately 143 ms), not a real detector-driven sidechain.
- Phase44: master-bus-only compressor and maximizer change; **not** the source of earlier groove/harmony separation.

## Implemented policy

- Shift harmony notes by 240 ticks (= 119 ms at 126 BPM) only when their attack is within 24 ticks of a bass attack and clip boundaries allow it. The bass and drum MIDI notes remain unchanged. No reference-song note sequence is copied.
- Reduce foreground harmony channel by 2.5 dB relative to its starting fader and automation; apply 230-Hz high-pass and 7.5-kHz low-pass, plus restrained low-mid EQ to reduce competition with bass.
- Bass: 32-Hz high-pass, 1.8-kHz low-pass, harmonic emphasis around 600 Hz, stronger saturation and 18-ms-attack/110-ms-release compression. These are Phase40-inspired **starting settings**, not universally optimal presets.
- Route kick, snare, hats, auxiliary percussion and open hats through an editable drum bus, with 28-ms-attack/105-ms-release parallel glue compression and modest saturation.
- Disable the original harmony/pad insert plate reverbs and introduce a separate filtered, 100%-wet reverb bus, independently ducked by 2 dB at actual kick MIDI onsets with a 288-tick (~143 ms) recovery.
- Create two independently filtered chord-delay returns: one eighth and one dotted-eighth note, independent left/right panning, high-pass at 450 Hz and low-pass at 4.4 kHz.
- Preserve separate editable dry chord source and source-to-return sends; no audio-driven sidechain is claimed.

## Technical validation

- Focused unittest suites: **38 pass** (`PYTHONPATH=tests:. python3 -m unittest tests.test_house_template tests.test_house_source_fit tests.test_autonomous_create -q`).
- Local private native SoundCraft 0.11.0/Vitalium smoke test: export, save/reopen, native 16-bar rendered audio **PASS** for the same source/project, with preserved kick/bass note events and source patch identities. Smoke project and render under `.local/phase44-derived-generator-validation-20261114/` on authorized VPS. It tests the production policy applied to the existing private baseline, **not** an independently freshly selected one-prompt mix.
- No subjective sound quality or cross-profile acceptance is asserted. High-level one-prompt native regression still deserves cross-profile testing before promotion.

## Technical constraints

- Settings are currently opt-in and intentionally source-independent. The actual source spectra and perceptual groove may require calibrated profile-specific ranges.
- Both the original `production-harmony-duck` and the new independent spatial-return duck remain kick-timed MIDI gain envelopes, not audio-input sidechains.
- Existing audio stems, approved reference and private presets remain in `.local/` and must never be committed to the public repository.
