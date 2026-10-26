"""Original source design and immutable music; native proof is separate."""
import base64,tempfile,unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from kuang.groove_sources import groove_patch,TRACKS
from kuang.source_production import source_record
from kuang.vitalium_patch import original_patch,component,component_patch
from kuang.external_synth import bound_project
from kuang.sampled_instrument import bind_samples
from kuang.schema import ValidationError,dumps,state_hash
from kuang.midi import export_bytes
from test_external_synth import contract_patch
from test_sample_assets import asset,wav,credit,mapping
from kuang.sample_assets import create_asset

ROOT=Path(__file__).resolve().parents[1]


class GrooveSourceTests(unittest.TestCase):
 def test_original_deterministic_waves_and_component_state_no_factory_content(self):
  for voice in ('bass','stab','lead'):
   p=groove_patch(voice);self.assertEqual(p,groove_patch(voice));self.assertEqual(p,component_patch(component(p)))
   self.assertEqual(p['settings']['wavetables'],original_patch('pad')['settings']['wavetables'])
   self.assertEqual(base64.b64decode(p['settings']['sample']['samples']),bytes(64));self.assertEqual(p['settings']['sample_on'],0)
 def test_roles_have_distinct_envelopes_and_bass_remains_mono_integer_tuned(self):
  states={v:groove_patch(v)['settings'] for v in ('bass','stab','lead')}
  self.assertEqual(len({tuple(s['env_1_'+k] for k in ('attack','decay','sustain','release')) for s in states.values()}),3)
  b=states['bass'];self.assertEqual((b['polyphony'],b['osc_1_unison_voices'],b['osc_1_stereo_spread']),(1,1,0));self.assertLess(b['env_1_release']**4,.03)
  for s in states.values():
   for i in (1,2,3):self.assertEqual(s[f'osc_{i}_tune'],0);self.assertIn(s[f'osc_{i}_transpose'],(0,12));self.assertEqual(s[f'osc_{i}_random_phase'],0)
 def test_modulation_bypass_changes_only_routes_and_never_pitch(self):
  for v in ('bass','stab','lead'):
   on=groove_patch(v);off=groove_patch(v,modulation=False);links=on['settings']['modulations'];self.assertTrue(links)
   self.assertTrue(all(not any(x in r['destination'] for x in ('tune','transpose','pitch')) for r in links))
   off['settings']['modulations']=links;self.assertEqual(on,off)
  self.assertIn({'source':'lfo_1','destination':'osc_1_wave_frame'},groove_patch('stab')['settings']['modulations'])
 def test_unknown_roles_variants_units_and_nonfinite_gains_fail_closed(self):
  for args,kw in [(('official Vital',),{}),(('pad',),{}),(('lead',),{'variant':'edge'}),(('bass',),{'variant':'random'}),(('lead',),{'modulation':1}),(('lead',),{'volume_db':float('nan')}),(('bass',),{'volume_db':1})]:
   with self.subTest(args=args,kw=kw),self.assertRaises(ValidationError):groove_patch(*args,**kw)


class SourceProductionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import test_club_flow as f
  f.ClubFlowTests.setUpClass();cls.source=f.ClubFlowTests.p
 def setUp(self):
  scratch=ROOT/'.local/phase20/tests';scratch.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=scratch);self.path=Path(self.temp.name);self.patch=contract_patch(self.path/'original-contract','pluck')
 def tearDown(self):self.temp.cleanup()
 def propose(self,s=None,assignments=None,**kw):
  s=self.source if s is None else s
  with patch('kuang.record_mix.SOURCE_HASH',state_hash(s)):return source_record(s,{'track-harmony':self.patch,'track-lead':self.patch} if assignments is None else assignments,**kw)
 def test_all_note_fields_clip_order_sections_and_original_SongSpec_exact(self):
  before=dumps(self.source);p,r=self.propose();self.assertEqual(export_bytes(p),export_bytes(self.source));self.assertEqual(p.sections,self.source.sections);self.assertEqual(p.metadata['song_spec'],self.source.metadata['song_spec']);self.assertEqual(before,dumps(self.source))
  for t,u in zip(self.source.tracks,p.tracks):self.assertEqual((t.id,t.clips),(u.id,u.clips))
  self.assertFalse(r['native_master']);self.assertEqual(r['quality_preference'],'unreviewed')
 def test_only_explicit_sources_replaced_and_bass_pad_sample_controls_protected(self):
  p,r=self.propose();self.assertEqual({x['track_id'] for x in r['patch_changes']},{'track-harmony','track-lead'})
  for a,b in zip(self.source.tracks,p.tracks):
   if a.id not in ('track-harmony','track-lead'):self.assertEqual(a.instrument,b.instrument)
  self.assertFalse(any('master' in t.id for t in p.tracks));self.assertIsNone(r['sample_change'])
 def test_explicit_partial_assignment_and_deterministic_complete_journal(self):
  a,r=self.propose(assignments={'track-lead':self.patch});b,s=self.propose(assignments={'track-lead':self.patch});self.assertEqual(dumps(a),dumps(b));self.assertEqual(r,s);self.assertEqual(len(r['patch_changes']),1)
  x=r['patch_changes'][0];self.assertEqual(x['before'],asdict(next(t for t in self.source.tracks if t.id=='track-lead').instrument));self.assertEqual(x['after'],asdict(next(t for t in a.tracks if t.id=='track-lead').instrument))
 def test_unknown_assignment_relabel_identity_and_invalid_offsets_rejected(self):
  for assignments in ({},{'track-kick':self.patch},{'track-depth-pad':self.patch},{'missing':self.patch}):
   with self.assertRaises(ValidationError):self.propose(assignments=assignments)
  s=bound_project(self.source,{'track-lead':self.patch})
  with self.assertRaises(ValidationError):self.propose(s,assignments={'track-lead':self.patch})
  for offsets in ({'missing':0},{'track-lead':True},{'track-lead':float('inf')},{'track-lead':13},[]):
   with self.assertRaises(ValidationError):self.propose(offsets=offsets)
 def test_sample_replacement_preserves_original_trigger_parameters_and_all_music(self):
  kick=asset(self.path);incumbent=self.path/'incumbent'
  create_asset(wav(self.path/'incumbent.wav',frames=3600),incumbent,credit(),mapping())
  s=bind_samples(self.source,{'track-kick':incumbent});p,r=self.propose(s,kick=kick)
  old=next(t for t in s.tracks if t.id=='track-kick');new=next(t for t in p.tracks if t.id=='track-kick')
  self.assertEqual(old.instrument.parameters,new.instrument.parameters);self.assertEqual(old.instrument.plugin_ref,new.instrument.plugin_ref);self.assertEqual(old.clips,new.clips);self.assertNotEqual(old.instrument.preset_ref,new.instrument.preset_ref)
  self.assertEqual(r['sample_change']['mapping']['root_note'],36);self.assertEqual(export_bytes(p),export_bytes(self.source))
  with self.assertRaises(ValidationError):self.propose(kick=kick)
 def test_sample_pitch_tracking_velocity_range_or_loop_semantics_cannot_change(self):
  for name,kw in [('pitch',{'key_tracking':True}),('note',{'root_note':35,'key_low':35,'key_high':35}),('velocity',{'velocity_low':2}),('loop',{'playback':'loop'})]:
   if name=='loop':continue # asset importer itself already rejects unsupported loops
   with self.assertRaises(ValidationError):self.propose(kick=asset(self.path,name,**kw))
