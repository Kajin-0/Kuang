"""Explicit offline WAV conversion through optional libsamplerate 0.2.2.

No library discovery/download or runtime sampler dependency. SRC_SINC_BEST_QUALITY
uses the public C API; no third-party implementation is copied or bundled.
"""
import ctypes as C
import math
import os
import tempfile
import wave
from pathlib import Path

from .sample_assets import digest
from .schema import ValidationError


class _Data(C.Structure):
    _fields_ = [('data_in', C.POINTER(C.c_float)), ('data_out', C.POINTER(C.c_float)),
        ('input_frames', C.c_long), ('output_frames', C.c_long),
        ('input_frames_used', C.c_long), ('output_frames_gen', C.c_long),
        ('end_of_input', C.c_int), ('src_ratio', C.c_double)]


class SincConverter:
    def __init__(self, library):
        path = Path(library)
        if path.is_symlink() or not path.is_file():
            raise ValidationError('explicit regular libsamplerate library required')
        self.path = path.resolve()
        self.sha256 = digest(path)
        self.lib = C.CDLL(str(self.path))
        self.lib.src_get_version.restype = C.c_char_p
        self.lib.src_get_description.argtypes = [C.c_int]
        self.lib.src_get_description.restype = C.c_char_p
        self.lib.src_simple.argtypes = [C.POINTER(_Data), C.c_int, C.c_int]
        self.lib.src_simple.restype = C.c_int
        self.version = self.lib.src_get_version().decode()
        if not self.version.startswith('libsamplerate-0.2.2 '):
            raise ValidationError('reviewed libsamplerate 0.2.2 required')

    def convert(self, source, destination, *, gain_db=0):
        source, destination = Path(source), Path(destination)
        if source.is_symlink() or destination.exists() or destination.is_symlink():
            raise ValidationError('regular source and new conversion WAV required')
        if type(gain_db) not in (int, float) or not math.isfinite(gain_db) or not -24 <= gain_db <= 0:
            raise ValidationError('explicit conversion attenuation must be -24..0 dB')
        before = digest(source)
        with wave.open(str(source), 'rb') as w:
            ch, width, rate, count = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            if ch not in (1, 2) or width not in (2, 3) or rate != 44100 or not 1 <= count <= 30*rate:
                raise ValidationError('conversion accepts bounded 44.1k mono/stereo integer PCM only')
            raw = w.readframes(count)
            if len(raw) != count*ch*width:
                raise ValidationError('truncated source')
        # Explicit zero drain preserves reconstruction tails without moving
        # the original onset or fading/normalizing any original samples.
        pad = 256
        src = (C.c_float*((count+pad)*ch))()
        for i in range(count*ch):
            src[i] = int.from_bytes(raw[i*width:(i+1)*width], 'little', signed=True)/2**(8*width-1)
        capacity = math.ceil((count+pad)*48000/rate)+256
        dst = (C.c_float*(capacity*ch))()
        data = _Data(src, dst, count+pad, capacity, 0, 0, 1, 48000/rate)
        error = self.lib.src_simple(C.byref(data), 0, ch)
        if error or data.input_frames_used != count+pad or not 0 < data.output_frames_gen <= capacity:
            raise ValidationError('sinc conversion did not consume/produce the complete input')
        payload = bytearray()
        for i in range(data.output_frames_gen*ch):
            value = float(dst[i])*10**(gain_db/20)
            if not math.isfinite(value) or abs(value) >= 1:
                raise ValidationError('conversion overshoot; explicit gain decision required')
            payload += round(value*2**23).to_bytes(3, 'little', signed=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.src-') as d:
            path = Path(d)/'converted.wav'
            with wave.open(str(path), 'wb') as w:
                w.setparams((ch, 3, 48000, 0, 'NONE', 'not compressed'));w.writeframes(payload)
            if digest(source) != before:
                raise ValidationError('conversion source drift')
            os.link(path, destination)
        return {'source_sha256': before, 'converted_sha256': digest(destination),
            'source_rate': rate, 'destination_rate': 48000, 'source_frames': count,
            'destination_frames': data.output_frames_gen, 'channels': ch,
            'input_bits': width*8, 'output_bits': 24, 'gain_db': gain_db, 'dither': False,
            'zero_drain_input_frames': pad, 'library_version': self.version,
            'library_sha256': self.sha256, 'converter': self.lib.src_get_description(0).decode(),
            'license': 'BSD-2-Clause; optional external offline conversion library, not bundled'}
