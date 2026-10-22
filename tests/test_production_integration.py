"""Real native production checks. No host, plugin or asset is downloaded."""

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.audio import compare_wavs
from kuang.composer import compose
from kuang.create import create
from kuang.production import refine_house
from kuang.schema import AutomationPoint, dumps, load, state_hash
from kuang.song import rules_plan
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import AddAutomationPoints, Scope, SetParameter, receipt_from_dict, replay


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


@unittest.skipUnless(os.environ.get('KUANG_SOUNDCRAFT_INTEGRATION') == '1', 'opt in to installed SoundCraft production tests')
class ProductionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        selected = os.environ.get('KUANG_SOUNDCRAFT_ARTIFACTS')
        cls.temp = tempfile.TemporaryDirectory() if not selected else None
        cls.root = Path(selected+'-phase4' if selected else cls.temp.name)
        if cls.root.exists() and any(cls.root.iterdir()):
            raise RuntimeError('Phase 4 artifact directory must be new or empty')
        cls.root.mkdir(parents=True, exist_ok=True)
        cls.adapter = SoundCraftAdapter(timeout=120)
        cls.results = {}

    @classmethod
    def tearDownClass(cls):
        (cls.root/'verification.json').write_text(json.dumps(cls.results, indent=2, sort_keys=True)+'\n')
        if cls.temp:
            cls.temp.cleanup()

    def assert_notes_fx_lanes(self, p, native):
        # Independent note fields, chain order, important DSP units, automation
        # addresses and values. Adapter verification is an additional check.
        for t, h in zip(p.tracks, native['tracks']):
            actual = [(n['start'], n['length'], n['pitch'], n['velocity'], n['channel'])
                      for c in h['playlists'][0]['clips'] for n in c['content']['Midi']['sequence']['notes']]
            expected = [(c.start+n.start, n.duration, n.pitch, n.velocity, n.channel) for c in t.clips for n in c.notes]
            self.assertEqual(Counter(actual), Counter(expected))
            inserts = [x for x in h['mixer']['inserts'] if x is not None]
            self.assertEqual([x['plugin'] for x in inserts], [e.plugin_ref.split(':')[1] for e in t.effects])
            if t.id == 'track-bass':
                self.assertEqual(h['instrument']['params']['osc1_wave'], 2)
                self.assertEqual(h['instrument']['params']['filter_env_amount'], 20)
                self.assertEqual(h['instrument']['params']['filter_decay'], 180)
                self.assertEqual(inserts[2]['params']['threshold'], -25)
            for fx, host in zip(t.effects, inserts):
                if fx.plugin_ref == 'soundcraft:plate_reverb':
                    self.assertAlmostEqual(host['params']['decay'], fx.parameters['soundcraft.decay_ms']/1000, places=6)
            self.assertEqual(h['mixer']['automation_mode'], 'Read')
            for lane in (a for a in p.automation if a.target_id in {t.id, *(e.id for e in t.effects)}):
                if lane.target_id == t.id:
                    params = ['Volume'] if lane.parameter_id == 'mixer.gain_db' else [{'Pan': 0}, {'Pan': 1}]
                    factor = 1
                else:
                    slot = next(i for i, fx in enumerate(t.effects) if fx.id == lane.target_id)
                    params = [{'Plugin': {'slot': slot, 'param': 'mix' if lane.parameter_id == 'effect.wet' else 'lpf_freq'}}]
                    factor = 100 if lane.parameter_id == 'effect.wet' else 1
                for param in params:
                    host_lane = next(a for a in h['automation'] if a['param'] == param)
                    self.assertTrue(host_lane['enabled'])
                    self.assertEqual([a['at'] for a in host_lane['points']], [round(a.tick*48000*60/(960*p.tempo_bpm)) for a in lane.points])
                    for actual, expected in zip(host_lane['points'], lane.points):
                        self.assertAlmostEqual(actual['value'], expected.value*factor, delta=2e-4)

    def test_two_refined_house_variants_full_native_reopen_render_and_direct_instrument_edit(self):
        results = []
        for i, prompt in enumerate(('uplifting house, 126 bpm, C major, 16 bars', 'dark house, 122 bpm, D minor, 8 bars')):
            out = self.root/f'house-{i}'
            report = create(prompt, out, production='refined', seed=29+i, soundcraft=str(self.adapter.executable), render=True)
            original = inventory(out)
            p = load(out/'project.kuang.json')
            native = self.adapter.inspect(out/'native')['native']
            self.assert_notes_fx_lanes(p, native)
            clone = self.root/f'house-{i}-saved'
            self.adapter.save(out/'native', clone)
            self.assertEqual(self.adapter.inspect(clone)['native'], native)
            self.assertEqual(dumps(self.adapter.import_project(clone)), dumps(p))
            a = report['render']['analysis']
            self.assertGreater(a['rms'], 1e-6)
            self.assertLess(a['peak'], 1)
            self.assertEqual(a['clipped_samples'], 0)
            self.assertEqual((a['sample_rate'], a['channels'], a['bits_per_sample']), (48000, 2, 24))
            # A real host-side single instrument parameter edit, with exact
            # equality of every other persistent field and another save/reopen.
            changed = self.root/f'direct-instrument-{i}'
            changed.mkdir()
            target = next(t for t in native['tracks'] if t['name'] == 'Envelope bass')['id']
            result = subprocess.run([str(self.adapter.executable), 'run', '--in', str(out/'native/session.scraft'),
                '--cmd', 'mix.instrument_param='+json.dumps({'track':target,'param':'filter_decay','value':220}),
                '--save', str(changed/'session.scraft')], capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = deepcopy(native)
            next(t for t in expected['tracks'] if t['id'] == target)['instrument']['params']['filter_decay'] = 220
            self.assertEqual(json.loads((changed/'session.scraft').read_text()), expected)
            reopened = self.adapter._reopen(changed/'session.scraft', changed)
            self.assertEqual(json.loads(reopened.read_text()), expected)
            self.assertEqual(inventory(out), original)
            results.append(report)
        self.results['roundtrips'] = results

    def test_automation_changes_audio_and_scoped_fx_lane_edit_preserves_all_other_state(self):
        spec, _ = rules_plan('house, 126 bpm, C major, 8 bars', 29)
        p = refine_house(spec, compose(spec))
        on, off = self.root/'automation-on', self.root/'automation-off'
        self.adapter.export(p, on)
        before = inventory(on)
        dry = deepcopy(p)
        dry.automation = []
        self.adapter.export(dry, off)
        a = self.adapter.render(on, self.root/'automation-on.wav')
        b = self.adapter.render(off, self.root/'automation-off.wav')
        delta = compare_wavs(a['output'], b['output'])
        self.assertTrue(delta['measurable_change'])
        for r in (a, b):
            self.assertEqual(r['analysis']['clipped_samples'], 0)
            self.assertGreater(r['analysis']['rms'], 1e-6)
        self.assertEqual(inventory(on), before)
        ops = [SetParameter('set_parameter','effect-bass-compression','soundcraft.threshold',-28),
               SetParameter('set_parameter','effect-harmony-chorus','soundcraft.rate',.6),
               AddAutomationPoints('add_automation_points','production-lead-throw',
                                   [AutomationPoint('phase4-throw-edit',240,.23,'linear')])]
        scope = Scope(['track-bass','track-harmony','track-lead'], [],
                      ['soundcraft.threshold','soundcraft.rate','effect.wet'], None, None)
        edited = self.root/'fx-edited'
        self.adapter.apply(on, edited, ops, scope, state_hash(p))
        receipt = receipt_from_dict(json.loads((edited/'receipt.json').read_text()))
        q = self.adapter.import_project(edited)
        self.assertEqual(dumps(replay(q, receipt, undo=True)), dumps(p))
        self.assertEqual(dumps(replay(p, receipt, undo=False)), dumps(q))
        old = self.adapter.inspect(on)['native']
        new = self.adapter.inspect(edited)['native']
        expected = deepcopy(old)
        expected['tracks'][3]['mixer']['inserts'][2]['params']['threshold'] = -28
        expected['tracks'][4]['mixer']['inserts'][2]['params']['rate'] = new['tracks'][4]['mixer']['inserts'][2]['params']['rate']
        self.assertAlmostEqual(expected['tracks'][4]['mixer']['inserts'][2]['params']['rate'],.6,places=6)
        lane = next(a for a in expected['tracks'][6]['automation'] if a['param'] == {'Plugin':{'slot':1,'param':'mix'}})
        lane['points'].append({'at':round(240*48000*60/(960*126)), 'value':23})
        lane['points'].sort(key=lambda x:x['at'])
        self.assertEqual(new, expected)
        self.adapter.save(edited, self.root/'fx-edited-saved')
        self.assertEqual(self.adapter.inspect(self.root/'fx-edited-saved')['native'], new)
        self.assertEqual(inventory(on), before)
        self.results['automation'] = {'delta':delta,'renders':[a,b], 'source_unchanged':True, 'scoped_native_equality':True}
