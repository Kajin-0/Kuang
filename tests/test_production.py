import json
import os
import tempfile
import unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from kuang.composer import SCALES, compose
from kuang.create import create
from kuang.midi import export_bytes
from kuang.production import refine_house
from kuang.schema import (BAR, PPQ, AutomationLane, AutomationPoint, ParameterSpec,
                          ValidationError, dumps, state_hash, validate)
from kuang.song import rules_plan
from kuang.soundcraft import AdapterError, SoundCraftAdapter
from kuang.transactions import (AddAutomationPoints, Engine, SetParameter, Scope, replay)
from soundcraft_fake import CONTRACT


def refined(prompt="house, 126 bpm, C major, 16 bars", seed=29):
    spec, _ = rules_plan(prompt, seed)
    return refine_house(spec, compose(spec))


class ProductionTests(unittest.TestCase):
    def test_sketch_input_and_songspec_provenance_are_unchanged(self):
        spec, _ = rules_plan("house", 29)
        original = compose(spec)
        before = dumps(original)
        project = refine_house(spec, original)
        self.assertEqual(dumps(original), before)
        self.assertEqual(project.version, "0.1")
        self.assertEqual(project.metadata["song_spec"], original.metadata["song_spec"])
        # Original generator fixtures have independent drift coverage as well.
        self.assertEqual(json.loads(project.metadata["song_spec"]), asdict(spec))

    def test_deterministic_notes_midi_and_stable_identifiers_across_seeds(self):
        a, b, other = refined(), refined(), refined(seed=31)
        self.assertEqual(dumps(a), dumps(b))
        self.assertEqual(export_bytes(a), export_bytes(b))
        self.assertNotEqual(dumps(a), dumps(other))
        ids = lambda p: [n.id for t in p.tracks for clip in t.clips for n in clip.notes]
        self.assertEqual(ids(a), ids(other))
        self.assertNotEqual([n.pitch for t in a.tracks for clip in t.clips for n in clip.notes],
                            [n.pitch for t in other.tracks for clip in t.clips for n in clip.notes])

    def test_all_lengths_keys_and_modes_remain_in_meter_and_harmony(self):
        for bars in (8, 16, 32):
            for key in ("C major", "D minor", "F# major"):
                with self.subTest(bars=bars, key=key):
                    p = refined(f"house, {key}, {bars} bars")
                    validate(p)
                    self.assertEqual(p.time_signature, [4, 4])
                    self.assertEqual(sum(s.length for s in p.sections), bars*BAR)
                    allowed = {(p.key_tonic+n) % 12 for n in SCALES[p.key_mode]}
                    for t in p.tracks:
                        for c in t.clips:
                            for n in c.notes:
                                self.assertLessEqual(n.start+n.duration, c.length)
                                if n.channel != 9:
                                    self.assertIn(n.pitch % 12, allowed)

    def test_exact_transposition_of_all_melodic_voices(self):
        a, b = refined(), refined("house, D major, 16 bars")
        for x, y in zip(a.tracks, b.tracks):
            for cx, cy in zip(x.clips, y.clips):
                for nx, ny in zip(cx.notes, cy.notes):
                    self.assertEqual(ny.pitch-nx.pitch, 0 if nx.channel == 9 else 2)
                    self.assertEqual((nx.id, nx.start, nx.duration, nx.velocity), (ny.id, ny.start, ny.duration, ny.velocity))

    def test_arrangement_call_response_voicings_fills_and_microgroove(self):
        p = refined()
        tracks = {t.id: t for t in p.tracks}
        self.assertEqual([s.name for s in p.sections], ["Intro", "Groove", "Breakdown", "Drop"])
        self.assertFalse(any(c.start == 8*BAR for c in tracks['track-kick'].clips))
        self.assertTrue(any(c.start == 8*BAR for c in tracks['track-snare'].clips))
        self.assertTrue(any(c.start == 8*BAR for c in tracks['track-pad'].clips))
        lead = next(c for c in tracks['track-lead'].clips if c.start == 4*BAR)
        self.assertGreater(sum(n.start < BAR for n in lead.notes), sum(BAR <= n.start < 2*BAR for n in lead.notes))
        arp = next(c for c in tracks['track-arp'].clips if c.start == 4*BAR)
        self.assertLess(sum(n.start < BAR for n in arp.notes), sum(BAR <= n.start < 2*BAR for n in arp.notes))
        chord = tracks['track-harmony'].clips[0].notes[:4]
        self.assertEqual(len({n.pitch % 12 for n in chord}), 4)
        hats = [n for c in tracks['track-hats'].clips for n in c.notes]
        self.assertTrue(any(n.start % (PPQ//4) == 30 for n in hats))
        self.assertGreater(max(n.velocity for n in hats)-min(n.velocity for n in hats), 20)
        self.assertTrue(all(n.start % PPQ == 0 for c in tracks['track-kick'].clips for n in c.notes))

    def test_sound_design_fx_order_bounds_and_independent_lanes(self):
        p = refined()
        for t in p.tracks:
            self.assertEqual(t.effects[0].plugin_ref, "soundcraft:eq_7band")
            if t.instrument.plugin_ref == "soundcraft:subtractive_synth":
                self.assertIn("soundcraft.filter_env_amount", t.instrument.parameters)
                self.assertIn("soundcraft.osc1_wave", t.instrument.parameters)
        bass = next(t for t in p.tracks if t.id == 'track-bass')
        self.assertEqual([e.plugin_ref for e in bass.effects],
                         ['soundcraft:eq_7band', 'soundcraft:saturator', 'soundcraft:compressor'])
        pairs = [(a.target_id, a.parameter_id) for a in p.automation]
        self.assertEqual(len(pairs), len(set(pairs)))
        for lane in p.automation:
            self.assertEqual(lane.points[0].tick, 0)
            self.assertTrue(all(a.tick < b.tick for a, b in zip(lane.points, lane.points[1:])))
        self.assertGreaterEqual(len(p.automation), 10)

    def test_dry_and_requested_role_omissions(self):
        p = refined('house, dry, no lead, no drums, 8 bars')
        self.assertEqual({t.id for t in p.tracks}, {'track-bass', 'track-harmony', 'track-arp', 'track-pad'})
        self.assertFalse(any(e.plugin_ref in ('soundcraft:plate_reverb', 'soundcraft:mod_delay') for t in p.tracks for e in t.effects))

    def test_profile_rejects_other_genres_and_keeps_sketch_default(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
                with self.assertRaisesRegex(ValidationError, 'house'):
                    create('trap', root/'bad', production='refined')
                self.assertFalse((root/'bad').exists())
                r = create('house', root/'sketch')
                s = compose(rules_plan('house')[0])
                s.metadata.update(prompt='house', planner='rules-v1', ai_plan='false')
                self.assertEqual((root/'sketch/project.kuang.json').read_text(), dumps(s))
                r = create('house', root/'refined', production='refined')
                self.assertEqual(r['engine']['production'], 'refined')
                with self.assertRaises(ValidationError):
                    create('house', root/'refined', production='refined')

    def test_production_parameters_use_ordinary_scopes_and_exact_history(self):
        p = refined()
        engine = Engine(p)
        scope = Scope(['track-harmony'], [], ['soundcraft.rate'], None, None)
        receipt = engine.apply([SetParameter('set_parameter', 'effect-harmony-chorus', 'soundcraft.rate', .6)], scope, state_hash(p))
        expected = deepcopy(p)
        next(e for t in expected.tracks for e in t.effects if e.id == 'effect-harmony-chorus').parameters['soundcraft.rate'] = .6
        self.assertEqual(dumps(engine.project), dumps(expected))
        self.assertEqual(dumps(replay(engine.project, receipt, undo=True)), dumps(p))
        self.assertEqual(dumps(replay(p, receipt, undo=False)), dumps(expected))


class ProductionMappingTests(unittest.TestCase):
    def setUp(self):
        self.adapter = SoundCraftAdapter('/bin/true')
        self.adapter._discovery = deepcopy(CONTRACT)
        self.adapter._discovery['plugins'].update(json.loads((Path(__file__).parent/'fixtures/soundcraft-production-plugins.json').read_text()))
        self.p = refined()

    def test_full_recorded_catalog_accepts_refined_profile(self):
        self.assertTrue(self.adapter.capabilities(self.p)['supported'])

    def test_normalized_choices_and_time_units_are_converted_exactly(self):
        bass = next(t for t in self.p.tracks if t.id == 'track-bass').instrument
        self.assertEqual(self.adapter._parameter(self.p, bass, 'subtractive_synth', 'soundcraft.osc1_wave', 2/3), ('osc1_wave', 2))
        reverb = next(e for t in self.p.tracks for e in t.effects if e.plugin_ref == 'soundcraft:plate_reverb')
        self.assertEqual(self.adapter._parameter(self.p, reverb, 'plate_reverb', 'soundcraft.decay_ms', 1500), ('decay', 1.5))
        with self.assertRaisesRegex(AdapterError, 'fractional'):
            self.adapter._parameter(self.p, bass, 'subtractive_synth', 'soundcraft.osc1_wave', .5)

    def test_wrong_units_missing_choices_and_discrete_automation_are_rejected(self):
        next(s for s in self.p.parameters if s.id == 'soundcraft.osc1_wave').unit = 'Hz'
        self.assertFalse(self.adapter.capabilities(self.p)['supported'])
        self.p = refined()
        for choices in ([], None, 'Saw', [0, 1, 2, 3]):
            self.adapter._discovery['plugins']['subtractive_synth']['params'][0]['choices'] = choices
            self.assertFalse(self.adapter.capabilities(self.p)['supported'])
        self.adapter._discovery = deepcopy(CONTRACT)
        self.p = refined()
        fx = self.p.tracks[0].effects[0]
        fx.parameters['soundcraft.hpf_slope'] = 1/3
        self.p.parameters.append(ParameterSpec('soundcraft.hpf_slope','normalized',0,1,1/3,['effect']))
        self.p.automation.append(AutomationLane('bad-discrete',fx.id,'soundcraft.hpf_slope',
                                  [AutomationPoint('bad-discrete-point',0,1/3,'linear')]))
        self.assertFalse(self.adapter.capabilities(self.p)['supported'])
