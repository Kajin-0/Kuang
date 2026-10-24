"""Licensed, content-addressed one-sample assets. No downloads or SFZ claims."""
import hashlib
import json
import math
import os
import shutil
import struct
import tempfile
import wave
from pathlib import Path

from .schema import ValidationError, strict_json

MAX_BYTES = 32*2**20
LICENSES = {'CC0-1.0': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'CC-BY-4.0': 'https://creativecommons.org/licenses/by/4.0/',
            'MIT': 'https://opensource.org/license/mit'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    Path(path).write_text(json.dumps(data, sort_keys=True, indent=2, allow_nan=False)+'\n')


def inventory(root):
    root=Path(root)
    if root.is_symlink() or any(p.is_symlink() for p in root.rglob('*')):
        raise ValidationError('sample/bundle symlinks are unsupported')
    return {str(p.relative_to(root)):digest(p) for p in sorted(root.rglob('*')) if p.is_file()}


def provenance(data):
    keys={'creator','source','license','license_url','notice','redistribution_permitted'}
    if type(data) is not dict or set(data)!=keys:
        raise ValidationError('exact sample provenance fields required')
    if type(data['license']) is not str or data['license'] not in LICENSES or data['license_url']!=LICENSES[data['license']]:
        raise ValidationError('unreviewed sample license identifier/URL')
    if data['redistribution_permitted'] is not True:
        raise ValidationError('portable assets require declared raw-file redistribution rights')
    for key in ('creator','source','notice'):
        if type(data[key]) is not str or not data[key].strip() or len(data[key])>8192 or '\x00' in data[key]:
            raise ValidationError('missing/oversized sample attribution: '+key)
    if data['license']=='MIT' and not all(s in data['notice'] for s in (
            'Permission is hereby granted, free of charge', 'THE SOFTWARE IS PROVIDED')):
        raise ValidationError('retain the complete supplied MIT copyright/permission/disclaimer notice')
    return data


def mapping(data):
    if type(data) is not dict or set(data)!={'root_note','key_low','key_high','velocity_low','velocity_high','key_tracking','playback'}:
        raise ValidationError('exact single-sample mapping required')
    for key in ('root_note','key_low','key_high','velocity_low','velocity_high'):
        lo=1 if key.startswith('velocity') else 0
        if type(data[key]) is not int or not lo<=data[key]<=127:
            raise ValidationError('invalid semantic MIDI mapping: '+key)
    if data['key_low']>data['key_high'] or data['velocity_low']>data['velocity_high']:
        raise ValidationError('reversed sample key/velocity range')
    if type(data['key_tracking']) is not bool or data['playback'] not in ('gate','one_shot'):
        raise ValidationError('unsupported sample playback mapping')
    return data


def pcm_info(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_BYTES:
        raise ValidationError('missing/oversized/symlink sample')
    try:
        with wave.open(str(path),'rb') as w:
            channels,width,rate,frames=w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()
            if channels not in (1,2) or width not in (2,3) or rate!=48000 or not 1<=frames<=30*rate or w.getcomptype()!='NONE':
                raise ValidationError('sample needs 48k mono/stereo 16/24-bit PCM, at most 30s')
            data=w.readframes(frames)
            if len(data)!=channels*width*frames:raise ValidationError('truncated sample PCM')
    except (wave.Error, EOFError, OSError) as e:
        raise ValidationError('invalid sample WAV') from e
    limit=1<<(8*width-1);peak=0;normalized=hashlib.sha256()
    for i in range(0,len(data),width):
        value=int.from_bytes(data[i:i+width],'little',signed=True)
        peak=max(peak,abs(value))
        normalized.update(struct.pack('<f',value/limit))
    if not peak or peak>=limit-1:raise ValidationError('silent or clipped sample rejected')
    return {'sample_rate':rate,'channels':channels,'bits_per_sample':8*width,'frames':frames,
            'float32_pcm_sha256':normalized.hexdigest()}


def create_asset(wav, destination, credit, note_mapping):
    wav=Path(wav);destination=Path(destination)
    if destination.exists() or destination.is_symlink():raise ValidationError('new asset destination required')
    provenance(credit);mapping(note_mapping);info=pcm_info(wav);sha=digest(wav)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent,prefix='.sample-') as d:
        stage=Path(d);filename='audio-'+sha+'.wav';shutil.copyfile(wav,stage/filename)
        if digest(stage/filename)!=sha:raise ValidationError('sample source changed during copy')
        write(stage/'asset.json',{'version':'sample-asset-1','file':filename,'sha256':sha,
              'audio':info,'provenance':credit,'mapping':note_mapping})
        read_asset(stage)
        destination.mkdir()
        try:
            for p in stage.iterdir():p.rename(destination/p.name)
        except BaseException:shutil.rmtree(destination);raise
    return {'asset':str(destination),'manifest_sha256':digest(destination/'asset.json')}


def read_asset(root):
    root=Path(root)
    if root.is_symlink() or (root/'asset.json').is_symlink() or not (root/'asset.json').is_file() or (root/'asset.json').stat().st_size>32768:
        raise ValidationError('missing/oversized sample asset manifest')
    m=strict_json((root/'asset.json').read_text())
    if type(m) is not dict or set(m)!={'version','file','sha256','audio','provenance','mapping'} or m['version']!='sample-asset-1':
        raise ValidationError('unsupported sample asset manifest')
    sha=m['sha256']
    if type(sha) is not str or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha) or m['file']!='audio-'+sha+'.wav':
        raise ValidationError('invalid content-addressed sample path/hash')
    provenance(m['provenance']);mapping(m['mapping'])
    actual=inventory(root)
    if any(p.is_dir() for p in root.rglob('*')):raise ValidationError('unexpected asset subdirectory')
    if set(actual)!={'asset.json',m['file']} or actual[m['file']]!=sha or pcm_info(root/m['file'])!=m['audio']:
        raise ValidationError('sample asset content/format/closure drift')
    return m


def verify_native_audio(path, expected):
    """Host saves decoded source as float32 WAVE_EXTENSIBLE, not original WAV.

    Validate the bounded RIFF structure and exact normalized PCM identity.
    No host JSON or media is rewritten. Metadata/file hashes are separately
    retained by the native bundle inventory.
    """
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>MAX_BYTES*2:
        raise ValidationError('invalid native sample source')
    b=p.read_bytes()
    if len(b)<12 or b[:4]!=b'RIFF' or b[8:12]!=b'WAVE' or struct.unpack_from('<I',b,4)[0]+8!=len(b):
        raise ValidationError('invalid native sample RIFF')
    chunks={};i=12
    while i+8<=len(b):
        tag,size=struct.unpack_from('<4sI',b,i);end=i+8+size
        if end>len(b) or (tag in (b'fmt ',b'data') and tag in chunks):raise ValidationError('invalid native WAV chunks')
        if tag in (b'fmt ',b'data'):chunks[tag]=b[i+8:end]
        i=end+(size%2)
    if i!=len(b) or set(chunks)!={b'fmt ',b'data'}:raise ValidationError('incomplete native sample chunks')
    fmt=chunks[b'fmt ']
    if len(fmt)<16:raise ValidationError('short native WAV format')
    kind,ch,rate,byte_rate,align,bits=struct.unpack_from('<HHIIHH',fmt)
    if kind==65534:
        if (len(fmt)!=40 or struct.unpack_from('<HHI',fmt,16)!=(22,32,4 if ch==1 else 3) or
            fmt[24:]!=bytes.fromhex('0300000000001000800000aa00389b71')):
            raise ValidationError('unsupported native WAV subformat')
    elif kind!=3:raise ValidationError('native source must be float32 WAV')
    if (ch,rate,bits,align,byte_rate)!=(expected['channels'],48000,32,expected['channels']*4,48000*expected['channels']*4):
        raise ValidationError('native sample format drift')
    payload=chunks[b'data']
    if len(payload)!=expected['frames']*ch*4 or hashlib.sha256(payload).hexdigest()!=expected['float32_pcm_sha256']:
        raise ValidationError('native decoded sample PCM differs from licensed source')
    return digest(path)
