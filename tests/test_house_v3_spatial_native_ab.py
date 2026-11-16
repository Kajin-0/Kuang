"""Pure symbolic source-locking tests; actual native SoundCraft is the acceptance source."""
import unittest
from copy import deepcopy
from kuang import midi
from kuang.schema import Track, Effect, state_hash, ValidationError
from kuang.song import rules_plan
from kuang.house_template import template
from tools.house_v3_spatial_native_ab import make_scene, SCENES


def source():
    spec,_=rules_plan("deep house E minor 16 bars 123 bpm",seed=41)
    return template(spec,profile="deep",harmony_profile="simple",
                    impact_pocket=True,groove_identity_v2=True)[0]


def reference(p):
    r=deepcopy(p)
    for tid,plugin in (("phase15-shared-room","room_reverb"),
                       ("phase17-dark-space","plate_reverb"),
                       ("phase17-echo","mod_delay")):
        r.tracks.append(Track(tid,tid,"bus",None,
             {"mixer.gain_db":0.,"mixer.pan":0.,"mixer.mute":0.},
             [Effect("fx-"+tid,"soundcraft:"+plugin,None,{})],[],[],True))
    return r


class SpatialNativeSymbolicTests(unittest.TestCase):
    def test_three_bounded_scenes_keep_source_midi_instruments_and_mix(self):
        p=source()
        r=reference(p)
        original=state_hash(p)
        expected={"A_dry":0,"B_room_plate":2,"C_room_plate_echo":3}
        for scene in SCENES:
            with self.subTest(scene=scene):
                candidate=make_scene(p,r,scene)
                self.assertEqual(state_hash(p),original)
                self.assertEqual(midi.export_bytes(candidate),midi.export_bytes(p))
                self.assertEqual(len([t for t in candidate.tracks if t.kind=="bus"]),
                                 expected[scene])
                for a,b in zip(p.tracks,candidate.tracks):
                    self.assertEqual(a.instrument,b.instrument)
                    self.assertEqual(a.effects,b.effects)
                    self.assertEqual(a.clips,b.clips)
                    self.assertEqual(a.controls,b.controls)
                    self.assertEqual(a.output_master,b.output_master)
                    if a.id in ("track-kick","track-bass"):
                        self.assertEqual(a.sends,b.sends)
                self.assertFalse(any(t.sends for t in candidate.tracks
                    if t.id in ("track-kick","track-bass")))

    def test_invalid_scene_fails(self):
        p=source()
        with self.assertRaises(ValidationError):
            make_scene(p,reference(p),"all_channels_mono_widen")


if __name__=="__main__":
    unittest.main()
