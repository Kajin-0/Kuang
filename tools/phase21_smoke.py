"""Installed authored theme, symbolic surrogate; no real-host audio claim."""
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.house_composition import compose_record
from kuang.club_flow import refine_flow
from kuang.house_theme import compose_theme
from kuang.theme_audit import audit_theme,require_theme,PROTECTED
from kuang.schema import state_hash
s=repaired_house(split_house(atmosphere_house())[0])[0]
for t in s.tracks:
 if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
with patch('kuang.mix_polish.SOURCE_HASH',state_hash(s)):s=polished_mix(s)[0]
with patch('kuang.house_composition.SOURCE_HASH',state_hash(s)):s=compose_record(s)[0]
with patch('kuang.club_flow.SOURCE_HASH',state_hash(s)):s=refine_flow(s)[0]
with patch('kuang.house_theme.SOURCE_HASH',state_hash(s)):p,r=compose_theme(s)
require_theme(audit_theme(s,p,r))
assert p.bars==160 and all(a==b for a,b in zip(s.tracks,p.tracks) if a.id in PROTECTED)
print('Installed Phase21: authored160-bar upper theme, exact rhythm section/graph, complete harmony audit; no audio/preference claim')
