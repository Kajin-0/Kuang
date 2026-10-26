#!/usr/bin/env python3
"""Fresh PCM pitch and pulse-continuity gates for the editorial arrangement."""
import argparse,json,sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,ValidationError
from kuang.ensemble_production import isolate
from kuang.pitch_audio import note_pitch,spectrum,hz,cents
from kuang.production_audio import _decode
from kuang.sample_assets import digest,write
from tools.phase15_pitch import held,ON,WINDOWS
from tools.phase19_house import adapter,media,END,AUDIO


def pitch_gate(root,out,host,plugin):
 root=Path(root);out=Path(out);out.mkdir();a=adapter(host,plugin);p=load(root/'B/project.kuang.json');_,patches=media(root/'B',p)
 rows={}
 for tid,n in [('track-lead',67),('track-lead',63),('track-lead',65),('track-bass',36)]:
  q=held(p,tid,[n]);name=tid+'-'+str(n);a.export(q,{}, {tid:patches[tid]},out/name);wav=out/(name+'.wav');a.render(out/name,wav)
  measured=[note_pitch(wav,n,ON+lo,ON+hi) for lo,hi in WINDOWS]
  if any(abs(x['fft_cents'])>5 or abs(x['period_cents'])>5 or x['period_correlation']<.85 for x in measured):raise ValidationError('editorial pitch gate failed')
  a.save(out/name,out/(name+'-saved'));a.render(out/(name+'-saved'),out/(name+'-repeat.wav'))
  if digest(wav)!=digest(out/(name+'-repeat.wav')) or a.inspect(out/name)['native']!=a.inspect(out/(name+'-saved'))['native']:raise ValidationError('pitch state/PCM reload mismatch')
  rows[name]=measured
 chords={}
 for tid,name,tones in [('track-harmony','Cm9',(51,55,58,62)),('track-harmony','Fm9-C-color',(53,56,60,63)),
                        ('track-depth-pad','Cm9-pad',(63,70,74)),('track-depth-pad','Fm9-C-pad',(63,68,79))]:
  q=held(p,tid,list(tones));a.export(q,{}, {tid:patches[tid]},out/name);a.render(out/name,out/(name+'.wav'))
  peaks=spectrum(out/(name+'.wav'),ON+.5,ON+.9)[2][:100]
  r=[{'midi':n,'nearest_peak_cents':min(abs(cents(x['hz'],hz(n))) for x in peaks)} for n in tones]
  if any(x['nearest_peak_cents']>5 for x in r):raise ValidationError('editorial simultaneous chord gate failed')
  chords[name]=r
 native=a.inspect(root/'B/native')['native']
 for t in native['tracks']:
  ins=t.get('instrument')
  if ins and '1835232641' in ins.get('params',{}) and ins['params']['1835232641']!=.5:raise ValidationError('external pitch input not neutral')
 r={'version':'phase19-pitch-1','notes':rows,'chords':chords,'maximum_cents':5,'native_synthetic_MIDI_input_1835232641':.5,'patches_changed':False,'saved_reopened_PCM_exact':True,
    'scope':'Actual G4-Eb4-F4 signature/C2 bass and simultaneous home/color voices. No new pitch vocabulary per role; all prior registers also repeated in the420-method regression.'}
 write(out/'verification.json',r);return r


def pulse_gate(root,out,host,plugin):
 root=Path(root);out=Path(out);out.mkdir();a=adapter(host,plugin);report={}
 for label,source in [('A',root/'source/phase18-reference.kuang.json'),('B',root/'B/project.kuang.json')]:
  p=load(source);q=isolate(p,{'track-kick'});assets,_=media(root/'B',q)
  a.export(q,assets,{},out/(label+'-kick'));wav=out/(label+'-kick.wav');a.render(out/(label+'-kick'),wav,end_seconds=END)
  samples=[]
  with wave.open(str(wav),'rb') as w:
   for bar in range(160):
    for beat in range(4):
     frame=round((bar*4+beat)*60/126*48000);w.setpos(frame)
     data=list(_decode(w.readframes(2400),3,2));values=[max(abs(x) for x in row) for row in data]
     power=sum(x*x for row in data for x in row)/(2*len(data))
     samples.append({'zero_bar':bar,'beat':beat+1,'onset_frame':frame,'first_50ms_peak':max(values),'mean_square':power,'peak_offset_ms':values.index(max(values))/48})
  active=[x for x in samples if 88<=x['zero_bar']<112 and x['first_50ms_peak']>.01]
  report[label]={'sha256':digest(wav),'beat_windows':samples,'audible_kick_attacks_88_112':len(active)}
 if report['B']['audible_kick_attacks_88_112']!=96:raise ValidationError('missing actual PCM kick attacks in recovered groove')
 if report['A']['audible_kick_attacks_88_112']>=96:raise ValidationError('reference pulse control failed')
 r={'version':'phase19-pulse-1','records':report,'scope':'Actual isolated kick through its unchanged native drum-sum path; attack timing only, not a nonlinear full-mix stem reconstruction or a musical quality score',
    'B_all_96_recovered_kick_attacks_present':True,'reference_and_candidate_same_sample_asset':True}
 write(out/'verification.json',r)
 for label in ('A','B'):(out/(label+'-kick.wav')).unlink()
 return r

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('pitch','pulse'));ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);x=ap.parse_args()
 (pitch_gate if x.action=='pitch' else pulse_gate)(x.root,x.out,x.soundcraft,x.plugin)
