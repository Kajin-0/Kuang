"""Quality scorecard: reference invariants, fail cases, velocity-resistant diversity."""
import unittest
from copy import deepcopy

from kuang.song import rules_plan
from kuang.composer import compose
from kuang.production import refine_house
from kuang.house_template import template
from kuang.house_full_arranger import arrange_full_song
from kuang.house_gates import evaluate,VERSION,CORE
from kuang.schema import BAR,ValidationError,state_hash
from tools.house_gates import benchmark

class MusicalScorecardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec,_=rules_plan("jackin house in G major 32 bars, 127 bpm",217)
        cls.base=compose(cls.spec)
        cls.refined=refine_house(cls.spec,deepcopy(cls.base))
        cls.source=template(cls.spec,profile="jackin",impact_pocket=True,
                            groove_identity_v2=True)[0]
        cls.full,_=arrange_full_song(cls.source,bars=128,profile="jackin",seed=217)

    def test_legacy_and_groove_are_versioned_with_explicit_na(self):
        for name,project in [("sketch",self.base),("refined",self.refined),
                             ("groove",self.source),("full",self.full)]:
            with self.subTest(version=name):
                result=evaluate(project,expected_no_lead_arp=name in ("groove","full"))
                self.assertEqual(result["version"],VERSION)
                self.assertEqual(result["hard_failures"],[])
                self.assertEqual(result["perceptual_quality"],"NOT_EVALUATED")
                self.assertIsNone(result["hard_gates"]["H06_no_lead_arp_when_requested"] if name in ("sketch","refined") else None)
                self.assertIsNone(result["diagnostics"]["D04_outro_minus_groove_core_onsets_per_bar"] if name!="full" else None)
        self.assertFalse(evaluate(self.refined)["diagnostics"]["D01_no_lead_arp"])
        self.assertTrue(evaluate(self.full,expected_no_lead_arp=True)["diagnostics"]["D01_no_lead_arp"])

    def test_exact_velocity_changes_do_not_create_new_musical_identity(self):
        variant=deepcopy(self.source)
        chord=next(t for t in variant.tracks if t.id=="track-harmony")
        for clip in chord.clips:
            for note in clip.notes:note.velocity= min(127,note.velocity+4)
        before=evaluate(self.source)
        after=evaluate(variant)
        self.assertEqual(before["fingerprints"],after["fingerprints"])
        self.assertEqual(before["diagnostics"]["D02_core_groove_drop_equal_fraction"],
                         after["diagnostics"]["D02_core_groove_drop_equal_fraction"])

    def test_musically_different_note_changes_fingerprint(self):
        variant=deepcopy(self.source)
        bass=next(t for t in variant.tracks if t.id=="track-bass")
        note=next(n for c in bass.clips for n in c.notes)
        note.pitch+=1
        x=evaluate(self.source)["fingerprints"]
        y=evaluate(variant)["fingerprints"]
        self.assertNotEqual(x["musical_core"],y["musical_core"])
        self.assertEqual(x["rhythm_core"],y["rhythm_core"])
        self.assertEqual(state_hash(self.source),state_hash(self.source))

    def test_missing_expected_kick_in_active_groove_is_hard_failure(self):
        bad=deepcopy(self.source)
        groove=next(s for s in bad.sections if s.name=="Groove")
        kicks=next(t for t in bad.tracks if t.id=="track-kick")
        removed=False
        for clip in kicks.clips:
            for note in tuple(clip.notes):
                if groove.start<=clip.start+note.start<groove.start+groove.length:
                    clip.notes.remove(note);removed=True;break
            if removed:break
        self.assertTrue(removed)
        report=evaluate(bad,expected_no_lead_arp=True)
        self.assertEqual(report["hard_gates"]["H04_kick_in_active_groove"],False)
        self.assertIn("H04_kick_in_active_groove",report["hard_failures"])

    def test_breakdown_with_kick_fails_not_full_song(self):
        bad=deepcopy(self.full)
        section=next(s for s in bad.sections if s.name=="Breakdown")
        track=next(t for t in bad.tracks if t.id=="track-kick")
        from kuang.schema import Clip,Note
        track.clips.append(Clip("quality-injected","kick in breakdown","midi",section.start,BAR,
                                [Note("kick-in-breakdown",0,120,36,100,9)],None))
        report=evaluate(bad,expected_no_lead_arp=True)
        self.assertFalse(report["hard_gates"]["H05_breakdown_kick_bass_absent"])

    def test_lead_arp_only_hard_gated_when_explicit(self):
        from kuang.schema import Clip,Note
        bad=deepcopy(self.source)
        track=next(t for t in bad.tracks if t.id=="track-harmony")
        track.id="track-lead"
        self.assertIsNone(evaluate(bad)["hard_gates"]["H06_no_lead_arp_when_requested"])
        gated=evaluate(bad,expected_no_lead_arp=True)
        self.assertFalse(gated["hard_gates"]["H06_no_lead_arp_when_requested"])

    def test_dry_harmony_policy_conflict_is_hard_failure(self):
        from kuang.schema import AutomationLane,AutomationPoint
        bad=deepcopy(self.full)
        bad.automation.append(AutomationLane("production-harmony-duck","track-harmony","mixer.gain_db",
              [AutomationPoint("bad-gain",0,-7.,"linear")]))
        actual=evaluate(bad,expected_no_lead_arp=True)
        self.assertFalse(actual["hard_gates"]["H07_preserve_dry_harmony_impact_policy"])
        self.assertIn("H07_preserve_dry_harmony_impact_policy",actual["hard_failures"])
        healthy=evaluate(self.full,expected_no_lead_arp=True)
        self.assertTrue(healthy["hard_gates"]["H07_preserve_dry_harmony_impact_policy"])
        self.assertIsNone(evaluate(self.refined)["hard_gates"]["H07_preserve_dry_harmony_impact_policy"])

    def test_long_sections_thin_out_and_record_core_copying(self):
        report=evaluate(self.full,expected_no_lead_arp=True)
        d=report["diagnostics"]
        self.assertLess(d["D04_outro_minus_groove_core_onsets_per_bar"],0)
        self.assertGreater(d["D02_core_groove_drop_equal_fraction"]["bass"],.75)
        self.assertIsNotNone(d["D06_eight_bar_pitch_rhythm_repetition"]["bass"]["fraction_repeated"])

    def test_matrix_is_stable_and_controls_fixed(self):
        options=dict(profiles=("deep",),keys=("C major",),lengths=(16,),
                     seeds=(17,29),variants=("sketch","refined","groove-v2"))
        first=benchmark(**options)
        second=benchmark(**options)
        self.assertEqual(first,second)
        self.assertEqual(len(first["cases"]),6)
        self.assertEqual(first["errors"],[])
        self.assertEqual(set(first["summary"]),{"sketch","refined","groove-v2"})
        for composer in first["summary"]:
            self.assertEqual(first["summary"][composer]["songs"],2)
            self.assertIsNone(first["summary"][composer]["outro_minus_groove_core_density_median"])

if __name__=="__main__":unittest.main()
