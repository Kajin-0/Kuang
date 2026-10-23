"""Offline contracts use captured controller facts, never fake a native proof."""
import base64
import json
import math
import struct
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from kuang.atmosphere import atmosphere_house
from kuang.depth import note_fingerprints
from kuang.external_synth import (ExternalSynthAdapter,LAYOUT_SHA,bound_project,digest,
                                  inventory,read_patch,write)
from kuang.midi import export
from kuang.schema import Lock,ValidationError,dumps,state_hash,validate
from kuang.transactions import Engine,Scope,SetParameter,receipt_from_dict,replay
from kuang.vitalium_patch import CLASS_ID,PLUGIN_ID,chunks,component,component_patch,original_patch,vstpreset

ROOT=Path(__file__).resolve().parents[1]
SCRATCH=ROOT/'.local/phase11/tests'
FACTS=json.loads((ROOT/'tests/fixtures/vitalium-controls.json').read_text())


def contract_patch(path,role='pad'):
    """Synthetic contract fixture; actual compatibility is opt-in only."""
    path.mkdir();p=original_patch(role);state=component(p)
    (path/'patch.vital').write_text(json.dumps(p))
    (path/'component.bin').write_bytes(state);(path/'patch.vstpreset').write_bytes(vstpreset(state))
    rows=deepcopy(FACTS['bindings'])
    for row in rows:row['normalized']=row['default_normalized']
    write(path/'bindings.json',rows)
    write(path/'manifest.json',{'version':'external-patch-1','plugin':PLUGIN_ID,'plugin_version':'1.0.6',
        'role':role,'license':'original test fixture, not a real-host success claim','host':'Pedalboard 0.9.26',
        'original_content_only':True,'factory_content':False,'native_defaults':FACTS['native_defaults'],
        'all_normalized_parameters_restored':True,'component_roundtrip_exact':True,'sha256':inventory(path)})
    return path


class OriginalPatchTests(unittest.TestCase):
    def test_original_formula_waves_no_factory_content_and_strict_options(self):
        for role in ('pad','bass','pluck'):
            a=original_patch(role);self.assertEqual(a,original_patch(role));s=a['settings']
            self.assertEqual(base64.b64decode(s['sample']['samples']),bytes(64));self.assertEqual(s['sample_on'],0)
            for w in s['wavetables']:
                self.assertEqual(w['author'],'Kuang');frames=w['groups'][0]['components'][0]['keyframes']
                self.assertEqual([f['position'] for f in frames],[0,128,256])
                for f in frames:
                    data=struct.unpack('<2048f',base64.b64decode(f['wave_data']));self.assertLess(abs(sum(data)),.001)
                    self.assertTrue(all(math.isfinite(v) and abs(v)<1.1 for v in data))
        for kwargs in ({'role':'official Vital'},{'role':'pad','modulation':1},{'role':'bass','volume_db':float('nan')},{'role':'pad','volume_db':1}):
            with self.assertRaises(ValidationError):original_patch(**kwargs)

    def test_actual_internal_lfo_adsr_and_mono_bass_choices(self):
        pad=original_patch('pad')['settings'];bass=original_patch('bass')['settings'];pluck=original_patch('pluck')['settings']
        self.assertEqual(pad['osc_1_unison_voices'],7);self.assertEqual(pad['modulations'][0],{'source':'lfo_1','destination':'osc_1_wave_frame'})
        self.assertAlmostEqual(pad['env_1_attack']**4,.65);self.assertAlmostEqual(pad['env_1_release']**4,2.6)
        self.assertEqual(bass['osc_1_unison_voices'],1);self.assertEqual(bass['osc_2_unison_voices'],1)
        self.assertEqual((bass['osc_1_stereo_spread'],bass['osc_2_stereo_spread']),(0,0))
        self.assertEqual(bass['osc_2_transpose'],12);self.assertEqual(bass['osc_2_wave_frame'],0)
        self.assertEqual(pluck['modulations'][0]['source'],'env_2');self.assertGreater(pluck['delay_dry_wet'],0)
        dry=original_patch('pad',modulation=False)
        self.assertEqual(dry['settings']['modulations'],[])
        dry['settings']['modulations']=pad['modulations'];self.assertEqual(dry,original_patch('pad'))

    def test_standard_preset_chunks_lengths_and_malformed_states(self):
        state=component(original_patch('pad'));data=vstpreset(state);self.assertEqual(chunks(data)[b'Comp'],state)
        self.assertEqual(data[8:40],CLASS_ID.encode());self.assertEqual(state[:4],b'VstW')
        self.assertEqual(struct.unpack_from('>I',state,20)[0],len(state)-24)
        self.assertEqual(struct.unpack_from('>I',state,172)[0],len(state)-176)
        self.assertEqual(component_patch(state),original_patch('pad'))
        for invalid in (b'',state[:-1],state[:176]+b'NaN'+state[-32:]):
            with self.assertRaises(ValidationError):component_patch(invalid)
        for invalid in (b'',data[:-1],b'XXXX'+data[4:],data+b'x',data[:8]+bytes(32)+data[40:]):
            with self.assertRaises(ValidationError):chunks(invalid)
        bad=bytearray(data);struct.pack_into('<q',bad,40,2**60)
        with self.assertRaises(ValidationError):chunks(bytes(bad))

    def test_worker_import_is_optional_and_unknown_job_is_rejected(self):
        from kuang.vst3_worker import prepare
        with self.assertRaises(ValidationError):prepare({'execute':'anything'})
        with patch.dict(sys.modules,{'pedalboard':None}):
            with self.assertRaises(ImportError):prepare(dict(plugin='x',defaults={},role='pad',modulation=True,volume_db=None,out='x'))


class ExternalContractTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=SCRATCH)
        self.root=Path(self.temp.name);self.asset=contract_patch(self.root/'asset');self.source=atmosphere_house()
    def tearDown(self):self.temp.cleanup()

    def test_captured_layout_and_complete_metadata_asset_integrity(self):
        from kuang.soundcraft import _hash
        self.assertEqual(_hash(FACTS['bindings']),LAYOUT_SHA)
        m,rows=read_patch(self.asset);self.assertEqual(len(rows),771);self.assertEqual(len(m['native_defaults']),2851)
        self.assertEqual(m['factory_content'],False)

    def test_bound_source_full_notes_form_fx_lanes_and_midi_bytes_exact(self):
        before=dumps(self.source);p=bound_project(self.source,{'track-depth-pad':self.asset,'track-arp':self.asset})
        validate(p);self.assertEqual(dumps(self.source),before)
        self.assertEqual(note_fingerprints(p),note_fingerprints(self.source))
        self.assertEqual((p.bars,p.tempo_bpm,p.key_tonic,p.key_mode,p.sections,p.automation),
                         (64,126,0,'minor',self.source.sections,self.source.automation))
        for old,new in zip(self.source.tracks,p.tracks):
            self.assertEqual((old.clips,old.effects,old.controls,old.id),(new.clips,new.effects,new.controls,new.id))
        self.assertEqual(p.metadata['song_spec'],self.source.metadata['song_spec'])
        export(self.source,self.root/'a.mid');export(p,self.root/'b.mid');self.assertEqual((self.root/'a.mid').read_bytes(),(self.root/'b.mid').read_bytes())

    def test_deterministic_canonical_parameter_registry_and_preset_fingerprints(self):
        a=bound_project(self.source,{'track-bass':self.asset});b=bound_project(self.source,{'track-bass':self.asset})
        self.assertEqual(dumps(a),dumps(b));self.assertEqual(state_hash(a),state_hash(b))
        t=next(t for t in a.tracks if t.id=='track-bass');self.assertEqual(t.instrument.preset_ref,'sha256:'+digest(self.asset/'manifest.json'))
        self.assertEqual(len(t.instrument.parameters),771)
        self.assertTrue(all(x.unit=='normalized' and (x.minimum,x.maximum)==(0,1) for x in a.parameters if x.id.startswith('vitalium.')))

    def test_unknown_targets_locks_and_synth_automation_fail_closed(self):
        for assignments in ({},{'missing':self.asset}):
            with self.assertRaises(ValidationError):bound_project(self.source,assignments)
        p=deepcopy(self.source);t=next(t for t in p.tracks if t.id=='track-bass')
        p.locks=[Lock('lock-vital',t.instrument.id,None)]
        with self.assertRaises(ValidationError):bound_project(p,{t.id:self.asset})
        self.assertEqual(self.source.locks,[])

    def test_exact_typed_edit_undo_redo_and_locks_keep_snapshot(self):
        p=bound_project(self.source,{'track-bass':self.asset});t=next(t for t in p.tracks if t.id=='track-bass')
        param=next(k for k in t.instrument.parameters if k.endswith('48'));op=SetParameter('set_parameter',t.instrument.id,param,.2)
        e=Engine(p);r=e.apply([op],Scope([t.id],[],[param],None,None),state_hash(p))
        q=e.project;self.assertEqual(dumps(replay(q,receipt_from_dict(__import__('dataclasses').asdict(r)),undo=True)),dumps(p))
        self.assertEqual(dumps(replay(p,r,undo=False)),dumps(q))
        p.locks=[Lock('lock-param',t.instrument.id,param)]
        with self.assertRaises(ValidationError):Engine(p).apply([op],Scope([t.id],[],[param],None,None),state_hash(p))

    def test_tampered_assets_unknown_fields_extra_files_and_symlinks_rejected(self):
        (self.asset/'extra').write_text('x')
        with self.assertRaises(ValidationError):read_patch(self.asset)
        (self.asset/'extra').unlink();m=json.loads((self.asset/'manifest.json').read_text());m['execute']='no';write(self.asset/'manifest.json',m)
        with self.assertRaises(ValidationError):read_patch(self.asset)
        del m['execute'];write(self.asset/'manifest.json',m);(self.asset/'component.bin').write_bytes(b'changed')
        with self.assertRaises(ValidationError):read_patch(self.asset)

    def test_binding_name_or_scale_mutation_rejected_even_with_new_hashes(self):
        rows=json.loads((self.asset/'bindings.json').read_text());rows[0]['name']='Invented control';write(self.asset/'bindings.json',rows)
        m=json.loads((self.asset/'manifest.json').read_text());m['sha256']['bindings.json']=digest(self.asset/'bindings.json');write(self.asset/'manifest.json',m)
        with self.assertRaisesRegex(ValidationError,'fingerprint'):read_patch(self.asset)

    def test_unavailable_official_or_changed_binary_no_fallback_or_output(self):
        with self.assertRaisesRegex(ValidationError,'official Vital is not verified'):
            ExternalSynthAdapter(self.root/'Vital.vst3',workspace=ROOT)
        self.assertFalse((self.root/'output').exists())
        p=self.root/'Vital.vst3/Contents/x86_64-linux/vitalium.so';p.parent.mkdir(parents=True);p.write_bytes(b'not reviewed')
        with self.assertRaises(ValidationError):ExternalSynthAdapter(p.parents[2],workspace=ROOT)

    def test_paths_no_clobber_discrete_values_and_units(self):
        a=ExternalSynthAdapter.__new__(ExternalSynthAdapter);a.workspace=ROOT;a.plugin=self.root/'plugin.vst3'
        with self.assertRaises(ValidationError):a.local('/outside-kuang')
        with self.assertRaises(ValidationError):a._new(self.asset)
        with self.assertRaises(ValidationError):a._new(a.plugin/'new')
        p=bound_project(self.source,{'track-bass':self.asset});t=next(t for t in p.tracks if t.id=='track-bass')
        _,rows=read_patch(self.asset);row=next(r for r in rows if r['steps'])
        t.instrument.parameters[row['canonical_id']]=.12345
        with self.assertRaisesRegex(ValidationError,'fractional'):a._values(p,t,self.asset)
        t.instrument.parameters[row['canonical_id']]=row['normalized']
        next(x for x in p.parameters if x.id==row['canonical_id']).unit='Hz'
        with self.assertRaisesRegex(ValidationError,'normalized registry'):a._values(p,t,self.asset)

    def test_cli_help_has_explicit_optional_paths_and_normalized_edit(self):
        r=subprocess.run([sys.executable,'-m','kuang.external_synth','--help'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0);self.assertIn('--host-python',r.stdout);self.assertIn('--normalized-value',r.stdout)
        self.assertIn('capabilities',r.stdout)

    def test_large_native_lane_batches_use_ordered_script_without_shell(self):
        a=ExternalSynthAdapter.__new__(ExternalSynthAdapter);a.workspace=ROOT;a.plugin=self.root/'plugins/plugin.vst3'
        a.scratch=self.root/'scratch';a.scratch.mkdir();a.bwrap='/usr/bin/bwrap'
        argv=['/pinned/soundcraft','run','--in',str(self.root/'input.scraft')]
        for i in range(4500):argv+=['--cmd','automation.set_point='+json.dumps({'tick':i,'value':i/4500})]
        argv+=['--save',str(self.root/'output.scraft')]
        def subprocess_mock(command,**kwargs):
            self.assertNotIn('shell',kwargs);self.assertEqual(command.count('--cmd'),0)
            index=command.index('script');path=Path(command[index+1]);lines=path.read_text().splitlines()
            self.assertEqual(len(lines),4500)
            self.assertEqual([json.loads(x.partition(' ')[2])['tick'] for x in lines],list(range(4500)))
            return subprocess.CompletedProcess(command,0,'verified\n','')
        with patch('kuang.external_synth.subprocess.run',side_effect=subprocess_mock):
            self.assertEqual(a.call(argv,self.root),'verified\n')
        self.assertFalse(list(a.scratch.glob('commands-*.txt')))
