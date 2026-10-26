"""Optional separately installed GPL host, new-note tuning only; no factory data."""
import json,sys,wave
from pathlib import Path
import numpy as np
import pedalboard
if __name__=='__main__':
 r=json.loads(Path(sys.argv[1]).read_text())
 if set(r)!={'plugin','out','cases'} or pedalboard.__version__!='0.9.26':raise SystemExit('reviewed strict independent request required')
 for voice,case in r['cases'].items():
  p=pedalboard.load_plugin(r['plugin']);p.preset_data=(Path(case['patch'])/'patch.vstpreset').read_bytes()
  if p.version!='1.0.6' or p.manufacturer_name!='DISTRHO':raise SystemExit('reviewed Vitalium required')
  groups=[[n] for n in case['notes']]+case['chords'];events=[]
  for i,pitches in enumerate(groups):
   on=(i*12+.5)*60/126
   for n in pitches:events.extend([(bytes([0x90,n,96]),on),(bytes([0x80,n,0]),on+3*60/126)])
  audio=p(sorted(events,key=lambda x:x[1]),duration=len(groups)*12*60/126+5,sample_rate=48000,num_channels=2,buffer_size=512)*.1
  if not np.isfinite(audio).all() or np.max(np.abs(audio))>=1:raise SystemExit('invalid independent PCM')
  data=np.rint(audio.T.reshape(-1)*2**23).astype('<i4').view(np.uint8).reshape(-1,4)[:,:3].tobytes()
  with wave.open(str(Path(r['out'])/(voice+'-independent.wav')),'wb') as w:w.setparams((2,3,48000,0,'NONE',''));w.writeframes(data)
