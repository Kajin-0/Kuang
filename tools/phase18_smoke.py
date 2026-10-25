"""Installed stdlib extended-arrangement smoke, not a native playback claim."""
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.house_composition import compose_record
from kuang.composition_analysis import audit_composition
from kuang.schema import state_hash,validate
base=repaired_house(split_house(atmosphere_house())[0])[0]
for t in base.tracks:
 if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
with patch('kuang.mix_polish.SOURCE_HASH',state_hash(base)):source=polished_mix(base)[0]
with patch('kuang.house_composition.SOURCE_HASH',state_hash(source)):p,r=compose_record(source)
validate(p);a=audit_composition(source,p,r);assert p.bars==160 and len(p.sections)==8
assert a['unique_eight_bar_signatures_without_velocity']==18 and not a['bridge_wrong_root_note_ids']
assert not a['out_of_key_intervals'] and a['all_note_origins_exact']
print('Installed Phase18 record:160bars,18distinct musical phrases,complete provenance; native playback not claimed by smoke')
