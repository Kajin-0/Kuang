# SoundCraft test recordings

Recorded from the already installed SoundCraft CLI 0.11.0 on 2026-10-22; no backend is bundled or downloaded by tests.

- `soundcraft-contract.json`: command metadata from `describe` and parameter IDs/units/ranges from `engine.plugins`. The fixture retains the four built-ins used by these tests. These are API facts, not copied implementation code.
- `soundcraft-small-native.json`: a real saved native project generated from Kuang's `tests/helpers.py::small_project`, using SoundCraft built-ins. The musical notes are Kuang's original test data. It contains no rendered audio, samples, presets or external assets.
- `soundcraft-production-plugins.json`: additional factual `engine.plugins` descriptors from the same installed build: compressor, saturator, chorus, modulated delay and plate reverb. Keeps the original contract fixture intact. Real production tests independently verify the live catalog and persisted parameter values.

The fake process transport consumes these recordings to check failure handling and state preservation without installing SoundCraft. The opt-in integration suite executes the actual installed binary and writes separate artifacts. Upstream code is [MIT OR Apache-2.0](https://github.com/storytold/soundcraft/tree/v0.11.0); the binary remains a user-supplied executable.
