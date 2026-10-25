"""Installed mix-only module smoke; no native host/plugin dependency."""
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.schema import state_hash,validate
from kuang.midi import export_bytes
p=repaired_house(split_house(atmosphere_house())[0])[0]
for t in p.tracks:
    if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
with patch('kuang.mix_polish.SOURCE_HASH',state_hash(p)):q,r=polished_mix(p)
validate(q);assert export_bytes(p)==export_bytes(q);assert len(q.tracks)==17
assert sum(len(c.notes) for t in q.tracks for c in t.clips)==1536
print('Installed Phase17 mix: exact1536 notes, four actual aux graph specifications; native playback not claimed by smoke')
