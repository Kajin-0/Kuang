import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from kuang.composer import compose
from kuang.groove import house_loop
from kuang.midi import export_bytes
from kuang.production import refine_house
from kuang.schema import BAR, PPQ, ValidationError, dumps, state_hash, validate
from kuang.song import rules_plan
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import Engine, Scope, ScopeError, SetParameter, replay
from soundcraft_fake import CONTRACT
from tools.phase5_house import ROOT, build


class GrooveTests(unittest.TestCase):
    def test_determinism_stable_ids_and_previous_composer_unchanged(self):
        spec=rules_plan('house',29)[0]
        before=dumps(refine_house(spec,compose(spec)))
        a,b,c=house_loop(),house_loop(),house_loop(30)
        self.assertEqual(dumps(a),dumps(b));self.assertEqual(export_bytes(a),export_bytes(b))
        self.assertNotEqual(dumps(a),dumps(c))
        self.assertEqual([n.id for t in a.tracks for x in t.clips for n in x.notes],
                         [n.id for t in c.tracks for x in t.clips for n in x.notes])
        self.assertEqual(before,dumps(refine_house(spec,compose(spec))))

    def test_continuous_grid_kick_and_bass_pickups_clear_next_attack(self):
        p=house_loop()
        kick=next(t for t in p.tracks if t.id=='track-kick')
        self.assertEqual([c.start+n.start for c in kick.clips for n in c.notes],list(range(0,16*BAR,PPQ)))
        bass=next(t for t in p.tracks if t.id=='track-bass')
        for c in bass.clips:
            notes=c.notes
            self.assertTrue(all(a.start+a.duration<=b.start for a,b in zip(notes,notes[1:])))
            for n in notes:
                end=n.start+n.duration+round(28*126*PPQ/60000)
                self.assertLess(end,((n.start//PPQ)+1)*PPQ)
                self.assertGreaterEqual(n.start%PPQ,PPQ//4)
        self.assertEqual(bass.instrument.parameters['soundcraft.osc_mix'],0)

    def test_four_bar_variation_small_hook_and_no_song_breakdown(self):
        p=house_loop()
        self.assertEqual([s.length for s in p.sections],[4*BAR]*4)
        self.assertEqual([s.name for s in p.sections],['Pocket','Answer','Lift','Return'])
        hook=next(t for t in p.tracks if t.id=='track-lead')
        self.assertEqual({n.pitch for c in hook.clips for n in c.notes},{63,65,67})
        self.assertEqual([len(c.notes) for c in hook.clips],[6,6,6,7])
        hats=next(t for t in p.tracks if t.id=='track-hats')
        self.assertGreater(len(hats.clips[2].notes),len(hats.clips[0].notes))
        clap=next(t for t in p.tracks if t.id=='track-snare')
        self.assertGreater(len(clap.clips[1].notes),len(clap.clips[0].notes))
        self.assertTrue(all(c.notes for t in p.tracks for c in t.clips))

    def test_meter_diatonic_membership_register_and_deliberate_timing(self):
        p=house_loop();validate(p)
        self.assertEqual((p.version,p.bars,p.tempo_bpm,p.key_tonic,p.key_mode),('0.1',16,126,0,'minor'))
        self.assertEqual(p.time_signature,[4,4])
        self.assertEqual(json.loads(p.metadata['song_spec'])['progression'],[0,0,0,3])
        for t in p.tracks:
            for c in t.clips:
                for n in c.notes:
                    self.assertLessEqual(n.start+n.duration,c.length)
                    if n.channel!=9:
                        self.assertIn(n.pitch%12,{0,2,3,5,7,8,10})
                        self.assertLessEqual(n.pitch,70)
        clap=next(t for t in p.tracks if t.id=='track-snare')
        self.assertTrue(all(n.start%PPQ==18 for c in clap.clips for n in c.notes if n.pitch==39))
        hats=next(t for t in p.tracks if t.id=='track-hats')
        self.assertTrue(any(n.start%(PPQ//4)==40 for c in hats.clips for n in c.notes))

    def test_live_recorded_capabilities_and_explicit_envelopes_modulation(self):
        p=house_loop();a=SoundCraftAdapter('/bin/true');a._discovery=deepcopy(CONTRACT)
        a._discovery['plugins'].update(json.loads((Path(__file__).parent/'fixtures/soundcraft-production-plugins.json').read_text()))
        report=a.capabilities(p)
        self.assertTrue(report['supported'],report['unsupported'])
        for t in p.tracks:
            self.assertTrue(all(e.plugin_ref.startswith('soundcraft:') for e in t.effects))
            if t.instrument.plugin_ref.endswith('subtractive_synth'):
                self.assertIn('soundcraft.filter_decay',t.instrument.parameters)
                self.assertLess(t.instrument.parameters['soundcraft.amp_release'],100)
        self.assertTrue(all(l.points[0].tick==0 for l in p.automation))
        self.assertFalse(any(l.target_id.startswith('instrument-') for l in p.automation))

    def test_new_controls_keep_exact_existing_scope_history_semantics(self):
        p=house_loop();engine=Engine(p)
        op=SetParameter('set_parameter','effect-harmony-chorus','effect.wet',.23)
        scope=Scope(['track-harmony'],[],['effect.wet'],None,None)
        r=engine.apply([op],scope,state_hash(p))
        expected=deepcopy(p)
        next(e for t in expected.tracks for e in t.effects if e.id==op.target_id).parameters['effect.wet']=.23
        self.assertEqual(dumps(engine.project),dumps(expected))
        self.assertEqual(dumps(replay(engine.project,r,undo=True)),dumps(p))
        self.assertEqual(dumps(replay(p,r,undo=False)),dumps(expected))
        with self.assertRaises(ScopeError):
            Engine(p).apply([op],Scope(['track-bass'],[],['effect.wet'],None,None),state_hash(p))


class GroovePublicationTests(unittest.TestCase):
    def setUp(self):
        scratch=ROOT/'.local/phase5';scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_symbolic_bytes_provenance_no_clobber_and_no_fake_audio_proof(self):
        a,b=self.root/'a',self.root/'b'
        ra=build(a);build(b)
        self.assertEqual((a/'project.kuang.json').read_bytes(),(b/'project.kuang.json').read_bytes())
        self.assertEqual((a/'song.mid').read_bytes(),(b/'song.mid').read_bytes())
        self.assertFalse(ra['native_verified']);self.assertFalse(ra['club_quality_established'])
        self.assertFalse((a/'candidate.wav').exists())
        before=(a/'verification.json').read_bytes()
        with self.assertRaises(ValidationError):build(a)
        self.assertEqual((a/'verification.json').read_bytes(),before)
        empty=self.root/'empty';empty.mkdir()
        with self.assertRaises(ValidationError):build(empty)
        self.assertEqual(list(empty.iterdir()),[])

    def test_reference_metadata_invalid_grid_and_failed_backend_leave_no_output(self):
        ref=self.root/'reference.wav';ref.write_bytes(b'private source untouched')
        for kwargs in ({'reference':ref},{'reference_start':float('nan')},{'executable':str(self.root/'absent')}):
            out=self.root/'bad'
            with self.assertRaises(ValidationError):build(out,**kwargs)
            self.assertFalse(out.exists())
        self.assertEqual(ref.read_bytes(),b'private source untouched')
        with self.assertRaises(ValidationError):house_loop(-1)
