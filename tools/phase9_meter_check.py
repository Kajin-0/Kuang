#!/usr/bin/env python3
"""Check original synthetic recipes against frozen goldens and libebur128.

Never downloads/builds a library or rewrites test expectations. Supply a
separately installed/built MIT libebur128 1.2.6 explicitly.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from kuang.loudness import measure
from kuang.mastering import file_hash
from kuang.schema import ValidationError
from loudness_vectors import RECIPES,write_vector
from tools.phase5_house import write
from tools.phase7_house import local


def check(destination,library):
    dest=local(destination);library=local(library)
    if dest.exists():raise ValidationError('new meter-check output only')
    dest.mkdir(parents=True)
    expected=json.loads((ROOT/'tests/fixtures/loudness-golden.json').read_text());vectors={}
    for name in RECIPES:
        path=dest/(name+'.wav');write_vector(path,name)
        if file_hash(path)!=expected['vectors'][name]['input_sha256']:raise ValidationError('vector generation drift')
        reference=measure(path,library=library);python=measure(path)
        for key in ('integrated_lufs','true_peak_dbtp'):
            value=expected['vectors'][name][key]
            for m in (reference,python):
                if value is None:
                    if m[key] is not None:raise ValidationError('silent/short-block meter mismatch')
                elif m[key] is None or abs(m[key]-value)>.01:raise ValidationError('meter golden mismatch')
        vectors[name]={'reference':reference,'python4':python}
        if name.startswith('tp'):
            vectors[name]['python8']=measure(path,oversample=8)
    report={'all_passed':True,'library_sha256':file_hash(library),'reference_source':expected['source_url'],
        'reference_source_tar_sha256':expected['source_tar_sha256'],'vectors':vectors,
        'tolerance_lu':.01,'tolerance_dbtp':.01,'certified':False}
    write(dest/'verification.json',report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);p.add_argument('--library',required=True)
    args=p.parse_args();r=check(args.out_dir,args.library);print(json.dumps({'all_passed':r['all_passed'],'vectors':len(r['vectors'])}))
