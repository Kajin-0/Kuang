"""Per-section sampled spectral diagnostics, without changing source audio."""

import math
import wave

from .audio import analyze_wav
from .production_audio import BANDS, _decode, _fft
from .schema import ValidationError


def section_spectra(path,regions):
    audio=analyze_wav(path)
    if audio['channels']!=2:raise ValidationError('section spectrum needs stereo PCM')
    result={};size=2048;rate=audio['sample_rate']
    hann=[.5-.5*math.cos(2*math.pi*i/(size-1)) for i in range(size)]
    with wave.open(str(path),'rb') as stream:
        width=stream.getsampwidth()
        for label,start,end in regions:
            if (label in result or not isinstance(label,str) or not label or
                    not 0<=start<end<=audio['duration_seconds']):
                raise ValidationError('invalid section spectrum region')
            first,last=round(start*rate),round(end*rate)
            windows=min(32,(last-first)//size)
            if not windows:raise ValidationError('section spectrum region too short')
            powers=[0.]*(size//2+1)
            for index in range(windows):
                stream.setpos(first+round(index*(last-first-size)/max(1,windows-1)))
                frames=list(_decode(stream.readframes(size),width,2))
                for channel in (0,1):
                    fft=_fft([f[channel]*w for f,w in zip(frames,hann)])
                    for k in range(1,len(powers)):
                        powers[k]+=abs(fft[k])**2*(1 if k==size//2 else 2)
            bands={name:sum(v for k,v in enumerate(powers) if lo<=k*rate/size<hi)
                   for name,lo,hi in BANDS}
            total=sum(bands.values())
            result[label]={'start_frame':first,'end_frame':last,'windows':windows,
                          'band_power_fraction':{k:v/total if total else 0 for k,v in bands.items()}}
    return {'method':'32 or fewer equally spaced 2048-frame Hann FFTs per region; sum stereo powers, exclude <20 Hz',
            'bin_hz':rate/size,'sections':result}
