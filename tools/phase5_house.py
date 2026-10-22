#!/usr/bin/env python3
"""Build one reproducible house-loop experiment and a private audition package.

All files remain inside this checkout. --symbolic needs only Python; full proof
uses the explicitly selected installed SoundCraft and an unchanged Phase 4 bundle.
Optional user reference is private, attributed, and excluded from the download ZIP.
"""

import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
import wave
import zipfile
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from kuang.audio import analyze_wav, compare_wavs
from kuang.groove import GROOVE_VERSION, house_loop
from kuang.groove_audio import low_end_interaction, stem_sum_error, transient_metrics
from kuang.midi import export
from kuang.production_audio import production_metrics
from kuang.schema import ValidationError, dumps, load, save, state_hash, targets
from kuang.soundcraft import SoundCraftAdapter
from tools.phase4_reference import excerpt

STEMS = {"kick":['track-kick'],"bass":['track-bass'],
         "drums":['track-snare','track-hats','track-percussion'],
         "music":['track-harmony','track-lead','track-arp']}


def write(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')


def project_path(path):
    path = Path(path).expanduser()
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise ValidationError('Phase 5 paths must be inside Kuang, without a final symlink')
    return path.resolve()


def inventory(roots):
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for r in roots for p in sorted(r.rglob('*')) if p.is_file()}


def subset(project, ids):
    q = deepcopy(project)
    q.tracks = [t for t in q.tracks if t.id in ids]
    owners = targets(q)
    q.automation = [a for a in q.automation if a.target_id in owners]
    return q


def checked_audio(path):
    a = analyze_wav(path)
    if not a['non_silent'] or a['rms'] <= 1e-6 or a['peak'] >= 1 or a['clipped_samples']:
        raise ValidationError('failed non-silence/clipping check: '+str(path))
    return a


def timing(project):
    tick_ms = 60000/(project.tempo_bpm*project.ppq)
    result = {}
    for t in project.tracks:
        notes = [n for c in t.clips for n in c.notes]
        result[t.id] = {'notes':len(notes),'velocity_min':min(n.velocity for n in notes),
            'velocity_max':max(n.velocity for n in notes),
            'sixteenth_delay_ms':sorted({round(n.start%(project.ppq//4)*tick_ms,4) for n in notes})}
    return result


def build(destination, *, seed=29, executable=None, baseline=None, reference=None, credit=None, license_text=None, reference_start=0):
    raw = Path(destination).expanduser()
    if raw.is_symlink() or raw.exists():
        raise ValidationError('output already exists; new paths only')
    destination = project_path(raw)
    reference = project_path(reference) if reference else None
    if reference and (not executable or not credit or not license_text):
        raise ValidationError('reference requires native build, --reference-credit and --reference-license')
    if type(reference_start) not in (int,float) or not math.isfinite(reference_start) or reference_start < 0:
        raise ValidationError('reference start must be finite and nonnegative')
    baseline = project_path(baseline or ROOT/'artifacts/phase4-house-reference/B-refined') if executable else None
    roots = [r for r in (baseline,ROOT/'examples',ROOT/'artifacts/phase2-house-final',ROOT/'artifacts/phase3-house-release') if r and r.exists()]
    if any(destination.is_relative_to(r) for r in roots):
        raise ValidationError('output must be outside preserved sources')
    before = inventory(roots)
    ref_hash = hashlib.sha256(reference.read_bytes()).hexdigest() if reference else None
    p = house_loop(seed)
    scratch = ROOT/'.local/phase5'
    scratch.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='audition-',dir=scratch) as directory:
        stage = Path(directory)/'publish';stage.mkdir()
        save(p,stage/'project.kuang.json');export(p,stage/'song.mid')
        write(stage/'song-spec.json',json.loads(p.metadata['song_spec']))
        report = {'version':'1','experiment':GROOVE_VERSION,'canonical_hash':state_hash(p),
            'listening_performed':False,'club_quality_established':False,'timing':timing(p),
            'reference':None,'native_verified':False,'sources_unchanged':False}
        gate = ROOT/'artifacts/phase5-house-proof/surge-gate.json'
        if gate.is_file():
            shutil.copyfile(gate,stage/'surge-gate.json')
            report['surge_gate'] = 'surge-gate.json'
        else:
            report['surge_gate'] = 'not run on this machine; built-ins selected'
        if executable:
            a = SoundCraftAdapter(executable,timeout=120)
            original = load(baseline/'project.kuang.json')
            if dumps(a.import_project(baseline/'native')) != dumps(original):
                raise ValidationError('baseline parent/native canonical mismatch')
            a.export(p,stage/'native');a.save(stage/'native',stage/'saved-native')
            n = a.inspect(stage/'native')['native']
            if a.inspect(stage/'saved-native')['native'] != n or dumps(a.import_project(stage/'native')) != dumps(p):
                raise ValidationError('full canonical/native save/reopen mismatch')
            a.render(stage/'native',stage/'candidate.wav')
            # Fresh baseline bounce also tests that the preserved bundle remains usable.
            a.render(baseline/'native',stage/'phase4-baseline.wav')
            stems = stage/'stems';stems.mkdir()
            for name,ids in STEMS.items():
                a.export(subset(p,ids),stems/(name+'-native'))
                a.render(stems/(name+'-native'),stems/(name+'.wav'))
                checked_audio(stems/(name+'.wav'))
            recombine = stem_sum_error(stage/'candidate.wav',[stems/(name+'.wav') for name in STEMS])
            if recombine['peak_error_lsb'] > 5:
                raise ValidationError('independent stems did not recombine within 24-bit quantization tolerance')
            regions = [(s.name.lower(),s.start/p.ppq*60/p.tempo_bpm,(s.start+s.length)/p.ppq*60/p.tempo_bpm) for s in p.sections]
            metrics = {}
            for name in ('phase4-baseline','candidate'):
                checked_audio(stage/(name+'.wav'))
                metrics[name] = production_metrics(stage/(name+'.wav'),regions)
            stem_metrics = {name:{'audio':checked_audio(stems/(name+'.wav')),
                                 'transients':transient_metrics(stems/(name+'.wav'))} for name in STEMS}
            matched = stage/'listening';matched.mkdir()
            target = min(m['rms'] for m in metrics.values())
            match = {}
            for name in ('phase4-baseline','candidate'):
                gain = target/metrics[name]['rms']
                excerpt(stage/(name+'.wav'),matched/(name+'-matched.wav'),0,metrics[name]['frames'],gain)
                match[name] = {'gain_db':20*math.log10(gain),'audio':checked_audio(matched/(name+'-matched.wav'))}
            # Four steady bars, exact PCM slice; no synthetic crossfade or added mastering.
            start,end = (round(beat*48000*60/126) for beat in (32,48))
            excerpt(matched/'candidate-matched.wav',matched/'candidate-4bar-loop.wav',start,end)
            with wave.open(str(matched/'candidate-4bar-loop.wav'),'rb') as wav:
                width=wav.getsampwidth();channels=wav.getnchannels()
                first=wav.readframes(1);wav.setpos(wav.getnframes()-1);last=wav.readframes(1)
                jump=max(abs(int.from_bytes(first[i*width:(i+1)*width],'little',signed=True)-
                             int.from_bytes(last[i*width:(i+1)*width],'little',signed=True)) for i in range(channels))/(1 << (width*8-1))
            report['loop_segment']={'start_beat':32,'end_beat':48,'crossfade':False,
                                    'boundary_sample_jump_peak':jump,'audio':checked_audio(matched/'candidate-4bar-loop.wav')}
            if reference:
                r = production_metrics(reference)
                duration=metrics['candidate']['duration_seconds']
                if r['duration_seconds'] < reference_start+duration:
                    raise ValidationError('reference must cover the complete comparison duration')
                private=stage/'private-reference';private.mkdir()
                start=round(reference_start*r['sample_rate']);end=start+round(duration*r['sample_rate'])
                excerpt(reference,private/'reference-excerpt.wav',start,end)
                measured=checked_audio(private/'reference-excerpt.wav')
                target_ref=min(measured['rms'],metrics['candidate']['rms'])
                excerpt(private/'reference-excerpt.wav',private/'reference-matched.wav',0,measured['frames'],target_ref/measured['rms'])
                excerpt(stage/'candidate.wav',private/'candidate-matched.wav',0,metrics['candidate']['frames'],target_ref/metrics['candidate']['rms'])
                report['reference'] = {'path':str(reference.relative_to(ROOT)),'sha256':ref_hash,
                    'credit':credit,'declared_license':license_text,'metrics':r,'professional_status':'user supplied; not independently established'}
                report['reference'].update(start_seconds=reference_start,excerpt_metrics=measured,
                    matched={name:checked_audio(private/(name+'-matched.wav')) for name in ('reference','candidate')})
                # User reference remains private; never add it to the downloadable ZIP.
            text = ('Kuang Phase 5 listening experiment\n\nA: phase4-baseline-matched.wav\nB: candidate-matched.wav\n'
                    'Both are stereo 48 kHz / 24-bit PCM at equal full-file RMS. RMS matching is not LUFS matching.\n'
                    'candidate-4bar-loop.wav is bars 9-12 cut from B without crossfade.\n'
                    'Editable native/canonical session and MIDI are in editable/. Keep the native manifest beside session.scraft.\n'
                    'No independent professional reference was licensed/downloaded. No club-quality claim.\n'
                    'Original Kuang composition; MIT. No plugin binaries, samples or third-party reference audio included.\n')
            (matched/'README.txt').write_text(text)
            write(matched/'levels.json',match)
            report.update(native_verified=True,capabilities=a.capabilities(p),metrics=metrics,stem_metrics=stem_metrics,
                stem_recombination=recombine,low_end=low_end_interaction(stems/'kick.wav',stems/'bass.wav'),
                rms_matching=match,aligned_difference=compare_wavs(stage/'phase4-baseline.wav',stage/'candidate.wav'),
                download='phase5-house-listening.zip',native_session='native/session.scraft')
            # Native reports carry published locations; canonical/native hashes do not change.
            for f in stage.rglob('report.json'):
                v=json.loads(f.read_text())
                if isinstance(v.get('output'),str): v['output']=v['output'].replace(str(stage),str(destination),1)
                write(f,v)
            archive = stage/'phase5-house-listening.zip'
            with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
                for f in sorted(matched.iterdir()): z.write(f,f.name)
                for f in sorted((stage/'native').iterdir()):
                    if f.is_file(): z.write(f,'editable/native/'+f.name)
                for name in ('project.kuang.json','song.mid','song-spec.json'):
                    z.write(stage/name,'editable/'+name)
                z.write(ROOT/'LICENSE','editable/LICENSE')
            with zipfile.ZipFile(archive) as z:
                if z.testzip() is not None: raise ValidationError('listening ZIP integrity failure')
        after = inventory(roots)
        if before != after or (reference and hashlib.sha256(reference.read_bytes()).hexdigest() != ref_hash):
            raise ValidationError('source files changed during production')
        report.update(sources_unchanged=True,source_before=before,source_after=after,artifact_sha256={
            str(f.relative_to(stage)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(stage.rglob('*')) if f.is_file()})
        write(stage/'verification.json',report)
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.mkdir()  # Atomic reservation; preserve even racing empty directories.
        try:
            for child in stage.iterdir(): child.rename(destination/child.name)
        except BaseException:
            shutil.rmtree(destination)
            raise
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--symbolic',action='store_true')
    mode.add_argument('--soundcraft')
    parser.add_argument('--seed',type=int,default=29)
    parser.add_argument('--baseline',default=str(ROOT/'artifacts/phase4-house-reference/B-refined'))
    parser.add_argument('--reference',help='private user-supplied stereo integer PCM WAV inside Kuang; never redistributed')
    parser.add_argument('--reference-credit')
    parser.add_argument('--reference-license')
    parser.add_argument('--reference-start',type=float,default=0,help='seconds into user reference; no resampling or time stretching')
    args=parser.parse_args()
    result=build(args.out_dir,seed=args.seed,executable=args.soundcraft,baseline=args.baseline,
                 reference=args.reference,credit=args.reference_credit,license_text=args.reference_license,reference_start=args.reference_start)
    print(json.dumps({'canonical_hash':result['canonical_hash'],'native_verified':result['native_verified'],
                      'report':str(Path(args.out_dir)/'verification.json')},indent=2))
