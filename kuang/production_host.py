"""Opt-in native production graph: live samples/Vitalium and real aux buses.

Canonical 0.1 remains authoritative. Only actual CLI commands write .scraft;
verification-only projections reuse the established sample/note/FX verifier.
Send automation is an explicitly named channel-owned dB TRIM over Send.gain_db.
It never pretends that a send is the track's master fader or a new schema kind.
"""
import base64
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
from .external_synth import ExternalSynthAdapter,PLUGIN_ID
from .midi import export as midi_export
from .production_audio import _decode
from .sample_assets import digest,inventory,write,read_asset
from .sampled_instrument import SampledInstrumentAdapter,_voice_events,CONTROLS
from .schema import Instrument,ParameterSpec,ValidationError,load,save,state_hash,validate
from .soundcraft import _close,_hash,_read_json
from .transactions import Engine,SetParameter

MIXER={'mixer.gain_db','mixer.pan','mixer.mute'}
SPREAD='mixer.stereo_spread'
SPREAD_SPEC=ParameterSpec(SPREAD,'normalized',0,1,0,['track'])
COMMANDS={'mix.instrument','mix.insert_state','mix.new_bus','track.new','track.input','track.output',
          'mix.volume','mix.pan','mix.mute','mix.insert','mix.insert_bypass','mix.send',
          'mix.send_level','track.comments','automation.clear','automation.set_point'}


def trim_id(send):return 'route.'+send.id+'.trim_db'


def native_pan(track):
    """Two native channel pan positions, not a widening DSP or phase shift."""
    pan=track.controls['mixer.pan'];spread=track.controls.get(SPREAD,0)
    if abs(pan)+spread>1:raise ValidationError('native stereo pan positions outside [-1,1]')
    return [pan-spread,pan+spread]


def add_spread(project,track,value):
    old=next((x for x in project.parameters if x.id==SPREAD),None)
    if old is not None and old!=SPREAD_SPEC:raise ValidationError('stereo pan registry collision')
    if old is None:project.parameters.append(deepcopy(SPREAD_SPEC))
    track.controls[SPREAD]=value;native_pan(track)


def add_send_trim(project,track,send,base=0):
    key=trim_id(send);spec=ParameterSpec(key,'dB',-72,12,0,['track'])
    old=next((s for s in project.parameters if s.id==key),None)
    if old is not None and old!=spec:raise ValidationError('routing trim registry collision')
    if key in track.controls:raise ValidationError('routing trim control already exists')
    if old is None:project.parameters.append(spec)
    track.controls[key]=base
    return key


def graph_contract(p):
    validate(p);names=[t.name for t in p.tracks]
    if len(names)!=len(set(names)) or any(not name for name in names):raise ValidationError('unique production track names required')
    tracks={t.id:t for t in p.tracks};specs={s.id:s for s in p.parameters}
    for t in p.tracks:
        if t.kind not in ('midi','bus') or (t.kind=='midi' and not any(c.notes for c in t.clips)):
            raise ValidationError('production graph supports sounding MIDI and empty aux buses only')
        if t.kind=='bus' and (t.instrument is not None or t.clips):raise ValidationError('aux buses cannot contain instruments or clips')
        if t.kind=='bus' and t.sends:raise ValidationError('bus-to-bus sends are not verified; use one-level aux returns')
        if not t.output_master and not t.sends:raise ValidationError('disconnected silent production track')
        if len(t.sends)>10 or len(t.effects)>10:raise ValidationError('native strip slot bound exceeded')
        extra=set(t.controls)-MIXER;allowed={trim_id(s) for s in t.sends}|{SPREAD}
        if not MIXER<=set(t.controls) or not extra<=allowed:raise ValidationError('unmapped production channel control')
        native_pan(t)
        if SPREAD in t.controls and specs.get(SPREAD)!=SPREAD_SPEC:raise ValidationError('stereo pan requires exact normalized registry')
        if any(a.target_id==t.id and a.parameter_id==SPREAD for a in p.automation):raise ValidationError('automated spread is not verified')
        if any(abs(x.value)+t.controls.get(SPREAD,0)>1 for a in p.automation if a.target_id==t.id and a.parameter_id=='mixer.pan' for x in a.points):
            raise ValidationError('automated stereo pan positions outside [-1,1]')
        for send in t.sends:
            if tracks[send.target_track_id].kind!='bus' or send.mode!='post_fader' or send.pan!=0:
                raise ValidationError('only verified post-fader center/follow-pan sends to aux buses are supported')
            key=trim_id(send)
            if key in t.controls:
                if specs[key]!=ParameterSpec(key,'dB',-72,12,0,['track']):raise ValidationError('send trim requires exact dB units')
                values=[t.controls[key]]+[x.value for a in p.automation if a.target_id==t.id and a.parameter_id==key for x in a.points]
                if any(not -90<=send.gain_db+v<=12 for v in values):raise ValidationError('trimmed native send gain out of bounds')
        if t.kind=='bus' and any(e.preset_ref is not None or not e.plugin_ref.startswith('soundcraft:') for e in t.effects):
            raise ValidationError('aux effects require verified built-ins without foreign presets')
    return tracks


class ProductionAdapter:
    def __init__(self,executable=None,*,plugin=None,workspace=None):
        self.workspace=Path(workspace or Path.cwd()).resolve();self.scratch=self.workspace/'.local/phase14/tmp';self.scratch.mkdir(parents=True,exist_ok=True)
        self.samples=SampledInstrumentAdapter(executable,workspace=self.workspace);self.samples.scratch=self.scratch
        self.external=ExternalSynthAdapter(plugin,executable,workspace=self.workspace) if plugin else None
        if self.external:self.external.scratch=self.scratch;self.samples.base=self.external.base
        self.base=self.samples.base

    def local(self,path):return self.samples.local(path)

    def new(self,path,source=None):
        if Path(path).is_symlink():raise ValidationError('production destination cannot be a symlink')
        p=self.local(path)
        if p.exists() or p.is_symlink() or (source and p.is_relative_to(self.local(source))):raise ValidationError('new production destination outside source required')
        return p

    def capabilities(self):
        sample=self.samples.capabilities();ext=self.external.capabilities() if self.external else None
        return {'version':'production-native-1','host_sha256':sample['soundcraft_sha256'],'contract_hash':sample['contract_hash'],
            'plugin_sha256':ext['plugin_sha256'] if ext else None,'sampler':True,'aux_buses':True,
            'post_fader_sends':True,'send_automation':'channel-owned dB trim plus fixed Send.gain_db',
            'stereo_pan':'two native pan positions = center minus/plus static spread; no phase DSP',
            'external_plugin':PLUGIN_ID if ext else None,'instrument_automation':False,'pre_fader_or_send_pan':False,
            'true_triggered_sidechain':False,'native_json_mutation':False}

    @staticmethod
    def _plain(p):
        q=deepcopy(p);q.tracks=[t for t in q.tracks if t.kind=='midi']
        owners={x for t in q.tracks for x in (t.id,t.instrument.id,*(e.id for e in t.effects))}
        for t in q.tracks:
            t.sends=[];t.output_master=True;t.controls={k:v for k,v in t.controls.items() if k in MIXER}
            if t.instrument.plugin_ref==PLUGIN_ID:t.instrument=Instrument(t.instrument.id,'plugin','soundcraft:subtractive_synth',None,None,{})
        q.automation=[a for a in q.automation if a.target_id in owners and not a.parameter_id.startswith('route.')]
        q.locks=[l for l in q.locks if l.target_id in owners or any(l.target_id==c.id for t in q.tracks for c in t.clips)]
        validate(q);return q

    def _script(self,commands,path,work):
        if any(k not in COMMANDS for k,_ in commands):raise ValidationError('unreviewed production host operation')
        script=Path(work)/'graph-commands.txt';script.write_text('\n'.join(k+' '+json.dumps(v,allow_nan=False) for k,v in commands)+'\n')
        out=self.base._call(['script',str(script),'--in',str(path),'--save',str(path)],work)
        lines=out.splitlines()
        if len(lines)!=len(commands)+1 or any(not line.startswith(k+': ') for line,(k,_) in zip(lines,commands)):
            raise ValidationError('unexpected production command result')

    def _lane(self,p,lane):
        t=next((t for t in p.tracks if t.id==lane.target_id),None)
        if t and lane.parameter_id.startswith('route.'):
            found=[(i,s) for i,s in enumerate(t.sends) if trim_id(s)==lane.parameter_id]
            if len(found)!=1 or any(x.shape!='linear' for x in lane.points):raise ValidationError('unmapped send trim lane/shape')
            slot,send=found[0]
            return t.id,[('send_'+chr(97+slot)+'_level',{'SendLevel':slot},[(x.id,x.tick,send.gain_db+x.value) for x in sorted(lane.points,key=lambda x:x.tick)])]
        index,mapped=self.base._lane(p,lane)
        if t and lane.parameter_id=='mixer.pan' and t.controls.get(SPREAD,0):
            mapped=[(name,native,[(pid,tick,value+sign*t.controls[SPREAD]) for pid,tick,value in points]) for sign,(name,native,points) in zip((-1,1),mapped)]
        return p.tracks[index].id,mapped

    def _verify_lanes(self,p,t,h):
        expected=[]
        for lane in p.automation:
            tid,mapped=self._lane(p,lane)
            if tid!=t.id:continue
            for _,native,points in mapped:
                matches=[x for x in h['automation'] if x['param']==native];expected.append(native)
                if len(matches)!=1 or matches[0]['enabled'] is not True:raise ValidationError('missing native production lane')
                actual=matches[0]['points']
                if len(actual)!=len(points) or any(a['at']!=self.base._samples(p,tick) or not _close(a['value'],v) for a,(_,tick,v) in zip(actual,points)):
                    raise ValidationError('native production lane timing/value drift')
        if len(h['automation'])!=len(expected):raise ValidationError('extra native production automation')

    def _verify(self,p,native,assets,patches,root):
        graph_contract(p);buses=[t for t in p.tracks if t.kind=='bus'];midi=[t for t in p.tracks if t.kind=='midi']
        if len(native['tracks'])!=len(p.tracks) or len(native['busses'])!=len(buses):raise ValidationError('native production graph count drift')
        busids={}
        for t,b in zip(buses,native['busses']):
            if set(b)!={'id','name','format'} or b['name']!=t.name or b['format']!='Stereo':raise ValidationError('native bus identity/format drift')
            busids[t.id]=b['id']
        hosts={t.id:h for t,h in zip(midi+buses,native['tracks'])}
        view=deepcopy(native);view['busses']=[];view['tracks']=view['tracks'][:len(midi)]
        plain=self._plain(p);defaults={x['id']:x['default'] for x in self.base._discover()['plugins']['subtractive_synth']['params']}
        external={t.id for t in midi if t.instrument.plugin_ref==PLUGIN_ID}
        if external!=set(patches) or (external and self.external is None):raise ValidationError('missing/extra original external patch binding')
        for t in midi+buses:
            h=hosts[t.id];mix=h['mixer']
            if h['name']!=t.name or mix['output']!=('Main' if t.output_master else 'None'):raise ValidationError('native output routing drift')
            for i in range(10):
                s=t.sends[i] if i<len(t.sends) else None;observed=mix['sends'][i]
                if s is None:
                    if observed is not None:raise ValidationError('extra native send')
                else:
                    wanted={'target':{'Bus':busids[s.target_track_id]},'level_db':s.gain_db+t.controls.get(trim_id(s),0),
                        'pan':0.0,'mute':False,'pre_fader':False,'follow_main_pan':True,'surround':None}
                    if type(observed) is not dict or set(observed)!=set(wanted) or any(not _close(observed[k],v) if k=='level_db' else observed[k]!=v for k,v in wanted.items()):
                        raise ValidationError('native send parameters differ')
            self._verify_lanes(p,t,h)
            if t.kind=='midi':
                i=midi.index(t);v=view['tracks'][i];v['mixer']['output']='Main';v['mixer']['sends']=[None]*10
                if any(not _close(a,b) for a,b in zip(mix['pan'],native_pan(t))):raise ValidationError('native stereo channel pan drift')
                v['mixer']['pan']=[t.controls['mixer.pan']]*2
                v['automation']=[x for x in v['automation'] if not (isinstance(x['param'],dict) and 'SendLevel' in x['param'])]
                for lane in v['automation']:
                    if lane['param'] in ('Pan',):raise ValidationError('unknown stereo pan automation encoding')
                    if type(lane['param']) is dict and 'Pan' in lane['param']:
                        sign=-1 if lane['param']['Pan']==0 else 1
                        for point in lane['points']:point['value']-=sign*t.controls.get(SPREAD,0)
                if t.id in external:
                    inst=h['instrument'];values=self.external._values(p,t,patches[t.id])
                    if (set(inst)!={'plugin','params','bypass','active','preset','state'} or inst['plugin']!=PLUGIN_ID or inst['active'] is not True or inst['bypass'] is not False or
                        inst['preset']!='<factory default>' or inst['state']!=base64.b64encode((Path(patches[t.id])/'component.bin').read_bytes()).decode() or set(inst['params'])!=set(values) or
                        any(not math.isclose(inst['params'][k],v,rel_tol=2e-7,abs_tol=1e-6) for k,v in values.items())):
                        raise ValidationError('live external state/controls drift')
                    v['instrument']={'plugin':'subtractive_synth','params':defaults,'active':True,'bypass':False,'preset':None}
            else:
                if h['kind']!='Aux' or h['instrument'] is not None or h['format']!='Stereo' or h['playlists']!=[{'name':t.name,'clips':[]}] or h['active_playlist']!=0 or mix['input']!={'Bus':busids[t.id]}:
                    raise ValidationError('native aux structure/input drift')
                dynamic={'id','name','kind','format','playlists','active_playlist','mixer','automation','instrument'}
                color=h.get('color')
                if type(color) is not list or len(color)!=3 or any(type(v) is not int or not 0<=v<=255 for v in color):raise ValidationError('invalid native aux color')
                # Native track.new rotates its UI palette by strip index.
                defaults={'color':color,'height':'Medium','view':'volume','hidden':False,'inactive':False,'frozen':False,
                    'comments':json.dumps({'kuang_track_id':t.id}),'folder':None,'folder_open':True,'ticks_timebase':False,
                    'elastic':None,'pinned':False}
                mix_dynamic={'volume_db','pan','mute','input','output','inserts','sends'}
                mix_defaults={'solo':False,'solo_safe':False,'record_arm':False,'input_monitor':False,'phase_invert':False,
                    'automation_mode':'Read','trim_db':0.0,'vca':None,'surround':None}
                if ({k:v for k,v in h.items() if k not in dynamic}!=defaults or
                    {k:v for k,v in mix.items() if k not in mix_dynamic}!=mix_defaults or len(mix['pan'])!=2 or len(mix['inserts'])!=10 or len(mix['sends'])!=10):
                    raise ValidationError('unmapped aux native state')
                if not _close(mix['volume_db'],t.controls['mixer.gain_db']) or mix['mute'] is not bool(t.controls['mixer.mute']) or any(not _close(v,w) for v,w in zip(mix['pan'],native_pan(t))):
                    raise ValidationError('aux mixer control drift')
                if sum(x is not None for x in mix['inserts'])!=len(t.effects):raise ValidationError('aux effect count drift')
                for slot,e in enumerate(t.effects):
                    fx=mix['inserts'][slot];plugin=e.plugin_ref.removeprefix('soundcraft:')
                    supplied=dict(self.base._parameter(p,e,plugin,k,v) for k,v in e.parameters.items());bypass=supplied.pop('bypass',False)
                    expected={x['id']:x['default'] for x in self.base._discover()['plugins'][plugin]['params']};expected.update(supplied)
                    if (type(fx) is not dict or set(fx)!={'plugin','params','bypass','active','preset'} or fx['plugin']!=plugin or fx['active'] is not True or fx['bypass'] is not bypass or
                        fx['preset']!='<factory default>' or set(fx['params'])!=set(expected) or any(not _close(fx['params'][k],v) for k,v in expected.items())):
                        raise ValidationError('aux effect parameters differ')
        ids=self.samples._verify(plain,view,assets,root)
        ids['buses']=busids;return ids

    def _publish(self,stage,dest,p,report):
        assets={t.id:stage/'assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
        patches={t.id:stage/'patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref==PLUGIN_ID}
        ids=self._verify(p,_read_json(stage/'session.scraft'),assets,patches,stage)
        for name in ('manifest.json','project.kuang.json','song.mid','report.json'):
            if (stage/name).exists():(stage/name).unlink()
        save(p,stage/'project.kuang.json');midi_export(p,stage/'song.mid');write(stage/'report.json',report)
        write(stage/'manifest.json',{'version':'production-native-1','canonical_hash':state_hash(p),'capabilities':self.capabilities(),'identities':ids,'files':inventory(stage)})
        dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
        try:
            for f in stage.iterdir():shutil.move(str(f),dest/f.name)
        except BaseException:shutil.rmtree(dest);raise
        return report

    def export(self,p,assets,patches,destination):
        graph_contract(p);self.capabilities();dest=self.new(destination)
        assets={k:self.local(v) for k,v in assets.items()};patches={k:self.local(v) for k,v in patches.items()}
        if any(dest.is_relative_to(v) for v in [*assets.values(),*patches.values()]):raise ValidationError('production output intersects assets')
        before={str(v):inventory(v) for v in [*assets.values(),*patches.values()]}
        plain=self._plain(p);midi=[t for t in p.tracks if t.kind=='midi'];buses=[t for t in p.tracks if t.kind=='bus']
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='graph-') as d:
            work=Path(d);stage=work/'publish'
            if assets:self.samples.export(plain,assets,work/'bridge')
            else:self.base.export(plain,work/'bridge')
            shutil.copytree(work/'bridge',stage)
            original=_read_json(stage/'session.scraft');hostids={t.id:h['id'] for t,h in zip(midi,original['tracks'])};commands=[]
            if patches and self.external is None:raise ValidationError('explicit optional external plugin required')
            for t in midi:
                if t.id in patches:
                    target=stage/'patches'/t.id;target.parent.mkdir(exist_ok=True);shutil.copytree(patches[t.id],target)
                    commands.extend([('mix.instrument',{'track':hostids[t.id],'plugin':PLUGIN_ID,'params':self.external._values(p,t,target)}),
                        ('mix.insert_state',{'track':hostids[t.id],'slot':'instrument','state':base64.b64encode((target/'component.bin').read_bytes()).decode()})])
            for t in buses:
                commands.extend([('mix.new_bus',{'name':t.name,'format':'stereo'}),('track.new',{'name':t.name,'kind':'aux','format':'stereo'}),
                    ('track.input',{'track':t.name,'input':t.name}),('track.output',{'track':t.name,'output':'main' if t.output_master else 'none'}),
                    ('mix.volume',{'track':t.name,'db':t.controls['mixer.gain_db']}),('mix.mute',{'track':t.name,'value':bool(t.controls['mixer.mute'])}),
                    ('mix.pan',{'track':t.name,'index':0,'pan':native_pan(t)[0]}),('mix.pan',{'track':t.name,'index':1,'pan':native_pan(t)[1]}),
                    ('track.comments',{'track':t.name,'comments':json.dumps({'kuang_track_id':t.id})})])
                for slot,e in enumerate(t.effects):
                    plugin=e.plugin_ref.removeprefix('soundcraft:');values=dict(self.base._parameter(p,e,plugin,k,v) for k,v in e.parameters.items());bypass=values.pop('bypass',False)
                    commands.extend([('mix.insert',{'track':t.name,'slot':slot,'plugin':plugin,'params':values}),('mix.insert_bypass',{'track':t.name,'slot':slot,'value':bypass})])
            for t in midi+buses:
                target=hostids.get(t.id,t.name)
                if t.kind=='midi' and SPREAD in t.controls:
                    commands.extend(('mix.pan',{'track':target,'index':i,'pan':v}) for i,v in enumerate(native_pan(t)))
                if t.kind=='midi' and not t.output_master:commands.append(('track.output',{'track':t.name,'output':'none'}))
                for slot,s in enumerate(t.sends):
                    commands.append(('mix.send',{'track':target,'slot':slot,'bus':next(x.name for x in buses if x.id==s.target_track_id),
                        'level_db':s.gain_db+t.controls.get(trim_id(s),0),'pre_fader':False}))
            for lane in p.automation:
                tid,mapped=self._lane(p,lane)
                if tid in hostids and not lane.parameter_id.startswith('route.') and not (lane.parameter_id=='mixer.pan' and next(t for t in midi if t.id==tid).controls.get(SPREAD,0)):continue
                target=hostids.get(tid,next((t.name for t in buses if t.id==tid),None))
                for name,_,points in mapped:
                    commands.append(('automation.clear',{'track':target,'param':name,'start':0,'end':self.base._samples(p,p.length)+1}))
                    commands.extend(('automation.set_point',{'track':target,'param':name,'at':self.base._samples(p,tick),'value':value}) for _,tick,value in points)
            self._script(commands,stage/'session.scraft',work)
            actual=_read_json(stage/'session.scraft');view=deepcopy(actual);view['tracks']=view['tracks'][:len(midi)]
            for i,t in enumerate(midi):
                if t.id in patches:view['tracks'][i]['instrument']=original['tracks'][i]['instrument']
                view['tracks'][i]['mixer']['pan']=original['tracks'][i]['mixer']['pan']
                view['tracks'][i]['mixer']['output']='Main';view['tracks'][i]['mixer']['sends']=[None]*10
                view['tracks'][i]['automation']=[x for x in view['tracks'][i]['automation'] if not (isinstance(x['param'],dict) and 'SendLevel' in x['param'])]
                if t.controls.get(SPREAD,0):
                    lanes=view['tracks'][i]['automation'];oldlanes=original['tracks'][i]['automation']
                    if len(lanes)!=len(oldlanes):raise ValidationError('stereo pan lane count drift')
                    ordered=[]
                    for oldlane in oldlanes:
                        found=[x for x in lanes if x['param']==oldlane['param']]
                        if len(found)!=1:raise ValidationError('stereo pan lane identity drift')
                        ordered.append(oldlane if type(oldlane['param']) is dict and 'Pan' in oldlane['param'] else found[0])
                    view['tracks'][i]['automation']=ordered
            view['busses']=original['busses'];view['next_id']=original['next_id'];view['edit']['selected_tracks']=original['edit']['selected_tracks']
            if view!=original or actual['next_id']!=original['next_id']+2*len(buses):raise ValidationError('routing changed unrelated native state')
            self._verify(p,actual,{k:stage/'assets'/k for k in assets},{k:stage/'patches'/k for k in patches},stage)
            reopened=work/'reopened';shutil.copytree(stage,reopened);self.base._run([],work,source=stage/'session.scraft',destination=reopened/'session.scraft')
            if _read_json(reopened/'session.scraft')!=actual:raise ValidationError('production native reopen drift')
            if any(inventory(Path(k))!=v for k,v in before.items()):raise ValidationError('production asset drift')
            return self._publish(stage,dest,p,{'verified':True,'native_graph_and_instruments':True,'full_native_reopen_equal':True})

    def _load(self,source):
        source=self.local(source);m=_read_json(source/'manifest.json')
        if set(m)!={'version','canonical_hash','capabilities','identities','files'} or m['version']!='production-native-1' or m['capabilities']!=self.capabilities():raise ValidationError('production bundle contract drift')
        actual=inventory(source);actual.pop('manifest.json',None)
        if actual!=m['files']:raise ValidationError('production bundle/file drift')
        p=load(source/'project.kuang.json');native=_read_json(source/'session.scraft')
        assets={t.id:source/'assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
        patches={t.id:source/'patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref==PLUGIN_ID}
        if state_hash(p)!=m['canonical_hash'] or self._verify(p,native,assets,patches,source)!=m['identities']:raise ValidationError('production canonical/native identity drift')
        return source,p,native,assets,patches

    def inspect(self,source):
        source,p,native,_,_=self._load(source);before=inventory(source)
        host=self.base._run([('session.inspect',{'detail':'full'})],self.scratch,source=source/'session.scraft')[0]
        if inventory(source)!=before:raise ValidationError('production inspection source drift')
        return {'native':native,'host':host,'canonical_hash':state_hash(p)}

    def save(self,source,destination):
        source,p,native,_,_=self._load(source);dest=self.new(destination,source);before=inventory(source)
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='save-') as d:
            stage=Path(d)/'publish';shutil.copytree(source,stage);(stage/'manifest.json').unlink()
            self.base._run([],d,source=source/'session.scraft',destination=stage/'session.scraft')
            if _read_json(stage/'session.scraft')!=native or inventory(source)!=before:raise ValidationError('production save drift')
            return self._publish(stage,dest,p,{'verified':True,'full_native_reopen_equal':True})

    def render(self,source,output,*,end_seconds=None):
        source,p,native,assets,_=self._load(source);dest=self.new(output,source);end=p.length/p.ppq*60/p.tempo_bpm+5 if end_seconds is None else end_seconds
        if dest.suffix!='.wav' or type(end) not in (float,int) or not math.isfinite(end) or not p.length/p.ppq*60/p.tempo_bpm<=end<=600:raise ValidationError('full production WAV and bounded duration required')
        last=max([p.length/p.ppq*60/p.tempo_bpm]+[at+.25 for t in p.tracks if t.id in assets for at,change in _voice_events(p,t,read_asset(assets[t.id])) if change==-1])
        if end<last:raise ValidationError('production bounce would truncate an active sample')
        before=inventory(source)
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='render-') as d:
            work=Path(d);stage=work/'bundle';shutil.copytree(source,stage);out=work/'render.wav'
            self.base._run([('file.bounce_mix',{'path':str(out),'format':'wav','bit_depth':24,'dither':False,'start':{'seconds':0},'end':{'seconds':end}})],work,source=stage/'session.scraft',destination=stage/'session.scraft')
            audio=analyze_wav(out)
            with wave.open(str(out),'rb') as w:
                w.setpos(w.getnframes()-12000);v=list(_decode(w.readframes(12000),3,2));tail=math.sqrt(sum(l*l+r*r for l,r in v)/(2*len(v)))
            if (audio['sample_rate'],audio['channels'],audio['bits_per_sample'])!=(48000,2,24) or not audio['non_silent'] or audio['clipped_samples'] or abs(audio['duration_seconds']-end)>1/48000 or tail>10**(-65/20):raise ValidationError('production audio format/silence/clips/tail failure')
            if _read_json(stage/'session.scraft')!=native or inventory(source)!=before:raise ValidationError('production render changed native/source')
            dest.parent.mkdir(parents=True,exist_ok=True);os.link(out,dest)
        return {'audio':audio,'sha256':digest(dest),'native_unchanged':True}

    def apply(self,source,destination,operations,scope,expected_before_hash):
        source,p,before,assets,patches=self._load(source);dest=self.new(destination,source)
        if not operations or any(type(x) is not SetParameter for x in operations):raise ValidationError('production apply accepts existing static parameters only; edit lanes canonically before fresh export')
        if any(a.target_id==o.target_id and a.parameter_id==o.parameter_id and a.points for o in operations for a in p.automation):raise ValidationError('base edit overridden by automation; edit the explicit lane instead')
        e=Engine(p);receipt=e.apply(operations,scope,expected_before_hash);original=inventory(source)
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='edit-') as d:
            stage=Path(d)/'candidate';self.export(e.project,assets,patches,stage)
            actual=_read_json(stage/'session.scraft');expected=deepcopy(before)
            for o in operations:
                owner=next((t for t in p.tracks if o.target_id==t.id or (t.instrument and o.target_id==t.instrument.id) or any(f.id==o.target_id for f in t.effects)),None)
                if owner is None:raise ValidationError('unknown production parameter owner')
                index=next(i for i,t in enumerate(actual['tracks']) if t['name']==owner.name);old=expected['tracks'][index];new=actual['tracks'][index]
                if o.target_id==owner.id:
                    if o.parameter_id in MIXER or o.parameter_id==SPREAD:
                        key={'mixer.gain_db':'volume_db','mixer.pan':'pan','mixer.mute':'mute',SPREAD:'pan'}[o.parameter_id];old['mixer'][key]=new['mixer'][key]
                    else:
                        slot=next(i for i,s in enumerate(owner.sends) if trim_id(s)==o.parameter_id);old['mixer']['sends'][slot]['level_db']=new['mixer']['sends'][slot]['level_db']
                elif owner.instrument and o.target_id==owner.instrument.id:
                    if owner.id in assets:
                        key=CONTROLS[o.parameter_id][0]
                    elif owner.id in patches:
                        from .external_synth import read_patch
                        key=next(r['native_id'] for r in read_patch(patches[owner.id])[1] if r['canonical_id']==o.parameter_id)
                    else:raise ValidationError('unsupported production instrument edit')
                    old['instrument']['params'][key]=new['instrument']['params'][key]
                else:
                    slot=next(i for i,f in enumerate(owner.effects) if f.id==o.target_id);effect=owner.effects[slot]
                    key,_=self.base._parameter(e.project,effect,effect.plugin_ref.removeprefix('soundcraft:'),o.parameter_id,o.value)
                    if key=='bypass':old['mixer']['inserts'][slot]['bypass']=new['mixer']['inserts'][slot]['bypass']
                    else:old['mixer']['inserts'][slot]['params'][key]=new['mixer']['inserts'][slot]['params'][key]
            if expected!=actual or inventory(source)!=original:raise ValidationError('production edit changed unrelated native/source state')
            (stage/'manifest.json').unlink();write(stage/'receipt.json',asdict(receipt))
            return self._publish(stage,dest,e.project,{'verified':True,'exact_unrelated_native_state':True,'full_native_reopen_equal':True})


def main():
    """Explicit native bundle operations; no default backend migration."""
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('capabilities','inspect','save','render'))
    parser.add_argument('--source');parser.add_argument('--out');parser.add_argument('--soundcraft')
    parser.add_argument('--plugin');parser.add_argument('--workspace',default=str(Path.cwd()))
    args=parser.parse_args();a=ProductionAdapter(args.soundcraft,plugin=args.plugin,workspace=args.workspace)
    if args.action=='capabilities':result=a.capabilities()
    else:
        if not args.source:parser.error('--source required')
        if args.action=='inspect':result=a.inspect(args.source)
        else:
            if not args.out:parser.error('--out required')
            result=getattr(a,args.action)(args.source,args.out)
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__':main()
