"""Absolute/fractional low-end band diagnostics, no target EQ curve."""

import math
import wave

from .production_audio import _decode, _fft
from .schema import ValidationError

BANDS=(('20_40',20,40),('40_80',40,80),('80_120',80,120),
       ('120_250',120,250),('250_500',250,500),('500_2000',500,2000),
       ('2000_8000',2000,8000),('8000_nyquist',8000,float('inf')))


def band_metrics(path,*,first=0,last=None,windows=16):
    if type(windows) is not int or not 1<=windows<=64:raise ValidationError('invalid spectral window count')
    with wave.open(str(path),'rb') as w:
        rate,width,channels,count=w.getframerate(),w.getsampwidth(),w.getnchannels(),w.getnframes()
        if channels!=2 or width not in (2,3,4) or w.getcomptype()!='NONE':raise ValidationError('band metrics need stereo PCM')
        last=count/rate if last is None else last
        if not all(type(v) in (int,float) and math.isfinite(v) for v in (first,last)) or not 0<=first<last<=count/rate:
            raise ValidationError('invalid spectral time window')
        a,b=round(first*rate),round(last*rate);size=16384
        if b-a<size:raise ValidationError('low-end spectrum requires 16384 frames')
        windows=min(windows,(b-a)//size)
        hann=[.5-.5*math.cos(2*math.pi*i/(size-1)) for i in range(size)]
        norm=2*size*sum(x*x for x in hann);all_windows=[];midside=[0.,0.,0.,0.]
        for i in range(windows):
            frame=a+round(i*(b-a-size)/max(1,windows-1));w.setpos(frame)
            frames=list(_decode(w.readframes(size),width,2))
            fft=[_fft([f[ch]*h for f,h in zip(frames,hann)]) for ch in (0,1)]
            power=[(abs(l)**2+abs(r)**2)*(1 if k==size//2 else 2)/norm for k,(l,r) in enumerate(zip(*fft)) if k<=size//2]
            bands={name:sum(v for k,v in enumerate(power) if lo<=k*rate/size<hi) for name,lo,hi in BANDS}
            bands['harmonics_100_400']=sum(v for k,v in enumerate(power) if 100<=k*rate/size<400)
            for k in range(1,size//2):
                freq=k*rate/size
                if 20<=freq<120 or freq>=500:
                    m=(fft[0][k]+fft[1][k])/2;s=(fft[0][k]-fft[1][k])/2
                    index=0 if freq<120 else 2
                    midside[index]+=abs(m)**2;midside[index+1]+=abs(s)**2
            all_windows.append({'start_frame':frame,'band_mean_square':bands})
    average={k:sum(v['band_mean_square'][k] for v in all_windows)/windows for k in all_windows[0]['band_mean_square']}
    total=sum(average[name] for name,_,_ in BANDS)
    return {'method':'16384-frame Hann, stereo absolute mean squares, window-power normalized; no target EQ curve',
        'sample_rate':rate,'bin_hz':rate/size,'first_seconds':first,'last_seconds':last,
        'band_mean_square':average,'band_power_fraction':{k:v/total if total else 0 for k,v in average.items()},
        'windows':all_windows,'mono_energy_retention':{
            label:midside[i]/(midside[i]+midside[i+1]) if midside[i]+midside[i+1] else None
            for label,i in (('20_120',0),('over_500',2))}}
