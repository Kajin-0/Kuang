"""Musical record contracts; symbolic validity does not establish preference."""
import unittest
from copy import deepcopy
from dataclasses import asdict
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.house_composition import compose_record,FORM,CHORDS
from kuang.composition_analysis import audit_composition,event_rows
from kuang.schema import BAR,PPQ,load,dumps,state_hash,validate,ValidationError
from kuang.midi import export_bytes
from kuang.gestures import lane_value
from kuang.production_host import graph_contract

class HouseCompositionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # A symbolic surrogate with the same performance/graph; no optional binary
  # or ignored release is needed in CI. Native tests use the sealed real B.
  base=repaired_house(split_house(atmosphere_house())[0])[0]
  for t in base.tracks:
   if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
  with patch('kuang.mix_polish.SOURCE_HASH',state_hash(base)):cls.source=polished_mix(base)[0]
  with patch('kuang.house_composition.SOURCE_HASH',state_hash(cls.source)):cls.p,cls.r=compose_record(cls.source)
  cls.a=audit_composition(cls.source,cls.p,cls.r)
 def proposal(self):
  with patch('kuang.house_composition.SOURCE_HASH',state_hash(self.source)):return compose_record(self.source)
 def test_exact_160_bar_form_eight_functions_and_valid_boundaries(self):
  p=self.p;validate(p);self.assertEqual(p.bars,160);self.assertEqual(p.sections[0].start,0);self.assertEqual(p.sections[-1].start+p.sections[-1].length,160*BAR)
  self.assertEqual([s.length//BAR for s in p.sections],[16,16,32,16,16,16,32,16]);self.assertEqual(len(self.r['phrases']),20)
  self.assertTrue(all(c.start+n.start+n.duration<=p.length for t in p.tracks for c in t.clips for n in c.notes));self.assertEqual(p.metadata['song_spec'],self.source.metadata['song_spec'])
 def test_source_immutable_deterministic_complete_receipt_and_new_MIDI(self):
  before=dumps(self.source);q,r=self.proposal();self.assertEqual(dumps(q),dumps(self.p));self.assertEqual(r,self.r);self.assertEqual(dumps(self.source),before)
  self.assertNotEqual(export_bytes(q),export_bytes(self.source));self.assertFalse(r['MIDI_bytes_exact']);self.assertTrue(r['not_transaction_receipt'])
 def test_wrong_source_and_lock_fail_closed(self):
  with self.assertRaises(ValidationError):compose_record(self.source)
  q=deepcopy(self.source);q.name+=' drift'
  with self.assertRaises(ValidationError):compose_record(q)
  from kuang.schema import Lock
  q=deepcopy(self.source);q.locks=[Lock('test-lock',q.tracks[0].id,None)]
  with patch('kuang.house_composition.SOURCE_HASH',state_hash(q)):
   with self.assertRaises(ValidationError):compose_record(q)
 def test_entire_approved_source_palette_mixer_fx_sends_registry_retained(self):
  self.assertEqual(self.p.parameters,self.source.parameters)
  for t,u in zip(self.source.tracks,self.p.tracks):
   a=asdict(t);b=asdict(u);a.pop('clips');b.pop('clips');self.assertEqual(a,b)
  graph_contract(self.p)
 def test_original_statement_and_translated_return_actual_fields(self):
  rows={x['id']:x for x in event_rows(self.p)}
  for x in event_rows(self.source):
   if not 32*BAR<=x['absolute_tick']<48*BAR:continue
   self.assertEqual(rows[x['id']],x);y=rows['phase18-return-'+x['id']]
   self.assertEqual(y['absolute_tick'],x['absolute_tick']+80*BAR)
   for k in ('pitch','velocity','duration','channel'):self.assertEqual(y[k],x[k])
 def test_eighteen_musical_phrase_signatures_ignore_velocity_and_ids(self):
  self.assertEqual(self.a['unique_eight_bar_signatures_without_velocity'],18)
  self.assertTrue(all(x['notes']>0 and x['function'] for x in self.a['phrases']))
  self.assertNotEqual(self.a['phrases'][6]['signature_without_velocity'],self.a['phrases'][16]['signature_without_velocity'])
 def test_harmony_every_active_interval_and_paired_bridge_roots(self):
  for k in ('out_of_key_intervals','non_chord_harmonic_layer_intervals','non_chord_bass_intervals','bridge_wrong_root_note_ids'):self.assertFalse(self.a[k],k)
  self.assertGreater(len(self.a['concurrent_intervals']),2000);self.assertTrue(self.a['melodic_color_intervals'])
  self.assertLessEqual(max(abs(n) for x in self.a['bridge_voice_leading'] for n in x['semitones']),3)
  roots={x['pitch'] for x in event_rows(self.p) if x['track_id']=='track-bass' and 64*BAR<=x['absolute_tick']<80*BAR};self.assertEqual(roots,{32,39,41,34})
 def test_audit_rejects_invented_provenance_and_reports_in_key_wrong_bass(self):
  r=deepcopy(self.r);nid=next(iter(r['note_origins']));r['note_origins'][nid]['destination_tick']+=1
  with self.assertRaises(ValidationError):audit_composition(self.source,self.p,r)
  q=deepcopy(self.p);n=next(n for t in q.tracks if t.id=='track-bass' for c in t.clips for n in c.notes if c.start+n.start==64*BAR+492)
  n.pitch=36;r=deepcopy(self.r);r['note_origins'][n.id]['note']=asdict(n);r['candidate_hash']=state_hash(q)
  a=audit_composition(self.source,q,r);self.assertTrue(a['bridge_wrong_root_note_ids']);self.assertFalse(a['non_chord_bass_intervals']);self.assertFalse(a['out_of_key_intervals'])
  # C is a valid Ab chord third, but violates this explicit root-position plan.
 def test_mixable_bookends_lead_absent_intro_and_last_eight_unpitched(self):
  rows=event_rows(self.p);self.assertFalse(any(x['track_id']=='track-lead' and x['absolute_tick']<16*BAR for x in rows))
  drums={'track-kick','track-snare','track-snare.p38','track-hats','track-hats.p46','track-percussion'}
  self.assertFalse(any(x['track_id'] not in drums and x['absolute_tick']+x['duration']>152*BAR for x in rows))
  for bar in list(range(16))+list(range(144,160)):
   kicks=[x['absolute_tick']-bar*BAR for x in rows if x['track_id']=='track-kick' and bar*BAR<=x['absolute_tick']<(bar+1)*BAR];self.assertEqual(kicks,[0,PPQ,2*PPQ,3*PPQ])
 def test_breakdown_and_pre_drop_note_silences_are_real(self):
  rows=event_rows(self.p);self.assertFalse(any(x['track_id'] in ('track-kick','track-bass','track-sub-pulse') and 80*BAR<=x['absolute_tick']<96*BAR for x in rows))
  self.assertFalse(any(95*BAR<=x['absolute_tick']+x['duration'] and x['absolute_tick']<96*BAR for x in rows))
  self.assertFalse(any(x['absolute_tick']<112*BAR and x['absolute_tick']+x['duration']>111*BAR+3*PPQ for x in rows))
 def test_native_automation_bounds_endpoints_echo_and_drop_reset(self):
  p=self.p;specs={x.id:x for x in p.parameters}
  for a in p.automation:
   self.assertEqual(len(a.points),len({x.tick for x in a.points}));self.assertTrue(all(0<=x.tick<=160*BAR and specs[a.parameter_id].minimum<=x.value<=specs[a.parameter_id].maximum for x in a.points))
  a=next(a for a in p.automation if a.target_id=='effect-lead-eq' and a.parameter_id=='soundcraft.hpf_freq')
  self.assertGreater(lane_value(a,112*BAR-1),800);self.assertLess(lane_value(a,112*BAR),400)
  e=next(a for a in p.automation if a.parameter_id.startswith('route.') and a.target_id=='track-lead')
  self.assertEqual(e.points[0].value,-60);self.assertEqual(e.points[-1].value,-60);self.assertTrue(any(x.tick>128*BAR and x.value==0 for x in e.points))
 def test_all_note_ids_have_actual_origins_and_fills_keep_sample_keys(self):
  self.assertEqual(len(self.r['note_origins']),sum(len(c.notes) for t in self.p.tracks for c in t.clips))
  pitches={'track-kick':36,'track-snare':39,'track-snare.p38':38,'track-hats':42,'track-hats.p46':46,'track-percussion':44}
  for t in self.p.tracks:
   if t.id in pitches:self.assertEqual({n.pitch for c in t.clips for n in c.notes},{pitches[t.id]})
 def test_short_sine_meter_independent_decaying_vectors_and_silence(self):
  import tempfile,wave,math
  from pathlib import Path
  from tools.phase18_verify import short_sine_pitch
  scratch=Path(__file__).resolve().parents[1]/'.local/phase18/unit-audio';scratch.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(dir=scratch) as d:
   for n in (36,41):
    path=Path(d)/(str(n)+'.wav');frequency=440*2**((n-69)/12)
    with wave.open(str(path),'wb') as w:
     w.setparams((2,3,48000,0,'NONE','not compressed'))
     data=[]
     for i in range(9600):
      t=i/48000;v=.12*min(t/.008,1)*math.exp(-t/.028)*math.sin(2*math.pi*frequency*t+.31) if t<.11 else 0
      data.append(round(v*(2**23-1)).to_bytes(3,'little',signed=True)*2)
     w.writeframes(b''.join(data))
    for a,b in ((.015,.085),(.025,.095),(.035,.105)):
     r=short_sine_pitch(path,n,a,b);self.assertLess(abs(r['period_cents']),.2);self.assertGreaterEqual(r['observed_periods'],3)
    with self.assertRaises(ValidationError):short_sine_pitch(path,n,.12,.20)
    if n==41:self.assertAlmostEqual(short_sine_pitch(path,36,.025,.095)['period_cents'],500,delta=.2)
