"""Original, pitch-stable Phase16 Vitalium sound palette.

Internal synth controls (not canonical Hz/seconds): envelope times are fourth
roots of seconds, cutoff is a MIDI note, levels are quadratic. Only the real
1.0.6 plugin's captured normalized bindings can enter the native adapter.
No downloaded preset, factory wavetable or sample is used.
"""
from .schema import ValidationError
from .vitalium_patch import original_patch

ROLES = {'bass': 'bass', 'stab': 'pluck', 'lead': 'pluck', 'pad': 'pad'}
TRACKS = {'track-bass': 'bass', 'track-harmony': 'stab',
          'track-lead': 'lead', 'track-depth-pad': 'pad'}
# First full-song stem calibration, before any post-insert mix correction.
# Lower oscillator output also prevents driving inherited compressors harder
# merely because the replacement synth has a hotter default output.
PATCH_GAINS = {'bass': -11.3849088523, 'stab': -9.3286659978,
               'lead': -4.0221133029, 'pad': -1.2647295761}


def studio_patch(voice, *, modulation=True, volume_db=None):
    if type(voice) is not str or voice not in ROLES or type(modulation) is not bool:
        raise ValidationError('explicit studio voice and boolean modulation required')
    p = original_patch(ROLES[voice], modulation=False,
                       volume_db=PATCH_GAINS[voice] if volume_db is None else volume_db)
    s = p['settings']
    # Pitch has no modulation source. Deterministic phases, no random detune,
    # no hidden octave/fine tuning. Osc2 is an integer-ratio FM exciter.
    s.update(reverb_on=0, delay_on=0, chorus_on=0, distortion_on=0,
             osc_1_on=1, osc_1_transpose=0, osc_1_tune=0,
             osc_2_on=1, osc_2_transpose=12, osc_2_tune=0,
             osc_2_wave_frame=0, osc_2_level=0, osc_2_destination=0,
             osc_2_unison_voices=1, osc_2_stereo_spread=0,
             osc_3_on=0, osc_3_random_phase=0,
             osc_1_unison_voices=1, osc_1_stereo_spread=0,
             osc_1_random_phase=0, osc_2_random_phase=0,
             osc_1_phase=.25, osc_2_phase=.25,
             filter_1_model=0, filter_1_style=0, filter_1_drive=1.1,
             filter_1_keytrack=1, filter_1_resonance=.08,
             velocity_track=.40, polyphony=16, legato=0)

    def envelope(i, a, d, sustain, r):
        s.update({f'env_{i}_attack': a**.25, f'env_{i}_decay': d**.25,
                  f'env_{i}_sustain': sustain, f'env_{i}_release': r**.25})

    if voice == 'bass':
        # Rubber-like mid-bass: harmonically stable sine FM body + a little
        # original triangle, short release clearing the offbeat/kick pocket.
        envelope(1, .002, .145, .42, .026)
        envelope(2, .001, .105, 0, .020)
        s.update(osc_1_wave_frame=36, osc_1_level=.64,
                 osc_1_distortion_type=7, osc_1_distortion_amount=.065,
                 filter_1_cutoff=85, filter_1_drive=1.25, polyphony=1,
                 modulation_1_amount=.16, modulation_2_amount=.20)
        links = [('env_2', 'osc_1_distortion_amount'), ('env_2', 'filter_1_cutoff')]
    elif voice == 'stab':
        # Dry struck tine/reed chords, not a broad detuned supersaw. The FM
        # envelope gives a short bright strike followed by a woody body.
        envelope(1, .0015, .23, .13, .065)
        envelope(2, .001, .115, 0, .035)
        s.update(osc_1_wave_frame=12, osc_1_level=.62,
                 osc_1_distortion_type=7, osc_1_distortion_amount=.12,
                 filter_1_cutoff=100, filter_1_resonance=.10,
                 modulation_1_amount=.29, modulation_2_amount=.13,
                 modulation_3_amount=.06)
        links = [('env_2', 'osc_1_distortion_amount'), ('env_2', 'filter_1_cutoff'),
                 ('note', 'osc_1_distortion_amount')]
    elif voice == 'lead':
        # Focused, rounded phase-warp pluck. No pitch envelope, vibrato or
        # unison beating: the existing three-note call remains the foreground.
        envelope(1, .002, .17, .30, .055)
        envelope(2, .001, .12, 0, .035)
        s.update(osc_1_wave_frame=238, osc_1_level=.61,
                 osc_1_distortion_type=4, osc_1_distortion_amount=.48,
                 osc_2_on=0, filter_1_cutoff=95,
                 modulation_1_amount=.19, modulation_2_amount=.11)
        links = [('env_2', 'filter_1_cutoff'), ('env_2', 'osc_1_wave_frame')]
    else:
        # A narrow, in-tune core with slow stereo timbral motion. Width comes
        # from real stereo chorus, not pitch drift or an out-of-tune detune.
        envelope(1, .42, 1.5, .62, 1.45)
        envelope(2, .25, 2.2, .30, 1.2)
        s.update(osc_1_wave_frame=190, osc_1_level=.36,
                 osc_1_distortion_type=6, osc_1_distortion_amount=.50,
                 osc_2_on=1, osc_2_transpose=0, osc_2_wave_frame=90,
                 osc_2_level=.30, osc_2_stereo_spread=0,
                 osc_1_pan=-.90, osc_2_pan=.90, osc_2_phase=.32,
                 filter_1_cutoff=79, filter_1_resonance=.05,
                 lfo_1_tempo=7, lfo_1_stereo=.38,
                 modulation_1_amount=.13, modulation_2_amount=.055,
                 modulation_3_amount=.10)
        links = [('lfo_1', 'osc_1_wave_frame'), ('lfo_1', 'osc_1_distortion_amount'),
                 ('env_2', 'filter_1_cutoff')]
    s['modulations'] = [{'source': a, 'destination': b} for a, b in links] if modulation else []
    p['comments'] = ('Phase16 original '+voice+'; original Fourier waves; integer tuning; '
                     'role-specific articulation and timbral modulation, no factory content.')
    return p
