"""Separate optional GPL-host process; no dependency in the MIT runtime."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.producer_patches import ROLES,production_patch
from kuang.vst3_worker import prepare
from kuang.schema import ValidationError,strict_json

if __name__=='__main__':
    request=strict_json(Path(sys.argv[1]).read_text())
    if type(request) is not dict or set(request)!={'voice','job'} or request['voice'] not in ROLES:
        raise ValidationError('explicit original production voice request required')
    voice=request['voice']
    def factory(role,**kwargs):
        if role!=ROLES[voice]:raise ValidationError('voice/template role disagreement')
        return production_patch(voice,**kwargs)
    print(json.dumps(prepare(request['job'],patch_factory=factory),sort_keys=True))
