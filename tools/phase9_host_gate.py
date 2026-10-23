#!/usr/bin/env python3
"""Bounded sampler/asset and master-selector audit, separate from the adapter.

Uses actual CLI operations only. Does not synthesize native JSON or advertise
canonical sampler support. Original synthetic calibration pulse is MIT.
"""

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from kuang.audio import analyze_wav
from kuang.gestures import crop,gesture_house
from kuang.mastering import file_hash
from kuang.schema import ValidationError
from kuang.soundcraft import SoundCraftAdapter
from tools.phase5_house import write
from tools.phase7_house import local


def gate(destination,executable):
    import wave
    root=local(destination)
    if root.exists():raise ValidationError('new host-gate output only')
    root.mkdir(parents=True)
    a=SoundCraftAdapter(executable,timeout=120)
    p=crop(gesture_house(),0,2,['track-kick']);a.export(p,root/'builtin')
    descriptors={}
    for command in ('mix.sampler_load','mix.insert','file.bounce_mix'):
        r=subprocess.run([str(a.executable),'describe',command],capture_output=True,text=True,timeout=30,cwd=root)
        if r.returncode or r.stderr:raise ValidationError('host gate description failed')
        descriptors[command]=json.loads(r.stdout)
    sample=root/'original-pulse.wav'
    with wave.open(str(sample),'wb') as w:
        w.setparams((1,3,48000,0,'NONE','not compressed'))
        w.writeframes(b''.join(round(.3*math.sin(2*math.pi*220*i/48000)*math.exp(-i/2000)*min(1,i/48)*(2**23-1)).to_bytes(3,'little',signed=True) for i in range(12000)))
    native=json.loads((root/'builtin/session.scraft').read_text());tid=native['tracks'][0]['id']

    def run(source,commands,output):
        argv=[str(a.executable),'run','--in',str(source)]
        for command,value in commands:
            if command not in descriptors:raise ValidationError('unknown gate operation')
            argv+=['--cmd',command+'='+json.dumps(value)]
        argv+=['--save',str(output)]
        r=subprocess.run(argv,capture_output=True,text=True,timeout=120,cwd=output.parent)
        return {'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}

    def bounce(path):
        return {'path':str(path),'format':'wav','bit_depth':24,'dither':False,
                'start':{'seconds':0},'end':{'seconds':5}}

    sampler=root/'sampler';sampler.mkdir()
    first=run(root/'builtin/session.scraft',[
        ('mix.sampler_load',{'track':tid,'path':str(sample),'params':{'key_track':0,'play_mode':1,'level':-6}}),
        ('file.bounce_mix',bounce(sampler/'first.wav'))],sampler/'session.scraft')
    report={'capabilities':a.capabilities(p),'descriptors':descriptors,'sample_sha256':file_hash(sample),
        'sample_license':'original deterministic calibration pulse, MIT','load':first,
        'canonical_sampler_supported':False,'candidate_uses_sampler':False,'master_native_supported':False}
    if first['returncode'] or first['stderr']:raise ValidationError('sampler load/render gate failed')
    reopened=root/'reopened';reopened.mkdir()
    shutil.copy2(sampler/'session.scraft',reopened/'session.scraft')
    shutil.copytree(sampler/'Audio Files',reopened/'Audio Files')
    # Hide ALL old working asset paths; the copied Audio Files bundle must
    # suffice. Both saved filenames stay session.scraft for full state equality.
    sampler.rename(root/'hidden-sampler');sample.rename(root/'hidden-pulse')
    try:
        repeated=run(reopened/'session.scraft',[('file.bounce_mix',bounce(reopened/'second.wav'))],reopened/'session.scraft')
    finally:
        (root/'hidden-sampler').rename(sampler);(root/'hidden-pulse').rename(sample)
    if repeated['returncode'] or repeated['stderr']:raise ValidationError('sampler relocated reload failed')
    audio=[analyze_wav(sampler/'first.wav'),analyze_wav(reopened/'second.wav')]
    if any(not m['non_silent'] or m['clipped_samples'] or m['frames']!=240000 for m in audio):raise ValidationError('sampler PCM gate failed')
    same_pcm=file_hash(sampler/'first.wav')==file_hash(reopened/'second.wav')
    same_native=json.loads((sampler/'session.scraft').read_text())==json.loads((reopened/'session.scraft').read_text())
    if not same_pcm or not same_native:raise ValidationError('sampler full state/PCM persistence failed')
    report.update(reopen=repeated,audio=audio,full_native_equal=same_native,pcm_equal=same_pcm,
        relocated_with_original_assets_hidden=True,asset_sha256=file_hash(reopened/'Audio Files/original-pulse.wav'))
    probes={}
    for selector in ('master',0):
        probes[str(selector)]=run(root/'builtin/session.scraft',[('mix.insert',
            {'track':selector,'slot':0,'plugin':'compressor','params':{'threshold':-20}})],root/('master-'+str(selector)+'.scraft'))
    report['master_selector_probes']=probes
    if any(v['returncode']==0 for v in probes.values()):
        raise ValidationError('master selector behavior changed; inspect before claiming support')
    write(root/'gate.json',report)
    return report


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',required=True);parser.add_argument('--soundcraft',required=True)
    args=parser.parse_args();r=gate(args.out_dir,args.soundcraft)
    print(json.dumps({k:r[k] for k in ('full_native_equal','pcm_equal','canonical_sampler_supported','candidate_uses_sampler')}))
