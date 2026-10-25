#!/usr/bin/env python3
"""Independent same-performance stem/context and causal timbre controls.

Internal diagnostic WAVs are intentionally excluded from the listening ZIP.
Full stems include running-song FX history; shorter ON/OFF probes reset DSP in
both paths and explicitly clip boundary notes. Neither is a preference score.
"""
import argparse
import json
import math
import sys
import wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load
from kuang.studio_palette import TRACKS
from kuang.ensemble_production import isolate
from kuang.gestures import crop
from kuang.external_synth import bound_project
from kuang.production_audio import _decode
from kuang.lowend_audio import band_metrics
from kuang.audio import analyze_wav,compare_wavs
from kuang.sample_assets import write,digest
from tools.phase16_house import adapter,END


def rms(path,first,last):
    with wave.open(str(path),'rb') as w:
        rate=w.getframerate();w.setpos(round(first*rate));count=round((last-first)*rate)
        frames=_decode(w.readframes(count),w.getsampwidth(),w.getnchannels())
        return math.sqrt(sum(x*x for row in frames for x in row)/(count*2))


def diagnostics(root,host,plugin,mod_off,warp_report,pitch_folder):
    root=Path(root);out=root/'internal-controls'
    if out.exists():raise ValueError('new diagnostic directory required')
    out.mkdir();a=adapter(host,plugin);p=load(root/'A/project.kuang.json');q=load(root/'B/project.kuang.json')
    patches={t:root/'B/native/patches'/t for t in TRACKS};mod_off=Path(mod_off)
    first,last=32*4*60/126,40*4*60/126;roles={};causal={};onsets={}
    for tid,voice in TRACKS.items():
        roles[voice]={}
        for label,project in [('A',p),('B',q)]:
            name=label+'-'+voice;wav=out/(name+'.wav');stem=isolate(project,{tid})
            a.export(stem,{},{} if label=='A' else {tid:patches[tid]},out/name)
            a.render(out/name,wav,end_seconds=END)
            roles[voice][label]={'drop_rms_dbfs':20*math.log10(rms(wav,first,last)),
                   'bands':band_metrics(wav,first=first,last=last,windows=16),'audio':analyze_wav(wav),'sha256':digest(wav)}
        delta=roles[voice]['B']['drop_rms_dbfs']-roles[voice]['A']['drop_rms_dbfs']
        target=.5 if voice=='stab' else 0
        if abs(delta-target)>.15:raise ValueError('role level calibration drift '+voice+' '+str(delta))
        # Same input/FX/fader in both paths, just matrix connections off.
        stem=isolate(q,{tid});probe=crop(stem,32,8,[t.id for t in stem.tracks])
        off=bound_project(probe,{tid:mod_off/voice})
        for label,project,patch in [('on',probe,patches[tid]),('off',off,mod_off/voice)]:
            name=voice+'-matrix-'+label
            a.export(project,{}, {tid:patch},out/name);a.render(out/name,out/(name+'.wav'))
        causal[voice]=compare_wavs(out/(voice+'-matrix-off.wav'),out/(voice+'-matrix-on.wav'))
        if causal[voice]['difference_to_original_rms_ratio']<.02:raise ValueError('inert timbral matrix '+voice)
        # Actual controlled dry first C2, not an onset guessed from full-mix FFT.
        path=Path(pitch_folder)/(voice+'-native.wav')
        with wave.open(str(path),'rb') as w:
            frames=list(_decode(w.readframes(round(1.5*w.getframerate())),w.getsampwidth(),w.getnchannels()));rate=w.getframerate()
        peak=max(abs(v) for row in frames for v in row);threshold=peak*.01
        crossing=next(i for i,row in enumerate(frames) if max(abs(v) for v in row)>=threshold)
        onsets[voice]={'first_C2_input_seconds':.5*60/126,'first_1percent_peak_seconds':crossing/rate,
                       'delay_ms_including_intended_amp_attack':1000*(crossing/rate-.5*60/126),
                       'threshold_relative_to_local_peak':.01,'intentional_pad_attack_ms':420 if voice=='pad' else None}
        print(voice,'drop delta',round(delta,5),'matrix difference',causal[voice]['difference_to_original_rms_ratio'],flush=True)
    lead_margin={label:roles['lead'][label]['drop_rms_dbfs']-roles['stab'][label]['drop_rms_dbfs'] for label in ('A','B')}
    if lead_margin['B']<2:raise ValueError('lead hierarchy masked by stabs')
    kick={}
    for label,project in [('A',p),('B',q)]:
        stem=isolate(project,{'track-kick'});assets={'track-kick':root/label/'native/assets/track-kick'}
        a.export(stem,assets,{},out/('kick-'+label));a.render(out/('kick-'+label),out/('kick-'+label+'.wav'),end_seconds=END)
        kick[label]=digest(out/('kick-'+label+'.wav'))
    if kick['A']!=kick['B']:raise ValueError('approved kick sound/groove changed')
    result={'version':'phase16-source-context-1','roles':roles,'lead_over_stab_drop_rms_db':lead_margin,
            'same_input_matrix_on_off':causal,'one_control_warp_on_off':json.loads(Path(warp_report).read_text()),
            'dry_onset_measurements':onsets,'kick_full_PCM_exact':True,
            'diagnostic_boundary':'Full stems retain song FX history. Eight-bar matrix ON/OFF both reset DSP and clip boundary notes; not identical slices of the full bounce.',
            'quality_ranking':'No ear/preference score; human full-song judgement pending'}
    write(out/'verification.json',result);write(root/'sound-design.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for flag in ('root','soundcraft','plugin','mod-off','warp-report','pitch-folder'):ap.add_argument('--'+flag,required=True)
    z=ap.parse_args();diagnostics(z.root,z.soundcraft,z.plugin,z.mod_off,z.warp_report,z.pitch_folder)
