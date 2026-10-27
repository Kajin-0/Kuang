"""Installed stdlib shortlist on an explicit symbolic surrogate, no audio claim."""
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.house_composition import compose_record
from kuang.club_flow import refine_flow
from kuang.house_theme import compose_theme
from kuang.house_shortlist import main_reference,compose_candidate
from kuang.shortlist_audit import audit_shortlist,require_shortlist
from kuang.schema import state_hash
s=repaired_house(split_house(atmosphere_house())[0])[0]
for t in s.tracks:
 if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
with patch('kuang.mix_polish.SOURCE_HASH',state_hash(s)):s=polished_mix(s)[0]
with patch('kuang.house_composition.SOURCE_HASH',state_hash(s)):s=compose_record(s)[0]
with patch('kuang.club_flow.SOURCE_HASH',state_hash(s)):s=refine_flow(s)[0]
with patch('kuang.house_theme.SOURCE_HASH',state_hash(s)):s=compose_theme(s)[0]
with patch('kuang.house_shortlist.SOURCE_HASH',state_hash(s)):a=main_reference(s)
for kind in ('soulful','progressive','hypnotic'):
 with patch('kuang.house_shortlist.REFERENCE_HASH',state_hash(a)):p,r=compose_candidate(a,kind)
 require_shortlist(audit_shortlist(a,p,r));assert p.bars==16
print('Installed Phase22: three16-bar themes, exact drums/bass rhythm and palette; no full song/master/preference claim')
