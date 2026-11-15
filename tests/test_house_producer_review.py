import unittest
from copy import deepcopy
from kuang import midi
from kuang.house_producer_review import diagnose,candidate,evaluate_candidate_effect,producer_context_packet,validate_producer_proposal,revise_from_native_stems,CANDIDATES,BUS_ID
from kuang.house_template import template
from kuang.song import rules_plan
from kuang.schema import ValidationError,dumps

class HouseProducerReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec,_=rules_plan("straight house in F minor 32 bars 120 bpm",10942499)
        cls.source,_=template(spec,profile="straight",impact_pocket=True,groove_identity_v2=True)
        cls.evidence=dict(side_to_mid_db=-30.,presence_1_4k_vs_kick_bass_db=-12.7,groove_section="Groove")
        cls.reference=dict(side_to_mid_db=-17.,presence_1_4k_vs_kick_bass_db=-4.1)
    def test_stage3_requires_audio_context_and_valid_section(self):
        for evidence in ({}, dict(self.evidence,side_to_mid_db=float("nan")),
                         dict(self.evidence,groove_section="not-a-section")):
            with self.assertRaises(ValidationError):
                diagnose(self.source,audio_evidence=evidence,reference_evidence=self.reference)
    def test_weak_evidence_does_not_change_mix(self):
        result=diagnose(self.source,audio_evidence=self.evidence,
                        reference_evidence={"side_to_mid_db":-29.,"presence_1_4k_vs_kick_bass_db":-12.})
        self.assertEqual(result["decision"],"NO_CHANGE")
        with self.assertRaises(ValidationError):candidate(self.source,result,variant="soft")
    def test_two_bounded_reversible_variants_keep_dry_stems_exact(self):
        before=dumps(self.source)
        review=diagnose(self.source,audio_evidence=self.evidence,reference_evidence=self.reference)
        self.assertEqual(review["decision"],"AUDITION_WET_CHORD_SPACE")
        for variant in CANDIDATES:
            p,receipt=candidate(self.source,review,variant=variant)
            self.assertEqual(midi.export_bytes(p),midi.export_bytes(self.source))
            if variant!="body":
                self.assertEqual(p.automation,self.source.automation)
            else:
                original=next(t for t in self.source.tracks if t.id=="track-harmony")
                revised=next(t for t in p.tracks if t.id=="track-harmony")
                self.assertAlmostEqual(revised.controls["mixer.gain_db"]-original.controls["mixer.gain_db"],3.)
                self.assertEqual(revised.controls["mixer.stereo_spread"],.30)
            self.assertEqual(len(p.tracks),len(self.source.tracks)+1)
            self.assertEqual(p.tracks[-1].id,BUS_ID)
            self.assertEqual(len(p.tracks[-1].effects),3)
            self.assertEqual(p.tracks[-1].effects[1].parameters["effect.wet"],1.)
            self.assertTrue(receipt["source_kick_bass_exact"])
            self.assertIsNone(receipt["automatic_winner"])
            with self.assertRaises(ValidationError):candidate(p,review,variant=variant)
        self.assertEqual(dumps(self.source),before)
    def test_producer_review_rejects_ineffective_audio_results(self):
        review=diagnose(self.source,audio_evidence=self.evidence,reference_evidence=self.reference)
        weak=evaluate_candidate_effect(review,{
            "side_to_mid_db":-37.8738,"presence_1_4k_vs_kick_bass_db":-15.671},{
            "side_to_mid_db":-37.8195,"presence_1_4k_vs_kick_bass_db":-15.5508},
            candidate_id="present")
        self.assertEqual(weak["technical_decision"],"REJECT_INEFFECTIVE")
        viable=evaluate_candidate_effect(review,{
            "side_to_mid_db":-37.8738,"presence_1_4k_vs_kick_bass_db":-15.671},{
            "side_to_mid_db":-28.,"presence_1_4k_vs_kick_bass_db":-13.},
            candidate_id="body")
        self.assertEqual(viable["technical_decision"],"ELIGIBLE_FOR_LISTENING")
        self.assertFalse(viable["quality_improvement_proven"])

    def test_full_context_for_bounded_model_or_human_proposal(self):
        review=diagnose(self.source,audio_evidence=self.evidence,reference_evidence=self.reference)
        packet=producer_context_packet(self.source,review,native_audio_features={
            "side_to_mid_db":-37.8738,"presence_1_4k_vs_kick_bass_db":-15.671},
            previous_trials=[{"candidate":"soft","decision":"REJECT_INEFFECTIVE"}])
        self.assertEqual(len(packet["roles"]),len(self.source.tracks))
        self.assertEqual(packet["allowed_actions"],["NO_CHANGE","AUDITION_EXISTING_BOUNDED_CANDIDATE"])
        proposal={"context_digest":packet["context_digest"],
                  "action":"AUDITION_EXISTING_BOUNDED_CANDIDATE","candidate":"body",
                  "reason":"Dry harmony appears too recessed, and wet-only candidate failed.",
                  "evidence":["presence_1_4k_vs_kick_bass_db"]}
        accepted=validate_producer_proposal(packet,proposal)
        self.assertEqual(accepted["candidate"],"body")
        self.assertFalse(accepted["automatically_good"])
        for invalid in ({**proposal,"candidate":"master_gain_plus_24db"},
                        {**proposal,"context_digest":"oldhash"},
                        {**proposal,"evidence":["imagined_qa_score"]},
                        {**proposal,"reason":"vague"},
                        {**proposal,"new_controls":{"track-kick":24.}}):
            with self.assertRaises(ValidationError):
                validate_producer_proposal(packet,invalid)

    def test_native_stem_review_pivots_from_ineffective_effects_to_source(self):
        review=diagnose(self.source,audio_evidence=self.evidence,reference_evidence=self.reference)
        stems={"kick":{"rms_dbfs":-29.64},"bass":{"rms_dbfs":-36.06},
               "harmony":{"rms_dbfs":-64.07}}
        trial=[{"technical_decision":"REJECT_INEFFECTIVE"}]
        finding=revise_from_native_stems(review,stems,
              explicit_chord_prominence=True,previous_trials=trial)
        self.assertEqual(finding["decision"],"AUDITION_VERIFIED_CHORD_SOURCE")
        self.assertAlmostEqual(finding["native_chord_vs_kick_rms_db"],-34.43)
        self.assertFalse(finding["changed_midi_or_presets"])
        for kwargs in ({"explicit_chord_prominence":False,"previous_trials":trial},
                       {"explicit_chord_prominence":True,"previous_trials":()}):
            self.assertEqual(revise_from_native_stems(review,stems,**kwargs)["decision"],
                             "NO_SOURCE_CHANGE_RECOMMENDED")

    def test_source_hash_rejects_other_song(self):
        review=diagnose(self.source,audio_evidence=self.evidence,reference_evidence=self.reference)
        changed=deepcopy(self.source);changed.tempo_bpm+=1
        with self.assertRaises(ValidationError):candidate(changed,review,variant="soft")

if __name__=="__main__":unittest.main()
