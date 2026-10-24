"""Musical preservation and fail-closed graph contracts, no quality score."""
import unittest
from copy import deepcopy
from dataclasses import asdict
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.ensemble_production import build_ensemble,isolate,VOICES,DRUMS
from kuang.production_host import graph_contract,add_send_trim,trim_id,add_spread,native_pan,ProductionAdapter
from kuang.producer_patches import production_patch
from kuang.schema import Track,Send,Lock,AutomationLane,AutomationPoint,ParameterSpec,ValidationError,dumps,state_hash,validate
from kuang.midi import export_bytes


def source():return split_house(atmosphere_house())[0]
def proposal(p=None):
    with patch('kuang.ensemble_production.bound_project',side_effect=lambda p,a:deepcopy(p)):
        return build_ensemble(p or source(),{k:'explicit-test-patch' for k in VOICES})


class EnsembleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=source();cls.p,cls.r=proposal(cls.source)
    def test_deterministic_full_song_and_no_source_mutation(self):
        before=dumps(self.source);p,r=proposal(self.source)
        self.assertEqual(dumps(p),dumps(self.p));self.assertEqual(r,self.r)
        self.assertEqual(export_bytes(p),export_bytes(self.p));self.assertEqual(dumps(self.source),before)
    def test_exact_64_bar_six_sections_tempo_key_and_song_spec(self):
        self.assertEqual((self.p.bars,self.p.tempo_bpm,self.p.key_tonic,self.p.key_mode),(64,126,0,'minor'))
        self.assertEqual(self.p.sections,self.source.sections);self.assertEqual(len(self.p.sections),6)
        self.assertEqual(self.p.metadata['song_spec'],self.source.metadata['song_spec']);validate(self.p)
    def test_every_drum_bass_and_main_call_note_field_and_clip_exact(self):
        for t in self.source.tracks:
            if t.id in DRUMS|{'track-bass','track-lead'}:
                other=next(x for x in self.p.tracks if x.id==t.id)
                self.assertEqual(other.clips,t.clips)
        self.assertTrue(self.r['protected_drum_bass_and_main_call_notes_exact'])
    def test_only_declared_upper_voice_and_velocity_changes(self):
        before={n.id:(t.id,c.start,asdict(n)) for t in self.source.tracks for c in t.clips for n in c.notes}
        after={n.id:asdict(n) for t in self.p.tracks for c in t.clips for n in c.notes}
        changes={x['id'] for x in self.r['changed_notes']}
        self.assertEqual({k for k,(_,_,v) in before.items() if after[k]!=v},changes)
        for row in self.r['changed_notes']:
            tid,start,n=before[row['id']];self.assertEqual(tid,'track-harmony')
            self.assertTrue(32*3840<=start+n['start']<48*3840)
            for key in ('id','start','duration','channel'):self.assertEqual(row['before'][key],row['after'][key])
            self.assertIn(row['after']['pitch']-n['pitch'],(0,12))
    def test_eight_harmonically_valid_pickups_no_removed_notes(self):
        self.assertEqual(len(self.r['added_response_notes']),8);self.assertEqual(self.r['removed_note_ids'],[])
        for row in self.r['added_response_notes']:
            self.assertEqual(row['track'],'track-arp');self.assertIn(row['note']['pitch']%12,(0,2,3,5,7,8,10))
        self.assertEqual(sum(len(c.notes) for t in self.p.tracks for c in t.clips),1544)
    def test_chord_fundamentals_restored_and_no_bass_stereo_spread(self):
        by={t.id:t for t in self.p.tracks}
        self.assertEqual(by['track-harmony'].effects[0].parameters['soundcraft.hpf_freq'],150)
        self.assertEqual(native_pan(by['track-bass']),[0,0]);self.assertEqual(native_pan(by['track-kick']),[0,0])
    def test_true_summed_drums_and_distinct_100percent_wet_returns(self):
        by={t.id:t for t in self.p.tracks};buses=[t for t in self.p.tracks if t.kind=='bus']
        self.assertEqual(len(buses),4)
        for tid in DRUMS:
            self.assertFalse(by[tid].output_master);self.assertEqual(by[tid].sends[0].target_track_id,'phase14-drum-sum')
        for t in buses[1:]:self.assertEqual(t.effects[0].parameters['effect.wet'],1)
    def test_real_filter_gestures_and_throw_trim_bounds(self):
        for a in self.p.automation:
            if a.parameter_id=='soundcraft.lpf_freq':self.assertTrue(all(1000<=x.value<=20000 for x in a.points))
        self.assertEqual(len([a for a in self.p.automation if a.parameter_id.startswith('route.')]),2)
        for t in self.p.tracks:
            for s in t.sends:
                if trim_id(s) in t.controls:
                    self.assertEqual(s.gain_db,-12);self.assertEqual(t.controls[trim_id(s)],-60)
    def test_isolated_stem_keeps_only_reachable_buses_and_lanes(self):
        p=isolate(self.p,['track-lead']);self.assertEqual({t.id for t in p.tracks},{'track-lead','phase14-short-room','phase14-dark-space','phase14-echo'})
        self.assertEqual(p.tracks[0].clips,next(t for t in self.p.tracks if t.id=='track-lead').clips);graph_contract(p)
        with self.assertRaises(ValidationError):isolate(self.p,['missing'])
    def test_reject_wrong_song_or_duplicate_production(self):
        for attr,value in [('bars',63),('tempo_bpm',125),('key_mode','major')]:
            p=deepcopy(self.source);setattr(p,attr,value)
            with self.assertRaises(ValidationError):proposal(p)
        with self.assertRaises(ValidationError):proposal(self.p)
        p=deepcopy(self.source);p.locks=[Lock('protected-drum',p.tracks[0].id,None)]
        with self.assertRaises(ValidationError):proposal(p)
    def test_unique_track_names_and_empty_bus_only(self):
        p=deepcopy(self.p);p.tracks[-1].name=p.tracks[0].name
        with self.assertRaises(ValidationError):graph_contract(p)
        p=deepcopy(self.p);p.tracks[-1].clips=deepcopy(p.tracks[0].clips)
        with self.assertRaises(ValidationError):graph_contract(p)
    def test_reject_cycles_disconnected_unmapped_and_pre_fader(self):
        for mode in ('cycle','chain','disconnected','unmapped','pre'):
            p=deepcopy(self.p)
            if mode=='cycle':p.tracks[-1].sends=[Send('cycle',p.tracks[-1].id,0,0,'post_fader')]
            if mode=='chain':p.tracks[-2].sends=[Send('chain',p.tracks[-1].id,0,0,'post_fader')]
            if mode=='disconnected':p.tracks[0].sends=[];p.tracks[0].output_master=False
            if mode=='unmapped':p.tracks[0].controls['invented']=0
            if mode=='pre':p.tracks[0].sends[0].mode='pre_fader'
            with self.assertRaises(ValidationError):graph_contract(p)
    def test_send_pan_units_and_trim_registry_fail_closed(self):
        p=deepcopy(self.p);p.tracks[0].sends[0].pan=.2
        with self.assertRaises(ValidationError):graph_contract(p)
        p=deepcopy(self.p);spec=next(s for s in p.parameters if s.id.startswith('route.'));spec.unit='ratio'
        with self.assertRaises(ValidationError):graph_contract(p)
    def test_trim_addition_and_automation_native_bounds(self):
        p=deepcopy(self.p);t=p.tracks[0];s=t.sends[0];s.gain_db=12;key=add_send_trim(p,t,s,0)
        t.controls[key]=1
        with self.assertRaises(ValidationError):graph_contract(p)
    def test_stereo_channel_positions_and_pan_lane_bounds(self):
        p=deepcopy(self.p);t=next(t for t in p.tracks if t.id=='track-harmony')
        self.assertEqual(native_pan(t),[-.75,.75]);t.controls['mixer.pan']=.5
        with self.assertRaises(ValidationError):graph_contract(p)
        p=deepcopy(self.p);t=next(t for t in p.tracks if t.id=='track-lead')
        p.automation.append(AutomationLane('bad-spread',t.id,'mixer.stereo_spread',[AutomationPoint('spread-point',0,.2,'linear')]))
        with self.assertRaises(ValidationError):graph_contract(p)
    def test_legacy_shadow_removes_routes_but_preserves_all_note_fields(self):
        q=ProductionAdapter._plain(self.p)
        self.assertEqual(len(q.tracks),len(self.source.tracks));self.assertTrue(all(t.output_master and not t.sends for t in q.tracks))
        self.assertEqual([[c for c in t.clips] for t in q.tracks],[[c for c in t.clips] for t in self.p.tracks if t.kind=='midi'])


class ProductionPatchTests(unittest.TestCase):
    def test_curated_designs_original_deterministic_distinct(self):
        ps={k:production_patch(k) for k in ('bass','stab','lead','pad')}
        self.assertEqual(ps,{k:production_patch(k) for k in ps})
        self.assertEqual(len({str(p['settings']) for p in ps.values()}),4)
        self.assertTrue(all(p['author']=='Kuang' for p in ps.values()))
    def test_bass_mono_same_octave_no_random_phase_and_short_release(self):
        s=production_patch('bass')['settings']
        for k in ('osc_1_stereo_spread','osc_2_stereo_spread','osc_1_random_phase','osc_2_random_phase','osc_2_transpose'):self.assertEqual(s[k],0)
        self.assertEqual(s['polyphony'],1);self.assertAlmostEqual(s['env_1_release']**4,.025)
    def test_pad_amp_envelope_and_actual_internal_modulation(self):
        s=production_patch('pad')['settings'];self.assertAlmostEqual(s['env_1_attack']**4,.26);self.assertAlmostEqual(s['env_1_release']**4,1.25)
        self.assertEqual([x['source'] for x in s['modulations']],['lfo_1','lfo_1'])
        self.assertEqual(production_patch('pad',modulation=False)['settings']['modulations'],[])
    def test_internal_fx_off_all_roles_and_foreign_role_rejected(self):
        for role in ('bass','stab','lead','pad'):
            s=production_patch(role)['settings']
            for k in ('reverb_on','delay_on','chorus_on'):self.assertEqual(s[k],0)
        with self.assertRaises(ValidationError):production_patch('factory-supersaw')
