"""Optional GPL Pedalboard host worker, invoked in a separate interpreter.

Kuang does not depend on/import Pedalboard in its normal runtime. No downloads,
network services, factory presets or binary redistribution occur here. The
tested private parameter-index API is deliberately pinned; upgrades fail closed.
"""
import base64
import hashlib
import json
import math
import sys
from pathlib import Path

from .schema import ValidationError,strict_json
from .vitalium_patch import PLUGIN_ID,VERSION,chunks,component,original_patch,vstpreset


def prepare(job):
    if type(job) is not dict or set(job)!={'plugin','defaults','role','modulation','volume_db','out'}:
        raise ValidationError('invalid worker request')
    import pedalboard
    if pedalboard.__version__!='0.9.26':raise ValidationError('worker requires reviewed Pedalboard 0.9.26')
    p=pedalboard.load_plugin(job['plugin'])
    if not p.is_instrument or (p.name,p.manufacturer_name,p.version)!=('Vitalium','DISTRHO',VERSION):
        raise ValidationError('this worker validates DISTRHO Vitalium 1.0.6 only; official Vital is untested')
    defaults=job['defaults'];bindings=[]
    for parameter in p._parameters:
        if parameter.index>=772:continue
        native_id=0
        for char in str(parameter.index):native_id=(31*native_id+ord(char))&0x7fffffff
        key=str(native_id)
        # The VST3 bypass is excluded by SoundCraft's discovered registry.
        if key not in defaults:continue
        scale=parameter.num_steps-1 if 2<=parameter.num_steps<=129 else 1
        if abs(defaults[key]-parameter.raw_value*scale)>.00002:
            raise ValidationError('SoundCraft/independent-host default parameter disagreement: '+parameter.name)
        bindings.append({'index':parameter.index,'native_id':key,'name':parameter.name,
            'canonical_id':'vitalium.param'+str(parameter.index),'scale':scale,
            'steps':parameter.num_steps if 2<=parameter.num_steps<=129 else 0,
            'default_normalized':parameter.raw_value})
    if len(bindings)!=771:raise ValidationError('unexpected Vitalium controller layout')
    patch=original_patch(job['role'],modulation=job['modulation'],volume_db=job['volume_db'])
    p.preset_data=vstpreset(component(patch))
    saved=p.preset_data;state=chunks(saved)[b'Comp']
    readback=strict_json(state[state.index(b'{'):state.rindex(b'}')+1].decode())
    for key,value in patch['settings'].items():
        if key not in readback['settings']:raise ValidationError('plugin does not expose original control: '+key)
        if type(value) in (int,float) and not math.isclose(value,readback['settings'][key],rel_tol=2e-6,abs_tol=1e-6):
            raise ValidationError('plugin did not restore original control: '+key)
    connections=[{k:v for k,v in x.items() if k in ('source','destination')} for x in readback['settings']['modulations'] if x['source']]
    if connections!=patch['settings']['modulations']:raise ValidationError('actual modulation connections differ')
    sample=readback['settings']['sample']
    if sample['length']!=32 or base64.b64decode(sample['samples'],validate=True)!=bytes(64):
        raise ValidationError('unexpected sample content')
    if readback['settings']['wavetables']!=patch['settings']['wavetables'] or readback['settings']['lfos'][0]!=patch['settings']['lfos'][0]:
        raise ValidationError('actual wavetable/LFO shapes differ from original formulas')
    for row in bindings:
        parameter=p._parameters[row['index']]
        value=parameter.raw_value
        if not math.isfinite(value) or not 0<=value<=1:raise ValidationError('invalid actual normalized control')
        row['normalized']=value
    # A second real plugin restores the saved VST3 state. Verify every mapped
    # control and the full component payload, not just a device's name.
    q=pedalboard.load_plugin(job['plugin']);q.preset_data=saved
    for row in bindings:
        if abs(q._parameters[row['index']].raw_value-row['normalized'])>2e-6:
            raise ValidationError('independent VST3 state restoration failed: '+row['name'])
    if chunks(q.preset_data)[b'Comp']!=state:raise ValidationError('repeated component state differs')
    out=Path(job['out']);out.mkdir()
    (out/'patch.vital').write_text(json.dumps(patch,sort_keys=True,indent=2)+'\n')
    (out/'patch.vstpreset').write_bytes(saved);(out/'component.bin').write_bytes(state)
    (out/'bindings.json').write_text(json.dumps(bindings,sort_keys=True,indent=2)+'\n')
    manifest={'version':'external-patch-1','plugin':PLUGIN_ID,'plugin_version':VERSION,
        'role':job['role'],'license':'Original Kuang patch/waves MIT; external Vitalium GPL-3.0-or-later, Pedalboard GPL-3.0 separately installed',
        'host':'Pedalboard 0.9.26','original_content_only':True,'factory_content':False,
        'native_defaults':defaults,
        'all_normalized_parameters_restored':True,'component_roundtrip_exact':True,
        'sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir())}}
    (out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: python -m kuang.vst3_worker REQUEST.json')
    try:
        p=Path(sys.argv[1])
        if p.stat().st_size>2**20:raise ValidationError('oversized worker request')
        print(json.dumps(prepare(strict_json(p.read_text())),sort_keys=True))
    except (ValidationError,ImportError) as exc:
        raise SystemExit(str(exc))
