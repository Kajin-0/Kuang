# Phase 11: the Vital question and a working live Vitalium VST3 path

Built from **`f830e4560787cab8b75f5fb85edf7be4eac34758`**. Vital was missed in the previous instrument sprint: Phase 0's `examples/vital-bindings.example.json` was an unverified REAPER binding example; Phase 5 tested Surge XT, not Vital. Neither establishes actual Vital support. This phase prioritizes a real external synth lifecycle, rather than another EQ profile.

**Positive result: DISTRHO Vitalium 1.0.6 works live in SoundCraft 0.11.0**, including original wavetable/modulation patches, exact notes and normalized controls, embedded component state, full save/reopen and repeated PCM. **Official Vital has not been instantiated:** an authorized anonymous official Linux binary was not obtained. The distinction matters; this is not a relabelled current Vital build.

## Availability, permissions and separate licenses

Checked conventional user/system VST/VST3/CLAP/LV2 directories and existing project resources: no official Vital installation was found. [Vital's official page](https://vital.audio/) advertises Basic as free with the full synth engine and Ubuntu support. Its [Basic route](https://account.vital.audio/basic) presents registration/login. The anonymous account page provides a login-dependent download view, not an actual downloadable plugin; the official `mtytel/vital` GitHub releases API returned no binary releases. No account creation, login, credential access, hidden-token download or third-party mirror was attempted.

The [official forum's April 2026 thread](https://forum.vital.audio/t/vital-1-6-0-early-access/19076) reports 1.6.0 early access, then 1.6.1 and a Windows-only 1.6.2. These are community reports on the official forum, not confirmation of the current Basic Linux download version. That exact version remains unverified behind the account boundary. The [official source README](https://github.com/mtytel/vital) describes delayed source updates and GPLv3 source, with separate branding/web-service/factory-preset restrictions. It does not authorize redistributing official factory content or pretending a fork is current Vital.

Used the maintained [DISTRHO port](https://github.com/DISTRHO/DISTRHO-Ports/tree/2021-03-15/ports/vitalium), named **Vitalium** with online/account functionality removed. Source files carry GPL-3.0-or-later notices. The project maintainer's [KXStudio plugin listing](https://kx.studio/Repositories%3APlugins) links public packages. The actual [Launchpad package](https://launchpad.net/~kxstudio-debian/+archive/ubuntu/plugins/+files/vitalium-vst_20210315_amd64.deb) is **5:20210315**, **3,024,340 bytes**; its VST3 reports **1.0.6**, DISTRHO. The official PPA Packages record's SHA-256 matches the downloaded package exactly:

`ee73aba51b6342f690a6651a9f5b8c8c823c530c04b4faeaef20ce0ed5d46740`

It was extracted only under `.local/phase11/vitalium/`, not installed system-wide. Reviewed plugin module SHA-256:

`c6329121bd9a4923a54d3e55a9fba9bf8635a1e1d8990fa4be69a05703ed24c1`

Optional patch preparation uses **Pedalboard 0.9.26 (GPL-3.0)** in a separate project-local Python venv, plus its **NumPy 2.5.4** dependency. These total about 22 MB of downloaded wheels; the plugin package is about 3 MB. No build tree/system package/Carla installation was needed. Kuang does not statically link, bundle or relicense these components; none is a default runtime dependency. The external host/plugin binaries, source downloads, factory presets and samples are absent from Git, Kuang's wheel and the listening ZIP. Original patch controls, mathematical wavetable frames, zero unused sample and authored LFO shape are Kuang content under MIT. The optional host reads back and verifies those exact waves/zeros/shape, rather than copying a factory preset.

## Actual host gates and the Surge diagnosis

SoundCraft **0.11.0**, executable SHA-256 **`84466d199a6cb4d4924a9179fdf36b0c6d1ab3a0082b60ceed50d06f09f0b130`**, builtin contract **`5af7ed8eed0e51a251da6dee6f57a9b83ac6ae004c70b13a96416cdee4ad49f7`**. Vitalium VST3 class ID is **`56535456697461766974616C69756D00`**. Discovery, instantiation, MIDI and original patches are distinct gates.

| Probe | Observed result |
| --- | --- |
| Official Vital Linux binary | Not present/obtained; **not tested** |
| Vitalium VST3 discovery | Real class ID, version, vendor, path and instrument flag returned |
| Vitalium initialized patch | Non-silent, unclipped at -18 dB track gain; full native state repeats, initialized PCM does **not** repeat exactly |
| Original fixed-phase Vitalium patches | Non-silent pad/bass/pluck; all 771 controls and full component state restore; native and full-song PCM repeat exactly |
| Surge XT 1.3.4 CLAP and VST3 in SoundCraft | Both reproduce **digital silence**, despite successful device save/reopen |
| Same Surge VST3 in separate Pedalboard host | Non-silent, peak **.267790**, RMS **.060042**, without adding factory content |
| Legacy `mix.instrument_param` on externals | Explicit **not a built-in instrument** failure; not a named external-control API |

The initialized Vitalium patch includes phase randomness; it is not used as a deterministic reference. Original patches set oscillator phase randomness to zero and pass exact repeat checks. This reports the observed difference without treating a device shell as a restored custom patch.

Surge's separate-host result rules out the binary being intrinsically unable to play an initialized sound without extra factory content. Its precise SoundCraft interoperability failure remains unresolved; discovery is not rendering support. Both formats' negative sessions/PCM and the independent-host result are retained as proof. SoundCraft source documents third-party state restoration, MIDI scheduling and numeric parameters; its built-in-only named setter is a deliberate boundary. No invented numeric meanings, missing-factory diagnosis or universal Surge-incompatibility claim is made. Further Surge work stopped once Vitalium provided a working native route. Carla/LV2 and sampler freezing were unnecessary.

`tools/phase11_plugin_gate.py` is a reusable bounded initialized-patch gate, including for a future **user-installed official Vital**. It does not download plugins or claim custom-preset compatibility. Example, with the actual discovered external ID:

```bash
python3 tools/phase11_plugin_gate.py --out-dir .local/phase11/new-plugin-gate \
  --soundcraft /absolute/path/to/soundcraft-cli \
  --vst3-path .local/phase11/your-legally-installed-plugins \
  --instrument 'vst3:ACTUAL_DISCOVERED_CLASS_ID'
```

The new adapter's public capability check intentionally accepts only the reviewed Vitalium module/host. A different official Vital binary must pass a new lifecycle/binding review; it is not silently treated as the fork.

## Live native adapter and exact semantics

`kuang/external_synth.py` is an explicit optional adapter/CLI; **the old SoundCraft adapter, defaults, composer, schema and transactions are unchanged**. `kuang/vitalium_patch.py` constructs original patch data and standard VST3 containers. `kuang/vst3_worker.py` uses an explicitly supplied separate interpreter only when preparing patches. Normal import, canonical editing and rendering already prepared bundles need no Pedalboard/NumPy import.

The preparer checks the real plugin identity, cross-checks SoundCraft's default numeric values against the independent host, writes an original preset, reads back its waves/LFOs/numeric controls, then restores it into a second real plugin. VST3 `.vstpreset`, native component state, minimal original `.vital`, a strict binding table and hashes travel together. The exact reviewed layout hash is **`1cc2cf525f8801a6ca7dc5c643074b4f36dda7b76182b3052da352b9d43452d7`**. A captured metadata fixture contains interface facts only, not a plugin/preset/audio asset.

The canonical instrument uses the real `vst3:` class and a SHA-256 preset reference. Its **771 normalized static controls** have stable IDs `vitalium.param<index>`, mapped to captured names/native IDs. Discrete positions must map to integers. No inferred Hz, pitch, ratio or envelope-ms units are invented: the synth's internal quartic envelope/time and MIDI-note cutoff scales are distinct from canonical normalized values. Native shell instruments have **2851** numeric entries including MIDI-controller plumbing; only the 771 reviewed synth controls are exposed canonically. Existing FX/mixer/EQ lanes retain their original legitimate units.

SoundCraft's `mix.instrument` initializes numeric defaults; `mix.insert_state` stores opaque component state. The adapter supplies both state **and** explicit numeric overrides so default reapplication cannot silently erase the intended patch. The host's shell `preset` label remains **`<factory default>`**; the verified embedded synth state contains **Kuang pad/bass/pluck** names and original content. The generic shell label is not evidence of which sound is loaded.

The adapter exports a verified builtin staging session, then invokes the actual native lifecycle commands to replace only the authorized instruments. It compares the complete persistent state outside those instruments. No native JSON is edited or synthesized. A validation-only in-memory projection reuses the old strict verifier for all note fields, FX, mixer and automation, while external state/parameters are checked independently. Large batches use the real CLI's data-only `script` transport: the original >7000 automation points exceed bubblewrap's argv-count limit. Order and JSON values are preserved and stress-tested. Unknown operations, binaries, bindings, units, discrete positions, lanes, media/buses, paths, locks and drift fail closed.

Exports, saves and edits publish new verified bundles only. `apply` uses the existing typed Engine/Scope/hash/receipt rules and compares full native state outside explicitly edited scalars. Changing a normalized cutoff causes a measured PCM difference; exact undo/redo recovers canonical bytes. MIDI edits remain native notes; fresh export of a changed canonical project is available. `import_project()` is verified snapshot recovery, **not automatic reconciliation of GUI edits**. A moved bundle can use a separately copied identical plugin at another location; plugin paths are provenance, while binary SHA/class/version/contract remain pinned.

All plugin processes run with the root filesystem read-only, only Kuang writable, network unshared, and project-local XDG/TMP paths. No extra tmux, Codex/model process, account or service is involved.

## Three original sounds over unchanged music

The complete **64-bar / 126 BPM / C minor / six-section** Phase 10 song remains. All **1536 notes**, IDs, clips, pitches, timings, velocities, channels, native FX/mixer lanes and the **entire MIDI file bytes** remain exact. Only three instruments change: **body pad, bass, answering arp/pluck**. Original kick, air, lead, percussion, quiet sine pulse and all other tracks remain. Source canonical **`dad1db280f798fdf07ab4b0243bcc6e528f680b30f32b8a5e92104a94ce640b1`**; candidate **`ed567f8198579b7769fdd93cb0134a94ded3b0e77ed6f14f2dafe26227ebb404`**. Original SongSpec is unchanged provenance; canonical schema remains **0.1**.

All three tables use original 2048-sample mathematical frames: sine, a smooth odd-harmonic series and a 32-harmonic saw series, with native interpolation/normalization. No sampled/factory timbre is hidden in the state.

| Patch | Authored engine behavior |
| --- | --- |
| Pad | 7 unison voices; detune internal2.4 (quadratic display5.76%); spread .8; amp **650ms / 1.4s / .64 / 2.6s**; internal LFO1 moves **wavetable frame and filter cutoff**, authored smooth triangle, two-bar tempo setting and stereo phase .15; internal reverb .20 |
| Bass | One centered main saw-rich oscillator plus a quiet centered **upper-octave sine** harmonic layer, not a lower sub; fixed phase; amp **2ms /180ms /.30 /45ms**; Env2→filter cutoff, base MIDI-note78 (~740Hz), low resonance .08; no bass stereo spread |
| Pluck | 3 voices, modest detune/spread; amp **3ms /260ms /.15 /300ms**; Env2 filter attack/decay and LFO wavetable movement; restrained internal delay .13/feedback .23 |

The initial bass patch lost upper-harmonic power after matching loudness and was revised; the first pluck was too loud. Final native master-volume controls are **pad -4.953425 dB / bass -10.707696 dB / pluck -17 dB**. Those are instrument trims, not hidden WAV gains. All original track faders/lanes stay exact. Independent final stems differ from baseline by **-.000023 / +.401691 / -.514265 LU** respectively; the audition stems are additionally matched by constant attenuation only. Tests/measurements do not establish that these sounds are superior.

## Listening and measured limits

Full raw A and B: **48k stereo 24-bit**, **6,091,429 frames /126.9047708 seconds** (64bars+5s tail), no clips, digital-zero final250ms. A is a fresh bounce **byte-identical** to Phase10 D. B's full native session and a separately saved/reopened full PCM repeat exactly. No freezing, external audio track or offline mastering is used in B.

| Full raw file | Integrated LUFS | True peak dBTP | RMS dBFS | Crest dB |
| --- | --- | --- | --- | --- |
| A Phase10 builtins | -25.050292 | -5.339738 | -27.055525 | 21.715788 |
| B live Vitalium | -25.042267 | -5.313822 | -27.129282 | 21.815460 |

Native loudness changes only **+.008024 LU**. Full A/B audition target **-25.050292 LUFS**; matching uses constant attenuation, no hidden EQ/dynamics. Eight-bar drops and all three stem pairs are measured/matched separately. The existing validated Phase9 K-weighted/gated meter and finite FIR true peak are reused; no formal EBU certification or commercial loudness target is claimed.

Same pad MIDI/input with only the internal modulation connections removed gives **-37.676099 dBFS difference RMS**, **33.6621%** of the enabled signal RMS. Native inserts/automation are removed identically in that diagnostic; common track gain -6dB/pan0 and internal reverb remain identical. Six localized spectral windows are retained. This demonstrates actual internal oscillator/filter movement, not a built-in chorus being called oscillator LFO.

Full >500Hz side/(mid+side) rises from **5.2521% to 6.0163%** (side/mid .055433→.064014). B's high-band mono retention **93.9837%**, low **99.999995%**, mono RMS loss **.071031dB**, no fold-down clipping. This full-song width change is modest; the quiet original mix and other tracks remain. It is not a match to a vocal/generative reference or a perceptual quality score.

Download **`artifacts/phase11-vital/phase11-vitalium-listening.zip`**, **85,894,467 bytes**, SHA-256 **`ee1f403f1b7b12f7f3025a598ff33497440f832e066b077e72a48751c7cdea14`**. Full/drop matched A/B, matched pad/bass/pluck pairs, same-input LFO ON/OFF, complete native/canonical/MIDI/original-patch state and measurements are included. Raw full WAVs, native stems, negative gates and proof logs remain on the server.

```bash
scp YOUR_HOST:/home/User/Kuang/artifacts/phase11-vital/phase11-vitalium-listening.zip .
```

Open **`native/session.scraft`** with the separately installed exact Linux Vitalium VST3; keep companions. Original `.vital`/`.vstpreset` files are included under `native/patches/`. **Official Vital1.6/Windows preset compatibility is untested**; its different plugin class is not substituted silently. GUI/editor/display behavior was not tested on this headless VPS. Native MIDI, state and static control changes were tested through the real CLI. Only human audition can decide preference. No Suno audio, vocals, motifs, stems, API or LUFS target were used.

## Reproduce locally without system installation

Use fresh paths and a reviewed optional plugin. These commands extract the public GPL package locally; they do not install system packages or redistribute its binary:

```bash
mkdir -p .local/phase11/downloads .local/phase11/tmp
export TMPDIR="$PWD/.local/phase11/tmp"
curl --fail --location \
  https://launchpad.net/~kxstudio-debian/+archive/ubuntu/plugins/+files/vitalium-vst_20210315_amd64.deb \
  --output .local/phase11/downloads/vitalium-vst_20210315_amd64.deb
sha256sum .local/phase11/downloads/vitalium-vst_20210315_amd64.deb
dpkg-deb --extract .local/phase11/downloads/vitalium-vst_20210315_amd64.deb .local/phase11/vitalium
python3 -m venv .local/phase11/host-venv
PIP_CACHE_DIR="$PWD/.local/phase11/cache/pip" \
  .local/phase11/host-venv/bin/pip install pedalboard==0.9.26 numpy==2.5.4
```

Verify the package checksum above and upstream license before use. Existing system runtime libraries satisfied `ldd`; missing dependencies on another machine are an explicit blocker, not automatically installed. The optional prep environment is separate from Kuang. Bubblewrap must already be user-installed. No runtime tool/test fetches these resources.

With `SOUNDCRAFT_TOOL` and `VITALIUM_PLUGIN` pointing at the user-installed executable and project-local bundle:

```bash
SOUNDCRAFT_TOOL=/absolute/path/to/soundcraft-cli
VITALIUM_PLUGIN="$PWD/.local/phase11/vitalium/usr/lib/vst3/vitalium.vst3"
python3 -m kuang.external_synth prepare --plugin "$VITALIUM_PLUGIN" --soundcraft "$SOUNDCRAFT_TOOL" \
  --host-python .local/phase11/host-venv/bin/python --role pad --volume-db -4.953425072515728 --out-dir .local/phase11/new-pad
python3 -m kuang.external_synth prepare --plugin "$VITALIUM_PLUGIN" --soundcraft "$SOUNDCRAFT_TOOL" \
  --host-python .local/phase11/host-venv/bin/python --role bass --volume-db -10.707695728730297 --out-dir .local/phase11/new-bass
python3 -m kuang.external_synth prepare --plugin "$VITALIUM_PLUGIN" --soundcraft "$SOUNDCRAFT_TOOL" \
  --host-python .local/phase11/host-venv/bin/python --role pluck --volume-db -17 --out-dir .local/phase11/new-pluck
python3 -m kuang.external_synth prepare --plugin "$VITALIUM_PLUGIN" --soundcraft "$SOUNDCRAFT_TOOL" \
  --host-python .local/phase11/host-venv/bin/python --role pad --volume-db -4.953425072515728 \
  --modulation-off --out-dir .local/phase11/new-pad-off
python3 tools/phase11_vital.py --source artifacts/phase10-house --out-dir artifacts/my-phase11 \
  --plugin "$VITALIUM_PLUGIN" --soundcraft "$SOUNDCRAFT_TOOL" \
  --patch-pad .local/phase11/new-pad --patch-bass .local/phase11/new-bass \
  --patch-pluck .local/phase11/new-pluck --pad-mod-off .local/phase11/new-pad-off
python3 tools/phase11_vital.py package --out-dir artifacts/my-phase11
```

An explicit existing `--meter-library .local/phase11/libebur128.so` speeds measurement; Python-only remains available without it. Subsequent native export/save/inspect/render/edit uses prepared assets and needs no Pedalboard interpreter. For example:

```bash
python3 -m kuang.external_synth edit --source artifacts/phase11-vital/native \
  --plugin "$VITALIUM_PLUGIN" --soundcraft "$SOUNDCRAFT_TOOL" --out-dir artifacts/new-cutoff \
  --track track-bass --parameter 'Filter 1 Cutoff' --normalized-value .8
python3 -m kuang.external_synth render --source artifacts/new-cutoff --out-dir artifacts/new-cutoff.wav \
  --plugin "$VITALIUM_PLUGIN" --soundcraft "$SOUNDCRAFT_TOOL"
```

Validation: **277/277 real-host/plugin methods passed**, zero skips/failures/errors, **1464.638s**; offline **277 methods /263 passed /14 optional-host skips**, **314.150s**. All261 earlier methods and7907 historical artifact/example files remain unchanged. The installed wheel reproduces B exactly without importing Pedalboard/NumPy. Tests, wheel/install, historical fingerprints, independent native/PCM/edit/relocation proof and Python3.11/3.13 CI results are recorded in [STATUS.md](STATUS.md), [PHASE11_VERIFICATION.json](PHASE11_VERIFICATION.json) and release `proof/`. Optional tests never download plugins. Main remaining limits are official Vital availability/compatibility, GUI verification, instrument automation and subjective sound quality; no professional/club-ready claim follows from a green test suite.
