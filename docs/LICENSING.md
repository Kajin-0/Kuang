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
