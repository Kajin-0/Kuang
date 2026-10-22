# REAPER bridge and optional installed Vital

## Implemented adapter contract

Generate an importer with `python3 -m kuang reaper examples/demo.kuang.json out/import.lua --plan out/import.plan.json`. The plan contains the complete validated canonical project, hash, local plugin bindings and honest warnings. Lua contains inert serialized data and the adapter; no JSON parser, SWS extension, network access or external script package is required.

The adapter targets the [official REAPER ReaScript API](https://www.reaper.fm/sdk/reascript/reascripthelp.html). It creates native tracks and MIDI takes, converts quarter-note positions through the host API, sets mixer controls, creates stereo audio sends and section regions, loads bound local FX/presets, and creates native automation envelopes. First-party ReaVerbate wet/bypass controls use the documented `:wet` / `:bypass` identifiers. User plugin controls resolve by host identifier and exact name, with explicit calibration. There are no guessed Vital/VST parameter indices.

The demo's instruments are MIDI placeholders with General MIDI program references where appropriate. They produce no sound by themselves. ReaVerbate is requested from the user's REAPER installation; nothing is bundled. A missing plugin/preset or mismatched parameter fails import and requests REAPER undo. The script refuses tabs with tracks, items, section markers or tempo markers. Use a new empty project tab, even if an existing project looks silent.

Track/clip IDs are stored in native extended fields. The complete original canonical session and hash are stored in project extended state. Note IDs and lock data remain in that manifest; per-note host identity and reverse synchronization are not implemented. Save the imported tab as `.RPP` using REAPER. Human edits in REAPER are native and editable but do not update `.kuang.json` automatically.

Track gain maps dB to linear amplitude; pan stays -1..1. Canonical mute 1 means muted, and native mute envelope values are inverted to REAPER's audible/muted convention. Envelope insertion uses host scaling APIs. Points retain times and converted values; interpolation between converted points needs host validation for gain/nonlinear mappings. Sends explicitly use stereo channels 1/2 and disable MIDI forwarding, with pre-fader/post-FX or post-fader audio routing. The project key remains in the manifest and exported MIDI metadata.

The adapter intentionally rejects audio tracks, unbound plugin controls, unsupported additional track controls, unresolved presets and missing plugin bindings. Empty MIDI tracks and buses remain editable native tracks. Locks constrain canonical operations; they are not a lock on a human editing the `.RPP`.

## Human validation in REAPER

No REAPER process is available on the implementation VPS. These steps remain unexecuted there:

1. Record your REAPER version, OS and installed plugin versions. Generate the seed-7 demo, open a new empty REAPER project tab, and load `out/import_demo.lua` through Actions → ReaScript → Load. Run it.
2. Confirm eight tracks and five regions: Intro bars 1–4, Verse 5–12, Hook A 13–20, Break 21–24 and Hook B 25–32. Confirm 124 BPM and 4/4.
3. Inspect MIDI items in the piano roll. There should be 1,083 note events, editable velocities, channels and durations. Compare a note in a later section against the canonical absolute tick divided by 960. Do not import `demo.mid` on top of this project; that would duplicate notes.
4. Confirm kick/snare/hats use MIDI channel 10 in REAPER's one-based display. Assign suitable already installed local drum and pitched instruments, or route MIDI to your own devices. Confirm mixer gain/pan and pad ReaVerbate wet 0.18. No listening/quality result is implied by the numeric fixture.
5. Inspect the pad volume envelope at ticks 0, 15360, 76800, 92160 and 122880. Compare its point values to -30, -21, -25, -21 and -32 dB. Check actual envelope scaling/interpolation and playback behavior between points; report any host difference before treating the adapter as production-ready.
6. Save as `.RPP`, close and reopen it, and verify notes, names, FX and envelopes remain editable. Confirm imported provenance in project extended state if needed. Exercise native REAPER undo on a fresh import.
7. On a disposable new empty tab, try an unavailable local binding/preset and verify the failed import's undo restores the tab. The mock checks the undo request; real host rollback is still unverified.

The standalone type-1 `.mid` is also usable with REAPER's normal MIDI import. It contains tempo/signature/key, section metadata and symbolic notes/programs. Mixer controls, FX and automation require the Kuang session/Lua path.

## Vital and other user plugins

Use an already installed [Vital](https://vital.audio/) instance if you have one. Phase 0 does not install, redistribute, reverse-engineer, or generate proprietary plugin assets. A reference such as `user:vital` is an opaque user-controlled ID, not a plugin binary path or executable code.

1. Insert your installed plugin manually on a disposable REAPER track. Save your own sound as a **REAPER host preset**, with a chosen name. A `.vital` file is not loaded by this adapter; manually loading it in Vital and saving a host preset is the supported path.
2. Run [tools/inspect_reaper_parameters.lua](../tools/inspect_reaper_parameters.lua) with that track selected. It prints plugin/parameter names, host identifiers and current normalized values without changing parameters. Record plugin version separately.
3. Add a normalized macro to the canonical registry, for example:

   ```json
   {"id":"user.vital.macro1","unit":"normalized","minimum":0,"maximum":1,"default":0,"targets":["instrument"]}
   ```

   Change the chosen canonical instrument to `kind: "plugin"`, `plugin_ref: "user:vital"`, `preset_ref: "user:my-vital-preset"`, `midi_program: null`, and `parameters: {"user.vital.macro1": 0.35}`. Keep its existing stable ID. This is an explicit human configuration edit; run `kuang validate` afterward.
4. Copy [examples/vital-bindings.example.json](../examples/vital-bindings.example.json) to a local file. Replace the FX name, preset name, identifier and exact parameter name with your installed values. The example's placeholder identifiers are deliberately unusable. For normalized controls, measure/check 0 and 1. For physical values such as Hz, provide user-measured piecewise calibration covering the entire canonical registry range. Never assume a cutoff parameter is linear in Hz or that an index remains stable across plugin versions.
5. Generate `python3 -m kuang reaper my.kuang.json out/vital-import.lua --bindings local-bindings.json --plan out/vital-plan.json`. Run it in a new empty tab. Verify host preset resolution and normalized values against the plugin UI; then add canonical automation points for the same instrument ID/parameter and verify the imported FX envelope.
6. Save/reopen `.RPP`, inspect the plugin GUI/preset and automation, and test manual edits. Change the inspection name/identifier in a disposable binding and confirm a mismatch fails rather than selecting an unrelated knob.

Bindings are local adapter configuration, separate from canonical musical intent. Each parameter binding has an exact host `ident`, expected `name`, and at least two calibration points `{value, normalized}`. Canonical values increase strictly; endpoints cover the registry's min/max, and normalized values remain within 0..1. The adapter linearly interpolates this explicit table. It validates identifier/name at runtime and never falls back to a numeric index.

External plugin/preset references do not freeze plugin binaries or full preset state. Audio reproducibility across machines/versions is therefore **not** established. Portable plugin state, measured calibration, curve verification and bidirectional reconciliation belong to the next host milestone.
