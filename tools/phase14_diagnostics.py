#!/usr/bin/env python3
"""Internal same-input native controls and full-song causal stems, no score."""
import argparse
import json
import math
import sys
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.ensemble_production import isolate,DRUMS,VOICES
from kuang.production_host import ProductionAdapter
from kuang.producer import _subset
from kuang.schema import load,ValidationError
from kuang.sample_assets import write
from kuang.audio import analyze_wav,compare_wavs
from kuang.lowend_audio import band_metrics
from kuang.groove_audio import stem_sum_error,low_end_interaction
from tools.phase13_house import window_rms
from tools.phase14_house import END


def diagnostics(release,output,executable,plugin):
    root=Path(release).resolve();out=Path(output).resolve()
    if out.exists() or not out.is_relative_to(ROOT/'.local/phase14'):raise ValidationError('new internal Phase14 diagnostics required')
    out.mkdir();a=ProductionAdapter(executable,plugin=plugin,workspace=ROOT);p=load(root/'B/project.kuang.json');original=load(root/'A/project.kuang.json')
    groups={'drums':DRUMS,'bass':{'track-bass'},'stabs':{'track-harmony'},'lead':{'track-lead'},'pad':{'track-depth-pad'},
            'other':{t.id for t in p.tracks if t.kind=='midi'}-DRUMS-set(VOICES)}
    def render(name,q):
        assets={t.id:root/'B/native/assets'/t.id for t in q.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'}
        patches={t.id:root/'B/native/patches'/t.id for t in q.tracks if t.id in VOICES}
        a.export(q,assets,patches,out/(name+'-native'));a.render(out/(name+'-native'),out/(name+'.wav'),end_seconds=END)
        print('Native diagnostic',name,flush=True)
    controls={}
    for name in ('no-shared-space','no-drum-glue','static-stab-filter'):
        q=deepcopy(p)
        if name=='no-shared-space':
            for t in q.tracks:
                if t.id in ('phase14-short-room','phase14-dark-space','phase14-echo'):t.controls['mixer.mute']=1
        elif name=='no-drum-glue':next(t for t in q.tracks if t.id=='phase14-drum-sum').effects[0].parameters['effect.bypass']=1
        else:
            q.automation=[x for x in q.automation if not (x.target_id=='effect-harmony-eq' and x.parameter_id=='soundcraft.lpf_freq')]
            next(t for t in q.tracks if t.id=='track-harmony').effects[0].parameters['soundcraft.lpf_freq']=3400
        render(name,q);controls[name]=compare_wavs(root/'B-Phase14-ensemble-native.wav',out/(name+'.wav'))
    stems={};paths=[]
    for name,ids in groups.items():
        render(name,isolate(p,ids));path=out/(name+'.wav');paths.append(path)
        stems[name]={'drop_rms_dbfs':window_rms(path),'audio':analyze_wav(path),
            'drop_bands':band_metrics(path,first=32*4*60/126,last=40*4*60/126,windows=8)}
    # Separate summed-drum input, same MIDI/samples/faders, compressor bypass.
    q=isolate(p,DRUMS);next(t for t in q.tracks if t.id=='phase14-drum-sum').effects[0].parameters['effect.bypass']=1
    render('drums-bypass',q)
    # Actual kick plus bass stems for timing/mono interference. New shared room
    # has no kick or bass send; compressor sees only the isolated kick here.
    render('kick',isolate(p,{'track-kick'}))
    old={}
    legacy=a.samples
    for name,ids in [('bass',{'track-bass'}),('stabs',{'track-harmony'}),('lead',{'track-lead'}),('pad',{'track-depth-pad'})]:
        q=_subset(original,ids);legacy.base.export(q,out/('A-'+name+'-native'));legacy.base.render(out/('A-'+name+'-native'),out/('A-'+name+'.wav'),end_seconds=END)
        old[name]={'drop_rms_dbfs':window_rms(out/('A-'+name+'.wav')),'drop_bands':band_metrics(out/('A-'+name+'.wav'),first=32*4*60/126,last=40*4*60/126,windows=8)}
    summation=stem_sum_error(root/'B-Phase14-ensemble-native.wav',paths)
    onsets=[(c.start+n.start)/p.ppq*60/p.tempo_bpm for t in p.tracks if t.id=='track-kick' for c in t.clips for n in c.notes if 32*3840<=c.start+n.start<40*3840]
    envelope=[]
    for begin,end in ((0,.02),(.02,.10),(.10,.20)):
        powers=[]
        for name in ('drums-bypass','drums'):
            powers.append(sum(10**(window_rms(out/(name+'.wav'),t+begin,t+end)/10) for t in onsets)/len(onsets))
        envelope.append({'after_kick_ms':[begin*1000,end*1000],'bypass_mean_square':powers[0],'enabled_mean_square':powers[1],
                         'gain_db':10*math.log10(powers[1]/powers[0])})
    report={'version':'phase14-native-diagnostics-1','same_input_effect_controls':controls,'full_song_stems':stems,
        'old_roles':old,'independent_reconstruction':summation,'drum_compressor_envelope':envelope,
        'kick_bass_interaction':low_end_interaction(out/'kick.wav',out/'bass.wav'),
        'human_listened':False,'perceived_quality_proven':False}
    if any(not x['measurable_change'] for x in controls.values()) or summation['peak_error_lsb']>32:
        raise ValidationError('native control or stem reconstruction failure')
    write(out/'verification.json',report);return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--release',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);a=ap.parse_args()
    print(json.dumps(diagnostics(a.release,a.out,a.soundcraft,a.plugin),indent=2))
