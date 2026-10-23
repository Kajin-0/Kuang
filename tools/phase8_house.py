#!/usr/bin/env python3
"""Reproduce the Phase 8 gestures and same-input native audio controls.

New-only, project-local staged publication. No downloads, inference or mastering.
"""

import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from kuang.audio import compare_wavs
from kuang.depth import note_fingerprints
from kuang.gesture_audio import (echo_peak_timing, echo_trails, gain_reduction_envelope,
                                 phase_gain, window_metrics)
from kuang.gestures import (HARMONICS, PADS, SOURCE_HASH, control, crop, gesture_house)
from kuang.house_song import activity_map, arrange_house
from kuang.midi import export
from kuang.production_audio import production_metrics
from kuang.schema import BAR, ValidationError, dumps, load, save, state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.spatial_audio import spatial_metrics
from tools.phase4_reference import excerpt
from tools.phase5_house import checked_audio, inventory, write
from tools.phase7_house import fresh, hashes, local, publish

SCRATCH=ROOT/'.local/phase8'


def symbolic(p, directory):
    directory.mkdir(parents=True,exist_ok=True)
    save(p,directory/'project.kuang.json');export(p,directory/'song.mid')
    write(directory/'source-song-spec.json',json.loads(p.metadata['song_spec']))
    write(directory/'arrangement.json',json.loads(p.metadata['arrangement_spec']))


def bounce(a,p,directory,*,tail=4):
    symbolic(p,directory)
    a.export(p,directory/'native')
    path=directory/'audio.wav'
    a.render(directory/'native',path,end_seconds=p.length/p.ppq*60/p.tempo_bpm+tail)
    return checked_audio(path)


def demonstrations(a,p,stage):
    """All controls retain identical MIDI/ADSR/pan and unaffected FX/lanes."""
    root=stage/'demonstrations';root.mkdir();report={}
    build=crop(p,16,8,[*HARMONICS,'track-hats','track-percussion','track-snare'])
    beat=60/126;bar=4*beat
    examples=[('filters',build,None),('hpf-static',control(build,'hpf'),'filters'),
        ('lpf-static',control(build,'lpf'),'filters')]
    # An existing final lead note, original ID/pitch/timing/velocity, exposes
    # individual tempo echoes. Other spatial FX are dry only in this diagnostic.
    delay=control(control(crop(p,12,4,['track-lead']),'reverb'),'modulation')
    last=max((c.start+n.start,n.id) for t in delay.tracks for c in t.clips for n in c.notes)[1]
    for t in delay.tracks:
        for c in t.clips:c.notes=[n for n in c.notes if n.id==last]
        t.clips=[c for c in t.clips if c.notes]
    examples += [('delay-throw',delay,None),('delay-dry',control(delay,'delay'),'delay-throw')]
    reverb=crop(p,24,4,list(PADS))
    examples += [('breakdown-reverb',reverb,None),('reverb-dry',control(reverb,'reverb'),'breakdown-reverb')]
    pump=crop(p,32,4,[*PADS,'track-harmony'])
    examples += [('drop-pump',pump,None),('duck-off',control(pump,'duck'),'drop-pump')]
    mod=control(control(crop(p,32,4,list(PADS)),'reverb'),'duck')
    examples += [('modulation',mod,None),('modulation-off',control(mod,'modulation'),'modulation')]
    # Existing local compressor, same original threshold/attack/release. Set
    # makeup to zero in BOTH diagnostic inputs to measure gain reduction alone.
    comp=control(control(crop(p,32,4,['track-harmony']),'reverb'),'modulation')
    for e in comp.tracks[0].effects:
        if e.plugin_ref=='soundcraft:compressor':e.parameters['soundcraft.makeup']=0
    bypass=deepcopy(comp)
    for e in bypass.tracks[0].effects:
        if e.plugin_ref=='soundcraft:compressor':e.parameters['effect.bypass']=1
    examples += [('compression',comp,None),('compressor-bypass',bypass,'compression')]
    for name,project,reference in examples:
        print('Native control: '+name,flush=True)
        measured=bounce(a,project,root/name)
        report[name]={'audio':measured,'canonical_hash':state_hash(project)}
        if reference:
            q=load(root/reference/'project.kuang.json')
            if note_fingerprints(project)!=note_fingerprints(q):raise ValidationError('control MIDI differs')
            delta=compare_wavs(root/reference/'audio.wav',root/name/'audio.wav')
            if not delta['measurable_change']:raise ValidationError('inert native effect: '+name)
            report[name].update(same_midi=True,difference=delta)
    windows=[('early-build',0,2*bar),('late-build',6*bar,8*bar)]
    for name in ('filters','hpf-static','lpf-static'):
        report[name]['timed_bands']=window_metrics(root/name/'audio.wav',windows)
    bands=report['filters']['timed_bands']['regions']
    hpf=report['hpf-static']['timed_bands']['regions']
    lpf=report['lpf-static']['timed_bands']['regions']
    # Actual BANDS names are kept in the report; use their frequency ranges.
    keys=list(bands['late-build']['band_mean_square'])
    low,high=keys[1],keys[3]
    filter_deltas={'late_hpf_lowmid_db':10*math.log10(bands['late-build']['band_mean_square'][low]/hpf['late-build']['band_mean_square'][low]),
        'early_lpf_high_db':10*math.log10(bands['early-build']['band_mean_square'][high]/lpf['early-build']['band_mean_square'][high])}
    if filter_deltas['late_hpf_lowmid_db']> -3 or filter_deltas['early_lpf_high_db']> -4:
        raise ValidationError('filter gestures do not change localized band power enough: '+str(filter_deltas))
    note_end=max((c.start+n.start+n.duration)/delay.ppq*60/delay.tempo_bpm for t in delay.tracks for c in t.clips for n in c.notes)
    trails=echo_trails(root/'delay-throw/audio.wav',root/'delay-dry/audio.wav',note_end,60000/126*.75)
    note_start=min((c.start+n.start)/delay.ppq*60/126 for t in delay.tracks for c in t.clips for n in c.notes)
    timing=echo_peak_timing(root/'delay-throw/audio.wav',note_start,60000/126*.75)
    if timing['max_spacing_error_ms']>10:raise ValidationError('measured echo spacing differs from tempo')
    # At least two measured echo windows exceed dry residual by 6 dB, with
    # real absolute signal. The configured delay time alone proves nothing.
    if sum(v['wet_rms']>max(1e-5,v['dry_rms']*2) for v in trails.values())<2:
        raise ValidationError('delay throw has no distinct measured rhythmic trail')
    pump_envelope=phase_gain(root/'drop-pump/audio.wav',root/'duck-off/audio.wav',first_beat=2,beats=12)
    if pump_envelope['duck']['on_off_db']> -6 or pump_envelope['open']['on_off_db']< -2:
        raise ValidationError('pump envelope insufficient: '+str(pump_envelope))
    # Reverb tail beyond the last note + synth release. A new DSP-reset native
    # render is used identically for wet/dry, not waveform tail fabrication.
    end_note=max((c.start+n.start+n.duration)/reverb.ppq*60/126 for t in reverb.tracks for c in t.clips for n in c.notes)
    region=[('released-tail',end_note+1.5,end_note+2.5)]
    tail={name:window_metrics(root/name/'audio.wav',region)['regions']['released-tail']
          for name in ('breakdown-reverb','reverb-dry')}
    if tail['breakdown-reverb']['rms']<=max(1e-6,tail['reverb-dry']['rms']*2):
        raise ValidationError('no measured reverb release tail')
    active,bypassed=(report[n]['audio'] for n in ('compression','compressor-bypass'))
    compression={'same_input_zero_makeup':True,'rms_gain_db':20*math.log10(active['rms']/bypassed['rms']),
                 'peak_gain_db':20*math.log10(active['peak']/bypassed['peak']),
                 'envelope':gain_reduction_envelope(root/'compression/audio.wav',root/'compressor-bypass/audio.wav')}
    if compression['peak_gain_db']> -1:raise ValidationError('compressor has no measured peak reduction')
    if compression['envelope']['gain_variation_db']<1:raise ValidationError('compressor envelope resembles static trim')
    return {'controls':report,'filter_deltas':filter_deltas,'delay_echo_windows':trails,
        'delay_peak_timing':timing,'pump_phase_energy':pump_envelope,'reverb_release_tail':tail,'compression':compression,
        'diagnostic_note':'Fresh native DSP-reset windows, not full-bounce slices. Same MIDI within each pair; compression makeup zero in both only for gain-reduction measurement.'}


def build(destination,*,executable=None,source=None):
    dest=fresh(destination);source=local(source) if source else None
    roots=[ROOT/'examples']+[r for r in (ROOT/'artifacts').iterdir() if r.is_dir() and r.name!='phase8-house'] if (ROOT/'artifacts').exists() else [ROOT/'examples']
    if source and not any(source.is_relative_to(r) for r in roots):roots.append(source)
    if any(dest.is_relative_to(r) for r in roots):raise ValidationError('output intersects preserved source')
    before=inventory(roots)
    old=load(source/'project.kuang.json') if source else arrange_house()
    p=gesture_house(old)
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='production-',dir=SCRATCH) as temp:
        stage=Path(temp)/'publish';stage.mkdir();symbolic(p,stage)
        write(stage/'activity.json',activity_map(p))
        report={'phase':8,'source_hash':SOURCE_HASH,'canonical_hash':state_hash(p),'native_verified':False,
            'human_listening':False,'club_ready':False,'note_deviations':json.loads(p.metadata['gesture_note_deviations']),
            'sidechain':'programmed tempo-synced native mixer gain ducking; no input-triggered routing',
            'source_note_fingerprints':note_fingerprints(old),'candidate_note_fingerprints':note_fingerprints(p)}
        if executable:
            if source is None:raise ValidationError('native build requires an exact Phase 7 source bundle')
            a=SoundCraftAdapter(executable,timeout=240)
            if dumps(a.import_project(source/'native'))!=dumps(old):raise ValidationError('Phase 7 source/native drift')
            end=p.length/p.ppq*60/p.tempo_bpm+5
            print('Rendering aligned full Phase 7 / Phase 8 song',flush=True)
            a.save(source/'native',stage/'baseline-native')
            a.render(source/'native',stage/'A-phase7-original-64bars.wav',end_seconds=end)
            original=source/'C-phase7-house-64bars.wav'
            if original.exists() and original.read_bytes()!=(stage/'A-phase7-original-64bars.wav').read_bytes():
                raise ValidationError('original Phase 7 full PCM bytes changed')
            a.export(p,stage/'native');a.render(stage/'native',stage/'B-phase8-motion-64bars.wav',end_seconds=end)
            a.save(stage/'native',stage/'saved-native')
            if a.inspect(stage/'native')['native']!=a.inspect(stage/'saved-native')['native']:
                raise ValidationError('full native save/reopen differs')
            regions=[(s.name,s.start/p.ppq*60/126,(s.start+s.length)/p.ppq*60/126) for s in p.sections]
            metrics={name:production_metrics(stage/file,regions) for name,file in (
                ('phase7','A-phase7-original-64bars.wav'),('phase8','B-phase8-motion-64bars.wav'))}
            for name in ('A-phase7-original-64bars.wav','B-phase8-motion-64bars.wav'):checked_audio(stage/name)
            spatial=spatial_metrics(stage/'B-phase8-motion-64bars.wav')
            if spatial['bands']['low_20_120']['mono_energy_retention']<.99 or spatial['bands']['high_over_500']['mono_energy_retention']<.7:
                raise ValidationError('mono safety failed')
            if spatial['last_250ms']['rms']>10**(-65/20):raise ValidationError('release tail truncated')
            if metrics['phase8']['sections']['Breakdown']['rms']>=metrics['phase8']['sections']['Main Drop']['rms']*.7:
                raise ValidationError('breakdown/drop energy contrast failed')
            report.update(native_verified=True,capabilities=a.capabilities(p),metrics=metrics,spatial=spatial,
                full_difference=compare_wavs(stage/'A-phase7-original-64bars.wav',stage/'B-phase8-motion-64bars.wav'),
                tail_seconds=5,arrangement_seconds=p.length/p.ppq*60/126)
            report['dsp']=demonstrations(a,p,stage)
            listening=stage/'listening';listening.mkdir();target=min(m['rms'] for m in metrics.values());levels={}
            for key,label,file in (('phase7','A-phase7','A-phase7-original-64bars.wav'),('phase8','B-phase8','B-phase8-motion-64bars.wav')):
                gain=target/metrics[key]['rms'];out=listening/(label+'-64bars-RMS-matched.wav')
                excerpt(stage/file,out,0,metrics[key]['frames'],gain)
                levels[label]={'gain_db':20*math.log10(gain),'audio':checked_audio(out)}
            if abs(levels['A-phase7']['audio']['rms_dbfs']-levels['B-phase8']['audio']['rms_dbfs'])>1e-4:
                raise ValidationError('full RMS matching failed')
            # Context excerpts come from the actual running full-track PCM.
            for label,first,bars in (('C-build-filter',16,8),('D-breakdown-and-drop',28,8),('E-drop-call-response',36,8)):
                excerpt(stage/'B-phase8-motion-64bars.wav',listening/(label+'.wav'),round(first*4*60/126*48000),round((first+bars)*4*60/126*48000))
            report['rms_matching']=levels
        if inventory(roots)!=before:raise ValidationError('historical source drift')
        report.update(sources_unchanged=True,source_sha256=before,artifact_sha256=hashes(stage))
        write(stage/'verification.json',report);publish(stage,dest)
    return report


def package(root):
    root=local(root);out=fresh(root/'phase8-house-listening.zip')
    report=json.loads((root/'verification.json').read_text())
    if not report['native_verified']:raise ValidationError('listening ZIP requires real native/audio proof')
    for name,digest in report['artifact_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValidationError('package source drift: '+name)
    text=('Kuang Phase 8 — same 64-bar Phase 7 song, audible production experiment\n\n'
        'A/B: aligned full songs, equal whole-file RMS by constant attenuation only. 48 kHz, stereo 24-bit PCM.\n'
        '64 bars at 126 BPM (121.905 s) plus 5 s release tail. C minor. No mastering/limiter/post-render effects.\n'
        'Form: intro 1–8; groove 9–16; build 17–24; breakdown 25–32; drop 33–48; outro 49–64.\n'
        'C/D/E are exact full-B PCM excerpts: build filters; breakdown/drop; drop call/response.\n'
        'controls/: short fresh native renders of the same MIDI per pair, original render level, NOT level matched.\n'
        'filters vs hpf-static / lpf-static: eight-bar build; static controls open HPF to 10 Hz / LPF to 20 kHz.\n'
        'delay-throw vs delay-dry: one existing phrase-ending lead note, other spatial effects dry; listen for dotted eighth echoes.\n'
        'breakdown-reverb vs reverb-dry: four-bar pad section plus tail. drop-pump vs duck-off: programmed beat gain duck.\n'
        'modulation vs modulation-off: actual chorus/phaser, no reverb or duck.\n'
        'compression vs compressor-bypass: existing stab compressor, makeup ZERO in both diagnostics to expose gain reduction.\n'
        'Gain ducking is tempo programmed, NOT a kick-input-triggered sidechain. No bus/routing or oscillator-LFO claim.\n'
        'Controls reset DSP at their window start and retain same MIDI/ADSR/pan within each pair.\n'
        'Five pre-drop percussion notes removed; every kick/bass/main-hook note and the complete original drop MIDI unchanged.\n'
        'editable-phase8/: canonical JSON, MIDI, source SongSpec (16-bar provenance), 64-bar arrangement and complete native bundle.\n'
        'Open editable-phase8/native/session.scraft with installed SoundCraft 0.11.0. Keep companions together.\n'
        'editable-phase7-native/ contains the baseline canonical/native/MIDI snapshot. Controls also have editable bundles.\n'
        'Core/original composition MIT. No third-party samples/plugins/models bundled or required.\n'
        'No human listening test performed by the agent. Technical effects evidence does not establish preference or club readiness.\n')
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='zip-',dir=SCRATCH) as temp:
        path=Path(temp)/'listening.zip'
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('README.txt',text);z.writestr('levels-and-dsp.json',json.dumps({k:report[k] for k in ('rms_matching','dsp','metrics','spatial','note_deviations')},indent=2)+'\n')
            for f in sorted((root/'listening').iterdir()):z.write(f,f.name)
            for f in sorted((root/'native').iterdir()):
                if f.is_file():z.write(f,'editable-phase8/native/'+f.name)
            for name in ('project.kuang.json','song.mid','source-song-spec.json','arrangement.json','activity.json'):
                z.write(root/name,'editable-phase8/'+name)
            for f in sorted((root/'baseline-native').iterdir()):
                if f.is_file():z.write(f,'editable-phase7-native/'+f.name)
            for f in sorted((root/'demonstrations').rglob('*')):
                if f.is_file():z.write(f,'controls/'+str(f.relative_to(root/'demonstrations')))
            z.write(ROOT/'LICENSE','LICENSE')
        with zipfile.ZipFile(path) as z:
            if z.testzip():raise ValidationError('ZIP CRC failed')
        os.link(path,out)
    result={'zip':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size}
    write(root/'download.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',required=True);parser.add_argument('--source')
    parser.add_argument('--package',action='store_true')
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--symbolic',action='store_true');mode.add_argument('--soundcraft')
    args=parser.parse_args()
    if args.package:r=package(args.out_dir)
    elif not (args.symbolic or args.soundcraft):parser.error('select --symbolic or --soundcraft')
    else:r=build(args.out_dir,executable=args.soundcraft,source=args.source)
    print(json.dumps({k:v for k,v in r.items() if k in ('canonical_hash','native_verified','zip','sha256','bytes')},indent=2))
