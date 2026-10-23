"""Original deterministic synthetic vectors; no redistributed EBU audio."""
import math
import wave

RECIPES={
 'silence':{'seconds':1,'channels':2,'segments':[(1,0,1000,0)]},
 'stereo-1k':{'seconds':1.2,'channels':2,'segments':[(1.2,10**(-23/20),1000,0)]},
 'mono-1k':{'seconds':1.2,'channels':1,'segments':[(1.2,10**(-23/20),1000,0)]},
 'quiet-absolute-gate':{'seconds':1,'channels':2,'segments':[(1,10**(-80/20),1000,0)]},
 'relative-gate':{'seconds':4,'channels':2,'segments':[(1,0,1000,0),(1.5,.1,1000,0),(1.5,.001,1000,0)]},
 'two-level':{'seconds':3.2,'channels':2,'segments':[(1.6,.1,1000,0),(1.6,.05,1000,0)]},
 'tp15':{'seconds':.2,'channels':2,'segments':[(.2,.5,12000,0)],'taper':True},
 'tp16-intersample':{'seconds':.2,'channels':2,'segments':[(.2,.5,12000,math.pi/4)],'taper':True},
 'tp17':{'seconds':.2,'channels':2,'segments':[(.2,.5,8000,math.pi/3)],'taper':True},
 'tp18':{'seconds':.2,'channels':2,'segments':[(.2,.5,6000,3*math.pi/8)],'taper':True},
 'tp19-overfull':{'seconds':.2,'channels':2,'segments':[(.2,1.41,12000,math.pi/4)],'taper':True},
 'short-block':{'seconds':.399,'channels':1,'segments':[(.399,.1,1000,0)]},
}

def write_vector(path,name):
    recipe=RECIPES[name];rate=48000;data=bytearray();offset=0
    for seconds,amplitude,frequency,phase in recipe['segments']:
        frames=round(seconds*rate)
        for i in range(frames):
            taper=min(1,i/(rate*.01),(frames-1-i)/(rate*.01)) if recipe.get('taper') else 1
            value=round(amplitude*taper*math.sin(2*math.pi*frequency*(offset+i)/rate+phase)*(2**23-1))
            if not -(2**23)<=value<2**23:raise ValueError('fixture clips')
            data+=value.to_bytes(3,'little',signed=True)*recipe['channels']
        offset+=frames
    with wave.open(str(path),'wb') as w:
        w.setparams((recipe['channels'],3,rate,0,'NONE','not compressed'));w.writeframes(data)
