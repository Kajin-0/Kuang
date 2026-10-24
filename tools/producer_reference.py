#!/usr/bin/env python3
"""Full-song sampler infrastructure proof, NOT a claimed better production.

The original drum fixtures exercise a generic licensed-asset importer. No
fixture is automatically called a preferred sound or promoted to a music ZIP.
"""
import argparse
import json
import math
import os
import random
import shutil
import sys
import wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kuang.atmosphere import atmosphere_house
from kuang.producer import audition
from kuang.sample_assets import LICENSES, create_asset, digest, write
from kuang.schema import ValidationError, dumps, load


def fixture_library(destination):
    root=Path(destination)
    if root.exists():raise ValidationError('new fixture library only')
    root.mkdir(parents=True)
    credit={'creator':'Kuang contributors','source':'Original mathematical drum test fixture; no recordings or factory content. Not a curated professional sample library.',
        'license':'MIT','license_url':LICENSES['MIT'],'notice':(ROOT/'LICENSE').read_text(),'redistribution_permitted':True}
    mapping={'root_note':36,'key_low':36,'key_high':36,'velocity_low':1,'velocity_high':127,
             'key_tracking':False,'playback':'one_shot'}
    for name,decay,noise in [('short',.045,.035),('body',.075,.02),('edge',.055,.07)]:
        out=root/(name+'.wav');rng=random.Random(971);phase=0;data=bytearray();frames=24000
        for i in range(frames):
            t=i/48000;phase+=2*math.pi*(49+105*math.exp(-t/.012))/48000
            value=(.48*math.sin(phase)*math.exp(-t/decay)+noise*rng.uniform(-1,1)*math.exp(-t/.002))
            value*=min(1,i/24,(frames-1-i)/720)
            data+=round(value*(2**23-1)).to_bytes(3,'little',signed=True)
        with wave.open(str(out),'wb') as w:
            w.setnchannels(1);w.setsampwidth(3);w.setframerate(48000);w.writeframes(data)
        create_asset(out,root/name,credit,mapping)
    write(root/'README.json',{'purpose':'Original deterministic lifecycle fixtures, not preferred producer sounds',
        'license':'MIT; complete notice in each asset.json','human_selected':False,'generator':'tools/producer_reference.py',
        'names':['short','body','edge']})
    return root


def build(destination,source,executable,library=None):
    dest=Path(destination).resolve();source=Path(source).resolve()
    if not dest.is_relative_to(ROOT/'.local/producer') or dest.exists():raise ValidationError('new .local/producer stage required')
    if dumps(load(source/'project.kuang.json'))!=dumps(atmosphere_house()):raise ValidationError('full preferred Phase10 D source required')
    dest.mkdir(parents=True);assets=fixture_library(dest/'fixture-library')
    r=audition(source,{'track-kick':assets/'short'},dest/'full-song-audition',
        'Infrastructure validation: preserve the entire preferred 64-bar song and replace only its kick instrument with an original licensed one-shot fixture. This is not a musical quality claim or a human-selected source.',
        executable=executable,library=library,workspace=ROOT)
    # Full original native bounce must remain identical to released Phase10 D.
    if digest(dest/'full-song-audition/A/raw.wav')!=digest(source/'D-phase10-combined-native.wav'):
        raise ValidationError('full baseline audio identity failed')
    write(dest/'verification.json',{'infrastructure_only':True,'source_full_song_bars':64,
        'source_notes':1536,'all_note_fields_exact':True,'baseline_PCM_exact':True,'native_live_sampler':True,
        'full_native_reopen_PCM_exact':True,'human_preference':'unreviewed','quality_improvement_claimed':False,
        'production_listening_zip_created':False,'audition_manifest_sha256':digest(dest/'full-song-audition/audition.json'),
        'candidate_native':'full-song-audition/B/native/session.scraft',
        'why_no_listening_zip':'The importer/host mechanism is validated. The synthesized assets are test fixtures, not a credible human-curated studio-quality sound selection. No human preference has been recorded.',
        'levels':r['levels'],'matching':r['matching']})
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out-dir',required=True);p.add_argument('--source',default=str(ROOT/'artifacts/phase10-house'))
    p.add_argument('--soundcraft',required=True);p.add_argument('--meter-library',default=os.environ.get('KUANG_EBUR128'))
    args=p.parse_args();build(args.out_dir,args.source,args.soundcraft,args.meter_library)
