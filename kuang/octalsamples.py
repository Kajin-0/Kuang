"""Read-only, pinned audit/import of the separately obtained CC0 house-core.

No git/npm execution or download. Committed WAV identity and source/license
records are checked against the reviewed commit; authorship is a declaration.
"""
import json
import wave
from importlib.resources import files
from pathlib import Path

from .sample_assets import create_asset, digest, write
from .schema import ValidationError, strict_json

COMMIT = '22d222ce36e290ba3792c776811aa9c69dcc8776'


def catalog():
    return strict_json(files('kuang').joinpath('data/house-core-22d222c.json').read_text())


def inspect_pack(root):
    root = Path(root)
    c = catalog()
    if root.is_symlink() or not root.is_dir():
        raise ValidationError('regular reviewed sample pack required')
    for name, expected in c['reviewed_files'].items():
        path = root/name
        if path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise ValidationError('reviewed sample source/license/script drift: '+name)
    manifest = strict_json((root/'manifest.json').read_text())
    if set(manifest['samples']) != set(c['samples']):
        raise ValidationError('sample manifest identities differ')
    actual = {str(p.relative_to(root)) for p in (root/'samples').rglob('*') if p.is_file()}
    if actual != {v['path'] for v in c['samples'].values()}:
        raise ValidationError('sample pack has missing/extra WAVs')
    for key, sample in c['samples'].items():
        p = root/sample['path']
        if p.is_symlink() or any(a.is_symlink() for a in p.parents if a.is_relative_to(root)) or digest(p) != sample['sha256']:
            raise ValidationError('committed sample PCM identity differs: '+key)
        with wave.open(str(p), 'rb') as w:
            if (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getcomptype()) != (1, 2, 44100, 'NONE') or abs(w.getnframes()/44100-sample['length']) > .001:
                raise ValidationError('source sample format/duration differs')
    return {'commit': COMMIT, 'samples': len(c['samples']), 'files_verified': len(c['reviewed_files']),
        'license': c['license'], 'script_execution': False, 'authorship_authenticated': False,
        'quality_verified': False, 'formats': 'mono 44.1 kHz PCM16'}


def import_sound(root, key, pitch, destination, converter, *, playback='one_shot', conversion_gain_db=0):
    """Selected sounds are original CC0 synthesis, excluding uzu derivatives.

    Cymbals' separate public-domain origins are audited in the source record,
    but not silently relabelled or needed by this unchanged-note song.
    """
    c = catalog()
    if key not in c['samples']:
        raise ValidationError('unknown reviewed sample')
    sample = c['samples'][key]
    if not sample['license_source'].startswith('own synthesis'):
        raise ValidationError('this importer requires original CC0 sounds; separate derivative terms need explicit mapping')
    root, destination = Path(root), Path(destination)
    if destination.exists() or destination.is_symlink() or destination.resolve().is_relative_to(root.resolve()):
        raise ValidationError('new imported asset outside source pack required')
    if digest(root/sample['path']) != sample['sha256']:
        raise ValidationError('selected original sample drift')
    import tempfile
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.convert-') as d:
        converted = Path(d)/'converted.wav'
        report = converter.convert(root/sample['path'], converted, gain_db=conversion_gain_db)
        credit = {'creator': 'octalmusic/octal-samples contributors; see pinned source commit',
            'source': c['repository']+'/blob/'+COMMIT+'/'+sample['path']+
                '; source SHA256 '+sample['sha256']+'; explicit conversion '+json.dumps(report, sort_keys=True),
            'license': 'CC0-1.0', 'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'notice': sample['audit']+'\nPublisher CC0 dedication: '+c['repository']+'/blob/'+COMMIT+'/LICENSE',
            'redistribution_permitted': True}
        mapping = {'root_note': pitch, 'key_low': pitch, 'key_high': pitch, 'velocity_low': 1,
            'velocity_high': 127, 'key_tracking': False, 'playback': playback}
        result = create_asset(converted, destination, credit, mapping)
    return {'key': key, 'trigger_pitch': pitch, 'source_root_note': sample['root_note'],
        'key_tracking': False, 'retuned': False, 'conversion': report, **result}
