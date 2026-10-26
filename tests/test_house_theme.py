"""Musical performance invariants; actual audio and preference are separate."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict
from unittest.mock import patch
from kuang.schema import BAR,PPQ,Lock,ValidationError,dumps,state_hash,save
from kuang.house_theme import compose_theme,harmonic_plan,EDITABLE
from kuang.theme_audit import audit_theme,require_theme,PROTECTED
from kuang.composition_analysis import event_rows
from kuang.midi import export_bytes

class HouseThemeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import test_club_flow as flow
  flow.ClubFlowTests.setUpClass();cls.source=flow.ClubFlowTests.p
  with patch('kuang.house_theme.SOURCE_HASH',state_hash(cls.source)):cls.p,cls.r=compose_theme(cls.source)
  cls.a=audit_theme(cls.source,cls.p,cls.r)
 def propose(self,s=None):
  s=self.source if s is None else s
  with patch('kuang.house_theme.SOURCE_HASH',state_hash(s)):return compose_theme(s)
 def test_complete_drum_bass_subpulse_tracks_exact_not_just_counts(self):
  for a,b in zip(self.source.tracks,self.p.tracks):
   if a.id in PROTECTED:self.assertEqual(a,b)
  self.assertTrue(self.a['kick_counts_exact']);self.assertEqual(self.a['longest_kick_free_bars'],8)
 def test_every_instrument_FX_fader_send_lane_section_and_registry_exact(self):
  self.assertEqual(self.p.sections,self.source.sections);self.assertEqual(self.p.automation,self.source.automation);self.assertEqual(self.p.parameters,self.source.parameters)
  for a,b in zip(self.source.tracks,self.p.tracks):
   x=asdict(a);y=asdict(b);x.pop('clips');y.pop('clips');self.assertEqual(x,y)
  self.assertEqual(self.p.metadata['song_spec'],self.source.metadata['song_spec'])
 def test_deterministic_authored_score_and_full_source_immutability(self):
  before=dumps(self.source);p,r=self.propose();self.assertEqual(dumps(p),dumps(self.p));self.assertEqual(r,self.r);self.assertEqual(dumps(self.source),before);self.assertNotEqual(export_bytes(p),export_bytes(self.source));self.assertFalse(r['MIDI_bytes_exact'])
  root=Path(__file__).resolve().parents[1];scratch=root/'.local/phase21/tests';scratch.mkdir(parents=True,exist_ok=True)
  code='from kuang.schema import load,state_hash; from kuang.house_theme import compose_theme; from kuang.midi import export_bytes; from unittest.mock import patch; import json,hashlib,sys; s=load(sys.argv[1]); scope=patch("kuang.house_theme.SOURCE_HASH",state_hash(s)); scope.start(); p,r=compose_theme(s); print(json.dumps([state_hash(p),hashlib.sha256(export_bytes(p)).hexdigest(),hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()]))'
  with tempfile.TemporaryDirectory(dir=scratch) as d:
   source=Path(d)/'source.kuang.json';save(self.source,source)
   outputs=[subprocess.check_output([sys.executable,'-c',code,str(source)],cwd=root,env={**os.environ,'PYTHONHASHSEED':seed},text=True) for seed in ('1','2')]
  self.assertEqual(outputs[0],outputs[1],'score/MIDI/complete receipt must be deterministic across independent processes')
 def test_actual_four_plus_four_theme_contour_and_recognizable_seed(self):
  rows=sorted((x for x in event_rows(self.p) if x['track_id']=='track-lead' and 32*BAR<=x['absolute_tick']<40*BAR),key=lambda x:x['absolute_tick'])
  self.assertEqual([x['pitch'] for x in rows[:3]],[67,63,65]);self.assertEqual([x['pitch'] for x in rows[-2:]],[74,72]);self.assertEqual(max(x['pitch'] for x in rows),75)
  self.assertTrue(any(33*BAR<=x['absolute_tick']<34*BAR for x in rows));self.assertEqual(rows[-1]['duration'],round(.72*PPQ));self.assertGreater(self.a['phrases'][2]['silent_beats'],20)
 def test_connected_pedal_colors_and_actual_existing_F_root_supported(self):
  plan=self.r['harmonic_plan'];self.assertEqual([x['name'] for x in plan[32:40]],['Cm9','Cm9','Cm11','Cm11','Abmaj9-C','Abmaj9-C','Cm9','Cm9'])
  for x in plan:
   if 5 in x['actual_low_pitch_classes']:self.assertTrue(x['name'].startswith('Fm'))
  self.assertTrue(self.a['voice_leading']);self.assertLessEqual(max(abs(n) for x in self.a['voice_leading'] for n in x['semitones']),5)
 def test_every_active_harmonic_interval_and_short_melodic_color_audited(self):
  require_theme(self.a)
  for k in ('out_of_key_intervals','non_chord_upper_intervals','non_chord_low_intervals','unexplained_new_melodic_colors'):self.assertEqual(self.a[k],[])
  self.assertGreater(len(self.a['concurrent_intervals']),2000)
 def test_pad_is_sustained_performance_and_color_voices_have_release_space(self):
  notes=[x for x in event_rows(self.p) if x['track_id']=='track-depth-pad' and 32*BAR<=x['absolute_tick']<40*BAR]
  held=[x for x in notes if x['duration']>6*BAR];self.assertEqual({x['pitch'] for x in held},{63,67})
  self.assertTrue(all(x['velocity']<75 for x in notes));self.assertGreater(len(notes),len(held))
  for x in notes:
   if x not in held:self.assertGreaterEqual((2*BAR-((x['absolute_tick']% (2*BAR))+x['duration']))/PPQ*60/126,1.64)
 def test_counterline_occupies_new_lead_rests_and_density_recedes(self):
  rows=event_rows(self.p);arp=[x for x in rows if x['track_id']=='track-arp' and 32*BAR<=x['absolute_tick']<40*BAR];lead=[x for x in rows if x['track_id']=='track-lead' and 32*BAR<=x['absolute_tick']<40*BAR]
  self.assertEqual(len(arp),4);self.assertTrue(all(x['velocity']<=59 for x in arp))
  self.assertFalse(any(a['absolute_tick']<l['absolute_tick']+l['duration'] and l['absolute_tick']<a['absolute_tick']+a['duration'] for a in arp for l in lead))
 def test_DJ_bookends_and_breakdown_note_fields_and_timing_preserved(self):
  old={x['id']:x for x in event_rows(self.source)};new={x['id']:x for x in event_rows(self.p)}
  for nid,x in old.items():
   if x['absolute_tick']<16*BAR or 80*BAR<=x['absolute_tick']<88*BAR or x['absolute_tick']>=144*BAR:self.assertEqual(new[nid],x)
 def test_original_provenance_covers_every_new_removed_and_surviving_note(self):
  self.assertEqual(set(self.r['note_origins']),{x['id'] for x in event_rows(self.p)});self.assertTrue(self.a['all_note_lineage_exact']);self.assertTrue(self.a['all_removed_notes_accounted']);self.assertEqual(self.r['human_preference'],'unreviewed');self.assertFalse(self.r['professional_quality_claimed'])
 def test_source_drift_locks_and_unexplained_origin_rejected(self):
  with self.assertRaises(ValidationError):compose_theme(self.source)
  s=deepcopy(self.source);s.locks=[Lock('keep-pocket','track-bass',None)]
  with self.assertRaises(ValidationError):self.propose(s)
  r=deepcopy(self.r);next(iter(r['note_origins'].values()))['source']['pitch']=127
  with self.assertRaises(ValidationError):audit_theme(self.source,self.p,r)
 def altered(self,pitch=None,duration=None):
  p=deepcopy(self.p);r=deepcopy(self.r);n=next(n for t in p.tracks if t.id=='track-depth-pad' for c in t.clips for n in c.notes if n.pitch==74 and c.start==32*BAR)
  if pitch is not None:n.pitch=pitch
  if duration is not None:n.duration=duration
  r['note_origins'][n.id].update(asdict(n));r['candidate_hash']=state_hash(p);return p,r
 def test_key_membership_does_not_excuse_wrong_chord_or_held_color(self):
  p,r=self.altered(pitch=73);a=audit_theme(self.source,p,r)
  with self.assertRaises(ValidationError):require_theme(a)
  p,r=self.altered(duration=5*BAR);a=audit_theme(self.source,p,r);self.assertTrue(a['non_chord_upper_intervals'])
  with self.assertRaises(ValidationError):require_theme(a)
 def test_fake_chord_label_and_protected_velocity_change_fail_closed(self):
  r=deepcopy(self.r);r['harmonic_plan'][32]['name']='Abmaj9-C'
  with self.assertRaises(ValidationError):audit_theme(self.source,self.p,r)
  p=deepcopy(self.p);r=deepcopy(self.r);p.tracks[0].clips[0].notes[0].velocity-=1;r['candidate_hash']=state_hash(p)
  with self.assertRaises(ValidationError):audit_theme(self.source,p,r)
