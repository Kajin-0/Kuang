"""Installed-wheel sound-only design smoke; no optional plugin dependency."""
from kuang.studio_palette import studio_patch, ROLES
from kuang.sound_palette import performance
from kuang.musical_repair import repaired_house
from kuang.record_palette import split_house
from kuang.atmosphere import atmosphere_house
from kuang.vitalium_patch import component, component_patch
from kuang.schema import validate

for voice in ROLES:
    p=studio_patch(voice)
    assert component_patch(component(p)) == p
    assert p == studio_patch(voice)
    assert p['settings']['osc_1_tune'] == 0
p=repaired_house(split_house(atmosphere_house())[0])[0];validate(p)
assert sum(len(c['notes']) for t in performance(p)['tracks'] for c in t['clips']) == 1536
print('Installed Phase16 original palette: no optional host import; exact1536-note source')
