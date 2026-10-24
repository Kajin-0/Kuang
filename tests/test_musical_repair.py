import math,tempfile,unittest,wave
from copy import deepcopy
from pathlib import Path
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house,zero_pitch_bend_operations
from kuang.harmonic_audit import context
from kuang.pitch_audio import hz,note_pitch,spectrum
from kuang.schema import ValidationError,Lock,dumps
from kuang.midi import export_bytes

SCRATCH=Path(__file__).resolve().parents[1]/'.local/phase15/tests'
def source():return split_house(atmosphere_house())[0]
class RepairTests(unittest.TestCase):
    def test_deterministic_exact_MIDI_and_all_original_source_sound_fields(self):
        p=source();before=dumps(p);a,r=repaired_house(p);b,s=repaired_house(p)
        self.assertEqual(dumps(a),dumps(b));self.assertEqual(r,s);self.assertEqual(dumps(p),before)
        self.assertEqual(export_bytes(a),export_bytes(p));self.assertEqual(sum(len(c.notes) for t in a.tracks for c in t.clips),1536)
        for t,u in zip(p.tracks,a.tracks):
            self.assertEqual((t.instrument,t.effects,t.controls,t.clips),(u.instrument,u.effects,u.controls,u.clips))
        self.assertEqual(a.automation,p.automation);self.assertEqual(a.sections,p.sections);self.assertEqual(a.metadata['song_spec'],p.metadata['song_spec'])
    def test_only_two_real_auxes_six_drums_route_no_extra_notes_or_voices(self):
        p,r=repaired_house(source());self.assertEqual(len(p.tracks),15)
        self.assertEqual(len([t for t in p.tracks if not t.output_master]),6)
        self.assertEqual(r['added_notes'],[]);self.assertEqual(r['voicing_changes'],[]);self.assertFalse(r['quality_upgrade_claimed'])
        self.assertFalse(any(t.instrument and t.instrument.plugin_ref.startswith('vst3:') for t in p.tracks))
    def test_reject_locked_already_routed_and_wrong_source_form(self):
        for mode in ('lock','routed','tempo'):
            p=source()
            if mode=='lock':p.locks=[Lock('lock',p.tracks[0].id,None)]
            if mode=='routed':p=repaired_house(p)[0]
            if mode=='tempo':p.tempo_bpm=125
            with self.assertRaises(ValidationError):repaired_house(p)
    def test_harmony_unchanged_but_measured_source_offset_exposes_outsiders(self):
        p=source();q,_=repaired_house(p);a=context(p)
        self.assertEqual(a,context(q));self.assertFalse(a['out_of_scale_note_records'])
        self.assertTrue(a['minor_second_or_seventh_windows']);self.assertFalse(a['minor_seconds_automatically_errors'])
        shifted=context(p,{'track-harmony':-2,'track-bass':-2,'track-lead':-2,'track-depth-pad':-2})
        self.assertTrue(shifted['out_of_scale_note_records']);self.assertNotEqual(a['interval_pair_ticks'],shifted['interval_pair_ticks'])
    def test_workaround_fails_for_unreviewed_or_empty_targets(self):
        with self.assertRaises(ValidationError):zero_pitch_bend_operations(source(),{})
        with self.assertRaises(ValidationError):zero_pitch_bend_operations(source(),{'track-bass':'missing'})

class PitchAudioTests(unittest.TestCase):
    def setUp(self):SCRATCH.mkdir(parents=True,exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=SCRATCH);self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def tone(self,note,shift=0,harmonic=0):
        path=self.root/f'{note}-{shift}-{harmonic}.wav';f=hz(note)*2**(shift/1200);raw=bytearray()
        for i in range(48000):
            v=.12*math.sin(2*math.pi*f*i/48000)+harmonic*math.sin(4*math.pi*f*i/48000)
            raw+=round(v*2**23).to_bytes(3,'little',signed=True)
        with wave.open(str(path),'wb') as w:w.setparams((1,3,48000,0,'NONE',''));w.writeframes(raw)
        return path
    def test_independent_frequency_estimators_across_register(self):
        for n in (36,51,55,58,62,63,65,67,84):
            r=note_pitch(self.tone(n),n,.1,.8)
            self.assertLess(abs(r['fft_cents']),1);self.assertLess(abs(r['period_cents']),1)
    def test_actual_shift_detected_not_assumed_from_midi_key(self):
        r=note_pitch(self.tone(67,-200),67,.1,.8)
        self.assertAlmostEqual(r['fft_cents'],-200,delta=1);self.assertAlmostEqual(r['period_cents'],-200,delta=1)
    def test_stronger_second_harmonic_not_mistaken_for_fundamental(self):
        r=note_pitch(self.tone(63,harmonic=.30),63,.1,.8)
        self.assertAlmostEqual(r['strongest_full_band_peak_hz'],2*hz(63),delta=.2)
        self.assertLess(abs(r['fft_cents']),1);self.assertLess(abs(r['period_cents']),1)
    def test_invalid_note_window_and_silence_fail_closed(self):
        for n in (-1,128,60.5):
            with self.assertRaises(ValidationError):hz(n)
        path=self.tone(60)
        for a,b in [(-1,.2),(.2,.21),(.5,2)]:
            with self.assertRaises(ValidationError):note_pitch(path,60,a,b)
        silent=self.root/'silent.wav'
        with wave.open(str(silent),'wb') as w:w.setparams((1,3,48000,0,'NONE',''));w.writeframes(bytes(48000*3))
        with self.assertRaises(ValidationError):note_pitch(silent,60,.1,.8)
    def test_polyphonic_peak_analysis_keeps_distinct_cm9_voices(self):
        path=self.root/'chord.wav';raw=bytearray();notes=(51,55,58,62)
        for i in range(48000):raw+=round(sum(.08*math.sin(2*math.pi*hz(n)*i/48000) for n in notes)*2**23).to_bytes(3,'little',signed=True)
        with wave.open(str(path),'wb') as w:w.setparams((1,3,48000,0,'NONE',''));w.writeframes(raw)
        peaks=spectrum(path,.1,.8)[2][:8]
        for n in notes:self.assertLess(min(abs(1200*math.log2(p['hz']/hz(n))) for p in peaks),1)
