"""Installed-wheel/resource check, run with -I outside checkout imports."""
from kuang.atmosphere import atmosphere_house
from kuang.drum_palette import note_inventory
from kuang.octalsamples import catalog
from kuang.record_palette import split_house
from kuang.schema import validate

p=atmosphere_house();q,r=split_house(p);validate(q)
assert note_inventory(p)==note_inventory(q) and len(note_inventory(q))==1536
assert len(q.tracks)==13 and len(catalog()['samples'])==44
assert catalog()['commit']=='22d222ce36e290ba3792c776811aa9c69dcc8776'
print('Installed Phase13 profile + reviewed catalog smoke passed; no host or quality claim')
