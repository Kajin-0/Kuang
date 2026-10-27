# Phase 2 license/provenance review

Reviewed 2026-10-22 in the existing checkout, on the user's explicit authorization to license original Kuang code under MIT. `LICENSE` now grants MIT terms, attributed to **Copyright (c) 2026 Kuang contributors**. This covers original Kuang code/documentation and generated symbolic fixtures; separate programs/models retain their terms.

The prior tracked history consists of Phase 0 commit `567b4c6` and Phase 1 commit `efdb710`, both credited to the same repository author (Brooks Photonics). Phase 0's recorded status states the remote was empty on clone; no preexisting repository code was imported. A tracked-file inventory and copyright/license/source-reference scan found original Python/Lua implementation, tests, documentation, original generated symbolic JSON/MIDI and factual recorded command/native-output fixtures. No copied upstream implementation, plugin code, presets, samples, models, fonts or vendor binaries were found. This is a repository/history review, not an independent legal chain-of-title audit. No unrelated author's copyright is asserted or removed.

| Component | Distribution/use and terms |
| --- | --- |
| Kuang | Original implementation; MIT; Python runtime uses only the standard library |
| Python | User-installed interpreter, separately licensed under the Python Software Foundation terms |
| setuptools | Build-only requirement, already present locally; MIT; no new runtime dependency |
| SoundCraft 0.11.0 | Optional installed subprocess, not linked/bundled; MIT OR Apache-2.0; built-in synthesis/FX used through its CLI |
| Ollama | Optional installed local inference service, not bundled; MIT |
| Qwen3.5-4B | Optional installed model, not bundled/downloaded; Apache-2.0; only allowlisted local model in this MVP |
| Qwen2.5-3B-Instruct | **Qwen Research license**, not unrestricted Apache; not selected or run for Phase 2 inference and rejected by the planner |
| REAPER / Vital | Optional legacy user-installed integrations only; neither required nor bundled; no real host verification |

The installed SoundCraft release's `share/doc/soundcraft/LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE` and `ATTRIBUTION.md` were inspected. Its code copyright belongs to the ArtCraft Team and SoundCraft contributors; branding/trademarks and egui font notices remain separate. Kuang redistributes none of those assets or executables. Recorded fixture descriptions are API facts, not copied source; the small native fixture contains Kuang's own test notes.

The installed Ollama `/api/show` license metadata reports Apache License 2.0 for `qwen3.5:4b`, consistent with the [official Qwen3.5-4B repository](https://huggingface.co/Qwen/Qwen3.5-4B/tree/main). It reports Qwen Research License for `qwen2.5:3b-instruct`, consistent with the [official license](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE) and [Qwen's release explanation](https://qwenlm.github.io/blog/qwen2.5-llm/). That corrects the earlier assumption that the installed 3B model was permissively licensed. No model weights were downloaded or relicensed. See [SoundCraft source/license](https://github.com/storytold/soundcraft) and [Ollama license](https://github.com/ollama/ollama/blob/main/LICENSE).

No third-party audio, melodies, scores, artist references, presets or sample assets were added. The composer uses newly written diatonic/rhythmic templates, not copied songs. MIT does not grant rights to future third-party material or replace downstream dependency notices. Review future assets/dependencies independently.

Phase 4 adds original house arrangement/production templates, stdlib PCM/FFT measurement code and factual plugin API descriptors from the same user-installed SoundCraft build. No dependencies, synth implementation, third-party presets, samples, plugins or models were added. All new runtime code remains standard-library-only under Kuang's MIT license; the optional host's separate terms are unchanged.

Phase 5 privately evaluates the official [Surge XT 1.3.4 plugin-only Linux archive](https://github.com/surge-synthesizer/releases-xt/releases/tag/1.3.4), separately licensed under [GPLv3](https://github.com/surge-synthesizer/surge/blob/release_xt_1.3.4/LICENSE). The user explicitly authorized this download. Its 97,294,804-byte archive matched the release's official MD5 `0180f06ec7a8445b1c749471e29c702b`; local SHA-256 is `dd431b75f5fa197c4bffa6ca27ca46970f0a94c834119bb1db7decdeec4c28db`. No official SHA-256 was supplied in that release metadata. The archive/extracted plugins and inspected upstream source stay ignored under `.local/phase5/`, with no system/home installation. Surge failed this production gate and is not linked, bundled, redistributed in the wheel/listening ZIP or required by Kuang. No factory content package was downloaded. A future redistribution/integration would require its own license review; the MIT label does not relicense Surge.

The delivered Phase 5 music, MIDI and parameter recipe are original Kuang material using the existing free SoundCraft built-ins. No independently sourced professional recording was downloaded or used as a standard. User-supplied reference comparison requires attribution/license metadata and keeps reference audio outside the listening ZIP. These declarations record user input; they do not establish professional provenance or redistribute permission. New Python runtime remains stdlib only; no commercial model or recursive model call was used.

Future Codex CLI/other-provider planning is not implemented or required. An open-source client does not grant an open license to hosted model weights or remove provider service/account terms, usage limits, subscription costs or API inference charges. Review the exact client license and provider terms when an optional backend is proposed, and record actual costs in the planned A/B benchmark. See [official OpenAI pricing](https://developers.openai.com/codex/pricing) and the [future planner contract](PHASE2.md#future-planner-benchmark-not-implemented). No commercial inference or recursive Codex call was run for Phase 2 production planning.

Phase13 explicitly adds separately attributed **CC0-1.0 sample assets** to its ignored listening/native release, from [octal-samples at pinned commit22d222ce36e290ba3792c776811aa9c69dcc8776](https://github.com/octalmusic/octal-samples/tree/22d222ce36e290ba3792c776811aa9c69dcc8776). The wheel contains only a reviewed CC0 metadata/hash catalog, no audio or plugin binary. The six used WAVs are publisher-declared original synthesis; the complete license, per-file origins, original PCM and derived asset hashes accompany the bundle. Authorship/quality is not independently certified. The pack's unused Unlicense cymbal origins were checked against pinned upstream originals but are not redistributed. Explicit offline resampling uses separately extracted **BSD-2-Clause libsamplerate0.2.2**, not a new mandatory dependency or bundled implementation. Kuang's original code remains MIT; its own frozen source accompanies the reproduction recipe. No GPL/proprietary plugin or factory preset is bundled. [PHASE13.md](PHASE13.md) records source URLs, exact package/hash, scope, conversion and limitations.

Phase14 reuses the six Phase13 declared-CC0 source assets and adds **original
Kuang Fourier wavetables and four role-specific patch designs** under MIT.
No factory preset/sample, third-party DSP implementation, plugin binary or Suno
recording is included in Git, wheel or listening ZIP. The separately installed
[DISTRHO Vitalium1.0.6](https://github.com/DISTRHO/DISTRHO-Ports/tree/2021-03-15/ports/vitalium)
remains GPL-3.0-or-later, invoked as an external live VST3 instrument by the
separately installed MIT/Apache-2.0 SoundCraft host. Original serialized patch/
component settings and the strict Python integration do not statically link or
relicense that synth. Optional original-patch preparation uses separately
installed [Pedalboard0.9.26](https://github.com/spotify/pedalboard),GPL-3.0; prepared
native replay needs neither Pedalboard nor a converter. No new download,
account, paid component or system installation occurs. The portable archive
includes original MIT source/notices and per-file CC0 identities/licenses,
with the external GPL component requirement explicit. Official Vital/latest
application/factory terms are not inferred from Vitalium's GPL fork. See
[PHASE14.md](PHASE14.md) for exact source/host gates and remaining limitations.

Phase15 adds original MIT tuning diagnostics, harmonic-context analysis and a
conservative production/replay script. Its listening ZIP reuses only the same
six declared-CC0 Phase13 samples and original built-in instrument music; **no
Vitalium binary or prepared preset is required or bundled**. Independent
pitch diagnostics privately reuse the already separately installed GPL
Vitalium/Pedalboard components and Kuang's original patches. The optional
native MIDI initializer uses a verified API parameter ID, not copied DSP code.
Pinned SoundCraft source is read only into ignored project-local audit scratch;
no third-party implementation is added to Git/wheel. No reference/Suno audio,
factory material, download, account or system package is introduced. Previous
release files remain unchanged. See [postmortem](PHASE14_POSTMORTEM.md) and
[Phase15 scope](PHASE15.md).


Phase16 authors original MIT FM/phase-shaped role patches using the existing
original Fourier waves and zero unused sample. Tutorial presets were inspected
privately, with no raw redistribution permission inferred from track-use terms.
The pinned CC BY-SA alanjyu bank includes separately credited embedded waves;
those rights were not independently established, so none is used or bundled.
No downloaded preset/wavetable or GPL binary is in Git, the wheel or listening
ZIP. Vitalium1.0.6 and optional Pedalboard remain separately installed external
GPL components; official Vital's account Basic route was not accessed with
credentials. Original patches, component state and all normalized parameters
travel as editable data. The existing six CC0 sample identities/notices remain
unchanged. [Phase16 audit and source URLs](PHASE16.md).


Phase17 reuses the exact human-approved Phase16 original MIT patch/wavetable
content and the same six licensed CC0 sample assets, with their notices and
hashes. No new third-party sound, plugin, bank or code dependency is added. Its
mix profile, timing/PCM diagnostics and frozen replay source are original MIT;
Vitalium remains a separately installed external GPL component. Ableton and
iZotope articles inform general production decisions; no example audio, preset,
implementation or proprietary plugin is copied. Native outputs stay editable;
reference/Suno audio is absent. [Phase17 references and limits](PHASE17.md).


Phase18 composes new original MIDI and automation from the user-approved Phase17
project, retaining the same original MIT Vitalium patches and licensed CC0 samples.
No third-party music, preset, plugin binary or new dependency is added. EDMProd,
MusicRadar and the official Dennis DeSantis/Ableton online chapters inform general
arrangement decisions; no tutorial sound/example or book text is copied. Original
core, note receipts and replay code remain MIT; external GPL Vitalium stays
separately installed. [Phase18 sources and limits](PHASE18.md).


Phase19 is an original MIT editorial transformation of the Phase18 reference,
retaining the same original prepared synth patches and licensed CC0 sample
identities/notices. No new third-party sound, plugin binary, preset bank, book
text, reference recording or runtime dependency is introduced. GPL Vitalium
remains a separately installed component. The journal, continuity/pitch/pulse
checks and frozen replay are original Kuang code/data. [Phase19](PHASE19.md).


Phase20 adds original MIT synth-source designs, production/diagnostic code and a bounded optional terminal-bus adapter. Two newly authored Vitalium patches use the existing original Fourier waves and no factory content; the approved bass/pad states remain. A shorter CC0 kick comes from the previously reviewed octalmusic pack pinned at22d222ce36e290ba3792c776811aa9c69dcc8776. Its source identity, CC0 dedication and explicit offline best-sinc conversion remain in the portable asset manifest; five previous drum assets remain exact. GPL Vitalium/Pedalboard remain separately installed and unbundled; the BSD converter and optional MIT libebur128 meter are not bundled or runtime requirements. Sound On Sound, Ableton, iZotope and EDMProd inform general decisions with attribution in [Phase20](PHASE20.md). No tutorial sound/preset, factory bank, DJ/Suno recording, proprietary plugin binary or new runtime dependency is redistributed. Private reference excerpts are excluded from the listening ZIP and Git.


Phase21 adds original MIT melodic/harmonic MIDI, deterministic composition/audit
code and native verification/replay tools. All four prepared original synth
patches and six licensed CC0 drum assets remain exact; no tutorial music,
reference recording, factory preset, plugin binary or new audio asset is copied.
Attack Magazine and the official Ableton book inform general musical principles,
with links in [Phase21](PHASE21.md). Restricted tutorial downloads are not used.
GPL Vitalium/Pedalboard and SoundCraft remain separate user-installed components;
core runtime remains standard-library-only MIT.

## Phase22 original musical shortlist

The three16-bar compositions, code, note-origin receipts and score reports are original Kuang MIT work. The same earlier licensed CC0 sample assets and original prepared patches are copied with unchanged provenance/notices; no new third-party audio, tutorial preset, factory bank or reference recording is introduced. Research links and unavailable Berklee-page status are recorded in [Phase22](PHASE22.md). Separate user-installed SoundCraft and GPL Vitalium/Pedalboard are not bundled or statically linked into MIT Kuang.

## Phase23 one melody-free groove

The single original score, two synth recipes and Fourier content remain Kuang MIT. Existing licensed CC0 drums and unchanged bass/pulse sources retain their exact notices and hashes. No reference audio, new sample/preset pack, plugin binary or external model is introduced. Separately installed GPL Vitalium/Pedalboard are not bundled or linked into MIT core; SoundCraft stays an optional external host.
