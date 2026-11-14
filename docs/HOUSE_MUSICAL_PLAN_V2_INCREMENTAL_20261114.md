# Kuang Musical Plan V2 — additive harmonic planning (2026-11-14)

## Existing framework remains authoritative

The existing one-prompt producer-ready house template workflow remains the product. V2 is an **opt-in harmonic-progression planning layer** over the existing SongSpec, not a replacement for SongSpec, the composer, house template, groove/harmony interlock, secure private Vital audition, native SoundCraft renderer, house_full_arranger or master-preview systems. All previous Phase43/44/45 reference materials, candidate D and native source evidence remain immutable.

The user positively evaluated the recent groove-aware harmony interlock, but two independent one-prompt songs still selected the same bass/chord Vital presets and the default degree progression [0,4,5,3]. V2 targets the harmonic-progression repetition problem **only**; it does not claim to fix source diversity or professional production quality.

## Concrete opt-in implementation

- New module: kuang/house_musical_plan.py, entry point enrich_house_spec(spec, original_prompt, house_profile), returns NEW validated SongSpec plus versioned decision receipt.
- Style-conditioned, seeded harmonic progressions: deep, straight, jackin, minimal house, each in major and natural minor. Four curated families per style/mode. The key, tempo, bars, instruments, energy, space and seed remain unchanged.
- Explicit user-supplied four-degree Roman numeral progressions remain authoritative. Does not introduce modal support, ninth chords, a new songwriter, forced source diversity or independent lead melodies.
- New opt-in flag --musical-plan-v2 on BOTH the canonical symbolic create path and the private autonomous Vital/SoundCraft one-prompt path. All original paths preserve their behavior by default.
- Plan selected before real-source audition and before composing MIDI; the same existing SongSpec then drives harmony, bass, arrangement, native projects and saved song-spec. Writes musical-plan-evidence.json, metadata and report associations.
- No new network dependency, catalog change, asset copy, host-contract change or schema migration.

## Tests and representative evidence

Focused command: PYTHONPATH=tests:. python3 -m unittest tests.test_house_musical_plan tests.test_house_template tests.test_house_harmony tests.test_house_harmony_interlock tests.test_autonomous_create -q

On the authorized Kuang VPS, 50 tests passed, including eight style/mode groups across 16 seeds, replayable decisions, explicit progression preservation, non-house rejection, legacy-output equivalence, canonical project consistency and original 96-bar arranger compatibility.

| Independent song plan | Legacy degree progression | Experimental progression | Selected family |
| --- | --- | --- | --- |
| Jackin B-flat major, 128 BPM, seed 83 | [0,4,5,3] | [0,4,3,4] | bright_cycle |
| Deep E major, 123 BPM, seed 67 | [0,4,5,3] | [0,3,0,4] | tonic_pedal |
| Minimal F-sharp minor, 122 BPM, seed 29 | [0,4,5,3] | [0,3,0,3] | minor_pedal |

These are degree sequences, not measured musical-quality scores. Distinct progressions still require coherent voice leading, source compatibility and actual groove/harmony listening evaluation.

## Next decisive gates

1. Finish a real native 16-bar private Vital/SoundCraft V2 render and compare with the previous independent prompt/seed baseline, checking exact keys and asset-source provenance, native save/reopen, 48-kHz 24-bit output, true peak and clipping. Do not claim success until this finishes.
2. Compare level-matched rendered audio and preserve the incumbent. V2 remains experimental until user listening confirms improvement; do not declare progress based on chord-degree variety alone.
3. Continue improving context-aware source compatibility by REUSING existing native pair audition and source-fit modules. Never enforce arbitrary preset uniqueness as a substitute for quality.
4. Enrich coherent voice leading and full-song thematic development through the existing harmony and arrangement modules, not a separate composer.

Product intent: one prompt produces different, reliably strong-sounding, mostly finished editable house templates. Stop if this work breaks earlier host/source integrity or silently changes the default path.