"""Localized, absolute PCM diagnostics for the opt-in gesture experiment.

Band powers are sampled Hann-window mean squares (not perceived loudness).
Counterfactuals must be aligned renders of the same MIDI and signal chain.
"""

import math
import wave

from .audio import analyze_wav
from .production_audio import BANDS, _decode, _fft
from .schema import ValidationError


def window_metrics(path, regions):
    audio=analyze_wav(path);rate=audio['sample_rate'];result={};size=4096
    if audio['channels']!=2:raise ValidationError('gesture diagnostics require stereo PCM')
    hann=[.5-.5*math.cos(2*math.pi*i/(size-1)) for i in range(size)]
    norm=sum(x*x for x in hann)*size
    with wave.open(str(path),'rb') as w:
        for label,start,end in regions:
            if label in result or not isinstance(label,str) or not label or not all(
                    type(v) in (int,float) and math.isfinite(v) for v in (start,end)) or not 0<=start<end<=audio['duration_seconds']:
                raise ValidationError('invalid localized audio region')
            first,last=round(start*rate),round(end*rate)
            if last-first<size:raise ValidationError('localized spectrum needs at least 4096 frames')
            w.setpos(first);remaining=last-first;squares=peak=count=0
            while remaining:
                data=w.readframes(min(65536,remaining));remaining-=len(data)//(2*w.getsampwidth())
                if not data:raise ValidationError('truncated gesture PCM')
                for f in _decode(data,w.getsampwidth(),2):
                    squares+=sum(x*x for x in f);peak=max(peak,*map(abs,f));count+=2
            windows=min(32,(last-first)//size);power=[0.]*(size//2+1)
            for i in range(windows):
                w.setpos(first+round(i*(last-first-size)/max(1,windows-1)))
                frames=list(_decode(w.readframes(size),w.getsampwidth(),2))
                for ch in (0,1):
                    spectrum=_fft([f[ch]*h for f,h in zip(frames,hann)])
                    for k in range(1,len(power)):
                        power[k]+=abs(spectrum[k])**2*(1 if k==size//2 else 2)/(2*windows*norm)
            bands={name:sum(x for k,x in enumerate(power) if lo<=k*rate/size<hi) for name,lo,hi in BANDS}
            rms=math.sqrt(squares/count)
            result[label]={'rms':rms,'rms_dbfs':20*math.log10(rms) if rms else None,
                'peak':peak,'band_mean_square':bands,'sampled_windows':windows}
    return {'method':'absolute mean squares: up to 32 equally spaced stereo 4096-frame Hann FFTs, window-power normalized; RMS uses every frame',
            'bin_hz':rate/size,'regions':result}


def phase_gain(on, off, *, bpm=126, first_beat=0, beats=16):
    """Same-input energy ratios at beat phases, excluding silence in control."""
    a,b=analyze_wav(on),analyze_wav(off)
    if any(a[k]!=b[k] for k in ('frames','sample_rate','channels','bits_per_sample')):
        raise ValidationError('pump controls must be aligned')
    result={};rate=a['sample_rate'];beat=60/bpm
    with wave.open(str(on),'rb') as x,wave.open(str(off),'rb') as y:
        for name,lo,hi in (('duck',.015,.090),('recover',.14,.24),('open',.35,.44)):
            wet=dry=0
            for index in range(first_beat,first_beat+beats):
                start=round((index*beat+lo)*rate);end=round((index*beat+hi)*rate)
                if end>a['frames']:raise ValidationError('pump region exceeds PCM')
                x.setpos(start);y.setpos(start)
                wet+=sum(v*v for f in _decode(x.readframes(end-start),x.getsampwidth(),2) for v in f)
                dry+=sum(v*v for f in _decode(y.readframes(end-start),y.getsampwidth(),2) for v in f)
            result[name]={'on_off_energy_ratio':wet/dry if dry else None,
                          'on_off_db':10*math.log10(wet/dry) if wet and dry else None}
    return result


def echo_trails(on, off, note_end, delay_ms, repeats=3):
    """Absolute energy in short windows after the isolated authored note ends.

    A native dry synth release can occupy echo 1. Later windows are reported
    independently; no correlation or timing inference from parameter values.
    """
    delay=delay_ms/1000
    regions=[('echo-'+str(i),note_end+i*delay-.04,note_end+i*delay+.10) for i in range(1,repeats+1)]
    a=window_metrics(on,regions)['regions'];b=window_metrics(off,regions)['regions']
    return {k:{'seconds':regions[i][1:],'wet_rms':a[k]['rms'],'dry_rms':b[k]['rms'],
               'wet_minus_dry_db':20*math.log10(a[k]['rms']/b[k]['rms']) if b[k]['rms'] and a[k]['rms'] else None}
            for i,k in enumerate(a)}


def echo_peak_timing(path, note_start, delay_ms):
    """Locate actual 20 ms RMS envelope maxima, with a 2 ms search hop.

    Search windows are centred around each expected echo. Report the observed
    spacing separately, so a delay time value alone cannot satisfy the gate.
    The input is an isolated authored note, no reverb/modulation.
    """
    with wave.open(str(path),'rb') as w:
        rate=w.getframerate();width=w.getsampwidth()
        peaks=[]
        for repeat in range(1,4):
            expected=note_start+repeat*delay_ms/1000
            candidates=[]
            for frame in range(round((expected-.04)*rate),round((expected+.20)*rate),round(.002*rate)):
                w.setpos(frame)
                samples=[x for f in _decode(w.readframes(round(.020*rate)),width,2) for x in f]
                candidates.append((math.sqrt(sum(x*x for x in samples)/len(samples)),frame/rate))
            rms,at=max(candidates)
            peaks.append({'repeat':repeat,'peak_window_start_seconds':at,'window_rms':rms})
    spacings=[(b['peak_window_start_seconds']-a['peak_window_start_seconds'])*1000 for a,b in zip(peaks,peaks[1:])]
    return {'rms_window_ms':20,'search_hop_ms':2,'observed_peaks':peaks,
            'observed_spacing_ms':spacings,'configured_delay_ms':delay_ms,
            'max_spacing_error_ms':max(abs(x-delay_ms) for x in spacings)}


def gain_reduction_envelope(active, bypass):
    """20 ms same-input gain ratios; exclude windows below -80 dBFS input.

    Measures a local compressor with makeup zero in both diagnostic projects.
    Gain changes over active windows distinguish compression from static trim.
    """
    a,b=analyze_wav(active),analyze_wav(bypass)
    if any(a[k]!=b[k] for k in ('frames','sample_rate','channels','bits_per_sample')):
        raise ValidationError('compressor controls must be aligned')
    values=[];rate=a['sample_rate'];size=round(rate*.02)
    with wave.open(str(active),'rb') as x,wave.open(str(bypass),'rb') as y:
        while da:=x.readframes(size):
            db=y.readframes(size)
            if len(da)!=len(db):raise ValidationError('truncated compressor control')
            wet=sum(v*v for f in _decode(da,x.getsampwidth(),2) for v in f)
            dry=sum(v*v for f in _decode(db,y.getsampwidth(),2) for v in f)
            count=len(db)//y.getsampwidth()
            if dry/count>1e-8 and wet:values.append(10*math.log10(wet/dry))
    if not values:raise ValidationError('no active compressor input windows')
    values.sort()
    return {'window_ms':20,'active_windows':len(values),'minimum_gain_db':values[0],
            'median_gain_db':values[len(values)//2],'maximum_gain_db':values[-1],
            'gain_variation_db':values[-1]-values[0]}
