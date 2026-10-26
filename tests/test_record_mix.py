"""Source-immutable production, explicit bounded terminal graph and meters."""
import math,tempfile,unittest,wave
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from kuang.schema import load,dumps,state_hash,ValidationError,Lock,Send,AutomationLane,AutomationPoint
from kuang.midi import export_bytes
from kuang.master_bus import attach_terminal,terminal_projection,SINK_KEY
from kuang.production_host import graph_contract,trim_id
from kuang.record_mix import mixed_record,BALANCE
from kuang.mix_diagnostics import shortterm_trace,linked_gain_audit,envelope_gain_audit


class RecordMixTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # Existing offline surrogate, separate from the sealed real-host source.
  import test_club_flow as flow
  flow.ClubFlowTests.setUpClass();cls.source=flow.ClubFlowTests.p
  with patch('kuang.record_mix.SOURCE_HASH',state_hash(cls.source)):
   cls.p,cls.r=mixed_record(cls.source);cls.pre,cls.pr=mixed_record(cls.source,master=False)
 def propose(self,source=None,**kw):
  source=self.source if source is None else source
  with patch('kuang.record_mix.SOURCE_HASH',state_hash(source)):return mixed_record(source,**kw)
 def test_entire_MIDI_note_fields_clip_order_sections_and_instruments_exact(self):
  self.assertEqual(export_bytes(self.p),export_bytes(self.source));self.assertEqual(self.p.sections,self.source.sections)
  for a,b in zip(self.source.tracks,self.p.tracks):self.assertEqual((a.id,a.instrument,a.clips),(b.id,b.instrument,b.clips))
  self.assertEqual(self.p.metadata['song_spec'],self.source.metadata['song_spec'])
 def test_deterministic_generation_preserves_source_and_full_change_journal(self):
  before=dumps(self.source);p,r=self.propose();self.assertEqual(dumps(p),dumps(self.p));self.assertEqual(r,self.r);self.assertEqual(dumps(self.source),before)
  self.assertEqual(self.r['tracks_before'],[asdict(t) for t in self.source.tracks]);self.assertEqual(self.r['automation_before'],[asdict(a) for a in self.source.automation]);self.assertEqual(self.r['automation_after'],[asdict(a) for a in self.p.automation])
 def test_exact_source_and_lock_preconditions_and_calibration_validation(self):
  with self.assertRaises(ValidationError):mixed_record(self.source)
  q=deepcopy(self.source);q.locks=[Lock('mix-lock',q.tracks[0].id,None)]
  with self.assertRaises(ValidationError):self.propose(q)
  for value in ({},{**BALANCE,'unknown':0},{**BALANCE,'track-bass':True},{**BALANCE,'track-bass':float('nan')},{**BALANCE,'track-bass':13}):
   with self.assertRaises(ValidationError):self.propose(balance=value)
  with self.assertRaises(ValidationError):self.propose(master=1)
 def test_one_terminal_master_and_all_earlier_auxes_retained_no_drum_double_feed(self):
  sink=self.p.metadata[SINK_KEY];self.assertEqual([t.id for t in self.p.tracks if t.output_master],[sink]);self.assertEqual(len([t for t in self.p.tracks if t.kind=='bus']),5)
  for t in self.p.tracks[:-1]:
   feeds=[s for s in t.sends if s.target_track_id==sink]
   if t.kind=='bus':self.assertEqual(len(feeds),1)
   if t.id in ('track-kick','track-hats','track-snare','track-snare.p38','track-hats.p46','track-percussion'):self.assertFalse(feeds)
  terminal_projection(self.p)
 def test_terminal_projection_preserves_the_entire_premaster_state(self):
  q=terminal_projection(self.p);sink=q.tracks.pop()
  q.metadata.pop(SINK_KEY);q.metadata={k:v for k,v in q.metadata.items() if not k.startswith('phase20_')}
  pre=deepcopy(self.pre);pre.metadata={k:v for k,v in pre.metadata.items() if not k.startswith('phase20_')}
  self.assertEqual(dumps(q),dumps(pre));self.assertEqual(sink.controls['mixer.gain_db'],0)
 def test_legacy_graph_stays_strict_and_new_terminal_is_explicit_only(self):
  with self.assertRaises(ValidationError):graph_contract(self.p)
  with self.assertRaises(ValidationError):terminal_projection(self.source)
  graph_contract(self.pre)
 def test_terminal_rejects_bypass_cycle_duplicate_trim_or_foreign_nested_route(self):
  for variant in range(6):
   q=deepcopy(self.p);t=next(t for t in q.tracks if t.id=='track-bass');sink=q.tracks[-1]
   if variant==0:t.output_master=True
   elif variant==1:sink.sends=[Send('cycle',q.tracks[-2].id,0,0,'post_fader')]
   elif variant==2:t.sends.append(deepcopy(t.sends[-1]));t.sends[-1].id+='-duplicate'
   elif variant==3:t.sends[-1].gain_db=1
   elif variant==4:t.controls[trim_id(t.sends[-1])]=0
   else:q.tracks[-2].sends=[Send('nested',q.tracks[-3].id,0,0,'post_fader')]
   with self.assertRaises(ValidationError):terminal_projection(q)
 def test_immutable_patch_parameters_and_source_registry_exact(self):
  for a,b in zip(self.source.tracks,self.p.tracks):self.assertEqual(a.instrument,b.instrument)
  for spec in self.source.parameters:self.assertEqual(spec,next(s for s in self.p.parameters if s.id==spec.id))
  self.assertNotIn('soundcraft.ratio',{s.id for s in self.p.parameters});self.assertFalse(self.r['native_limiter_true_peak_aware_claimed'])
 def test_automation_ownership_point_ids_ticks_shapes_and_validated_bounds(self):
  specs={s.id:s for s in self.p.parameters};old={a.id:a for a in self.source.automation}
  for a in self.p.automation:
   if a.id=='phase20-kick-startup':
    self.assertEqual(a.target_id,'track-kick');self.assertEqual(a.points[0].value,next(t for t in self.p.tracks if t.id=='track-kick').controls['mixer.gain_db']);self.assertEqual(a.points[2].value,next(t for t in self.source.tracks if t.id=='track-kick').controls['mixer.gain_db']);continue
   self.assertEqual([(p.id,p.tick,p.shape) for p in a.points],[(p.id,p.tick,p.shape) for p in old[a.id].points])
   self.assertTrue(all(specs[a.parameter_id].minimum<=p.value<=specs[a.parameter_id].maximum for p in a.points))
  for a in self.p.automation:
   if a.parameter_id.startswith('route.'):self.assertEqual(a,old[a.id])
 def test_native_master_and_premaster_are_distinct_reproducible_workflows(self):
  self.assertEqual([e.plugin_ref for e in self.p.tracks[-1].effects],['soundcraft:eq_7band','soundcraft:compressor','soundcraft:maximizer'])
  self.assertNotIn(SINK_KEY,self.pre.metadata);self.assertFalse(self.pr['native_master']);self.assertTrue(self.r['native_master'])
  self.assertEqual(self.p.tracks[-1].effects[-1].parameters['soundcraft.ceiling'],-1.8)


class MixDiagnosticTests(unittest.TestCase):
 def tone(self,path,seconds,scale):
  with wave.open(str(path),'wb') as w:
   w.setparams((2,3,48000,0,'NONE','not compressed'));data=bytearray()
   for i in range(round(seconds*48000)):
    v=round(scale*math.sin(2*math.pi*1000*i/48000)*(2**23));data+=v.to_bytes(3,'little',signed=True)*2
   w.writeframes(data)
 def test_shortterm_steady_stereo_golden_and_silence(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'tone.wav';self.tone(p,4,.1);r=shortterm_trace(p);self.assertEqual(len(r['rows']),2);self.assertAlmostEqual(r['maximum_lufs'],-20.,delta=.1)
   s=Path(tmp)/'silence.wav';self.tone(s,3,0);self.assertIsNone(shortterm_trace(s)['maximum_lufs'])
 def test_actual_gain_control_reports_known_attenuation_and_channel_agreement(self):
  with tempfile.TemporaryDirectory() as tmp:
   a=Path(tmp)/'a.wav';b=Path(tmp)/'b.wav';self.tone(a,.2,.2);self.tone(b,.2,.1);r=linked_gain_audit(a,b)
   self.assertAlmostEqual(r['median_attenuation_below_nominal_db'],6.0206,delta=.001);self.assertLess(r['maximum_channel_gain_disagreement'],.001)
   e=envelope_gain_audit(a,b);self.assertAlmostEqual(e['whole_file_attenuation_below_nominal_db'],6.0206,delta=.001)
 def test_shortterm_and_gain_fail_closed_on_unaligned_or_unsupported_PCM(self):
  with tempfile.TemporaryDirectory() as tmp:
   a=Path(tmp)/'a.wav';b=Path(tmp)/'b.wav';self.tone(a,.2,.2);self.tone(b,.3,.1)
   with self.assertRaises(ValidationError):linked_gain_audit(a,b)
   for value in (0,-1,True,float('nan')):
    with self.assertRaises(ValidationError):linked_gain_audit(a,a,minimum_input=value)
