#!/usr/bin/env python3
"""Bounded native send/aux proof, separate from the production adapter/ABCD.

Writes host state exclusively through discovered commands. This is a probe,
not a general canonical bus importer, reconciler or production routing API.
"""
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kuang.audio import compare_wavs
from kuang.gestures import crop
from kuang.pocket_production import baseline
from kuang.production_audio import production_metrics
from kuang.schema import Send, Track, ValidationError, save, state_hash, validate
from kuang.soundcraft import SoundCraftAdapter
from tools.phase5_house import checked_audio, write
from tools.phase7_house import local

COMMANDS = ('mix.new_bus', 'track.new', 'track.input', 'track.output', 'mix.volume',
            'mix.pan', 'mix.insert', 'mix.send', 'mix.send_level', 'file.bounce_mix')


def probe(destination, executable=None):
    dest = local(destination)
    if not dest.is_relative_to(ROOT/'.local/phase12') or dest.exists():
        raise ValidationError('routing probe requires a new .local/phase12 directory')
    a = SoundCraftAdapter(executable, timeout=120)
    a._discover()  # Exact existing 0.11.0 command/plugin contract pin.
    dest.mkdir(parents=True)
    q = crop(baseline(), 0, 2, ['track-snare'])
    source = q.tracks[0]
    room = deepcopy(source.effects[-1])
    room.id = 'phase12-room-effect'
    room.parameters.update({'effect.wet': 1, 'soundcraft.decay_ms': 800})
    source.effects = []
    source.controls.update({'mixer.gain_db': -12, 'mixer.pan': 0})
    q.automation = []
    p = deepcopy(q)
    p.tracks[0].sends = [Send('phase12-post-send', 'phase12-room-return', -9, 0, 'post_fader')]
    p.tracks.append(Track('phase12-room-return', 'Phase12 room return', 'bus', None,
        {'mixer.gain_db': -6, 'mixer.pan': 0, 'mixer.mute': 0}, [room], [], [], True))
    validate(p)
    save(p, dest/'prototype.kuang.json')
    a.export(q, dest/'dry')
    native_dry = a.inspect(dest/'dry')['native']

    def run(src, folder, commands):
        folder.mkdir()
        for cmd, _ in commands:
            if cmd not in COMMANDS:
                raise ValidationError('unreviewed routing command')
            d = json.loads(a._call(['describe', cmd], dest))
            if d['id'] != cmd or type(d.get('params')) is not str:
                raise ValidationError('missing native routing command')
        argv = ['run', '--in', str(src)]
        for cmd, value in commands:
            argv += ['--cmd', cmd+'='+json.dumps(value, separators=(',', ':'), allow_nan=False)]
        path = folder/'session.scraft'
        argv += ['--save', str(path)]
        result = a._call(argv, dest)
        (folder/'command-results.txt').write_text(result)
        return json.loads(path.read_text())

    params = dict(a._parameter(p, room, 'room_reverb', key, value)
                  for key, value in room.parameters.items() if key != 'effect.bypass')
    bus = 'Phase12 room bus'
    name = p.tracks[-1].name
    commands = [('mix.new_bus', {'name': bus, 'format': 'stereo'}),
        ('track.new', {'name': name, 'kind': 'aux', 'format': 'stereo'}),
        ('track.input', {'tracks': name, 'input': bus}),
        ('track.output', {'tracks': name, 'output': 'main'}),
        ('mix.volume', {'tracks': name, 'db': -6}),
        ('mix.pan', {'tracks': name, 'index': 0, 'pan': 0}),
        ('mix.pan', {'tracks': name, 'index': 1, 'pan': 0}),
        ('mix.insert', {'track': name, 'slot': 0, 'plugin': 'room_reverb', 'params': params}),
        ('mix.send', {'track': source.name, 'slot': 0, 'bus': bus, 'level_db': -9, 'pre_fader': False})]
    native = run(dest/'dry/session.scraft', dest/'routed', commands)
    reopened = run(dest/'routed/session.scraft', dest/'reopened', [])
    if native != reopened:
        raise ValidationError('routed full native state did not persist')
    # Compare all original native fields; only its declared send may change.
    expected = deepcopy(native_dry)
    expected['tracks'][0]['mixer']['sends'] = native['tracks'][0]['mixer']['sends']
    expected['tracks'].append(native['tracks'][-1])
    for field in ('busses', 'next_id'):
        expected[field] = native[field]
    # track.new selects the newly created aux; preserve every other UI field.
    expected['edit']['selected_tracks'] = [native['tracks'][-1]['id']]
    if expected != native:
        raise ValidationError('routing probe changed unrelated native state')
    bus_id = native['busses'][0]['id']
    send = native['tracks'][0]['mixer']['sends'][0]
    ret = native['tracks'][-1]
    if (send['target'], send['level_db'], send['pre_fader'], ret['kind'], ret['mixer']['input'],
            ret['mixer']['output'], ret['mixer']['volume_db'], ret['mixer']['pan']) != (
            {'Bus': bus_id}, -9, False, 'Aux', {'Bus': bus_id}, 'Main', -6, [0, 0]):
        raise ValidationError('native routing addresses do not match the prototype')
    for key, value in params.items():
        if abs(ret['mixer']['inserts'][0]['params'][key]-value) > .001:
            raise ValidationError('return FX control did not persist')
    off = run(dest/'routed/session.scraft', dest/'send-off',
              [('mix.send_level', {'track': source.name, 'slot': 0, 'mute': True})])
    expected_off = deepcopy(native)
    expected_off['tracks'][0]['mixer']['sends'][0]['mute'] = True
    if off != expected_off:
        raise ValidationError('send mute changed other native fields')
    duration = 2*4*60/126+4
    for label, folder in [('dry', 'dry'), ('wet', 'routed'), ('repeat', 'reopened'), ('off', 'send-off')]:
        run(dest/folder/'session.scraft', dest/('bounce-'+label), [('file.bounce_mix', {
            'path': str(dest/(label+'.wav')), 'format': 'wav', 'bit_depth': 24, 'dither': False,
            'start': {'seconds': 0}, 'end': {'seconds': duration}})])
        checked_audio(dest/(label+'.wav'))
    if (dest/'wet.wav').read_bytes() != (dest/'repeat.wav').read_bytes():
        raise ValidationError('reopened send rendering changed PCM')
    if (dest/'dry.wav').read_bytes() != (dest/'off.wav').read_bytes():
        raise ValidationError('muted send is not an exact dry control')
    delta = compare_wavs(dest/'dry.wav', dest/'wet.wav')
    if not delta['measurable_change'] or delta['difference_to_original_rms_ratio'] < .01:
        raise ValidationError('native send has no substantial PCM effect')
    last_onset = max(c.start+n.start for c in source.clips for n in c.notes)*60/(126*960)
    report = {'host_native_send_aux_proven': True, 'canonical_prototype_hash': state_hash(p),
        'full_native_reopen_equal': True, 'reopened_PCM_exact': True,
        'send_off_dry_PCM_exact': True, 'source_native_outside_send_unchanged': True,
        'difference': delta, 'commands': commands,
        'tail': {key: production_metrics(dest/(key+'.wav'), [('after_notes', last_onset+.45, last_onset+.95)])['sections']
                 for key in ('dry', 'wet')},
        'production_adapter_support': a.capabilities(p),
        'production_bus_used': False,
        'limit': 'Bounded static post-fader send/aux prototype only. General canonical routing, locks, native transactions and send automation are not mapped; production adapter continues to reject them.'}
    write(dest/'verification.json', report)
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--soundcraft')
    args = parser.parse_args()
    print(json.dumps(probe(args.out_dir, args.soundcraft), indent=2))
