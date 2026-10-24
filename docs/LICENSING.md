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
