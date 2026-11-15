# Kuang house production research and acceptance gates — 2026-11-14

## Grounded references

- Witek et al., *PLOS ONE* 9:e94446 (2014), DOI 10.1371/journal.pone.0094446: perceived groove/pleasure has an inverted-U relation to syncopation in the tested funk break stimuli. This does **not** imply that increasing hats and sixteenth notes is necessarily better for house.
- Nozaradan et al., *PNAS* 2018, *Neural tracking of the musical beat is enhanced by low-frequency sounds*, PMCID PMC6094140: bass-frequency events can increase neural synchronization to a musical beat. Do **not** translate that into simply maximizing kick/sub RMS.
- iZotope, *9 Tips for Producing and Mixing House Music*: kick-vs-bass low-end priority should be identified; avoid excessive overlapping energy, and choose suitable elements before EQ correction.
- iZotope, *How to Mix Kick and Bass*, Dec 21, 2022: time-varying overlap and masking matter; frequency separation and sidechain compression are tools, not universal settings.
- Ableton Live reference (sidechaining in dance music): ducking bass from kick is useful **when** the kick and bass compete; the correct release/depth depends on the two sounds.
- Armada Music, *How To Mix Your Kick & Bass: 5 Must-Know Methods*: some waveform overlap supports continuity; overly aggressive ducking can remove desirable low-end energy.

## Historical evidence from the approved private reference

- Phase32 established distinctive two-bar syncopated bass, kick/percussion pocket and selectively placed atmospheric harmony.
- Phase34, Phase36 and Phase37 worked on bass-relative melodic structure, clearer chord/lead roles and groove arrangement.
- Phase39–40 addressed bass harmonics, chord low-mid masking, drum-bus transient dynamics and microtiming.
- Phase41–43 evolved spatial sends and subtly ducked **pad/plate paths** at kick onsets; Phase44 changed the terminal master while preserving its developed musical mix.
- Phase44 has 22 editable tracks with routing/effects buses; the recent autonomous outputs used 7 direct tracks. Copying phase-specific EQ/saturation/FX settings onto unrelated selected presets was an invalid generalization.

## Rejected experiment

- Commit c10dbd4 transferred the Phase44 effects architecture and fixed frequency/level values into the impact generator; the user explicitly rejected its sound. Reverted in 5694cce without modifying the approved reference. This is an archived *failed musical experiment*, not successful validation.

## Source code defects / sound-quality bottlenecks

1. `house_template.py` generated a 5-dB / ~208-ms pumping envelope **on dry chords and bass alike**. This can suppress groove continuity and dry harmonic attacks. The 16-bar native examples used the same uniform programmed envelope independent of the chosen patch.
2. `autonomous_palette.py` favors one-shot isolated preset features (65% feature proxy, 35% text semantic). It does not evaluate actual kick/bass/chord interactions before accepting the default sources.
3. `house_one_prompt_context.py` skips native alternative auditions whenever the first preset passes hard electrical/audio flags; both tested prompts had **zero** alternatives rendered in mix context despite verified runners-up. It therefore cannot establish musical superiority.
4. `production.py` produces generic chord timing with some bass-aligned attacks. Musical roles should be composed intentionally, not repaired by mechanically shifting every coincident chord by a fixed amount.
5. A full 96–128-bar arrangement or master cannot rescue an unconvincing 8–16-bar nucleus. Treat technical objective scores as rejection/safety guards, **never** as perceptual success.

## Controlled repair shipped in source

The opt-in impact duck now uses kick-MIDI onset scheduling with independent role depths: **bass −3 dB / 115 ms; optional pad −1.25 dB / 143 ms; dry harmony 0 dB**. Those are conservative initial parameters, not universal learned ideals. Non-impact mode is unchanged. No sources, MIDI notes, CC0 drum kit or EQ/reverb master settings are altered.

Focused suites: `PYTHONPATH=tests:. python3 -m unittest tests.test_house_template tests.test_house_source_fit tests.test_autonomous_create -q` — **38 tests passed**. One *private pre-existing baseline* native SoundCraft/Vitalium export+save+render smoke gate passed with bit-identical project MIDI and locked preset identities. This is not a new fully autonomous song, and there is **no listening approval**.

## Next decisive gates; avoid churn

1. **Source-selection experiment.** Evaluate two to four genuinely different kick+bass candidates in the *same* 8-bar native MIDI context. Expose short identical-level excerpts, time-varying kick/bass occupancy and upper-bass harmonic continuity. Reject hard safety failures but do not rank solely by LUFS or FFT targets. Select based on audible groove and mask risk.
2. **Harmony placement.** Once kick+bass pass, audition two musically intentional chord articulation/voicing choices with identical source preset. Verify that bass articulation remains readable. No mechanical global note shift and no simultaneous effects-chain rewrite.
3. **Mix-space policy.** Add dry/wet separation only after independently proving its need. Introduce optional filtered return busses with active gain/stereo assessment, rather than copying fixed values from the old mix.
4. **Expand to 96–128 bars only after the 8–16-bar native context sounds convincing.** Verify sections, lead motif and transitions with real listening, then finalize one-prompt native source/reopen QA.

Prioritize audible success over the count of commits, phases or passes. Preserve failed variants and reports; do not overwrite history or merge the draft branch until approved.
