"""Synthetic attack/release controls and real SongSpec note-group evidence gates."""
from __future__ import annotations
import math
import tempfile
import unittest
import wave
from pathlib import Path

from kuang.house_full_arranger import arrange_full_song
from kuang.house_note_envelope_v1 import _note_onsets,native_note_envelope
from kuang.house_template import template
from kuang.schema import BAR,PPQ,ValidationError
from kuang.song import rules_plan


class HouseNoteEnvelopeV1Tests(unittest.TestCase):
    @staticmethod
    def project():
        plan,_=rules_plan("minimal house in C minor 32 bars 120 bpm",17)
        short,_=template(plan,profile="minimal",impact_pocket=True,groove_identity_v2=True)
        long,_=arrange_full_song(short,bars=128,profile="minimal",seed=17)
        return long

    @staticmethod
    def synthetic(path,kind,*,duration=16):
        frames=duration*48000
        buff=bytearray()
        # Synthetic 120 BPM 4-beat pattern: chord note onsets every 2s;
        # the stimulus makes attack shape measurable in the native PCM format.
        for n in range(frames):
            t=n/48000
            elapsed=(t-0.5)%2
            if t<.5 or elapsed>=.45:
                v=0.
            elif kind=="sharp":
                env=min(1.,elapsed/.008)
                v=.2*env*math.sin(2*math.pi*440*t)
            elif kind=="slow":
                env=min(1.,elapsed/.11)
                v=.2*env*math.sin(2*math.pi*440*t)
            else:raise ValueError(kind)
            x=round(max(-.99,min(.99,v))*8388607)
            buff.extend(x.to_bytes(3,"little",signed=True)*2)
        with wave.open(str(path),"wb") as f:
            f.setnchannels(2);f.setsampwidth(3);f.setframerate(48000)
            f.writeframes(buff)

    def test_project_event_groups_and_source_bounds(self):
        p=self.project()
        events,start,end=_note_onsets(p,"harmony","Groove A",bars=8)
        self.assertTrue(events)
        self.assertEqual(end-start,8*BAR)
        self.assertTrue(all(x["voices"]>=1 for x in events))
        with self.assertRaises(ValidationError):
            _note_onsets(p,"harmony","DoesNotExist",bars=8)
        with self.assertRaises(ValidationError):
            _note_onsets(p,"kick","Groove A",bars=8)

    def test_known_fast_and_slow_note_attack_are_distinguished(self):
        from kuang.schema import Clip,Note,validate
        p=self.project()
        section=next(sec for sec in p.sections if sec.name=="Groove A")
        harmony=next(t for t in p.tracks if t.id=="track-harmony")
        # Four genuinely isolated quarter-note gates at two-bar spacing.
        harmony.clips=[Clip("test-note-envelope","Isolated test chord",
            "midi",section.start,8*BAR,
            [Note("v-"+str(i),i*2*BAR+PPQ,PPQ,60,90,0)
             for i in range(4)],None)]
        validate(p)
        def render(path,attack):
            nframes=round(8*BAR/PPQ*60/p.tempo_bpm*48000)
            starts=[round((i*2*BAR/PPQ+1)*60/p.tempo_bpm*48000)
                    for i in range(4)]
            frames=bytearray()
            for k in range(nframes):
                e=0.
                for onset in starts:
                    d=(k-onset)/48000
                    if 0<=d<.5:
                        e=min(1.,d/attack)
                    elif .5<=d<.9:
                        e=math.exp(-(d-.5)/.07)
                    if e>0:break
                v=int(.2*e*math.sin(2*math.pi*440*k/48000)*8388607)
                frames+=v.to_bytes(3,"little",signed=True)*2
            with wave.open(str(path),"wb") as wav:
                wav.setnchannels(2);wav.setsampwidth(3);wav.setframerate(48000)
                wav.writeframes(frames)
        with tempfile.TemporaryDirectory() as d:
            sharp=Path(d)/"sharp.wav";slow=Path(d)/"slow.wav"
            render(sharp,.008);render(slow,.115)
            x=native_note_envelope(p,sharp,role="harmony",section="Groove A",bars=8)
            y=native_note_envelope(p,slow,role="harmony",section="Groove A",bars=8)
            self.assertTrue(x["evidence_sufficient"],x)
            self.assertTrue(y["evidence_sufficient"],y)
            self.assertGreaterEqual(y["median_attack_10_90_ms"]-
                                    x["median_attack_10_90_ms"],45)
            self.assertGreater(y["median_midi_onset_to_90pct_ms"],
                               x["median_midi_onset_to_90pct_ms"])
            self.assertTrue(x["release_evidence_sufficient"])
            self.assertTrue(y["release_evidence_sufficient"])
            self.assertTrue(x["qualified_release_events"]>=2)
            self.assertTrue(y["qualified_release_events"]>=2)

    def test_invalid_pcm_format_fails_closed(self):
        p=self.project()
        with tempfile.TemporaryDirectory() as d:
            with wave.open(str(Path(d)/"wrong.wav"),"wb") as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000)
                f.writeframes(b"\0"*96000)
            with self.assertRaises(ValidationError):
                native_note_envelope(p,Path(d)/"wrong.wav",role="harmony",section="Groove A",bars=8)

    def test_silent_real_format_report_does_not_invent_attack(self):
        p=self.project()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"silent.wav"
            with wave.open(str(path),"wb") as f:
                f.setnchannels(2);f.setsampwidth(3);f.setframerate(48000)
                f.writeframes(b"\0"*(48000*6*18))
            x=native_note_envelope(p,path,role="harmony",section="Groove A",bars=8)
            self.assertFalse(x["evidence_sufficient"])
            self.assertIsNone(x["median_attack_10_90_ms"])

if __name__=="__main__":
    unittest.main()


class ChordStrumGroupingTests(unittest.TestCase):
    def test_microstaggered_chord_is_one_onset_not_four(self):
        from kuang.house_note_envelope_v1 import _rollups
        chords={240:[(300,51)],245:[(300,55)],250:[(300,58)],255:[(300,60)],
                1680:[(300,51)],1685:[(300,55)],1690:[(300,58)],1695:[(300,60)]}
        merged=_rollups(chords,group_strummed_chords=True)
        self.assertEqual(len(merged),2)
        self.assertEqual([x["voices"] for x in merged],[4,4])
        self.assertEqual([x["max_strum_spread_ticks"] for x in merged],[15,15])
        self.assertEqual([x["duration_ticks"] for x in merged],[315,315])
        self.assertEqual(len(_rollups(chords)),8)

    def test_tight_separate_repeated_note_not_collapsed(self):
        from kuang.house_note_envelope_v1 import _rollups
        notes={240:[(130,60)],245:[(130,64)],250:[(130,60)]}
        merged=_rollups(notes,group_strummed_chords=True)
        self.assertEqual(len(merged),2)
        self.assertEqual(merged[0]["voices"],2)
        self.assertEqual(merged[1]["voices"],1)
        notes={240:[(130,60)],265:[(130,64)]}
        self.assertEqual(len(_rollups(notes,group_strummed_chords=True)),2)

    def test_existing_long_house_chords_are_4voice_clusters(self):
        p=HouseNoteEnvelopeV1Tests.project()
        events,_,_=_note_onsets(p,"harmony","Groove A",bars=8)
        self.assertGreaterEqual(len(events),6)
        self.assertTrue(all(x["voices"]>=2 for x in events[:5]),events[:5])
        self.assertTrue(all(x["max_strum_spread_ticks"]<=24 for x in events))
