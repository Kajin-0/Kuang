"""Sound design and exact performance contracts; no offline quality claims."""
import base64
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.studio_palette import studio_patch, ROLES, TRACKS
from kuang.sound_palette import sound_palette, performance, MIX_TRIMS
from kuang.schema import ValidationError, dumps, state_hash
from kuang.midi import export_bytes
from kuang.vitalium_patch import original_patch, component, component_patch
from test_external_synth import contract_patch

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT/'.local/phase16/tests'


class StudioPatchTests(unittest.TestCase):
    def test_deterministic_original_waves_no_embedded_third_party_content(self):
        for voice in ROLES:
            p = studio_patch(voice)
            self.assertEqual(p, studio_patch(voice))
            self.assertEqual(p, component_patch(component(p)))
            self.assertEqual(p['settings']['wavetables'], original_patch('pad')['settings']['wavetables'])
            self.assertEqual(base64.b64decode(p['settings']['sample']['samples']), bytes(64))
            self.assertEqual(p['settings']['sample_on'], 0)

    def test_role_articulation_and_bass_mono_integer_tuning(self):
        states = {k: studio_patch(k)['settings'] for k in ROLES}
        self.assertEqual(len({tuple(s['env_1_'+k] for k in ('attack','decay','sustain','release')) for s in states.values()}), 4)
        self.assertGreater(states['pad']['env_1_release']**4, 1)
        self.assertLess(states['bass']['env_1_release']**4, .03)
        self.assertEqual(states['bass']['polyphony'], 1)
        for s in states.values():
            self.assertEqual(s['osc_1_tune'], 0)
            self.assertEqual(s['osc_2_tune'], 0)
            self.assertIn(s['osc_2_transpose'], (0, 12))
            self.assertEqual(s['osc_1_random_phase'], 0)
            self.assertEqual(s['osc_1_unison_voices'], 1)
        self.assertEqual(states['bass']['osc_1_stereo_spread'], 0)
        self.assertGreater(states['pad']['osc_2_pan']-states['pad']['osc_1_pan'],1)
        self.assertLess(abs(states['pad']['osc_2_phase']-states['pad']['osc_1_phase']),.1)

    def test_actual_timbre_destinations_no_pitch_modulation_and_bypass_causal_scope(self):
        for voice in ROLES:
            a = studio_patch(voice); b = studio_patch(voice, modulation=False)
            links = a['settings']['modulations']
            self.assertTrue(links)
            self.assertFalse(any('tune' in x['destination'] or 'transpose' in x['destination'] for x in links))
            self.assertEqual(b['settings']['modulations'], [])
            b['settings']['modulations'] = links
            self.assertEqual(a, b)
        self.assertEqual(studio_patch('bass')['settings']['osc_1_distortion_type'], 7)
        self.assertEqual(studio_patch('lead')['settings']['osc_1_distortion_type'], 4)

    def test_fail_closed_voice_boolean_gain(self):
        for args, kw in [(('official Vital',), {}), (('pad',), {'modulation': 1}),
                         (('bass',), {'volume_db': float('nan')}), (('lead',), {'volume_db': 1})]:
            with self.assertRaises(ValidationError): studio_patch(*args, **kw)


class SoundOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = repaired_house(split_house(atmosphere_house())[0])[0]
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.asset = contract_patch(Path(self.temp.name)/'contract-only')
    def tearDown(self): self.temp.cleanup()
    def proposal(self, assignments=None):
        # Symbolic fixture contains no downloaded sample assets; use its exact
        # explicit fingerprint. Native tests use the shipped incumbent hash.
        with patch('kuang.sound_palette.SOURCE_HASH', state_hash(self.source)):
            return sound_palette(self.source, assignments or {k:self.asset for k in TRACKS})

    def test_all_1536_note_fields_clip_ownership_sections_and_MIDI_bytes_exact(self):
        p, r = self.proposal()
        self.assertEqual(performance(p), performance(self.source))
        self.assertEqual(export_bytes(p), export_bytes(self.source))
        self.assertEqual(r['note_count'], 1536)
        for a,b in zip(self.source.automation,p.automation):
            self.assertEqual((a.id,a.target_id,a.parameter_id),(b.id,b.target_id,b.parameter_id))
            self.assertEqual([(x.id,x.tick,x.shape) for x in a.points],[(x.id,x.tick,x.shape) for x in b.points])
            for x,y in zip(a.points,b.points):
                expected=x.value
                if a.target_id in TRACKS and a.parameter_id=='mixer.gain_db': expected+=MIX_TRIMS[a.target_id]
                if a.target_id=='effect-harmony-eq' and a.parameter_id=='soundcraft.hpf_freq' and expected==280: expected=150
                self.assertEqual(y.value,expected)
        self.assertEqual(p.sections, self.source.sections)

    def test_every_drum_sub_arp_air_and_existing_bus_fully_exact(self):
        p, _ = self.proposal()
        for t, u in zip(self.source.tracks, p.tracks):
            if t.id not in TRACKS: self.assertEqual(t, u)
            if t.id!='track-harmony':self.assertEqual(t.effects, u.effects)
            self.assertEqual((t.sends,t.output_master), (u.sends,u.output_master))

    def test_sequential_opt_in_voice_assignments_no_unrequested_swap(self):
        for tid in TRACKS:
            p, r = self.proposal({tid:self.asset})
            self.assertEqual([x['track'] for x in r['changes']], [tid])
            for t, u in zip(self.source.tracks, p.tracks):
                if t.id != tid: self.assertEqual(t, u)

    def test_deterministic_source_immutable_and_strict_original(self):
        before = dumps(self.source)
        a, r = self.proposal(); b, s = self.proposal()
        self.assertEqual(dumps(a), dumps(b)); self.assertEqual(r, s)
        self.assertEqual(dumps(self.source), before)
        with self.assertRaises(ValidationError): sound_palette(self.source, {k:self.asset for k in TRACKS})
        with patch('kuang.sound_palette.SOURCE_HASH', state_hash(self.source)):
            for assignments in ({}, {'track-kick':self.asset}, {'missing':self.asset}):
                with self.assertRaises(ValidationError): sound_palette(self.source, assignments)

    def test_music_guard_detects_injected_note_or_section_change(self):
        from kuang.external_synth import bound_project
        def corrupt(p, a):
            q = bound_project(p,a);q.tracks[0].clips[0].notes[0].velocity -= 1;return q
        with patch('kuang.sound_palette.bound_project', side_effect=corrupt):
            with self.assertRaises(ValidationError): self.proposal()

    def test_native_stereo_positions_bounded_and_low_end_unchanged(self):
        from kuang.production_host import native_pan
        p, _ = self.proposal()
        for t in p.tracks:
            self.assertTrue(all(-1 <= v <= 1 for v in native_pan(t)))
        for tid in ('track-bass','track-kick','track-sub-pulse'):
            t = next(t for t in p.tracks if t.id == tid)
            self.assertEqual(native_pan(t), [0,0])
