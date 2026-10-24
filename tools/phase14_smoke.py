"""Installed stdlib graph/patch smoke; intentionally needs no host or plugin."""
from kuang.atmosphere import atmosphere_house
from kuang.gestures import crop
from kuang.production_host import graph_contract,add_send_trim,add_spread,native_pan
from kuang.producer_patches import production_patch
from kuang.vitalium_patch import component,vstpreset,chunks
from kuang.schema import Track,Send
from kuang.midi import export_bytes
p=crop(atmosphere_house(),32,2,['track-kick','track-harmony']);p.automation=[]
bus=Track('smoke-bus','Installed aux','bus',None,{'mixer.gain_db':0,'mixer.pan':0,'mixer.mute':0},[],[],[],True)
p.tracks.append(bus);source=p.tracks[1];source.controls['mixer.pan']=0;add_spread(p,source,.5)
s=Send('smoke-send',bus.id,-12,0,'post_fader');source.sends=[s];add_send_trim(p,source,s)
graph_contract(p);assert native_pan(source)==[-.5,.5];assert export_bytes(p)[:4]==b'MThd'
for voice in ('bass','stab','lead','pad'):
 patch=production_patch(voice);assert patch==production_patch(voice)
 assert chunks(vstpreset(component(patch)))[b'Comp']==component(patch)
print('Installed stdlib producer graph and four original patch designs passed')
