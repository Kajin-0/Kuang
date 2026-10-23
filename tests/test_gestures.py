import json
import math
import tempfile
import unittest
import wave
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from kuang.depth import note_fingerprints
from kuang.gesture_audio import gain_reduction_envelope, phase_gain, window_metrics
from kuang.gestures import HARMONICS, PADS, SOURCE_HASH, control, crop, gesture_house, lane_value
from kuang.house_song import arrange_house
from kuang.midi import export_bytes
from kuang.schema import (BAR, PPQ, AutomationPoint, Lock, ValidationError,
                          dumps, state_hash, validate)
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import AddAutomationPoints, Engine, LockedError, Scope, replay
from soundcraft_fake import CONTRACT
from tools.phase8_house import ROOT, SCRATCH, build, package


class GestureCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.old=arrange_house();cls.p=gesture_house(cls.old)

    def test_exact_source_form_key_midi_and_determinism(self):
        self.assertEqual(state_hash(self.old),SOURCE_HASH)
        p=self.p;validate(p)
        self.assertEqual((p.version,p.bars,p.tempo_bpm,p.key_tonic,p.key_mode),('0.1',64,126,0,'minor'))
        self.assertEqual(p.sections,self.old.sections);self.assertEqual(len(p.sections),6)
        self.assertEqual(dumps(p),dumps(gesture_house()))
        self.assertEqual(export_bytes(p),export_bytes(gesture_house()))
        self.assertEqual(p.metadata['song_spec'],self.old.metadata['song_spec'])
        self.assertEqual(p.metadata['arrangement_spec'],self.old.metadata['arrangement_spec'])

    def test_all_note_fields_unchanged_except_five_explicit_percussion_removals(self):
        changes=json.loads(self.p.metadata['gesture_note_deviations']);self.assertEqual(len(changes),5)
        removed={x['removed']['id'] for x in changes}
        self.assertEqual(len(removed),5)
        for a,b in zip(self.old.tracks,self.p.tracks):
            expected=deepcopy(a.clips)
            for c in expected:c.notes=[n for n in c.notes if n.id not in removed]
            self.assertEqual(expected,b.clips)
            for c in b.clips:
                for n in c.notes:
                    if 32*BAR<=c.start<48*BAR:
                        self.assertTrue(n.id.startswith(('pocket-','depth-')))
        for x in changes:
            self.assertIn(x['track'],('track-snare','track-hats','track-percussion'))
            self.assertTrue(32*BAR-PPQ<=x['absolute_tick']<32*BAR)
        for role in ('kick','bass','lead'):
            self.assertEqual(note_fingerprints(self.p)['track-'+role],note_fingerprints(self.old)['track-'+role])

    def test_low_end_devices_controls_and_every_automation_point_preserved(self):
        for role in ('kick','bass'):
            a=next(t for t in self.old.tracks if t.id=='track-'+role)
            b=next(t for t in self.p.tracks if t.id==a.id)
            self.assertEqual(a,b)
            owners={a.id,*(e.id for e in a.effects)}
            self.assertEqual([x for x in self.old.automation if x.target_id in owners],
                             [x for x in self.p.automation if x.target_id in owners])

    def test_source_drift_locks_rejected_without_mutation(self):
        q=deepcopy(self.old);q.tracks[0].clips[0].notes[0].velocity-=1
        before=dumps(q)
        with self.assertRaises(ValidationError):gesture_house(q)
        self.assertEqual(dumps(q),before)
        q=deepcopy(self.old);q.locks.append(Lock('user-lock','track-lead',None))
        with self.assertRaises(ValidationError):gesture_house(q)

    def test_cutoff_sweeps_real_hz_ranges_reset_on_drop_and_static_choices(self):
        p=self.p
        for role in ('harmony','lead','arp','snare'):
            hp=next(a for a in p.automation if a.id=='gesture-'+role+'-hpf')
            lp=next(a for a in p.automation if a.id=='gesture-'+role+'-lpf')
            self.assertEqual(lane_value(hp,32*BAR-12),1000)
            self.assertLessEqual(lane_value(hp,32*BAR),280)
            self.assertEqual(lane_value(lp,32*BAR-12),1100)
            self.assertEqual(lane_value(lp,32*BAR),14000)
            self.assertEqual(lane_value(lp,0),1000)
        for t in p.tracks:
            if t.id in HARMONICS:
                self.assertEqual(t.effects[0].parameters['soundcraft.hpf_slope'],1)
                self.assertEqual(t.effects[0].parameters['soundcraft.lpf_slope'],1)
        for a in p.automation:
            self.assertEqual(a.points[0].tick,0);self.assertEqual(a.points[-1].tick,p.length)
            self.assertTrue(all(x.shape=='linear' for x in a.points))
            self.assertFalse(a.target_id.startswith('instrument-'))
            self.assertNotIn(a.parameter_id,('soundcraft.hpf_slope','soundcraft.lpf_slope'))

    def test_delay_throws_align_to_authored_phrase_endings_instead_of_empty_beats(self):
        for role,factor in (('lead',.75),('arp',.5)):
            t=next(t for t in self.p.tracks if t.id=='track-'+role)
            fx=next(e for e in t.effects if e.plugin_ref.endswith('mod_delay'))
            self.assertAlmostEqual(fx.parameters['soundcraft.time'],60000/126*factor)
            a=next(a for a in self.p.automation if a.target_id==fx.id and a.parameter_id=='effect.wet')
            for first in range(0,64,2):
                events=[c.start+n.start for c in t.clips for n in c.notes if first*BAR<=c.start+n.start<(first+2)*BAR]
                if events:self.assertGreaterEqual(lane_value(a,max(events)),.48)
            self.assertEqual(fx.parameters['soundcraft.mod_depth'],0)

    def test_pump_is_11_db_on_pads_free_breakdown_and_quiet_base_mix(self):
        for role in PADS:
            t=next(t for t in self.p.tracks if t.id==role)
            old=next(t for t in self.old.tracks if t.id==role)
            self.assertEqual(t.controls,old.controls)
            a=next(a for a in self.p.automation if a.target_id==role and a.parameter_id=='mixer.gain_db')
            base=t.controls['mixer.gain_db']
            self.assertEqual(lane_value(a,32*BAR),base-11)
            self.assertEqual(lane_value(a,32*BAR+680),base)
            self.assertEqual(lane_value(a,26*BAR+240),base)
            self.assertTrue(all(x.value<=base for x in a.points))
            self.assertGreaterEqual(t.effects[-1].parameters['soundcraft.decay_ms'],3000)

    def test_same_input_controls_keep_notes_and_only_remove_named_automation(self):
        for kind,param in (('hpf','soundcraft.hpf_freq'),('lpf','soundcraft.lpf_freq'),
                           ('delay','effect.wet'),('reverb','effect.wet'),('modulation','effect.wet'),('duck','mixer.gain_db')):
            q=control(self.p,kind);validate(q)
            self.assertEqual(note_fingerprints(q),note_fingerprints(self.p))
            for t,original in zip(q.tracks,self.p.tracks):
                self.assertEqual(t.instrument,original.instrument)
                self.assertEqual(t.controls,original.controls)
            removed=[a for a in self.p.automation if a not in q.automation]
            self.assertTrue(all(a.parameter_id==param for a in removed))
            if kind=='hpf':
                for t,old in zip(q.tracks,self.p.tracks):
                    if t.id in ('track-hats','track-percussion',*PADS):
                        self.assertEqual(t.effects[0],old.effects[0])
        with self.assertRaises(ValidationError):control(self.p,'unverified-sidechain')

    def test_window_note_intersections_and_automation_boundary_interpolation(self):
        q=crop(self.p,17,5,[*PADS,'track-harmony']);validate(q)
        self.assertEqual(q.bars,5)
        for t in q.tracks:
            old=next(x for x in self.p.tracks if x.id==t.id)
            expected=[]
            for c in old.clips:
                for n in c.notes:
                    a,b=max(17*BAR,c.start+n.start),min(22*BAR,c.start+n.start+n.duration)
                    if b>a:expected.append((n.id,a-17*BAR,b-a,n.pitch,n.velocity,n.channel))
            actual=[(n.id,c.start+n.start,n.duration,n.pitch,n.velocity,n.channel) for c in t.clips for n in c.notes]
            self.assertEqual(expected,actual)
        for a in q.automation:
            old=next(x for x in self.p.automation if x.id==a.id)
            self.assertEqual(a.points[0].value,lane_value(old,17*BAR))
            self.assertEqual(a.points[-1].value,lane_value(old,22*BAR))
        for first,bars,ids in ((-1,4,list(PADS)),(63,2,list(PADS)),(0,0,list(PADS)),(0,4,['missing']),(0,4,[])):
            with self.assertRaises(ValidationError):crop(self.p,first,bars,ids)

    def test_discovered_native_capability_choices_units_and_unsupported_lanes_fail_closed(self):
        a=SoundCraftAdapter('/bin/true');a._discovery=deepcopy(CONTRACT)
        for name in ('soundcraft-production-plugins.json','soundcraft-depth-plugins.json'):
            a._discovery['plugins'].update(json.loads((Path(__file__).parent/'fixtures'/name).read_text()))
        self.assertTrue(a.capabilities(self.p)['supported'])
        q=deepcopy(self.p);q.tracks[4].effects[0].parameters['soundcraft.hpf_slope']=.5
        self.assertFalse(a.capabilities(q)['supported'])
        q=deepcopy(self.p);next(x for x in q.parameters if x.id=='soundcraft.hpf_freq').unit='ms'
        self.assertFalse(a.capabilities(q)['supported'])
        q=deepcopy(self.p);q.automation[0].points[1].shape='step'
        self.assertFalse(a.capabilities(q)['supported'])

    def test_existing_lane_edits_keep_exact_receipts_and_lock_semantics(self):
        p=self.p;a=next(x for x in p.automation if x.id=='gesture-lead-hpf')
        op=AddAutomationPoints('add_automation_points',a.id,[AutomationPoint('user-sweep-point',PPQ,450,'linear')])
        scope=Scope(['track-lead'],[],['soundcraft.hpf_freq'],0,2*PPQ)
        e=Engine(p);r=e.apply([op],scope,state_hash(p))
        self.assertEqual(dumps(replay(e.project,r,undo=True)),dumps(p))
        self.assertEqual(dumps(replay(p,r,undo=False)),dumps(e.project))
        q=deepcopy(p);q.locks.append(Lock('filter-lock',a.target_id,'soundcraft.hpf_freq'))
        with self.assertRaises(LockedError):Engine(q).apply([op],scope,state_hash(q))


class GesturePublicationTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=SCRATCH);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_symbolic_publication_has_no_false_native_or_listening_success(self):
        out=self.root/'symbolic';r=build(out)
        self.assertFalse(r['native_verified']);self.assertFalse(r['human_listening']);self.assertFalse(r['club_ready'])
        self.assertEqual((out/'song.mid').read_bytes(),export_bytes(gesture_house()))
        with self.assertRaises(ValidationError):build(out)
        with self.assertRaises(ValidationError):package(out)

    def test_failed_host_source_drift_and_escaped_paths_publish_nothing(self):
        with self.assertRaises(ValidationError):build(self.root/'failed',executable='/bin/true')
        self.assertFalse((self.root/'failed').exists())
        with self.assertRaises(ValidationError):build(ROOT.parent/'forbidden-phase8')
        link=self.root/'link';link.symlink_to(self.root)
        with self.assertRaises(ValidationError):build(link)


class LocalizedAudioTests(unittest.TestCase):
    def test_absolute_band_power_matches_known_tones_and_rejects_invalid_regions(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            paths=[]
            for frequency in (200,4000):
                path=Path(d)/str(frequency);paths.append(path)
                with wave.open(str(path),'wb') as w:
                    w.setparams((2,3,48000,0,'NONE','not compressed'))
                    w.writeframes(b''.join(round(.1*math.sin(2*math.pi*frequency*i/48000)*(2**23-1)).to_bytes(3,'little',signed=True)*2 for i in range(24000)))
            a,b=[window_metrics(path,[('tone',0,.5)])['regions']['tone'] for path in paths]
            self.assertAlmostEqual(a['band_mean_square']['body_120_500'],.005,delta=.0001)
            self.assertAlmostEqual(b['band_mean_square']['presence_2000_8000'],.005,delta=.0001)
            self.assertGreater(a['band_mean_square']['body_120_500'],b['band_mean_square']['body_120_500']*100)
            for regions in ([('bad',-.1,.2)],[('bad',0,.01)],[('bad',0,float('nan'))],[('x',0,.2),('x',.2,.4)]):
                with self.assertRaises(ValidationError):window_metrics(paths[0],regions)

    def test_beat_gain_metric_measures_known_temporal_duck(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            paths=[]
            for duck in (True,False):
                p=Path(d)/str(duck);paths.append(p)
                with wave.open(str(p),'wb') as w:
                    w.setparams((2,3,48000,0,'NONE','not compressed'))
                    data=bytearray()
                    for i in range(96000):
                        phase=(i/48000)%(60/126)
                        gain=.25 if duck and phase<.1 else 1
                        data+=round(gain*.1*math.sin(2*math.pi*200*i/48000)*(2**23-1)).to_bytes(3,'little',signed=True)*2
                    w.writeframes(data)
            r=phase_gain(*paths,beats=4)
            self.assertAlmostEqual(r['duck']['on_off_db'],20*math.log10(.25),places=4)
            self.assertAlmostEqual(r['open']['on_off_db'],0,places=5)
            envelope=gain_reduction_envelope(*paths)
            self.assertLess(envelope['minimum_gain_db'],-11)
            self.assertGreater(envelope['gain_variation_db'],11)
