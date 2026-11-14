# Kuang Groove and Mix Intelligence V1 — engineering record (November 14, 2026)

## Goal

One prompt must produce a convincing and fully editable house production with a physically felt kick/bass pocket and sensible level balance. This work extends, and does not replace, the existing SongSpec, house_template, Groove Identity V2, Musical Planning V2, private Vitalium source selection, CC0 sample kit, SoundCraft native host, harmony interlock and prior Phase44 evidence.

## Implemented native algorithm

Added house_groove_body.py to analyze exactly time-aligned genuine native kick and bass SoundCraft stem WAVs in the active Groove section. Window origin is each real programmed kick MIDI event, not a fixed 126BPM clock. Hann FFT integration over two bands (25–90 Hz sub; 90–250 Hz upper-bass) gives three linear-power-normalized observations per beat: kick 0–100ms, bass 150–250ms and bass 250–350ms. The report stores bass early/late relative to kick and bass late relative to early. It refuses malformed, silent or misaligned audio. This is a spectral source-context diagnostic, not musical taste or a calibrated commercial reference.

Integrated optional --groove-body-review with the already established --contextual-shortlist in autonomous_create/house_one_prompt_context. Uses existing native source-fit kick/bass stems and adds no new default render. The existing source and composition are unchanged unless the old hard safety rescue already independently authorizes a repair.

Added --groove-body-audition, requiring review, to render at most one independently runtime-verified alternate Vital bass candidate when its audited isolated-source upper-band energy fraction differs by at least +8 percentage points. This difference is a conservative compute-eligibility heuristic ONLY; it does not imply the new bass is better. The alternate uses exactly the same MIDI, kick, harmony, other patches, FX, fader gains, time grid and source provenance. Real native save/reopen and final true-peak/clipping gates apply. The candidate and original mix WAV are retained privately, and their sub and upper-bass ratios are compared. No automatic source winner is asserted.

The user previously said simply increasing bass level +3dB did not clearly improve the groove. Consequently this system does not boost all bass tracks, replicate Phase44 mixer gains, or force a particular Vital preset.

## Native independent three-prompt test

Three completely new source prompts were started sequentially in private experiment directory, no duplicate compute:
1. Deep D minor / 124 BPM / seed 118; warm rolling offbeats.
2. Jackin G major / 127 BPM / seed 217; syncopated funk with strong kick.
3. Straight A major / 125 BPM / seed 313; driving groove and wide chords.

Each opts in to Groove Identity V2, Musical Plan V2, verified sample-pack, contextual shortlist, additional groove-body source analysis/candidate audition and previously user-approved section-aware pad level calibration. The full native output must remain editable with a verified host save/reopen, zero clips, known CC0 samples, unchanged private licenses and a clearly marked music-quality listening gate. The original approved C balanced-pad variant and prior A/B songs remain immutable.

## STOP and acceptance

Never claim a source is musically preferable on spectral proxy alone. Retain original bass unless the user explicitly approves an independent matched-volume source audition. Run regression tests on source safety, mode preflight, envelope/frequency logic, no unintended auto-switch, legacy compatibility, source integrity and native export. If a prompt fails in the private pipeline, stop and report it rather than silently substituting weaker audio. Three new valid outputs do not, by themselves, certify studio-grade groove or producer readiness.

Status: implementation underway; actual native three-prompt receipts and listening archive to be added after verified completion.
