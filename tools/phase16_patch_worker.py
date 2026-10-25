"""Optional independent GPL host process; no dependency in Kuang runtime."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kuang.studio_palette import ROLES, studio_patch
from kuang.vst3_worker import prepare
from kuang.schema import ValidationError, strict_json

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('expected one explicit local request')
    request = strict_json(Path(sys.argv[1]).read_text())
    if type(request) is not dict or set(request) != {'voice', 'job'} or request['voice'] not in ROLES:
        raise ValidationError('explicit studio voice request required')
    def factory(role, **kwargs):
        if role != ROLES[request['voice']]:
            raise ValidationError('studio voice/template disagreement')
        return studio_patch(request['voice'], **kwargs)
    print(json.dumps(prepare(request['job'], patch_factory=factory), sort_keys=True))
