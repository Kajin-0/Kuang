import unittest
from kuang import midi
from kuang.house_bass_producer_v2 import context_bass_variants
from kuang.house_template import template
from kuang.song import rules_plan
from kuang.schema import ValidationError,state_hash,dumps


class HouseBassProducerV2(unittest.TestCase):
    @staticmethod
    def source(profile="straight"):
        spec,_=rules_plan(f"{profile} house in F minor 32 bars 124 bpm",217)
        p,_=template(spec,profile=profile,impact_pocket=True,groove_identity_v2=True)
        return p
    @staticmethod
    def native(p,bass_vs_kick=-8.5):
        return {"native_canonical_sha256":state_hash(p),"source_preserved":True,
                "role_stems":{"kick":{"rms_dbfs":-29.5},"bass":{"rms_dbfs":-29.5+bass_vs_kick}}}
    def test_cross_style_candidate_preserves_dry_song_and_midi(self):
        for profile in ("straight","jackin","minimal"):
            with self.subTest(profile=profile):
                p=self.source(profile)
                original=dumps(p)
                v=context_bass_variants(p,native_stems=self.native(p,-15 if profile=="minimal" else -8.5),
                                        section="Groove",bars=8)
                self.assertEqual(dumps(p),original)
                self.assertEqual(midi.export_bytes(p),midi.export_bytes(v["B"]))
                if v["receipt"]["phrase_variant_available"]:
                    self.assertNotEqual(midi.export_bytes(p),midi.export_bytes(v["C"]))
                else:
                    self.assertEqual(midi.export_bytes(v["B"]),midi.export_bytes(v["C"]))
                self.assertTrue(v["receipt"]["phase_pickup_receipt"]["kick_midi_unchanged"])
                self.assertIsNone(v["receipt"]["auto_winner"])
                self.assertFalse(v["receipt"]["default_enabled"])
    def test_audition_gain_depends_on_evidence_not_universal_rule(self):
        p=self.source()
        for gap,expected in [(-16,2.),(-8.5,1.5),(-3,.5)]:
            with self.subTest(gap=gap):
                v=context_bass_variants(p,native_stems=self.native(p,gap),
                                        section="Groove",bars=8)
                self.assertEqual(v["receipt"]["conditional_audition_gain_db"],expected)
    def test_stale_or_unverified_native_evidence_fails(self):
        p=self.source()
        for evidence in ({}, {"native_canonical_sha256":"stale","source_preserved":True,
                             "role_stems":self.native(p)["role_stems"]},
                         {**self.native(p),"source_preserved":False}):
            with self.assertRaises(ValidationError):
                context_bass_variants(p,native_stems=evidence,section="Groove",bars=8)

if __name__=="__main__":unittest.main()
