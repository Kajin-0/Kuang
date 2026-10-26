"""Installed editorial arranger smoke; no optional host or playback claim."""
from unittest.mock import patch
from kuang.schema import state_hash,validate
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.house_composition import compose_record
from kuang.club_flow import refine_flow
from kuang.flow_audit import audit_flow,require_flow
s=repaired_house(split_house(atmosphere_house())[0])[0]
for t in s.tracks:
 if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
with patch('kuang.mix_polish.SOURCE_HASH',state_hash(s)):s=polished_mix(s)[0]
with patch('kuang.house_composition.SOURCE_HASH',state_hash(s)):s=compose_record(s)[0]
with patch('kuang.club_flow.SOURCE_HASH',state_hash(s)):p,r=refine_flow(s)
validate(p);a=audit_flow(s,p,r);require_flow(a)
assert a['candidate_facts']['longest_kick_free_bars']==8 and a['candidate_facts']['first_complete_signature_zero_bar']==16
print('Installed Phase19 continuity:160bars,8-bar maximum kick gap,signature16,exact note journal; native playback not claimed by smoke')
