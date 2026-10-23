"""Explicit off-host derivation: gentle linked compression and measured gain.

No master-bus claim or limiter fiction. A frozen recipe reproduces the exact
two 24-bit quantization stages without needing the optional reference meter.
"""

import hashlib
import json
import math
import os
import tempfile
import wave
from pathlib import Path

from .loudness import db, measure
from .production_audio import _decode
from .schema import ValidationError, strict_json


def file_hash(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        while data:=f.read(1048576):h.update(data)
    return h.hexdigest()


def validate_recipe(r):
    keys={'version','input_sha256','threshold_dbfs','ratio','attack_ms','release_ms','gain_db','ceiling_dbtp'}
    if type(r) is not dict or set(r)!=keys or r['version']!='gentle-master-1':raise ValidationError('invalid master recipe')
    digest=r['input_sha256']
    if type(digest) is not str or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValidationError('invalid master input hash')
    limits={'threshold_dbfs':(-40,0),'ratio':(1,2),'attack_ms':(1,100),'release_ms':(20,1000),
            'gain_db':(-24,12),'ceiling_dbtp':(-12,-1)}
    for k,(lo,hi) in limits.items():
        if type(r[k]) not in (int,float) or not math.isfinite(r[k]) or not lo<=r[k]<=hi:raise ValidationError('invalid master control: '+k)
    return r


def _fresh(source,destination):
    source=Path(source).resolve();destination=Path(destination)
    if destination.exists() or destination.is_symlink() or source==destination.resolve():raise ValidationError('new master output only')
    if not destination.parent.is_dir():raise ValidationError('master output parent must exist')
    return source,destination


def _compress(source,dest,recipe):
    """Linked peak detector, exponential attack/release, no makeup/clipping."""
    maximum=energy_in=energy_out=0.;active=total=0;envelope=0.
    with wave.open(str(source),'rb') as a,wave.open(str(dest),'wb') as b:
        if a.getnchannels()!=2 or a.getsampwidth()!=3 or a.getframerate()!=48000 or a.getcomptype()!='NONE':
            raise ValidationError('master requires stereo 48k / 24-bit PCM')
        b.setparams(a.getparams());rate=a.getframerate()
        attack=math.exp(-1/(rate*recipe['attack_ms']/1000));release=math.exp(-1/(rate*recipe['release_ms']/1000))
        threshold=recipe['threshold_dbfs'];slope=1-1/recipe['ratio'];limit=2**23
        while data:=a.readframes(32768):
            out=bytearray()
            for frame in _decode(data,3,2):
                detector=max(map(abs,frame));coefficient=attack if detector>envelope else release
                envelope=coefficient*envelope+(1-coefficient)*detector
                reduction=max(0,(db(envelope)-threshold)*slope) if envelope else 0
                gain=10**(-reduction/20);maximum=max(maximum,reduction);active+=reduction>.1;total+=1
                for value in frame:
                    energy_in+=value*value;energy_out+=(value*gain)**2
                    integer=round(value*gain*limit)
                    if not -limit<integer<limit:raise ValidationError('compression would clip')
                    out+=integer.to_bytes(3,'little',signed=True)
            b.writeframes(out)
    return {'maximum_reduction_db':maximum,'active_fraction':active/total,
            'rms_gain_db':10*math.log10(energy_out/energy_in) if energy_in else None,
            'detector':'linked stereo peak, exponential 15ms attack / 150ms release; no makeup',
            'native_editable':False}


def attenuate(source,destination,gain_db):
    source,destination=_fresh(source,destination)
    if type(gain_db) not in (int,float) or not math.isfinite(gain_db) or not -90<=gain_db<=12:raise ValidationError('invalid PCM gain')
    gain=10**(gain_db/20)
    # Stage all PCM before exclusive publication. A racing writer's output
    # must never be truncated or deleted during failure cleanup.
    with tempfile.TemporaryDirectory(prefix='.kuang-gain-',dir=destination.parent) as d:
        staged=Path(d)/'audio.wav'
        with wave.open(str(source),'rb') as a,wave.open(str(staged),'wb') as b:
            if a.getsampwidth()!=3 or a.getcomptype()!='NONE':raise ValidationError('gain derivation requires 24-bit PCM')
            b.setparams(a.getparams())
            while data:=a.readframes(32768):
                out=bytearray()
                for i in range(0,len(data),3):
                    value=round(int.from_bytes(data[i:i+3],'little',signed=True)*gain)
                    if not -(2**23)<value<2**23:raise ValidationError('PCM gain would clip')
                    out+=value.to_bytes(3,'little',signed=True)
                b.writeframes(out)
        os.link(staged,destination)


def apply_master(source,destination,recipe):
    recipe=validate_recipe(recipe);source,destination=_fresh(source,destination)
    if file_hash(source)!=recipe['input_sha256']:raise ValidationError('master input hash mismatch')
    with tempfile.TemporaryDirectory(prefix='.kuang-master-',dir=destination.parent) as d:
        stage=Path(d)/'compressed.wav';stats=_compress(source,stage,recipe)
        attenuate(stage,destination,recipe['gain_db'])
    return {**stats,'input_sha256':file_hash(source),'output_sha256':file_hash(destination),
            'gain_db':recipe['gain_db'],'recipe':recipe}


def plan_master(source,*,library=None):
    source=Path(source).resolve()
    recipe={'version':'gentle-master-1','input_sha256':file_hash(source),
        'threshold_dbfs':-20.,'ratio':1.3,'attack_ms':15.,'release_ms':150.,'gain_db':0.,'ceiling_dbtp':-1.2}
    validate_recipe(recipe)
    with tempfile.TemporaryDirectory(prefix='.kuang-master-plan-',dir=source.parent) as d:
        output=Path(d)/'compressed.wav';stats=_compress(source,output,recipe)
        meter=measure(output,library=library)
    if meter['integrated_lufs'] is None:raise ValidationError('cannot master silence')
    # Use 75% of measured headroom, capped at 3 LU: a conservative experiment,
    # not an invented universal commercial loudness target or hidden limiter.
    headroom=recipe['ceiling_dbtp']-meter['true_peak_dbtp']
    recipe['gain_db']=min(3.,max(0.,.75*headroom)) if headroom>=0 else headroom
    return recipe,{'compressed_measurement':meter,'compression':stats,'available_true_peak_headroom_db':headroom,
                   'choice':'75% of measured headroom, maximum 3 dB gain; no commercial loudness target'}


def match_lufs(source,destination,target,*,library=None):
    source,destination=_fresh(source,destination)
    if type(target) not in (int,float) or not math.isfinite(target):raise ValidationError('invalid LUFS match target')
    original=measure(source,library=library)
    if original['integrated_lufs'] is None:raise ValidationError('cannot level-match silence')
    gain=target-original['integrated_lufs']
    if gain>.00001:raise ValidationError('audition matching attenuates only')
    with tempfile.TemporaryDirectory(prefix='.kuang-match-',dir=destination.parent) as d:
        for iteration in range(3):
            temporary=Path(d)/f'{iteration}.wav';attenuate(source,temporary,min(0,gain))
            measured=measure(temporary,library=library);error=target-measured['integrated_lufs']
            if abs(error)<=.001:
                # Exclusive publication also protects against a racing writer.
                import os
                os.link(temporary,destination)
                return {'gain_db':min(0,gain),'target_lufs':target,'measurement':measured,'error_lu':error,
                        'processing':'constant attenuation only; no hidden EQ/compression'}
            gain+=error
    raise ValidationError('integrated-LUFS matching did not converge')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input');parser.add_argument('output');parser.add_argument('--recipe',required=True)
    args=parser.parse_args()
    print(json.dumps(apply_master(args.input,args.output,strict_json(Path(args.recipe).read_text())),indent=2))
