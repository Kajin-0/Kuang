"""Musical function, exact source protection and independent event audits."""
import json,os,subprocess,sys,tempfile,unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from kuang.schema import BAR,PPQ,Lock,ValidationError,dumps,save,state_hash
from kuang.composition_analysis import event_rows
from kuang.groove_record import arrange_groove,audit_record,anchor_project,FORM,FUNCTIONS
from kuang.chord_bed import PROTECTED,UPPER,REMOVED

class GrooveRecordTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import test_chord_bed as bed
  bed.ChordBedTests.setUpClass();cls.source=deepcopy(bed.ChordBedTests.p)
  with patch('kuang.groove_record.SOURCE_HASH',state_hash(cls.source)):
   cls.p,cls.r=arrange_groove(cls.source);cls.a=audit_record(cls.source,cls.p,cls.r)
 def check(self,p,r):
  with patch('kuang.groove_record.SOURCE_HASH',state_hash(self.source)):return audit_record(self.source,p,r)
 def test_exact_144_bar_eight_section_form_and_all_eight_bar_functions(self):
  self.assertEqual(self.p.bars,144);self.assertEqual(len(self.p.sections),8);self.assertEqual([s.start//BAR for s in self.p.sections],[0,16,48,64,72,80,112,128]);self.assertEqual(self.p.sections[-1].start+self.p.sections[-1].length,144*BAR);self.assertEqual(len(FUNCTIONS),18)
 def test_all_501_anchor_notes_clip_ids_order_lanes_and_shapes_exact(self):
  self.assertEqual(anchor_project(self.source,self.p),self.source);source_ids={x['id'] for x in event_rows(self.source)};now=[x for x in event_rows(self.p) if 16*BAR<=x['absolute_tick']<32*BAR];self.assertEqual({x['id'] for x in now},source_ids)
 def test_every_original_device_patch_effect_fader_and_signal_route_exact(self):
  for a,b in zip(self.source.tracks,self.p.tracks):
   x=asdict(a);y=asdict(b);x.pop('clips');y.pop('clips');self.assertEqual(x,y)
  self.assertEqual(self.source.parameters,self.p.parameters)
 def test_kick_is_four_floor_except_exactly_eight_bar_break_and_recovers72(self):
  rows=event_rows(self.p)
  for b in range(144):self.assertEqual(sorted(x['absolute_tick']%BAR for x in rows if x['track_id']=='track-kick' and x['absolute_tick']//BAR==b),[] if 64<=b<72 else [i*PPQ for i in range(4)])
  self.assertEqual(self.a['longest_kick_free_bars'],8)
 def test_bass_and_pulse_all_retained_event_fields_and_microtiming_exact(self):
  for x in event_rows(self.p):
   if x['track_id'] not in ('track-bass','track-sub-pulse'):continue
   o=self.r['note_origins'][x['id']]['source'];self.assertEqual([x[k] for k in ('pitch','velocity','duration','channel')],[o[k] for k in ('pitch','velocity','duration','channel')]);self.assertEqual(x['absolute_tick']%BAR,o['absolute_tick']%BAR)
 def test_dj_intro_bass_before16_and_last_eight_bars_are_unpitched(self):
  rows=event_rows(self.p);self.assertEqual(min(x['absolute_tick']//BAR for x in rows if x['track_id']=='track-bass'),8);self.assertFalse(any(x['absolute_tick']>=136*BAR and x['track_id'] in UPPER|{'track-bass','track-sub-pulse'} for x in rows));self.assertTrue(all(self.a['per_bar_kick_onsets'][136:]))
 def test_no_lead_arp_extra_track_or_hidden_single_note_hook(self):
  self.assertFalse(REMOVED&{t.id for t in self.p.tracks});self.assertEqual({t.id for t in self.p.tracks},{t.id for t in self.source.tracks});self.assertTrue(self.a['no_lead_arp_or_new_instrument']);self.assertTrue(all(x['duration']>=8*PPQ for x in event_rows(self.p) if x['track_id']=='track-depth-pad'))
 def test_whole_song_active_and_release_bass_harmony_concurrent_audit(self):
  self.assertFalse(self.a['unexplained_harmonic_intervals']);self.assertGreater(len(self.a['harmonic_active_release_intervals']),3000);self.assertEqual(self.a['release_budgets_seconds']['track-depth-pad'],2.)
 def test_upper_performance_develops_beyond_nine_identical_copies(self):
  self.assertGreaterEqual(self.a['unique_upper_shapes'],10);self.assertGreaterEqual(self.a['unique_eight_bar_shapes'],10)
  rows=event_rows(self.p);self.assertIn(58,{x['pitch'] for x in rows if x['track_id']=='track-depth-pad' and 112*BAR<=x['absolute_tick']<128*BAR});self.assertIn(55,{x['pitch'] for x in rows if x['track_id']=='track-harmony' and 48*BAR<=x['absolute_tick']<64*BAR})
 def test_actual_lane_bounds_1000hz_profile_floor_and_throw_attack_windows(self):
  specs={x.id:x for x in self.p.parameters}
  for a in self.p.automation:
   self.assertTrue(all(specs[a.parameter_id].minimum<=x.value<=specs[a.parameter_id].maximum and 0<=x.tick<=self.p.length for x in a.points))
  a=next(a for a in self.p.automation if a.target_id=='effect-harmony-eq' and a.parameter_id=='soundcraft.hpf_freq');self.assertGreater(max(x.value for x in a.points if 72*BAR<x.tick<80*BAR),400)
 def test_original_source_spec_immutable_cross_process_score_midi_journal(self):
  before=dumps(self.source);self.assertEqual(self.p.metadata['song_spec'],self.source.metadata['song_spec']);root=Path(__file__).resolve().parents[1];w=root/'.local/phase24/tmp';w.mkdir(parents=True,exist_ok=True)
  code='import sys,json,hashlib; from unittest.mock import patch; from kuang.schema import load,state_hash; from kuang.groove_record import arrange_groove; from kuang.midi import export_bytes; s=load(sys.argv[1]); scope=patch("kuang.groove_record.SOURCE_HASH",state_hash(s)); scope.start(); p,r=arrange_groove(s); print(json.dumps([state_hash(p),hashlib.sha256(export_bytes(p)).hexdigest(),hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()]))'
  with tempfile.TemporaryDirectory(dir=w) as d:
   path=Path(d)/'source.json';save(self.source,path);out=[subprocess.check_output([sys.executable,'-c',code,str(path)],cwd=root,text=True,env={**os.environ,'PYTHONHASHSEED':seed}) for seed in ('1','2')]
  self.assertEqual(out[0],out[1]);self.assertEqual(dumps(self.source),before)
 def test_locked_unknown_source_and_changed_anchor_or_source_graph_rejected(self):
  with self.assertRaises(ValidationError):arrange_groove(self.source)
  s=deepcopy(self.source);s.locks=[Lock('keep','track-bass',None)]
  with patch('kuang.groove_record.SOURCE_HASH',state_hash(s)):
   with self.assertRaises(ValidationError):arrange_groove(s)
  p=deepcopy(self.p);r=deepcopy(self.r);next(t for t in p.tracks if t.id=='track-bass').controls['mixer.pan']=.1;r['candidate_hash']=state_hash(p)
  with self.assertRaises(ValidationError):self.check(p,r)
 def test_key_legal_wrong_chord_and_forged_note_origin_fail_closed(self):
  p=deepcopy(self.p);r=deepcopy(self.r);n=next(n for t in p.tracks if t.id=='track-harmony' for c in t.clips for n in c.notes if c.start==48*BAR);n.pitch=56
  x=next(x for x in event_rows(p) if x['id']==n.id);r['note_origins'][n.id]['actual']=x;r['candidate_hash']=state_hash(p)
  with self.assertRaisesRegex(ValidationError,'chord/bass conflict'):self.check(p,r)
  r=deepcopy(self.r);next(iter(r['note_origins'].values()))['source']['velocity']=1
  with self.assertRaises(ValidationError):self.check(self.p,r)
