"""Original Phase20 source designs: bass foundation, struck chords, lead bite.

No factory preset/wave content. These are explicit Vitalium INTERNAL settings,
not canonical Hz/ms or guessed normalized host controls. The real two-instance
worker must restore/read back every setting and modulation before native use.
"""
from .studio_palette import studio_patch,PATCH_GAINS
from .schema import ValidationError

TRACKS={'track-bass':'bass','track-harmony':'stab','track-lead':'lead'}
TEMPLATES={'bass':'bass','stab':'pluck','lead':'pluck'}
SOURCE_GAINS={('bass','body'):-11.30579630414811,('bass','edge'):-8.539053391222053,
    ('stab','body'):-6.2615209492101425,('lead','body'):-6.744884966017529}


def groove_patch(voice,*,variant='body',modulation=True,volume_db=None):
    if voice not in TEMPLATES or variant not in ('body','edge') or type(modulation) is not bool:raise ValidationError('explicit source voice/variant/modulation required')
    if voice!='bass' and variant!='body':raise ValidationError('only the bass has a second authored source variant')
    p=studio_patch(voice,modulation=False,volume_db=SOURCE_GAINS[(voice,variant)] if volume_db is None else volume_db)
    s=p['settings']
    # Keep an unambiguous tuned core; pitch is never a modulation destination.
    s.update(osc_1_transpose=0,osc_1_tune=0,osc_1_random_phase=0,
        osc_2_transpose=12,osc_2_tune=0,osc_2_random_phase=0,
        osc_3_transpose=0,osc_3_tune=0,osc_3_random_phase=0,
        osc_1_phase=.25,osc_2_phase=.25,osc_3_phase=.25,
        osc_1_unison_voices=1,osc_2_unison_voices=1,osc_3_unison_voices=1,
        osc_1_stereo_spread=0,osc_2_stereo_spread=0,osc_3_stereo_spread=0,
        osc_1_pan=0,osc_2_pan=0,osc_3_pan=0,
        osc_2_destination=0,osc_3_destination=0,
        reverb_on=0,delay_on=0,chorus_on=0,distortion_on=0,
        filter_1_keytrack=1,filter_1_resonance=.08,velocity_track=.5)
    def env(i,a,d,hold,r):
        s.update({f'env_{i}_attack':a**.25,f'env_{i}_decay':d**.25,
            f'env_{i}_sustain':hold,f'env_{i}_release':r**.25})
    if voice=='bass':
        # Develop the approved FM family instead of adding sub to an already
        # low-heavy mix. The rejected sine-layer trial reduced useful harmonics.
        env(1,.003,.17,.48,.025);env(2,.001,.105,0,.020)
        s.update(osc_1_wave_frame=80 if variant=='body' else 220,osc_1_level=.64,
            osc_1_distortion_type=7,osc_1_distortion_amount=.08 if variant=='body' else .055,
            osc_2_on=1,osc_2_wave_frame=0,osc_2_level=0,
            osc_3_on=0,osc_3_wave_frame=0,osc_3_level=0,
            filter_1_cutoff=88 if variant=='body' else 94,filter_1_drive=1.35,polyphony=1,legato=0,
            modulation_1_amount=.13,modulation_2_amount=.19)
        links=[('env_2','osc_1_distortion_amount'),('env_2','filter_1_cutoff')]
    elif voice=='stab':
        # Warm saw/triangle chord strike and a quieter octave texture. Separate
        # envelope from the slow approved pad; no detuned bass fundamentals.
        env(1,.0015,.18,.22,.085);env(2,.001,.14,0,.045)
        s.update(osc_1_wave_frame=215,osc_1_level=.65,
            osc_1_distortion_type=0,osc_1_distortion_amount=0,
            osc_2_on=1,osc_2_wave_frame=256,osc_2_level=.12,
            osc_2_pan=-.55,osc_1_pan=.15,osc_2_phase=.32,
            osc_3_on=0,filter_1_cutoff=100,filter_1_drive=1.35,
            lfo_1_tempo=7,lfo_1_stereo=.30,
            modulation_1_amount=.28,modulation_2_amount=.05,
            polyphony=16)
        links=[('env_2','filter_1_cutoff'),('lfo_1','osc_1_wave_frame')]
    else:
        # A harmonic pluck that speaks above the bass/chord body. Mild integer
        # FM changes the strike, not its tuning; no broad supersaw replacement.
        env(1,.0015,.20,.20,.050);env(2,.001,.09,0,.030)
        s.update(osc_1_wave_frame=256,osc_1_level=.65,
            osc_1_distortion_type=7,osc_1_distortion_amount=.02,
            osc_2_on=1,osc_2_wave_frame=0,osc_2_level=0,
            osc_3_on=0,filter_1_cutoff=105,filter_1_drive=1.25,
            modulation_1_amount=.27,modulation_2_amount=.075,
            velocity_track=.45,polyphony=8,osc_1_unison_voices=3,
            osc_1_unison_detune=.12,osc_1_stereo_spread=.55)
        links=[('env_2','filter_1_cutoff'),('env_2','osc_1_distortion_amount')]
    s['modulations']=[{'source':a,'destination':b} for a,b in links] if modulation else []
    # Keep the existing strict original-content preset-name contract; role and
    # version are explicit in the original comments and prepared folder map.
    p.update(comments='Phase20 '+voice+' '+variant+': original source design, role-specific harmonic body and envelopes; integer tuning; original Fourier waves; no factory content.')
    return p
