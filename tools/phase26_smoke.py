"""Installed optional composer smoke without plugin/media downloads."""
from pathlib import Path
from unittest.mock import patch
# Reuse the independently runnable installed ancestor construction.
exec((Path(__file__).resolve().parent/'phase25_smoke.py').read_text())
from kuang.groove_direction import compose_direction,audit_direction
from kuang.schema import state_hash
from kuang.schema import AutomationLane,AutomationPoint,BAR
# Explicit known captured source lane absent from the symbolic ancestors.
p.automation.append(AutomationLane('phase20-kick-startup','track-kick','mixer.gain_db',[AutomationPoint('symbolic-kick-'+str(b),b*BAR,-3.,'linear') for b in (0,16,32,48,64,80,96,112,128,144)]))
with patch('kuang.groove_direction.SOURCE_HASH',state_hash(p)):
 q,r=compose_direction(p);a=audit_direction(p,q,r)
assert next(a for a in q.automation if a.target_id=='track-kick').points[0].value==-5
assert q.bars==144 and a['anchor_notes_exact']==501 and a['bass_pitch_only']
print('Installed Phase26: functional cadence and staged intro; exact approved anchor')
