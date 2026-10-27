#!/usr/bin/env python3
"""Bounded dry/stem controls and tuning for ONE authored chord-bed candidate."""
import argparse,json,math,sys,tempfile,wave
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.chord_bed import PROTECTED,UPPER
from kuang.schema import load,ValidationError,Section,Clip,Note,BAR
from kuang.external_synth import bound_project
from kuang.production_host import ProductionAdapter
from kuang.sample_assets import digest,write
from kuang.audio import compare_wavs
from kuang.production_audio import _decode
from kuang.lowend_audio import band_metrics
from kuang.loudness import measure
from tools.phase22_shortlist import stem
from tools.phase23_groove import adapter,media,END
from tools.phase15_pitch import held
from tools.phase21_pitch import analyze

def normalized_delta(a,b,gain_db):
    gain=10**(gain_db/20);squares=reference=0;count=0
    with wave.open(str(a),'rb') as x,wave.open(str(b),'rb') as y:
        if x.getparams()!=y.getparams():raise ValidationError('same-input controls must align')
        while data:=x.readframes(8192):
            for u,v in zip(_decode(data,3,2),_decode(y.readframes(8192),3,2)):
                for left,right in zip(u,v):squares+=(right*gain-left)**2;reference+=left*left;count+=1
    return {'difference_to_source_RMS':math.sqrt(squares/reference),'constant_analysis_gain_db':gain_db,'samples':count,'processing':'Analysis only; no new listening/mix WAV generated'}

def controls(root,host,plugin,meter=None):
    root=Path(root);a=adapter(host,plugin);s=load(root/'reference.kuang.json');p=load(root/'project/project.kuang.json');assets,patches=media(root/'project',p)
    original=ROOT/'artifacts/phase22-house/A/native/patches';results={};sources={}
    with tempfile.TemporaryDirectory(dir=a.scratch,prefix='bed-controls-') as d:
        d=Path(d)
        def render(name,q,pp):
            a.export(q,{t.id:assets[t.id] for t in q.tracks if t.id in assets},{t.id:pp[t.id] for t in q.tracks if t.id in pp},d/name);wav=d/(name+'.wav');a.render(d/name,wav,end_seconds=END);return wav
        for name,q in [('reference',s),('candidate',p)]:
            q=stem(q,PROTECTED);sources[name]=render('pocket-'+name,q,patches)
        if digest(sources['reference'])!=digest(sources['candidate']):raise ValidationError('approved complete rhythm PCM changed')
        # Same NEW chord performance and same new inserts, swapping only the
        # two original-vs-new source states. No alternative authored palette.
        for tid in sorted(UPPER):
            q=stem(p,{tid});old=deepcopy(q);next(t for t in old.tracks if t.id==tid).instrument=deepcopy(next(t for t in s.tracks if t.id==tid).instrument)
            oldpath=render('old-source-'+tid,old,{tid:original/tid});newpath=render('new-source-'+tid,q,patches)
            levels={'old':measure(oldpath,library=meter),'new':measure(newpath,library=meter)}
            gain=levels['old']['integrated_lufs']-levels['new']['integrated_lufs'];delta=normalized_delta(oldpath,newpath,gain)
            if delta['difference_to_source_RMS']<.10:raise ValidationError('source change is only a label or gain')
            bands={k:band_metrics(path,first=.5,last=30,windows=12) for k,path in [('old',oldpath),('new',newpath)]}
            results[tid]={'equal_LUFS_source_difference':delta,'levels':levels,'bands':bands,'old_sha256':digest(oldpath),'new_sha256':digest(newpath)}
        pad=stem(p,{'track-depth-pad'});static=deepcopy(pad)
        lane=next(x for x in static.automation if x.target_id=='effect-depth-pad-eq' and x.parameter_id=='soundcraft.lpf_freq')
        for point in lane.points:point.value=1300
        on=render('pad-evolving-filter',pad,patches);off=render('pad-static-filter',static,patches);motion=compare_wavs(off,on)
        if motion['difference_to_original_rms_ratio']<.01:raise ValidationError('native slow filter expression is inert')
        report={'version':'phase23-source-and-pocket-1','rhythm_section_PCM_exact':True,'rhythm_reference_sha256':digest(sources['reference']),'rhythm_candidate_sha256':digest(sources['candidate']),
          'same_input_source_timbres':results,'native_slow_filter_on_off':motion,'listening_mix_variants_created':0,
          'scope':'Private rhythm/harmonic stems only, same MIDI/input and actual source-state swaps. Gain-normalized analysis is not an artistic quality score. No new full mix/baseline render.'}
    write(root/'sound-proof.json',report);return report

CASES={'stab':{'track':'track-harmony','notes':[51,53,56,58,62,63,67],'chords':[[51,58,62],[53,58,63],[51,56,58]]},
       'pad':{'track':'track-depth-pad','notes':[63,67,72,74,77],'chords':[[63,67,74],[63,67,77],[63,67,72]]},
       'bass':{'track':'track-bass','notes':[36],'chords':[[36]]}}

def pitch(root,out,host,plugin,host_python):
    root=Path(root);out=Path(out).resolve()
    if out.exists() or not out.is_relative_to(ROOT/'.local/phase23'):raise ValidationError('new Phase23 tuning scratch required')
    out.mkdir();p=load(root/'project/project.kuang.json');full=load(ROOT/'artifacts/phase21-house/B/project.kuang.json');_,patches=media(root/'project',p)
    a=ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase23/tmp',center_pitch_bend=True);report={}
    for voice,case in CASES.items():
        tid=case['track'];q=held(full,tid,[36]);q.tracks[0].instrument=deepcopy(next(t.instrument for t in p.tracks if t.id==tid));q.parameters=deepcopy(p.parameters)
        groups=[[n] for n in case['notes']]+case['chords'];q.bars=3*len(groups);q.sections=[Section('phase23-pitch-'+voice,'Actual source tuning and chords',0,q.bars*BAR)]
        q.tracks[0].controls['mixer.gain_db']=-24;q.tracks[0].clips=[Clip('phase23-pitch-clip','Dry source calibration','midi',0,q.bars*BAR,
            [Note('phase23-pitch-'+str(i)+'-'+str(j),i*3*BAR+480,2880,n,96,0) for i,notes in enumerate(groups) for j,n in enumerate(notes)],None)]
        a.export(q,{}, {tid:patches[tid]},out/voice);wav=out/(voice+'-native.wav');a.render(out/voice,wav);rows=analyze(wav,case)
        a.save(out/voice,out/(voice+'-saved'));a.render(out/(voice+'-saved'),out/(voice+'-repeat.wav'))
        if digest(wav)!=digest(out/(voice+'-repeat.wav')):raise ValidationError('pitch state/PCM reload changed')
        report[voice]={'native':rows,'native_PCM_reopen_exact':True};print(voice,'actual native pitch/chords pass',flush=True)
    request=out/'request.json';write(request,{'plugin':str(a.external.plugin),'out':str(out),'cases':{v:{'patch':str(patches[c['track']]),'notes':c['notes'],'chords':c['chords']} for v,c in CASES.items()}})
    a.external.call([str(Path(host_python).absolute()),str(ROOT/'tools/phase21_independent.py'),str(request)],ROOT)
    for voice,case in CASES.items():report[voice]['independent']=analyze(out/(voice+'-independent.wav'),case)
    result={'version':'phase23-actual-tuning-1','voices':report,'native_pitch_center':.5,'limit_cents':5,'scope':'Two new harmonic voices plus unchanged C2 bass in actual native and independent hosts; no preference inference'}
    write(out/'verification.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('controls','pitch'));ap.add_argument('--root',required=True);ap.add_argument('--out');ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);ap.add_argument('--host-python');ap.add_argument('--meter-library');z=ap.parse_args()
    result=controls(z.root,z.soundcraft,z.plugin,z.meter_library) if z.action=='controls' else pitch(z.root,z.out,z.soundcraft,z.plugin,z.host_python)
    if z.action=='pitch':write(Path(z.root)/'pitch-proof.json',result)
    print(json.dumps(result,indent=2))
