"""Bounded, local-only heuristic preset audition; not a song generator.

Foreign presets are never sent to the original-only ExternalSynthAdapter.
Runtime auditions use an isolated, network-disabled subprocess and a pinned
Vitalium module; selected source files remain in the user's private library.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from .schema import ValidationError, strict_json
from .song import check_prompt

ROLES = ('chord', 'pad', 'bass')
ROLE_STYLES = {'chord': {'keys', 'chord', 'pluck', 'piano'},
               'pad': {'pad', 'pads'}, 'bass': {'bass'}}
ROLE_WORDS = {'chord': {'chord', 'chords', 'keys', 'key', 'stab', 'stabs', 'pluck', 'plucks'},
              'pad': {'pad', 'pads', 'atmosphere', 'atmospheric', 'texture'},
              'bass': {'bass', 'sub', 'subbass'}}
PINNED_MODULES = {'d92f7925401ad4706758fca613236b1026894b9c7a5f4901fda56058827e655d',
                  'c6329121bd9a4923a54d3e55a9fba9bf8635a1e1d8990fa4be69a05703ed24c1'}
MAX_CATALOG_BYTES = 8 * 1024 * 1024
MAX_PRESET_BYTES = (1 << 20) - 2048
MAX_ROWS = 10000
MAX_SOURCE_ARCHIVES = 100
SHA = re.compile(r'^[0-9a-f]{64}$')
VERSION = re.compile(r'^(\d{1,2})\.(\d{1,2})\.(\d{1,2})$')
TOKEN = re.compile(r'[a-z0-9]+')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(data, label):
    try:
        value = strict_json(data.decode('utf-8'))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ValidationError(f'{label}: invalid strict UTF-8 JSON') from exc
    if type(value) is not dict:
        raise ValidationError(f'{label}: expected JSON object')
    return value


def _no_symlinks(path):
    path = Path(os.path.abspath(os.fspath(path)))
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValidationError('symlinks are not permitted in trusted input paths')
    return path


def _bounded_read(path, maximum):
    path = Path(os.path.abspath(os.fspath(path)))
    descriptors = _open_directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, 'O_CLOEXEC', 0), dir_fd=descriptors[-1])
        descriptors.append(fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise ValidationError('missing, non-regular, or oversized input')
        with os.fdopen(os.dup(fd), 'rb') as f:
            data = f.read(maximum + 1)
    except OSError as exc:
        raise ValidationError('input could not be safely opened') from exc
    finally:
        for fd in reversed(descriptors): os.close(fd)
    if len(data) > maximum:
        raise ValidationError('oversized input')
    return data


def _relative_parts(value):
    if (type(value) is not str or not value or len(value) > 1024 or '\\' in value or
            '\x00' in value or value.startswith('/') or re.match(r'^[A-Za-z]:', value)):
        raise ValidationError('invalid preset path')
    try:
        value.encode('utf-8')
    except UnicodeError as exc:
        raise ValidationError('preset path must be valid UTF-8') from exc
    parts = value.split('/')
    if any(part in ('', '.', '..') or len(part) > 255 for part in parts):
        raise ValidationError('preset path must be confined and canonical')
    if any(any(ord(c) < 32 or ord(c) == 127 for c in part) for part in parts):
        raise ValidationError('control characters are not permitted in preset paths')
    if not parts[-1].lower().endswith('.vital'):
        raise ValidationError('preset must be a .vital file')
    return parts


def _open_directory(path):
    # Open every absolute component with O_NOFOLLOW, not just the final file.
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise ValidationError('safe no-follow directory opens are unavailable')
    path = Path(os.path.abspath(os.fspath(path)))
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, 'O_CLOEXEC', 0)
    descriptors = []
    try:
        current = os.open('/', flags); descriptors.append(current)
        for part in path.parts[1:]:
            current = os.open(part, flags, dir_fd=current); descriptors.append(current)
        return descriptors
    except OSError as exc:
        for fd in reversed(descriptors): os.close(fd)
        raise ValidationError('directory missing, unsafe, or symlinked') from exc


def _read_preset(root, relative, expected_size, expected_hash):
    """Descriptor-relative traversal prevents symlink escapes and path races."""
    parts = _relative_parts(relative)
    if type(expected_size) is not int or not 0 < expected_size <= MAX_PRESET_BYTES:
        raise ValidationError('invalid or oversized catalog preset')
    if type(expected_hash) is not str or not SHA.fullmatch(expected_hash):
        raise ValidationError('invalid catalog SHA-256')
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise ValidationError('safe no-follow opens are unavailable')
    flags = os.O_RDONLY | getattr(os, 'O_CLOEXEC', 0) | os.O_NOFOLLOW
    directory = flags | os.O_DIRECTORY
    descriptors = _open_directory(root)
    try:
        current = descriptors[-1]
        for part in parts[:-1]:
            current = os.open(part, directory, dir_fd=current)
            descriptors.append(current)
        fd = os.open(parts[-1], flags, dir_fd=current)
        descriptors.append(fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size != expected_size:
            raise ValidationError('preset file is missing, non-regular, or size differs')
        with os.fdopen(os.dup(fd), 'rb') as f:
            data = f.read(MAX_PRESET_BYTES + 1)
        if len(data) != expected_size or _sha(data) != expected_hash:
            raise ValidationError('preset size or SHA-256 does not match catalog')
        return data
    except OSError as exc:
        raise ValidationError('preset missing, unsafe, or symlinked') from exc
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def _version(value):
    if type(value) is not str or not (m := VERSION.fullmatch(value)):
        raise ValidationError('missing or invalid synth version')
    return tuple(map(int, m.groups()))


def _validate_patch(data, row):
    patch = _json_bytes(data, 'preset')
    version = patch.get('synth_version')
    if (row.get('compatibility') != 'version_candidate' or version != row.get('synth_version') or
            _version(version) > (1, 0, 6)):
        raise ValidationError('preset version is unverified or newer than Vitalium 1.0.6')
    pending = [patch]
    visited = 0
    while pending:
        obj = pending.pop(); visited += 1
        if visited > 200000:
            raise ValidationError('preset structure is too complex')
        if type(obj) is dict:
            for key, value in obj.items():
                if re.search(r'(^|_)(?:file|filename|path|url|uri|external)(?:_|$)', key.lower()):
                    raise ValidationError('external resource reference unsupported')
                pending.append(value)
        elif type(obj) is list:
            pending.extend(obj)
        elif type(obj) is float and not math.isfinite(obj):
            raise ValidationError('non-finite preset value')
    settings = patch.get('settings')
    if type(settings) is not dict or type(settings.get('sample_on')) not in (int, float) or settings['sample_on'] != 0:
        raise ValidationError('sample oscillator enabled or sample state missing')
    sample = settings.get('sample')
    if type(sample) is not dict or type(sample.get('length')) is not int or type(sample.get('samples')) is not str:
        raise ValidationError('missing embedded sample state')
    try:
        sample_data = base64.b64decode(sample['samples'], validate=True)
    except (ValueError, TypeError) as exc:
        raise ValidationError('invalid embedded sample state') from exc
    if not 0 <= sample['length'] <= MAX_PRESET_BYTES // 2 or len(sample_data) != 2 * sample['length']:
        raise ValidationError('embedded sample state length mismatch')
    waves = settings.get('wavetables')
    if type(waves) is not list or len(waves) != 3:
        raise ValidationError('three embedded wavetables are required')
    for wave in waves:
        groups = wave.get('groups') if type(wave) is dict else None
        if type(groups) is not list or not groups:
            raise ValidationError('missing embedded wavetable groups')
        for group in groups:
            components = group.get('components') if type(group) is dict else None
            if type(components) is not list or not components:
                raise ValidationError('missing embedded wavetable components')
            for item in components:
                frames = item.get('keyframes') if type(item) is dict else None
                if type(item) is not dict or item.get('type') != 'Wave Source' or type(frames) is not list or not frames:
                    raise ValidationError('external or unsupported wavetable resource')
                for frame in frames:
                    try:
                        raw = base64.b64decode(frame['wave_data'], validate=True)
                    except (KeyError, TypeError, ValueError) as exc:
                        raise ValidationError('invalid embedded waveform') from exc
                    if len(raw) != 8192:
                        raise ValidationError('unexpected embedded waveform length')
                    if any(not math.isfinite(v[0]) or abs(v[0]) > 4 for v in struct.iter_unpack('<f', raw)):
                        raise ValidationError('invalid embedded waveform samples')
    if type(patch.get('preset_name')) is not str or not patch['preset_name'] or len(patch['preset_name']) > 256:
        raise ValidationError('missing or oversized preset identity')
    if row.get('preset_name') is not None and patch['preset_name'] != row['preset_name']:
        raise ValidationError('preset identity differs from catalog')
    if patch.get('author') is not None and (type(patch['author']) is not str or len(patch['author']) > 256):
        raise ValidationError('invalid preset author')
    return patch


def _tokens(value):
    return set(TOKEN.findall(re.sub(r'([a-z])([A-Z])', r'\1 \2', value).lower()))


def _intent(prompt):
    roles = []
    clauses = re.split(r'[,;\n]', prompt.lower())
    words = _tokens(prompt)
    role_terms = {}
    for role in ROLES:
        if re.search(r'\b(?:no|without)\s+(?:\w+\s+){0,2}' + ('(?:chords?|keys?|stabs?)' if role == 'chord' else role + r's?') + r'\b', prompt.lower()):
            continue
        roles.append(role)
        terms = set()
        for clause in clauses:
            if _tokens(clause) & ROLE_WORDS[role]:
                terms |= _tokens(clause)
        role_terms[role] = sorted(terms - set().union(*ROLE_WORDS.values()))
    if not roles:
        raise ValidationError('prompt excludes every supported role')
    key_matches = re.findall(r'\b([a-g])\s*([#b♯♭]?)\s+(major|minor)\b', prompt.lower())
    keys = {(({'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}[note] +
              {'': 0, '#': 1, '♯': 1, 'b': -1, '♭': -1}[accidental]) % 12, mode)
            for note, accidental, mode in key_matches}
    if len(keys) > 1:
        raise ValidationError('use one major/minor key for the audition')
    tonic, mode = next(iter(keys)) if keys else (0, 'minor')
    return {'roles': roles, 'genre': 'house' if 'house' in words else 'unspecified',
            'tonic': tonic, 'mode': mode, 'key_defaulted': not bool(keys),
            'prompt_tokens': sorted(words), 'role_terms': role_terms}


def _semantic_score(row, role, intent):
    name = row.get('preset_name', '')
    path = row.get('path', '')
    if type(name) is not str or type(path) is not str:
        return 0.0
    text = _tokens(name + ' ' + path)
    terms = set(intent['role_terms'][role]) - {'house', 'the', 'and', 'with', 'a', 'in'}
    common = set(intent['prompt_tokens']) & {'deep', 'dark', 'warm', 'bright', 'soft', 'hypnotic', 'funky', 'lush'}
    hits = len(text & terms) * 2 + len(text & common)
    role_bonus = 1 if text & ROLE_WORDS[role] else 0
    return round(min(1., (hits + role_bonus) / 8.), 6)


def _role_candidates(rows, role, intent, seed):
    candidates = []
    for row in rows:
        if type(row) is not dict or type(row.get('preset_style')) is not str:
            continue
        if row['preset_style'].strip().lower() not in ROLE_STYLES[role]:
            continue
        if row.get('compatibility') != 'version_candidate':
            continue
        path = row.get('path')
        if type(path) is not str:
            continue
        score = _semantic_score(row, role, intent)
        tie = _sha(f'{seed}\0{role}\0{path}'.encode('utf-8', errors='replace'))
        candidates.append((score, tie, row))
    return sorted(candidates, key=lambda item: (-item[0], item[1]))


def score_features(role, f):
    """Normalized technical heuristic; independent of absolute loudness."""
    if role not in ROLES or type(f) is not dict:
        raise ValidationError('invalid role or feature object')
    required = ('low_fraction', 'mid_fraction', 'high_fraction', 'attack_ratio', 'tail_ratio', 'stereo_side_fraction', 'crest_db')
    if any(type(f.get(k)) not in (int, float) or not math.isfinite(f[k]) for k in required):
        raise ValidationError('missing or non-finite audio features')
    if any(not 0 <= f[k] <= 1 for k in ('low_fraction', 'mid_fraction', 'high_fraction', 'stereo_side_fraction')):
        raise ValidationError('invalid spectral or stereo fraction')
    if abs(sum(f[k] for k in ('low_fraction', 'mid_fraction', 'high_fraction')) - 1) > .05:
        raise ValidationError('spectral fractions must sum to one')
    if not 0 <= f['attack_ratio'] <= 20 or not 0 <= f['tail_ratio'] <= 20 or not 0 <= f['crest_db'] <= 100:
        raise ValidationError('invalid envelope features')
    def near(value, ideal, width):
        return max(0., 1. - abs(value - ideal) / width)
    targets = {'bass': (.75, .22, .03, .9, .12, .04),
               'chord': (.12, .70, .18, .85, .20, .15),
               'pad': (.10, .65, .25, .35, .45, .25)}[role]
    widths = (.75, .70, .50, 1.3, 1.5, .55)
    keys = ('low_fraction', 'mid_fraction', 'high_fraction', 'attack_ratio', 'tail_ratio', 'stereo_side_fraction')
    parts = {k: near(f[k], target, width) for k, target, width in zip(keys, targets, widths)}
    weights = (.23, .20, .12, .18, .17, .10)
    score = sum(parts[k] * w for k, w in zip(keys, weights))
    return {'score': round(score, 6), 'components': {k: round(v, 6) for k, v in parts.items()},
            'method': 'fixed role-feature proximity; not a perceptual quality rating'}


def _validate_runtime_features(features):
    if type(features) is not dict:
        raise ValidationError('missing runtime audio features')
    for key in ('peak', 'rms', 'pitch_distance_semitones'):
        value = features.get(key)
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValidationError('invalid runtime audio features')
    if not .0001 <= features['peak'] < 1 or not .00001 <= features['rms'] <= features['peak']:
        raise ValidationError('silent, clipped, or inconsistent runtime audio')
    if not 0 <= features['pitch_distance_semitones'] <= 2:
        raise ValidationError('gross runtime pitch mismatch')


def _plugin_info(plugin):
    plugin = _no_symlinks(plugin)
    if plugin.suffix != '.vst3' or not plugin.is_dir():
        raise ValidationError('an installed Vitalium .vst3 directory is required')
    module = plugin / 'Contents/x86_64-linux/vitalium.so'
    data = _bounded_read(module, 64 * 1024 * 1024)
    digest = _sha(data)
    if digest not in PINNED_MODULES:
        raise ValidationError('Vitalium module is not one of the pinned reviewed builds')
    if any(p.is_symlink() for p in plugin.rglob('*')):
        raise ValidationError('plugin bundle symlinks are unsupported')
    if not shutil.which('bwrap'):
        raise ValidationError('runtime audition requires installed bubblewrap')
    return {'path': str(plugin), 'module_sha256': digest, 'expected_version': '1.0.6',
            'backend': 'isolated-pedalboard-vst3', 'isolation': 'read-only filesystem except private scratch; network namespace disabled'}


def _audition(plugin, plugin_info, data, role, work, timeout, intent):
    """Run one plugin load and render in its own network-isolated process."""
    work.mkdir(mode=0o700)
    (work / 'input.vital').write_bytes(data)
    pythonpath = os.pathsep.join(dict.fromkeys([str(Path(__file__).resolve().parent.parent)] + [str(Path(x).resolve()) for x in sys.path if x]))
    env = {'PATH': '/usr/bin:/bin', 'PYTHONPATH': pythonpath, 'HOME': str(work), 'TMPDIR': str(work),
           'XDG_CONFIG_HOME': str(work / 'config'), 'XDG_CACHE_HOME': str(work / 'cache'),
           'XDG_DATA_HOME': str(work / 'data'), 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
    cmd = [shutil.which('bwrap'), '--die-with-parent', '--unshare-net', '--ro-bind', '/', '/',
           '--bind', str(work), str(work), '--chdir', str(work), '--clearenv']
    for key, value in env.items():
        cmd.extend(('--setenv', key, value))
    cmd.extend((sys.executable, '-m', 'kuang._palette_worker', '--plugin', str(plugin), '--plugin-sha',
                plugin_info['module_sha256'], '--source-sha', _sha(data), '--role', role, '--tonic', str(intent['tonic']), '--mode', intent['mode'], '--work', str(work)))
    try:
        done = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return {'status': 'rejected', 'reason': 'worker timeout'}
    if done.returncode != 0:
        return {'status': 'rejected', 'reason': f'worker failed or crashed (exit {done.returncode})'}
    try:
        result = _json_bytes(_bounded_read(work / 'result.json', 65536), 'worker result')
    except ValidationError:
        return {'status': 'rejected', 'reason': 'missing or invalid worker result'}
    return result


def _validate_preview(path):
    data = _bounded_read(path, 4 * 48000 * 6 + 4096)
    try:
        with wave.open(io.BytesIO(data), 'rb') as f:
            if (f.getframerate(), f.getnchannels(), f.getsampwidth(), f.getcomptype()) != (48000, 2, 3, 'NONE'):
                raise ValidationError('preview must be 48 kHz 24-bit stereo PCM')
            frames = f.getnframes()
            if not 0 < frames <= 4 * 48000:
                raise ValidationError('invalid preview duration')
            audio = f.readframes(frames)
            if len(audio) != frames * 6:
                raise ValidationError('truncated preview')
            peak = max(abs(int.from_bytes(audio[i:i+3], 'little', signed=True)) for i in range(0, len(audio), 3))
            if peak < 839 or peak >= 2**23 - 1:
                raise ValidationError('preview is silent or clipped')
    except (OSError, wave.Error, EOFError) as exc:
        raise ValidationError('missing or malformed preview') from exc
    return _sha(data), data


def _catalog_sources(catalog):
    rows = catalog.get('sources')
    if type(rows) is not list or not 1 <= len(rows) <= MAX_SOURCE_ARCHIVES:
        raise ValidationError('catalog must name bounded source archives')
    result = {}
    for row in rows:
        if type(row) is not dict:
            raise ValidationError('invalid source archive metadata')
        name, digest, size = row.get('filename'), row.get('sha256'), row.get('size_bytes')
        if (type(name) is not str or len(name) > 255 or any(ord(c) < 32 for c in name) or '/' in name or '\\' in name or name in ('', '.', '..') or
                type(digest) is not str or not SHA.fullmatch(digest) or type(size) is not int or size <= 0):
            raise ValidationError('invalid source archive metadata')
        suffix = next((x for x in ('.7z', '.vitalbank') if name.endswith(x)), None)
        if not suffix or name[:-len(suffix)] in result:
            raise ValidationError('unsupported or duplicate source archive')
        result[name[:-len(suffix)]] = {'filename': name, 'catalog_sha256': digest, 'catalog_size_bytes': size,
                                       'archive_content_verified': False}
    return result


def select_palette(prompt, catalog, plugin, out_dir, *, seed=17, per_role=3, max_candidates=12, timeout=15, renderer=None):
    """Select a private palette; an injected renderer is for offline tests only."""
    check_prompt(prompt)
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValidationError('seed must be a 32-bit unsigned integer')
    if type(per_role) is not int or not 1 <= per_role <= 5:
        raise ValidationError('per-role must be 1..5')
    if type(max_candidates) is not int or not 1 <= max_candidates <= 30:
        raise ValidationError('max-candidates must be 1..30')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 1 <= timeout <= 60:
        raise ValidationError('timeout must be 1..60 seconds')
    catalog = _no_symlinks(catalog)
    library = _no_symlinks(catalog.parent.parent)
    preset_root = _no_symlinks(library / 'presets')
    if not preset_root.is_dir():
        raise ValidationError('library presets directory is missing')
    catalog_bytes = _bounded_read(catalog, MAX_CATALOG_BYTES)
    catalog_sha256 = _sha(catalog_bytes)
    catalog_data = _json_bytes(catalog_bytes, 'catalog')
    rows = catalog_data.get('presets')
    if catalog_data.get('catalog_version') != 1 or type(rows) is not list or len(rows) > MAX_ROWS:
        raise ValidationError('unsupported or oversized catalog')
    sources = _catalog_sources(catalog_data)
    destination = Path(out_dir).expanduser()
    if destination.is_symlink() or destination.exists():
        raise ValidationError('output already exists; choose a new directory')
    parent = _no_symlinks(destination.parent)
    if not parent.is_dir():
        raise ValidationError('output parent directory must already exist')
    destination = parent / destination.name
    if destination.is_relative_to(library):
        raise ValidationError('output must be outside the source library')
    info = _plugin_info(plugin) if renderer is None else {'backend': 'injected-test-renderer', 'runtime_verified': False}
    intent = _intent(prompt)
    pools = {r: _role_candidates(rows, r, intent, seed) for r in intent['roles']}
    counters = {r: 0 for r in intent['roles']}
    accepted = {r: [] for r in intent['roles']}
    decisions = []
    attempts = preflights = 0
    preflight_limit = min(MAX_ROWS, max_candidates * 12)
    with tempfile.TemporaryDirectory(prefix='.palette-stage-', dir=parent) as temp:
        stage = Path(temp); (stage / 'previews').mkdir(mode=0o700)
        exhausted = set()
        while attempts < max_candidates and preflights < preflight_limit and len(exhausted) < len(intent['roles']):
            progressed = False
            for role in intent['roles']:
                if attempts >= max_candidates or preflights >= preflight_limit:
                    break
                if len(accepted[role]) >= per_role or counters[role] >= len(pools[role]):
                    exhausted.add(role)
                    continue
                semantic, _, row = pools[role][counters[role]]; counters[role] += 1; preflights += 1; progressed = True
                entry = {'role': role, 'path': row.get('path'), 'catalog_sha256': row.get('sha256'),
                         'catalog_size': row.get('size'), 'catalog_version': row.get('synth_version'),
                         'semantic_score': semantic, 'status': 'rejected'}
                try:
                    parts = _relative_parts(row.get('path'))
                    if parts[0] not in sources:
                        raise ValidationError('preset has no catalogued source archive')
                    entry['source_archive'] = sources[parts[0]]
                    data = _read_preset(preset_root, row.get('path'), row.get('size'), row.get('sha256'))
                    patch = _validate_patch(data, row)
                    entry.update({'source_sha256': _sha(data), 'source_preset_name': patch['preset_name'],
                                  'source_author': patch.get('author'), 'license': 'unknown; private use only'})
                except (ValidationError, OSError, TypeError, AttributeError) as exc:
                    entry['reason'] = str(exc)[:300]; decisions.append(entry); continue
                attempts += 1
                work = stage / ('worker-' + str(attempts))
                try:
                    result = _audition(info['path'], info, data, role, work, timeout, intent) if renderer is None else renderer(data, role, work)
                    if type(result) is not dict or result.get('status') != 'accepted':
                        entry['reason'] = str(result.get('reason', 'invalid renderer result') if type(result) is dict else 'invalid renderer result')[:300]
                        decisions.append(entry); continue
                    features = result.get('features')
                    _validate_runtime_features(features)
                    proxy = score_features(role, features)
                    preview = work / 'preview.wav'
                    preview_hash, preview_data = _validate_preview(preview)
                    dest = stage / 'previews' / f'{role}-{attempts:02d}.wav'
                    with dest.open('xb') as published:
                        published.write(preview_data)
                    entry.update({'status': 'accepted', 'runtime_verified': renderer is None,
                                  'runtime': result.get('runtime', {}), 'features': features,
                                  'quality_proxy': proxy, 'combined_score': round(.35 * semantic + .65 * proxy['score'], 6),
                                  'preview': str(dest.relative_to(stage)), 'preview_sha256': preview_hash})
                    accepted[role].append(entry)
                except (ValidationError, OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
                    entry['reason'] = str(exc)[:300]
                decisions.append(entry)
            if not progressed:
                break
        # Source references are published only if their bytes still match after audition.
        selected = {}
        for role, entries in accepted.items():
            ranked = sorted(entries, key=lambda e: (e['combined_score'], e['semantic_score'],
                            _sha(f"{seed}\0{role}\0{e['path']}".encode('utf-8'))), reverse=True)
            for entry in ranked:
                try:
                    _read_preset(preset_root, entry['path'], entry['catalog_size'], entry['source_sha256'])
                except ValidationError:
                    entry['status'] = 'rejected'; entry['reason'] = 'source drift after audition'
                    (stage / entry['preview']).unlink(missing_ok=True)
                    continue
                selected[role] = entry
                break
        if renderer is None and _plugin_info(plugin)['module_sha256'] != info['module_sha256']:
            raise ValidationError('plugin changed during audition')
        complete = len(selected) == len(intent['roles'])
        selection = {'version': 'autonomous-palette-selection-1', 'prompt': prompt, 'seed': seed,
                     'status': 'complete' if complete else 'incomplete', 'roles': selected,
                     'catalog_sha256': catalog_sha256, 'catalog_path': str(catalog), 'library_root': str(library),
                     'preset_root': str(preset_root), 'plugin': info,
                     'usage': 'Private local source references only; not an external_synth binding or a rendered song.',
                     'quality': 'heuristic proxy; human listening and subjective quality unverified'}
        decision = {'version': 'autonomous-palette-decision-1', 'prompt': prompt, 'seed': seed,
                    'intent': intent, 'catalog_sha256': catalog_sha256, 'library_root': str(library),
                    'plugin': info, 'max_candidates': max_candidates, 'auditions': attempts,
                    'preflights': preflights, 'preflight_limit': preflight_limit,
                    'per_role': per_role, 'decisions': decisions, 'status': selection['status'],
                    'limitations': ['Foreign preset licensing is unaudited; do not redistribute.',
                                    'Candidate scores are deterministic for given features, but plugin renders may vary; no listening or studio-quality judgment.',
                                    'No native DAW binding or complete song is produced.',
                                    'Preset hashes are verified; archive hashes are catalog metadata and do not prove provenance or authenticity.']}
        for name, value in (('selection.json', selection), ('decision.json', decision)):
            (stage / name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        # Workers and staged source files never enter published output.
        for child in stage.glob('worker-*'):
            shutil.rmtree(child)
        try:
            destination.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise ValidationError('output already exists; choose a new directory') from exc
        try:
            for child in stage.iterdir():
                child.rename(destination / child.name)
        except BaseException:
            shutil.rmtree(destination)
            raise
    return {'status': selection['status'], 'output': str(destination), 'selection': str(destination / 'selection.json'),
            'decision': str(destination / 'decision.json'), 'roles': {r: e['source_preset_name'] for r, e in selected.items()},
            'auditions': attempts, 'preflights': preflights}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prompt'); parser.add_argument('--catalog', required=True); parser.add_argument('--plugin', required=True)
    parser.add_argument('--out-dir', required=True); parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--per-role', type=int, default=3); parser.add_argument('--max-candidates', type=int, default=12)
    parser.add_argument('--timeout', type=float, default=15)
    args = parser.parse_args(argv)
    try:
        result = select_palette(args.prompt, args.catalog, args.plugin, args.out_dir, seed=args.seed,
                                per_role=args.per_role, max_candidates=args.max_candidates, timeout=args.timeout)
    except (ValidationError, OSError) as exc:
        print(f'autonomous-palette: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
