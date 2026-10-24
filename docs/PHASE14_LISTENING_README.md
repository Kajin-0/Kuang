# Phase14 — full-song ensemble production proposal

Start with the two complete WAVs in `listening/`, at the same playback volume:

- **A-Phase13-original-full-LUFS-matched.wav** — the previous six-sampler drum mix.
- **B-Phase14-ensemble-full-LUFS-matched.wav** — new articulated bass, stabs, hook and pad, shared room/plate/echo and actual summed drum compression.

Both are stereo 48k/24bit PCM, **126.9047708 seconds**: the same 64-bar,
126 BPM C-minor song plus five seconds of settled release. Both measure
**−25.0624 integrated LUFS**. Only constant attenuation is used: A0dB,
B−0.3218003dB. No hidden master, limiter, EQ, timing shift or reference audio.
The absolute level is deliberately conservative; adjust your playback volume
for both together. Compare the complete record, especially the breakdown and
main return. These are an unreviewed proposal; no professional-quality claim
or invented human preference follows from technical checks.

The six drum sources, bass notes and original main-call notes retain every
original field. The stabs gain body and distinct envelope articulation, the
hook has its own shorter voice, and the pad sits about1dB behind its previous
role level. Four original Vitalium patches/wavetables replace four built-in
voices; this is DISTRHO Vitalium1.0.6, **not official Vital**. Upper chord voices
lift in the second four bars of each drop phrase, with small accent changes;
eight short response pickups are added at four phrase endings. Exact changes
and original IDs are in `production.json`; original SongSpec remains provenance.
The original sampled kick and groove are retained. The new bass tone is an
alternative, not an asserted improvement in weight or translation.

All six drums feed a real shared compressor aux with their direct Main paths
disabled. Separate short-room, dark-plate and dotted-eighth echo returns give
common depth; phrase-ending sends, filters and scheduled return ducking are
editable automation. Ducking is time-programmed, **not triggered sidechain**.
Native channel pans keep higher synth voices spread; kick/bass/sub stay center.

## Editable projects and replay

`A/native/session.scraft` and `B/native/session.scraft` contain actual MIDI,
live instruments, inserts, sends, aux buses, mixer, automation and six markers.
Their adjacent manifests retain canonical IDs missing from native MIDI.
`A/` and `B/` also contain canonical0.1, type-1 MIDI and source SongSpec.
The complete relative sampler media and original preset/component/control
bindings accompany the native projects. These are live instruments, not
frozen full-track recordings. GUI operation/cross-platform plugin migration
has not been tested on the headless Linux VPS.

A needs separately installed SoundCraft0.11.0. B additionally needs the
reviewed optional **DISTRHO Vitalium1.0.6 Linux VST3** and bubblewrap. There is
no automatic download, paid dependency, account or service. The plugin binary
is **not included**; its GPL license stays separate from MIT Kuang. Preparing
new original patches can use separately installed GPL Pedalboard0.9.26;
prepared-project replay does not need it.

Extract inside a project workspace, then reproduce B with Python3.11+:

```bash
python3 -I reproduce.py --source . --out ./replayed \
  --workspace /absolute/path/to/your/project \
  --soundcraft /absolute/path/to/soundcraft-cli \
  --plugin /absolute/path/inside/workspace/to/vitalium.vst3
```

All source, output and plugin paths must stay inside the explicit workspace.
The script uses the frozen original MIT source in `reproduction/`, rebuilds
canonical state from A and the four original patches, exports via real host
commands, reopens/renders and requires the raw B SHA-256 in `recipe.json`.
The target directory must be new. On the reviewed Linux host replay is
byte-identical, including after original media/patch locations are hidden.
Manual DAW changes are detected as drift; there is no automatic reconciliation.
Use canonical edits plus a fresh export or save a separate native DAW version.

## Rights and limits

Original Kuang code, Fourier wavetables, patches and symbolic music are MIT.
Six inherited original synthesized octal WAVs are publisher-declared CC0,
pinned to commit22d222ce36e290ba3792c776811aa9c69dcc8776; per-file origins,
licenses, original/converted/host PCM hashes accompany the assets and `licenses/`.
The publisher's authorship declaration is not independent title certification.
No plugin binary, factory preset, Suno audio, reference recording or GPL source
implementation is redistributed. `zip-manifest.json` hashes every packaged file.

`verification.json` records full-song matching, spectral/stereo/mono/tail
measurements and internal causal controls. Internal stems are excluded from
this listening download. Meters diagnose behavior; your listening decides
whether this musical direction is better. One-level post-fader aux routing,
static plugin controls and existing linear native lanes are supported here;
pre-fader sends, nested buses, external instrument parameter automation, real
input sidechain and a native master bus remain unsupported.
