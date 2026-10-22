import hashlib
import json
import math
import tempfile
import unittest
import wave
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from kuang.arrangement_audio import section_spectra
from kuang.depth import PAD_IDS, depth_house, note_fingerprints
from kuang.house_song import FORM, activity_map, arrange_house, control_changes, corrected_pads
from kuang.midi import export_bytes
from kuang.schema import BAR, PPQ, AutomationPoint, Lock, ValidationError, dumps, save, state_hash, validate
from kuang.song import decode, SongSpec, validate_spec
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import (AddAutomationPoints, Engine, LockedError, Scope,
                                ScopeError, SetParameter, replay)
from soundcraft_fake import CONTRACT
from tools.phase7_house import ROOT, SCRATCH, package, pad_preview, publish, song_build


class PadMixTests(unittest.TestCase):
    def test_exact_same_midi_and_every_non_pad_track_and_lane_unchanged(self):
        old=depth_house();before=dumps(old);p=corrected_pads(old)
        self.assertEqual(note_fingerprints(old),note_fingerprints(p))
        self.assertEqual(dumps(old),before)
        for a,b in zip(old.tracks,p.tracks):
            self.assertEqual(a.clips,b.clips)
            if a.id not in PAD_IDS:self.assertEqual(a,b)
        for a,b in zip(old.automation,p.automation):
            if a.target_id in PAD_IDS:
                self.assertEqual([x.value-6 for x in a.points],[x.value for x in b.points])
                self.assertEqual([x.id for x in a.points],[x.id for x in b.points])
            elif not a.id.startswith('depth-'):self.assertEqual(a,b)

    def test_calibrated_pad_level_longer_space_and_gentler_sound_design(self):
        old,new=depth_house(),corrected_pads()
        for a,b in zip(old.tracks[-2:],new.tracks[-2:]):
            self.assertEqual(b.controls['mixer.gain_db'],a.controls['mixer.gain_db']-6)
            self.assertGreater(b.instrument.parameters['soundcraft.amp_attack'],a.instrument.parameters['soundcraft.amp_attack'])
            self.assertLess(b.instrument.parameters['soundcraft.filter_env_amount'],a.instrument.parameters['soundcraft.filter_env_amount'])
            self.assertLess(b.instrument.parameters['soundcraft.amp_sustain'],a.instrument.parameters['soundcraft.amp_sustain'])
            for x,y in zip(a.effects,b.effects):
                if x.plugin_ref in ('soundcraft:chorus','soundcraft:phaser'):
                    self.assertLess(y.parameters['soundcraft.depth'],x.parameters['soundcraft.depth'])
                    self.assertLess(y.parameters['soundcraft.rate'],x.parameters['soundcraft.rate'])
                if x.plugin_ref.endswith('reverb'):
                    self.assertGreater(y.parameters['effect.wet'],x.parameters['effect.wet'])
                    self.assertTrue(1800<=y.parameters['soundcraft.decay_ms']<=3500)
                    self.assertGreaterEqual(y.parameters['soundcraft.low_cut'],500)
                    self.assertEqual(y.parameters['soundcraft.width'],.75)
        changes=control_changes(old,new)
        self.assertEqual(set(changes),{*PAD_IDS,'automation'})

    def test_source_drift_locks_and_arbitrary_snapshot_changes_fail_closed(self):
        p=depth_house();p.tracks[-2].controls['mixer.gain_db']-=1
        with self.assertRaises(ValidationError):corrected_pads(p)
        p=depth_house();p.locks.append(Lock('reviewed-lock',PAD_IDS[0],None))
        with self.assertRaises(ValidationError):corrected_pads(p)
        p=corrected_pads();p.metadata['unreviewed']='drift'
        with self.assertRaises(ValidationError):arrange_house(p)


class HouseArrangementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=corrected_pads();cls.p=arrange_house(cls.source)

    def test_exact_64_bar_form_and_stable_deterministic_bytes(self):
        p=self.p;validate(p)
        self.assertEqual(p.version,'0.1');self.assertEqual(p.bars,64)
        self.assertEqual((p.tempo_bpm,p.key_tonic,p.key_mode,p.ppq,p.time_signature),(126,0,'minor',960,[4,4]))
        self.assertEqual([(s.name,s.start//BAR,s.length//BAR) for s in p.sections],[(n,b,l) for _,n,b,l in FORM])
        q=arrange_house()
        self.assertEqual(dumps(p),dumps(q));self.assertEqual(export_bytes(p),export_bytes(q))
        self.assertEqual([t.id for t in p.tracks],[t.id for t in self.source.tracks])

    def test_main_drop_retains_every_original_motif_field_and_id(self):
        for old,new in zip(self.source.tracks,self.p.tracks):
            drop=[c for c in new.clips if 32*BAR<=c.start<48*BAR]
            self.assertEqual(len(drop),4)
            for a,b in zip(old.clips,drop):
                expected=deepcopy(a);expected.start+=32*BAR
                self.assertEqual(expected,b)
        kick=next(t for t in self.p.tracks if t.id=='track-kick')
        self.assertTrue(any(c.start+n.start==32*BAR and n.pitch==36 for c in kick.clips for n in c.notes))

    def test_entrances_breakdown_build_pickup_and_progressive_outro(self):
        p=self.p
        def notes(role,first,last):
            t=next(t for t in p.tracks if t.id=='track-'+role)
            return [n for c in t.clips for n in c.notes if first*BAR<=c.start+n.start<last*BAR]
        self.assertFalse(notes('bass',0,8));self.assertFalse(notes('lead',0,8))
        self.assertFalse(notes('kick',24,32));self.assertFalse(notes('bass',24,32))
        self.assertTrue(notes('depth-pad',24,32));self.assertTrue(notes('depth-air',24,32))
        self.assertEqual(len(notes('kick',20,24)),8)
        self.assertGreaterEqual(len([n for n in notes('snare',31,32) if n.pitch==38]),4)
        self.assertFalse(notes('lead',52,64));self.assertFalse(notes('depth-pad',56,64))
        self.assertFalse(notes('bass',60,64));self.assertEqual(len(notes('kick',60,64)),16)

    def test_sections_differ_in_actual_relative_note_patterns_and_activity(self):
        patterns=[]
        for s in self.p.sections:
            patterns.append(tuple((t.id,c.start+n.start-s.start,n.pitch,n.duration,n.velocity)
                for t in self.p.tracks for c in t.clips for n in c.notes if s.start<=c.start+n.start<s.start+s.length))
        self.assertEqual(len(set(patterns)),6)
        a=activity_map(self.p)
        self.assertEqual(sum(s['bars'] for s in a),64)
        total=sum(len(t['onsets']) for s in a for b in s['activity'] for t in b['tracks'].values())
        self.assertEqual(total,sum(len(c.notes) for t in self.p.tracks for c in t.clips))
        self.assertTrue(all(t['sounding_notes']>=len(t['onsets']) for s in a for b in s['activity'] for t in b['tracks'].values()))

    def test_diatonic_notes_boundaries_and_valid_unchanged_source_songspec(self):
        p=self.p;validate(p)
        spec=validate_spec(decode(SongSpec,json.loads(p.metadata['song_spec'])))
        self.assertEqual(spec.bars,16)
        self.assertEqual(p.metadata['song_spec'],self.source.metadata['song_spec'])
        self.assertEqual(json.loads(p.metadata['arrangement_spec'])['bars'],64)
        for t in p.tracks:
            for c in t.clips:
                for n in c.notes:
                    self.assertLessEqual(n.start+n.duration,c.length)
                    if n.channel!=9:self.assertIn(n.pitch%12,{0,2,3,5,7,8,10})
        origin=json.loads(p.metadata['arrangement_origin_notes'])
        self.assertEqual(sum(k==v for k,v in origin.items()),548)

    def test_native_fx_lanes_units_and_existing_low_end_sound_preserved(self):
        a=SoundCraftAdapter('/bin/true');a._discovery=deepcopy(CONTRACT)
        for name in ('soundcraft-production-plugins.json','soundcraft-depth-plugins.json'):
            a._discovery['plugins'].update(json.loads((Path(__file__).parent/'fixtures'/name).read_text()))
        self.assertTrue(a.capabilities(self.p)['supported'])
        for role in ('kick','bass'):
            old=next(t for t in self.source.tracks if t.id=='track-'+role)
            new=next(t for t in self.p.tracks if t.id==old.id)
            self.assertEqual((old.controls,old.instrument,old.effects),(new.controls,new.instrument,new.effects))
        for lane in self.p.automation:
            self.assertEqual(lane.points[0].tick,0);self.assertEqual(lane.points[-1].tick,self.p.length)
            self.assertTrue(all(x.shape=='linear' for x in lane.points))
            self.assertFalse(lane.target_id.startswith('instrument-'))
        bad=deepcopy(self.p);bad.tracks[-2].effects[2].parameters['soundcraft.feedback']=.99
        self.assertFalse(a.capabilities(bad)['supported'])
        bad=asdict(self.p);bad['parameters'][-1]['unit']='cents'
        from kuang.schema import Project
        with self.assertRaises(ValidationError):decode(Project,bad)

    def test_scoped_pad_edit_lane_edit_locks_and_exact_receipt_replay(self):
        p=corrected_pads();op=SetParameter('set_parameter','effect-depth-pad-plate','effect.wet',.4)
        engine=Engine(p);scope=Scope([PAD_IDS[0]],[],['effect.wet'],None,None)
        r=engine.apply([op],scope,state_hash(p));expected=deepcopy(p)
        expected.tracks[-2].effects[-1].parameters['effect.wet']=.4
        self.assertEqual(dumps(engine.project),dumps(expected))
        self.assertEqual(dumps(replay(engine.project,r,undo=True)),dumps(p))
        self.assertEqual(dumps(replay(p,r,undo=False)),dumps(expected))
        with self.assertRaises(ScopeError):Engine(p).apply([op],Scope(['track-bass'],[],['effect.wet'],None,None),state_hash(p))
        p.locks.append(Lock('pad-locked',PAD_IDS[0],None))
        with self.assertRaises(LockedError):Engine(p).apply([op],scope,state_hash(p))
        p=deepcopy(self.p);lane=next(x for x in p.automation if x.id=='song-lead-pan')
        op=AddAutomationPoints('add_automation_points',lane.id,[AutomationPoint('reviewed-pan',240,-.2,'linear')])
        e=Engine(p);r=e.apply([op],Scope(['track-lead'],[],['mixer.pan'],0,PPQ),state_hash(p))
        self.assertEqual(dumps(replay(e.project,r,undo=True)),dumps(p))


class SongPublicationTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=SCRATCH);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_symbolic_pad_and_song_reproduction_with_no_false_audio_evidence(self):
        a,b=self.root/'pads',self.root/'song'
        pr=pad_preview(a);r=song_build(b,source=a)
        self.assertFalse(pr['native_verified']);self.assertFalse(r['native_verified'])
        self.assertFalse(r['human_listening']);self.assertFalse(r['club_ready'])
        self.assertEqual((b/'song.mid').read_bytes(),export_bytes(arrange_house()))
        self.assertTrue((b/'activity.json').exists());self.assertFalse((b/'C-phase7-house-64bars.wav').exists())
        with self.assertRaises(ValidationError):pad_preview(a)
        empty=self.root/'empty';empty.mkdir()
        with self.assertRaises(ValidationError):song_build(empty)
        self.assertEqual(list(empty.iterdir()),[])

    def test_failed_host_and_escaped_symlink_paths_publish_nothing(self):
        source=self.root/'source';source.mkdir();save(depth_house(),source/'project.kuang.json')
        out=self.root/'failed'
        with self.assertRaises(ValidationError):pad_preview(out,source=source,executable=str(self.root/'absent'))
        self.assertFalse(out.exists())
        with self.assertRaises(ValidationError):song_build(out,executable='/bin/true')
        with self.assertRaises(ValidationError):pad_preview(ROOT.parent/'forbidden-phase7')
        link=self.root/'link';link.symlink_to(source)
        with self.assertRaises(ValidationError):pad_preview(link)

    def test_publication_race_preserves_other_writer(self):
        stage=self.root/'stage';stage.mkdir();(stage/'ours').write_text('ours')
        out=self.root/'race';out.mkdir();(out/'keep').write_text('other writer')
        with self.assertRaises(FileExistsError):publish(stage,out)
        self.assertEqual((out/'keep').read_text(),'other writer');self.assertTrue((stage/'ours').is_file())

    def test_zip_requires_real_proof_and_rejects_drift_and_existing_output(self):
        for name in ('pad-fix','song'):
            r=self.root/name;r.mkdir()
            (r/'verification.json').write_text(json.dumps({'native_verified':False}))
        with self.assertRaises(ValidationError):package(self.root)
        self.assertFalse((self.root/'phase7-house-listening.zip').exists())
        for name in ('pad-fix','song'):
            r=self.root/name;(r/'project.kuang.json').write_text('changed')
            (r/'verification.json').write_text(json.dumps({'native_verified':True,'artifact_sha256':{'project.kuang.json':hashlib.sha256(b'original').hexdigest()}}))
        with self.assertRaisesRegex(ValidationError,'drift'):package(self.root)
        archive=self.root/'phase7-house-listening.zip';archive.write_bytes(b'keep')
        with self.assertRaises(ValidationError):package(self.root)
        self.assertEqual(archive.read_bytes(),b'keep')


class SectionAudioTests(unittest.TestCase):
    def test_section_bands_follow_known_changed_pcm_and_invalid_regions_fail(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            path=Path(d)/'bands.wav'
            with wave.open(str(path),'wb') as w:
                w.setparams((2,3,48000,0,'NONE','not compressed'))
                w.writeframes(b''.join(round(.3*math.sin(2*math.pi*(93.75 if i<12000 else 3000)*i/48000)*(2**23-1)).to_bytes(3,'little',signed=True)*2 for i in range(24000)))
            m=section_spectra(path,[('sub',0,.25),('presence',.25,.5)])['sections']
            self.assertGreater(m['sub']['band_power_fraction']['sub_20_120'],.99)
            self.assertGreater(m['presence']['band_power_fraction']['presence_2000_8000'],.99)
            for regions in ([('x',0,.25),('x',.25,.5)],[('x',0,.001)],[('x',-.1,.5)]):
                with self.assertRaises(ValidationError):section_spectra(path,regions)
