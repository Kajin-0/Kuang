"""Pure deterministic gates for the opt-in private native pair audition."""
import math
import tempfile
import unittest
import wave
from pathlib import Path

from kuang import midi
from kuang.house_native_pair_audition import _clip, _gain_only, _variant
from kuang.house_template import template
from kuang.schema import ValidationError, state_hash, validate
from kuang.song import rules_plan


class HouseNativePairAuditionTests(unittest.TestCase):
    def test_original_score_is_unchanged_when_only_bass_instrument_changes(self):
        spec,_ = rules_plan('deep house in C minor 16 bars', 43)
        p,_=template(spec, profile='deep', include_pad=False)
        original=state_hash(p)
        old_midi=midi.export_bytes(p)

        def bass_only(q):
            bass=next(t for t in q.tracks if t.id=='track-bass')
            bass.instrument.parameters['soundcraft.level']=-14
            return q

        alt=_variant(p,bass_patch=bass_only)
        validate(alt)
        self.assertEqual(midi.export_bytes(alt),old_midi)
        self.assertEqual(state_hash(p), original)
        self.assertNotEqual(state_hash(alt), original)
        self.assertEqual([t.controls for t in alt.tracks], [t.controls for t in p.tracks])
        self.assertEqual([t.effects for t in alt.tracks], [t.effects for t in p.tracks])

    def test_wrong_role_or_rhythm_change_rejected(self):
        spec,_ = rules_plan('deep house in C minor 16 bars',43)
        p,_ = template(spec, profile='deep', include_pad=False)
        def wrong_role(q):
            next(t for t in q.tracks if t.id=='track-harmony').controls['mixer.gain_db']-=1
            return q
        with self.assertRaisesRegex(ValidationError,'changed timing, levels'):
            _variant(p,bass_patch=wrong_role)
        def wrong_note(q):
            next(t for t in q.tracks if t.id=='track-bass').clips[0].notes[0].pitch+=1
            return q
        with self.assertRaisesRegex(ValidationError,'modified MIDI'):
            _variant(p,bass_patch=wrong_note)

    def test_lossless_24bit_gain_and_window(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,c=[Path(d)/x for x in ('a.wav','b.wav','c.wav')]
            with wave.open(str(a),'wb') as w:
                w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000)
                pcm=(100000).to_bytes(3,'little',signed=True)*2
                w.writeframes(pcm*48000)
            _clip(a,b,start_seconds=.25,length_seconds=.5)
            with wave.open(str(b),'rb') as w:
                self.assertEqual(w.getnframes(),24000)
            _gain_only(b,c,-6.020599913279624)
            with wave.open(str(c),'rb') as w:
                data=w.readframes(1)
                self.assertEqual(int.from_bytes(data[:3],'little',signed=True),50000)
            with self.assertRaisesRegex(ValidationError,'outside WAV'):
                _clip(a,Path(d)/'bad.wav',start_seconds=.9,length_seconds=.5)

if __name__=='__main__':unittest.main()
