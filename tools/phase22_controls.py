#!/usr/bin/env python3
"""Internal native role controls; four full mixes are the listening deliverable."""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.house_shortlist import DRUMS,LOW,UPPER
from kuang.schema import load,ValidationError
from kuang.sample_assets import digest,write
from kuang.audio import compare_wavs
from kuang.lowend_audio import band_metrics
from tools.phase22_shortlist import adapter,media,stem,OPTIONS,END

def controls(root,host,plugin):
 root=Path(root);ps={n:load(root/n/'project.kuang.json') for n in OPTIONS};assets,patches=media(root/'A',ps['A']);a=adapter(host,plugin);hashes={};deltas={};bands={}
 with tempfile.TemporaryDirectory(dir=a.scratch,prefix='role-control-') as d:
  d=Path(d);files={}
  for n,p in ps.items():
   for role,ids in [('drums',DRUMS),('low',LOW),('upper',UPPER)]:
    q=stem(p,ids);folder=d/(n+'-'+role);a.export(q,{t.id:assets[t.id] for t in q.tracks if t.id in assets},{t.id:patches[t.id] for t in q.tracks if t.id in patches},folder);wav=folder.with_suffix('.wav');a.render(folder,wav,end_seconds=END);files[n+'-'+role]=wav;hashes[n+'-'+role]=digest(wav)
   print(n,'actual native role controls rendered',flush=True)
  if any(hashes['A-drums']!=hashes[n+'-drums'] for n in 'BCD') or hashes['A-low']!=hashes['D-low']:raise ValidationError('protected pocket PCM changed')
  for n in 'BCD':
   deltas[n+'-upper']=compare_wavs(files['A-upper'],files[n+'-upper'])
   if deltas[n+'-upper']['difference_to_original_rms_ratio']<.1:raise ValidationError('upper composition control too small')
  for n in 'BC':
   deltas[n+'-low']=compare_wavs(files['A-low'],files[n+'-low'])
   if deltas[n+'-low']['difference_to_original_rms_ratio']<.1:raise ValidationError('root motion did not sound')
  # Real powers/fractions of unchanged-patch low stems, not quality targets.
  for n in OPTIONS:bands[n]=band_metrics(files[n+'-low'],first=0,last=16*4*60/126)
 report={'version':'phase22-role-controls-1','all_four_drums_PCM_exact':True,'A_D_bass_and_sub_PCM_exact':True,'role_sha256':hashes,'same_palette_performance_differences':deltas,'low_band_measurements':bands,
         'scope':'Actual isolated native roles through their reachable shared graph; no source/FX edits, not artistic preference scores. Disposable control PCM is omitted from listening pack.'}
 write(root/'context-verification.json',report);return report

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__)
 for f in ('root','soundcraft','plugin'):ap.add_argument('--'+f,required=True)
 z=ap.parse_args();print(json.dumps(controls(z.root,z.soundcraft,z.plugin),indent=2))
