"""Focused, engine-free tests for the opt-in groove-first house template MVP."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kuang import midi
from kuang.create import create
from kuang.house_template import PROFILES, select_profile, template
from kuang.schema import BAR, PPQ, ValidationError, dumps, load, state_hash, validate
from kuang.song import rules_plan


class GrooveTemplateTests(unittest.TestCase):
    def test_all_curated_profiles_have_a_real_structural_pocket(self):
        for family in PROFILES:
            for seed in (7, 8):
                with self.subTest(family=family, seed=seed):
                    spec, _ = rules_plan("warm house in D minor, 16 bars, 124 bpm", seed)
                    project, proof = template(spec, profile=family)
                    validate(project)
                    self.assertTrue(proof["technical_pass"])
                    self.assertEqual(proof["perceptual_quality"], "NEEDS_LISTENING")
                    self.assertTrue(all(proof["technical_gates"].values()))
                    self.assertEqual(proof["full_groove_bars"], 4)
                    self.assertEqual(len(proof["full_groove_onsets"]["kick"]), 16)
                    self.assertEqual(len(proof["full_groove_onsets"]["snare"]) >= 8, True)
                    self.assertNotIn("track-lead", {t.id for t in project.tracks})
                    self.assertNotIn("track-arp", {t.id for t in project.tracks})
                    self.assertEqual(project.key_tonic, 2)
                    self.assertEqual(project.key_mode, "minor")
                    self.assertEqual(project.tempo_bpm, 124)
                    for track in project.tracks:
                        for clip in track.clips:
                            for note in clip.notes:
                                self.assertGreater(note.duration, 0)
                                self.assertGreaterEqual(note.start, 0)
                                self.assertLessEqual(note.start + note.duration, clip.length)

    def test_kick_backbeat_and_pump_follow_actual_events(self):
        spec, _ = rules_plan("deep house in C minor, 32 bars", 7)
        project, proof = template(spec, profile="deep", include_pad=True)
        tracks = {t.id: t for t in project.tracks}
        groove = project.sections[1]
        self.assertEqual(groove.length, 8 * BAR)
        kick_onsets = {c.start + n.start for c in tracks["track-kick"].clips for n in c.notes}
        self.assertNotIn(project.sections[2].start, kick_onsets)
        self.assertEqual(len(proof["full_groove_onsets"]["kick"]), 32)
        for role in ("bass", "harmony", "pad"):
            lane = next(a for a in project.automation if a.id == f"production-{role}-duck")
            values = {point.tick: point.value for point in lane.points}
            self.assertEqual(values[0], tracks[f"track-{role}"].controls["mixer.gain_db"] - 5)
            self.assertTrue(all(tick in kick_onsets for tick, value in values.items()
                                if value == tracks[f"track-{role}"].controls["mixer.gain_db"] - 5))
        clap = proof["full_groove_onsets"]["snare"]
        for bar in range(8):
            self.assertIn(bar * BAR + PPQ + 14, clap)
            self.assertIn(bar * BAR + 3 * PPQ + 14, clap)

    def test_opt_in_phase_reference_pocket_is_deterministic_and_default_is_unchanged(self):
        spec,_=rules_plan("deep house in C minor, 16 bars",41)
        baseline,_=template(spec,profile="deep",include_pad=False)
        impact,evidence=template(spec,profile="deep",include_pad=False,impact_pocket=True)
        repeat,_=template(spec,profile="deep",include_pad=False,impact_pocket=True)
        self.assertFalse(state_hash(baseline)==state_hash(impact))
        self.assertEqual(state_hash(impact),state_hash(repeat))
        validate(impact)
        self.assertEqual(evidence["groove_impact_pocket"],True)
        self.assertEqual(evidence["perceptual_quality"],"NEEDS_LISTENING")
        self.assertTrue(all(evidence["technical_gates"].values()))
        self.assertEqual(len(evidence["full_groove_onsets"]["kick"]),16)
        bass=next(t for t in impact.tracks if t.id=="track-bass")
        groove=impact.sections[1]
        counts=[len([n for c in bass.clips for n in c.notes
                     if groove.start+i*BAR<=c.start+n.start<groove.start+(i+1)*BAR])
                for i in range(4)]
        self.assertTrue(all(x>=3 for x in counts))
        old_bass=next(t for t in baseline.tracks if t.id=="track-bass")
        old_count=sum(1 for c in old_bass.clips for n in c.notes
                      if groove.start<=c.start+n.start<groove.start+groove.length)
        self.assertGreaterEqual(sum(counts),old_count)
        self.assertTrue(all(n.duration<=326 for c in bass.clips for n in c.notes))
        impact_perc=next(t for t in impact.tracks if t.id=="track-percussion")
        old_perc=next(t for t in baseline.tracks if t.id=="track-percussion")
        self.assertGreater(sum(len(c.notes) for c in impact_perc.clips),
                           sum(len(c.notes) for c in old_perc.clips))
        self.assertEqual(evidence["source_selection"],"built-in SoundCraft instruments only; no real sample audition")
        self.assertEqual(template(spec,profile="deep",include_pad=False)[0].metadata.get("groove_impact_pocket"),None)

    def test_impact_duck_preserves_dry_harmony_and_tightens_bass_recovery(self):
        spec,_=rules_plan("deep house in C minor, 16 bars",43)
        p,proof=template(spec,profile="deep",include_pad=True,impact_pocket=True)
        validate(p)
        self.assertEqual(proof["impact_ducking_policy"],"source-preserving-impact-v2")
        self.assertFalse(any(a.id=="production-harmony-duck" for a in p.automation))
        tracks={t.id:t for t in p.tracks}
        kick=tracks["track-kick"]
        ticks=sorted({c.start+n.start for c in kick.clips for n in c.notes})
        self.assertTrue(ticks)
        for role,depth_ms in (("bass",(3.,115.)),("pad",(1.25,143.))):
            lane=next(a for a in p.automation if a.id==f"production-{role}-duck")
            bytick={q.tick:q.value for q in lane.points}
            base=tracks[f"track-{role}"].controls["mixer.gain_db"]
            depth,ms=depth_ms
            recovery=round(ms*p.tempo_bpm*p.ppq/60000)
            for at in ticks[:4]:
                self.assertAlmostEqual(bytick[at],base-depth)
                self.assertAlmostEqual(bytick[at+recovery],base)
            self.assertTrue(any(point.tick == p.length for point in lane.points))
        noimpact,_=template(spec,profile="deep",include_pad=True)
        self.assertNotEqual(state_hash(p),state_hash(noimpact))
        self.assertTrue(any(a.id=="production-harmony-duck" for a in noimpact.automation))

    def test_seed_determinism_and_meaningful_variation(self):
        a, _ = rules_plan("house in F# minor, 32 bars", 7)
        b, _ = rules_plan("house in F# minor, 32 bars", 8)
        first, ar = template(a, profile="jackin")
        clone, rr = template(a, profile="jackin")
        variant, br = template(b, profile="jackin")
        self.assertEqual(dumps(first), dumps(clone))
        self.assertEqual(midi.export_bytes(first), midi.export_bytes(clone))
        self.assertEqual(ar["groove_fingerprint_sha256"], rr["groove_fingerprint_sha256"])
        self.assertNotEqual(ar["groove_fingerprint_sha256"], br["groove_fingerprint_sha256"])
        self.assertNotEqual(state_hash(first), state_hash(variant))

    def test_default_and_explicit_profile_selection(self):
        self.assertEqual(select_profile("warm deep house", 19), "deep")
        self.assertEqual(select_profile("minimal house", 19), "minimal")
        self.assertEqual(select_profile("funky house", 19), "jackin")
        self.assertEqual(select_profile("generic house", 8), "straight")
        self.assertEqual(select_profile("generic house", 7), "deep")
        self.assertEqual(select_profile("deep house", 7, "minimal"), "minimal")
        with self.assertRaises(ValidationError):
            select_profile("house", 7, "future-profile")

    def test_pad_optional_and_non_house_fail_closed(self):
        spec, _ = rules_plan("house, no lead, 8 bars", 10)
        project, proof = template(spec, profile="minimal", include_pad=False)
        self.assertNotIn("track-pad", {t.id for t in project.tracks})
        self.assertEqual(proof["melody_roles"], [])
        with self.assertRaises(ValidationError):
            template(spec, profile="not-a-family")
        spec, _ = rules_plan("trap, 8 bars", 10)
        with self.assertRaisesRegex(ValidationError, "house"):
            template(spec, profile="straight")


class GrooveTemplateCreateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_one_prompt_uses_shared_spec_and_publishes_groove_receipt(self):
        out = self.root / "deep-house"
        with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
            result = create("warm deep house in C minor, 16 bars, 126 bpm, no lead, without pad",
                            out, seed=17, production="groove-template")
        self.assertEqual(result["engine"]["production"], "groove-template")
        self.assertEqual(result["groove"]["selected_profile"], "deep")
        self.assertTrue(result["groove"]["technical_pass"])
        self.assertFalse(result["validation"]["audio_verified"])
        spec = json.loads((out / "song-spec.json").read_text())
        self.assertNotIn("lead", spec["instruments"])
        self.assertNotIn("arp", spec["instruments"])
        proof = json.loads((out / "groove-evidence.json").read_text())
        self.assertEqual(proof["song_spec"], spec)
        self.assertEqual(result["artifacts"]["groove_evidence"], str(out / "groove-evidence.json"))
        self.assertIn("groove-evidence.json", result["artifact_sha256"])
        p = load(out / "project.kuang.json")
        self.assertNotIn("track-pad", {t.id for t in p.tracks})
        self.assertTrue((out / "song.mid").is_file())
        self.assertEqual(p.metadata["groove_profile"], "deep")
        self.assertEqual(json.loads(p.metadata["song_spec"]), spec)

    def test_cli_profile_works_without_native_dependencies(self):
        from kuang.cli import main
        with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
            self.assertEqual(main(["create", "house in C major, 8 bars",
                                   "--out-dir", str(self.root / "out"),
                                   "--production", "groove-template",
                                   "--groove-profile", "jackin"]), 0)
        proof = json.loads((self.root / "out/groove-evidence.json").read_text())
        self.assertEqual(proof["selected_profile"], "jackin")

    def test_opt_in_profile_never_changes_legacy_create(self):
        with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
            with self.assertRaisesRegex(ValidationError, "only valid"):
                create("house", self.root / "bad", production="refined", groove_profile="deep")
            with self.assertRaisesRegex(ValidationError, "house"):
                create("trap", self.root / "bad", production="groove-template")
            base = create("house in C major, 8 bars", self.root / "sketch")
            prod = create("house in C major, 8 bars", self.root / "refined", production="refined")
        self.assertEqual(base["engine"]["production"], "sketch")
        self.assertEqual(prod["engine"]["production"], "refined")
        self.assertFalse((self.root / "bad").exists())

    def test_output_no_clobber_and_groove_proof_determinism(self):
        with patch.dict(os.environ, {"KUANG_SOUNDCRAFT": ""}):
            first = create("funky house, 16 bars", self.root / "a",
                           seed=7, production="groove-template")
            second = create("funky house, 16 bars", self.root / "b",
                            seed=7, production="groove-template")
            self.assertEqual(first["groove"]["groove_fingerprint_sha256"],
                             second["groove"]["groove_fingerprint_sha256"])
            self.assertEqual((self.root / "a/song.mid").read_bytes(),
                             (self.root / "b/song.mid").read_bytes())
            with self.assertRaises(ValidationError):
                create("funky house, 16 bars", self.root / "a",
                       seed=7, production="groove-template")
