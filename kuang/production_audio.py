"""Offline production measurements, stdlib only; no perceptual quality score.

Spectrum uses 64 equally spaced 2048-frame Hann windows, both stereo channels,
and a radix-2 FFT. Reported band fractions exclude DC and cover 20 Hz–Nyquist.
They are sampled spectral estimates, not LUFS, true peak or audibility tests.
"""

import cmath
import math
import wave

from .audio import analyze_wav
from .schema import ValidationError

BANDS = (("sub_20_120", 20, 120), ("body_120_500", 120, 500),
         ("mid_500_2000", 500, 2000), ("presence_2000_8000", 2000, 8000),
         ("air_8000_nyquist", 8000, float("inf")))


def _fft(values):
    result = list(map(complex, values))
    size, j = len(result), 0
    for i in range(1, size):
        bit = size >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            result[i], result[j] = result[j], result[i]
    span = 2
    while span <= size:
        root = cmath.exp(-2j*math.pi/span)
        for start in range(0, size, span):
            twiddle = 1
            for offset in range(span//2):
                a = result[start+offset]
                b = twiddle*result[start+offset+span//2]
                result[start+offset], result[start+offset+span//2] = a+b, a-b
                twiddle *= root
        span *= 2
    return result


def _decode(data, width, channels):
    stride = width*channels
    limit = 1 << (width*8-1)
    for offset in range(0, len(data), stride):
        yield tuple(int.from_bytes(data[offset+c*width:offset+(c+1)*width], "little", signed=True)/limit
                    for c in range(channels))


def production_metrics(path, regions=()):
    """regions is [(label, start_seconds, end_seconds)]; no source modifications."""
    audio = analyze_wav(path)
    if audio["channels"] != 2:
        raise ValidationError("production stereo measurements require two channels")
    rate, count = audio["sample_rate"], audio["frames"]
    metrics = {**audio, "crest_db": audio["peak_dbfs"]-audio["rms_dbfs"] if audio["rms"] else None}
    selections = [("full", 0, count)]
    labels = {"full"}
    for label, start, end in regions:
        if (not isinstance(label, str) or not label or label in labels or
                type(start) not in (int, float) or type(end) not in (int, float) or
                not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end <= count/rate):
            raise ValidationError("invalid production measurement region")
        labels.add(label)
        selections.append((label, round(start*rate), round(end*rate)))
    sections = {}
    with wave.open(str(path), "rb") as stream:
        width = stream.getsampwidth()
        for label, start, end in selections:
            stream.setpos(start)
            squares = left = right = cross = side = peak = frames = 0
            remaining = end-start
            while remaining:
                data = stream.readframes(min(65536, remaining))
                if not data:
                    raise ValidationError("truncated production WAV")
                for l, r in _decode(data, width, 2):
                    squares += l*l+r*r
                    left += l*l
                    right += r*r
                    cross += l*r
                    side += ((l-r)*.5)**2
                    peak = max(peak, abs(l), abs(r))
                    frames += 1
                remaining -= len(data)//(2*width)
            if frames == 0:
                raise ValidationError("production region rounds to zero frames")
            rms = math.sqrt(squares/(2*frames))
            sections[label] = {"start_frame": start, "end_frame": end, "rms": rms, "peak": peak,
                "rms_dbfs": 20*math.log10(rms) if rms else None,
                "crest_db": 20*math.log10(peak/rms) if rms else None,
                "stereo_correlation": cross/math.sqrt(left*right) if left*right else None,
                "side_rms": math.sqrt(side/frames)}
        size, windows = 2048, min(64, count//2048)
        if not windows:
            raise ValidationError("production spectrum requires at least 2048 frames")
        powers = [0.0]*(size//2+1)
        hann = [.5-.5*math.cos(2*math.pi*i/(size-1)) for i in range(size)]
        for index in range(windows):
            stream.setpos(round(index*(count-size)/max(1, windows-1)))
            frames = list(_decode(stream.readframes(size), width, 2))
            for channel in range(2):
                spectrum = _fft([frame[channel]*w for frame, w in zip(frames, hann)])
                for k in range(1, len(powers)):
                    # One-sided power; Nyquist has no negative-frequency twin.
                    powers[k] += abs(spectrum[k])**2*(1 if k == size//2 else 2)
        bands = {name: sum(v for k, v in enumerate(powers) if low <= k*rate/size < high)
                 for name, low, high in BANDS}
        total = sum(bands.values())
    metrics.update(sections=sections, spectrum={"method": "2048-frame Hann FFT, equally spaced windows, sum of stereo powers",
                   "windows": windows, "bin_hz": rate/size,
                   "band_power_fraction": {k: v/total if total else 0 for k, v in bands.items()}})
    return metrics
