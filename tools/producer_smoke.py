#!/usr/bin/env python3
"""Run with an installed Python from a fresh project-local working directory."""
import math
import wave
from pathlib import Path

from kuang.atmosphere import atmosphere_house
from kuang.depth import note_fingerprints
from kuang.midi import export_bytes
from kuang.sample_assets import LICENSES, create_asset, read_asset
from kuang.sampled_instrument import bind_samples
from kuang.schema import save, validate

root=Path.cwd()/'producer-smoke';root.mkdir()
source=root/'original.wav'
with wave.open(str(source),'wb') as w:
    w.setparams((1,3,48000,0,'NONE','not compressed'))
    w.writeframes(b''.join(round(.2*math.sin(i*2*math.pi*70/48000)*(2**23-1)).to_bytes(3,'little',signed=True) for i in range(4800)))
credit={'creator':'Kuang','source':'Original installed-wheel test tone','license':'MIT','license_url':LICENSES['MIT'],
        'notice':(Path(__file__).resolve().parents[1]/'LICENSE').read_text(),'redistribution_permitted':True}
mapping={'root_note':36,'key_low':36,'key_high':36,'velocity_low':1,'velocity_high':127,'key_tracking':False,'playback':'one_shot'}
create_asset(source,root/'asset',credit,mapping);read_asset(root/'asset')
old=atmosphere_house();p=bind_samples(old,{'track-kick':root/'asset'});validate(p)
assert note_fingerprints(p)==note_fingerprints(old)
assert export_bytes(p)==export_bytes(old)
save(p,root/'project.kuang.json')
print('Installed generic asset + full-song binding smoke passed; no host/quality claim')
