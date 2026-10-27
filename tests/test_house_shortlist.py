"""Independent composition search; no rendering or taste claim from unit checks."""
import hashlib,json,os,subprocess,sys,tempfile,unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from kuang.schema import BAR,PPQ,Lock,ValidationError,state_hash,dumps,save
from kuang.house_shortlist import main_reference,compose_candidate,UPPER,LOW,DRUMS
from kuang.shortlist_audit import audit_shortlist,require_shortlist
from kuang.composition_analysis import event_rows
from kuang.midi import export_bytes

class HouseShortlistTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # Explicit symbolic CI surrogate. Actual sealed source/audio tested separately.
  import test_house_theme as theme
  theme.HouseThemeTests.setUpClass();cls.full=theme.HouseThemeTests.p
  with patch('kuang.house_shortlist.SOURCE_HASH',state_hash(cls.full)):cls.a=main_reference(cls.full)
  cls.ps={};cls.rs={};cls.audits={}
  for kind in ('soulful','progressive','hypnotic'):
   with patch('kuang.house_shortlist.REFERENCE_HASH',state_hash(cls.a)):p,r=compose_candidate(cls.a,kind)
   cls.ps[kind]=p;cls.rs[kind]=r;cls.audits[kind]=require_shortlist(audit_shortlist(cls.a,p,r))
 def test_exact_main_peak_reference_and_16bar_no_extension(self):
  self.assertEqual(self.a.bars,16);self.assertEqual(self.a.tracks[-1].controls['mixer.gain_db'],-6);self.assertFalse(self.a.tracks[-1].effects)
  old={x['id']:x for x in event_rows(self.full)}
  for x in event_rows(self.a):
   if x['track_id'] in DRUMS|LOW:
    y=old[x['id']];self.assertEqual(x['absolute_tick']+32*BAR,y['absolute_tick']);self.assertEqual(x['duration'],y['duration']);self.assertEqual(x['velocity'],y['velocity']);self.assertEqual(x['pitch'],y['pitch'])
  self.assertTrue(all(p.bars==16 for p in self.ps.values()))
 def test_all_six_drum_tracks_full_exact_and_palette_graph_lanes_unchanged(self):
  for p in self.ps.values():
   for a,b in zip(self.a.tracks,p.tracks):
    if a.id in DRUMS:self.assertEqual(a,b)
    aa=asdict(a);bb=asdict(b);aa.pop('clips');bb.pop('clips');self.assertEqual(aa,bb)
   self.assertEqual(p.automation,self.a.automation);self.assertEqual(p.parameters,self.a.parameters);self.assertEqual(p.sections,self.a.sections)
 def test_bass_sub_note_identity_rhythm_accents_and_clip_order_exact(self):
  old={x['id']:x for x in event_rows(self.a)}
  for p in self.ps.values():
   for x in event_rows(p):
    if x['track_id'] in LOW:self.assertEqual({**x,'pitch':old[x['id']]['pitch']},old[x['id']])
 def test_hypnotic_entire_low_tracks_exact_and_two_moving_root_plans(self):
  for a,b in zip(self.a.tracks,self.ps['hypnotic'].tracks):
   if a.id in LOW:self.assertEqual(a,b)
  for kind,expected in [('soulful',[36,41,32,36,36,32,41,36]),('progressive',[36,36,32,32,39,39,34,36])]:
   rows=event_rows(self.ps[kind]);roots=[next(x['pitch'] for x in rows if x['track_id']=='track-bass' and x['absolute_tick']//BAR==b) for b in range(0,16,2)];self.assertEqual(roots,expected)
   self.assertTrue(self.rs[kind]['pitch_edits'])
 def test_three_independent_melodic_contours_rhythms_and_cadences(self):
  signatures=[]
  for kind,p in self.ps.items():
   rows=[x for x in event_rows(p) if x['track_id']=='track-lead'];signatures.append([(x['absolute_tick'],x['pitch'],x['duration']) for x in rows]);self.assertNotEqual([x['pitch'] for x in rows[:3]],[67,63,65])
   self.assertTrue(all(x['rests_beats']>7 for x in self.audits[kind]['four_bar_themes']))
  self.assertEqual(len({json.dumps(x) for x in signatures}),3)
  self.assertEqual([x['pitches'][-1] for k in self.ps for x in self.audits[k]['four_bar_themes'][-1:]],[60,72,67])
 def test_all_active_chords_bass_functions_and_voice_leading_independently_checked(self):
  for a in self.audits.values():
   require_shortlist(a);self.assertGreater(len(a['active_interval_matrix']),200);self.assertFalse(a['bass_function_errors']);self.assertFalse(a['non_chord_or_key_intervals'])
   self.assertLessEqual(max(abs(n) for x in a['stab_voice_leading'] for n in x['semitones']),5)
 def test_ensemble_pad_inner_support_topline_contrary_motion_and_release(self):
  for k,p in self.ps.items():
   rows=[x for x in event_rows(p) if x['track_id']=='track-depth-pad'];held=[x for x in rows if x['duration']>12*BAR];self.assertEqual([x['pitch'] for x in held],[63]);self.assertFalse(self.audits[k]['pad_release_handoff_errors']);self.assertTrue(all(x['velocity']<=66 for x in rows))
  d=[x for x in event_rows(self.ps['hypnotic']) if x['track_id']=='track-depth-pad' and x['duration']<12*BAR]
  pairs=[[x['pitch'] for x in d if x['absolute_tick']//BAR==b] for b in (0,4,8,12)]
  self.assertEqual(pairs,[[67,74],[65,77],[68,72],[67,74]])
 def test_lineage_removed_and_pitch_only_journal_complete(self):
  for k,p in self.ps.items():
   r=self.rs[k];self.assertEqual(set(r['note_origins']),{x['id'] for x in event_rows(p)});self.assertEqual({x['track_id'] for x in r['removed_notes']},UPPER)
   self.assertTrue(all(x['before']['id']==x['after']['id'] and x['before']['duration']==x['after']['duration'] for x in r['pitch_edits']))
 def test_cross_process_determinism_and_original_immutable(self):
  root=Path(__file__).resolve().parents[1];scratch=root/'.local/phase22/tmp';scratch.mkdir(parents=True,exist_ok=True);before=dumps(self.a)
  code='import sys,json,hashlib; from unittest.mock import patch; from kuang.schema import load,state_hash; from kuang.house_shortlist import compose_candidate; from kuang.midi import export_bytes; s=load(sys.argv[1]); scope=patch("kuang.house_shortlist.REFERENCE_HASH",state_hash(s)); scope.start(); out=[]\nfor k in ("soulful","progressive","hypnotic"):\n p,r=compose_candidate(s,k);out.append([state_hash(p),hashlib.sha256(export_bytes(p)).hexdigest(),hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()])\nprint(json.dumps(out))'
  with tempfile.TemporaryDirectory(dir=scratch) as d:
   path=Path(d)/'a.json';save(self.a,path);outputs=[subprocess.check_output([sys.executable,'-c',code,str(path)],cwd=root,text=True,env={**os.environ,'PYTHONHASHSEED':seed}) for seed in ('1','2')]
  self.assertEqual(outputs[0],outputs[1]);self.assertEqual(dumps(self.a),before)
 def test_unknown_direction_source_drift_and_locks_fail_closed(self):
  with self.assertRaises(ValidationError):compose_candidate(self.a,'soulful')
  for kind in ('anything','mastered'):
   with self.assertRaises(ValidationError):compose_candidate(self.a,kind)
  q=deepcopy(self.a);q.locks=[Lock('phase22-lock','track-bass',None)]
  with patch('kuang.house_shortlist.REFERENCE_HASH',state_hash(q)):
   with self.assertRaises(ValidationError):compose_candidate(q,'soulful')
 def altered(self,kind,track,pitch):
  p=deepcopy(self.ps[kind]);r=deepcopy(self.rs[kind]);t=next(t for t in p.tracks if t.id==track);n=t.clips[0].notes[0];n.pitch=pitch
  x=next(x for x in event_rows(p) if x['id']==n.id);r['note_origins'][n.id].update(x);r['candidate_hash']=state_hash(p);return p,r,n
 def test_key_membership_does_not_excuse_wrong_chord_or_held_release(self):
  p,r,_=self.altered('soulful','track-harmony',53);a=audit_shortlist(self.a,p,r)
  with self.assertRaises(ValidationError):require_shortlist(a)
  p,r,n=self.altered('soulful','track-depth-pad',62);a=audit_shortlist(self.a,p,r);self.assertTrue(a['non_chord_or_key_intervals']);self.assertTrue(a['pad_release_handoff_errors'])
  p=deepcopy(self.ps['progressive']);r=deepcopy(self.rs['progressive']);n=next(n for t in p.tracks if t.id=='track-depth-air' for c in t.clips for n in c.notes if n.start//BAR==11);n.pitch=79
  x=next(x for x in event_rows(p) if x['id']==n.id);r['note_origins'][n.id].update(x);r['candidate_hash']=state_hash(p);a=audit_shortlist(self.a,p,r);self.assertFalse(a['non_chord_or_key_intervals']);self.assertTrue(a['air_release_handoff_errors'])
  with self.assertRaises(ValidationError):require_shortlist(a)
 def test_wrong_bass_root_pulse_and_forged_ancestry_rejected(self):
  p,r,n=self.altered('soulful','track-bass',39);r['pitch_edits'].append({'before':r['note_origins'][n.id]['source'],'after':next(x for x in event_rows(p) if x['id']==n.id),'reason':'forged root'})
  with self.assertRaises(ValidationError):require_shortlist(audit_shortlist(self.a,p,r))
  r=deepcopy(self.rs['progressive']);next(iter(r['note_origins'].values()))['source']['velocity']=1
  with self.assertRaises(ValidationError):audit_shortlist(self.a,self.ps['progressive'],r)
 def test_no_clobber_staging_and_human_choice_no_full_song_or_master(self):
  from tools.phase22_shortlist import build,package
  with self.assertRaises(ValidationError):build(Path(__file__).resolve().parents[1]/'artifacts','missing','missing')
  for p,r in zip(self.ps.values(),self.rs.values()):
   self.assertFalse(r['new_full_song']);self.assertFalse(r['mastering']);self.assertFalse(r['professional_quality_claimed']);self.assertEqual(r['human_preference'],'unreviewed');self.assertEqual(p.metadata['song_spec'],self.a.metadata['song_spec'])
