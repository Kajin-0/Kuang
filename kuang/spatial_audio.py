"""Sampled frequency-resolved mid/side and actual mono-sum PCM measurements.

No stereo widening DSP, perceptual scoring, LUFS or true-peak certification.
The sampled FFT uses 4096-frame Hann windows: about 11.72 Hz bins at 48 kHz.
"""

import math
import wave

from .audio import analyze_wav
from .production_audio import _decode, _fft
from .schema import ValidationError


def spatial_metrics(path):
    audio = analyze_wav(path)
    if audio['channels'] != 2 or audio['frames'] < 4096:
        raise ValidationError('spatial analysis needs stereo PCM with at least 4096 frames')
    size, count, rate = 4096, audio['frames'], audio['sample_rate']
    hann = [.5-.5*math.cos(2*math.pi*i/(size-1)) for i in range(size)]
    windows = min(96,count//size)
    bands = {name:{'mid':0.,'side':0.} for name in ('low_20_120','high_over_500')}
    mono_square = mono_peak = tail_square = tail_peak = samples = tail_count = 0
    with wave.open(str(path),'rb') as stream:
        width = stream.getsampwidth()
        while data := stream.readframes(65536):
            for left,right in _decode(data,width,2):
                mono = (left+right)*.5
                mono_square += mono*mono;mono_peak=max(mono_peak,abs(mono))
                if samples >= count-round(rate*.25):
                    tail_square += (left*left+right*right)*.5
                    tail_peak=max(tail_peak,abs(left),abs(right));tail_count+=1
                samples += 1
        for index in range(windows):
            stream.setpos(round(index*(count-size)/max(1,windows-1)))
            frames=list(_decode(stream.readframes(size),width,2))
            for component,sign in (('mid',1),('side',-1)):
                spectrum=_fft([(f[0]+sign*f[1])*.5*w for f,w in zip(frames,hann)])
                for k in range(1,size//2+1):
                    hz=k*rate/size
                    band='low_20_120' if 20<=hz<120 else 'high_over_500' if hz>500 else None
                    if band:
                        bands[band][component] += abs(spectrum[k])**2*(1 if k==size//2 else 2)
    for b in bands.values():
        total=b['mid']+b['side']
        ratio=b['side']/b['mid'] if b['mid'] else None
        b.update(side_to_mid_power_ratio=ratio,
                 side_to_mid_db=10*math.log10(ratio) if ratio else None,
                 mono_energy_retention=b['mid']/total if total else None)
    mono_rms=math.sqrt(mono_square/samples)
    tail_rms=math.sqrt(tail_square/tail_count)
    return {'method':'96 or fewer equally spaced 4096-frame Hann FFTs; M=(L+R)/2, S=(L-R)/2; energy ratios, no phase correction',
        'windows':windows,'bin_hz':rate/size,'bands':bands,
        'mono_sum':{'rms':mono_rms,'peak':mono_peak,'clipped':mono_peak>=1,
                    'rms_loss_db':20*math.log10(mono_rms/audio['rms']) if mono_rms and audio['rms'] else None},
        'last_250ms':{'rms':tail_rms,'rms_dbfs':20*math.log10(tail_rms) if tail_rms else None,'peak':tail_peak}}
