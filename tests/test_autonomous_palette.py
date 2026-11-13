import base64
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
from pathlib import Path

from kuang import autonomous_palette as palette
from kuang.schema import ValidationError


def preset(name, version='1.0.5', sample_on=0):
    frame = base64.b64encode(bytes(8192)).decode('ascii')
    wave_source = {'groups': [{'components': [{'type': 'Wave Source', 'keyframes': [{'wave_data': frame}]}]}]}
    return {'preset_name': name, 'author': 'test', 'synth_version': version,
            'settings': {'sample_on': sample_on, 'sample': {'length': 0, 'samples': ''},
                         'wavetables': [wave_source, wave_source, wave_source]}}


def features(role):
    bands = {'bass': (.75, .22, .03), 'chord': (.12, .70, .18), 'pad': (.10, .65, .25)}[role]
    return {'low_fraction': bands[0], 'mid_fraction': bands[1], 'high_fraction': bands[2],
            'attack_ratio': .5, 'tail_ratio': .25, 'stereo_side_fraction': .1, 'crest_db': 10.,
            'peak': .2, 'rms': .05, 'pitch_distance_semitones': .1}


class FakeRenderer:
    def __init__(self, reject=False):
        self.calls = []
        self.reject = reject

    def __call__(self, data, role, work):
        self.calls.append((role, hashlib.sha256(data).hexdigest()))
        work.mkdir(mode=0o700)
        if self.reject:
            return {'status': 'rejected', 'reason': 'simulated crash'}
        with wave.open(str(work / 'preview.wav'), 'wb') as f:
            f.setnchannels(2); f.setsampwidth(3); f.setframerate(48000); f.writeframes((500000).to_bytes(3, 'little', signed=True) * 480 * 2)
        return {'status': 'accepted', 'features': features(role), 'runtime': {'fixture': True}}


class PaletteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.library = self.root / 'library'
        self.presets = self.library / 'presets'
        self.reports = self.library / 'reports'
        self.presets.mkdir(parents=True); self.reports.mkdir()
        self.catalog = self.reports / 'catalog.json'
        self.rows = []
        for role, style in [('chord', 'Keys'), ('pad', 'Pad'), ('bass', 'Bass')]:
            for i in range(4):
                name = f'{role} warm {i}'
                data = json.dumps(preset(name)).encode()
                path = f'{role}/{i}.vital'; file = self.presets / path
                file.parent.mkdir(exist_ok=True); file.write_bytes(data)
                self.rows.append({'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data),
                                  'synth_version': '1.0.5', 'preset_name': name, 'preset_style': style,
                                  'compatibility': 'version_candidate', 'license': 'unknown'})
        self.write_catalog()

    def tearDown(self):
        self.tmp.cleanup()

    def write_catalog(self):
        self.catalog.write_text(json.dumps({'catalog_version': 1, 'root': '/untrusted/ignored', 'presets': self.rows, 'sources': [{'filename': name + '.7z', 'sha256': '1' * 64, 'size_bytes': 1} for name in ('chord','pad','bass')]}))

    def run_selection(self, name, renderer=None, **kwargs):
        renderer = renderer or FakeRenderer()
        result = palette.select_palette('warm deep house in C minor, warm chords, soft pad, bass', self.catalog,
                                        None, self.root / name, renderer=renderer, **kwargs)
        return result, renderer

    def test_determinism_and_private_output(self):
        a, ra = self.run_selection('one', seed=17, per_role=2, max_candidates=8)
        b, rb = self.run_selection('two', seed=17, per_role=2, max_candidates=8)
        self.assertEqual(a['status'], 'complete'); self.assertEqual(a['roles'], b['roles']); self.assertEqual(ra.calls, rb.calls)
        selected = json.loads(Path(a['selection']).read_text())
        self.assertFalse(selected['roles']['bass']['runtime_verified'])
        self.assertEqual(selected['plugin']['backend'], 'injected-test-renderer')
        self.assertEqual(selected['catalog_sha256'], hashlib.sha256(self.catalog.read_bytes()).hexdigest())
        self.assertEqual(json.loads(Path(a['decision']).read_text())['catalog_sha256'], selected['catalog_sha256'])
        self.assertEqual(set(selected['roles']), {'chord', 'pad', 'bass'})
        self.assertFalse(list((self.root / 'one').rglob('*.vital')))
        self.assertEqual(len(list((self.root / 'one' / 'previews').glob('*.wav'))), 6)
        self.assertEqual(json.loads(Path(a['decision']).read_text())['intent']['mode'], 'minor')

    def test_semantic_relevance_and_key(self):
        x = palette._intent('funky house in F# major, bright chord stabs, soft pad, deep bass')
        self.assertEqual((x['tonic'], x['mode']), (6, 'major'))
        warm = {'preset_name': 'Warm Stab', 'path': 'keys/warm_stab.vital'}
        cold = {'preset_name': 'Bell', 'path': 'keys/bell.vital'}
        intent = palette._intent('deep house, warm chord stabs, dark pad, rounded bass')
        self.assertGreater(palette._semantic_score(warm, 'chord', intent), palette._semantic_score(cold, 'chord', intent))
        self.assertNotIn('pad', palette._intent('house without pad')['roles'])
        with self.assertRaises(ValidationError): palette._intent('C minor and D major house')

    def test_integrated_audition_uses_validated_composition_key(self):
        from kuang.song import rules_plan
        spec, _ = rules_plan('warm house, bass, chords and pad', seed=17)
        self.assertEqual((spec.tonic, spec.mode), (0, 'major'))
        self.assertEqual((palette._intent('warm house, bass, chords and pad')['tonic'],
                          palette._intent('warm house, bass, chords and pad')['mode']), (0, 'major'))
        result = palette.select_palette('warm house, bass, chords and pad', self.catalog,
                                        None, self.root/'major-spec', renderer=FakeRenderer(),
                                        seed=17, per_role=1, max_candidates=5, musical_spec=spec)
        self.assertEqual(result['status'], 'complete')
        evidence = json.loads((self.root/'major-spec/decision.json').read_text())
        self.assertEqual((evidence['intent']['tonic'], evidence['intent']['mode']), (0, 'major'))
        self.assertEqual(evidence['intent']['key_source'], 'validated SongSpec')
        with self.assertRaisesRegex(ValidationError, 'explicit audition key conflicts'):
            self.run_selection('contradictory', seed=17, per_role=1, max_candidates=5, musical_spec=spec)
        self.assertFalse((self.root/'contradictory').exists())

    def test_scoring_is_gain_independent_and_role_sensitive(self):
        a = features('bass'); b = dict(a, rms=.005, peak=.02)
        self.assertEqual(palette.score_features('bass', a), palette.score_features('bass', b))
        self.assertGreater(palette.score_features('bass', a)['score'], palette.score_features('chord', a)['score'])
        with self.assertRaises(ValidationError): palette.score_features('bass', dict(a, low_fraction=float('nan')))

    def test_wrong_hash_and_version_fail_closed(self):
        row = self.rows[0].copy(); row['sha256'] = '0' * 64
        with self.assertRaises(ValidationError): palette._read_preset(self.presets, row['path'], row['size'], row['sha256'])
        data = json.dumps(preset('future', version='1.5.0')).encode()
        with self.assertRaises(ValidationError): palette._validate_patch(data, {'synth_version': '1.5.0', 'compatibility': 'version_candidate'})
        data = json.dumps(preset('sample', sample_on=1)).encode()
        with self.assertRaises(ValidationError): palette._validate_patch(data, {'synth_version': '1.0.5', 'compatibility': 'version_candidate'})

    def test_confined_paths_and_symlinks(self):
        target = self.presets / self.rows[0]['path']
        (self.presets / 'escape').symlink_to(target.parent, target_is_directory=True)
        row = self.rows[0]
        for path in ('../outside.vital', '/etc/passwd.vital', 'escape/0.vital', 'chord/../0.vital', 'chord\\0.vital'):
            with self.subTest(path=path), self.assertRaises(ValidationError):
                palette._read_preset(self.presets, path, row['size'], row['sha256'])

    def test_missing_and_no_candidates(self):
        self.rows = []; self.write_catalog()
        result, render = self.run_selection('empty')
        self.assertEqual(result['status'], 'incomplete'); self.assertEqual(render.calls, [])
        self.assertEqual(json.loads(Path(result['selection']).read_text())['roles'], {})
        self.presets.rename(self.root / 'gone')
        with self.assertRaises(ValidationError): self.run_selection('missing')

    def test_no_overwrite(self):
        (self.root / 'exists').mkdir(); (self.root / 'exists' / 'keep').write_text('safe')
        render = FakeRenderer()
        with self.assertRaises(ValidationError): self.run_selection('exists', renderer=render)
        self.assertEqual(render.calls, []); self.assertEqual((self.root / 'exists' / 'keep').read_text(), 'safe')

    def test_bounded_auditions_and_preflights(self):
        result, render = self.run_selection('bounded', per_role=3, max_candidates=2)
        decision = json.loads(Path(result['decision']).read_text())
        self.assertEqual(len(render.calls), 2); self.assertEqual(decision['auditions'], 2)
        self.assertLessEqual(decision['preflights'], decision['preflight_limit'])
        self.assertEqual(result['status'], 'incomplete')

    def test_renderer_failures_are_reported(self):
        result, render = self.run_selection('failed', renderer=FakeRenderer(reject=True), max_candidates=3)
        decision = json.loads(Path(result['decision']).read_text())
        self.assertEqual(result['status'], 'incomplete'); self.assertEqual(len(render.calls), 3)
        self.assertTrue(any(d.get('reason') == 'simulated crash' for d in decision['decisions']))

    def test_invalid_untrusted_json(self):
        self.catalog.write_text('{"catalog_version":1,"catalog_version":1,"presets":[]}')
        with self.assertRaises(ValidationError): self.run_selection('duplicate')
        self.catalog.write_text('{"catalog_version":1,"presets":NaN}')
        with self.assertRaises(ValidationError): self.run_selection('nan')
        data = json.dumps(preset('unsafe')).encode(); patch = json.loads(data)
        patch['settings']['wavetables'][0]['groups'][0]['components'][0]['type'] = 'File Source'
        with self.assertRaises(ValidationError):
            palette._validate_patch(json.dumps(patch).encode(), {'compatibility': 'version_candidate', 'synth_version': '1.0.5'})

    def test_silent_preview_and_invalid_audio_features_are_rejected(self):
        class Silent(FakeRenderer):
            def __call__(self, data, role, work):
                work.mkdir(mode=0o700)
                with wave.open(str(work / 'preview.wav'), 'wb') as f:
                    f.setnchannels(2); f.setsampwidth(3); f.setframerate(48000); f.writeframes(bytes(480 * 6))
                return {'status': 'accepted', 'features': features(role)}
        result, _ = self.run_selection('silent', renderer=Silent(), max_candidates=3)
        decision = json.loads(Path(result['decision']).read_text())
        self.assertEqual(result['status'], 'incomplete')
        self.assertTrue(any('silent or clipped' in d.get('reason', '') for d in decision['decisions']))
        for f in (dict(features('bass'), peak=1.), dict(features('bass'), pitch_distance_semitones=2.5),
                  dict(features('bass'), rms=float('inf'))):
            with self.assertRaises(ValidationError): palette._validate_runtime_features(f)

    def test_nonfinite_or_external_resources_rejected(self):
        row = {'compatibility': 'version_candidate', 'synth_version': '1.0.5'}
        value = preset('unsafe'); value['settings']['external_path'] = '/etc/passwd'
        with self.assertRaises(ValidationError): palette._validate_patch(json.dumps(value).encode(), row)
        value = preset('unsafe'); value['settings']['wavetables'][0]['groups'][0]['components'][0]['keyframes'][0]['wave_data'] = base64.b64encode(struct.pack('<f', float('nan')) + bytes(8188)).decode()
        with self.assertRaises(ValidationError): palette._validate_patch(json.dumps(value).encode(), row)

    def test_source_drift_invalidates_selection(self):
        class Drift(FakeRenderer):
            def __call__(self, data, role, work):
                result = super().__call__(data, role, work)
                actual = hashlib.sha256(data).hexdigest()
                row = next(row for row in self_outer.rows if row['sha256'] == actual)
                (self_outer.presets / row['path']).write_bytes(b'changed')
                return result
        self_outer = self
        result, _ = self.run_selection('drift', renderer=Drift(), max_candidates=3, per_role=1)
        self.assertEqual(result['status'], 'incomplete')
        d = json.loads(Path(result['decision']).read_text())
        self.assertTrue(any(item.get('reason') == 'source drift after audition' for item in d['decisions']))

    def test_timeout_is_a_candidate_failure(self):
        work = self.root / 'timeout-work'
        with patch.object(palette.subprocess, 'run', side_effect=subprocess.TimeoutExpired('worker', 1)):
            result = palette._audition('/fake/plugin', {'module_sha256': '0'*64}, b'{}', 'bass', work, 1,
                                       {'tonic': 0, 'mode': 'minor'})
        self.assertEqual(result, {'status': 'rejected', 'reason': 'worker timeout'})

    def test_cli_help_has_no_optional_audio_imports(self):
        done = subprocess.run([sys.executable, '-m', 'kuang.autonomous_palette', '--help'],
                              capture_output=True, text=True, check=False, timeout=10)
        self.assertEqual(done.returncode, 0); self.assertIn('--max-candidates', done.stdout)

    def test_unpinned_plugin_rejected(self):
        plugin = self.root/'fake.vst3'; module = plugin/'Contents/x86_64-linux/vitalium.so'; module.parent.mkdir(parents=True); module.write_bytes(b'not a reviewed plugin')
        with self.assertRaises(ValidationError): palette._plugin_info(plugin)


if __name__ == '__main__':
    unittest.main()
