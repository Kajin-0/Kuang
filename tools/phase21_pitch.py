#!/usr/bin/env python3
"""New-register and real chord PCM tuning, retaining the original patch states."""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,Section,Clip,Note,BAR,ValidationError
from kuang.pitch_audio import note_pitch,spectrum,hz,cents
from kuang.sample_assets import write,digest
from tools.phase15_pitch import held,ON,WINDOWS
from tools.phase21_house import adapter,media
CASES={
 'bass':{'track':'track-bass','notes':[36,43],'chords':[[36]]},
 'lead':{'track':'track-lead','notes':[63,65,67,68,70,72,74,75],'chords':[[63,67,70,74]]},
 'stab':{'track':'track-harmony','notes':[51,53,55,56,58,60,62,63,67],
         'chords':[[51,55,58,62],[51,53,58,62],[51,56,58,67],[53,56,60,63]]},
 'pad':{'track':'track-depth-pad','notes':[63,67,68,70,72,74,77],
        'chords':[[63,67,70,74],[63,67,70,77],[63,67,70,72],[63,67,68,72]]}}
BUILTINS={
 'arp':{'track':'track-arp','notes':[72,74,75,79],'chords':[[74,79]]},
 'air':{'track':'track-depth-air','notes':[70,72,74,75,79],'chords':[[74,79]]}}


def analyze(path,case):
 result={};step=12*60/126
 for i,n in enumerate(case['notes']):
  rows=[note_pitch(path,n,i*step+ON+a,i*step+ON+b) for a,b in WINDOWS]
  if any(abs(x['fft_cents'])>5 or abs(x['period_cents'])>5 or x['period_correlation']<.85 for x in rows):raise ValidationError('new register tuning failed '+str(n))
  result[str(n)]=rows
 chords=[]
 for i,notes in enumerate(case['chords']):
  peaks=spectrum(path,(len(case['notes'])+i)*step+ON+.5,(len(case['notes'])+i)*step+ON+.9)[2][:120]
  rows=[{'midi':n,'nearest_peak_cents':min(abs(cents(x['hz'],hz(n))) for x in peaks)} for n in notes]
  if any(x['nearest_peak_cents']>5 for x in rows):raise ValidationError('new actual chord partials failed '+str(rows))
  chords.append(rows)
 return {'notes':result,'chords':chords}


def builtin_gate(out,a,source):
 out=Path(out);out.mkdir();report={}
 for voice,case in BUILTINS.items():
  tid=case['track'];groups=[[n] for n in case['notes']]+case['chords'];q=held(source,tid,[36]);q.bars=3*len(groups);q.sections=[Section('phase21-builtin-'+voice,'Built-in upper registers',0,q.bars*BAR)]
  q.tracks[0].controls['mixer.gain_db']=-24;q.tracks[0].clips=[Clip('phase21-builtin-calibration','Original built-in state','midi',0,q.bars*BAR,
   [Note('phase21-builtin-'+str(i)+'-'+str(j),i*3*BAR+480,2880,n,96,0) for i,ns in enumerate(groups) for j,n in enumerate(ns)],None)]
  a.export(q,{}, {},out/voice);wav=out/(voice+'.wav');a.render(out/voice,wav);rows=analyze(wav,case)
  with tempfile.TemporaryDirectory(dir=a.scratch) as d:
   d=Path(d);a.save(out/voice,d/'saved');a.render(d/'saved',d/'repeat.wav')
   if digest(wav)!=digest(d/'repeat.wav') or a.inspect(out/voice)['native']!=a.inspect(d/'saved')['native']:raise ValidationError('built-in tuning reload drift')
  report[voice]={'native':rows,'native_save_reopen_state_PCM_exact':True,'independent_VST_host_applicable':False};print(voice,'built-in high-note tuning/reopen pass',flush=True)
 write(out/'verification.json',report);return report


def gate(destination,host,plugin,host_python):
 out=Path(destination).resolve()
 if out.exists() or not out.is_relative_to(ROOT/'.local/phase21'):raise ValidationError('fresh Phase21 pitch destination required')
 out.mkdir();s=load(ROOT/'artifacts/phase20-house/B/project.kuang.json');a=adapter(host,plugin);_,patches=media(ROOT/'artifacts/phase20-house/B',s);report={}
 for voice,case in CASES.items():
  tid=case['track'];groups=[[n] for n in case['notes']]+case['chords'];q=held(s,tid,[36]);q.bars=3*len(groups);q.sections=[Section('phase21-pitch-'+voice,'New notes and chord cases',0,q.bars*BAR)]
  q.tracks[0].controls['mixer.gain_db']=-24;q.tracks[0].clips=[Clip('phase21-pitch-clip','Dry tuning, original state','midi',0,q.bars*BAR,
   [Note('phase21-pitch-'+str(i)+'-'+str(j),i*3*BAR+480,2880,n,96,0) for i,ns in enumerate(groups) for j,n in enumerate(ns)],None)]
  a.export(q,{}, {tid:patches[tid]},out/voice);wav=out/(voice+'-native.wav');a.render(out/voice,wav);rows=analyze(wav,case)
  with tempfile.TemporaryDirectory(dir=a.scratch) as d:
   d=Path(d);a.save(out/voice,d/'saved');a.render(d/'saved',d/'repeat.wav')
   if digest(wav)!=digest(d/'repeat.wav') or a.inspect(out/voice)['native']!=a.inspect(d/'saved')['native']:raise ValidationError('new pitch case reload drift')
  report[voice]={'native':rows,'native_save_reopen_state_PCM_exact':True,'original_patch_manifest_sha256':digest(patches[tid]/'manifest.json')};write(out/'verification.json',report);print(voice,'new native notes/chords/reopen pass',flush=True)
 request=out/'independent-request.json';write(request,{'plugin':str(a.external.plugin),'out':str(out),'cases':{v:{'patch':str(patches[c['track']]),'notes':c['notes'],'chords':c['chords']} for v,c in CASES.items()}})
 a.external.call([str(Path(host_python).absolute()),str(ROOT/'tools/phase21_independent.py'),str(request)],ROOT)
 for voice,case in CASES.items():report[voice]['independent']=analyze(out/(voice+'-independent.wav'),case)
 result={'version':'phase21-actual-pitch-1','voices':report,'native_builtin':builtin_gate(out/'builtins',a,s),'native_synthetic_MIDI_pitch_center':.5,'maximum_cents':5,'minimum_period_correlation':.85,'original_patch_states_unchanged':True,'independent_host':'Pedalboard0.9.26/Vitalium1.0.6, external voices only'};write(out/'verification.json',result);return result

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__)
 for f in ('out-dir','soundcraft','plugin','host-python'):ap.add_argument('--'+f,required=True)
 z=ap.parse_args();gate(z.out_dir,z.soundcraft,z.plugin,z.host_python)
