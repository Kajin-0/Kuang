# Native MIDI-aligned note-envelope intelligence V1
November 15, 2026. Development branch only; original ten full-length songs, source presets, MIDI and native sessions preserved.

## Why this is important
A note's MIDI onset is not its acoustic arrival. A synth/preset/FX combination can reach its peak tens of milliseconds after the note begins, or sustain significant energy after MIDI note-off. Bass, chords, percussion and hats may thereby feel loose or overly dense despite a correct beat grid. Research in groove/perceptual timing encourages actual audio-envelope analysis rather than globally random MIDI microtiming or blindly increasing volume.

## Implemented
New kuang/house_note_envelope_v1.py analyzes actual native SoundCraft 48kHz stereo PCM24 isolated role audio, aligned to original MIDI chord/bass note onsets in 4–16 active Groove bars. Polyphonic simultaneous chord notes are grouped into a single audible onset. It computes bounded 5ms-window RMS approximations of MIDI-onset to 90% local attack, 10–90% rise time, early 0–30 vs 30–100ms body, 30–100 vs 100–200ms presence, and 60–160ms post-noteoff energy versus the last 40ms before noteoff when no new notes intervene. Instrument FX, VST latency, prior tails and fader automation are part of the measurement; these are NOT literal synth ADSR settings.

The analyzer filters onsets less than 180ms from the previous or 250ms from the next; detects preceding note overlap, low signal, invalid native PCM and incomplete boundaries. Up to 20 qualifying onset groups are processed in deterministic order, with >=3 for sufficient evidence. A dense performance with too little isolation MUST yield evidence_sufficient=false, never a fabricated source-attack score. The exact raw role WAV is discarded after private measurement.

The existing opt-in native source analysis kuang/house_context_palette_native_probe.py now includes the new note_envelopes dict when include_waveform=True, using the same already-rendered native kick/bass/harmony role stems, no extra full-song render. The default public generation or existing experiment results are unchanged.

## Measured real saved source songs
Independent existing native 128bar source projects, same first 16 Groove A bars, original Vital preset/FX/MIDI, 20 measured eligible bass events each.

| Metric | #05 jackin bass | #07 minimal bass |
| --- | ---: | ---: |
| Original MIDI onset groups | 64 | 40 |
| Qualified bass events | 20 | 20 |
| Median MIDI onset to 90% of local peak | **45ms** | **25ms** |
| Median 10-90% attack rise | 10ms | 15ms |
| First 0-30ms vs 30-100ms RMS | **-27.550dB** | **+0.129dB** |
| 60-160ms post-noteoff vs last 40ms before | **-1.194dB** | **-47.552dB** |

The #05 native bass generally builds significant energy after the initial 30ms and retains nearly the same energy well past note-off. #07 arrives sooner with much shorter tails. This could affect perceived groove even though both use typical house MIDI. The observations do not prove either source is better or authorize an automatic substitution.

CRITICAL NEGATIVE FINDING: both songs contain 160 grouped chord attacks in those 16 bars, and ZERO meet 180/250ms isolation. The method correctly abstains from chord source attack estimation. Do not infer a chord attack time or rank the presets based on a dense FX-containing performance. The next source comparison should use a short isolated fixed-velocity chord stimulus at the actual note register, with real source patches and a then separately evaluated fullmix. User explicitly preferred original chord A on #05; do not replace it.

Private numeric evidence for the originals:
- Kuang/.local/house-note-envelope-native-v1-song05-20261115/actual-native-waveform-features.json
- Kuang/.local/house-note-envelope-native-v1-song07-20261115/actual-native-waveform-features.json

## Validation and integration limits
Four new unit tests cover source MIDI grouping and bounds, wrong PCM rejection, silence abstention, and deterministic synthetic 8ms-fast versus 115ms-slow attack recognition including release. A measured difference is only a diagnostic; listening quality remains NOT_EVALUATED. This cannot replace a learned musical evaluator.

Next decisive experiment: bounded, private, runtime-verified fixed-note source tests in a native DAW patch, comparing effective attack and tail across already acceptable source candidates. Only promote across songs when the rendered candidate meets exact source/hash, headroom, mono and independent musical compatibility gates. Do not request the user to adjudicate routine insignificant A/B variants.
