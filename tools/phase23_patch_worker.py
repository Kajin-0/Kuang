"""Prepare the ONE two-voice original palette in two real Vitalium instances."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.chord_bed import bed_patch
from kuang.vst3_worker import prepare
from kuang.schema import strict_json,ValidationError
if __name__=='__main__':
 r=strict_json(Path(sys.argv[1]).read_text())
 if set(r)!={'voice','job'} or r['voice'] not in ('stab','pad'):raise ValidationError('one declared bed voice required')
 def factory(role,**kw):
  if role!=('pluck' if r['voice']=='stab' else 'pad'):raise ValidationError('voice/template mismatch')
  return bed_patch(r['voice'],**kw)
 print(json.dumps(prepare(r['job'],patch_factory=factory),sort_keys=True))
