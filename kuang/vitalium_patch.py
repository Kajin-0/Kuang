"""Original Vitalium 1.0.6 patches and standard VST3 preset containers.

No factory content, samples, synth code or plugin binary. Engine values are
explicitly INTERNAL controls: envelope times are fourth roots of seconds,
filter cutoffs are MIDI-note numbers, volume is (80+dB)**2. Canonical edits
use the separately discovered normalized controller bindings, never fake units.
"""
import base64
import json
import math
import struct
from copy import deepcopy

from .schema import ValidationError,strict_json

PLUGIN_ID='vst3:56535456697461766974616C69756D00'
CLASS_ID=PLUGIN_ID.split(':')[1]
VERSION='1.0.6'


def original_patch(role,*,modulation=True,volume_db=None):
    if role not in ('pad','bass','pluck') or type(modulation) is not bool:
        raise ValidationError('expected pad/bass/pluck and a boolean modulation option')
    db={'pad':-12,'bass':-8,'pluck':-6}[role] if volume_db is None else volume_db
    if type(db) not in (int,float) or not math.isfinite(db) or not -30<=db<=0:
        raise ValidationError('patch level must be -30..0dB')
    def frame(position,kind):
        values=[]
        for i in range(2048):
            x=2*math.pi*i/2048
            v=(math.sin(x) if kind=='sine' else
               .48*sum(math.sin(h*x)/h for h in range(1,33)) if kind=='saw' else
               .8*sum(math.sin(h*x)/(h*h) for h in range(1,24,2)))
            values.append(v)
        return {'position':position,'wave_data':base64.b64encode(struct.pack('<2048f',*values)).decode()}
    wave={'name':'Kuang original Fourier morph','author':'Kuang','version':VERSION,
          'full_normalize':True,'remove_all_dc':True,'groups':[{'components':[{
          'type':'Wave Source','interpolation':1,'interpolation_style':1,
          'keyframes':[frame(0,'sine'),frame(128,'soft'),frame(256,'saw')]}]}]}
    s={'volume':(80+db)**2,'sample_on':0,'osc_1_random_phase':0,
       'osc_2_random_phase':0,'osc_1_phase':.25,'osc_2_phase':.25,
       'osc_1_level':.55,'osc_2_on':0,'osc_3_on':0,'beats_per_minute':2.1,
       'filter_1_on':1,'filter_1_resonance':.12,'filter_1_drive':1,
       'filter_1_cutoff':82,'osc_1_wave_frame':100,'osc_1_destination':0,
       'lfo_1_sync':1,'lfo_1_sync_type':0,
       'lfo_1_tempo':5,'lfo_1_stereo':.15,'velocity_track':.25,
       'sample':{'length':32,'name':'Kuang unused zeros','sample_rate':48000,
                 'samples':base64.b64encode(bytes(64)).decode()},
       'wavetables':[deepcopy(wave) for _ in range(3)],
       'lfos':[{'name':'Kuang smooth triangle','num_points':3,
                'points':[0,1,.5,0,1,1],'powers':[0,0,0],'smooth':True}]}
    connections=[]
    if role=='pad':
        s.update(env_1_attack=.65**.25,env_1_decay=1.4**.25,env_1_sustain=.64,
                 env_1_release=2.6**.25,osc_1_unison_voices=7,osc_1_unison_detune=2.4,
                 osc_1_stereo_spread=.8,osc_1_wave_frame=70,modulation_1_amount=.35,
                 modulation_2_amount=.13,reverb_on=1,reverb_dry_wet=.20,
                 reverb_decay_time=1.3,reverb_pre_low_cutoff=72)
        connections=[('lfo_1','osc_1_wave_frame'),('lfo_1','filter_1_cutoff')]
    elif role=='bass':
        s.update(env_1_attack=.002**.25,env_1_decay=.18**.25,env_1_sustain=.30,
                 env_1_release=.045**.25,osc_1_unison_voices=1,osc_1_stereo_spread=0,
                 osc_1_wave_frame=256,filter_1_cutoff=78,filter_1_resonance=.08,
                 osc_2_on=1,osc_2_level=.32,osc_2_transpose=12,osc_2_destination=0,
                 osc_2_unison_voices=1,osc_2_stereo_spread=0,osc_2_wave_frame=0,
                 env_2_attack=.002**.25,env_2_decay=.14**.25,env_2_sustain=0,
                 env_2_release=.04**.25,modulation_1_amount=.20)
        connections=[('env_2','filter_1_cutoff')]
    else:
        s.update(env_1_attack=.003**.25,env_1_decay=.26**.25,env_1_sustain=.15,
                 env_1_release=.30**.25,osc_1_unison_voices=3,osc_1_unison_detune=1.5,
                 osc_1_stereo_spread=.65,osc_1_wave_frame=180,filter_1_cutoff=76,
                 env_2_attack=.002**.25,env_2_decay=.18**.25,env_2_sustain=0,
                 env_2_release=.20**.25,modulation_1_amount=.27,
                 modulation_2_amount=.12,delay_on=1,delay_sync=1,delay_tempo=7,
                 delay_style=1,delay_dry_wet=.13,delay_feedback=.23)
        connections=[('env_2','filter_1_cutoff'),('lfo_1','osc_1_wave_frame')]
    s['modulations']=[{'source':a,'destination':b} for a,b in connections] if modulation else []
    return {'synth_version':VERSION,'preset_name':'Kuang '+role,'author':'Kuang',
            'comments':'Original Fourier waves and controls; no factory preset/sample.',
            'preset_style':role,'macro1':'Tone','macro2':'Motion','macro3':'Space','macro4':'Shape',
            'settings':s}


def component(patch):
    """JUCE VST2-compatible component state, not a SoundCraft JSON edit.

    VstW extension + standard FBCh bank header + UTF-8 synth state. This exact
    format is read back from the actual 1.0.6 plugin in the integration gate.
    """
    data=json.dumps(patch,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    if len(data)>2**20:raise ValidationError('patch exceeds 1MiB')
    payload=data+bytes(17)+b'JUCEPrivateData'
    fxb=b'CcnK'+struct.pack('>I',152+len(payload))+b'FBCh'+struct.pack('>IIII',2,0x56697461,0x10006,0)+bytes(128)+struct.pack('>I',len(payload))+payload
    return b'VstW'+struct.pack('>III',8,1,0)+fxb


def vstpreset(state):
    if type(state) is not bytes or not 0<len(state)<=2**21:raise ValidationError('invalid component size/type')
    end=48+len(state)
    return (b'VST3'+struct.pack('<i',1)+CLASS_ID.encode()+struct.pack('<q',end)+state+
            b'List'+struct.pack('<i',2)+struct.pack('<4sqq',b'Comp',48,len(state))+
            struct.pack('<4sqq',b'Cont',end,0))


def chunks(data):
    if type(data) is not bytes or not 56<=len(data)<=2**22 or data[:8]!=b'VST3\x01\0\0\0' or data[8:40]!=CLASS_ID.encode():
        raise ValidationError('expected bounded Vitalium 1.0.6 VST3 preset')
    offset=struct.unpack_from('<q',data,40)[0]
    if not 48<=offset<=len(data)-8 or data[offset:offset+4]!=b'List':raise ValidationError('bad preset table')
    count=struct.unpack_from('<i',data,offset+4)[0]
    if count!=2 or offset+8+20*count!=len(data):raise ValidationError('unexpected preset chunks/trailing bytes')
    result={}
    for i in range(count):
        kind,start,size=struct.unpack_from('<4sqq',data,offset+8+20*i)
        if kind not in (b'Comp',b'Cont') or kind in result or start<48 or size<0 or start+size>offset:
            raise ValidationError('invalid/overlapping preset chunk')
        if kind==b'Comp' and (start!=48 or start+size!=offset):raise ValidationError('unexpected component layout')
        if kind==b'Cont' and (start!=offset or size):raise ValidationError('unexpected controller state')
        result[kind]=data[start:start+size]
    return result


def component_patch(state):
    """Strictly decode only the observed JUCE/Vitalium data format."""
    if (type(state) is not bytes or not 208<=len(state)<=2**21 or
        state[:16]!=b'VstW'+struct.pack('>III',8,1,0) or state[16:20]!=b'CcnK' or
        state[24:28]!=b'FBCh' or state[28:44]!=struct.pack('>IIII',2,0x56697461,0x10006,0) or
        state[44:172]!=bytes(128) or state[-32:]!=bytes(17)+b'JUCEPrivateData' or
        struct.unpack_from('>I',state,20)[0]!=len(state)-24 or struct.unpack_from('>I',state,172)[0]!=len(state)-176):
        raise ValidationError('unexpected Vitalium component format')
    try:return strict_json(state[176:-32].decode('utf-8'))
    except (UnicodeError,ValueError) as exc:raise ValidationError('invalid Vitalium component JSON') from exc
