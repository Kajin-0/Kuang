import json
import math
import tempfile
import unittest
import wave
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from kuang.depth import PAD_IDS, SOURCE_HASH, depth_house, note_fingerprints
from kuang.groove import house_loop
from kuang.midi import export_bytes
from kuang.schema import BAR, ValidationError, dumps, save, state_hash, validate
from kuang.soundcraft import SoundCraftAdapter
from kuang.spatial_audio import spatial_metrics
from soundcraft_fake import CONTRACT
from tools.phase6_house import ROOT, build, control, pcm_prefix_equal, write


class DepthTests(unittest.TestCase):
    def test_deterministic_exact_original_notes_and_mono_low_end(self):
        source=house_loop();before=dumps(source)
        self.assertEqual(state_hash(source),SOURCE_HASH)
        a,b=depth_house(source),depth_house()
        self.assertEqual(dumps(a),dumps(b));self.assertEqual(export_bytes(a),export_bytes(b))
        self.assertEqual(before,dumps(source))
        for t in source.tracks:
            new=next(x for x in a.tracks if x.id==t.id)
            self.assertEqual(asdict(t)['clips'],asdict(new)['clips'])
            if t.id in ('track-kick','track-bass'):
                self.assertEqual(t,new);self.assertEqual(new.controls['mixer.pan'],0)
        self.assertEqual(a.sections,source.sections)
        self.assertEqual(a.automation[:len(source.automation)],source.automation)

    def test_source_drift_is_rejected_even_if_notes_are_valid(self):
        for mutate in (lambda p:setattr(p.tracks[0].clips[0].notes[0],'velocity',99),
                       lambda p:p.metadata.update(unreviewed='drift')):
            p=house_loop();mutate(p)
            with self.assertRaisesRegex(ValidationError,'unchanged Phase 5'):depth_house(p)

    def test_rootless_ninth_harmony_register_and_phrase_density(self):
        p=depth_house();validate(p)
        self.assertEqual((p.version,p.bars,p.tempo_bpm,p.time_signature),('0.1',16,126,[4,4]))
        self.assertEqual(json.loads(p.metadata['song_spec'])['progression'],[0,0,0,3])
        pad=next(t for t in p.tracks if t.id==PAD_IDS[0])
        self.assertEqual([len(c.notes) for c in pad.clips],[9,12,9,12])
        for t in p.tracks[-2:]:
            for c in t.clips:
                for n in c.notes:
                    self.assertIn(n.pitch%12,{0,2,3,5,7,8,10})
                    self.assertTrue(63<=n.pitch<=84);self.assertEqual(n.channel,0)
                    self.assertLessEqual(n.start+n.duration,c.length)
                    self.assertGreater(n.duration,960)
                    if n.start<3*BAR:self.assertIn(n.pitch%12,{0,2,3,7,10})
                    else:self.assertIn(n.pitch%12,{0,3,5,7,8})
        for c in pad.clips:
            cm={n.pitch%12 for n in c.notes if n.start<3*BAR}
            fm={n.pitch%12 for n in c.notes if n.start>=3*BAR}
            self.assertTrue({2,3,10}<=cm)  # Cm ninth, third and seventh
            self.assertTrue({3,7,8}<=fm)   # Fm seventh, ninth and minor third

    def test_distinct_static_envelopes_and_actual_effect_movement(self):
        p=depth_house();pad,air=p.tracks[-2:]
        a,b=pad.instrument.parameters,air.instrument.parameters
        for params in (a,b):
            for name in ('amp_attack','amp_release'):
                self.assertTrue(250<=params['soundcraft.'+name]<=1200)
        self.assertNotEqual([a['soundcraft.'+x] for x in ('amp_attack','amp_decay','amp_sustain','amp_release')],
                            [b['soundcraft.'+x] for x in ('amp_attack','amp_decay','amp_sustain','amp_release')])
        self.assertLess(pad.controls['mixer.pan'],0);self.assertGreater(air.controls['mixer.pan'],0)
        for t in (pad,air):
            chorus=next(e for e in t.effects if e.plugin_ref=='soundcraft:chorus')
            self.assertGreater(chorus.parameters['soundcraft.depth'],.5)
            self.assertEqual(chorus.parameters['soundcraft.spread'],1)
            self.assertGreater(t.effects[0].parameters['soundcraft.hpf_freq'],300)
        self.assertTrue(any(e.plugin_ref=='soundcraft:phaser' for e in pad.effects))
        lanes=[x for x in p.automation if x.id in ('depth-pad-filter','depth-air-filter')]
        for lane in lanes:
            self.assertEqual(lane.points[0].tick,0)
            self.assertEqual(lane.points[-1].tick,p.length)
            self.assertGreater(max(x.value for x in lane.points)/min(x.value for x in lane.points),4)
            self.assertTrue(all(1000<=x.value<=20000 and x.shape=='linear' for x in lane.points))
        self.assertFalse(any(x.target_id.startswith('instrument-') for x in p.automation))

    def test_original_inserts_preserved_except_documented_reverb_scalars(self):
        old,new=house_loop(),depth_house()
        for a,b in zip(old.tracks,new.tracks):
            expected=deepcopy(a)
            if a.id=='track-harmony':
                expected.effects[2].parameters.update({'effect.wet':.22,'soundcraft.decay_ms':1250,'soundcraft.pre_delay':22})
            if a.id=='track-lead':expected.effects.append(deepcopy(b.effects[-1]))
            self.assertEqual(expected,b)

    def test_pinned_native_capabilities_and_units_reject_bad_phaser_bounds(self):
        a=SoundCraftAdapter('/bin/true');a._discovery=deepcopy(CONTRACT)
        for name in ('soundcraft-production-plugins.json','soundcraft-depth-plugins.json'):
            a._discovery['plugins'].update(json.loads((Path(__file__).parent/'fixtures'/name).read_text()))
        p=depth_house();r=a.capabilities(p)
        self.assertTrue(r['supported'],r['unsupported'])
        phaser=next(e for e in p.tracks[-2].effects if e.plugin_ref=='soundcraft:phaser')
        phaser.parameters['soundcraft.feedback']=.99  # registry allows it; actual phaser does not
        self.assertFalse(a.capabilities(p)['supported'])

    def test_same_input_controls_preserve_all_notes_and_modulation_wet_mix(self):
        p=depth_house()
        for mode in ('reverb-dry','mod-depth-zero','filter-static'):
            q=control(p,mode)
            self.assertEqual(note_fingerprints(p),note_fingerprints(q))
            self.assertNotEqual(dumps(p),dumps(q))
            self.assertEqual(p.tracks[:4],q.tracks[:4])
        q=control(p,'mod-depth-zero')
        for old,new in zip(p.tracks[-2:],q.tracks[-2:]):
            for a,b in zip(old.effects,new.effects):
                if b.plugin_ref in ('soundcraft:chorus','soundcraft:phaser'):
                    self.assertEqual(b.parameters['soundcraft.depth'],0)
                    self.assertEqual(a.parameters['effect.wet'],b.parameters['effect.wet'])
        with self.assertRaises(ValidationError):control(p,'imaginary-lfo')


class DepthPublicationTests(unittest.TestCase):
    def setUp(self):
        scratch=ROOT/'.local/phase6';scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_symbolic_bytes_and_no_fake_native_success(self):
        a,b=self.root/'a',self.root/'b'
        r=build(a);build(b)
        self.assertEqual((a/'project.kuang.json').read_bytes(),(b/'project.kuang.json').read_bytes())
        self.assertEqual((a/'song.mid').read_bytes(),(b/'song.mid').read_bytes())
        self.assertFalse(r['native_verified']);self.assertFalse(r['listening_performed'])
        self.assertFalse(r['club_quality_established']);self.assertTrue(r['sources_unchanged'])
        self.assertFalse((a/'B-phase6-depth.wav').exists())

    def test_no_clobber_symlink_escape_failed_backend_and_source_drift(self):
        empty=self.root/'empty';empty.mkdir()
        with self.assertRaises(ValidationError):build(empty)
        self.assertEqual(list(empty.iterdir()),[])
        link=self.root/'link';link.symlink_to(empty)
        with self.assertRaises(ValidationError):build(link)
        with self.assertRaises(ValidationError):build(ROOT.parent/'forbidden-phase6')
        out=self.root/'failure'
        with self.assertRaises((ValidationError,FileNotFoundError)):
            build(out,executable=str(self.root/'missing'),source=empty)
        self.assertFalse(out.exists())
        source=self.root/'source';source.mkdir();save(house_loop(),source/'project.kuang.json')
        with self.assertRaises(ValidationError):
            build(out,executable=str(self.root/'missing'),source=source)
        self.assertFalse(out.exists())

    def test_prefix_comparison_checks_complete_pcm_and_formats(self):
        def wav(name,values,rate=48000):
            path=self.root/name
            with wave.open(str(path),'wb') as w:
                w.setparams((2,3,rate,0,'NONE','not compressed'))
                w.writeframes(b''.join(v.to_bytes(3,'little',signed=True)*2 for v in values))
            return path
        a=wav('a.wav',[1,2,3]);b=wav('b.wav',[1,2,3,4])
        self.assertTrue(pcm_prefix_equal(a,b));self.assertFalse(pcm_prefix_equal(b,a))
        self.assertFalse(pcm_prefix_equal(a,wav('c.wav',[1,2,4,4])))
        self.assertFalse(pcm_prefix_equal(a,wav('d.wav',[1,2,3,4],44100)))

    def test_racing_output_is_preserved_and_private_stage_is_cleaned(self):
        destination=self.root/'raced'
        stages=set((ROOT/'.local/phase6').glob('depth-*'))
        def raced_write(path,value):
            if not destination.exists():
                destination.mkdir();(destination/'keep.txt').write_text('other writer')
            write(path,value)
        with patch('tools.phase6_house.write',side_effect=raced_write):
            with self.assertRaises(FileExistsError):build(destination)
        self.assertEqual((destination/'keep.txt').read_text(),'other writer')
        self.assertEqual([p.name for p in destination.iterdir()],['keep.txt'])
        self.assertEqual(set((ROOT/'.local/phase6').glob('depth-*')),stages)


class SpatialAudioTests(unittest.TestCase):
    def setUp(self):
        scratch=ROOT/'.local/phase6';scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def tone(self,name,side):
        path=self.root/name
        with wave.open(str(path),'wb') as w:
            w.setparams((2,3,48000,0,'NONE','not compressed'))
            frames=[]
            for i in range(16384):
                high=.15*math.sin(2*math.pi*2015.625*i/48000)
                low=.2*math.sin(2*math.pi*58.59375*i/48000) if side=='split' else 0
                l=low+high;r=low+(-high if side in ('anti','split') else high)
                frames.extend(round(x*(2**23-1)).to_bytes(3,'little',signed=True) for x in (l,r))
            w.writeframes(b''.join(frames))
        return path

    def test_mono_and_antiphase_energy_have_expected_extremes(self):
        mono=spatial_metrics(self.tone('mono.wav','mono'))
        anti=spatial_metrics(self.tone('anti.wav','anti'))
        self.assertEqual(mono['bands']['high_over_500']['side'],0)
        self.assertEqual(mono['bands']['high_over_500']['mono_energy_retention'],1)
        self.assertEqual(anti['bands']['high_over_500']['mono_energy_retention'],0)
        self.assertEqual(anti['mono_sum']['rms'],0)
        self.assertAlmostEqual(mono['mono_sum']['rms_loss_db'],0,places=10)

    def test_frequency_split_detects_safe_low_end_and_cancelled_high_end(self):
        m=spatial_metrics(self.tone('split.wav','split'))
        self.assertGreater(m['bands']['low_20_120']['mono_energy_retention'],.999)
        self.assertLess(m['bands']['high_over_500']['mono_energy_retention'],1e-7)
        self.assertFalse(m['mono_sum']['clipped'])
        self.assertGreater(m['last_250ms']['rms'],.1)
