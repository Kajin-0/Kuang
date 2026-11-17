"""Regression tests for the previously failed native eight-bar crop harness."""
import unittest

from kuang.house_full_arranger import arrange_full_song
from kuang.house_native_excerpt import crop_sounding_native
from kuang.house_template import template
from kuang.midi import export_bytes
from kuang.schema import dumps, state_hash
from kuang.song import rules_plan


def _source(profile, seed):
    spec,_=rules_plan(f"{profile} house in C minor, 32 bars, 126 bpm",seed)
    return template(spec,profile=profile,include_pad=True,
                    impact_pocket=True,groove_identity_v2=True)[0]


class NativeHouseExcerptTests(unittest.TestCase):
    def test_main_drop_crop_removes_silent_roles_and_orphan_effect_lanes(self):
        # The real native failed attempt retained a silent optional voice.
        # After removing it the test harness forgot to filter its effect
        # automation targets. This is a reproducible preflight.
        for style in ("deep","minimal","jackin"):
            with self.subTest(style=style):
                short=_source(style,41)
                full,_=arrange_full_song(short,bars=128,seed=41,
                    phrase_development_v1=True,drum_scenes_v1=True)
                before=dumps(full)
                drop=next(s for s in full.sections if s.name=="Main Drop")
                excerpt,receipt=crop_sounding_native(full,drop.start//3840,8)
                self.assertEqual(dumps(full),before)
                self.assertTrue(receipt["native_graph_verified"])
                self.assertTrue(receipt["dsp_reset"])
                self.assertFalse(receipt["continuous_render_exact_slice"])
                owners={t.id for t in excerpt.tracks}
                owners|={e.id for t in excerpt.tracks for e in t.effects}
                self.assertTrue(all(a.target_id in owners
                                    for a in excerpt.automation))
                self.assertTrue(all(any(c.notes for c in t.clips)
                                    for t in excerpt.tracks if t.kind=="midi"))
                self.assertIn("track-kick",receipt["remaining_audio_roles"])
                self.assertIn("track-bass",receipt["remaining_audio_roles"])

    def test_drum_scenes_change_hats_without_altering_native_kick_bass_chords(self):
        src=_source("jackin",217)
        a,_=arrange_full_song(src,bars=128,seed=217,
                              phrase_development_v1=True)
        b,_=arrange_full_song(src,bars=128,seed=217,
                              phrase_development_v1=True,drum_scenes_v1=True)
        first=next(s for s in a.sections if s.name=="Main Drop").start//3840
        cut_a,receipt_a=crop_sounding_native(a,first,8)
        cut_b,receipt_b=crop_sounding_native(b,first,8)
        def role_events(project,role):
            t=next(t for t in project.tracks if t.id=="track-"+role)
            return sorted((c.start+n.start,n.duration,n.pitch,n.velocity)
                          for c in t.clips for n in c.notes)
        for role in ("kick","bass","harmony","snare"):
            self.assertEqual(role_events(cut_a,role),
                             role_events(cut_b,role))
        self.assertNotEqual(role_events(cut_a,"hats"),
                            role_events(cut_b,"hats"))
        self.assertNotEqual(export_bytes(cut_a),export_bytes(cut_b))
        self.assertNotEqual(receipt_a["excerpt_hash"],receipt_b["excerpt_hash"])


if __name__=="__main__":
    unittest.main()
