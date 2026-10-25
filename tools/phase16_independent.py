"""Separate optional GPL host: render original calibration, no factory content."""
import json
import sys
import wave
from pathlib import Path
import numpy as np
import pedalboard

if __name__ == '__main__':
    if pedalboard.__version__ != '0.9.26':
        raise SystemExit('reviewed optional host version required')
    q = json.loads(Path(sys.argv[1]).read_text())
    if set(q) != {'plugin', 'patches', 'out'}:
        raise SystemExit('strict independent render request required')
    for voice, patch in q['patches'].items():
        p = pedalboard.load_plugin(q['plugin'])
        preset = (Path(patch)/'patch.vstpreset').read_bytes()
        p.preset_data = preset
        if p.version != '1.0.6' or p.manufacturer_name != 'DISTRHO':
            raise SystemExit('reviewed independent instrument required')
        events = []
        for i, n in enumerate((36, 43, 51, 55, 58, 62, 63, 65, 67)):
            on = (i*12+.5)*60/126
            events += [(bytes([0x90,n,96]), on), (bytes([0x80,n,0]), on+3*60/126)]
        for n in (51, 55, 58, 62):
            on = (9*12+.5)*60/126
            events += [(bytes([0x90,n,96]), on), (bytes([0x80,n,0]), on+3*60/126)]
        events.sort(key=lambda x:x[1])
        audio = p(events, duration=30*4*60/126+5, sample_rate=48000, num_channels=2, buffer_size=512)
        # Calibration attenuation only, identical for all notes; no pitch DSP.
        audio *= .10
        if not np.isfinite(audio).all() or np.max(np.abs(audio)) >= 1:
            raise SystemExit('invalid independent calibration PCM')
        data = np.rint(audio.T.reshape(-1)*2**23).astype('<i4').view(np.uint8).reshape(-1,4)[:,:3].tobytes()
        with wave.open(str(Path(q['out'])/(voice+'-independent.wav')), 'wb') as w:
            w.setparams((2,3,48000,0,'NONE',''));w.writeframes(data)
