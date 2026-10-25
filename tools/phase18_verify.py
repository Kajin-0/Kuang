#!/usr/bin/env python3
"""Actual new-note/chord tuning and localized arrangement/automation controls."""
import argparse,json,sys,wave,math,statistics
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,Clip,Note,Section,BAR,ValidationError
from kuang.house_composition import CHORDS
from kuang.composition_analysis import event_rows
from kuang.ensemble_production import isolate
from kuang.pitch_audio import note_pitch,spectrum,hz,cents
from kuang.audio import compare_wavs,analyze_wav
from kuang.lowend_audio import band_metrics
from kuang.sample_assets import digest,write
from tools.phase15_pitch import held,ON,WINDOWS
from tools.phase17_verify import energy
from tools.phase18_house import adapter,media,END,AUDIO

SPACING=3*4*60/126

def short_sine_pitch(path,note,first,last):
 """Positive-crossing periods for the actual110ms sine pulse, not rich timbres.

 No expected-frequency search or synthetic sustain. Three or more observed
 complete periods, sub-sample linear crossings and median reject late low-level
 PCM quantization. A different octave is reported as wrong, never corrected.
 """
 from kuang.production_audio import _decode
 with wave.open(str(path),'rb') as w:
  rate=w.getframerate();w.setpos(round(first*rate));frames=list(_decode(w.readframes(round((last-first)*rate)),w.getsampwidth(),w.getnchannels()))
 a=[sum(row)/len(row) for row in frames]
 if not a or max(abs(x) for x in a)<1e-6:raise ValidationError('no measurable short sine')
 crossings=[i-a[i]/(a[i+1]-a[i]) for i in range(len(a)-1) if a[i]<=0<a[i+1]]
 periods=[b-a for a,b in zip(crossings,crossings[1:])]
 if len(periods)<3:raise ValidationError('short sine needs at least three measured periods')
 period=statistics.median(periods);variation=max(abs(x-period)/period for x in periods)
 if variation>.002:raise ValidationError('unstable zero-crossing periods; not a supported isolated sine')
 actual=rate/period
 return {'method':'median observed positive zero-crossing periods; actual110ms envelope','expected_hz':hz(note),'measured_hz':actual,'period_cents':cents(actual,hz(note)),'observed_periods':len(periods),'max_relative_period_variation':variation}

def pitch_gate(root,out,host,plugin):
 root=Path(root);out=Path(out);out.mkdir();a=adapter(host,plugin);p=load(root/'B/project.kuang.json');s=load(root/'source/phase17-approved.kuang.json');_,patches=media(root/'B',p)
 rows=event_rows(p);old=event_rows(s);cases={}
 for t in p.tracks:
  if t.kind!='midi' or t.instrument.plugin_ref=='soundcraft:sampler':continue
  new={x['pitch'] for x in rows if x['track_id']==t.id}-{x['pitch'] for x in old if x['track_id']==t.id}
  if t.id=='track-lead':new|={63,67}
  if t.id in ('track-bass','track-sub-pulse'):new|={36}
  if new:cases[t.id]=sorted(new)
 report={}
 for tid,notes in cases.items():
  q=held(p,tid,[notes[0]]);q.bars=3*len(notes);q.sections=[Section('phase18-pitch-section','Independent held notes',0,q.length)]
  q.tracks[0].clips=[Clip('phase18-pitch-clip','No note overlaps or track effects','midi',0,q.length,[Note('phase18-held-'+str(n),i*3*BAR+480,2880,n,96,0) for i,n in enumerate(notes)],None)]
  aa={tid:patches[tid]} if tid in patches else {}
  a.export(q,{},aa,out/tid);wav=out/(tid+'.wav');a.render(out/tid,wav);r={}
  for i,n in enumerate(notes):
   r[str(n)]=[short_sine_pitch(wav,n,i*SPACING+ON+lo,i*SPACING+ON+hi) for lo,hi in ((.015,.085),(.025,.095),(.035,.105))] if tid=='track-sub-pulse' else [note_pitch(wav,n,i*SPACING+ON+lo,i*SPACING+ON+hi) for lo,hi in WINDOWS]
   if any(abs(x.get('fft_cents',0))>5 or abs(x['period_cents'])>5 or x.get('period_correlation',1)<.85 for x in r[str(n)]):raise ValidationError('actual new-note tuning failed '+tid+' '+str(n))
  a.save(out/tid,out/(tid+'-saved'));repeat=out/(tid+'-repeat.wav');a.render(out/(tid+'-saved'),repeat)
  if digest(wav)!=digest(repeat) or a.inspect(out/tid)['native']!=a.inspect(out/(tid+'-saved'))['native']:raise ValidationError('new-note native state/PCM reload differs')
  report[tid]={'notes':r,'native_state_and_PCM_reload_exact':True,'sha256':digest(wav)}
  print(tid,'new-pitch gate pass',notes,flush=True)
 chords={};seen=set()
 for name,(_,tones) in CHORDS.items():
  if tones in seen:continue
  seen.add(tones);q=held(p,'track-harmony',list(tones));native=out/('chord-'+name);wav=out/('chord-'+name+'.wav')
  a.export(q,{}, {'track-harmony':patches['track-harmony']},native);a.render(native,wav)
  peaks=spectrum(wav,ON+.5,ON+.9)[2][:100]
  rr=[{'midi':n,'nearest_peak_cents':min(abs(cents(x['hz'],hz(n))) for x in peaks)} for n in tones]
  if any(x['nearest_peak_cents']>5 for x in rr):raise ValidationError('actual chord partial gate failed '+name)
  chords[name]=rr
 native=a.inspect(root/'B/native')['native']
 for track in native['tracks']:
  instrument=track.get('instrument')
  if instrument and '1835232641' in instrument.get('params',{}) and instrument['params']['1835232641']!=.5:raise ValidationError('native external MIDI pitch not neutral')
 r={'version':'phase18-pitch-1','scope':'Every new pitched MIDI value per changed role, plus leadG4/Eb4 and bassC2; six unique actual poly voicings. Existing unchanged registers also covered by the402-method regression.',
    'cases':report,'chords':chords,'windows_per_note':3,'threshold_cents':5,'native_synthetic_MIDI_input_1835232641':.5,'patches_modified':False,'MIDI_transposed_as_workaround':False}
 write(out/'verification.json',r);return r

def gestures(root,out,host,plugin):
 root=Path(root);out=Path(out);out.mkdir();a=adapter(host,plugin);p=load(root/'B/project.kuang.json');_,patches=media(root/'B',p)
 q=isolate(p,{'track-harmony','track-lead','track-arp'});off=deepcopy(q)
 eqs={e.id for t in off.tracks for e in t.effects if e.plugin_ref=='soundcraft:eq_7band'}
 off.automation=[x for x in off.automation if not(x.target_id in eqs and x.parameter_id in ('soundcraft.lpf_freq','soundcraft.hpf_freq'))]
 for t in off.tracks:
  if t.kind=='midi':
   for e in t.effects:
    if e.id in eqs:e.parameters['soundcraft.lpf_freq']=14000
 paths={}
 for label,project in [('performed',q),('static',off)]:
  path=out/(label+'.wav');a.export(project,{}, {t.id:patches[t.id] for t in project.tracks if t.id in patches},out/label);a.render(out/label,path,end_seconds=END);paths[label]=path
 delta=compare_wavs(paths['static'],paths['performed'])
 bands={label:{'early_rebuild':band_metrics(wav,first=96*4*60/126,last=100*4*60/126,windows=4),
               'late_rebuild':band_metrics(wav,first=108*4*60/126,last=111.5*4*60/126,windows=4)} for label,wav in paths.items()}
 early=bands['performed']['early_rebuild']['band_mean_square']['2000_8000']/bands['static']['early_rebuild']['band_mean_square']['2000_8000']
 if delta['difference_to_original_rms_ratio']<.001 or early>=.9:raise ValidationError('performed rebuilding filters inert')
 full=root/AUDIO['B'];lastbeat=energy(full,(111*4+3)*60/126,112*4*60/126);returnbar=energy(full,112*4*60/126,113*4*60/126)
 if lastbeat/returnbar>=.4:raise ValidationError('pre-drop gap lacks measured release contrast')
 # Read all twenty non-overlapping eight-bar PCM windows. Hashes alone are not
 # musical variety proof; the independent note-signature audit supplies that.
 hashes=[]
 with wave.open(str(full),'rb') as w:
  import hashlib
  for first in range(0,160,8):
   lo=round(first*4*60/126*48000);hi=round((first+8)*4*60/126*48000);w.setpos(lo)
   hashes.append({'first_bar':first+1,'PCM_sha256':hashlib.sha256(w.readframes(hi-lo)).hexdigest()})
 r={'version':'phase18-gestures-1','control_scope':'Same harmonic MIDI/patches/sends/gains; only EQ7 HPF/LPF automation removed; static LPF14000Hz with the original resting HPF, not the closed1000Hz base. A fresh full160-bar native bounce each, no postprocessing.',
    'same_input_difference':delta,'bands':bands,'early_rebuild_2_8k_power_performed_over_static':early,
    'pre_drop_last_beat_mean_square':lastbeat,'first_return_bar_mean_square':returnbar,'gap_over_return_power':lastbeat/returnbar,
    'phrase_PCM_hashes':hashes,'different_PCM_phrase_windows':len({x['PCM_sha256'] for x in hashes}),'controls_sha256':{k:digest(v) for k,v in paths.items()}}
 write(out/'verification.json',r)
 for wav in paths.values():wav.unlink() # repeatable native/control hashes kept; avoid redundant full stems
 return r

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('pitch','gestures'));ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);x=ap.parse_args()
 (pitch_gate if x.action=='pitch' else gestures)(x.root,x.out,x.soundcraft,x.plugin)
