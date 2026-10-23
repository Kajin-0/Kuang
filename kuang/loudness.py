"""Mono/stereo BS.1770-style file measurements, stdlib only, not certification.

K weighting, complete 400 ms blocks / 100 ms hop, -70 LUFS then -10 LU gate.
True peak uses a Hann-windowed sinc reconstruction FIR, 4x or 8x, including
zero-padded filter drain. Optional user-built MIT libebur128 1.2.6 is an
explicit fast reference backend, never downloaded or loaded automatically.
See docs/PHASE9.md and tests/fixtures/loudness-golden.json for validation.
"""

# Interpolator design / generalized filter design attribution:
# Copyright (c) 2011 Jan Kokemüller, libebur128 (MIT).
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import ctypes as C
import math
import wave
from array import array
from collections import deque
from pathlib import Path

from .production_audio import _decode
from .schema import ValidationError


def db(value):
    return 20*math.log10(value) if value>0 else None


def k_coefficients(rate):
    if type(rate) is not int or not 8000<=rate<=192000:
        raise ValidationError('K weighting supports integer sample rates 8000..192000')
    # ITU's 48k coefficients generalized by the published bilinear design.
    k=math.tan(math.pi*1681.974450955533/rate)
    vh=10**(3.999843853973347/20);vb=vh**.4996667741545416;q=.7071752369554196
    a=1+k/q+k*k
    shelf=((vh+vb*k/q+k*k)/a,2*(k*k-vh)/a,(vh-vb*k/q+k*k)/a,
           2*(k*k-1)/a,(1-k/q+k*k)/a)
    k=math.tan(math.pi*38.13547087602444/rate);q=.5003270373238773;a=1+k/q+k*k
    # RLB numerator is deliberately NOT divided by a. This is ITU's weighting,
    # not a generic unity-normalized highpass.
    high=(1.,-2.,1.,2*(k*k-1)/a,(1-k/q+k*k)/a)
    return shelf,high


class Biquad:
    def __init__(self,coefficients):
        self.b0,self.b1,self.b2,self.a1,self.a2=coefficients
        self.x1=self.x2=self.y1=self.y2=0.

    def process(self,x):
        y=self.b0*x+self.b1*self.x1+self.b2*self.x2-self.a1*self.y1-self.a2*self.y2
        self.x2,self.x1,self.y2,self.y1=self.x1,x,self.y1,y
        return y


class KBlocks:
    def __init__(self,rate,channels):
        if rate%10:raise ValidationError('meter requires a sample rate divisible by 10')
        shelf,high=k_coefficients(rate)
        self.filters=[(Biquad(shelf),Biquad(high)) for _ in range(channels)]
        self.hop=rate//10;self.count=0;self.energy=0.;self.chunks=deque(maxlen=30)
        self.blocks=[];self.shortterm=[]

    def add(self,frame):
        for x,(s,h) in zip(frame,self.filters):
            y=h.process(s.process(x));self.energy+=y*y
        self.count+=1
        if self.count==self.hop:
            self.chunks.append(self.energy/self.hop);self.count=0;self.energy=0.
            if len(self.chunks)>=4:self.blocks.append(sum(list(self.chunks)[-4:])/4)
            if len(self.chunks)==30:self.shortterm.append(sum(self.chunks)/30)

    def result(self):
        absolute=10**((-70+.691)/10)
        passed=[p for p in self.blocks if p>absolute]
        threshold=sum(passed)/len(passed)*.1 if passed else None
        gated=[p for p in passed if p>threshold] if passed else []
        loud=lambda power: -.691+10*math.log10(power) if power>0 else None
        return {'integrated_lufs':loud(sum(gated)/len(gated)) if gated else None,
                'absolute_gate_lufs':-70,'relative_gate_lufs':loud(threshold) if threshold else None,
                'complete_blocks':len(self.blocks),'absolute_pass_blocks':len(passed),
                'relative_pass_blocks':len(gated),
                'shortterm_max_lufs':loud(max(self.shortterm)) if self.shortterm else None}


class TruePeak:
    """Polyphase anti-imaging FIR: 12 input-sample support, factor*12+1 taps.

    Mathematical construction matches the MIT libebur128 1.2.6 interpolator;
    independently coded delay evaluation, doubles and explicit filter drain.
    It is finite reconstruction, with documented high-frequency uncertainty.
    """
    def __init__(self,channels,factor=4):
        if type(factor) is not int or factor not in (4,8):raise ValidationError('true peak oversampling must be 4 or 8')
        taps=12*factor+1;self.phases=[];self.history=[deque([0.]*13,maxlen=13) for _ in range(channels)]
        for phase in range(factor):
            coefficients=[]
            for j in range(phase,taps,factor):
                x=(j-(taps-1)/2)/factor
                c=(math.sin(math.pi*x)/(math.pi*x) if x else 1)*(.5-.5*math.cos(2*math.pi*j/(taps-1)))
                if abs(c)>1e-6:coefficients.append((j//factor,c))
            self.phases.append(coefficients)
        self.peak=0.;self.channels=channels

    def add(self,frame):
        for h,x in zip(self.history,frame):
            h.appendleft(x)
            self.peak=max(self.peak,abs(x))
            for phase in self.phases:
                self.peak=max(self.peak,abs(sum(h[i]*c for i,c in phase)))

    def finish(self):
        for _ in range(13):self.add([0.]*self.channels)
        return self.peak


class ReferenceMeter:
    def __init__(self,path,rate,channels):
        try:self.lib=C.CDLL(str(Path(path).resolve()))
        except OSError as exc:raise ValidationError('explicit reference library could not load') from exc
        l=self.lib;l.ebur128_init.argtypes=[C.c_uint,C.c_ulong,C.c_int];l.ebur128_init.restype=C.c_void_p
        l.ebur128_destroy.argtypes=[C.POINTER(C.c_void_p)]
        l.ebur128_add_frames_double.argtypes=[C.c_void_p,C.POINTER(C.c_double),C.c_size_t]
        l.ebur128_loudness_global.argtypes=[C.c_void_p,C.POINTER(C.c_double)]
        l.ebur128_true_peak.argtypes=[C.c_void_p,C.c_uint,C.POINTER(C.c_double)]
        l.ebur128_get_version.argtypes=[C.POINTER(C.c_int)]*3
        version=[C.c_int() for _ in range(3)];l.ebur128_get_version(*(C.byref(v) for v in version))
        if tuple(v.value for v in version)!=(1,2,6):raise ValidationError('reference backend must be libebur128 1.2.6')
        self.state=C.c_void_p(l.ebur128_init(channels,rate,1|2|4|16|32));self.channels=channels
        if not self.state:raise ValidationError('reference meter initialization failed')

    def add(self,values):
        data=array('d',values)
        if self.lib.ebur128_add_frames_double(self.state,(C.c_double*len(data)).from_buffer(data),len(data)//self.channels):
            raise ValidationError('reference meter processing failed')

    def result(self):
        value=C.c_double()
        if self.lib.ebur128_loudness_global(self.state,C.byref(value)):raise ValidationError('reference loudness failed')
        loud=value.value if math.isfinite(value.value) else None
        # Drain after integrated measurement, so padding cannot add a block.
        self.add([0.]*(13*self.channels));peaks=[]
        for ch in range(self.channels):
            if self.lib.ebur128_true_peak(self.state,ch,C.byref(value)):raise ValidationError('reference true peak failed')
            peaks.append(value.value)
        return {'integrated_lufs':loud,'true_peak':max(peaks),'backend':'libebur128-1.2.6',
                'oversample':4,'fir_taps':49}

    def close(self):
        if self.state:self.lib.ebur128_destroy(C.byref(self.state))


def measure(path,*,oversample=4,library=None):
    if type(oversample) is not int or oversample not in (4,8):raise ValidationError('true peak oversampling must be 4 or 8')
    with wave.open(str(path),'rb') as w:
        channels,width,rate,frames=w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()
        if channels not in (1,2) or width not in (2,3,4) or not frames or w.getcomptype()!='NONE':
            raise ValidationError('loudness requires nonempty mono/stereo integer PCM')
        k_coefficients(rate)
        # libebur128 selects other factors above 48k; restrict the optional
        # reference backend to the exact verified 48k/4x contract.
        if library and (rate!=48000 or oversample!=4):raise ValidationError('reference backend is pinned to 48k / 4x')
        meter=ReferenceMeter(library,rate,channels) if library else None
        blocks=None if meter else KBlocks(rate,channels)
        peak_meter=None if meter else TruePeak(channels,oversample)
        count=0;squares=peak=0.;clipped=0
        try:
            while data:=w.readframes(32768):
                if len(data)%(width*channels):raise ValidationError('truncated loudness PCM')
                values=[]
                for frame in _decode(data,width,channels):
                    count+=1
                    for x in frame:
                        squares+=x*x;peak=max(peak,abs(x));clipped+=abs(x)>=1-1/(1<<(width*8-1))
                    if meter:values.extend(frame)
                    else:blocks.add(frame);peak_meter.add(frame)
                if meter:meter.add(values)
            if count!=frames:raise ValidationError('truncated loudness PCM')
            result=meter.result() if meter else {**blocks.result(),'true_peak':peak_meter.finish(),
                'backend':'python-windowed-sinc','oversample':oversample,'fir_taps':12*oversample+1}
        finally:
            if meter:meter.close()
    rms=math.sqrt(squares/(count*channels))
    result.update(sample_rate=rate,channels=channels,bits_per_sample=width*8,frames=count,
        duration_seconds=count/rate,sample_peak=peak,sample_peak_dbfs=db(peak),rms=rms,rms_dbfs=db(rms),
        crest_db=db(peak/rms) if rms else None,true_peak_dbtp=db(result['true_peak']),clipped_samples=clipped,
        certified=False,algorithm='K weighting; 400ms / 100ms hop; absolute -70 LUFS, relative -10 LU; finite sinc FIR true peak')
    return result
