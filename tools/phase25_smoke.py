"""Installed144-bar arranger on a symbolic surrogate; no audio/preference claim."""
from unittest.mock import patch
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.mix_polish import polished_mix
from kuang.house_composition import compose_record
from kuang.club_flow import refine_flow
from kuang.house_theme import compose_theme
from kuang.house_shortlist import main_reference
from kuang.chord_bed import compose_bed,audit_bed,bed_patch
from kuang.schema import state_hash
s=repaired_house(split_house(atmosphere_house())[0])[0]
for t in s.tracks:
 if t.id in ('track-harmony','track-depth-pad'):t.controls['mixer.pan']=-.12
with patch('kuang.mix_polish.SOURCE_HASH',state_hash(s)):s=polished_mix(s)[0]
with patch('kuang.house_composition.SOURCE_HASH',state_hash(s)):s=compose_record(s)[0]
with patch('kuang.club_flow.SOURCE_HASH',state_hash(s)):s=refine_flow(s)[0]
with patch('kuang.house_theme.SOURCE_HASH',state_hash(s)):s=compose_theme(s)[0]
with patch('kuang.house_shortlist.SOURCE_HASH',state_hash(s)):s=main_reference(s)
with patch('kuang.chord_bed.REFERENCE_HASH',state_hash(s)):p,r=compose_bed(s);audit_bed(s,p,r)
for role in ('stab','pad'):assert bed_patch(role)==bed_patch(role)
assert p.bars==16
from kuang.groove_record import arrange_groove,audit_record,anchor_project
source=p
with patch('kuang.groove_record.SOURCE_HASH',state_hash(source)):
 p,r=arrange_groove(source);a=audit_record(source,p,r)
assert p.bars==144 and anchor_project(source,p)==source and a['longest_kick_free_bars']==8
from kuang.production_refinement import refine_record,audit_refinement,refined_patch
from kuang.schema import ParameterSpec
reference=p
if not any(x.id=='soundcraft.input_gain' for x in reference.parameters):reference.parameters.append(ParameterSpec('soundcraft.input_gain','dB',-24,24,0,['effect']))
with patch('kuang.production_refinement.SOURCE_HASH',state_hash(reference)):
 p,r=refine_record(reference);a=audit_refinement(reference,p,r)
assert p.bars==144 and a['anchor_MIDI_exact']==501 and len(a['removed_extra_ghosts'])==4
for role in ('stab','pad'):assert refined_patch(role)==refined_patch(role)
print('Installed Phase25: scoped transition repair, two original source recipes and existing native production lanes; no preference claim')
