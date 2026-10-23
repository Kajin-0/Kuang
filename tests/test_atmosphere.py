import json
import math
import tempfile
import unittest
import wave
from copy import deepcopy
from pathlib import Path

from kuang.atmosphere import PULSE_ID,SOURCE_HASH,atmosphere_house
from kuang.atmosphere_audio import pulse_windows,reference_guide,sample_steps,speaker_approx,sub_power
from kuang.depth import PAD_IDS,note_fingerprints
from kuang.midi import export_bytes
from kuang.schema import BAR,PPQ,Lock,ValidationError,dumps,state_hash,validate
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import Engine,LockedError,Scope,SetParameter,replay
from kuang.translation import translation_house
from soundcraft_fake import CONTRACT
from tools.phase10_house import ROOT,SCRATCH,build,package,wet_dry


class AtmosphereTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=translation_house();cls.b=atmosphere_house(cls.old,space=False)
        cls.c=atmosphere_house(cls.old,pulse=False);cls.d=atmosphere_house(cls.old)

    def test_exact_original_notes_clips_form_tempo_key_and_provenance(self):
        p=self.d;validate(p);self.assertEqual(state_hash(self.old),SOURCE_HASH)
        self.assertEqual((p.version,p.bars,p.tempo_bpm,p.key_tonic,p.key_mode),('0.1',64,126,0,'minor'))
        self.assertEqual(p.sections,self.old.sections)
        for k,v in note_fingerprints(self.old).items():self.assertEqual(note_fingerprints(p)[k],v)
        self.assertEqual(sum(len(c.notes) for t in self.old.tracks for c in t.clips),1446)
        self.assertEqual(p.metadata['song_spec'],self.old.metadata['song_spec'])
        self.assertEqual(p.metadata['arrangement_spec'],self.old.metadata['arrangement_spec'])

    def test_causal_variants_and_deterministic_bytes_without_source_mutation(self):
        before=dumps(self.old)
        self.assertEqual(dumps(atmosphere_house(self.old,space=False,pulse=False)),before)
        self.assertEqual(self.b.tracks[:-1],self.old.tracks)
        self.assertEqual(self.d.tracks[:-1],self.c.tracks)
        self.assertEqual(self.d.tracks[-1],self.b.tracks[-1])
        self.assertEqual(dumps(self.d),dumps(atmosphere_house()))
        self.assertEqual(export_bytes(self.d),export_bytes(atmosphere_house()))
        self.assertEqual(dumps(self.old),before)
        renamed=deepcopy(self.old);renamed.name=self.c.name
        self.assertEqual(export_bytes(self.c),export_bytes(renamed))

    def test_sine_pitch_roots_timing_release_gaps_and_pruned_turnaround(self):
        p=self.d;t=p.tracks[-1]
        self.assertEqual(t.id,PULSE_ID);self.assertEqual(t.controls['mixer.pan'],0)
        self.assertEqual(t.instrument.parameters['soundcraft.osc1_wave'],2/3)
        self.assertEqual(t.instrument.parameters['soundcraft.osc2_wave'],2/3)
        self.assertEqual(t.instrument.parameters['soundcraft.osc_mix'],0)
        self.assertEqual(t.instrument.parameters['synth.resonance'],0)
        self.assertEqual(t.effects[0].parameters['soundcraft.hpf_freq'],30)
        self.assertEqual(t.effects[1].parameters,{'effect.bypass':0,'soundcraft.type':4/6,'soundcraft.freq':140})
        bass=next(t for t in self.old.tracks if t.id=='track-bass')
        events=sorted((c.start+n.start,n.pitch) for c in bass.clips for n in c.notes)
        notes=[(c,n) for c in t.clips for n in c.notes];self.assertEqual(len(notes),90)
        for c,n in notes:
            at=c.start+n.start
            self.assertIn(c.start//BAR,[*range(8,16),*range(32,48)])
            self.assertEqual(n.start%PPQ,592);self.assertEqual(n.duration,180)
            self.assertEqual(n.pitch,max((tick,pitch) for tick,pitch in events if c.start<=tick<=at)[1])
            self.assertNotEqual(n.pitch,34)
            self.assertGreater((PPQ-(n.start%PPQ+n.duration))/PPQ*60000/126-24,60)
        self.assertEqual(sum(len(c.notes) for t in p.tracks for c in t.clips),1536)

    def test_pad_gain_lanes_and_all_old_automation_identities_preserved(self):
        p=self.d
        edited={'effect-depth-pad-plate','effect-depth-air-plate','effect-depth-lead-plate',
                'effect-arp-room','effect-lead-delay','effect-arp-delay'}
        for old,new in zip(self.old.automation,p.automation):
            self.assertEqual((old.id,old.target_id,old.parameter_id),(new.id,new.target_id,new.parameter_id))
            self.assertEqual([(x.id,x.tick,x.shape) for x in old.points],[(x.id,x.tick,x.shape) for x in new.points])
            if old.target_id not in edited or old.parameter_id!='effect.wet':self.assertEqual(old,new)
        for name in PAD_IDS:
            a=next(t for t in self.old.tracks if t.id==name);b=next(t for t in p.tracks if t.id==name)
            self.assertEqual(a.controls['mixer.gain_db'],b.controls['mixer.gain_db'])
            for key in ('soundcraft.osc1_wave','soundcraft.osc2_wave','soundcraft.osc_mix'):
                self.assertEqual(a.instrument.parameters[key],b.instrument.parameters[key])
            self.assertGreater(b.instrument.parameters['soundcraft.amp_release'],a.instrument.parameters['soundcraft.amp_release'])
        for name in ('track-kick','track-bass','track-snare','track-hats','track-percussion'):
            self.assertEqual(next(t for t in self.old.tracks if t.id==name),next(t for t in p.tracks if t.id==name))

    def test_fx_order_tempo_delays_decay_and_control_same_input(self):
        for name in PAD_IDS:
            a=next(t for t in self.old.tracks if t.id==name);b=next(t for t in self.d.tracks if t.id==name)
            old_ids=[e.id for e in a.effects]
            self.assertEqual([e.id for e in b.effects if e.id in old_ids],old_ids)
            delay=next(e for e in b.effects if e.plugin_ref=='soundcraft:mod_delay')
            self.assertAlmostEqual(delay.parameters['soundcraft.time'],60000/126*(.75 if name==PAD_IDS[1] else 1))
            self.assertEqual(delay.parameters['soundcraft.mod_depth'],0)
            self.assertTrue(2000<=b.effects[-1].parameters['soundcraft.decay_ms']<=4000)
            self.assertGreaterEqual(b.effects[-1].parameters['soundcraft.low_cut'],500)
        dry=wet_dry(self.d,PAD_IDS)
        self.assertEqual(note_fingerprints(dry),note_fingerprints(self.d))
        for a,b in zip(dry.tracks,self.d.tracks):self.assertEqual(a.instrument,b.instrument);self.assertEqual(a.controls,b.controls)

    def test_actual_eq1_choice_units_discovery_and_rejections(self):
        a=SoundCraftAdapter('/bin/true');a._discovery=deepcopy(CONTRACT)
        for name in ('soundcraft-production-plugins.json','soundcraft-depth-plugins.json','soundcraft-pulse-eq1.json'):
            a._discovery['plugins'].update(json.loads((Path(__file__).parent/'fixtures'/name).read_text()))
        self.assertTrue(a.capabilities(self.d)['supported'])
        bad=deepcopy(self.d);bad.tracks[-1].effects[-1].parameters['soundcraft.type']=.25
        self.assertFalse(a.capabilities(bad)['supported'])
        bad=deepcopy(self.d);next(x for x in bad.parameters if x.id=='soundcraft.freq').unit='ms'
        self.assertFalse(a.capabilities(bad)['supported'])

    def test_drift_locks_and_non_boolean_options_fail_closed(self):
        p=deepcopy(self.old);p.metadata['unreviewed']='drift'
        with self.assertRaises(ValidationError):atmosphere_house(p)
        p=deepcopy(self.old);p.locks.append(Lock('user-pad-lock',PAD_IDS[0],None))
        with self.assertRaises(ValidationError):atmosphere_house(p)
        for space,pulse in ((1,True),(True,'yes')):
            with self.assertRaises(ValidationError):atmosphere_house(space=space,pulse=pulse)

    def test_legitimate_lowpass_edit_exact_receipt_replay_and_locks(self):
        p=self.d;owner=p.tracks[-1].effects[-1].id
        op=SetParameter('set_parameter',owner,'soundcraft.freq',135)
        scope=Scope([PULSE_ID],[],['soundcraft.freq'],None,None);e=Engine(p)
        receipt=e.apply([op],scope,state_hash(p));expected=deepcopy(p)
        expected.tracks[-1].effects[-1].parameters['soundcraft.freq']=135
        self.assertEqual(dumps(e.project),dumps(expected))
        self.assertEqual(dumps(replay(e.project,receipt,undo=True)),dumps(p))
        self.assertEqual(dumps(replay(p,receipt,undo=False)),dumps(expected))
        q=deepcopy(p);q.locks.append(Lock('lowpass-lock',owner,'soundcraft.freq'))
        with self.assertRaises(LockedError):Engine(q).apply([op],scope,state_hash(q))


class AtmospherePublicationTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    def test_symbolic_variants_do_not_claim_audio_or_master_success(self):
        out=self.root/'symbolic';r=build(out)
        self.assertFalse(r['native_verified']);self.assertFalse(r['human_listening']);self.assertFalse(r['master_native_editable'])
        self.assertEqual((out/'song.mid').read_bytes(),export_bytes(atmosphere_house()))
        self.assertTrue(r['original_notes_exact'])
        with self.assertRaises(ValidationError):build(out)
        with self.assertRaises(ValidationError):package(out)

    def test_failed_host_escape_and_corrupt_package_preserve_inputs(self):
        out=self.root/'failed'
        with self.assertRaises(ValidationError):build(out,executable='/bin/true')
        self.assertFalse(out.exists())
        with self.assertRaises(ValidationError):build(ROOT.parent/'forbidden-phase10')
        out=self.root/'drift';out.mkdir();(out/'asset').write_bytes(b'drift')
        (out/'verification.json').write_text(json.dumps({'native_verified':True,'artifact_sha256':{'asset':'0'*64}}))
        with self.assertRaisesRegex(ValidationError,'drift'):package(out)
        archive=out/'phase10-house-listening.zip';archive.write_bytes(b'keep')
        with self.assertRaises(ValidationError):package(out)
        self.assertEqual(archive.read_bytes(),b'keep')

    def test_numeric_guide_is_data_and_does_not_change_composition(self):
        guide={'purpose':'Directional data only','comparison':'Different arrangement; no audio redistribution',
            'suno':{'integrated_lufs_approx':-15.1,'stereo_correlation_approx':.937,'high_band_side_fraction_above_500Hz_approx':.142},
            'kuang_phase8':{'integrated_lufs_approx':-25.6,'stereo_correlation_approx':.985,'high_band_side_fraction_above_500Hz_approx':.025}}
        path=self.root/'guide.json';path.write_text(json.dumps(guide));r=reference_guide(path)
        self.assertFalse(r['source_audio_used']);self.assertFalse(r['loudness_target'])
        for key,value in (('audio','base64-data'),('suno',{'stereo_correlation_approx':'run code'})):
            path.write_text(json.dumps({**guide,key:value}))
            with self.assertRaises(ValidationError):reference_guide(path)


class AtmosphereAudioTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    def tone(self,name,frequency,amplitude=.1):
        p=self.root/name
        with wave.open(str(p),'wb') as w:
            w.setparams((2,3,48000,0,'NONE','not compressed'))
            w.writeframes(b''.join(round(amplitude*math.sin(2*math.pi*frequency*i/48000)*(2**23-1)).to_bytes(3,'little',signed=True)*2 for i in range(57600)))
        return p

    def test_speaker_highpass_attenuates_low_tone_and_preserves_high_band(self):
        low,high=self.tone('low.wav',40),self.tone('high.wav',1000)
        a,b=speaker_approx(low),speaker_approx(high,self.root/'high-HP.wav')
        self.assertGreater(b['rms_dbfs']-a['rms_dbfs'],30)
        self.assertAlmostEqual(b['rms_dbfs'],20*math.log10(.1/math.sqrt(2)),delta=.1)
        self.assertFalse(b['production_processing'])
        with self.assertRaises(ValidationError):speaker_approx(high,self.root/'high-HP.wav')
        with self.assertRaises(ValidationError):speaker_approx(high,cutoff=20)

    def test_sub_power_has_absolute_window_units_and_step_audit(self):
        low=self.tone('40.wav',40);high=self.tone('1k.wav',1000)
        a,b=sub_power(low,1.2),sub_power(high,1.2)
        self.assertAlmostEqual(a['mean_square'],.005,delta=.0001)
        self.assertLess(b['mean_square'],1e-9);self.assertEqual(len(a['windows']),16)
        steps=sample_steps(low);self.assertLess(steps['maximum_adjacent_sample_step'],.001)

    def test_local_pulse_gate_detects_cancellation_in_actual_pcm(self):
        off=self.tone('off.wav',65,.1);on=self.tone('on.wav',65,.08)
        r=pulse_windows(on,off,beats=2)
        self.assertAlmostEqual(r['minimum_db'],20*math.log10(.8),delta=.001)
        self.assertEqual(len(r['absolute_windows']),2)
