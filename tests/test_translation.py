import json
import tempfile
import unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from kuang.depth import note_fingerprints
from kuang.gestures import gesture_house
from kuang.lowend_audio import band_metrics
from kuang.midi import export_bytes
from kuang.schema import Lock,ValidationError,dumps,state_hash,validate
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import Engine,LockedError,Scope,SetParameter,replay
from kuang.translation import SOURCE_HASH,translation_house
from soundcraft_fake import CONTRACT
from loudness_vectors import write_vector
from tools.phase9_house import ROOT,SCRATCH,build,package,reference_report


class TranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.old=gesture_house();cls.p=translation_house(cls.old)

    def test_all_source_notes_clips_automation_sections_and_provenance_exact(self):
        p=self.p;validate(p)
        self.assertEqual(state_hash(self.old),SOURCE_HASH)
        self.assertEqual(note_fingerprints(self.old),note_fingerprints(p))
        self.assertEqual(p.automation,self.old.automation);self.assertEqual(p.sections,self.old.sections)
        self.assertEqual((p.version,p.bars,p.tempo_bpm,p.key_tonic,p.key_mode),('0.1',64,126,0,'minor'))
        self.assertEqual(p.metadata['song_spec'],self.old.metadata['song_spec'])
        self.assertEqual(p.metadata['arrangement_spec'],self.old.metadata['arrangement_spec'])
        self.assertEqual(len(p.sections),6)

    def test_deterministic_canonical_midi_and_no_source_mutation(self):
        old=dumps(self.old);q=translation_house(self.old)
        self.assertEqual(dumps(q),dumps(self.p));self.assertEqual(dumps(self.old),old)
        self.assertEqual(export_bytes(q),export_bytes(self.p))
        renamed=deepcopy(self.old);renamed.name=q.name
        self.assertEqual(export_bytes(q),export_bytes(renamed))

    def test_narrow_device_mix_changes_and_entire_pad_design_retained(self):
        for a,b in zip(self.old.tracks,self.p.tracks):
            self.assertEqual(a.clips,b.clips)
            if a.id not in ('track-kick','track-bass','track-harmony','track-arp'):self.assertEqual(a,b)
            self.assertEqual([e.id for e in a.effects],[e.id for e in b.effects])
            if a.id=='track-harmony':
                expected=deepcopy(a);expected.controls['mixer.pan']=-.48;expected.effects[0].parameters['soundcraft.low_mid_gain']=-3
                self.assertEqual(expected,b)
            if a.id=='track-arp':
                expected=deepcopy(a);expected.controls['mixer.pan']=.60;self.assertEqual(expected,b)

    def test_kick_decay_transient_settings_and_single_oscillator_bass_harmonics(self):
        k=next(t for t in self.p.tracks if t.id=='track-kick');b=next(t for t in self.p.tracks if t.id=='track-bass')
        self.assertEqual(k.instrument.parameters['soundcraft.kick_decay'],280)
        self.assertEqual(k.effects[1].parameters['soundcraft.attack'],8)
        self.assertEqual(k.effects[0].parameters['soundcraft.hpf_freq'],30)
        self.assertEqual(b.instrument.parameters['soundcraft.osc1_wave'],0)
        self.assertEqual(b.instrument.parameters['soundcraft.osc_mix'],0)
        self.assertEqual(b.instrument.parameters['synth.cutoff_hz'],650)
        self.assertEqual(b.instrument.parameters['soundcraft.amp_release'],28)
        for t in (k,b):self.assertEqual(t.controls['mixer.pan'],0)
        self.assertNotIn('soundcraft.kick_tune',k.instrument.parameters)

    def test_modified_or_locked_source_and_unsupported_native_units_fail_closed(self):
        q=deepcopy(self.old);q.tracks[0].clips[0].notes[0].velocity-=1
        with self.assertRaises(ValidationError):translation_house(q)
        q=deepcopy(self.old);q.locks.append(Lock('reviewed-lock','track-bass',None))
        with self.assertRaises(ValidationError):translation_house(q)
        a=SoundCraftAdapter('/bin/true');a._discovery=deepcopy(CONTRACT)
        for name in ('soundcraft-production-plugins.json','soundcraft-depth-plugins.json'):
            a._discovery['plugins'].update(json.loads((Path(__file__).parent/'fixtures'/name).read_text()))
        self.assertTrue(a.capabilities(self.p)['supported'])
        q=deepcopy(self.p);next(x for x in q.parameters if x.id=='soundcraft.high_mid_freq').unit='ms'
        self.assertFalse(a.capabilities(q)['supported'])

    def test_new_eq_control_edit_exact_replay_and_existing_locks(self):
        p=self.p;owner=p.tracks[0].effects[0].id;scope=Scope(['track-kick'],[],['soundcraft.high_mid_gain'],None,None)
        op=SetParameter('set_parameter',owner,'soundcraft.high_mid_gain',1)
        e=Engine(p);r=e.apply([op],scope,state_hash(p));expected=deepcopy(p)
        expected.tracks[0].effects[0].parameters['soundcraft.high_mid_gain']=1
        self.assertEqual(dumps(e.project),dumps(expected))
        self.assertEqual(dumps(replay(e.project,r,undo=True)),dumps(p))
        self.assertEqual(dumps(replay(p,r,undo=False)),dumps(expected))
        q=deepcopy(p);q.locks.append(Lock('eq-lock',owner,'soundcraft.high_mid_gain'))
        with self.assertRaises(LockedError):Engine(q).apply([op],scope,state_hash(q))


class TranslationPublicationTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    def test_symbolic_new_only_publication_no_audio_or_master_claim(self):
        out=self.root/'symbolic';r=build(out)
        self.assertFalse(r['native_verified']);self.assertFalse(r['human_listening']);self.assertFalse(r['master_native_editable'])
        self.assertEqual((out/'song.mid').read_bytes(),export_bytes(translation_house()))
        with self.assertRaises(ValidationError):build(out)
        with self.assertRaises(ValidationError):package(out)

    def test_failed_host_escape_and_package_drift_or_existing_zip_do_not_publish(self):
        with self.assertRaises(ValidationError):build(self.root/'failed',executable='/bin/true')
        self.assertFalse((self.root/'failed').exists())
        with self.assertRaises(ValidationError):build(ROOT.parent/'forbidden-phase9')
        out=self.root/'drift';out.mkdir();(out/'verification.json').write_text(json.dumps({'native_verified':True,'artifact_sha256':{'asset':'0'*64}}));(out/'asset').write_text('drift')
        with self.assertRaisesRegex(ValidationError,'drift'):package(out)
        archive=out/'phase9-house-listening.zip';archive.write_bytes(b'keep')
        with self.assertRaises(ValidationError):package(out)
        self.assertEqual(archive.read_bytes(),b'keep')

    def test_licensed_private_reference_interface_and_absolute_band_power(self):
        a,b=self.root/'a.wav',self.root/'b.wav';write_vector(a,'stereo-1k');write_vector(b,'two-level')
        with self.assertRaises(ValidationError):reference_report(a,b,self.root/'missing.json','','')
        r=reference_report(a,b,self.root/'reference.json','Original synthetic test','MIT')
        self.assertFalse(r['reference_audio_redistributed']);self.assertFalse(r['ideal_eq_curve_claim'])
        m=band_metrics(a,windows=2)
        self.assertGreater(m['band_power_fraction']['500_2000'],.99)
        self.assertEqual(len(m['windows']),2)
        self.assertAlmostEqual(m['band_mean_square']['500_2000'],.5*10**(-23/10),delta=1e-6)
        with self.assertRaises(ValidationError):band_metrics(a,first=-1)
