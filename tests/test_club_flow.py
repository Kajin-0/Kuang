"""Editorial continuity, exact deltas and restraint, never a preference score."""
import unittest
from copy import deepcopy
from dataclasses import asdict
from unittest.mock import patch
from kuang.schema import BAR,PPQ,state_hash,dumps,ValidationError,Lock
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.house_composition import compose_record
from kuang.club_flow import refine_flow
from kuang.flow_audit import audit_flow,require_flow,groove_facts
from kuang.composition_analysis import event_rows
from kuang.production_host import graph_contract
from kuang.gestures import lane_value

class ClubFlowTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # Symbolic CI surrogate; actual native cases use the sealed Phase18 artifact.
  base=repaired_house(split_house(atmosphere_house())[0])[0]
  for t in base.tracks:
   if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
  with patch('kuang.mix_polish.SOURCE_HASH',state_hash(base)):s=polished_mix(base)[0]
  with patch('kuang.house_composition.SOURCE_HASH',state_hash(s)):cls.source=compose_record(s)[0]
  with patch('kuang.club_flow.SOURCE_HASH',state_hash(cls.source)):cls.p,cls.r=refine_flow(cls.source)
  cls.a=audit_flow(cls.source,cls.p,cls.r)
 def proposal(self):
  with patch('kuang.club_flow.SOURCE_HASH',state_hash(self.source)):return refine_flow(self.source)
 def test_actual_reference_and_candidate_kick_gap_and_early_identity(self):
  a=self.a;self.assertEqual(a['source_facts']['longest_kick_free_bars'],24);self.assertEqual(a['source_facts']['first_complete_signature_zero_bar'],26)
  b=a['candidate_facts'];self.assertEqual(b['longest_kick_free_bars'],8);self.assertEqual(b['longest_kick_free_start_zero_bar'],80)
  self.assertEqual(b['first_complete_signature_zero_bar'],16);self.assertEqual(b['first_established_bass_drums_zero_bar'],8);self.assertTrue(b['steady_four_floor_88_112'])
 def test_all_96_recovered_kicks_exact_four_floor_not_section_names(self):
  for row in self.a['candidate_facts']['per_bar'][88:112]:self.assertEqual(row['kick_ticks_within_bar'],[0,PPQ,2*PPQ,3*PPQ])
  q=deepcopy(self.p)
  for t in q.tracks:
   if t.id=='track-kick':
    for c in t.clips:c.notes=[n for n in c.notes if not 100*BAR<=c.start+n.start<101*BAR]
  a=deepcopy(self.a);a['candidate_facts']=groove_facts(q)
  with self.assertRaises(ValidationError):require_flow(a)
 def test_hypnotic_identity_replaces_foreign_counterthemes(self):
  self.assertEqual(self.a['candidate_facts']['lead_pitch_vocabulary'],[63,65,67]);self.assertEqual(len(self.a['source_facts']['lead_pitch_vocabulary']),7)
  for bar in (16,18,24,32,48,64,68,72,76,88,92,96,100,104,108,112,128,142):self.assertIn(bar,self.a['candidate_facts']['complete_signature_zero_bars'])
 def test_bridge_is_same_C_pedal_and_one_short_neighbor_color(self):
  plan=self.r['harmonic_plan'];self.assertEqual({x['name'] for x in plan[64:80]},{'Cm9','Fm7-C'})
  self.assertEqual([x['bar'] for x in plan[64:80] if x['name']=='Fm7-C'],[69,70,71,72]);self.assertFalse(self.a['bridge_anchor_failures'])
  self.assertTrue(all(x['C_anchor'] for x in self.a['bridge_anchor_matrix']))
  self.assertTrue(all(x['color_all_C'] for x in self.a['bridge_anchor_matrix'] if 69<=x['bar']<=72))
 def test_all_simultaneous_harmonic_and_bass_intervals_audited(self):
  require_flow(self.a)
  for key in ('out_of_key_intervals','non_chord_harmonic_layer_intervals','non_chord_bass_intervals'):self.assertFalse(self.a['harmonic'][key])
  self.assertGreater(len(self.a['harmonic']['concurrent_intervals']),2500);self.assertFalse(self.a['measured_pitch_offset_context']['out_of_scale_note_records'])
 def test_two_approved_608_note_high_points_exact(self):
  self.assertEqual(self.a['harmonic']['approved_first_statement_exact'],608);self.assertEqual(self.a['harmonic']['approved_translated_return_exact'],608)
  before={x['id']:x for x in event_rows(self.source)};after={x['id']:x for x in event_rows(self.p)}
  for nid,x in before.items():
   if 32*BAR<=x['absolute_tick']<48*BAR or 112*BAR<=x['absolute_tick']<128*BAR:self.assertEqual(after[nid],x)
 def test_sound_graph_registry_and_all_instrument_parameters_exact(self):
  self.assertEqual(self.p.parameters,self.source.parameters)
  for old,new in zip(self.source.tracks,self.p.tracks):
   a=asdict(old);b=asdict(new);a.pop('clips');b.pop('clips');self.assertEqual(a,b)
  self.assertEqual(self.p.metadata['song_spec'],self.source.metadata['song_spec']);graph_contract(self.p)
 def test_source_unchanged_determinism_and_wrong_source_locks(self):
  before=dumps(self.source);q,r=self.proposal();self.assertEqual(before,dumps(self.source));self.assertEqual(dumps(q),dumps(self.p));self.assertEqual(r,self.r)
  with self.assertRaises(ValidationError):refine_flow(self.source)
  q=deepcopy(self.source);q.locks=[Lock('flow-lock',q.tracks[0].id,None)]
  with patch('kuang.club_flow.SOURCE_HASH',state_hash(q)):
   with self.assertRaises(ValidationError):refine_flow(q)
 def test_journal_replays_complete_state_and_rejects_invented_lineage(self):
  self.assertTrue(self.a['note_journal_exact']);self.assertGreater(self.a['unchanged_note_records'],3500)
  r=deepcopy(self.r);add=next(e for e in r['edits'] if e['action']=='add');add['source']['pitch']+=1
  with self.assertRaises(ValidationError):audit_flow(self.source,self.p,r)
  r=deepcopy(self.r);r['edits'].pop()
  with self.assertRaises(ValidationError):audit_flow(self.source,self.p,r)
 def test_intro_outro_original_rhythm_and_eight_bar_break_clock(self):
  old={x['id']:x for x in event_rows(self.source)};new={x['id']:x for x in event_rows(self.p)}
  for nid,x in old.items():
   if x['absolute_tick']>=144*BAR or(x['track_id']=='track-kick' and x['absolute_tick']<16*BAR):self.assertEqual(new[nid],x)
  for b in range(80,88):
   row=self.a['candidate_facts']['per_bar'][b];self.assertEqual(row['kick_count'],0);self.assertEqual(row['hat_count'],4)
  self.assertTrue(all(row['four_floor_exact'] for row in self.a['candidate_facts']['per_bar'][144:160]))
 def test_automation_recovers_with_kick_and_obeys_existing_units(self):
  specs={x.id:x for x in self.p.parameters}
  for a in self.p.automation:
   self.assertEqual(len(a.points),len({x.tick for x in a.points}));self.assertTrue(all(0<=x.tick<=160*BAR and specs[a.parameter_id].minimum<=x.value<=specs[a.parameter_id].maximum for x in a.points))
  a=next(a for a in self.p.automation if a.target_id=='track-depth-pad' and a.parameter_id=='mixer.gain_db')
  self.assertLess(lane_value(a,88*BAR),lane_value(a,88*BAR+700))
  h=next(a for a in self.p.automation if a.target_id=='effect-lead-eq' and a.parameter_id=='soundcraft.hpf_freq')
  self.assertLessEqual(lane_value(h,96*BAR),280);self.assertLess(lane_value(h,111*BAR+PPQ),500)
 def test_no_instrument_novelty_no_forced_variety_and_160_bar_duration(self):
  self.assertEqual(self.p.bars,160);self.assertEqual(self.p.tempo_bpm,126);self.assertEqual(sum(s.length for s in self.p.sections),160*BAR)
  self.assertEqual([s.length//BAR for s in self.p.sections],[16,16,32,16,8,8,16,32,16]);self.assertFalse(self.r['MIDI_bytes_exact']);self.assertTrue(self.r['not_transaction_receipt'])
  self.assertEqual(len(self.r['note_origins']),len(event_rows(self.p)))
