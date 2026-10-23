#!/usr/bin/env python3
"""Bounded initialized-instrument probe, including a future user-installed Vital.

No downloads or login. Enumeration/instantiation alone never mean success.
Custom-patch restoration is verified separately by the Vitalium adapter tests.
"""
import argparse
import json
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kuang.audio import analyze_wav
from kuang.external_synth import HOST_SHA,digest,write
from kuang.generator import generate
from kuang.schema import BAR,Clip,Instrument,Note,Section,ValidationError,save
from kuang.soundcraft import SoundCraftAdapter
from tools.phase7_house import local


def gate(destination,executable,paths,instruments):
    out=local(destination)
    if out.exists():raise ValidationError('new plugin-gate directory only')
    a=SoundCraftAdapter(executable)
    if digest(a.executable)!=HOST_SHA:raise ValidationError('exact reviewed SoundCraft required')
    bwrap=shutil.which('bwrap')
    if not bwrap:raise ValidationError('user-installed bubblewrap required')
    paths={k:local(v) for k,v in paths.items()}
    if any(not v.is_dir() for v in paths.values()):raise ValidationError('plugin search directory missing')
    if not instruments or len(instruments)>4 or any(not s.startswith(('vst3:','clap:')) for s in instruments):
        raise ValidationError('one to four explicit external instrument IDs required')
    out.mkdir(parents=True);scratch=ROOT/'.local/phase11';scratch.mkdir(parents=True,exist_ok=True)
    prefix=[bwrap,'--die-with-parent','--ro-bind','/','/','--bind',str(ROOT),str(ROOT),'--unshare-net']
    for k,v in {**paths,'XDG_CONFIG_HOME':scratch/'config','XDG_CACHE_HOME':scratch/'cache',
                'XDG_DATA_HOME':scratch/'data','XDG_DOCUMENTS_DIR':scratch/'documents','TMPDIR':scratch/'tmp'}.items():
        v.mkdir(parents=True,exist_ok=True);prefix+=['--setenv',k,str(v)]
    prefix+=[str(a.executable)]
    def run(args):
        r=subprocess.run(prefix+args,cwd=out,capture_output=True,text=True,timeout=120)
        return {'argv':prefix+args,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    discovery=run(['run','--cmd','engine.vst3_plugins','--cmd','engine.clap_plugins'])
    p=generate();p.bars=2;p.sections=[Section('section-plugin-gate','Gate',0,2*BAR)]
    p.tracks=p.tracks[:1];p.automation=[];p.locks=[];t=p.tracks[0]
    t.instrument=Instrument(t.instrument.id,'plugin','soundcraft:subtractive_synth',None,None,{})
    t.effects=[];t.controls.update({'mixer.gain_db':-18,'mixer.pan':0})
    t.clips=[Clip('clip-plugin-gate','Original initialized-note gate','midi',0,2*BAR,[Note('note-plugin-gate',192,2880,60,90,0)],None)]
    a.export(p,out/'builtin');native=json.loads((out/'builtin/session.scraft').read_text());tid=native['tracks'][0]['id']
    a.render(out/'builtin',out/'builtin.wav',end_seconds=8)
    report={'scope':'initialized patch only; no custom-preset claim','discovery':discovery,
            'soundcraft_sha256':HOST_SHA,'builtin_control':analyze_wav(out/'builtin.wav'),'plugins':{}}
    for index,plugin in enumerate(instruments):
        root=out/('external-'+str(index));first=root/'first';second=root/'reopened';first.mkdir(parents=True);second.mkdir()
        bounce=lambda path:'file.bounce_mix='+json.dumps({'path':str(path),'format':'wav','bit_depth':24,'dither':False,'start':{'seconds':0},'end':{'seconds':8}})
        initial=run(['run','--in',str(out/'builtin/session.scraft'),'--cmd','mix.instrument='+json.dumps({'track':tid,'plugin':plugin}),
                     '--cmd',bounce(first/'audio.wav'),'--save',str(first/'session.scraft')])
        result={'load':initial,'initialized_gate_passed':False}
        if initial['returncode']==0 and (first/'audio.wav').is_file():
            result['audio']=analyze_wav(first/'audio.wav')
            reopened=run(['run','--in',str(first/'session.scraft'),'--cmd',bounce(second/'audio.wav'),'--save',str(second/'session.scraft')])
            result['reopen']=reopened
            if reopened['returncode']==0:
                current=json.loads((first/'session.scraft').read_text());view=deepcopy(current);view['tracks'][0]['instrument']=native['tracks'][0]['instrument']
                result['all_state_outside_instrument_exact']=view==native
                result['full_native_reopen_equal']=current==json.loads((second/'session.scraft').read_text())
                result['pcm_reopen_exact']=digest(first/'audio.wav')==digest(second/'audio.wav')
                m=result['audio'];result['initialized_gate_passed']=bool(m['non_silent'] and m['rms']>1e-6 and not m['clipped_samples'] and result['full_native_reopen_equal'] and result['pcm_reopen_exact'] and result['all_state_outside_instrument_exact'])
            result['legacy_named_control_probe']=run(['run','--in',str(first/'session.scraft'),'--cmd','mix.instrument_param='+json.dumps({'track':tid,'param':'cutoff','value':1000})])
        report['plugins'][plugin]=result
    write(out/'gate.json',report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);p.add_argument('--soundcraft',required=True)
    p.add_argument('--vst3-path');p.add_argument('--clap-path');p.add_argument('--instrument',action='append',required=True)
    args=p.parse_args();paths={k:v for k,v in {'VST3_PATH':args.vst3_path,'CLAP_PATH':args.clap_path}.items() if v}
    if not paths:p.error('at least one explicit project-local plugin search directory required')
    r=gate(args.out_dir,args.soundcraft,paths,args.instrument)
    print(json.dumps({k:v['initialized_gate_passed'] for k,v in r['plugins'].items()},indent=2))
