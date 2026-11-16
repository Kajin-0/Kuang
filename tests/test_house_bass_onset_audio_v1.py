"""Real WAV synthetic transient timing and mono/format failure tests."""
import math
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from kuang.house_bass_onset_audio_v1 import evaluate_note_aligned_pocket,block_severe_native_source_faults
from kuang.schema import ValidationError


def project():
    kick=SimpleNamespace(id="track-kick",clips=[SimpleNamespace(start=0,notes=[
        SimpleNamespace(start=i*960) for i in range(8)])])
    bass=SimpleNamespace(id="track-bass",clips=[SimpleNamespace(start=0,notes=[
        SimpleNamespace(start=i*960+480) for i in range(8)])])
    return SimpleNamespace(ppq=960,tempo_bpm=120.,
        tracks=[kick,bass],
        sections=[SimpleNamespace(name="Groove",start=0,length=8*960)])


def write(path, *, role, amp=.12, antiphase=False):
    rate=48000
    with wave.open(str(path),"wb") as w:
        w.setnchannels(2);w.setsampwidth(3);w.setframerate(rate)
        out=bytearray()
        for i in range(rate*5):
            sec=i/rate
            age=(sec-.25 if role=="bass" else sec)%.5
            active=0<=age<.12
            value=round(8388607*amp*math.sin(2*math.pi*70*sec)) if active else 0
            out.extend(value.to_bytes(3,"little",signed=True))
            out.extend((-value if antiphase else value).to_bytes(3,"little",signed=True))
        w.writeframes(out)


class BassNoteOnsetAuditTests(unittest.TestCase):
    def test_bass_note_window_starts_at_real_offbeat_not_150ms_after_kick(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'kick.wav';b=Path(temp)/'bass.wav'
            write(a,role="kick");write(b,role="bass")
            v=evaluate_note_aligned_pocket(project(),a,b)
            bass=v["roles"]["bass"]["windows"]
            self.assertEqual(v["bass_timing_anchor"],"actual bass MIDI note-onset ticks")
            self.assertEqual(v["roles"]["bass"]["onsets_used"],8)
            self.assertGreater(bass["attack_0_40_ms"]["sub_25_90"]["power_median"],0)
            self.assertGreater(bass["body_40_140_ms"]["sub_25_90"]["power_median"],0)
            self.assertFalse(block_severe_native_source_faults(v)["hard_flags"])
            self.assertIsNone(block_severe_native_source_faults(v)["musical_winner"])

    def test_joint_sub_and_body_attack_deficit_blocks_without_quality_claim(self):
        import copy
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'kick.wav';b=Path(temp)/'bass.wav'
            write(a,role="kick");write(b,role="bass")
            source=evaluate_note_aligned_pocket(project(),a,b)
            r=copy.deepcopy(source)
            r["between_role"]["bass_attack_0_40_ms_versus_kick_attack_sub_25_90_db"]=-34.742
            r["between_role"]["bass_attack_0_40_ms_versus_kick_attack_body_90_250_db"]=-48.44
            gate=block_severe_native_source_faults(r)
            self.assertIn("bass_onset_attack_severely_masked_by_kick",gate["hard_flags"])
            self.assertFalse(gate["eligible_for_more_context_review"])
            self.assertIsNone(gate["musical_winner"])
            # Low harmonic upper bass alone is not a hard fault if sub attacks.
            r["between_role"]["bass_attack_0_40_ms_versus_kick_attack_sub_25_90_db"]=-7.5
            self.assertNotIn("bass_onset_attack_severely_masked_by_kick",
                             block_severe_native_source_faults(r)["hard_flags"])

    def test_mono_cancellation_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'kick.wav';b=Path(temp)/'bass.wav'
            write(a,role="kick");write(b,role="bass",antiphase=True)
            v=evaluate_note_aligned_pocket(project(),a,b)
            f=block_severe_native_source_faults(v)
            self.assertFalse(f["eligible_for_more_context_review"])
            self.assertTrue(any("mono" in x for x in f["hard_flags"]))

    def test_mismatched_native_frames_and_invalid_section_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'kick.wav';b=Path(temp)/'bass.wav'
            write(a,role="kick");write(b,role="bass")
            with self.assertRaises(ValidationError):
                evaluate_note_aligned_pocket(project(),a,b,section='Unknown')
            with wave.open(str(b),"rb") as w:
                data=w.readframes(w.getnframes()-8)
            with wave.open(str(b),"wb") as w:
                w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000)
                w.writeframes(data)
            with self.assertRaises(ValidationError):
                evaluate_note_aligned_pocket(project(),a,b)


if __name__=='__main__':
    unittest.main()
