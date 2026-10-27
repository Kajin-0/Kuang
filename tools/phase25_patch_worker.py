"""Prepare two original refined sources; verify BOTH actual LFO shapes."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.production_refinement import refined_patch
from kuang.vst3_worker import prepare
from kuang.vitalium_patch import component_patch
from kuang.schema import strict_json,ValidationError
if __name__=='__main__':
 r=strict_json(Path(sys.argv[1]).read_text())
 if set(r)!={'voice','job'} or r['voice'] not in ('stab','pad'):raise ValidationError('explicit known source voice required')
 def factory(role,**kw):
  if role!=('pluck' if r['voice']=='stab' else 'pad'):raise ValidationError('voice/template mismatch')
  return refined_patch(r['voice'],**kw)
 result=prepare(r['job'],patch_factory=factory)
 actual=component_patch((Path(r['job']['out'])/'component.bin').read_bytes())
 expected=factory(r['job']['role'],modulation=r['job']['modulation'],volume_db=r['job']['volume_db'])
 n=len(expected['settings']['lfos'])
 if actual['settings']['lfos'][:n]!=expected['settings']['lfos']:raise ValidationError('actual counter-phase LFO shapes failed restoration')
 print(json.dumps(result,sort_keys=True))
