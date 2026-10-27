"""Scoped rhythm repair, source design and production invariants, no taste score."""
import json,os,subprocess,sys,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from kuang.schema import BAR,PPQ,Lock,ParameterSpec,ValidationError,state_hash,dumps,save
from kuang.production_refinement import refine_record,audit_refinement,refined_patch,EXTRA_GHOSTS,SHIFT_BARS,PROTECTED
from kuang.composition_analysis import event_rows
from kuang.vitalium_patch import original_patch,component,component_patch

class ProductionRefinementTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import test_groove_record as record
  record.GrooveRecordTests.setUpClass();cls.s=deepcopy(record.GrooveRecordTests.p)
  # Symbolic ancestor lacks Phase20's captured EQ input spec; model that known
  # existing native registry entry explicitly, never infer a host capability.
  if not any(s.id=='soundcraft.input_gain' for s in cls.s.parameters):cls.s.parameters.append(ParameterSpec('soundcraft.input_gain','dB',-24,24,0,['effect']))
  with patch('kuang.production_refinement.SOURCE_HASH',state_hash(cls.s)):
   cls.p,cls.r=refine_record(cls.s);cls.a=audit_refinement(cls.s,cls.p,cls.r)
 def check(self,p,r):
  with patch('kuang.production_refinement.SOURCE_HASH',state_hash(self.s)):return audit_refinement(self.s,p,r)
 def test_all_144_bars_sections_key_meter_and_registry_exact(self):
  for k in ('sections','bars','tempo_bpm','key_tonic','key_mode','time_signature','ppq','parameters'):self.assertEqual(getattr(self.s,k),getattr(self.p,k))
  self.assertEqual(self.p.bars,144)
 def test_entire_501_note_anchor_MIDI_exact_not_falsely_audio_exact(self):
  self.assertEqual([x for x in event_rows(self.s) if 16*BAR<=x['absolute_tick']<32*BAR],[x for x in event_rows(self.p) if 16*BAR<=x['absolute_tick']<32*BAR]);self.assertEqual(self.a['anchor_MIDI_exact'],501);self.assertFalse(self.a['anchor_upper_audio_exact'])
 def test_only_four_added_ghosts_removed_source_late_ghosts_retained(self):
  a={x['id']:x for x in event_rows(self.s)};b={x['id']:x for x in event_rows(self.p)};self.assertEqual(set(a)-set(b),EXTRA_GHOSTS);self.assertFalse(set(b)-set(a))
  for bar in (63,79,111,127):self.assertTrue(any(x['track_id']=='track-snare.p38' and x['absolute_tick']==bar*BAR+round(3.75*PPQ)+26 for x in b.values()))
 def test_twelve_voice_onsets_restored_with_source_hand_strum_preserved(self):
  old={x['id']:x for x in event_rows(self.s)};moved=[]
  for x in event_rows(self.p):
   prior=old[x['id']]
   if x!=prior:
    self.assertEqual(x['track_id'],'track-harmony');self.assertIn(prior['absolute_tick']//BAR,SHIFT_BARS);self.assertEqual(x['absolute_tick'],prior['absolute_tick']-120);self.assertEqual(x['start'],prior['start']-120)
    self.assertEqual({k:v for k,v in x.items() if k not in ('start','absolute_tick')},{k:v for k,v in prior.items() if k not in ('start','absolute_tick')});moved.append(x)
  self.assertEqual(len(moved),12)
 def test_seven_protected_rhythm_tracks_instruments_FX_gain_routes_exact(self):
  by={t.id:t for t in self.p.tracks}
  for t in self.s.tracks:
   if t.id in PROTECTED-{'track-snare.p38'}:self.assertEqual(t,by[t.id])
 def test_bass_transition_omissions_and_all_kick_clock_events_untouched(self):
  for tid in ('track-kick','track-bass','track-sub-pulse'):
   self.assertEqual([x for x in event_rows(self.s) if x['track_id']==tid],[x for x in event_rows(self.p) if x['track_id']==tid])
  self.assertTrue(self.a['bass_omissions_intentionally_retained'])
 def test_original_Fourier_sources_and_tuning_no_new_layer_or_pitch_routes(self):
  for voice,role in [('stab','pluck'),('pad','pad')]:
   p=refined_patch(voice);s=p['settings'];self.assertEqual(p,component_patch(component(p)));self.assertEqual(s['wavetables'],original_patch(role)['settings']['wavetables']);self.assertEqual((s['osc_1_transpose'],s['osc_2_transpose'],s['osc_1_unison_voices'],s['osc_2_unison_voices']),(0,0,1,1));self.assertFalse(s['osc_3_on']);self.assertTrue(all('pitch' not in x['destination'] and 'tune' not in x['destination'] for x in s['modulations']))
 def test_two_counterphase_LFO_shapes_real_sync_and_motion_only_bypass(self):
  a=refined_patch('pad')['settings'];b=refined_patch('pad',modulation=False)['settings'];self.assertEqual((a['lfo_1_tempo'],a['lfo_2_tempo'],a['lfo_2_sync'],a['lfo_2_sync_type']),(3,3,1,1))
  self.assertEqual([a['lfos'][0]['points'][i]+a['lfos'][1]['points'][i] for i in (1,3,5)],[1,1,1]);self.assertTrue(all(not x['source'].startswith('lfo_') for x in b['modulations']));self.assertEqual({x['source'] for x in b['modulations']},{'env_2','velocity'});self.assertAlmostEqual(a['env_1_release']**4,1.65)
 def test_actual_physical_EQ_bounds_and_selective_pad_opening(self):
  specs={s.id:s for s in self.p.parameters}
  for lane in self.p.automation:self.assertTrue(all(specs[lane.parameter_id].minimum<=x.value<=specs[lane.parameter_id].maximum for x in lane.points))
  for tid in ('track-harmony','track-depth-pad'):
   eq=next(e for t in self.p.tracks if t.id==tid for e in t.effects if e.plugin_ref=='soundcraft:eq_7band');self.assertLess(eq.parameters['soundcraft.low_mid_gain'],0)
  lane=next(a for a in self.p.automation if a.target_id=='effect-depth-pad-eq' and a.parameter_id=='soundcraft.lpf_freq');self.assertGreater(max(x.value for x in lane.points),6000)
 def test_no_extra_lane_point_novelty_return_duck_halved_and_break_calm(self):
  self.assertEqual(len(self.p.automation),len(self.s.automation));self.assertEqual(sum(len(a.points) for a in self.p.automation),sum(len(a.points) for a in self.s.automation))
  a=next(a for a in self.s.automation if a.target_id=='phase17-dark-space' and a.parameter_id=='mixer.gain_db');b=next(b for b in self.p.automation if b.id==a.id)
  for x,y in zip(a.points,b.points):
   self.assertEqual((x.id,x.tick,x.shape),(y.id,y.tick,y.shape))
   if 64*BAR<=x.tick<72*BAR:self.assertEqual(x.value,y.value)
  self.assertTrue(all(y.value>=x.value for x,y in zip(a.points,b.points)))
 def test_same_source_independent_process_score_MIDI_receipt_and_no_mutation(self):
  root=Path(__file__).resolve().parents[1];w=root/'.local/phase25/tmp';w.mkdir(parents=True,exist_ok=True);before=dumps(self.s)
  code='import sys,json,hashlib;from unittest.mock import patch;from kuang.schema import load,state_hash;from kuang.production_refinement import refine_record;from kuang.midi import export_bytes;s=load(sys.argv[1]);scope=patch("kuang.production_refinement.SOURCE_HASH",state_hash(s));scope.start();p,r=refine_record(s);print(json.dumps([state_hash(p),hashlib.sha256(export_bytes(p)).hexdigest(),hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()]))'
  with tempfile.TemporaryDirectory(dir=w) as d:
   f=Path(d)/'s.json';save(self.s,f);rows=[subprocess.check_output([sys.executable,'-c',code,str(f)],cwd=root,text=True,env={**os.environ,'PYTHONHASHSEED':seed}) for seed in ('1','2')]
  self.assertEqual(rows[0],rows[1]);self.assertEqual(dumps(self.s),before);self.assertEqual(self.p.metadata['song_spec'],self.s.metadata['song_spec'])
 def test_source_drift_locks_unknown_voice_and_undeclared_edits_fail_closed(self):
  with self.assertRaises(ValidationError):refine_record(self.s)
  with self.assertRaises(ValidationError):refined_patch('lead')
  s=deepcopy(self.s);s.locks=[Lock('protect','track-bass',None)]
  with patch('kuang.production_refinement.SOURCE_HASH',state_hash(s)):
   with self.assertRaises(ValidationError):refine_record(s)
  p=deepcopy(self.p);r=deepcopy(self.r);next(t for t in p.tracks if t.id=='track-bass').controls['mixer.pan']=.1;r['candidate_hash']=state_hash(p)
  with self.assertRaises(ValidationError):self.check(p,r)
 def test_no_lead_master_new_assets_or_forged_remove_scope(self):
  self.assertEqual({t.id for t in self.p.tracks},{t.id for t in self.s.tracks});self.assertFalse(self.p.tracks[-1].effects);self.assertFalse(self.r['mastering'])
  r=deepcopy(self.r);r['note_edits'][0]['before']['velocity']=1
  with self.assertRaises(ValidationError):self.check(self.p,r)
