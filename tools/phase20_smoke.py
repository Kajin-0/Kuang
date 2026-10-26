"""Installed record mix/master contract, no optional host/playback claim."""
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.house_composition import compose_record
from kuang.club_flow import refine_flow
from kuang.record_mix import mixed_record
from kuang.master_bus import terminal_projection
from kuang.schema import state_hash,validate
from kuang.midi import export_bytes
from kuang.groove_sources import groove_patch
from kuang.vitalium_patch import component,component_patch
s=repaired_house(split_house(atmosphere_house())[0])[0]
for t in s.tracks:
    if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
with patch('kuang.mix_polish.SOURCE_HASH',state_hash(s)):s=polished_mix(s)[0]
with patch('kuang.house_composition.SOURCE_HASH',state_hash(s)):s=compose_record(s)[0]
with patch('kuang.club_flow.SOURCE_HASH',state_hash(s)):s=refine_flow(s)[0]
with patch('kuang.record_mix.SOURCE_HASH',state_hash(s)):p,r=mixed_record(s)
validate(p);terminal_projection(p)
assert export_bytes(p)==export_bytes(s) and r['native_master'] and not r['native_limiter_true_peak_aware_claimed']
for voice in ('bass','stab','lead'):
    q=groove_patch(voice)
    assert component_patch(component(q))==q
    assert all('pitch' not in x['destination'] for x in q['settings']['modulations'])
print('Installed Phase20: exact MIDI mix/terminal contracts and original source designs; no host playback or quality claim')
