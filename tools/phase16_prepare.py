#!/usr/bin/env python3
"""Prepare original role patches through an explicit optional independent host.

Discover the actual native defaults, restore every supplied synth control in
two real plugin instances, and publish hashed original content only. No download.
Use phase16_pitch.py before evaluating/exporting these patches as a palette.
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kuang.production_host import ProductionAdapter
from kuang.studio_palette import ROLES
from kuang.external_synth import read_patch, PLUGIN_ID
from kuang.sample_assets import write
from kuang.schema import load, ValidationError
from tools.phase15_pitch import held


def prepare(destination, host, plugin, host_python, *, modulation=True):
    if type(modulation) is not bool: raise ValidationError('explicit modulation boolean required')
    a = ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase16/tmp',center_pitch_bend=True)
    a.capabilities();dest = a.new(destination)
    if not dest.is_relative_to(ROOT/'.local/phase16'):raise ValidationError('Phase16 preparation belongs in project-local scratch')
    source = load(ROOT/'artifacts/phase15-house/B/project.kuang.json')
    with tempfile.TemporaryDirectory(dir=a.scratch,prefix='studio-prepare-') as d:
        d = Path(d); q = held(source,'track-lead',[67]); a.base.export(q,d/'probe')
        native = json.loads((d/'probe/session.scraft').read_text())
        a.external.script([('mix.instrument',{'track':native['tracks'][0]['id'],'plugin':PLUGIN_ID})],
                          d/'probe/session.scraft',d/'default.scraft',d)
        defaults = json.loads((d/'default.scraft').read_text())['tracks'][0]['instrument']['params']
        stage = d/'publish';stage.mkdir()
        for voice,role in ROLES.items():
            request = d/(voice+'.json')
            write(request,{'voice':voice,'job':{'plugin':str(a.external.plugin),'defaults':defaults,'role':role,
                  'modulation':modulation,'volume_db':None,'out':str(stage/voice)}})
            a.external.call([str(Path(host_python).absolute()),str(ROOT/'tools/phase16_patch_worker.py'),str(request)],ROOT)
            read_patch(stage/voice)
        dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir()
        try:
            for item in stage.iterdir():shutil.move(str(item),dest/item.name)
        except BaseException:shutil.rmtree(dest);raise
    return {'patches':str(dest),'actual_two_instance_state_readback':True,'pitch_gate_still_required':True}

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for flag in ('out-dir','soundcraft','plugin','host-python'):ap.add_argument('--'+flag,required=True)
    ap.add_argument('--modulation-off',action='store_true');z=ap.parse_args()
    print(json.dumps(prepare(z.out_dir,z.soundcraft,z.plugin,z.host_python,modulation=not z.modulation_off),indent=2))
