# House-v3 P1: Native shared spatial returns on three frozen songs

**Date:** November 16, 2026 UTC. **Status:** nine native SoundCraft A/B/C renders completed (3 styles × 3 scenes). This is a technical spatial production candidate, **not** a subjective favorite or final mix. No defaults were changed.

## Source-locked design

Reference fingerprint showed frozen Kuang groove 2–8kHz side/mid median **−22.954 dB** versus the user-approved **mastered** Phase44 first groove **−8.918 dB** when both were analyzed in the same eight-bar musical window. The gap is directional only: do not prescribe Phase44's width as a universal number or allow sub widening to meet it.

Selected three existing real native 128-bar SoundCraft/Vitalium premasters from the ten-song frozen library:

- **#03 jackin** (Biow Bass 2; WIP-D Retro Piano; minimal house pad 2)
- **#06 deep** (gentle pluck bass; SNFK Loaded Chords; minimal house pad 2)
- **#07 minimal** (gentle pluck bass; minimal house dub stab 23; Strings of Cygnus)

The disliked **LD Bass growling preset was excluded**. All dry instruments, exact MIDI/source/FX/gains, drum kit, kick/bass processing, source preset identities, and original 128-bar projects stayed untouched. An **independent eight-bar Groove A crop** provides each native test nucleus. Native DSP and return tails start from rest when cropped: it is a controlled same-reset A/B/C, *not* claimed sample-exact to the already-running full song at bar 17.

Test variants:

- **A dry:** unchanged source native MIDI, inserts, original faders; no new returns.
- **B room + plate:** two real, one-level post-fader SoundCraft stereo aux buses with 100% wet reverb from already vetted Phase44 built-in settings; chord room −6dB/plate −10dB; pad room −11dB/plate −7dB; spatial returns use the pinned native stereo pan spread at unity, **no low-frequency bass sends**.
- **C room + plate + echo:** B plus a third filtered, 100% wet modulation-delay return sent only from chord at −10dB. C is a causal test of an incremental echo return, not necessarily an approved design.

The production graph remains **native editable**: real bus objects, canonical SoundCraft inserts, real sends, and exact save/reopen verification. No offline fake stereo widening, spectral EQ replacement, exported third-party patches, or "AI hearing" claim.

Each of the nine variants separately passed native export, canonical save/reopen, 48-kHz stereo PCM24, zero clipped samples, ≤−1dBTP, original kick and bass unsent to effects, MIDI byte equality, non-FX source controls/instruments preserved, and unchanged original source-folder inventory.

## Matched eight-bar real native results

| Source | Dry 2–8kHz S/M | B room + plate S/M | B improvement | C room + plate + echo S/M | C improvement |
|---|---:|---:|---:|---:|---:|
| #03 jackin | −23.313 dB | −18.308 dB | **+5.006 dB** | −17.299 dB | +6.015 dB |
| #06 deep | −18.315 dB | −10.136 dB | **+8.179 dB** | −10.272 dB | +8.043 dB |
| #07 minimal | −24.797 dB | −17.586 dB | **+7.211 dB** | −16.580 dB | +8.217 dB |

| Source | B minus A integrated excerpt LUFS | C minus A integrated excerpt LUFS | B true peak dBTP | B 20–120Hz mono retention |
|---|---:|---:|---:|---:|
| #03 jackin | +0.042 LU | +0.336 LU | −5.650 dBTP | 1.000000 |
| #06 deep | +0.362 LU | +1.440 LU | −5.875 dBTP | 1.000000 |
| #07 minimal | +0.264 LU | +0.837 LU | −5.225 dBTP | 1.000000 |

All nine 2–8kHz side/mid values use the same phase-coherent 128-window FFT estimator as P0 and the same source/native context within each case. The upper-frequency *absolute total* energy increased less than **+0.74 dB** in all B versions while side/mid grew considerably. This is a directionally useful spatial expansion rather than just a broad high-frequency gain boost. No sub widening was required. B's full-excerpt RMS changed just **+0.026 / +0.235 / +0.229 dB**.

C may add a desirable musical echo texture in some cases but **does not generalize as consistently**: the deep-house C is **0.136 dB narrower** in 2–8kHz than B and approximately **+1.08 LU louder** than B without establishing improved quality. Avoid adding echo indiscriminately.

## Decision and promotion gate

**Select B (shared room and plate) as the technically stronger opt-in scene for further evaluation, not a production-default or musical winner.** It gives a measured **+5.0 to +8.2dB** increase in high-band stereo width in all three independent sources, without bass mono-loss or output peak violations. C is archived as a negative/uncertain incremental improvement hypothesis; do not turn it on by default.

Still open before normal one-prompt integration:

1. **Isolated chord/pad stems with the actual wet return** to establish ratio of direct attack to 50–500ms tail, not just fullmix width. Avoid obscuring the rhythmic identity of chord stabs with a long plate.
2. Independently calculate mono downmix and spectral interactions across the whole track, and verify no audible-source loss on small speakers.
3. Measure Phase44 and the actual native songs again in **long-form Groove A / Main Drop / Breakdown**, preserving source-specific section differences.
4. Add style/role-aware send strengths, not blindly use one global send recipe.
5. Conduct consolidated final listening only after complete House-v3 mixing, arrangement and mastering. No intermediate producer feedback is requested.

The original source and all generated private A/B/C audio/session data remain on the VPS:
`/home/User/Kuang/.local/house-v3-spatial-AB-20261116/`.

Implementation: `tools/house_v3_spatial_native_ab.py`. This is a separate opt-in experiment; legacy source generation and default routing remain unchanged.

## P1b: runtime-independent library recipe and native reproducibility

External review correctly noted the experimental builder loaded **private Phase44** to copy its effect settings, preventing the routing scene from being a general Kuang library recipe. A new opt-in, pure canonical transform in **`kuang/house_v3_space.py`**, `house_v3_space(project)`, serializes **exactly** the previously measured soundcraft built-in room and plate effect settings, required canonical parameter specifications, bus topology, unchanged four-floor kick/bass tracks, and explicit chord/pad sends. It **does not read any file** or import the producer's private Phase44 project. It fails closed for unknown settings, schema/spec collisions, missing chord source, or repeated application. No effect or send is added to the bass or kick. The caller selects whether to use the recipe; no existing creation default changes.

A fresh **real native SoundCraft export/save/reopen/render** of the jackin #03 B room/plate variant using the library transform was verified against the existing native private trial. Every audio track, bus, insert, send, fader and instrument field matched the prior canonical construction. Their WAVs were **byte-identical**, SHA256:

`6631993ec41fe00260e109349e6cfa0684aabc8573671d23c6de055e2a981bbb`

The rechecked eight-bar 2–8kHz side/mid = **−18.3075 dB** and 20–120Hz mono retention = **1.000000**. This proves deterministic audio parity of the new *library* recipe in the tested native environment. It does not mean the scene has been evaluated musically or that it is approved as a universal default. Other two styles retain the prior independently verified A/B SoundCraft results, and the isolated chord/pad transient/tail check remains open.

Private reproducibility receipt:
`/home/User/Kuang/.local/house-v3-library-recipe-native-recheck-20261116/verification.json`.

## P1c: native isolated chord attack-versus-tail control

The external review reasonably asked whether new stereo space would obscure the rhythmic stabs. Rather than request an intermediate human audition (against the producer's instruction), one causal native **chord-only path** test was performed on jackin #03. The A dry and B room+plate variants were each re-exported from their already validated canonical scene with **every non-chord MIDI track muted**; built-in bus sends and exact chord Vital preset/notes/FX remained native editable. Both original full-song reference artifacts were untouched. Native save/reopen passed for both.

For each original chord note onset, measure stereo squared-amplitude energy during **0–100ms attack** and **250–500ms tail**. Include a note only if no later chord onset occurs inside its tail interval; **16 independent usable onsets** out of 80 actual MIDI note-onset timestamps met that criterion (other overlapping notes excluded). All source note timing is preserved.

- Isolated B vs dry A, **attack 0–100ms energy change: +0.093 dB**.
- Isolated B vs dry A, **tail 250–500ms energy change: +1.241 dB**.
- B true peak remained below digital clipping; native session identity passed.

This is a limited objective indication that the shared return extends space without materially increasing the direct chord attack in this jackin context. It is **not** evidence that the wet tail is psychoacoustically unmasked or that stabs remain subjectively clear in every song. Do not turn the recipe on by default on this result. The deep and minimal styles still require similar isolated pathway checks before role-aware send values are tuned.

Private evidence: `/home/User/Kuang/.local/house-v3-chord-attack-tail-probe-20261116/evidence.json`.

## P1d: deep/minimal native chord-source and kick+bass control

Two further **native source-locked** 8-bar A/B comparisons were rendered using the frozen deep #06 and minimal #07 songs. Per candidate: chord-only and kick+bass-only stereo PCM24/48kHz SoundCraft stems with unchanged Vital MIDI/patches, no other instruments; original bus/send FX preserved; actual canonical export/save/reopen passed. The kick+bass stems are **sample-identical** in dry versus room/plate, confirming these shared effects never touched the rhythm source. Musical preference has not been evaluated.

A source-independent test measures the direct chord attack (0–100ms) and late chord tail (250–500ms). Only onset windows without a second chord attack within the next 500ms qualify.

| Source | Qualified chord windows | Attack energy B–A | Tail energy B–A | 2–8kHz chord power versus kick+bass (A → B) |
|---|---:|---:|---:|---:|
| Deep #06 | 15 | **+0.072 dB** | **+6.980 dB** | +34.463 → +35.209 dB |
| Minimal #07 | 16 | **+0.496 dB** | **+0.711 dB** | −1.177 → −0.132 dB |
| Jackin #03 (earlier separate test) | 16 | **+0.093 dB** | **+1.241 dB** | Not measured against native kick+bass |

The apparent deep-house **+34 dB** presence ratio is a narrow **2–8kHz spectral power** ratio of separately isolated stems, **not** integrated musical loudness or reliable perceptual audibility: the deep kick+bass source has comparatively weak upper harmonics, so this ratio becomes large. It must not be turned into a fixed target or interpreted as proof of overly loud chords.

**Decision:** source-specific spatial treatment is required. Room/plate barely changes chord attacks in all three songs, but its much larger deep-house tail increase is a potential articulation/smear risk even while fullmix upper-band stereo width looks better. Do **not** promote the shared send gains as a global default. Do not infer that an intentionally spacious deep chord tail is inherently bad; assess with an additional source-aware native conditional gate.

`kuang/house_v3_space_review.py` defines provisional, **non-release** objective review flags for >4dB chord-tail increase, >2dB chord-attack increase, or very low 2–8kHz chord/kickbass power. These are diagnostics rather than perceptual labels and never auto-promote a global send scene. The control requires >=8 onset windows, locked MIDI and identical dry/wet kick+bass stems. The high-tail deep source is flagged while the restrained minimal source is not. The producer-rejected growl preset remains excluded and no production default changed.

Private exact native evidence and stems: `/home/User/Kuang/.local/house-v3-chord-presence-crossstyle-20261116/`. Neither files nor third-party presets were uploaded. Next bounded trial: specifically reduce **deep-house plate send** while preserving chord attack and high-band stereo, then compare tail energy and mono/peak safety before selecting style-aware send gains.

## P1e: bounded deep-house plate-trim intervention and stop decision

To check whether the large **+6.980 dB** chord-tail increase in deep-house source #06 could be controlled without losing stereo width, two additional source-locked real native SoundCraft trials were rendered. They used the B room/plate project as-is except for the chord's plate post-fader send. The room send remained **−6 dB**, the chord source/notes/FX were fixed, and kick/bass were not routed into the effects. Both experiments rendered the complete 8-bar native mix plus a separate chord-only native stem, passed canonical export/save/reopen, had zero clipped samples, true peak under −1 dBTP, and preserved 20–120 Hz mono retention at 1.000.

| Deep #06 native variant | Plate chord send | 2–8 kHz fullmix side/mid | Stereo gain vs A dry (−18.315 dB) | Chord onset 0–100ms vs dry | Chord tail 250–500ms vs dry | Preliminary tail gate (≤+4dB) |
|---|---:|---:|---:|---:|---:|---|
| Baseline B room/plate | −10 dB | −10.136 dB | +8.179 dB | +0.072 dB | +6.980 dB | Review |
| D, 6dB plate trim | −16 dB | −11.499 dB | +6.816 dB | +0.043 dB | +4.870 dB | **Not met** |
| E, 12dB plate trim | −22 dB | −11.944 dB | +6.371 dB | +0.035 dB | +4.113 dB | **Not met** |

**Decision:** stop plate-send level sweeps. A 12 dB send reduction did not bring tail buildup below the provisional +4dB review boundary; the additional 6dB cut improved tail by only 0.757dB. The unchanged shared room return and/or the original chord source's sustained timbre may contribute to the remaining tail. That is a hypothesis, **not isolated causal proof**: the individual room-return and native original patch-release signals were not independently measured here. This negative result rules out simple plate-send trimming as a complete solution for this case.

All experiments retained the substantial upper-band spatial benefit and effectively unchanged chord attack, but **technical width and true-peak success do not establish perceptual clarity**. Keep room/plate opt-in, retain source-aware tail warnings, do not introduce a deep-house global plate-send default, and avoid changing provisional thresholds merely to approve this particular source. A future meaningful test should separate direct source sustain from room return before authoring individualized routing decisions.

Private native evidence and audio: `/home/User/Kuang/.local/house-v3-deep-plate-trim-20261116/` and `/home/User/Kuang/.local/house-v3-deep-plate-trim-12db-20261116/`. Source projects, Phase44 master, and original A/B/C renders were not overwritten. No intermediate listener approval requested.

## P1f: causal separation of room and plate, source-aware optional room-only

On frozen deep-house source #06, individually muting each return bus in a separate native SoundCraft render isolated the chord source's measured 250–500ms late-tail response. All original MIDI, patches, drum/kick/bass and source tracks remained fixed. The room-only source delivered +0.032dB attack and +3.805dB tail against dry; plate-only delivered +0.041dB attack and +5.527dB tail; both together delivered +0.072dB attack and +6.980dB tail.

The independent room-only *fullmix* native render retained +6.198dB upper (2–8kHz) side/mid improvement versus dry (−12.1167dB vs −18.315dB), full 20–120Hz mono retention 1.000, true peak −5.875dBTP and zero clipped samples. Real native export/save/reopen succeeded.

The library now exposes an explicitly opt-in room_only scene in house_v3_space. A source-aware technical reviewer only considers this alternative when the original combined room+plate source showed excessive measured tail and the independent native room-only result verifies at least +3dB upper-band spatial improvement, at most +4dB tail, at most +2dB attack change, at least 0.995 sub mono retention, no clipping and <=−1dBTP. This decision is strictly a source-context *technical* choice, never proof of preferred music or an automatic global deep-house rule. No normal production defaults changed.

Evidence preserved on the VPS in .local/house-v3-room-plate-causal-20261117/result.json and .local/house-v3-deep-room-only-fullmix-20261117/evidence.json. This closes the bounded return attribution question; development should move to P2 full-song drum/section development rather than continue wet-send parameter sweeps.
