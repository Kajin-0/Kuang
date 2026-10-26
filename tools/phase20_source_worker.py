"""Separate existing optional GPL host; restore original source-design state."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.groove_sources import groove_patch,TEMPLATES
from kuang.vst3_worker import prepare
from kuang.schema import strict_json,ValidationError

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('one explicit local source request required')
    r=strict_json(Path(sys.argv[1]).read_text())
    if set(r)!={'voice','variant','job'} or r['voice'] not in TEMPLATES:raise ValidationError('explicit original source request required')
    def factory(role,**kw):
        if role!=TEMPLATES[r['voice']]:raise ValidationError('source voice/template mismatch')
        return groove_patch(r['voice'],variant=r['variant'],**kw)
    print(json.dumps(prepare(r['job'],patch_factory=factory),sort_keys=True))
