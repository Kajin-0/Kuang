#!/usr/bin/env python3
"""Actual new registers/chords in SoundCraft and the separate reviewed host."""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,Section,Clip,Note,BAR,ValidationError
from kuang.production_host import ProductionAdapter
from kuang.sample_assets import write,digest
from tools.phase15_pitch import held
from tools.phase21_pitch import analyze
from tools.phase22_shortlist import media
CASES={
 'bass':{'track':'track-bass','notes':[29,31,32,34,36,38,39,41,43,44],'chords':[[36]]},
 'lead':{'track':'track-lead','notes':[60,62,63,65,67,68,70,72,74,75,77,79],'chords':[[63,67,70,74]]},
 'stab':{'track':'track-harmony','notes':[51,53,55,56,58,60,62,63],
         'chords':[[51,58,62],[56,60,63],[55,58,60],[55,58,62],[53,58]]},
 'pad':{'track':'track-depth-pad','notes':[63,65,67,68,72,74,77],
        'chords':[[63,67,74],[63,67,72],[63,65,72],[63,65,77],[63,68,72]]}}
BUILTINS={'arp':{'track':'track-arp','notes':[72,74,75,77,79],'chords':[[77,79]]},
          'air':{'track':'track-depth-air','notes':[77,79],'chords':[[77,79]]}}

def calibration(source,case,name):
 groups=[[n] for n in case['notes']]+case['chords'];q=held(source,case['track'],[36]);q.bars=3*len(groups);q.sections=[Section('phase22-pitch-'+name,'Original patch new register/chords',0,q.bars*BAR)]
 q.tracks[0].controls['mixer.gain_db']=-24;q.tracks[0].clips=[Clip('phase22-pitch-clip','Original state, dry held-note calibration','midi',0,q.bars*BAR,
  [Note('phase22-pitch-'+str(i)+'-'+str(j),i*3*BAR+480,2880,n,96,0) for i,ns in enumerate(groups) for j,n in enumerate(ns)],None)]
 return q

def gate(out,host,plugin,host_python):
 out=Path(out).resolve()
 if out.exists() or not out.is_relative_to(ROOT/'.local/phase22'):raise ValidationError('fresh Phase22 pitch gate required')
 out.mkdir();s=load(ROOT/'artifacts/phase21-house/B/project.kuang.json');_,patches=media(ROOT/'artifacts/phase21-house/B',s)
 a=ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase22/tmp',center_pitch_bend=True);report={};builtins={}
 for voice,case in {**CASES,**BUILTINS}.items():
  q=calibration(s,case,voice);pp={case['track']:patches[case['track']]} if voice in CASES else {};a.export(q,{},pp,out/voice);wav=out/(voice+'-native.wav');a.render(out/voice,wav)
  rows=analyze(wav,case)
  with tempfile.TemporaryDirectory(dir=a.scratch) as d:
   d=Path(d);a.save(out/voice,d/'saved');a.render(d/'saved',d/'repeat.wav')
   if digest(wav)!=digest(d/'repeat.wav') or a.inspect(out/voice)['native']!=a.inspect(d/'saved')['native']:raise ValidationError('pitch restore drift '+voice)
  item={'native':rows,'native_state_PCM_reopen_exact':True}
  if voice in CASES:report[voice]=item
  else:builtins[voice]=item
  print(voice,'native new register/chord gate pass',flush=True)
 request=out/'request.json';write(request,{'plugin':str(a.external.plugin),'out':str(out),'cases':{v:{'patch':str(patches[c['track']]),'notes':c['notes'],'chords':c['chords']} for v,c in CASES.items()}})
 a.external.call([str(Path(host_python).absolute()),str(ROOT/'tools/phase21_independent.py'),str(request)],ROOT)
 for voice,case in CASES.items():report[voice]['independent']=analyze(out/(voice+'-independent.wav'),case)
 result={'version':'phase22-played-pitch-1','voices':report,'builtins':builtins,'native_pitch_center':.5,'threshold_cents':5,'original_patch_states_unchanged':True,'scope':'Four external roles in two actual hosts, builtins native; no musical preference inference'}
 write(out/'verification.json',result);return result

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__)
 for arg in ('out','soundcraft','plugin','host-python'):ap.add_argument('--'+arg,required=True)
 z=ap.parse_args();gate(z.out,z.soundcraft,z.plugin,z.host_python)
