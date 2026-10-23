"""Phase 10 diagnostics, separate from the native musical signal path."""

import math
import os
import tempfile
import wave
from pathlib import Path

from .loudness import Biquad,db
from .production_audio import _decode,_fft
from .schema import ValidationError,strict_json


def reference_guide(path):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>65536:raise ValidationError('missing/oversized numeric reference guide')
    data=strict_json(path.read_text())
    if type(data) is not dict or set(data)!={'purpose','suno','kuang_phase8','comparison'}:
        raise ValidationError('unexpected reference-guide fields')
    keys={'integrated_lufs_approx','stereo_correlation_approx','high_band_side_fraction_above_500Hz_approx'}
    for name in ('suno','kuang_phase8'):
        values=data[name]
        if type(values) is not dict or set(values)!=keys:raise ValidationError('unexpected reference metrics')
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in values.values()):raise ValidationError('invalid reference metric')
        if not -1<=values['stereo_correlation_approx']<=1 or not 0<=values['high_band_side_fraction_above_500Hz_approx']<=1:
            raise ValidationError('invalid reference stereo range')
    if any(type(data[k]) is not str or not 1<=len(data[k])<=2048 for k in ('purpose','comparison')):
        raise ValidationError('invalid reference description')
    return {'provided_numeric_guide':data,'source_audio_used':False,'source_audio_redistributed':False,
            'same_arrangement':False,'loudness_target':False,'metric_caveat':'Approximate supplied guide; different material, duration, vocals and possibly analysis windows. Side fraction is S/(M+S), not S/M.'}


def speaker_approx(path,destination=None,cutoff=120):
    """Two Butterworth 2-pole highpasses, 24 dB/oct speaker approximation.

    Audio export is labelled diagnostic. Never used as hidden production DSP.
    """
    if type(cutoff) not in (int,float) or not math.isfinite(cutoff) or not 100<=cutoff<=150:
        raise ValidationError('speaker approximation cutoff must be 100..150Hz')
    dest=Path(destination) if destination is not None else None
    if dest is not None and (dest.exists() or dest.is_symlink()):raise ValidationError('new speaker diagnostic output only')
    with wave.open(str(path),'rb') as source:
        if (source.getnchannels(),source.getsampwidth(),source.getframerate(),source.getcomptype())!=(2,3,48000,'NONE'):
            raise ValidationError('speaker approximation needs stereo 48k/24bit PCM')
        omega=2*math.pi*cutoff/48000;co=math.cos(omega);alpha=math.sin(omega)/(2*math.sqrt(.5));a0=1+alpha
        coefficients=((1+co)/(2*a0),-(1+co)/a0,(1+co)/(2*a0),-2*co/a0,(1-alpha)/a0)
        filters=[(Biquad(coefficients),Biquad(coefficients)) for _ in range(2)]
        squared=peak=0.;count=0
        # Own temporary output, followed by exclusive publication if requested.
        parent=dest.parent if dest is not None else Path(path).parent
        with tempfile.TemporaryDirectory(prefix='.kuang-speaker-',dir=parent) as d:
            staged=Path(d)/'audio.wav';output=wave.open(str(staged),'wb') if dest is not None else None
            try:
                if output:output.setparams(source.getparams())
                while data:=source.readframes(32768):
                    out=bytearray()
                    for frame in _decode(data,3,2):
                        for value,(a,b) in zip(frame,filters):
                            value=b.process(a.process(value));squared+=value*value;peak=max(peak,abs(value));count+=1
                            if output:
                                integer=round(value*2**23)
                                if not -2**23<integer<2**23:raise ValidationError('speaker diagnostic would clip')
                                out+=integer.to_bytes(3,'little',signed=True)
                    if output:output.writeframes(out)
            finally:
                if output:output.close()
            if dest is not None:os.link(staged,dest)
    if not count:raise ValidationError('empty speaker diagnostic')
    rms=math.sqrt(squared/count)
    return {'method':'two cascaded 2-pole Butterworth HP, 24dB/oct; diagnostic approximation, not an actual speaker',
            'cutoff_hz':cutoff,'rms':rms,'rms_dbfs':db(rms),'peak':peak,'peak_dbfs':db(peak),'production_processing':False}


def sample_steps(path):
    with wave.open(str(path),'rb') as w:
        if w.getnchannels()!=2 or w.getsampwidth()!=3:raise ValidationError('step audit requires stereo 24bit PCM')
        last=[0.,0.];maximum=0.;frames=0
        while data:=w.readframes(32768):
            for frame in _decode(data,3,2):
                maximum=max(maximum,abs(frame[0]-last[0]),abs(frame[1]-last[1]))
                last[:]=frame;frames+=1
    return {'maximum_adjacent_sample_step':maximum,'frames':frames,
            'interpretation':'discontinuity diagnostic, not perceptual crackle-free certification'}


def pulse_windows(on,off,bpm=126,beats=32):
    """Actual mono 20HP/120LP energy change around every late-offbeat pulse."""
    from contextlib import ExitStack
    with ExitStack() as stack:
        streams=[stack.enter_context(wave.open(str(p),'rb')) for p in (on,off)]
        formats=[(w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()) for w in streams]
        if formats[0]!=formats[1] or formats[0][:3]!=(2,3,48000):raise ValidationError('aligned stereo 48k24 pulse controls required')
        rate=48000;hp=math.exp(-2*math.pi*20/rate);lp=1-math.exp(-2*math.pi*120/rate)
        ranges=[(round((beat*60/bpm+592/960*60/bpm-.01)*rate),
                 round((beat*60/bpm+592/960*60/bpm+.15)*rate)) for beat in range(beats)]
        if ranges[-1][1]>formats[0][3]:raise ValidationError('pulse windows exceed PCM')
        energies=[[0.,0.] for _ in ranges];previous=[0.,0.];high=[0.,0.];low=[0.,0.];frame=0;index=0
        while data:=streams[0].readframes(32768):
            other=streams[1].readframes(32768)
            if len(data)!=len(other):raise ValidationError('truncated pulse control')
            for a,b in zip(_decode(data,3,2),_decode(other,3,2)):
                while index<len(ranges) and frame>=ranges[index][1]:index+=1
                for ch,values in enumerate((a,b)):
                    x=sum(values)/2;high[ch]=hp*(high[ch]+x-previous[ch]);previous[ch]=x
                    low[ch]+=lp*(high[ch]-low[ch])
                    if index<len(ranges) and ranges[index][0]<=frame<ranges[index][1]:energies[index][ch]+=low[ch]**2
                frame+=1
    changes=[10*math.log10(a/b) if a and b else None for a,b in energies]
    finite=[v for v in changes if v is not None]
    if not finite:raise ValidationError('no active pulse windows')
    return {'method':'mono one-pole 20Hz HP /120Hz LP, same-input on/off; pulse onset -10ms to +150ms',
        'on_off_db_per_beat':changes,'minimum_db':min(finite),'maximum_db':max(finite),
        'median_db':sorted(finite)[len(finite)//2],
        'absolute_windows':[{'beat':i,'on_rms':math.sqrt(a/(ranges[i][1]-ranges[i][0])),
            'off_rms':math.sqrt(b/(ranges[i][1]-ranges[i][0]))} for i,(a,b) in enumerate(energies)],
        'rest_caveat':'Large positive ratios over near-silent bass rests are not mix-level boosts; inspect absolute RMS and whole-band limits.'}


def sub_power(path,last):
    """Resolve 20–60 Hz directly, rather than splitting the 40–80 bin band."""
    size=16384;windows=16;hann=[.5-.5*math.cos(2*math.pi*i/(size-1)) for i in range(size)]
    norm=2*size*sum(v*v for v in hann);powers=[]
    with wave.open(str(path),'rb') as w:
        rate=w.getframerate();end=round(last*rate)
        if w.getnchannels()!=2 or w.getsampwidth()!=3 or not size<=end<=w.getnframes():raise ValidationError('invalid sub-energy window')
        for i in range(windows):
            at=round(i*(end-size)/(windows-1));w.setpos(at)
            frames=list(_decode(w.readframes(size),3,2));energy=0.
            for ch in (0,1):
                spectrum=_fft([f[ch]*h for f,h in zip(frames,hann)])
                energy+=sum(2*abs(spectrum[k])**2/norm for k in range(1,size//2) if 20<=k*rate/size<60)
            powers.append({'start_frame':at,'mean_square':energy})
    return {'band_hz':[20,60],'bin_hz':rate/size,'mean_square':sum(v['mean_square'] for v in powers)/windows,'windows':powers,
            'method':'stereo 16384-frame Hann mean squares, 16 aligned windows; absolute sampled power'}
