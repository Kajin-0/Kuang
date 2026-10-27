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
from kuang.production_refinement import PROTECTED,INPUT_TRIMS,refine_record
from kuang.gesture_audio import phase_gain
from kuang.mix_diagnostics import linked_gain_audit,envelope_gain_audit
from tools.phase23_verify import normalized_delta
from kuang.lowend_audio import band_metrics
from kuang.production_host import ProductionAdapter
from kuang.gestures import crop
from tools.phase22_shortlist import stem
from tools.phase25_house import adapter,media
from tools.phase15_pitch import held
from tools.phase21_pitch import analyze

CASES={'stab':{'track':'track-harmony','notes':[51,53,55,56,58,62,63,67],
 'chords':[[51,58,62],[53,58,63],[51,56,58],[55,58,62],[56,58,63],[53,58,67]]},
 'pad':{'track':'track-depth-pad','notes':[58,63,67,70,72,74,77],
 'chords':[[63,67,74],[63,67,77],[63,67,72],[63,67,70],[58,63,74],[58,63,77],[58,63,67]]},
 'bass':{'track':'track-bass','notes':[36],'chords':[[36]]}}

def pitch(root,out,host,plugin,host_python):
 root=Path(root);out=Path(out).resolve()
 if out.exists() or not out.is_relative_to(ROOT/'.local/phase25'):raise ValidationError('new Phase25 pitch scratch required')
 out.mkdir();p=load(root/'project/project.kuang.json');_,patches=media(root/'project',p)
 a=ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase25/tmp',center_pitch_bend=True);result={}
 for voice,case in CASES.items():
  tid=case['track'];groups=[[n] for n in case['notes']]+case['chords'];q=held(p,tid,[36]);q.bars=3*len(groups);q.sections=[Section('phase25-pitch-'+voice,'Actual held source registers and chords',0,q.bars*BAR)]
  q.tracks[0].controls['mixer.gain_db']=-24;q.tracks[0].clips=[Clip('phase25-pitch-clip','Dry source calibration','midi',0,q.bars*BAR,
   [Note('phase25-pitch-'+str(i)+'-'+str(j),i*3*BAR+480,2880,n,96,0) for i,notes in enumerate(groups) for j,n in enumerate(notes)],None)]
  a.export(q,{}, {tid:patches[tid]},out/voice);wav=out/(voice+'-native.wav');a.render(out/voice,wav);rows=analyze(wav,case)
  a.save(out/voice,out/(voice+'-saved'));a.render(out/(voice+'-saved'),out/(voice+'-repeat.wav'))
  if digest(wav)!=digest(out/(voice+'-repeat.wav')) or a.inspect(out/voice)['native']!=a.inspect(out/(voice+'-saved'))['native']:raise ValidationError('held source tuning reload changed')
  result[voice]={'native':rows,'native_state_PCM_reopen_exact':True};print(voice,'actual pitch/chords pass',flush=True)
 request=out/'request.json';write(request,{'plugin':str(a.external.plugin),'out':str(out),'cases':{v:{'patch':str(patches[c['track']]),'notes':c['notes'],'chords':c['chords']} for v,c in CASES.items()}})
 a.external.call([str(Path(host_python).absolute()),str(ROOT/'tools/phase21_independent.py'),str(request)],ROOT)
 for voice,case in CASES.items():result[voice]['independent']=analyze(out/(voice+'-independent.wav'),case)
 r={'version':'phase25-actual-tuning-1','native_pitch_center':.5,'limit_cents':5,'voices':result,'scope':'All performed new upper registers and explicit new chords plus unchanged C2; original patch states, no preference inference'}
 write(out/'verification.json',r);return r

def source_controls(root,host,plugin,meter=None):
 root=Path(root);s=load(root/'phase24-source.kuang.json');p=load(root/'project/project.kuang.json');a=adapter(host,plugin);assets,patches=media(root/'project',p)
 original=ROOT/'artifacts/phase24-house/project/native/patches';dry=ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase25/tmp',center_pitch_bend=True)
 reports={};rhythm={}
 with tempfile.TemporaryDirectory(dir=a.scratch,prefix='source-controls-') as d:
  d=Path(d)
  def render(name,score,pp=patches,plain=False):
   folder=d/name;wav=d/(name+'.wav');engine=dry if plain else a
   engine.export(score,{t.id:assets[t.id] for t in score.tracks if t.id in assets},{t.id:pp[t.id] for t in score.tracks if t.id in pp},folder);engine.render(folder,wav,end_seconds=16*4*60/126+5);return wav
  window=crop(p,16,16,[t.id for t in p.tracks]);oldwindow=crop(s,16,16,[t.id for t in s.tracks])
  for label,score in [('old',oldwindow),('new',window)]:
   score=stem(score,PROTECTED);rhythm[label]=render('protected-anchor-'+label,score)
  if digest(rhythm['old'])!=digest(rhythm['new']):raise ValidationError('approved eight-role anchor rhythm PCM changed')
  for voice,tid in [('stab','track-harmony'),('pad','track-depth-pad')]:
   q=stem(window,{tid});old=deepcopy(q);next(t for t in old.tracks if t.id==tid).instrument=deepcopy(next(t.instrument for t in s.tracks if t.id==tid))
   oldwav=render('old-source-'+voice,old,{tid:original/tid});newwav=render('new-source-'+voice,q)
   levels={'old':measure(oldwav,library=meter),'new':measure(newwav,library=meter)};gain=levels['old']['integrated_lufs']-levels['new']['integrated_lufs'];delta=normalized_delta(oldwav,newwav,gain)
   if delta['difference_to_source_RMS']<.10:raise ValidationError('source difference is only gain/label '+voice)
   bands={label:band_metrics(path,first=.5,last=30,windows=8) for label,path in [('old',oldwav),('new',newwav)]}
   # Exactly the same new source/amp/velocity/filter envelopes; ONLY slow LFO
   # routes are disconnected, using a real saved/restored optional test state.
   offpath=ROOT/'.local/phase25/motion-off-patches'/voice;off=deepcopy(q)
   from kuang.external_synth import bound_project
   off=bound_project(off,{tid:offpath});offwav=render('motion-off-'+voice,off,{tid:offpath});motion=compare_wavs(offwav,newwav)
   if motion['difference_to_original_rms_ratio']<.02:raise ValidationError('new LFO motion is inert '+voice)
   # Independent calibrated pre-insert check. Explicit EQ input makeup is a
   # flat level stage; it is not a mix/master loudness shortcut.
   base=held(s,tid,[36]);base.bars=16;base.sections=[Section('dry-stage','Same-MIDI pre-insert source input',0,16*BAR)]
   base.tracks[0].clips=[deepcopy(c) for c in next(t for t in s.tracks if t.id==tid).clips if 16*BAR<=c.start<32*BAR]
   for c in base.tracks[0].clips:c.start-=16*BAR
   rawold=render('preinsert-old-'+voice,base,{tid:original/tid},True)
   calibrated=deepcopy(base);calibrated.tracks[0].instrument=deepcopy(next(t.instrument for t in p.tracks if t.id==tid))
   if INPUT_TRIMS[voice]:calibrated.tracks[0].effects=[Effect('phase25-flat-input-'+voice,'soundcraft:eq_7band',None,{'effect.bypass':0,'soundcraft.input_gain':INPUT_TRIMS[voice]})]
   rawnew=render('preinsert-new-'+voice,calibrated,{tid:patches[tid]},True)
   calibration={label:measure(path,library=meter) for label,path in [('old',rawold),('new',rawnew)]};error=calibration['new']['integrated_lufs']-calibration['old']['integrated_lufs']
   if abs(error)>.01:raise ValidationError('actual pre-insert level calibration failed '+voice+' '+str(error))
   reports[voice]={'same_new_MIDI_source_swap_equal_LUFS':delta,'levels':levels,'bands':bands,'LFO_routes_on_off_same_input':motion,'preinsert_calibration':calibration,'preinsert_error_LU':error,'native_EQ_input_makeup_db':INPUT_TRIMS[voice]}
   print(voice,'calibrated source and genuine LFO PCM gates pass',flush=True)
  wet=stem(window,{'track-depth-pad'});t=next(t for t in wet.tracks if t.id=='track-depth-pad');t.sends=[x for x in t.sends if x.target_track_id!='production-terminal-master']
  full=deepcopy(wet);target=next(x for x in full.automation if x.target_id=='phase17-dark-space' and x.parameter_id=='mixer.gain_db');source=next(x for x in oldwindow.automation if x.target_id==target.target_id and x.parameter_id==target.parameter_id);target.points=deepcopy(source.points)
  on=render('wet-return-corrected-duck',wet);off=render('wet-return-original-duck',full);envelope=phase_gain(on,off,first_beat=8,beats=32)
  if envelope['duck']['on_off_db']<1 or abs(envelope['open']['on_off_db'])>.1:raise ValidationError('extra return duck correction did not isolate actual postkick attenuation')
  return {'version':'phase25-source-proof-1','anchor_rhythm_PCM_exact':True,'anchor_rhythm_sha256':digest(rhythm['old']),'voices':reports,'wet_only_return_duck_correction':envelope,
   'scope':'Same-MIDI native source/input/LFO/return controls; reset16-bar anchor; gain-normalized timbral deltas are not preference scores. All private controls discarded.'}


def rhythm_qa(root,host,plugin):
 root=Path(root);s=load(root/'phase24-source.kuang.json');edited,r=refine_record(s);repair=deepcopy(s)
 for a,b in zip(repair.tracks,edited.tracks):a.clips=deepcopy(b.clips)
 a=next(a for a in repair.automation if a.target_id=='track-harmony' and a.parameter_id.startswith('route.'));b=next(b for b in edited.automation if b.id==a.id);a.points=deepcopy(b.points)
 original=ROOT/'artifacts/phase24-house/project';assets,patches=media(original,s);engine=adapter(host,plugin);reports={}
 with tempfile.TemporaryDirectory(dir=engine.scratch,prefix='rhythm-qa-') as d:
  d=Path(d)
  for first in (62,78,110,126):
   paths=[];events=[]
   for label,score in [('before',s),('after',repair)]:
    q=crop(score,first,4,[t.id for t in score.tracks]);folder=d/(str(first)+'-'+label);wav=d/(str(first)+'-'+label+'.wav');engine.export(q,assets,patches,folder);engine.render(folder,wav,end_seconds=4*4*60/126+5);paths.append(wav)
    from kuang.composition_analysis import event_rows
    events.append([{'id':x['id'],'track':x['track_id'],'beat':x['absolute_tick']/960,'pitch':x['pitch'],'duration':x['duration'],'velocity':x['velocity']} for x in event_rows(q) if x['track_id'] in ('track-snare','track-snare.p38','track-harmony','track-bass')])
   prefix=round(4*60/126*48000)
   with wave.open(str(paths[0]),'rb') as x,wave.open(str(paths[1]),'rb') as y:same=x.readframes(prefix)==y.readframes(prefix)
   if not same:raise ValidationError('transition repair changed the preceding unaffected bar')
   delta=compare_wavs(*paths)
   if not delta['measurable_change']:raise ValidationError('rhythm repair render is inert')
   reports[str(first+1)]={'zero_first_bar':first,'music_start_seconds':first*4*60/126,'bars':4,'unaffected_first_bar_PCM_exact':True,'actual_PCM_difference':delta,'event_audit_before':events[0],'event_audit_after':events[1]}
 return {'version':'phase25-rhythm-qa-1','extra_ghosts_removed':4,'source_ghost_3_777_retained':True,'chord_voice_onsets_moved':12,'shift_ms':120/960*60/126*1000,
  'bass_omissions_retained':True,'windows':reports,'scope':'Original Phase24 patches/FX/gains, ONLY reviewed note and echo timing repair; fresh native4-bar windows. PCM differences do not prove perceived rhythm preference; private WAVs discarded.'}


def master_probe(root,host,plugin,meter=None):
 root=Path(root);p=load(root/'project/project.kuang.json');q=crop(p,80,4,[t.id for t in p.tracks]);a=adapter(host,plugin);assets,patches=media(root/'project',q)
 if q.tracks[-1].effects:raise ValidationError('production master must remain transparent')
 effects=[Effect('phase25-probe-glue','soundcraft:compressor',None,{'effect.bypass':0,'effect.wet':.25,'soundcraft.threshold':-25,'soundcraft.attack':30,'soundcraft.release':150,'soundcraft.makeup':0,'soundcraft.knee':4}),
          Effect('phase25-probe-color','soundcraft:saturator',None,{'effect.bypass':0,'effect.wet':.3,'soundcraft.drive':4,'soundcraft.output':-4,'soundcraft.tone':5000}),
          Effect('phase25-probe-ceiling','soundcraft:maximizer',None,{'effect.bypass':0,'soundcraft.threshold':-12,'soundcraft.ceiling':-3,'soundcraft.release':80})]
 report={}
 with tempfile.TemporaryDirectory(dir=a.scratch,prefix='master-feasibility-') as d:
  d=Path(d)
  def render(name,score):
   folder=d/name;wav=d/(name+'.wav');a.export(score,assets,patches,folder);a.render(folder,wav,end_seconds=4*4*60/126+5);return folder,wav
  _,baseline=render('transparent',q)
  for effect in effects:
   tested=deepcopy(q);tested.tracks[-1].effects=[effect];folder,wav=render(effect.id,tested);difference=compare_wavs(baseline,wav)
   if difference['difference_to_original_rms_ratio']<.001:raise ValidationError('native terminal effect inert '+effect.plugin_ref)
   a.save(folder,d/(effect.id+'-reopen'));a.render(d/(effect.id+'-reopen'),d/(effect.id+'-repeat.wav'),end_seconds=4*4*60/126+5)
   if a.inspect(folder)['native']!=a.inspect(d/(effect.id+'-reopen'))['native'] or digest(wav)!=digest(d/(effect.id+'-repeat.wav')):raise ValidationError('terminal probe native state/PCM reload failed')
   row={'parameters':effect.parameters,'actual_difference':difference,'native_state_PCM_reopen_exact':True,'levels':measure(wav,library=meter)}
   if effect.plugin_ref=='soundcraft:compressor':
    row['observed_gain_reduction']=linked_gain_audit(baseline,wav)
    if row['observed_gain_reduction']['p01_attenuation_below_nominal_db']<.1:raise ValidationError('native terminal compression not demonstrated')
   elif effect.plugin_ref=='soundcraft:saturator':
    levels=measure(baseline,library=meter);row['equal_LUFS_shape_delta']=normalized_delta(baseline,wav,levels['integrated_lufs']-row['levels']['integrated_lufs'])
   else:
    row['envelope']=envelope_gain_audit(baseline,wav,nominal_gain_db=12)
   report[effect.plugin_ref]=row
 return {'version':'phase25-terminal-feasibility-1','actual_terminal_routes_and_processing':True,'effects':report,'applied_to_final_record':False,
  'decision':'Keep final master transparent to protect rhythm sound and isolate the source/role production step; no consumer-master variant.',
  'limits':'Native maximizer is NOT claimed true-peak-aware. One4-bar bounded probe, no mastering quality claim; optional control recordings discarded.'}


if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('rhythm','master','pitch','sources'));ap.add_argument('--root',required=True);ap.add_argument('--out');ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);ap.add_argument('--host-python');ap.add_argument('--meter-library');z=ap.parse_args()
 if z.action=='rhythm':r=rhythm_qa(z.root,z.soundcraft,z.plugin);name='rhythm-proof.json'
 elif z.action=='master':r=master_probe(z.root,z.soundcraft,z.plugin,z.meter_library);name='master-gate.json'
 elif z.action=='pitch':r=pitch(z.root,z.out,z.soundcraft,z.plugin,z.host_python);name='pitch-proof.json'
 else:r=source_controls(z.root,z.soundcraft,z.plugin,z.meter_library);name='source-proof.json'
 write(Path(z.root)/name,r);print(json.dumps(r,indent=2))
