"""Role-specific Phase14 designs, original Fourier waves, no factory content.

Values here are the plugin's verified INTERNAL state, not canonical Hz/ms
controls. The independent real plugin restores them and captures normalized
controller bindings before a patch becomes eligible for native export.
"""
from .schema import ValidationError
from .vitalium_patch import original_patch

ROLES={'bass':'bass','stab':'pluck','lead':'pluck','pad':'pad'}
# Calibrated against the actual Phase13 role stems, not a louder mix target.
# Original prototype used -18dB for every voice and buried bass/lead/pad.
PATCH_GAINS={'bass':-.8,'stab':-11.2,'lead':-5.1,'pad':-.8}


def production_patch(voice, *, modulation=True, volume_db=None):
    if voice not in ROLES:raise ValidationError('known producer voice required')
    role=ROLES[voice]
    p=original_patch(role,modulation=modulation,volume_db=PATCH_GAINS[voice] if volume_db is None else volume_db)
    s=p['settings'];s.update(reverb_on=0,delay_on=0,chorus_on=0,
        osc_1_random_phase=0,osc_2_random_phase=0,osc_1_phase=.25,osc_2_phase=.25,
        filter_1_drive=1.2,velocity_track=.5)
    def amp(a,d,sustain,r):
        s.update(env_1_attack=a**.25,env_1_decay=d**.25,env_1_sustain=sustain,env_1_release=r**.25)
    def filter_env(a,d,amount,r=.05):
        s.update(env_2_attack=a**.25,env_2_decay=d**.25,env_2_sustain=0,env_2_release=r**.25,
                 modulation_1_amount=amount)
    if voice=='bass':
        amp(.003,.16,.32,.025);filter_env(.001,.12,.24)
        s.update(osc_1_wave_frame=256,osc_1_level=.36,osc_1_unison_voices=1,osc_1_stereo_spread=0,
            osc_2_on=1,osc_2_wave_frame=0,osc_2_level=.30,osc_2_transpose=0,osc_2_destination=0,
            osc_2_unison_voices=1,osc_2_stereo_spread=0,filter_1_cutoff=80,filter_1_resonance=.07,
            polyphony=1,legato=0)
        links=[('env_2','filter_1_cutoff')]
    elif voice=='stab':
        amp(.0018,.23,.18,.09);filter_env(.001,.19,.40,.07)
        s.update(osc_1_wave_frame=235,osc_1_level=.40,osc_1_unison_voices=3,osc_1_unison_detune=.75,
            osc_1_stereo_spread=.68,osc_2_on=1,osc_2_wave_frame=128,osc_2_level=.15,
            osc_2_destination=0,osc_2_transpose=0,osc_2_unison_voices=1,osc_2_stereo_spread=.25,
            filter_1_cutoff=79,filter_1_resonance=.14,filter_1_drive=1.3,polyphony=16)
        links=[('env_2','filter_1_cutoff')]
    elif voice=='lead':
        amp(.002,.19,.22,.065);filter_env(.001,.17,.24,.05)
        s.update(osc_1_wave_frame=150,osc_1_level=.46,osc_1_unison_voices=2,osc_1_unison_detune=.42,
            osc_1_stereo_spread=.55,osc_2_on=1,osc_2_wave_frame=256,osc_2_level=.08,
            osc_2_transpose=12,osc_2_destination=0,osc_2_unison_voices=1,osc_2_stereo_spread=.30,
            filter_1_cutoff=91,filter_1_resonance=.10,polyphony=8)
        links=[('env_2','filter_1_cutoff')]
    else:
        amp(.26,1.6,.58,1.25)
        s.update(osc_1_wave_frame=190,osc_1_level=.32,osc_1_unison_voices=3,osc_1_unison_detune=1.15,
            osc_1_stereo_spread=.85,osc_2_on=1,osc_2_wave_frame=128,osc_2_level=.10,
            osc_2_transpose=12,osc_2_destination=0,osc_2_unison_voices=2,osc_2_unison_detune=.6,
            osc_2_stereo_spread=.75,filter_1_cutoff=77,filter_1_resonance=.08,
            modulation_1_amount=.12,modulation_2_amount=.045,lfo_1_tempo=7,polyphony=16)
        links=[('lfo_1','osc_1_wave_frame'),('lfo_1','filter_1_cutoff')]
    s['modulations']=[{'source':a,'destination':b} for a,b in links] if modulation else []
    p['comments']='Phase14 '+voice+': coordinated foreground/body/depth design; original Fourier frames; all internal FX disabled for real shared host returns.'
    return p
