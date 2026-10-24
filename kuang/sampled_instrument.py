"""Opt-in live native sample instruments; legacy SoundCraft stays strict.

Canonical 0.1 preset references pin licensed sample manifests. The host loads
them through mix.sampler_load. Read-only validation projections reuse the old
note/FX/lane verifier; no generated native JSON is ever sent to the host.
"""
import argparse
import json
import math
import os
import shutil
import tempfile
import wave
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from .audio import analyze_wav
from .production_audio import _decode
from .midi import export as midi_export
from .sample_assets import create_asset, digest, inventory, read_asset, verify_native_audio, write
from .schema import Instrument, ParameterSpec, ValidationError, dumps, load, save, state_hash, strict_json, validate
from .soundcraft import SoundCraftAdapter, _close, _hash, _read_json
from .transactions import Engine, SetParameter

HOST_SHA='84466d199a6cb4d4924a9179fdf36b0c6d1ab3a0082b60ceed50d06f09f0b130'
CONTRACT='5af7ed8eed0e51a251da6dee6f57a9b83ac6ae004c70b13a96416cdee4ad49f7'
# Canonical identifier: native id, canonical unit, bounds, default, native scale.
CONTROLS={
    'sample.attack_ms': ('attack','ms',.1,5000,1,1),
    'sample.decay_ms': ('decay','ms',1,10000,300,1),
    'sample.sustain': ('sustain','normalized',0,1,1,100),
    'sample.release_ms': ('release','ms',1,10000,150,1),
    'sample.velocity_sensitivity': ('velocity','normalized',0,1,.7,100),
    'sample.start': ('start','normalized',0,1,0,100),
    'sample.level_db': ('level','dB',-48,12,-6,1),
}


def bind_samples(source, assignments):
    validate(source)
    if not assignments:raise ValidationError('explicit track/asset bindings required')
    if any(k in source.metadata for k in ('sample_backend','sample_binding_parent_hash','sample_original_instruments','sample_binding_notes')):
        raise ValidationError('sample binding metadata collision; original annotations must remain intact')
    p=deepcopy(source);tracks={t.id:t for t in p.tracks}
    if not set(assignments)<=set(tracks):raise ValidationError('unknown sampled track')
    origins={}
    for tid,path in assignments.items():
        t=tracks[tid];m=read_asset(path)
        if t.kind!='midi' or t.instrument is None or t.instrument.plugin_ref=='soundcraft:sampler':
            raise ValidationError('bind an unsampled MIDI track; existing sampler controls require explicit edits')
        if any(x.target_id in (t.id,t.instrument.id) for x in p.locks):raise ValidationError('sample binding is locked')
        if any(x.target_id==t.instrument.id for x in p.automation):raise ValidationError('instrument automation is unsupported')
        origins[tid]=asdict(t.instrument)
        t.instrument=Instrument(t.instrument.id,'plugin','soundcraft:sampler','sha256:'+digest(Path(path)/'asset.json'),None,
                                 {k:v[4] for k,v in CONTROLS.items()})
        _check_notes(t,m)
    specs={s.id:s for s in p.parameters}
    for key,(_,unit,lo,hi,default,_) in CONTROLS.items():
        spec=ParameterSpec(key,unit,lo,hi,default,['instrument'])
        if key in specs and specs[key]!=spec:raise ValidationError('sample parameter registry collision')
        if key not in specs:p.parameters.append(spec)
    p.metadata.update(sample_backend='SoundCraft 0.11.0 / sample-asset-1',sample_binding_parent_hash=state_hash(source),
        sample_original_instruments=json.dumps(origins,sort_keys=True),
        sample_binding_notes='Live single-sample instruments. Original MIDI/SongSpec/FX/mixer/lanes retained. Root/key/velocity mapping is semantic MIDI metadata, not relabelled Hz. No SFZ zones, loops, pitch offsets or instrument automation mapping. License claims supplied by asset author.')
    validate(p)
    return p


def _check_notes(t,m):
    mapping=m['mapping']
    if any(not mapping['key_low']<=n.pitch<=mapping['key_high'] or
           not mapping['velocity_low']<=n.velocity<=mapping['velocity_high'] for c in t.clips for n in c.notes):
        raise ValidationError('sample mapping would silently discard existing notes: '+t.id)


def _voice_events(p,t,m):
    events=[];mp=m['mapping']
    for c in t.clips:
        for note in c.notes:
            ratio=2**((note.pitch-mp['root_note'])/12) if mp['key_tracking'] else 1
            if ratio>128:raise ValidationError('sample pitch would exceed native playback-step ceiling')
            duration=m['audio']['frames']/48000*(1-t.instrument.parameters['sample.start'])/ratio
            if mp['playback']=='gate':
                duration=min(duration,note.duration/p.ppq*60/p.tempo_bpm+t.instrument.parameters['sample.release_ms']/1000)
            at=(c.start+note.start)/p.ppq*60/p.tempo_bpm
            if duration>0:events.extend([(at,1),(at+duration,-1)])
    return events


class SampledInstrumentAdapter:
    def __init__(self, executable=None, *, workspace=None):
        self.workspace=Path(workspace or Path.cwd()).resolve()
        self.scratch=self.local(self.workspace/'.local/producer/tmp');self.scratch.mkdir(parents=True,exist_ok=True)
        self.base=SoundCraftAdapter(executable,timeout=240)
        self._caps=None

    def local(self,path):
        raw=Path(path).absolute()
        if raw.is_symlink() or not raw.resolve().is_relative_to(self.workspace):raise ValidationError('sample paths must stay within workspace without symlinks')
        return raw.resolve()

    def capabilities(self):
        if digest(self.base.executable)!=HOST_SHA:raise ValidationError('sampler requires the reviewed SoundCraft binary')
        if self._caps is None:
            d=self.base._discover()
            if _hash(d)!=CONTRACT:raise ValidationError('SoundCraft contract drift')
            descriptor=strict_json(self.base._call(['describe','mix.sampler_load'],self.scratch))
            if descriptor.get('id')!='mix.sampler_load' or descriptor.get('params')!='{track?, path, params?: {root_note, key_low, key_high, attack, loop_mode, …}}: an instrument track plays the file through the built-in Sampler (made its instrument if it is not already) → {track, source, name, frames, channels, sample_rate}':
                raise ValidationError('sampler command contract drift')
            self._caps={'version':'sample-native-1','soundcraft_sha256':HOST_SHA,'contract_hash':CONTRACT,
                'sampler_descriptor_sha256':_hash(d['plugins']['sampler']),'load_command':descriptor,
                'live_midi_sampler':True,'sample_per_track':1,'formats':'48k mono/stereo 16/24bit WAV',
                'controls':CONTROLS,'general_routing':False,'sfz':False,'instrument_automation':False,
                'license':'MIT integration; separately installed host; per-asset declared license'}
        # JSON conversion makes tuple representation identical after persistence.
        return json.loads(json.dumps(self._caps))

    def _new(self,path,source=None):
        p=self.local(path)
        if p.exists():raise ValidationError('new sampler bundle/output required')
        if source and p.is_relative_to(self.local(source)):raise ValidationError('output inside source bundle')
        return p

    @staticmethod
    def _shadow(p):
        q=deepcopy(p)
        for t in q.tracks:
            if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler':
                t.instrument=Instrument(t.instrument.id,'plugin','soundcraft:subtractive_synth',None,None,{})
        validate(q)
        return q

    def _values(self,p,t,asset):
        m=read_asset(asset);_check_notes(t,m)
        if t.instrument.preset_ref!='sha256:'+digest(Path(asset)/'asset.json') or t.instrument.midi_program is not None:
            raise ValidationError('canonical sample manifest identity mismatch')
        if set(t.instrument.parameters)!=set(CONTROLS):raise ValidationError('unmapped sample controls')
        if any(a.target_id==t.instrument.id for a in p.automation):raise ValidationError('sampler instrument automation unsupported')
        values={x['id']:x['default'] for x in self.base._discover()['plugins']['sampler']['params']}
        for key,(native,unit,lo,hi,default,scale) in CONTROLS.items():
            spec=next((s for s in p.parameters if s.id==key),None)
            if spec!=ParameterSpec(key,unit,lo,hi,default,['instrument']):raise ValidationError('sampler control units/registry drift')
            values[native]=t.instrument.parameters[key]*scale
        mp=m['mapping']
        events=_voice_events(p,t,m)
        voices=0
        for _,change in sorted(events):
            voices+=change
            if voices>32:raise ValidationError('sample mapping exceeds conservative native 32-voice budget')
        values.update(root_note=mp['root_note'],key_low=mp['key_low'],key_high=mp['key_high'],
            vel_low=mp['velocity_low'],vel_high=mp['velocity_high'],key_track=int(mp['key_tracking']),
            play_mode=int(mp['playback']=='one_shot'))
        return values

    def _verify(self,p,native,assets,root):
        validate(p);shadow=self._shadow(p);self.base._require(shadow)
        actual_ids={t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
        if actual_ids!=set(assets):raise ValidationError('missing/extra sampler asset assignment')
        if native.get('videos') or native.get('busses') or native.get('format_version')!=1 or native.get('sample_rate')!=48000 or native.get('bit_depth')!='Int24':
            raise ValidationError('unsupported sampled native media/routing/format')
        if len(native['tracks'])!=len(p.tracks):raise ValidationError('sample track count drift')
        view=deepcopy(native);sources=native['sources'];source_ids=[];media=set()
        defaults={x['id']:x['default'] for x in self.base._discover()['plugins']['subtractive_synth']['params']}
        for i,t in enumerate(p.tracks):
            if t.id not in assets:
                if native['tracks'][i]['kind']!='Instrument':raise ValidationError('unsupported native track kind')
                continue
            asset=assets[t.id];m=read_asset(asset);inst=native['tracks'][i]['instrument']
            if (set(inst)!={'plugin','params','bypass','active','preset','sample'} or inst['plugin']!='sampler' or
                inst['active'] is not True or inst['bypass'] is not False or inst['preset']!='<factory default>' or
                set(inst['params'])!=set(self._values(p,t,asset)) or native['tracks'][i]['kind']!='Instrument'):
                raise ValidationError('native sampled instrument structure drift')
            if any(not _close(inst['params'][k],v) for k,v in self._values(p,t,asset).items()):
                raise ValidationError('native sampler parameters differ')
            found=[s for s in sources if s['id']==inst['sample']]
            if len(found)!=1:raise ValidationError('missing/ambiguous sampler media source')
            s=found[0];path=Path(s['path'])
            if (set(s)!={'id','name','path','channels','frames','sample_rate','format','time_reference','unsaved'} or
                len(path.parts)!=2 or path.parts[0]!='Audio Files' or path.name in ('.','..') or '\\' in path.name or ':' in path.name or path.suffix!='.wav' or
                (s['channels'],s['frames'],s['sample_rate'],s['format'],s['time_reference'],s['unsaved']) !=
                (m['audio']['channels'],m['audio']['frames'],48000,'Wav',0,False)):
                raise ValidationError('native sample source metadata/path drift')
            verify_native_audio(Path(root)/path,m['audio']);media.add(s['path']);source_ids.append(s['id'])
            view['tracks'][i]['instrument']={'plugin':'subtractive_synth','params':defaults,'active':True,'bypass':False,'preset':None}
        if len({s['id'] for s in sources})!=len(sources) or set(source_ids)!={s['id'] for s in sources}:
            raise ValidationError('unreferenced/duplicate native sample sources')
        folder=Path(root)/'Audio Files'
        observed={str(x.relative_to(root)) for x in folder.rglob('*') if x.is_file()} if folder.exists() else set()
        if observed!=media:raise ValidationError('native sample media closure differs')
        return self.base._verify_project(shadow,view)

    def _script(self,commands,source,stage,work):
        if any(k!='mix.sampler_load' for k,_ in commands):raise ValidationError('unreviewed sampler command')
        script=Path(work)/'load.txt';script.write_text('\n'.join(k+' '+json.dumps(v,allow_nan=False) for k,v in commands)+'\n')
        text=self.base._call(['script',str(script),'--in',str(source),'--save',str(stage/'session.scraft')],work)
        lines=text.splitlines()
        if len(lines)!=len(commands)+1 or any(not l.startswith(k+': ') for l,(k,_) in zip(lines,commands)):
            raise ValidationError('unexpected sampler command results')

    def _reopen(self,stage,work):
        reopened=Path(work)/'reopened';shutil.copytree(stage,reopened)
        self.base._run([],work,source=stage/'session.scraft',destination=reopened/'session.scraft')
        if _read_json(stage/'session.scraft')!=_read_json(reopened/'session.scraft'):
            raise ValidationError('sample native state changed on reopen')
        return reopened

    def _publish(self,stage,dest,p,assets,report):
        native=_read_json(stage/'session.scraft');ids=self._verify(p,native,assets,stage)
        save(p,stage/'project.kuang.json');midi_export(p,stage/'song.mid');write(stage/'report.json',report)
        write(stage/'manifest.json',{'version':'sample-native-1','canonical_hash':state_hash(p),
            'capabilities':self.capabilities(),'identities':ids,'files':inventory(stage)})
        dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
        try:
            for f in stage.iterdir():shutil.move(str(f),dest/f.name)
        except BaseException:shutil.rmtree(dest);raise
        return report

    def export(self,project,assignments,destination):
        validate(project);self.capabilities();dest=self._new(destination)
        assets={k:self.local(v) for k,v in assignments.items()}
        if not assets or any(dest.is_relative_to(v) for v in assets.values()):raise ValidationError('invalid sample output/asset assignment')
        before={k:inventory(v) for k,v in assets.items()}
        bound=any(t.instrument and t.instrument.plugin_ref=='soundcraft:sampler' for t in project.tracks)
        p=deepcopy(project) if bound else bind_samples(project,assets)
        for t in p.tracks:
            if t.id in assets:self._values(p,t,assets[t.id])
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='sample-export-') as d:
            work=Path(d);bridge=work/'bridge';self.base.export(self._shadow(p),bridge)
            old=_read_json(bridge/'session.scraft');stage=work/'publish';stage.mkdir();(stage/'assets').mkdir()
            copied={};commands=[]
            for i,t in enumerate(p.tracks):
                if t.id not in assets:continue
                m=read_asset(assets[t.id]);target=stage/'assets'/t.id;shutil.copytree(assets[t.id],target);copied[t.id]=target
                commands.append(('mix.sampler_load',{'track':old['tracks'][i]['id'],'path':str(target/m['file']),
                                                     'params':self._values(p,t,target)}))
            self._script(commands,bridge/'session.scraft',stage,work)
            actual=_read_json(stage/'session.scraft');view=deepcopy(actual)
            for i,t in enumerate(p.tracks):
                if t.id in assets:view['tracks'][i]['instrument']=old['tracks'][i]['instrument']
            view['sources']=old['sources'];view['next_id']=old['next_id']
            if view!=old:raise ValidationError('sampler export changed unrelated native state')
            self._verify(p,actual,copied,stage);reopened=self._reopen(stage,work)
            self._verify(p,_read_json(reopened/'session.scraft'),{k:reopened/'assets'/k for k in copied},reopened)
            if any(inventory(v)!=before[k] for k,v in assets.items()):raise ValidationError('sample library changed during export')
            return self._publish(stage,dest,p,copied,{'verified':True,'live_sample_tracks':list(assets),
                'full_native_reopen_equal':True,'canonical_hash':state_hash(p),'human_listening':False})

    def _load(self,source):
        self.capabilities();source=self.local(source);m=_read_json(source/'manifest.json')
        if set(m)!={'version','canonical_hash','capabilities','identities','files'} or m['version']!='sample-native-1' or m['capabilities']!=self.capabilities():
            raise ValidationError('sample bundle contract drift')
        files=inventory(source);files.pop('manifest.json',None)
        if files!=m['files']:raise ValidationError('sample bundle/file drift')
        p=load(source/'project.kuang.json');assets={t.id:source/'assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
        native=_read_json(source/'session.scraft')
        if state_hash(p)!=m['canonical_hash'] or self._verify(p,native,assets,source)!=m['identities']:
            raise ValidationError('sample canonical/native identity drift')
        return source,p,native,assets

    def inspect(self,source):
        source,p,native,_=self._load(source);before=inventory(source)
        host=self.base._run([('session.inspect',{'detail':'full'})],self.scratch,source=source/'session.scraft')[0]
        if inventory(source)!=before:raise ValidationError('sample inspection changed source')
        return {'native':native,'host':host,'canonical_hash':state_hash(p),'verified_snapshot_only':True}

    def import_project(self,source):
        _,p,_,_=self._load(source);self.inspect(source);return deepcopy(p)

    def save(self,source,destination):
        source,p,native,_=self._load(source);dest=self._new(destination,source);before=inventory(source)
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='sample-save-') as d:
            stage=Path(d)/'publish';shutil.copytree(source,stage);(stage/'manifest.json').unlink()
            self.base._run([],d,source=source/'session.scraft',destination=stage/'session.scraft')
            if _read_json(stage/'session.scraft')!=native or inventory(source)!=before:raise ValidationError('sample save changed state/source')
            return self._publish(stage,dest,p,{k:stage/'assets'/k for k in (t.id for t in p.tracks if t.instrument.plugin_ref=='soundcraft:sampler')},
                                 {'verified':True,'full_native_reopen_equal':True,'canonical_hash':state_hash(p)})

    def render(self,source,output,*,end_seconds=None):
        source,p,native,assets=self._load(source);dest=self._new(output,source)
        end=p.bars*4*60/p.tempo_bpm+8 if end_seconds is None else end_seconds
        if dest.suffix!='.wav' or type(end) not in (float,int) or not math.isfinite(end) or not 0<end<=600:
            raise ValidationError('fresh sampler WAV and valid duration required')
        last=max([p.length/p.ppq*60/p.tempo_bpm]+[at+.25 for t in p.tracks if t.id in assets
            for at,change in _voice_events(p,t,read_asset(assets[t.id])) if change==-1])
        if end<last:raise ValidationError('render would truncate the song or an active sample; request a longer end')
        before=inventory(source)
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='sample-render-') as d:
            work=Path(d);stage=work/'bundle';shutil.copytree(source,stage);wav=work/'audio.wav'
            self.base._run([('file.bounce_mix',{'path':str(wav),'format':'wav','bit_depth':24,'dither':False,
                'start':{'seconds':0},'end':{'seconds':end}})],work,source=stage/'session.scraft',destination=stage/'session.scraft')
            audio=analyze_wav(wav)
            with wave.open(str(wav),'rb') as w:
                w.setpos(max(0,w.getnframes()-round(w.getframerate()*.25)))
                frames=list(_decode(w.readframes(round(w.getframerate()*.25)),3,2))
                tail=math.sqrt(sum(l*l+r*r for l,r in frames)/(2*len(frames)))
            if ((audio['sample_rate'],audio['channels'],audio['bits_per_sample'])!=(48000,2,24) or
                abs(audio['duration_seconds']-end)>1/48000 or not audio['non_silent'] or audio['clipped_samples'] or tail>10**(-65/20) or
                _read_json(stage/'session.scraft')!=native or inventory(source)!=before):
                raise ValidationError('sampler render format/silence/clipping/state/source failure')
            dest.parent.mkdir(parents=True,exist_ok=True);os.link(wav,dest)
        return {'audio':audio,'sha256':digest(dest),'native_unchanged':True}

    def apply(self,source,destination,operations,scope,expected_before_hash):
        source,p,before,assets=self._load(source);dest=self._new(destination,source)
        allowed={t.instrument.id:t for t in p.tracks if t.id in assets}
        if not operations or any(type(o) is not SetParameter or o.target_id not in allowed or o.parameter_id not in CONTROLS for o in operations):
            raise ValidationError('sample apply supports existing static sampler controls only')
        e=Engine(p);receipt=e.apply(operations,scope,expected_before_hash);original=inventory(source)
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='sample-edit-') as d:
            work=Path(d);stage=work/'edited';self.export(e.project,assets,stage)
            actual=_read_json(stage/'session.scraft');expected=deepcopy(before)
            for op in operations:
                t=allowed[op.target_id];i=next(i for i,x in enumerate(p.tracks) if x.id==t.id)
                native,_,_,_,_,scale=CONTROLS[op.parameter_id]
                if not _close(actual['tracks'][i]['instrument']['params'][native],op.value*scale):raise ValidationError('sample edit not applied')
                expected['tracks'][i]['instrument']['params'][native]=actual['tracks'][i]['instrument']['params'][native]
            if expected!=actual or inventory(source)!=original:raise ValidationError('sample edit changed unrelated state')
            (stage/'manifest.json').unlink();write(stage/'receipt.json',asdict(receipt))
            return self._publish(stage,dest,e.project,{k:stage/'assets'/k for k in assets},
                {'verified':True,'exact_unrelated_native_state':True,'full_native_reopen_equal':True})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('asset','capabilities','export','inspect','save','render','edit'))
    p.add_argument('--workspace');p.add_argument('--soundcraft');p.add_argument('--source');p.add_argument('--out')
    p.add_argument('--provenance');p.add_argument('--mapping');p.add_argument('--asset',action='append',default=[])
    p.add_argument('--track');p.add_argument('--parameter');p.add_argument('--value',type=float)
    p.add_argument('--end-seconds',type=float)
    a=p.parse_args()
    try:
        workspace=Path(a.workspace or Path.cwd()).resolve()
        def local(path):
            if path is None:raise ValidationError('required path missing')
            target=Path(path).absolute()
            if target.is_symlink() or not target.resolve().is_relative_to(workspace):raise ValidationError('files must stay inside workspace')
            return target.resolve()
        if a.action=='asset':
            result=create_asset(local(a.source),local(a.out),strict_json(local(a.provenance).read_text()),strict_json(local(a.mapping).read_text()))
        else:
            adapter=SampledInstrumentAdapter(a.soundcraft,workspace=workspace)
            if a.action=='capabilities':result=adapter.capabilities()
            elif a.action=='export':
                pairs=[x.split('=',1) for x in a.asset]
                if any(len(x)!=2 for x in pairs) or len({x[0] for x in pairs})!=len(pairs):raise ValidationError('unique TRACK=ASSET bindings required')
                result=adapter.export(load(local(a.source)),{k:local(v) for k,v in pairs},local(a.out))
            elif a.action=='inspect':result=adapter.inspect(local(a.source))
            elif a.action=='save':result=adapter.save(local(a.source),local(a.out))
            elif a.action=='render':result=adapter.render(local(a.source),local(a.out),end_seconds=a.end_seconds)
            else:
                from .transactions import Scope
                project=adapter.import_project(local(a.source));t=next((t for t in project.tracks if t.id==a.track),None)
                if t is None:raise ValidationError('unknown edit track')
                result=adapter.apply(local(a.source),local(a.out),[SetParameter('set_parameter',t.instrument.id,a.parameter,a.value)],
                    Scope([t.id],[],[a.parameter],None,None),state_hash(project))
        print(json.dumps(result,indent=2,allow_nan=False))
    except (ValidationError,OSError) as e:p.exit(2,str(e)+'\n')


if __name__=='__main__':main()
