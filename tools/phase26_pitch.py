#!/usr/bin/env python3
"""Actual source calibration, timbral motion, rhythm and optional bus proof."""
import argparse,json,sys,tempfile,wave
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,Section,Clip,Note,Effect,BAR,ValidationError
from kuang.sample_assets import digest,write
from kuang.audio import compare_wavs
from kuang.loudness import measure
from kuang.chord_bed import PROTECTED
from kuang.gesture_audio import phase_gain
from kuang.mix_diagnostics import linked_gain_audit,envelope_gain_audit
from tools.phase23_verify import normalized_delta
from kuang.lowend_audio import band_metrics
from kuang.production_host import ProductionAdapter
from kuang.gestures import crop
from tools.phase22_shortlist import stem
from tools.phase26_house import adapter,media
from tools.phase15_pitch import held
from tools.phase21_pitch import analyze

CASES={'stab':{'track':'track-harmony','notes':[55,56,59,60,63,65],'chords':[[55,60,63],[56,60,65],[55,60,65],[55,59,65]]},
'pad':{'track':'track-depth-pad','notes':[58,60,62,63,67,68],'chords':[[58,62,67],[60,63,68],[62,67]]},
'bass':{'track':'track-bass','notes':[36,38,39,41,43,44,47,48],'chords':[[36],[41],[43]]}}

def pitch(root,out,host,plugin,host_python):
 root=Path(root);out=Path(out).resolve()
 if out.exists() or not out.is_relative_to(ROOT/'.local/phase26'):raise ValidationError('new Phase25 pitch scratch required')
 out.mkdir();p=load(root/'project/project.kuang.json');_,patches=media(root/'project',p)
 a=ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase26/tmp',center_pitch_bend=True);result={}
 for voice,case in CASES.items():
  tid=case['track'];groups=[[n] for n in case['notes']]+case['chords'];q=held(p,tid,[36]);q.bars=3*len(groups);q.sections=[Section('phase26-pitch-'+voice,'Actual held source registers and chords',0,q.bars*BAR)]
  q.tracks[0].controls['mixer.gain_db']=-24;q.tracks[0].clips=[Clip('phase26-pitch-clip','Dry source calibration','midi',0,q.bars*BAR,
   [Note('phase26-pitch-'+str(i)+'-'+str(j),i*3*BAR+480,2880,n,96,0) for i,notes in enumerate(groups) for j,n in enumerate(notes)],None)]
  a.export(q,{}, {tid:patches[tid]},out/voice);wav=out/(voice+'-native.wav');a.render(out/voice,wav);rows=analyze(wav,case)
  a.save(out/voice,out/(voice+'-saved'));a.render(out/(voice+'-saved'),out/(voice+'-repeat.wav'))
  if digest(wav)!=digest(out/(voice+'-repeat.wav')) or a.inspect(out/voice)['native']!=a.inspect(out/(voice+'-saved'))['native']:raise ValidationError('held source tuning reload changed')
  result[voice]={'native':rows,'native_state_PCM_reopen_exact':True};print(voice,'actual pitch/chords pass',flush=True)
 request=out/'request.json';write(request,{'plugin':str(a.external.plugin),'out':str(out),'cases':{v:{'patch':str(patches[c['track']]),'notes':c['notes'],'chords':c['chords']} for v,c in CASES.items()}})
 a.external.call([str(Path(host_python).absolute()),str(ROOT/'tools/phase21_independent.py'),str(request)],ROOT)
 for voice,case in CASES.items():result[voice]['independent']=analyze(out/(voice+'-independent.wav'),case)
 r={'version':'phase26-actual-tuning-1','native_pitch_center':.5,'limit_cents':5,'voices':result,'scope':'All performed new upper registers and explicit new chords plus unchanged C2; original patch states, no preference inference'}
 write(out/'verification.json',r);return r
