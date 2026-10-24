#!/usr/bin/env python3
"""Real multi-register tuning gate for the rejected palette and opt-in repair.

Every pitch is an isolated dry held note; no track FX, sends, note overlaps or
transposition. Native component state and771 synth controls remain identical;
the fixed backend initializes the proven synthetic MIDI pitch-bend slot to.5.
"""
import argparse,json,sys
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.production_host import ProductionAdapter
from kuang.schema import load,Clip,Note,BAR
from kuang.pitch_audio import note_pitch,spectrum,hz,cents
from kuang.sample_assets import write,digest
from kuang.gestures import crop
from kuang.external_synth import read_patch

CASES={'lead':('track-lead',[67,65,63]),'bass':('track-bass',[36,43]),'stab':('track-harmony',[51,55,58,62]),'pad':('track-depth-pad',[60])}
ON=.5*60/126
WINDOWS=[(.10,.50),(.50,.90),(.90,1.30)]


def held(source,tid,pitches):
    p=ProductionAdapter._plain(source);q=crop(p,32,1,[tid]);t=q.tracks[0]
    t.instrument=deepcopy(next(t for t in source.tracks if t.id==tid).instrument);t.effects=[];t.sends=[];t.output_master=True
    t.controls={'mixer.gain_db':-18,'mixer.pan':0,'mixer.mute':0};q.automation=[];q.locks=[]
    t.clips=[Clip('pitch-clip','Isolated held pitch calibration','midi',0,BAR,[Note('pitch-note-'+str(i),480,2880,n,96,0) for i,n in enumerate(pitches)],None)]
    return q


def gate(destination,executable,plugin):
    out=Path(destination).resolve()
    if out.exists() or not out.is_relative_to(ROOT/'.local/phase15'):raise ValueError('new project-local pitch gate required')
    out.mkdir();a=ProductionAdapter(executable,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase15/tmp',center_pitch_bend=True)
    source=load(ROOT/'artifacts/phase14-house/B/project.kuang.json');report={}
    for role,(tid,pitches) in CASES.items():
        for note in pitches:
            name=f'{role}-{note}';p=held(source,tid,[note]);patches={tid:ROOT/'artifacts/phase14-house/B/native/patches'/tid}
            a.export(p,{},patches,out/name);a.render(out/name,out/(name+'.wav'))
            report[name]=[note_pitch(out/(name+'.wav'),note,ON+u,ON+v) for u,v in WINDOWS]
            if any(abs(x['fft_cents'])>20 or abs(x['period_cents'])>8 or x['period_correlation']<.7 for x in report[name]):raise ValueError('corrected pitch gate failed '+name)
            print(name,[(round(x['fft_cents'],3),round(x['period_cents'],3)) for x in report[name]],flush=True)
    # Four-note Cm9 upper voicing, tested as a chord, not four independent shells.
    chord=[51,55,58,62];p=held(source,'track-harmony',chord)
    a.export(p,{}, {'track-harmony':ROOT/'artifacts/phase14-house/B/native/patches/track-harmony'},out/'chord');a.render(out/'chord',out/'chord.wav')
    peaks=spectrum(out/'chord.wav',ON+.5,ON+.9)[2][:40]
    chord_result=[{'midi':n,'nearest_peak_cents':min(abs(cents(x['hz'],hz(n))) for x in peaks)} for n in chord]
    if any(x['nearest_peak_cents']>20 for x in chord_result):raise ValueError('chord voicing tuning failed')
    write(out/'verification.json',{'version':'phase15-pitch-gate-1','native_corrected':report,'chord':chord_result,
        'capabilities':a.capabilities(),'thresholds':{'fft_cents':20,'autocorrelation_cents':8,'minimum_period_correlation':.7},
        'MIDI_transposition':False,'synth_patch_state_modified':False,'workaround':'initialize native synthetic MIDI pitch input1835232641 to normalized.5; keep bend range2',
        'human_quality_claim':False})
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out-dir',required=True);ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);a=ap.parse_args();gate(a.out_dir,a.soundcraft,a.plugin)
