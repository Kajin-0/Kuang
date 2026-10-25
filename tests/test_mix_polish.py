"""Mix-only contracts; these symbolic checks do not claim audio quality."""
import unittest
from copy import deepcopy
from dataclasses import asdict
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.production_host import graph_contract,trim_id
from kuang.sound_palette import performance
from kuang.schema import state_hash,dumps,ValidationError,BAR
from kuang.midi import export_bytes


class MixPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=repaired_house(split_house(atmosphere_house())[0])[0]
        # No plugin/media is needed for symbolic contracts. Match the approved
        # Phase16 centers; actual native cases use the sealed shipped source.
        for t in cls.source.tracks:
            if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
    def proposal(self):
        with patch('kuang.mix_polish.SOURCE_HASH',state_hash(self.source)):
            return polished_mix(self.source)
    def test_every_note_clip_instrument_and_MIDI_byte_unchanged(self):
        q,r=self.proposal();old=self.source;check=deepcopy(q);check.tracks=check.tracks[:len(old.tracks)]
        self.assertEqual(performance(check),performance(old));self.assertEqual(export_bytes(q),export_bytes(old))
        for t,u in zip(old.tracks,q.tracks):self.assertEqual(t.instrument,u.instrument);self.assertEqual(t.clips,u.clips)
        self.assertEqual(sum(len(c.notes) for t in q.tracks for c in t.clips),1536)
    def test_source_immutable_deterministic_and_wrong_source_rejected(self):
        before=dumps(self.source);a,r=self.proposal();b,s=self.proposal()
        self.assertEqual(dumps(a),dumps(b));self.assertEqual(r,s);self.assertEqual(before,dumps(self.source))
        with self.assertRaises(ValidationError):polished_mix(self.source)
    def test_two_actual_new_auxes_filtered_wet_only_no_bus_cycles(self):
        q,r=self.proposal();self.assertEqual(len(q.tracks),17);graph_contract(q)
        for tid in r['new_auxes']:
            t=next(t for t in q.tracks if t.id==tid);self.assertEqual(t.kind,'bus');self.assertFalse(t.sends);self.assertFalse(t.clips)
            self.assertEqual(t.effects[0].plugin_ref,'soundcraft:eq_7band')
            self.assertGreaterEqual(t.effects[0].parameters['soundcraft.hpf_freq'],500)
        dark=next(t for t in q.tracks if t.id=='phase17-dark-space')
        self.assertEqual(dark.effects[-1].parameters['effect.wet'],1)
        self.assertEqual(dark.effects[-1].parameters['soundcraft.decay_ms'],2400)
    def test_echo_is_dotted_eighth_actual_post_fader_trim_with_finite_closures(self):
        q,r=self.proposal();echo=next(t for t in q.tracks if t.id=='phase17-echo')
        delay=next(e for e in echo.effects if e.plugin_ref=='soundcraft:mod_delay')
        self.assertAlmostEqual(delay.parameters['soundcraft.time'],60000/126*.75)
        for tid,windows in r['throw_windows'].items():
            t=next(t for t in q.tracks if t.id==tid);s=next(s for s in t.sends if s.target_track_id==echo.id)
            lane=next(a for a in q.automation if a.target_id==tid and a.parameter_id==trim_id(s))
            self.assertEqual(s.mode,'post_fader');self.assertEqual(lane.points[0].value,-60);self.assertEqual(lane.points[-1].value,-60)
            self.assertTrue(windows);self.assertTrue(all(w['close_tick']>w['onset_tick'] for w in windows))
    def test_kick_derived_duck_includes_dropouts_and_is_not_claimed_triggered_audio(self):
        q,r=self.proposal();kick={c.start+n.start for t in self.source.tracks if t.id=='track-kick' for c in t.clips for n in c.notes}
        self.assertEqual(set(r['kick_onsets']),kick);self.assertIn('not audio-triggered',r['ducking'])
        lane=next(a for a in q.automation if a.target_id=='track-bass' and a.parameter_id=='mixer.gain_db')
        self.assertEqual(lane,next(a for a in self.source.automation if a.target_id=='track-bass' and a.parameter_id=='mixer.gain_db'))
        self.assertTrue(all(0<=x.tick<=64*BAR for x in lane.points));self.assertEqual(len({x.tick for x in lane.points}),len(lane.points))
    def test_removed_inserts_have_no_dangling_lanes_and_low_end_remains_centered(self):
        q,r=self.proposal();removed=set(r['removed_insert_ids'])
        self.assertFalse(any(a.target_id in removed for a in q.automation))
        for tid in ('track-kick','track-bass','track-sub-pulse'):
            t=next(t for t in q.tracks if t.id==tid);self.assertEqual(t.controls['mixer.pan'],0);self.assertNotIn('mixer.stereo_spread',t.controls)
        self.assertEqual(q.sections,self.source.sections);self.assertEqual(q.metadata['song_spec'],self.source.metadata['song_spec'])
    def test_kick_free_breakdown_retains_explicit_space_level_and_drop_reset(self):
        from kuang.gestures import lane_value
        from kuang.ensemble_production import PAN_COMPENSATION_DB
        q,r=self.proposal()
        for tid in ('phase17-dark-space','phase17-echo'):
            a=next(a for a in q.automation if a.target_id==tid and a.parameter_id=='mixer.gain_db')
            self.assertIn(24*BAR,{x.tick for x in a.points});self.assertIn(32*BAR,{x.tick for x in a.points})
            self.assertAlmostEqual(lane_value(a,28*BAR),PAN_COMPENSATION_DB+1)
            self.assertLess(lane_value(a,32*BAR),PAN_COMPENSATION_DB)
