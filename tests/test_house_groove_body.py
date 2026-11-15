import unittest
import math
import tempfile
import wave
from pathlib import Path
from types import SimpleNamespace
from kuang.house_groove_body import compare_bass_sources,upper_body_audition_gate,groove_body,VERSION
from kuang.schema import ValidationError

def receipt(sub=0,mid=0,late=0):
    return {"version":VERSION,"kick_onsets_used":8,"bands":{
        "sub_25_90":{"bass_early_vs_kick_db":sub,"bass_late_vs_kick_db":sub+late,"bass_late_vs_early_db":late},
        "body_90_250":{"bass_early_vs_kick_db":mid,"bass_late_vs_kick_db":mid+late,"bass_late_vs_early_db":late}}}

class BassBodyTests(unittest.TestCase):
    @staticmethod
    def _pcm(path,kind):
        # Eight identical, independently authored onsets; different candidate
        # upper-bass harmonics but same original bass MIDI and rhythmic timing.
        with wave.open(str(path),"wb") as w:
            w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000)
            buf=bytearray()
            for i in range(48000*4):
                sec=i/48000
                phase=sec%.5
                if kind=="kick":
                    amp=.12 if 0<=phase<.1 else 0
                    sample=amp*(.7*math.sin(2*math.pi*65*sec)+.3*math.sin(2*math.pi*180*sec))
                else:
                    amp=.10 if .15<=phase<.35 else 0
                    high=.08 if kind=="original" else .62
                    sample=amp*((1-high)*math.sin(2*math.pi*65*sec)+
                                high*math.sin(2*math.pi*180*sec))
                val=max(-8388608,min(8388607,round(sample*8388608)))
                buf.extend(val.to_bytes(3,"little",signed=True)*2)
            w.writeframes(buf)

    def test_real_native_pcm_kick_bass_source_windows(self):
        with tempfile.TemporaryDirectory() as d:
            kick=Path(d)/"kick.wav";original=Path(d)/"old.wav";alternate=Path(d)/"new.wav"
            for name,p in [("kick",kick),("original",original),("alternate",alternate)]:
                self._pcm(p,name)
            c=SimpleNamespace(start=0,notes=[SimpleNamespace(start=i*960) for i in range(8)])
            project=SimpleNamespace(ppq=960,tempo_bpm=120,tracks=[SimpleNamespace(
                id="track-kick",clips=[c])])
            section={"start_tick":0,"end_tick":8*960,
                     "start_seconds":0.,"end_seconds":4.}
            a=groove_body(project,section,kick,original)
            b=groove_body(project,section,kick,alternate)
            self.assertEqual(a["kick_onsets_used"],8)
            comparison=compare_bass_sources(a,b)
            self.assertGreater(
                comparison["bands"]["body_90_250"]["early_bass_vs_kick_delta_db"],5)
            self.assertIsNone(comparison["automatic_winner"])
            with wave.open(str(alternate),"rb") as src:
                frames=src.readframes(src.getnframes()-100)
            shorter=Path(d)/"short.wav"
            with wave.open(str(shorter),"wb") as dst:
                dst.setnchannels(2);dst.setsampwidth(3);dst.setframerate(48000)
                dst.writeframes(frames)
            with self.assertRaises(ValidationError):
                groove_body(project,section,kick,shorter)

    def test_delta_independent_of_key_or_source_names(self):
        a=receipt(-8,-14,-6);b=receipt(-10,-4,1)
        r=compare_bass_sources(a,b)
        self.assertEqual(r["bands"]["body_90_250"]["late_bass_vs_kick_delta_db"],17)
        self.assertEqual(r["bands"]["sub_25_90"]["early_bass_vs_kick_delta_db"],-2)
        self.assertIsNone(r["automatic_winner"])
        self.assertEqual(r,compare_bass_sources(a,b))
    def test_candidate_gate_conserves_compute_without_forcing_selection(self):
        gate=upper_body_audition_gate({"mid_fraction":.21},{"mid_fraction":.49})
        self.assertTrue(gate["audition_warranted"])
        self.assertFalse(gate["automatic_source_swap"])
        close=upper_body_audition_gate({"mid_fraction":.16},{"mid_fraction":.154})
        self.assertFalse(close["audition_warranted"])
        for bad in [-1,float("nan"),float("inf"),1.2,".4"]:
            with self.subTest(bad=bad),self.assertRaises(ValidationError):
                upper_body_audition_gate({"mid_fraction":.16},{"mid_fraction":bad})

    def test_rejects_bad_receipts(self):
        with self.assertRaises(ValidationError):compare_bass_sources({},receipt())
        x=receipt();x["kick_onsets_used"]=7
        with self.assertRaises(ValidationError):compare_bass_sources(x,receipt())

if __name__=="__main__":unittest.main()
