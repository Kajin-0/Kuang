"""Synthetic audio checks for contextual kick/bass/source-fit diagnostics."""
import math
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace

from kuang.house_source_fit import (_sub_interaction, _mono_sub_power,
    _kick_onsets, fit_diagnostics, FFT, RATE)
from kuang.schema import ValidationError


def tone(freq=60, amp=.12, *, inversion=False, stereo=False):
    frames=[]
    for i in range(FFT):
        v=amp*math.sin(2*math.pi*freq*i/RATE)
        frames.append((v, -v if stereo else v*(-1 if inversion else 1)))
    return frames


class SourceFitTests(unittest.TestCase):
    def test_fft_linear_sum_add_and_cancel(self):
        a=tone()
        constructive=_sub_interaction(a,a)
        opposite=[(-x,-y) for x,y in a]
        destructive=_sub_interaction(a,opposite)
        self.assertAlmostEqual(constructive[0]/constructive[1],2,delta=.02)
        self.assertLess(destructive[0]/destructive[1],1e-10)
        self.assertGreater(destructive[1],0)

    def test_mono_fold_down_is_power_not_single_channel_peak(self):
        normal=tone()
        stereo=tone(stereo=True)
        a,b=_mono_sub_power(normal)
        x,y=_mono_sub_power(stereo)
        self.assertAlmostEqual(a/b,1,delta=.02)
        self.assertLess(x/y,1e-10)

    def test_actual_midi_kick_onsets_and_time_conversion(self):
        # Native project-compatible minimal note objects, deliberately distinct
        # from any commercial reference track.
        notes=[SimpleNamespace(start=n*960) for n in range(12)]
        clip=SimpleNamespace(start=0, notes=notes)
        kick=SimpleNamespace(id="track-kick",clips=[clip])
        source=SimpleNamespace(tracks=[kick],ppq=960,tempo_bpm=120)
        region={"start_tick":0,"end_tick":12*960,
                "start_seconds":0,"end_seconds":6}
        ticks,samples=_kick_onsets(source,region)
        self.assertEqual(ticks[0],0)
        self.assertEqual(ticks[-1],11*960)
        self.assertEqual(samples[1],24000)

    def test_real_pcm_alignment_detects_cancellation_and_antiphase_mono(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def write(name, polarity, antiphase=False):
                path=root/(name+'.wav')
                frames=round(2.0*RATE)
                with wave.open(str(path),'wb') as w:
                    w.setnchannels(2);w.setsampwidth(3);w.setframerate(RATE)
                    payload=bytearray()
                    for i in range(frames):
                        value=round(.1*(2**23-1)*math.sin(2*math.pi*60*i/RATE)*polarity)
                        other=-value if antiphase else value
                        payload.extend(value.to_bytes(3,'little',signed=True))
                        payload.extend(other.to_bytes(3,'little',signed=True))
                    w.writeframes(payload)
                return path
            kick=write('kick',1)
            bass=write('bass',-1)
            chord=write('chords',1)
            full=write('fullmix',1,antiphase=True)
            notes=[SimpleNamespace(start=i*960) for i in range(4)]
            proj=SimpleNamespace(tracks=[SimpleNamespace(id='track-kick',clips=[
                SimpleNamespace(start=0,notes=notes)])],ppq=960,tempo_bpm=120)
            region={'start_tick':0,'end_tick':3840,'start_seconds':0.,'end_seconds':2.}
            e=fit_diagnostics(proj,region,kick,bass,chord,full)
            self.assertEqual(e['onset_count'],4)
            self.assertEqual(e['technical_status'],'MEASURED')
            self.assertLess(e['linear_sum_kick_bass_sub_interference_db'],-50)
            self.assertLess(e['full_mix_sub_mono_retention_db'],-50)
            self.assertIn('kick_bass_sub_destructive_summation',e['warnings'])
            self.assertIn('full_mix_sub_mono_folddown_loss',e['warnings'])
            self.assertEqual(e['perceptual_quality'],'NOT_EVALUATED')

    def test_rejects_invalid_audio_and_unsafe_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"wrong.wav"
            with wave.open(str(path),"wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(44100)
                w.writeframes(b"\x00"*88200)
            source=SimpleNamespace(tracks=[])
            region={"start_tick":0,"end_tick":8*960,
                    "start_seconds":0,"end_seconds":4}
            with self.assertRaises(ValidationError):
                fit_diagnostics(source,region,path,path,path,path)
            with self.assertRaises(ValidationError):
                _mono_sub_power([(0,0)]*100)
