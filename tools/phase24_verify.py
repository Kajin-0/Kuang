#!/usr/bin/env python3
"""Private causal controls and new-register tuning for the ONE full record."""
import argparse,json,sys,tempfile,wave
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,Section,Clip,Note,BAR,ValidationError
from kuang.sample_assets import digest,write
from kuang.audio import compare_wavs
from kuang.lowend_audio import band_metrics
from kuang.production_host import ProductionAdapter
from kuang.gestures import crop
from tools.phase22_shortlist import stem
from tools.phase24_house import adapter,media
from tools.phase15_pitch import held
from tools.phase21_pitch import analyze

CASES={'stab':{'track':'track-harmony','notes':[51,53,55,56,58,62,63,67],
 'chords':[[51,58,62],[53,58,63],[51,56,58],[55,58,62],[56,58,63],[53,58,67]]},
 'pad':{'track':'track-depth-pad','notes':[58,63,67,70,72,74,77],
 'chords':[[63,67,74],[63,67,77],[63,67,72],[63,67,70],[58,63,74],[58,63,77],[58,63,67]]},
 'bass':{'track':'track-bass','notes':[36],'chords':[[36]]}}

def pitch(root,out,host,plugin,host_python):
 root=Path(root);out=Path(out).resolve()
 if out.exists() or not out.is_relative_to(ROOT/'.local/phase24'):raise ValidationError('new Phase24 pitch scratch required')
 out.mkdir();p=load(root/'project/project.kuang.json');_,patches=media(root/'project',p)
 a=ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase24/tmp',center_pitch_bend=True);result={}
 for voice,case in CASES.items():
  tid=case['track'];groups=[[n] for n in case['notes']]+case['chords'];q=held(p,tid,[36]);q.bars=3*len(groups);q.sections=[Section('phase24-pitch-'+voice,'Actual held source registers and chords',0,q.bars*BAR)]
  q.tracks[0].controls['mixer.gain_db']=-24;q.tracks[0].clips=[Clip('phase24-pitch-clip','Dry source calibration','midi',0,q.bars*BAR,
   [Note('phase24-pitch-'+str(i)+'-'+str(j),i*3*BAR+480,2880,n,96,0) for i,notes in enumerate(groups) for j,n in enumerate(notes)],None)]
  a.export(q,{}, {tid:patches[tid]},out/voice);wav=out/(voice+'-native.wav');a.render(out/voice,wav);rows=analyze(wav,case)
  a.save(out/voice,out/(voice+'-saved'));a.render(out/(voice+'-saved'),out/(voice+'-repeat.wav'))
  if digest(wav)!=digest(out/(voice+'-repeat.wav')) or a.inspect(out/voice)['native']!=a.inspect(out/(voice+'-saved'))['native']:raise ValidationError('held source tuning reload changed')
  result[voice]={'native':rows,'native_state_PCM_reopen_exact':True};print(voice,'actual pitch/chords pass',flush=True)
 request=out/'request.json';write(request,{'plugin':str(a.external.plugin),'out':str(out),'cases':{v:{'patch':str(patches[c['track']]),'notes':c['notes'],'chords':c['chords']} for v,c in CASES.items()}})
 a.external.call([str(Path(host_python).absolute()),str(ROOT/'tools/phase21_independent.py'),str(request)],ROOT)
 for voice,case in CASES.items():result[voice]['independent']=analyze(out/(voice+'-independent.wav'),case)
 r={'version':'phase24-actual-tuning-1','native_pitch_center':.5,'limit_cents':5,'voices':result,'scope':'All performed new upper registers and explicit new chords plus unchanged C2; original patch states, no preference inference'}
 write(out/'verification.json',r);return r

def controls(root,host,plugin):
 root=Path(root);p=load(root/'project/project.kuang.json');assets,patches=media(root/'project',p);a=adapter(host,plugin)
 q=crop(p,72,16,[t.id for t in p.tracks]);q=stem(q,{'track-harmony','track-depth-pad'});end=16*4*60/126+5
 with tempfile.TemporaryDirectory(dir=a.scratch,prefix='record-controls-') as d:
  d=Path(d)
  def render(name,score):
   a.export(score,{t.id:assets[t.id] for t in score.tracks if t.id in assets},{t.id:patches[t.id] for t in score.tracks if t.id in patches},d/name);wav=d/(name+'.wav');a.render(d/name,wav,end_seconds=end);return wav
  active=render('performance',q);reports={}
  for mode in ('lowpass','highpass','plate','echo'):
   off=deepcopy(q)
   if mode=='lowpass':
    for lane in off.automation:
     if lane.parameter_id=='soundcraft.lpf_freq' and lane.target_id in ('effect-harmony-eq','effect-depth-pad-eq'):
      for x in lane.points:x.value=1300
   elif mode=='highpass':
    for lane in off.automation:
     if lane.parameter_id=='soundcraft.hpf_freq' and lane.target_id=='effect-harmony-eq':
      for x in lane.points:x.value=100
   elif mode=='plate':next(t for t in off.tracks if t.id=='phase17-dark-space').controls['mixer.mute']=1
   else:
    for lane in off.automation:
     if lane.target_id=='track-harmony' and lane.parameter_id.startswith('route.'):
      for x in lane.points:x.value=-60
   baseline=render(mode+'-off',off);difference=compare_wavs(baseline,active)
   if difference['difference_to_original_rms_ratio']<.001:raise ValidationError('inert native performance control '+mode)
   reports[mode]={'aligned_PCM_difference':difference,'same_input_notes_exact':[[n for c in t.clips for n in c.notes] for t in q.tracks]==[[n for c in t.clips for n in c.notes] for t in off.tracks]}
   if mode in ('lowpass','highpass'):
    reports[mode]['localized_bands']={label:{name:band_metrics(path,first=first*4*60/126,last=last*4*60/126,windows=4) for name,path in [('on',active),('off',baseline)]} for label,first,last in [('anticipation',6,8),('arrival',8,12)]}
   if mode=='echo':
    frames=round(6*4*60/126*48000)
    with wave.open(str(active),'rb') as x,wave.open(str(baseline),'rb') as y:equal=x.readframes(frames)==y.readframes(frames)
    if not equal:raise ValidationError('throw difference leaks into the closed six-bar prefix')
    reports[mode]['closed_six_bar_prefix_PCM_exact']=True;reports[mode]['closed_floor_db']=-60
  return {'version':'phase24-causal-performance-1','window_zero_bars':[72,88],'DSP_reset_window':True,'controls':reports,
   'scope':'Private same-MIDI source/return controls only; closed send floor is -60dB, not mathematical mute. No new authored/listening/full-song variants, no perceptual score.'}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('pitch','controls'));ap.add_argument('--root',required=True);ap.add_argument('--out');ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);ap.add_argument('--host-python');z=ap.parse_args()
 r=pitch(z.root,z.out,z.soundcraft,z.plugin,z.host_python) if z.action=='pitch' else controls(z.root,z.soundcraft,z.plugin)
 write(Path(z.root)/('pitch-proof.json' if z.action=='pitch' else 'performance-proof.json'),r);print(json.dumps(r,indent=2))
