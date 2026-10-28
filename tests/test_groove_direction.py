import unittest
from copy import deepcopy
from unittest.mock import patch
from dataclasses import asdict
from kuang.schema import state_hash,ValidationError,BAR
from kuang.composition_analysis import event_rows
from kuang.groove_direction import compose_direction,audit_direction,function,VOICES
class DirectionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from test_production_refinement import ProductionRefinementTests as Prior
  Prior.setUpClass();cls.s=deepcopy(Prior.p)
  # The symbolic ancestor predates the captured Phase20/25 kick-fader lane.
  # Model its known flat -3dB source state explicitly; this is not host proof.
  from kuang.schema import AutomationLane,AutomationPoint
  cls.s.automation.append(AutomationLane('phase20-kick-startup','track-kick','mixer.gain_db',[AutomationPoint('symbolic-kick-'+str(b),b*BAR,-3.,'linear') for b in (0,16,32,48,64,80,96,112,128,144)]))
  with patch('kuang.groove_direction.SOURCE_HASH',state_hash(cls.s)):cls.p,cls.r=compose_direction(cls.s);cls.a=audit_direction(cls.s,cls.p,cls.r)
 def test_exact_anchor_notes_clips_and_performance(self):
  for a,b in zip(self.s.tracks,self.p.tracks):self.assertEqual([c for c in a.clips if 16*BAR<=c.start<32*BAR],[c for c in b.clips if 16*BAR<=c.start<32*BAR])
  for a,b in zip(self.s.automation,self.p.automation):self.assertEqual([x for x in a.points if 16*BAR<=x.tick<=32*BAR],[x for x in b.points if 16*BAR<=x.tick<=32*BAR])
  self.assertEqual(self.a['anchor_notes_exact'],501)
 def test_bass_and_sub_pocket_exact_except_pitch(self):
  for tid in ('track-bass','track-sub-pulse'):
   rows=lambda p:[{k:v for k,v in x.items() if k!='pitch'} for x in event_rows(p) if x['track_id']==tid]
   self.assertEqual(rows(self.s),rows(self.p))
 def test_percussion_after_intro_and_repaired_ghosts_exact(self):
  rows=lambda p:[x for x in event_rows(p) if x['track_id'] in ('track-kick','track-snare','track-snare.p38','track-hats','track-hats.p46','track-percussion') and x['absolute_tick']>=16*BAR]
  self.assertEqual(rows(self.s),rows(self.p))
 def test_dominant_leading_tone_resolves_and_common_voice_stays(self):
  self.assertEqual(VOICES['V'],(55,59,65));self.assertEqual(VOICES['i'],(55,60,63));self.assertEqual([function(i) for i in range(40,49)],['iv']*4+['Vsus']*2+['V']*2+['i'])
  self.assertEqual(function(80),'i');self.assertFalse(self.a['harmonic_errors'])
 def test_no_new_sources_or_master_and_form_exact(self):
  self.assertEqual(self.s.sections,self.p.sections);self.assertEqual(self.p.bars,144)
  for a,b in zip(self.s.tracks,self.p.tracks):
   x,y=asdict(a),asdict(b);x.pop('clips');y.pop('clips');self.assertEqual(x,y)
 def test_staged_intro_delays_upper_bed_until_twelve(self):
  lane=next(a for a in self.p.automation if a.target_id=='track-kick');self.assertEqual(lane.points[0].value,-5);self.assertEqual(next(x.value for x in lane.points if x.tick==16*BAR),-3)
  rows=event_rows(self.p);self.assertFalse(any(x['track_id'] in ('track-harmony','track-depth-pad') and x['absolute_tick']<12*BAR for x in rows));self.assertTrue(any(x['track_id']=='track-bass' and x['absolute_tick']//BAR==8 for x in rows))
 def test_source_drift_and_unreceipted_change_rejected(self):
  with self.assertRaises(ValidationError):compose_direction(self.s)
  p=deepcopy(self.p);p.tracks[0].clips[0].notes[0].velocity-=1
  with patch('kuang.groove_direction.SOURCE_HASH',state_hash(self.s)):
   with self.assertRaises(ValidationError):audit_direction(self.s,p,self.r)
 def test_determinism_source_immutable_and_note_lineage(self):
  h=state_hash(self.s)
  with patch('kuang.groove_direction.SOURCE_HASH',h):q,r=compose_direction(self.s)
  self.assertEqual((q,r),(self.p,self.r));self.assertEqual(h,state_hash(self.s));self.assertTrue(all(x['before']['id'] for x in r['events']))
