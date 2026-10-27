"""One melody-free score/palette; no preference claim from contract checks."""
import json,os,subprocess,sys,tempfile,unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from kuang.schema import BAR,PPQ,Lock,ValidationError,save,dumps,state_hash
from kuang.chord_bed import compose_bed,audit_bed,bed_patch,PROTECTED,UPPER,REMOVED
from kuang.composition_analysis import event_rows
from kuang.vitalium_patch import component,component_patch,original_patch

class ChordBedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # Existing symbolic ancestor fixture only; real tests use sealed actual A.
  import test_house_theme as theme
  from kuang.house_shortlist import main_reference
  theme.HouseThemeTests.setUpClass();s=theme.HouseThemeTests.p
  with patch('kuang.house_shortlist.SOURCE_HASH',state_hash(s)):cls.ref=main_reference(s)
  with patch('kuang.chord_bed.REFERENCE_HASH',state_hash(cls.ref)):
   cls.p,cls.r=compose_bed(cls.ref);cls.audit=audit_bed(cls.ref,cls.p,cls.r)
 def check(self,p=None,r=None):
  with patch('kuang.chord_bed.REFERENCE_HASH',state_hash(self.ref)):return audit_bed(self.ref,p or self.p,r or self.r)
 def test_lead_arp_and_ornamental_roles_actually_deleted_not_quieted(self):
  self.assertFalse(REMOVED&{t.id for t in self.p.tracks});self.assertEqual({t.id for t in self.p.tracks if t.kind=='midi'}-PROTECTED,UPPER)
  self.assertFalse(any(x['track_id'] in REMOVED for x in event_rows(self.p)));self.assertTrue(self.audit['lead_arp_air_tracks_and_notes_absent'])
 def test_all_eight_rhythm_tracks_full_equal_every_note_and_device_field(self):
  by={t.id:t for t in self.p.tracks}
  for t in self.ref.tracks:
   if t.id in PROTECTED:self.assertEqual(t,by[t.id])
 def test_shared_returns_routes_and_protected_automation_exact(self):
  by={t.id:t for t in self.p.tracks}
  for t in self.ref.tracks:
   if t.kind=='bus':self.assertEqual(t,by[t.id])
  self.assertTrue(self.audit['shared_bus_and_rhythm_expression_exact']);self.assertEqual(self.p.sections,self.ref.sections);self.assertEqual(self.p.parameters,self.ref.parameters)
 def test_chord_hook_is_polyphonic_not_a_renamed_topline(self):
  ns=[x for x in event_rows(self.p) if x['track_id']=='track-harmony'];self.assertEqual(len(ns),84);self.assertEqual(self.audit['chord_strikes'],28)
  for i in range(0,len(ns),3):self.assertEqual(len(ns[i:i+3]),3);self.assertLessEqual(max(x['absolute_tick'] for x in ns[i:i+3])-min(x['absolute_tick'] for x in ns[i:i+3]),8)
 def test_pad_common_voice_motion_long_gates_and_no_short_ornaments(self):
  ns=[x for x in event_rows(self.p) if x['track_id']=='track-depth-pad'];self.assertEqual(len(ns),6);self.assertTrue(all(x['duration']>8*PPQ for x in ns));self.assertEqual({x['pitch'] for x in ns if x['duration']>12*BAR},{63,67})
  self.assertEqual([x['pitch'] for x in ns if x['duration']<12*BAR],[74,77,72,74])
 def test_all_active_and_releasing_chords_fit_unchanged_actual_low_notes(self):
  self.assertFalse(self.audit['unexplained_harmonic_intervals']);self.assertGreater(len(self.audit['active_and_release_intervals']),400);self.assertEqual(self.audit['release_budgets_seconds']['pad'],2.0)
 def test_synth_sources_are_original_tuned_two_oscillators_no_pitch_modulation(self):
  for voice,role in [('stab','pluck'),('pad','pad')]:
   p=bed_patch(voice);s=p['settings'];self.assertEqual(s['wavetables'],original_patch(role)['settings']['wavetables']);self.assertEqual(component_patch(component(p)),p)
   self.assertEqual((s['osc_1_unison_voices'],s['osc_2_unison_voices'],s['osc_1_transpose'],s['osc_2_transpose']),(1,1,0,0));self.assertFalse(s['osc_3_on']);self.assertFalse(s['reverb_on']);self.assertTrue(all('pitch' not in x['destination'] and 'tune' not in x['destination'] for x in s['modulations']))
 def test_envelope_articulation_and_real_slow_tempo_enum(self):
  a=bed_patch('stab')['settings'];b=bed_patch('pad')['settings'];self.assertAlmostEqual(a['env_1_attack']**4,.007);self.assertAlmostEqual(a['env_1_release']**4,.17);self.assertAlmostEqual(b['env_1_attack']**4,.75);self.assertAlmostEqual(b['env_1_release']**4,1.8);self.assertEqual((a['lfo_1_tempo'],b['lfo_1_tempo']),(4,3));self.assertEqual(b['lfo_1_sync_type'],1)
 def test_native_lanes_have_four_bar_gestures_with_bounds_and_preserved_pump(self):
  specs={s.id:s for s in self.p.parameters}
  for a in self.p.automation:self.assertTrue(all(0<=x.tick<=16*BAR and specs[a.parameter_id].minimum<=x.value<=specs[a.parameter_id].maximum for x in a.points))
  for tid in ('effect-harmony-eq','effect-depth-pad-eq'):
   a=next(a for a in self.p.automation if a.target_id==tid and a.parameter_id=='soundcraft.lpf_freq');self.assertEqual([x.tick for x in a.points],[i*4*BAR for i in range(5)])
 def test_source_immutable_cross_process_score_receipt_determinism(self):
  root=Path(__file__).resolve().parents[1];w=root/'.local/phase23/tmp';w.mkdir(parents=True,exist_ok=True);before=dumps(self.ref)
  code='import sys,json,hashlib; from unittest.mock import patch; from kuang.schema import load,state_hash; from kuang.chord_bed import compose_bed; from kuang.midi import export_bytes; s=load(sys.argv[1]); scope=patch("kuang.chord_bed.REFERENCE_HASH",state_hash(s)); scope.start(); p,r=compose_bed(s); print(json.dumps([state_hash(p),hashlib.sha256(export_bytes(p)).hexdigest(),hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()]))'
  with tempfile.TemporaryDirectory(dir=w) as d:
   path=Path(d)/'ref.json';save(self.ref,path);rows=[subprocess.check_output([sys.executable,'-c',code,str(path)],cwd=root,text=True,env={**os.environ,'PYTHONHASHSEED':k}) for k in ('1','2')]
  self.assertEqual(rows[0],rows[1]);self.assertEqual(dumps(self.ref),before)
 def test_note_and_deleted_role_lineage_source_spec_complete(self):
  self.assertEqual(set(self.r['note_origins']),{x['id'] for x in event_rows(self.p)});self.assertEqual({x['track_id'] for x in self.r['removed_notes']},UPPER|REMOVED);self.assertEqual(self.p.metadata['song_spec'],self.ref.metadata['song_spec']);self.assertFalse(self.r['mastering']);self.assertFalse(self.r['full_song'])
 def test_locks_source_drift_unknown_voice_and_undeclared_gain_fail_closed(self):
  with self.assertRaises(ValidationError):compose_bed(self.ref)
  with self.assertRaises(ValidationError):bed_patch('lead')
  s=deepcopy(self.ref);s.locks=[Lock('keep-pocket','track-bass',None)]
  with patch('kuang.chord_bed.REFERENCE_HASH',state_hash(s)):
   with self.assertRaises(ValidationError):compose_bed(s)
  p=deepcopy(self.p);r=deepcopy(self.r);next(t for t in p.tracks if t.id=='track-bass').controls['mixer.gain_db']+=1;r['candidate_hash']=state_hash(p)
  with self.assertRaises(ValidationError):self.check(p,r)
 def test_tampered_key_legal_held_chord_and_forged_ancestry_rejected(self):
  p=deepcopy(self.p);r=deepcopy(self.r);n=next(n for t in p.tracks if t.id=='track-depth-pad' for c in t.clips for n in c.notes if n.pitch==77);n.duration=6*BAR;r['candidate_hash']=state_hash(p)
  with self.assertRaises(ValidationError):self.check(p,r)
  r=deepcopy(self.r);next(iter(r['note_origins'].values()))['source']['velocity']=1
  with self.assertRaises(ValidationError):self.check(self.p,r)
