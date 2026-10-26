"""Measured time-dependent loudness and gain behavior; no taste score."""
import ctypes as C
import math
import wave
from pathlib import Path

from .loudness import ReferenceMeter,KBlocks
from .production_audio import _decode
from .schema import ValidationError


def shortterm_trace(path,*,library=None):
    """Three-second K-weighted loudness every second; silence is None.

    The optional explicit MIT libebur1281.2.6 uses its genuine short-term mode.
    The stdlib path uses the same existing validated K weighting/100ms chunks.
    Short-term values have no integrated relative gate and are not LUFS targets.
    """
    rows=[]
    with wave.open(str(path),'rb') as w:
        rate,width,channels=w.getframerate(),w.getsampwidth(),w.getnchannels()
        if rate!=48000 or channels not in (1,2) or width not in (2,3,4) or w.getcomptype()!='NONE':raise ValidationError('short-term trace requires48k mono/stereo integer PCM')
        reference=ReferenceMeter(library,rate,channels) if library else None
        blocks=None if reference else KBlocks(rate,channels);count=0
        if reference:
            reference.lib.ebur128_loudness_shortterm.argtypes=[C.c_void_p,C.POINTER(C.c_double)]
            reference.lib.ebur128_loudness_shortterm.restype=C.c_int
        try:
            while data:=w.readframes(rate//10):
                if len(data)!=(rate//10)*channels*width:break
                frames=list(_decode(data,width,channels));count+=len(frames)
                if reference:reference.add([x for f in frames for x in f])
                else:
                    for f in frames:blocks.add(f)
                if count>=3*rate and count%rate==0:
                    if reference:
                        value=C.c_double();code=reference.lib.ebur128_loudness_shortterm(reference.state,C.byref(value))
                        if code:raise ValidationError('native short-term loudness failed')
                        value=value.value if math.isfinite(value.value) else None
                    else:
                        power=blocks.shortterm[-1];value=-.691+10*math.log10(power) if power>0 else None
                    rows.append({'end_seconds':count/rate,'window_seconds':3,'lufs':value})
        finally:
            if reference:reference.close()
    finite=[x['lufs'] for x in rows if x['lufs'] is not None]
    return {'method':'3s K weighting, one-second reporting hop, no integrated gating','backend':'libebur128-1.2.6' if library else 'stdlib-KBlocks',
        'maximum_lufs':max(finite) if finite else None,'rows':rows,'certified':False}


def linked_gain_audit(bypass,processed,*,nominal_gain_db=0,minimum_input=.002):
    """Actual same-input PCM envelope ratios, not a plug-in GR-meter claim.

    Intended for isolated compressor/limiter controls with identical alignment
    and no other changed FX. Reports channel gain agreement and observed gain
    below the explicitly stated linear makeup, including the real wet blend.
    """
    if type(nominal_gain_db) not in (int,float) or not math.isfinite(nominal_gain_db):raise ValidationError('finite nominal gain required')
    if type(minimum_input) not in (int,float) or not math.isfinite(minimum_input) or not 0<minimum_input<1:raise ValidationError('positive finite active-input threshold required')
    gains=[];differences=[];count=0
    with wave.open(str(bypass),'rb') as a,wave.open(str(processed),'rb') as b:
        if a.getparams()!=b.getparams() or a.getsampwidth()!=3 or a.getnchannels()!=2:raise ValidationError('aligned stereo24bit gain controls required')
        while data:=a.readframes(8192):
            other=b.readframes(8192)
            for x,y in zip(_decode(data,3,2),_decode(other,3,2)):
                count+=1
                if count%17:continue
                valid=[v/u for u,v in zip(x,y) if abs(u)>=minimum_input]
                if valid and all(g>0 for g in valid):gains.append(sum(valid)/len(valid))
                if len(valid)==2:differences.append(abs(valid[0]-valid[1]))
    if not gains:raise ValidationError('gain audit has no active input')
    gains.sort();nominal=10**(nominal_gain_db/20)
    def percentile(q):return gains[min(len(gains)-1,round((len(gains)-1)*q))]
    return {'active_sample_frames':len(gains),'nominal_unreduced_gain_db':nominal_gain_db,
        'maximum_observed_attenuation_below_nominal_db':20*math.log10(nominal/gains[0]),
        'p01_attenuation_below_nominal_db':20*math.log10(nominal/percentile(.01)),
        'median_attenuation_below_nominal_db':20*math.log10(nominal/percentile(.5)),
        'gain_p01':percentile(.01),'gain_median':percentile(.5),'gain_p99':percentile(.99),
        'maximum_channel_gain_disagreement':max(differences,default=0),
        'scope':'Observed aligned PCM gain through the actual declared blend; not external detector routing or an internal gain-reduction meter'}


def envelope_gain_audit(bypass,processed,*,nominal_gain_db=0,window_ms=50):
    """Windowed RMS gain for a processor that can alter phase/timing.

    No sample division or invented internal GR meter. Native latency remains in
    both delivered files; finite-window envelope differences include that DSP
    behavior. The exact output peak is measured independently by the TP meter.
    """
    if type(nominal_gain_db) not in (int,float) or not math.isfinite(nominal_gain_db):raise ValidationError('finite nominal gain required')
    if type(window_ms) not in (int,float) or not math.isfinite(window_ms) or not 1<=window_ms<=250:raise ValidationError('bounded envelope window required')
    values=[];ein=eout=0
    with wave.open(str(bypass),'rb') as a,wave.open(str(processed),'rb') as b:
        if a.getparams()!=b.getparams() or a.getsampwidth()!=3 or a.getnchannels()!=2:raise ValidationError('aligned stereo24bit envelopes required')
        size=round(a.getframerate()*window_ms/1000)
        while raw:=a.readframes(size):
            x=list(_decode(raw,3,2));y=list(_decode(b.readframes(size),3,2));pi=sum(v*v for f in x for v in f);po=sum(v*v for f in y for v in f);ein+=pi;eout+=po
            if pi/(2*len(x))>.002**2 and po>0:values.append(nominal_gain_db-10*math.log10(po/pi))
    if not values or not ein or not eout:raise ValidationError('no active envelope input')
    values.sort()
    return {'active_windows':len(values),'window_ms':window_ms,'nominal_gain_db':nominal_gain_db,
        'whole_file_attenuation_below_nominal_db':nominal_gain_db-10*math.log10(eout/ein),
        'p50_window_attenuation_below_nominal_db':values[len(values)//2],
        'p99_window_attenuation_below_nominal_db':values[round((len(values)-1)*.99)],
        'scope':'Observed50ms energy envelopes, not instantaneous linked gain or an internal GR meter; phase/latency can affect individual windows'}
