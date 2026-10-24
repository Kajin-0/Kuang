"""Installed stdlib musical repair/pitch contract smoke; no plugin or host."""
from kuang.atmosphere import atmosphere_house
from kuang.record_palette import split_house
from kuang.musical_repair import repaired_house
from kuang.pitch_audio import hz
from kuang.midi import export_bytes
from kuang.harmonic_audit import context
p=split_house(atmosphere_house())[0];q,r=repaired_house(p)
assert export_bytes(q)==export_bytes(p)
assert context(q)==context(p)
assert len(q.tracks)==15 and r['added_notes']==[]
assert hz(69)==440
print('Installed musical repair: exact original MIDI/harmony, two real-route aux specifications, stdlib pitch API')
