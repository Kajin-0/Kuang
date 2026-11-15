import unittest
from kuang.house_full_arranger import arrange_full_song
from kuang.house_predrop_tension_v1 import withdraw_predrop
from kuang.house_template import template
from kuang.song import rules_plan
from kuang.schema import BAR,PPQ,ValidationError,dumps
from kuang import midi

class PreDropTensionV1(unittest.TestCase):
    @staticmethod
    def source(style):
        spec,_=rules_plan(f"{style} house in F minor 32 bars 126 bpm",21)
        a,_=template(spec,profile=style,impact_pocket=True,groove_identity_v2=True)
        b,_=arrange_full_song(a,profile=style,bars=128,seed=21,phrase_development_v1=True)
        return b
    def test_128_bar_styles_preserve_other_sections_and_midi_roles(self):
        for profile in ("straight","deep","jackin","minimal"):
            with self.subTest(profile=profile):
                project=self.source(profile)
                orig=dumps(project)
                updated,r=withdraw_predrop(project)
                self.assertEqual(dumps(project),orig)
                self.assertEqual(r["beats_removed"],4 if profile=="jackin" else
                                 1 if profile in ("minimal","deep") else 2)
                self.assertGreater(r["removed_existing_drum_notes"]["kick"],0)
                self.assertEqual([(s.name,s.start,s.length) for s in project.sections],
                                 [(s.name,s.start,s.length) for s in updated.sections])
                for role in ("bass","harmony","pad"):
                    x=next(t for t in project.tracks if t.id=="track-"+role)
                    y=next(t for t in updated.tracks if t.id=="track-"+role)
                    self.assertEqual(x,y)
                drop=next(s.start for s in project.sections if s.name=="Main Drop")
                kick=lambda p:next(t for t in p.tracks if t.id=="track-kick")
                old=[(c.start+n.start,n.pitch) for c in kick(project).clips for n in c.notes]
                new=[(c.start+n.start,n.pitch) for c in kick(updated).clips for n in c.notes]
                self.assertTrue(all(x in old for x in new))
                self.assertEqual([x for x in old if x[0]>=drop],
                                 [x for x in new if x[0]>=drop])
                self.assertNotEqual(midi.export_bytes(project),midi.export_bytes(updated))
                if profile=="jackin":
                    self.assertFalse(any(a.id=="production-harmony-duck" for a in updated.automation))
    def test_one_bar_candidate_is_bounded_and_keeps_actual_drop(self):
        p=self.source("jackin")
        q,receipt=withdraw_predrop(p,beats=4)
        self.assertEqual(receipt["beats_removed"],4)
        drop=next(s for s in p.sections if s.name=="Main Drop")
        for role in ("kick","snare","hats","bass","harmony"):
            t=next(t for t in p.tracks if t.id=="track-"+role)
            u=next(t for t in q.tracks if t.id=="track-"+role)
            before=sorted((c.start+n.start,n.duration,n.pitch) for c in t.clips for n in c.notes if c.start+n.start>=drop.start)
            after=sorted((c.start+n.start,n.duration,n.pitch) for c in u.clips for n in c.notes if c.start+n.start>=drop.start)
            self.assertEqual(before,after)
    def test_strict_optin_range(self):
        p=self.source("jackin")
        for bad in (0,3,5,"1",True):
            with self.assertRaises(ValidationError):withdraw_predrop(p,beats=bad)

if __name__=="__main__":unittest.main()

class NativePreDropDecisionTest(unittest.TestCase):
    @staticmethod
    def row(name,contrast,gap,drop=-28.12,pre=-26.805):
        return {"native_hash":name*64,"native_lufs":-25.6,
                "true_peak_dbtp":-11.,"clipped_samples":0,
                "pre_gap_reference_rms_dbfs":pre,
                "last_beats_rms_dbfs":gap,
                "first_drop_bar_rms_dbfs":drop,
                "drop_over_last_gap_db":contrast,
                "audio_sha256":name*64}
    def test_factual_gate_accepts_fullbar_but_rejects_smaller_changes(self):
        from kuang.house_predrop_tension_v1 import decide_native_predrop
        a=self.row("a",-2.19,-25.931)
        b=self.row("b",.057,-28.174)
        small=self.row("c",-2.096,-26.022)
        self.assertEqual(decide_native_predrop(a,b,profile="jackin")["decision"],
                         "TECHNICALLY_ELIGIBLE_OPTIN")
        self.assertEqual(decide_native_predrop(a,small,profile="jackin")["decision"],
                         "RETAIN_ORIGINAL")
        self.assertFalse(decide_native_predrop(a,b,profile="jackin")["default_enabled"])
    def test_unverified_unsafe_or_damaged_drop_not_accepted(self):
        from kuang.house_predrop_tension_v1 import decide_native_predrop
        a=self.row("a",-2.19,-25.931)
        bad=self.row("b",.057,-28.174,drop=-25.)
        self.assertEqual(decide_native_predrop(a,bad,profile="jackin")["decision"],
                         "RETAIN_ORIGINAL")
        bad=self.row("b",.057,-28.174)
        bad["clipped_samples"]=1
        with self.assertRaises(ValidationError):decide_native_predrop(a,bad,profile="jackin")
