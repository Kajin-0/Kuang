"""Controlled PCM tuning diagnostics, not a polyphonic transcription/quality score.

Two independent estimators: full-band Hann FFT peaks with sub-bin log fitting,
and normalized time-domain autocorrelation around the expected period. Windows
must lie inside a single held note. Expected-note neighborhoods do not replace
reporting the strongest full-band peak or reveal a chord's actual roots alone.
"""
import math
import wave
from .production_audio import _decode,_fft
from .schema import ValidationError


def hz(note):
    if type(note) is not int or not 0<=note<=127:raise ValidationError('MIDI integer pitch required')
    return 440*2**((note-69)/12)


def cents(frequency,expected):return 1200*math.log2(frequency/expected)


def spectrum(path,first,last):
    with wave.open(str(path),'rb') as w:
        rate,width,channels=w.getframerate(),w.getsampwidth(),w.getnchannels()
        if channels not in (1,2) or width not in (2,3,4) or w.getcomptype()!='NONE':raise ValidationError('integer mono/stereo PCM required')
        if not 0<=first<last<=w.getnframes()/rate or last-first<.08 or last-first>2:raise ValidationError('bounded .08..2s analysis window required')
        a,b=round(first*rate),round(last*rate);w.setpos(a);frames=list(_decode(w.readframes(b-a),width,channels))
    if len(frames)!=b-a:raise ValidationError('truncated pitch PCM')
    size=1
    while size<2*len(frames):size*=2
    window=[.5-.5*math.cos(2*math.pi*i/(len(frames)-1)) for i in range(len(frames))]
    power=[0.]*(size//2+1)
    for ch in range(channels):
        mean=sum(x[ch] for x in frames)/len(frames)
        bins=_fft([(f[ch]-mean)*v for f,v in zip(frames,window)]+[0.]*(size-len(frames)))
        for i in range(len(power)):power[i]+=abs(bins[i])**2
    peaks=[]
    for k in range(max(1,math.ceil(20*size/rate)),min(size//2-1,math.floor(8000*size/rate))):
        if power[k]>=power[k-1] and power[k]>power[k+1]:
            a,b,c=[math.log(max(1e-40,power[j])) for j in (k-1,k,k+1)];den=a-2*b+c
            delta=max(-.5,min(.5,.5*(a-c)/den)) if den else 0
            peaks.append({'hz':(k+delta)*rate/size,'power':power[k]})
    peaks.sort(key=lambda x:x['power'],reverse=True)
    if not peaks or peaks[0]['power']<1e-12:raise ValidationError('no measurable pitched signal')
    return rate,frames,peaks,rate/size


def note_pitch(path,note,first,last):
    target=hz(note);rate,frames,peaks,bin_hz=spectrum(path,first,last)
    neighborhood=[p for p in peaks if abs(cents(p['hz'],target))<=450]
    if not neighborhood:raise ValidationError('no fundamental candidate within 450cents; inspect full-band peaks')
    peak=max(neighborhood,key=lambda p:p['power'])
    # Use the stronger real channel, never a potentially cancelling mono fold.
    ch=max(range(len(frames[0])),key=lambda ch:sum(f[ch]**2 for f in frames))
    x=[f[ch] for f in frames];mean=sum(x)/len(x);x=[v-mean for v in x]
    lo=max(2,math.floor(rate/(target*2**(450/1200))));hi=min(len(x)//3,math.ceil(rate/(target/2**(450/1200))))
    # Common segment length removes lag-dependent overlap/energy bias.
    n=min(12000,len(x)-hi);base=x[:n];base_power=sum(v*v for v in base);scores={}
    for lag in range(lo-1,hi+2):
        other=x[lag:lag+n];energy=sum(v*v for v in other)
        scores[lag]=sum(a*b for a,b in zip(base,other))/math.sqrt(base_power*energy) if energy and base_power else 0
    lag=max(range(lo,hi+1),key=lambda j:scores[j]);a,b,c=[scores[j] for j in (lag-1,lag,lag+1)];den=a-2*b+c
    shift=max(-.5,min(.5,.5*(a-c)/den)) if den else 0;period_hz=rate/(lag+shift)
    return {'midi':note,'expected_hz':target,'window_seconds':[first,last],'fft_bin_hz':bin_hz,
        'fft_fundamental_hz':peak['hz'],'fft_cents':cents(peak['hz'],target),
        'period_hz':period_hz,'period_cents':cents(period_hz,target),'period_correlation':b,
        'strongest_full_band_peak_hz':peaks[0]['hz'],'top_peaks':peaks[:12]}
