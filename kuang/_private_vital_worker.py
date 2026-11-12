"""Isolated optional Pedalboard worker for one already-selected private preset."""
import hashlib
import json
import math
import resource
import sys
from pathlib import Path

from .autonomous_palette import PINNED_MODULES, _bounded_read, _validate_patch, MAX_PRESET_BYTES
from .schema import ValidationError, strict_json
from .vitalium_patch import VERSION, PLUGIN_ID, chunks, component, component_patch, vstpreset


def wave_frames(patch):
    """Compare the embedded waveform payloads while allowing host metadata changes."""
    try:
        waves = patch['settings']['wavetables']
        if len(waves) != 3:
            raise ValueError('wrong wavetable count')
        result = []
        for wave in waves:
            components = []
            for group in wave['groups']:
                for part in group['components']:
                    if part['type'] != 'Wave Source':
                        raise ValueError('unsupported wavetable source')
                    components.append([(frame['position'], frame['wave_data']) for frame in part['keyframes']])
            if not components or any(not frames for frames in components):
                raise ValueError('missing waveform frames')
            result.append(components)
        return result
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError('invalid embedded waveform readback') from exc


def run(job):
    import pedalboard
    if pedalboard.__version__ != '0.9.26':
        raise ValidationError('private worker requires reviewed Pedalboard 0.9.26')
    plugin = Path(job['plugin'])
    module = plugin / 'Contents/x86_64-linux/vitalium.so'
    if job['plugin_sha'] not in PINNED_MODULES or hashlib.sha256(_bounded_read(module, 64*1024*1024)).hexdigest() != job['plugin_sha']:
        raise ValidationError('plugin changed or is not pinned')
    source = _bounded_read(Path(job['source']), MAX_PRESET_BYTES)
    if hashlib.sha256(source).hexdigest() != job['source_sha']:
        raise ValidationError('source hash changed')
    patch = _validate_patch(source, {'compatibility':'version_candidate', 'synth_version':job['version']})
    p = pedalboard.load_plugin(str(plugin))
    if not p.is_instrument or (p.name,p.manufacturer_name,p.version) != ('Vitalium','DISTRHO',VERSION):
        raise ValidationError('unexpected plugin identity')
    defaults = job['defaults']; bindings = []
    for parameter in p._parameters:
        if parameter.index >= 772: continue
        native_id = 0
        for ch in str(parameter.index): native_id = (31*native_id+ord(ch)) & 0x7fffffff
        key = str(native_id)
        if key not in defaults: continue
        steps = parameter.num_steps if 2 <= parameter.num_steps <= 129 else 0
        scale = steps-1 if steps else 1
        if abs(defaults[key] - parameter.raw_value*scale) > .00002:
            raise ValidationError('host/plugin controller defaults differ')
        bindings.append({'index':parameter.index,'native_id':key,'name':parameter.name,
            'canonical_id':'vitalium.param'+str(parameter.index),'scale':scale,'steps':steps,
            'default_normalized':parameter.raw_value})
    if len(bindings) != 771: raise ValidationError('unexpected controller count')
    p.preset_data = vstpreset(component(patch))
    saved = p.preset_data; state = chunks(saved)[b'Comp']; actual = component_patch(state)
    if (actual.get('preset_name') != patch.get('preset_name') or actual.get('author') != patch.get('author') or
            actual.get('settings',{}).get('sample_on') != 0 or wave_frames(actual) != wave_frames(patch)):
        raise ValidationError('plugin readback identity or sample state differs')
    for row in bindings:
        value = float(p._parameters[row['index']].raw_value)
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValidationError('invalid plugin control')
        row['normalized'] = value
    q = pedalboard.load_plugin(str(plugin)); q.preset_data = saved
    restored = component_patch(chunks(q.preset_data)[b'Comp'])
    if (restored.get('preset_name') != patch.get('preset_name') or restored.get('author') != patch.get('author') or
            restored.get('settings',{}).get('sample_on') != 0 or wave_frames(restored) != wave_frames(patch)):
        raise ValidationError('independent plugin identity/sample restoration differs')
    for row in bindings:
        if abs(q._parameters[row['index']].raw_value-row['normalized']) > 2e-6:
            raise ValidationError('independent plugin control restoration differs: '+row['name'])
    out = Path(job['out']); out.mkdir(mode=0o700)
    (out/'patch.vital').write_bytes(source)
    (out/'patch.vstpreset').write_bytes(saved)
    (out/'component.bin').write_bytes(state)
    (out/'bindings.json').write_text(json.dumps(bindings,sort_keys=True,indent=2,allow_nan=False)+'\n')
    files = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
    manifest = {'version':'private-selected-vital-1','plugin':PLUGIN_ID,'plugin_version':VERSION,
        'source_sha256':job['source_sha'],'source_version':job['version'], 'source_name':patch['preset_name'],
        'source_author':patch.get('author'),'license':'unknown; private local use only',
        'plugin_sha256':job['plugin_sha'],'native_defaults':defaults,'sha256':files}
    (out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2,allow_nan=False)+'\n')


if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024*1024,4*1024*1024))
    try:
        job = strict_json(_bounded_read(Path(sys.argv[1]),2*1024*1024).decode())
        run(job)
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc)[:400],file=sys.stderr)
        raise SystemExit(1)
