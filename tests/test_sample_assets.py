"""Offline asset/mapping/review contracts. These do not claim host success."""
import json
import math
import struct
import tempfile
import unittest
import wave
from copy import deepcopy
from pathlib import Path

from kuang.atmosphere import atmosphere_house
from kuang.depth import note_fingerprints
from kuang.midi import export_bytes
from kuang.producer import package_preferred,read_audition,record_review,review_history
from kuang.sample_assets import LICENSES,create_asset,digest,inventory,read_asset,verify_native_audio,write
from kuang.sampled_instrument import CONTROLS,SampledInstrumentAdapter,bind_samples
from kuang.schema import Lock,Note,ParameterSpec,ValidationError,dumps,save,state_hash,validate
from kuang.transactions import Engine,LockedError,Scope,SetParameter,replay
from soundcraft_fake import CONTRACT

ROOT=Path(__file__).resolve().parents[1]
SCRATCH=ROOT/'.local/producer/tests'


def wav(path,*,width=3,channels=1,rate=48000,frames=2400,silent=False):
    data=bytearray();limit=2**(8*width-1)-1
    for i in range(frames):
        for c in range(channels):
            x=0 if silent else round(.2*math.sin(2*math.pi*(220+c*110)*i/rate)*limit)
            data+=x.to_bytes(width,'little',signed=True)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(channels);w.setsampwidth(width);w.setframerate(rate);w.writeframes(data)
    return path


def credit():return {'creator':'Kuang test authors','source':'Original deterministic test signal, not a music-quality claim',
    'license':'MIT','license_url':LICENSES['MIT'],'notice':(ROOT/'LICENSE').read_text(),'redistribution_permitted':True}


def mapping(**overrides):
    return dict(root_note=36,key_low=36,key_high=36,velocity_low=1,velocity_high=127,key_tracking=False,playback='one_shot',**{})|overrides


def asset(root,name='asset',**map_overrides):
    source=wav(root/(name+'.wav'));out=root/name
    create_asset(source,out,credit(),mapping(**map_overrides))
    return out


def adapter():
    a=SampledInstrumentAdapter('/bin/true',workspace=ROOT)
    a.base._discovery=deepcopy(CONTRACT)
    for f in ('soundcraft-production-plugins.json','soundcraft-depth-plugins.json','soundcraft-pulse-eq1.json','soundcraft-sampler.json'):
        a.base._discovery['plugins'].update(json.loads((ROOT/'tests/fixtures'/f).read_text()))
    return a


class AssetTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=SCRATCH);self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()

    def test_original_pcm_content_addressed_copy_and_independent_formats(self):
        for width,channels in ((2,1),(3,2)):
            source=wav(self.root/f'{width}-{channels}.wav',width=width,channels=channels)
            dest=self.root/f'a-{width}';create_asset(source,dest,credit(),mapping())
            m=read_asset(dest);self.assertEqual(m['sha256'],digest(source));self.assertEqual(m['audio']['channels'],channels)
            self.assertEqual(m['audio']['bits_per_sample'],width*8)
            self.assertEqual((dest/m['file']).read_bytes(),source.read_bytes())

    def test_license_provenance_unknown_rights_and_missing_mit_notice_rejected(self):
        source=wav(self.root/'sample.wav')
        for field,value in [('license','Royalty-free'),('license',[]),('license_url','https://invalid'),('notice','MIT'),('creator',''),('redistribution_permitted',False)]:
            p=credit();p[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValidationError):create_asset(source,self.root/'out',p,mapping())
            self.assertFalse((self.root/'out').exists())
        p=credit();p['execute']='anything'
        with self.assertRaises(ValidationError):create_asset(source,self.root/'out',p,mapping())

    def test_midi_mapping_semantics_not_relabelled_units(self):
        source=wav(self.root/'sample.wav')
        for changes in ({'root_note':1.5},{'key_low':70,'key_high':36},{'velocity_low':0},
                        {'key_tracking':1},{'playback':'SFZ'},{'transpose':12}):
            with self.subTest(changes=changes),self.assertRaises(ValidationError):create_asset(source,self.root/'out',credit(),mapping(**changes))

    def test_pcm_format_silence_clips_and_truncation_fail_closed(self):
        for name,kw in [('silent',{'silent':True}),('rate',{'rate':44100}),('width',{'width':1})]:
            path=wav(self.root/(name+'.wav'),**kw)
            with self.assertRaises(ValidationError):create_asset(path,self.root/'out',credit(),mapping())
        path=wav(self.root/'truncated.wav');path.write_bytes(path.read_bytes()[:-13])
        with self.assertRaises(ValidationError):create_asset(path,self.root/'out',credit(),mapping())
        path=self.root/'clipped.wav'
        with wave.open(str(path),'wb') as w:
            w.setparams((1,3,48000,0,'NONE','not compressed'));w.writeframes((2**23-1).to_bytes(3,'little',signed=True)*100)
        with self.assertRaises(ValidationError):create_asset(path,self.root/'out',credit(),mapping())

    def test_asset_drift_extra_files_directories_symlinks_and_path_escape(self):
        out=asset(self.root);m=read_asset(out)
        (out/'extra').write_text('x')
        with self.assertRaises(ValidationError):read_asset(out)
        (out/'extra').unlink();(out/'extra').mkdir()
        with self.assertRaises(ValidationError):read_asset(out)
        (out/'extra').rmdir();original=(out/m['file']).read_bytes();(out/m['file']).write_bytes(original[:-1]+b'x')
        with self.assertRaises(ValidationError):read_asset(out)
        (out/m['file']).write_bytes(original);(out/'alias').symlink_to(out/m['file'])
        with self.assertRaises(ValidationError):read_asset(out)
        (out/'alias').unlink();m['file']='../sample.wav';write(out/'asset.json',m)
        with self.assertRaises(ValidationError):read_asset(out)

    def test_native_float32_reencoding_pcm_identity_not_wav_header_identity(self):
        out=asset(self.root);m=read_asset(out)
        with wave.open(str(out/m['file']),'rb') as w:data=w.readframes(w.getnframes())
        payload=b''.join(struct.pack('<f',int.from_bytes(data[i:i+3],'little',signed=True)/2**23) for i in range(0,len(data),3))
        fmt=struct.pack('<HHIIHH',3,1,48000,192000,4,32)
        body=b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(payload))+payload
        path=self.root/'native.wav';path.write_bytes(b'RIFF'+struct.pack('<I',len(body))+body)
        verify_native_audio(path,m['audio']);self.assertNotEqual(digest(path),m['sha256'])
        b=bytearray(path.read_bytes());b[-4:]=struct.pack('<f',.5);path.write_bytes(b)
        with self.assertRaisesRegex(ValidationError,'PCM differs'):verify_native_audio(path,m['audio'])

    def test_exclusive_asset_publication_preserves_existing_destination_and_source(self):
        out=asset(self.root);before=inventory(out);source=(self.root/'asset.wav').read_bytes()
        with self.assertRaises(ValidationError):create_asset(self.root/'asset.wav',out,credit(),mapping())
        self.assertEqual(inventory(out),before);self.assertEqual((self.root/'asset.wav').read_bytes(),source)
        (self.root/'linked.wav').symlink_to(self.root/'asset.wav')
        with self.assertRaises(ValidationError):create_asset(self.root/'linked.wav',self.root/'other',credit(),mapping())


class BindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=atmosphere_house()
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=SCRATCH);self.root=Path(self.temp.name);self.asset=asset(self.root)
    def tearDown(self):self.temp.cleanup()

    def test_full_song_identity_all_note_fields_midi_fx_lanes_and_spec_preserved(self):
        before=dumps(self.source);p=bind_samples(self.source,{'track-kick':self.asset})
        self.assertEqual((p.bars,p.tempo_bpm,p.key_tonic,p.key_mode),(64,126,0,'minor'))
        self.assertEqual(note_fingerprints(p),note_fingerprints(self.source));self.assertEqual(export_bytes(p),export_bytes(self.source))
        self.assertEqual((p.sections,p.automation,p.locks),(self.source.sections,self.source.automation,self.source.locks))
        for old,new in zip(self.source.tracks,p.tracks):
            self.assertEqual((old.clips,old.effects,old.controls,old.sends),(new.clips,new.effects,new.controls,new.sends))
            if old.id!='track-kick':self.assertEqual(old,new)
        self.assertEqual(p.metadata['song_spec'],self.source.metadata['song_spec']);self.assertEqual(dumps(self.source),before)

    def test_deterministic_asset_reference_and_canonical_bytes(self):
        a=bind_samples(self.source,{'track-kick':self.asset});b=bind_samples(self.source,{'track-kick':self.asset})
        self.assertEqual(dumps(a),dumps(b));self.assertEqual(a.tracks[0].instrument.preset_ref,'sha256:'+digest(self.asset/'asset.json'))
        self.assertEqual(set(a.tracks[0].instrument.parameters),set(CONTROLS))
        with self.assertRaises(ValidationError):bind_samples(a,{'track-kick':self.asset})

    def test_unknown_bindings_mapping_notes_and_locks_rejected(self):
        for assignments in ({},{'unknown':self.asset},{'track-lead':self.asset}):
            with self.assertRaises(ValidationError):bind_samples(self.source,assignments)
        p=deepcopy(self.source);p.locks.append(Lock('sample-lock','instrument-kick',None))
        with self.assertRaises(ValidationError):bind_samples(p,{'track-kick':self.asset})
        p=deepcopy(self.source);p.metadata['sample_backend']='unrelated user annotation'
        with self.assertRaises(ValidationError):bind_samples(p,{'track-kick':self.asset})
        m=read_asset(self.asset);m['mapping']['velocity_high']=50;write(self.asset/'asset.json',m)
        with self.assertRaises(ValidationError):bind_samples(self.source,{'track-kick':self.asset})

    def test_control_registry_native_values_and_unknown_units_fail_closed(self):
        p=bind_samples(self.source,{'track-kick':self.asset});a=adapter();t=p.tracks[0]
        values=a._values(p,t,self.asset);self.assertEqual(values['root_note'],36);self.assertEqual(values['key_track'],0)
        self.assertEqual(values['play_mode'],1);self.assertEqual(values['loop_mode'],0);self.assertEqual(values['sustain'],100)
        next(x for x in p.parameters if x.id=='sample.attack_ms').unit='Hz'
        with self.assertRaises(ValidationError):a._values(p,t,self.asset)
        p=deepcopy(self.source);p.parameters.append(ParameterSpec('sample.attack_ms','Hz',.1,5000,1,['instrument']))
        with self.assertRaises(ValidationError):bind_samples(p,{'track-kick':self.asset})

    def test_conservative_voice_budget_prevents_silent_voice_stealing(self):
        p=bind_samples(self.source,{'track-kick':self.asset});t=p.tracks[0];t.clips=t.clips[:1]
        t.clips[0].notes=[Note('dense-'+str(i),i,1,36,100,9) for i in range(100)]
        validate(p)
        with self.assertRaisesRegex(ValidationError,'32-voice'):adapter()._values(p,t,self.asset)

    def test_exact_typed_parameter_undo_redo_and_locks(self):
        p=bind_samples(self.source,{'track-kick':self.asset});op=SetParameter('set_parameter','instrument-kick','sample.attack_ms',5)
        e=Engine(p);r=e.apply([op],Scope(['track-kick'],[],['sample.attack_ms'],None,None),state_hash(p))
        self.assertEqual(note_fingerprints(e.project),note_fingerprints(p));self.assertEqual(dumps(replay(e.project,r,undo=True)),dumps(p))
        self.assertEqual(dumps(replay(p,r,undo=False)),dumps(e.project))
        p.locks.append(Lock('locked-attack','instrument-kick','sample.attack_ms'))
        with self.assertRaises(LockedError):Engine(p).apply([op],Scope(['track-kick'],[],['sample.attack_ms'],None,None),state_hash(p))

    def test_output_guards_no_source_subdirectory_creation_or_unavailable_fallback(self):
        a=adapter();a.capabilities=lambda:{}
        before=inventory(self.asset)
        with self.assertRaises(ValidationError):a.export(self.source,{'track-kick':self.asset},self.asset/'new'/'bundle')
        self.assertFalse((self.asset/'new').exists());self.assertEqual(inventory(self.asset),before)
        with self.assertRaises(ValidationError):a.local(ROOT.parent/'outside-sample')
        with self.assertRaises(ValidationError):SampledInstrumentAdapter('/bin/true',workspace=ROOT).capabilities()


def contract_audition(root,p):
    """Offline state-machine fixture; native success is tested separately."""
    root.mkdir();(root/'A').mkdir();(root/'B').mkdir();(root/'listening').mkdir()
    save(p,root/'A/project.kuang.json');save(p,root/'B/project.kuang.json')
    paths={}
    for k in ('A','B'):
        for role in ('full','instrument'):
            path=root/'listening'/(k+'-'+role+'-LUFS-matched.wav');wav(path);paths[str(path.relative_to(root))]=digest(path)
    m={'version':'producer-audition-1','hypothesis':'Offline contract fixture, no real host claim',
       'baseline_hash':state_hash(p),'candidate_hash':state_hash(p),'bars':p.bars,'note_fields_exact':True,
       'midi_bytes_exact':True,'song_spec_exact':True,'automation_exact':True,'full_native_reopen_PCM_exact':True,
       'technical_eligible':True,'preference':'unreviewed','quality_improvement_established':False,
       'levels':{},'matching':{},'full_context_difference':{},'independent_context_sum':{},
       'listening_files':paths,'assets':{},'files':inventory(root)}
    write(root/'audition.json',m);return m


class ProducerReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p=atmosphere_house()
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=SCRATCH);self.root=Path(self.temp.name)
        self.bundle=self.root/'audition';self.m=contract_audition(self.bundle,self.p)
    def tearDown(self):self.temp.cleanup()
    def review(self,decision='preferred',**changes):
        data=dict(audition_sha256=digest(self.bundle/'audition.json'),reviewer='Test reviewer declaration',
            decision=decision,reason='Contract test of explicit feedback, not an actual musical preference',listened_files=self.m['listening_files'])|changes
        return record_review(self.bundle,**data)

    def test_default_unreviewed_never_promotes_from_technical_metrics(self):
        self.assertEqual(read_audition(self.bundle)['preference'],'unreviewed')
        with self.assertRaisesRegex(ValidationError,'no explicit preferred'):package_preferred(self.bundle,self.root/'listen.zip')
        self.assertFalse((self.root/'listen.zip').exists())

    def test_review_requires_actual_file_identities_reason_reviewer_and_parent(self):
        for changes in ({'audition_sha256':'0'*64},{'reviewer':''},{'reason':''},{'decision':'auto_score'},
                        {'listened_files':{}},{'listened_files':{k:'0'*64 for k in self.m['listening_files']}}):
            with self.subTest(changes=changes),self.assertRaises(ValidationError):self.review(**changes)
        self.assertEqual(review_history(self.bundle),[])

    def test_append_only_review_chain_rejection_retains_incumbent_and_no_zip(self):
        before=(self.bundle/'A/project.kuang.json').read_bytes();self.review();self.review('rejected')
        self.assertEqual(len(review_history(self.bundle)),2)
        self.assertEqual((self.bundle/'A/project.kuang.json').read_bytes(),before)
        with self.assertRaises(ValidationError):package_preferred(self.bundle,self.root/'listen.zip')
        r=json.loads((self.bundle/'reviews/0000.json').read_text());r['reason']='tamper';write(self.bundle/'reviews/0000.json',r)
        with self.assertRaises(ValidationError):review_history(self.bundle)

    def test_review_and_package_locks_no_clobber_and_explicit_preference(self):
        (self.bundle/'.review-lock').write_text('another writer')
        with self.assertRaises(ValidationError):self.review()
        with self.assertRaises(ValidationError):package_preferred(self.bundle,self.root/'listen.zip')
        (self.bundle/'.review-lock').unlink();self.review();out=self.root/'listen.zip'
        r=package_preferred(self.bundle,out);self.assertTrue(r['human_declared_preference'])
        before=out.read_bytes()
        with self.assertRaises(ValidationError):package_preferred(self.bundle,out)
        self.assertEqual(out.read_bytes(),before)
        with self.assertRaises(ValidationError):package_preferred(self.bundle,self.bundle/'nested.zip')

    def test_audition_data_drift_missing_context_and_review_receipt_changes_rejected(self):
        self.review();p=self.bundle/'listening/B-full-LUFS-matched.wav';p.write_bytes(p.read_bytes()[:-6])
        with self.assertRaises(ValidationError):read_audition(self.bundle)
        with self.assertRaises(ValidationError):package_preferred(self.bundle,self.root/'listen.zip')
