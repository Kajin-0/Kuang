"""Opt-in, pinned live Vitalium VST3 adapter. Legacy SoundCraft stays strict.

An external user-installed GPL synth remains separate from MIT Kuang. This
adapter issues native CLI operations, never writes or patches host JSON.
Canonical 0.1 + hashed original preset/bindings remain authoritative. GUI edits
are detectable drift, not automatically reconciled. No automatic downloads.
"""
import argparse
import base64
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from .audio import analyze_wav
from .midi import export as midi_export
from .schema import (BAR,Clip,Instrument,Note,ParameterSpec,Section,ValidationError,
                     dumps,load,save,state_hash,strict_json,validate)
from .soundcraft import SoundCraftAdapter,_hash,_read_json
from .vitalium_patch import PLUGIN_ID,VERSION,chunks,component_patch,original_patch
from functools import lru_cache

HOST_SHA='84466d199a6cb4d4924a9179fdf36b0c6d1ab3a0082b60ceed50d06f09f0b130'
PLUGIN_SHA='c6329121bd9a4923a54d3e55a9fba9bf8635a1e1d8990fa4be69a05703ed24c1'
CONTRACT='5af7ed8eed0e51a251da6dee6f57a9b83ac6ae004c70b13a96416cdee4ad49f7'
LAYOUT_SHA='1cc2cf525f8801a6ca7dc5c643074b4f36dda7b76182b3052da352b9d43452d7'

@lru_cache(maxsize=1)
def _original_waves():return original_patch('pad')['settings']['wavetables']


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):Path(path).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def inventory(path):
    path=Path(path)
    if any(p.is_symlink() for p in path.rglob('*')):raise ValidationError('bundle symlinks unsupported')
    return {str(p.relative_to(path)):digest(p) for p in sorted(path.rglob('*')) if p.is_file()}


def read_patch(path):
    path=Path(path);m=_read_json(path/'manifest.json')
    keys={'version','plugin','plugin_version','role','license','host','original_content_only',
          'factory_content','native_defaults','all_normalized_parameters_restored','component_roundtrip_exact','sha256'}
    if set(m)!=keys or m['version']!='external-patch-1' or m['plugin']!=PLUGIN_ID or m['plugin_version']!=VERSION:
        raise ValidationError('unsupported external patch/manifest')
    if (m['role'] not in ('pad','bass','pluck') or m['host']!='Pedalboard 0.9.26' or
        m['original_content_only'] is not True or m['factory_content'] is not False or
        m['all_normalized_parameters_restored'] is not True or m['component_roundtrip_exact'] is not True):
        raise ValidationError('unverified/foreign external patch')
    files={'patch.vital','patch.vstpreset','component.bin','bindings.json'}
    if type(m['sha256']) is not dict or set(m['sha256'])!=files:
        raise ValidationError('invalid patch inventory')
    if any(not (path/f).is_file() or (path/f).stat().st_size>4*2**20 for f in files):raise ValidationError('missing/oversized patch asset')
    if inventory(path)!={**m['sha256'],'manifest.json':digest(path/'manifest.json')}:
        raise ValidationError('patch inventory drift or unexpected files')
    if any(digest(path/k)!=v for k,v in m['sha256'].items()):raise ValidationError('patch content drift')
    if chunks((path/'patch.vstpreset').read_bytes())[b'Comp']!=(path/'component.bin').read_bytes():
        raise ValidationError('preset/component mismatch')
    for data in (_read_json(path/'patch.vital'),component_patch((path/'component.bin').read_bytes())):
        try:
            sample=data['settings']['sample']
            valid=(data['author']=='Kuang' and data['synth_version']==VERSION and
                   data['preset_name']=='Kuang '+m['role'] and data['settings']['wavetables']==_original_waves() and
                   sample['length']==32 and base64.b64decode(sample['samples'],validate=True)==bytes(64))
        except (KeyError,TypeError,ValueError):valid=False
        if not valid:raise ValidationError('non-original or malformed preset/wavetable/sample content')
    rows=_read_json(path/'bindings.json');defaults=m['native_defaults']
    if type(defaults) is not dict or len(defaults)!=2851 or any(not k.isdecimal() or type(v) not in (int,float) or not math.isfinite(v) for k,v in defaults.items()):
        raise ValidationError('unexpected native controller defaults')
    seen=set();ids=set()
    if type(rows) is not list or len(rows)!=771:raise ValidationError('unexpected controller count')
    for row in rows:
        if type(row) is not dict or set(row)!={'index','native_id','name','canonical_id','scale','steps','default_normalized','normalized'}:
            raise ValidationError('unknown controller binding field')
        index=row['index'];steps=row['steps'];scale=row['scale']
        if (type(index) is not int or not 0<=index<772 or index in seen or row['native_id'] in ids or
            row['canonical_id']!='vitalium.param'+str(index) or not isinstance(row['name'],str) or not row['name'] or
            type(steps) is not int or steps not in (0,*range(2,130)) or scale!=(steps-1 if steps else 1)):
            raise ValidationError('invalid/duplicate normalized binding')
        native=0
        for char in str(index):native=(31*native+ord(char))&0x7fffffff
        if row['native_id']!=str(native) or str(native) not in defaults:raise ValidationError('wrong native parameter ID')
        for key in ('normalized','default_normalized'):
            value=row[key]
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:
                raise ValidationError('invalid normalized controller')
        if abs(defaults[str(native)]-row['default_normalized']*scale)>.00002:
            raise ValidationError('controller default disagreement')
        seen.add(index);ids.add(str(native))
    if _hash([{k:v for k,v in r.items() if k!='normalized'} for r in rows])!=LAYOUT_SHA:
        raise ValidationError('external controller metadata fingerprint changed')
    return m,rows


def bound_project(source,assignments):
    validate(source)
    if not assignments:raise ValidationError('explicit track/patch assignments required')
    p=deepcopy(source);registry={x.id for x in p.parameters};found=set()
    for t in p.tracks:
        if t.id not in assignments:continue
        if t.kind!='midi' or t.instrument is None:raise ValidationError('external patch requires MIDI instrument track')
        if any(l.target_id in (t.id,t.instrument.id) for l in p.locks):raise ValidationError('external instrument target is locked')
        if any(x.target_id==t.instrument.id for x in p.automation):raise ValidationError('external instrument automation unsupported')
        path=Path(assignments[t.id]);_,rows=read_patch(path)
        t.instrument.kind='plugin';t.instrument.plugin_ref=PLUGIN_ID;t.instrument.midi_program=None
        t.instrument.preset_ref='sha256:'+digest(path/'manifest.json')
        t.instrument.parameters={r['canonical_id']:r['normalized'] for r in rows}
        for r in rows:
            if r['canonical_id'] not in registry:
                p.parameters.append(ParameterSpec(r['canonical_id'],'normalized',0,1,0,['instrument']));registry.add(r['canonical_id'])
        found.add(t.id)
    if found!=set(assignments):raise ValidationError('unknown external track ID')
    p.metadata.update(external_synth_source_hash=state_hash(source),external_synth_backend='Vitalium 1.0.6 / SoundCraft 0.11.0 experimental',
        external_synth_notes='Live external GPL plugin, separately installed. Original MIDI unchanged. Hash-pinned preset + normalized overrides; no oscillator automation or official Vital compatibility claim.')
    validate(p);return p


class _SandboxSoundCraft(SoundCraftAdapter):
    def __init__(self,owner,executable):self.owner=owner;super().__init__(executable,timeout=240)
    def _call(self,argv,cwd):return self.owner.call([str(self.executable),*argv],cwd)


class ExternalSynthAdapter:
    def __init__(self,plugin,executable=None,*,workspace=None,center_pitch_bend=False):
        if type(center_pitch_bend) is not bool:raise ValidationError('explicit MIDI pitch-center boolean required')
        self.center_pitch_bend=center_pitch_bend
        self.workspace=Path(workspace or Path.cwd()).resolve();self.scratch=self.local(self.workspace/'.local/phase11/tmp')
        self.plugin=self.local(plugin);self.module=self.plugin/'Contents/x86_64-linux/vitalium.so'
        if not self.module.is_file() or digest(self.module)!=PLUGIN_SHA:
            raise ValidationError('reviewed DISTRHO Vitalium 1.0.6 Linux VST3 missing or different; official Vital is not verified')
        self.bwrap=shutil.which('bwrap')
        if not self.bwrap:raise ValidationError('optional external host path requires user-installed bubblewrap')
        self.scratch.mkdir(parents=True,exist_ok=True);self.base=_SandboxSoundCraft(self,executable)
        if digest(self.base.executable)!=HOST_SHA:raise ValidationError('external adapter requires exact reviewed SoundCraft binary')
        self._caps=None

    def local(self,path):
        p=Path(path).resolve()
        if not p.is_relative_to(self.workspace):raise ValidationError('external synth files must stay inside workspace')
        return p

    def call(self,argv,cwd):
        prefix=[self.bwrap,'--die-with-parent','--ro-bind','/','/','--bind',str(self.workspace),str(self.workspace),'--unshare-net']
        for key,path in {'VST3_PATH':self.plugin.parent,'XDG_CONFIG_HOME':self.scratch.parent/'config',
                         'XDG_CACHE_HOME':self.scratch.parent/'cache','XDG_DATA_HOME':self.scratch.parent/'data',
                         'XDG_DOCUMENTS_DIR':self.scratch.parent/'documents','TMPDIR':self.scratch}.items():
            path.mkdir(parents=True,exist_ok=True);prefix+=['--setenv',key,str(path)]
        # bubblewrap bounds argv count; the original 64-bar song has over 7000
        # automation points. Use the host's real data-only script transport for
        # long builtin batches, preserving exact command order and JSON values.
        script=None;argv=list(map(str,argv))
        if len(argv)>8000 and argv[1]=='run':
            from .soundcraft import COMMANDS
            lines=[];flags=[];i=2
            while i<len(argv):
                flag=argv[i]
                if flag not in ('--cmd','--in','--save') or i+1>=len(argv):raise ValidationError('unsupported long host argv')
                value=argv[i+1];i+=2
                if flag=='--cmd':
                    name,sep,data=value.partition('=')
                    if name not in COMMANDS:raise ValidationError('unsupported long host operation')
                    data=data if sep else '{}';strict_json(data);lines.append(name+' '+data)
                else:flags.extend([flag,value])
            fd,name=tempfile.mkstemp(prefix='commands-',suffix='.txt',dir=self.scratch);script=Path(name)
            with os.fdopen(fd,'w') as f:f.write('\n'.join(lines)+'\n')
            argv=[argv[0],'script',str(script),*flags]
        try:result=subprocess.run([*prefix,*argv],cwd=cwd,capture_output=True,text=True,timeout=240)
        finally:
            if script is not None:script.unlink()
        if result.returncode or result.stderr.strip():raise ValidationError('external host failed: '+result.stderr[:1200]+result.stdout[-1000:])
        if len(result.stdout)>32*2**20:raise ValidationError('oversized external host output')
        return result.stdout

    def capabilities(self):
        if digest(self.module)!=PLUGIN_SHA or digest(self.base.executable)!=HOST_SHA:
            raise ValidationError('reviewed plugin/host binary changed')
        if self._caps is None:
            if _hash(self.base._discover())!=CONTRACT:raise ValidationError('SoundCraft builtin contract drift')
            for command in ('engine.vst3_plugins','mix.insert_state'):
                if strict_json(self.base._call(['describe',command],self.scratch)).get('id')!=command:
                    raise ValidationError('missing external lifecycle command')
            line=self.base._call(['run','--cmd','engine.vst3_plugins'],self.scratch)
            if not line.startswith('engine.vst3_plugins: '):raise ValidationError('bad VST3 discovery output')
            plugins=strict_json(line.split(': ',1)[1]);matches=[x for x in plugins if x.get('id')==PLUGIN_ID]
            if len(matches)!=1 or matches[0]['version']!=VERSION or matches[0]['name']!='Vitalium' or matches[0]['is_instrument'] is not True or Path(matches[0]['path']).resolve()!=self.plugin:
                raise ValidationError('reviewed Vitalium not discovered at requested path')
            self._caps={'adapter':'external-vitalium-experimental-1','plugin':matches[0],
                'plugin_sha256':PLUGIN_SHA,'soundcraft_sha256':HOST_SHA,'contract_hash':CONTRACT,
                'official_vital_tested':False,'live_native_instrument':True,'normalized_static_controls':771,
                'instrument_automation':False,'native_json_mutation':False,'downloads':False,
                'license':'External Vitalium GPL-3.0-or-later; optional preparer Pedalboard GPL-3.0; MIT Kuang remains separate'}
        result=deepcopy(self._caps)
        if self.center_pitch_bend:
            result['midi_pitch_initialization']={'version':'vitalium-ch1-center-1','native_id':'1835232641','normalized':.5,'channel':0,
                'reason':'JUCE synthetic channel-1 pitch-bend input defaults to zero; actual multi-register PCM calibration required'}
        return result

    def script(self,commands,source,output,work):
        if any(k not in ('mix.instrument','mix.insert_state') for k,_ in commands):raise ValidationError('unsupported external operation')
        path=Path(work)/'commands.txt';path.write_text('\n'.join(k+' '+json.dumps(v,separators=(',',':'),allow_nan=False) for k,v in commands)+'\n')
        text=self.base._call(['script',str(path),'--in',str(source),'--save',str(output)],work)
        lines=text.splitlines()
        if len(lines)!=len(commands)+1 or any(not line.startswith(key+': ') for line,(key,_) in zip(lines,commands)):
            raise ValidationError('unexpected external command result')
        if strict_json(lines[-1]).get('path')!=str(output) or not Path(output).is_file():raise ValidationError('external save failed')

    def _new(self,path):
        p=self.local(path)
        if p.is_relative_to(self.plugin):raise ValidationError('outputs cannot modify the installed plugin bundle')
        if p.exists() or p.is_symlink():raise ValidationError('new external bundle/output only')
        p.parent.mkdir(parents=True,exist_ok=True);return p

    @staticmethod
    def _shadow(project):
        p=deepcopy(project)
        for t in p.tracks:
            if t.instrument and t.instrument.plugin_ref==PLUGIN_ID:
                t.instrument=Instrument(t.instrument.id,'plugin','soundcraft:subtractive_synth',None,None,{})
        validate(p);return p

    def _values(self,p,t,path):
        manifest,rows=read_patch(path)
        if t.instrument.plugin_ref!=PLUGIN_ID or t.instrument.preset_ref!='sha256:'+digest(path/'manifest.json') or t.instrument.midi_program is not None:
            raise ValidationError('external canonical/preset reference mismatch')
        if set(t.instrument.parameters)!={r['canonical_id'] for r in rows}:raise ValidationError('unmapped external controls')
        if any(a.target_id==t.instrument.id for a in p.automation):raise ValidationError('external instrument lanes unsupported')
        result=deepcopy(manifest['native_defaults'])
        for r in rows:
            spec=next(x for x in p.parameters if x.id==r['canonical_id'])
            if (spec.unit,spec.minimum,spec.maximum,spec.targets)!=('normalized',0,1,['instrument']):
                raise ValidationError('external controllers require their exact normalized registry')
            v=t.instrument.parameters[r['canonical_id']]
            if r['steps'] and abs(v*r['scale']-round(v*r['scale']))>2e-5:raise ValidationError('fractional external discrete selector')
            result[r['native_id']]=round(v*r['scale']) if r['steps'] else v
        if self.center_pitch_bend:
            if result.get('1835232641')!=0 or any(n.channel!=0 for c in t.clips for n in c.notes):
                raise ValidationError('reviewed channel-1 MIDI pitch-center contract requires default-zero slot and channel-0 notes')
            result['1835232641']=.5
        return result

    def _verify(self,p,native,patches):
        shadow=self._shadow(p);view=deepcopy(native)
        defaults={x['id']:x['default'] for x in self.base._discover()['plugins']['subtractive_synth']['params']}
        external={t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref==PLUGIN_ID}
        if external!=set(patches):raise ValidationError('missing/extra external asset assignments')
        if native.get('sources') or native.get('videos') or native.get('busses') or native.get('sample_rate')!=48000 or native.get('bit_depth')!='Int24':
            raise ValidationError('unsupported external native media/routing/format')
        for i,t in enumerate(p.tracks):
            if t.id not in external:continue
            path=patches[t.id];inst=native['tracks'][i]['instrument'];expected=self._values(p,t,path)
            if (set(inst)!={'plugin','params','bypass','active','preset','state'} or inst['plugin']!=PLUGIN_ID or
                inst['active'] is not True or inst['bypass'] is not False or inst['preset']!='<factory default>' or
                inst['state']!=base64.b64encode((Path(path)/'component.bin').read_bytes()).decode() or set(inst['params'])!=set(expected)):
                raise ValidationError('external device/embedded state differs')
            if any(not math.isclose(inst['params'][k],v,rel_tol=2e-7,abs_tol=1e-6) for k,v in expected.items()):
                raise ValidationError('external normalized/native controls differ')
            # Validation-only projection: no modified native JSON is written or
            # sent to the host. External state was verified above; reuse the
            # strict existing note/FX/mixer/lane verifier for everything else.
            view['tracks'][i]['instrument']={'plugin':'subtractive_synth','params':defaults,'active':True,'bypass':False,'preset':None}
        return self.base._verify_project(shadow,view)

    def _publish(self,stage,dest,p,patches,report):
        native=_read_json(stage/'session.scraft');ids=self._verify(p,native,patches)
        save(p,stage/'project.kuang.json');midi_export(p,stage/'song.mid');write(stage/'report.json',report)
        write(stage/'manifest.json',{'version':'external-native-1','canonical_hash':state_hash(p),
              'capabilities':self.capabilities(),'identities':ids,'files':inventory(stage)})
        # Exclusive directory reservation preserves a concurrent writer; only
        # the reserved directory is removed if publication itself fails.
        dest.mkdir()
        try:
            for f in sorted(stage.iterdir()):shutil.move(str(f),dest/f.name)
        except BaseException:
            shutil.rmtree(dest);raise
        return report

    def export(self,project,assignments,destination):
        validate(project);self.capabilities();dest=self._new(destination)
        patches={k:self.local(v) for k,v in assignments.items()};before={k:inventory(v) for k,v in patches.items()}
        if any(dest.is_relative_to(path) for path in patches.values()):raise ValidationError('external output inside source assets')
        # An unbound source is compiled explicitly; an already bound project
        # retains canonical overrides and exact transaction/receipt semantics.
        p=deepcopy(project) if any(t.instrument and t.instrument.plugin_ref==PLUGIN_ID for t in project.tracks) else bound_project(project,patches)
        for t in p.tracks:
            if t.id in patches:self._values(p,t,patches[t.id])
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='export-') as d:
            work=Path(d);bridge=work/'bridge';self.base.export(self._shadow(p),bridge)
            old=_read_json(bridge/'session.scraft');stage=work/'publish';stage.mkdir();assets=stage/'patches';assets.mkdir()
            commands=[];copied={}
            for i,t in enumerate(p.tracks):
                if t.id not in patches:continue
                target=assets/t.id;shutil.copytree(patches[t.id],target);copied[t.id]=target
                commands += [('mix.instrument',{'track':old['tracks'][i]['id'],'plugin':PLUGIN_ID,'params':self._values(p,t,target)}),
                             ('mix.insert_state',{'track':old['tracks'][i]['id'],'slot':'instrument','state':base64.b64encode((target/'component.bin').read_bytes()).decode()})]
            self.script(commands,bridge/'session.scraft',stage/'session.scraft',work)
            actual=_read_json(stage/'session.scraft');view=deepcopy(actual)
            for i,t in enumerate(p.tracks):
                if t.id in patches:view['tracks'][i]['instrument']=old['tracks'][i]['instrument']
            if view!=old:raise ValidationError('external export changed state outside authorized instruments')
            self._verify(p,actual,copied);self.base._reopen(stage/'session.scraft',work)
            if any(inventory(v)!=before[k] for k,v in patches.items()):raise ValidationError('external source assets changed')
            return self._publish(stage,dest,p,copied,{'verified':True,'live_native_instruments':list(patches),
                'native_full_save_reopen_equal':True,'canonical_hash':state_hash(p),'schema':'0.1','human_listening':False})

    def _load(self,source):
        self.capabilities();source=self.local(source);m=_read_json(source/'manifest.json')
        observed_caps=deepcopy(m.get('capabilities',{}));expected_caps=self.capabilities()
        # A plugin installation path is provenance, not instrument state. The
        # exact module SHA, class ID, version and host contract remain pinned.
        observed_caps.get('plugin',{}).pop('path',None);expected_caps['plugin'].pop('path',None)
        if set(m)!={'version','canonical_hash','capabilities','identities','files'} or m['version']!='external-native-1' or observed_caps!=expected_caps:raise ValidationError('external bundle contract drift')
        observed=inventory(source);observed.pop('manifest.json',None)
        if observed!=m['files']:raise ValidationError('external bundle/source drift')
        p=load(source/'project.kuang.json')
        if state_hash(p)!=m['canonical_hash']:raise ValidationError('canonical external snapshot drift')
        patches={t.id:source/'patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref==PLUGIN_ID}
        native=_read_json(source/'session.scraft')
        if self._verify(p,native,patches)!=m['identities']:raise ValidationError('external identity map drift')
        return source,p,native,patches

    def inspect(self,source):
        source,p,native,_=self._load(source);before=inventory(source)
        host=self.base._run([('session.inspect',{'detail':'full'})],self.scratch,source=source/'session.scraft')[0]
        if inventory(source)!=before:raise ValidationError('external inspection changed source')
        return {'native':native,'host':host,'canonical_hash':state_hash(p),'verified_snapshot_only':True}

    def import_project(self,source):
        # Explicit verified snapshot recovery only, never host-edit inference.
        source,p,_,_=self._load(source);self.inspect(source);return deepcopy(p)

    def save(self,source,destination):
        source,p,native,_=self._load(source);dest=self._new(destination)
        if dest.is_relative_to(source):raise ValidationError('derived external output inside source')
        before=inventory(source)
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='save-') as d:
            work=Path(d);stage=work/'publish';shutil.copytree(source,stage);(stage/'manifest.json').unlink()
            self.base._run([],work,source=source/'session.scraft',destination=stage/'session.scraft')
            if _read_json(stage/'session.scraft')!=native or inventory(source)!=before:raise ValidationError('external save/reopen state differs')
            patches={t.id:stage/'patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref==PLUGIN_ID}
            return self._publish(stage,dest,p,patches,{'verified':True,'native_full_save_reopen_equal':True,'canonical_hash':state_hash(p)})

    def render(self,source,output,*,end_seconds=None):
        source,p,native,_=self._load(source);dest=self._new(output)
        if dest.is_relative_to(source) or dest.suffix!='.wav':raise ValidationError('fresh external WAV outside bundle required')
        end=p.bars*4*60/p.tempo_bpm+8 if end_seconds is None else end_seconds
        if type(end) not in (int,float) or not math.isfinite(end) or not 0<end<=600:raise ValidationError('invalid external render duration')
        before=inventory(source)
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='render-') as d:
            work=Path(d);wav=work/'audio.wav'
            self.base._run([('file.bounce_mix',{'path':str(wav),'format':'wav','bit_depth':24,'dither':False,
                 'start':{'seconds':0},'end':{'seconds':end}})],work,source=source/'session.scraft',destination=work/'session.scraft')
            m=analyze_wav(wav)
            if ((m['sample_rate'],m['channels'],m['bits_per_sample'])!=(48000,2,24) or abs(m['duration_seconds']-end)>1/48000 or
                not m['non_silent'] or m['rms']<1e-6 or m['clipped_samples'] or m['peak']>=1 or _read_json(work/'session.scraft')!=native or inventory(source)!=before):
                raise ValidationError('external render failed PCM/format/persistence/source gate')
            os.link(wav,dest)
        return {'analysis':m,'sha256':digest(dest),'native_unchanged':True}

    def apply(self,source,destination,operations,scope,expected_before_hash):
        from .transactions import Engine,SetParameter
        source,p,before,patches=self._load(source);dest=self._new(destination)
        if dest.is_relative_to(source):raise ValidationError('external edit output inside source bundle')
        allowed={t.instrument.id:t for t in p.tracks if t.id in patches}
        if any(type(op) is not SetParameter or op.target_id not in allowed for op in operations):
            raise ValidationError('external native apply supports existing instrument controls only')
        engine=Engine(p);receipt=engine.apply(operations,scope,expected_before_hash);candidate=engine.project
        original=inventory(source)
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='apply-') as d:
            work=Path(d);staged=work/'candidate';self.export(candidate,patches,staged)
            actual=_read_json(staged/'session.scraft');expected=deepcopy(before)
            for op in operations:
                track=allowed[op.target_id];i=next(i for i,t in enumerate(p.tracks) if t.id==track.id)
                _,rows=read_patch(patches[track.id]);r=next(x for x in rows if x['canonical_id']==op.parameter_id)
                value=next(t for t in candidate.tracks if t.id==track.id).instrument.parameters[op.parameter_id]*r['scale']
                observed=actual['tracks'][i]['instrument']['params'][r['native_id']]
                if not math.isclose(observed,value,abs_tol=1e-6,rel_tol=2e-7):raise ValidationError('external edited scalar differs')
                expected['tracks'][i]['instrument']['params'][r['native_id']]=observed
            if expected!=actual or inventory(source)!=original:raise ValidationError('external edit collateral/source drift')
            (staged/'manifest.json').unlink();write(staged/'receipt.json',asdict(receipt))
            copied={k:staged/'patches'/k for k in patches}
            return self._publish(staged,dest,candidate,copied,{'verified':True,'exact_unrelated_native_state':True,
                'canonical_hash':state_hash(candidate),'native_full_save_reopen_equal':True})


def prepare_patch(adapter,host_python,role,destination,*,modulation=True,volume_db=None):
    from .generator import generate
    adapter.capabilities();dest=adapter._new(destination)
    p=generate();p.bars=2;p.sections=[Section('section-gate','Gate',0,2*BAR)];p.tracks=p.tracks[:1];p.automation=[];p.locks=[]
    t=p.tracks[0];t.instrument=Instrument(t.instrument.id,'plugin','soundcraft:subtractive_synth',None,None,{})
    t.effects=[];t.controls.update({'mixer.gain_db':-18,'mixer.pan':0})
    t.clips=[Clip('clip-gate','Original gate note','midi',0,2*BAR,[Note('note-gate',192,3840,60,90,0)],None)]
    with tempfile.TemporaryDirectory(dir=adapter.scratch,prefix='prepare-') as d:
        work=Path(d);adapter.base.export(p,work/'probe');native=_read_json(work/'probe/session.scraft')
        adapter.script([('mix.instrument',{'track':native['tracks'][0]['id'],'plugin':PLUGIN_ID})],work/'probe/session.scraft',work/'session.scraft',work)
        defaults=_read_json(work/'session.scraft')['tracks'][0]['instrument']['params']
        out=work/'patch';request=work/'request.json'
        write(request,{'plugin':str(adapter.plugin),'defaults':defaults,'role':role,'modulation':modulation,'volume_db':volume_db,'out':str(out)})
        # A small launcher fixes imports without relying on the caller's cwd.
        launcher=work/'worker.py';launcher.write_text('import sys,runpy\nsys.path.insert(0,'+repr(str(Path(__file__).resolve().parent.parent))+')\nrunpy.run_module("kuang.vst3_worker",run_name="__main__")\n')
        # Keep a venv's executable symlink path: resolving it would select the
        # system interpreter and lose the explicitly installed optional host.
        adapter.call([str(Path(host_python).absolute()),str(launcher),str(request)],work)
        read_patch(out)
        bound=bound_project(p,{t.id:out});adapter.export(bound,{t.id:out},work/'gate')
        first=adapter.render(work/'gate',work/'first.wav',end_seconds=8)
        adapter.save(work/'gate',work/'reopened');second=adapter.render(work/'reopened',work/'second.wav',end_seconds=8)
        if first['sha256']!=second['sha256']:raise ValidationError('prepared patch repeated native PCM is not deterministic')
        dest.mkdir()
        try:
            for f in out.iterdir():shutil.move(str(f),dest/f.name)
        except BaseException:shutil.rmtree(dest);raise
    return {'patch':str(dest),'native_non_silent_pcm_repeat_exact':True,'manifest_sha256':digest(dest/'manifest.json')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('capabilities','prepare','export','inspect','save','render','edit'))
    parser.add_argument('--plugin',required=True);parser.add_argument('--soundcraft');parser.add_argument('--workspace')
    parser.add_argument('--source');parser.add_argument('--out-dir');parser.add_argument('--host-python')
    parser.add_argument('--role',choices=('pad','bass','pluck'));parser.add_argument('--volume-db',type=float)
    parser.add_argument('--modulation-off',action='store_true');parser.add_argument('--patch',action='append',default=[])
    parser.add_argument('--track');parser.add_argument('--parameter');parser.add_argument('--normalized-value',type=float)
    args=parser.parse_args()
    try:
        a=ExternalSynthAdapter(args.plugin,args.soundcraft,workspace=args.workspace)
        if args.action=='capabilities':result=a.capabilities()
        elif args.action=='prepare':
            if not args.host_python or not args.role or not args.out_dir:parser.error('prepare requires host-python, role, out-dir')
            result=prepare_patch(a,args.host_python,args.role,args.out_dir,modulation=not args.modulation_off,volume_db=args.volume_db)
        elif args.action=='inspect':result=a.inspect(args.source)
        elif args.action=='save':result=a.save(args.source,args.out_dir)
        elif args.action=='render':result=a.render(args.source,args.out_dir)
        elif args.action=='edit':
            from .transactions import Scope,SetParameter
            source,p,_,patches=a._load(args.source)
            if args.track not in patches or args.parameter is None or args.normalized_value is None:
                parser.error('edit requires external track, exact parameter name/ID, normalized-value')
            _,rows=read_patch(patches[args.track]);matches=[r for r in rows if args.parameter in (r['name'],r['canonical_id'])]
            if len(matches)!=1:raise ValidationError('parameter name/ID is missing or ambiguous')
            param=matches[0]['canonical_id'];track=next(t for t in p.tracks if t.id==args.track)
            result=a.apply(source,args.out_dir,[SetParameter('set_parameter',track.instrument.id,param,args.normalized_value)],
                Scope([track.id],[],[param],None,None),state_hash(p))
        else:
            assignments={}
            for item in args.patch:
                track,sep,path=item.partition('=')
                if not sep or not track or not path or track in assignments:raise ValidationError('use distinct --patch TRACK=LOCAL_PATCH_DIR')
                assignments[track]=path
            result=a.export(load(args.source),assignments,args.out_dir)
        print(json.dumps(result,indent=2,sort_keys=True))
    except (ValidationError,OSError,subprocess.SubprocessError) as exc:raise SystemExit(str(exc))


if __name__=='__main__':main()
