import math,tempfile,unittest,wave
from pathlib import Path
from kuang.house_sound_fingerprint import fingerprint,compatible_rhythm,VERSION
from kuang.house_bass_syncopation import inspect_bass_pocket
from kuang.house_template import template
from kuang.song import rules_plan
from kuang.schema import ValidationError

class FingerprintTests(unittest.TestCase):
    def test_structural_proxies_not_confused_with_quality(self):
        result={}
        for style in ("straight","deep","jackin","minimal"):
            s,_=rules_plan(style+" house in F minor, 32 bars, 124 bpm",17)
            p,_=template(s,profile=style,impact_pocket=True,groove_identity_v2=True)
            r=inspect_bass_pocket(p,section="Groove",bars=8)
            self.assertEqual(r["kick_quarter_coverage"],1.)
            self.assertGreater(r["bass_offbeat_onset_fraction"],.6)
            self.assertEqual(r["perceptual_groove_quality"],"NOT_EVALUATED")
            result[style]=r["bass_onsets_per_bar"]
        self.assertLess(result["minimal"],result["straight"])
    @staticmethod
    def wav(path,which):
        buf=bytearray()
        for i in range(48000):
            t=i/48000;phase=t%.5
            if which=="kick":
                amp=.16 if phase<.12 else 0.
                v=amp*math.sin(2*math.pi*62*t)
            else:
                amp=.13 if .20<=phase<.40 else 0.
                v=amp*(.8*math.sin(2*math.pi*72*t)+.2*math.sin(2*math.pi*180*t))
            n=round(v*8388607)
            buf+=int(n).to_bytes(3,"little",signed=True)*2
        with wave.open(str(path),"wb") as f:
            f.setframerate(48000);f.setsampwidth(3);f.setnchannels(2);f.writeframes(buf)
    def test_real_pcm_fingerprint_and_role_pair(self):
        with tempfile.TemporaryDirectory() as d:
            kick=Path(d)/"kick.wav";bass=Path(d)/"bass.wav"
            self.wav(kick,"kick");self.wav(bass,"bass")
            a=fingerprint(kick,duration_seconds=1.,windows=8)
            b=fingerprint(bass,duration_seconds=1.,windows=8)
            self.assertTrue(a["signal_present"])
            self.assertGreater(a["spectral_bands"]["sub_30_120"],.6)
            self.assertEqual(a,fingerprint(kick,duration_seconds=1.,windows=8))
            p=compatible_rhythm(a,b,{"version":"house-bass-syncopation-fingerprint-v1",
                  "bass_offbeat_onset_fraction":1.,
                  "bass_anticipation_fraction":0.,"kick_quarter_coverage":1.})
            self.assertIsNone(p["automatic_bass_boost_db"])
            self.assertEqual(p["perceptual_quality"],"NOT_EVALUATED")
            with self.assertRaises(ValidationError):fingerprint(bass,duration_seconds=15)
    def test_reject_incompatible_source(self):
        with self.assertRaises(ValidationError):
            compatible_rhythm({"version":VERSION,"signal_present":False},{},{})
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"wrong.wav"
            with wave.open(str(f),"wb") as w:
                w.setframerate(22050);w.setsampwidth(2);w.setnchannels(1)
                w.writeframes(b"\x00"*50000)
            with self.assertRaises(ValidationError):fingerprint(f)

if __name__=="__main__":unittest.main()

class BassAnticipationTests(unittest.TestCase):
    def test_bounded_musical_pickup_without_new_notes_or_mixer_change(self):
        from kuang.house_bass_syncopation import propose_phrase_pickups
        from kuang.schema import dumps
        s,_=rules_plan("straight house in F minor, 32 bars, 120 bpm",18)
        p,_=template(s,profile="straight",impact_pocket=True,groove_identity_v2=True)
        old=dumps(p)
        q,rec=propose_phrase_pickups(p,section="Groove",bars=8)
        self.assertEqual(dumps(p),old)
        self.assertEqual(rec["version"],"house-bass-phrase-anticipation-audition-v1")
        self.assertTrue(rec["kick_midi_unchanged"])
        self.assertEqual(sum(len(c.notes) for t in p.tracks for c in t.clips),
                         sum(len(c.notes) for t in q.tracks for c in t.clips))
    def test_invalid_params_closed(self):
        from kuang.house_bass_syncopation import propose_phrase_pickups
        s,_=rules_plan("straight house in F minor, 16 bars, 120 bpm",18)
        p,_=template(s,profile="straight",impact_pocket=True,groove_identity_v2=True)
        with self.assertRaises(ValidationError):
            propose_phrase_pickups(p,section="Groove",bars=17)
        with self.assertRaises(ValidationError):
            propose_phrase_pickups(p,section="Not valid")

