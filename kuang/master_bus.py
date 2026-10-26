"""Optional single terminal stereo bus, built with native commands only.

Existing one-level production graphs remain strict and unchanged. This adapter
adds just one final summing stage: MIDI -> aux -> terminal -> Main. A terminal
feed is an explicit unity, post-fader canonical Send with direct Main disabled,
mapped to a native direct Bus output. The fixed route is signal-equivalent;
native send panning is deliberately avoided and no editable send trim is invented.
No arbitrary nested routing, detector sidechain or true-peak limiter is implied.
"""
import json
import shutil
import tempfile
from copy import deepcopy
from pathlib import Path

from .schema import Track,Send,ValidationError,load,save,state_hash,validate
from .production_host import ProductionAdapter,graph_contract,add_spread,trim_id
from .sample_assets import inventory,write
from .midi import export as midi_export
from .soundcraft import _read_json

SINK_KEY='terminal_stereo_bus_id'
VERSION='terminal-stereo-native-1'


def terminal_projection(p):
    """Validate the whole bounded graph and return its one-level projection."""
    validate(p);sink=p.metadata.get(SINK_KEY)
    if not isinstance(sink,str) or not sink:raise ValidationError('explicit terminal bus identity required')
    byid={t.id:t for t in p.tracks};master=byid.get(sink)
    if master is None or master is not p.tracks[-1] or master.kind!='bus' or master.sends or not master.output_master:
        raise ValidationError('one last terminal bus must be the sole Main output')
    q=deepcopy(p)
    for old,t in zip(p.tracks,q.tracks):
        if t.id==sink:continue
        if t.output_master:raise ValidationError('direct Main bypasses the terminal bus')
        if len(t.sends)>10:raise ValidationError('terminal routing slot bound exceeded')
        feeds=[(i,s) for i,s in enumerate(t.sends) if s.target_track_id==sink]
        if len(feeds)>1:raise ValidationError('duplicate terminal feed')
        if t.kind=='bus' and (len(t.sends)!=1 or not feeds):raise ValidationError('aux may feed only the terminal bus')
        if feeds:
            i,s=feeds[0]
            if (i!=len(t.sends)-1 or s.gain_db!=0 or s.pan!=0 or s.mode!='post_fader' or
                trim_id(s) in t.controls or any(a.target_id==t.id and a.parameter_id==trim_id(s) for a in p.automation)):
                raise ValidationError('terminal feed must be last, fixed unity, post-fader, follow-pan')
            t.sends.pop();t.output_master=True
        if not old.sends:raise ValidationError('disconnected nonterminal strip')
    graph_contract(q)  # Retains every earlier fail-closed units/slot/graph rule.
    return q


def attach_terminal(source,effects=(),*,identity='production-terminal-master'):
    graph_contract(source)
    if source.locks or SINK_KEY in source.metadata:raise ValidationError('unlocked one-level source without a terminal bus required')
    p=deepcopy(source)
    for t in p.tracks:
        if t.output_master:
            t.sends.append(Send('terminal-feed-'+t.id,identity,0,0,'post_fader'));t.output_master=False
    master=Track(identity,'Stereo terminal master','bus',None,
        {'mixer.gain_db':0,'mixer.pan':0,'mixer.mute':0},deepcopy(list(effects)),[],[],True)
    p.tracks.append(master);add_spread(p,master,1)
    p.metadata[SINK_KEY]=identity
    terminal_projection(p)
    return p


class MasterBusAdapter(ProductionAdapter):
    """New opt-in bundle contract; legacy ProductionAdapter is not loosened."""
    def __init__(self,*args,**kwargs):
        self.inner=ProductionAdapter(*args,**kwargs)
        for name in ('workspace','scratch','samples','external','base'):setattr(self,name,getattr(self.inner,name))

    def capabilities(self):
        return {**self.inner.capabilities(),'version':VERSION,'terminal_stereo_bus':True,
            'routing':'MIDI to one-level aux returns and/or one last terminal stereo bus; canonical fixed-unity feeds map to native direct Bus outputs',
            'arbitrary_nested_buses':False,'true_peak_limiter_claimed':False}

    def _verify(self,p,native,assets,patches,root):
        q=terminal_projection(p);sink=p.metadata[SINK_KEY]
        buses=[t for t in p.tracks if t.kind=='bus'];busids={t.id:b['id'] for t,b in zip(buses,native['busses'])}
        if sink not in busids:raise ValidationError('missing native terminal bus')
        view=deepcopy(native);ordered=[t for t in p.tracks if t.kind=='midi']+buses
        if len(view['tracks'])!=len(ordered):raise ValidationError('terminal strip count drift')
        for t,h,v in zip(ordered,native['tracks'],view['tracks']):
            if t.id==sink:continue
            feeds=[(i,s) for i,s in enumerate(t.sends) if s.target_track_id==sink]
            if feeds:
                i,_=feeds[0]
                if h['mixer']['output']!={'Bus':busids[sink]} or h['mixer']['sends'][i] is not None:raise ValidationError('native terminal output route drift')
                v['mixer']['output']='Main'
            elif h['mixer']['output']!='None':raise ValidationError('native direct Main leakage')
        return self.inner._verify(q,view,assets,patches,root)

    def _publish(self,stage,dest,p,report):
        assets={t.id:stage/'assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
        patches={t.id:stage/'patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')}
        identities=self._verify(p,_read_json(stage/'session.scraft'),assets,patches,stage)
        for name in ('manifest.json','project.kuang.json','song.mid','report.json'):
            if (stage/name).exists():(stage/name).unlink()
        save(p,stage/'project.kuang.json');midi_export(p,stage/'song.mid');write(stage/'report.json',report)
        write(stage/'manifest.json',{'version':VERSION,'canonical_hash':state_hash(p),'capabilities':self.capabilities(),'identities':identities,'files':inventory(stage)})
        dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
        try:
            for f in stage.iterdir():shutil.move(str(f),dest/f.name)
        except BaseException:shutil.rmtree(dest);raise
        return report

    def _load(self,source):
        source=self.local(source);m=_read_json(source/'manifest.json')
        if set(m)!={'version','canonical_hash','capabilities','identities','files'} or m['version']!=VERSION or m['capabilities']!=self.capabilities():raise ValidationError('terminal bundle contract drift')
        actual=inventory(source);actual.pop('manifest.json',None)
        if actual!=m['files']:raise ValidationError('terminal bundle/file drift')
        p=load(source/'project.kuang.json');native=_read_json(source/'session.scraft')
        assets={t.id:source/'assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
        patches={t.id:source/'patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')}
        if state_hash(p)!=m['canonical_hash'] or self._verify(p,native,assets,patches,source)!=m['identities']:raise ValidationError('terminal canonical/native identity drift')
        return source,p,native,assets,patches

    def export(self,p,assets,patches,destination):
        q=terminal_projection(p);self.capabilities();dest=self.new(destination)
        assets={k:self.local(v) for k,v in assets.items()};patches={k:self.local(v) for k,v in patches.items()}
        if any(dest.is_relative_to(v) for v in [*assets.values(),*patches.values()]):raise ValidationError('terminal output intersects assets')
        protected={str(v):inventory(v) for v in [*assets.values(),*patches.values()]}
        with tempfile.TemporaryDirectory(dir=self.scratch,prefix='terminal-') as d:
            work=Path(d);stage=work/'publish';self.inner.export(q,assets,patches,stage)
            before=_read_json(stage/'session.scraft');expected=deepcopy(before);sink=p.metadata[SINK_KEY]
            bus=next(b['id'] for t,b in zip([t for t in p.tracks if t.kind=='bus'],before['busses']) if t.id==sink)
            ordered=[t for t in p.tracks if t.kind=='midi']+[t for t in p.tracks if t.kind=='bus'];commands=[]
            name=next(t.name for t in p.tracks if t.id==sink)
            for t,h in zip(ordered,expected['tracks']):
                feeds=[(i,s) for i,s in enumerate(t.sends) if s.target_track_id==sink]
                if not feeds:continue
                commands.append(('track.output',{'track':t.name,'output':name}))
                h['mixer']['output']={'Bus':bus}
            self._script(commands,stage/'session.scraft',work)
            actual=_read_json(stage/'session.scraft')
            if actual!=expected:raise ValidationError('terminal routing changed unrelated native state')
            self._verify(p,actual,{k:stage/'assets'/k for k in assets},{k:stage/'patches'/k for k in patches},stage)
            reopened=work/'reopened';shutil.copytree(stage,reopened);self.base._run([],work,source=stage/'session.scraft',destination=reopened/'session.scraft')
            if _read_json(reopened/'session.scraft')!=actual or any(inventory(Path(k))!=v for k,v in protected.items()):raise ValidationError('terminal reopen or source drift')
            return self._publish(stage,dest,p,{'verified':True,'native_terminal_bus':True,'full_native_reopen_equal':True})


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('capabilities','inspect','save','render'));ap.add_argument('--source');ap.add_argument('--out');ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--workspace',default=str(Path.cwd()))
    z=ap.parse_args();a=MasterBusAdapter(z.soundcraft,plugin=z.plugin,workspace=z.workspace,center_pitch_bend=True)
    result=a.capabilities() if z.action=='capabilities' else a.inspect(z.source) if z.action=='inspect' else a.save(z.source,z.out) if z.action=='save' else a.render(z.source,z.out)
    print(json.dumps(result,indent=2))
