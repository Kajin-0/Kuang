#!/usr/bin/env python3
"""Pad preview first, then a 64-bar arrangement and one modest listening ZIP.

All paths are project-local, publication is staged/new-only, installed host is
optional, and every sound is native/editable. No external assets or inference.
"""

import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from kuang.arrangement_audio import section_spectra
from kuang.audio import compare_wavs
from kuang.depth import PAD_IDS, note_fingerprints
from kuang.house_song import (PHASE6_HASH, SONG_VERSION, activity_map, arrange_house,
                              control_changes, corrected_pads)
from kuang.midi import export
from kuang.production_audio import production_metrics
from kuang.schema import ValidationError, dumps, load, save, state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.spatial_audio import spatial_metrics
from tools.phase4_reference import excerpt
from tools.phase5_house import checked_audio, inventory, subset, write
from tools.phase6_house import pcm_prefix_equal

SCRATCH=ROOT/'.local/phase7'


def local(path):
    p=Path(path).expanduser()
    if p.is_symlink() or not p.resolve().is_relative_to(ROOT):
        raise ValidationError('Phase 7 paths must stay within Kuang, without a final symlink')
    return p.resolve()


def fresh(path):
    p=local(path)
    if p.exists():raise ValidationError('new output paths only; output already exists')
    return p


def publish(stage,destination):
    destination.parent.mkdir(parents=True,exist_ok=True);destination.mkdir()
    try:
        for f in stage.iterdir():f.rename(destination/f.name)
    except BaseException:
        shutil.rmtree(destination);raise


def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def sources(source,destination):
    roots=[ROOT/'examples']+[p for p in (ROOT/'artifacts/phase5-house',ROOT/'artifacts/phase6-house',source)
                              if p and p.exists()]
    roots=list(dict.fromkeys(roots))
    if any(destination.is_relative_to(r) for r in roots):
        raise ValidationError('output must be outside preserved input directories')
    return roots,inventory(roots)


def symbolic(p,stage):
    save(p,stage/'project.kuang.json');export(p,stage/'song.mid')
    # This remains the valid 16-bar originating SongSpec, labelled as source.
    write(stage/'source-song-spec.json',json.loads(p.metadata['song_spec']))


def bounce(a,p,bundle,wav,end):
    a.export(p,bundle);a.render(bundle,wav,end_seconds=end)
    return checked_audio(wav)


def finish(stage,dest,roots,before,report):
    after=inventory(roots)
    if before!=after:raise ValidationError('preserved input files changed')
    for f in stage.rglob('report.json'):
        value=json.loads(f.read_text())
        if isinstance(value.get('output'),str):value['output']=value['output'].replace(str(stage),str(dest),1)
        write(f,value)
    report.update(sources_unchanged=True,source_before=before,source_after=after,artifact_sha256=hashes(stage))
    write(stage/'verification.json',report);publish(stage,dest)
    return report


def pad_preview(destination,*,executable=None,source=None):
    dest=fresh(destination)
    source=local(source or ROOT/'artifacts/phase6-house') if executable or source else None
    roots,before=sources(source,dest)
    old=load(source/'project.kuang.json') if source else None
    p=corrected_pads(old)
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pads-',dir=SCRATCH) as temp:
        stage=Path(temp)/'publish';stage.mkdir();symbolic(p,stage)
        if old is None:
            from kuang.depth import depth_house
            old=depth_house()
        report={'phase':7,'part':'pad-preview','canonical_hash':state_hash(p),'source_hash':PHASE6_HASH,
                'control_changes':control_changes(old,p),'same_midi':note_fingerprints(old)==note_fingerprints(p),
                'native_verified':False,'human_listening':False,'quality_established':False}
        if executable:
            print('Rendering unchanged 16-bar pad comparison',flush=True)
            a=SoundCraftAdapter(executable,timeout=180)
            if dumps(a.import_project(source/'native'))!=dumps(old):raise ValidationError('Phase 6 native drift')
            end=p.length/p.ppq*60/p.tempo_bpm+5
            a.render(source/'native',stage/'A-phase6-old-pads.wav',end_seconds=end)
            if not pcm_prefix_equal(source/'B-phase6-depth.wav',stage/'A-phase6-old-pads.wav'):
                raise ValidationError('Phase 6 baseline PCM changed')
            bounce(a,p,stage/'native',stage/'B-phase7-corrected-pads.wav',end)
            a.save(stage/'native',stage/'saved-native')
            if a.inspect(stage/'native')['native']!=a.inspect(stage/'saved-native')['native']:
                raise ValidationError('corrected pad native roundtrip failed')
            stems=stage/'stems';stems.mkdir();balance={}
            for label,project,ids in (('A-pads',old,PAD_IDS),('B-pads',p,PAD_IDS),
                    ('B-lead',p,['track-lead']),('B-music',p,['track-harmony','track-lead','track-arp']),
                    ('B-drums',p,['track-kick','track-snare','track-hats','track-percussion'])):
                balance[label]=bounce(a,subset(project,ids),stems/(label+'-native'),stems/(label+'.wav'),end)
            dry=deepcopy(p)
            for t in dry.tracks:
                if t.id in PAD_IDS:t.effects[-1].parameters['effect.wet']=0
            controls=stage/'controls';controls.mkdir()
            deltas={}
            for label,project,reference in (('wet-dry-context',dry,stage/'B-phase7-corrected-pads.wav'),
                ('wet-dry-pads',subset(dry,PAD_IDS),stems/'B-pads.wav')):
                bounce(a,project,controls/(label+'-native'),controls/(label+'.wav'),end)
                delta=compare_wavs(reference,controls/(label+'.wav'))
                if not delta['measurable_change']:raise ValidationError('pad reverb wet/dry delta too small')
                deltas[label]=delta
            metrics={n:production_metrics(stage/(n+'.wav')) for n in ('A-phase6-old-pads','B-phase7-corrected-pads')}
            spatial={n:spatial_metrics(stage/(n+'.wav')) for n in metrics}
            pad_change=balance['B-pads']['rms_dbfs']-balance['A-pads']['rms_dbfs']
            print(json.dumps({'pad_stem_change_db':pad_change,'stems':{
                k:v['rms_dbfs'] for k,v in balance.items()}},sort_keys=True),flush=True)
            if pad_change>-3:raise ValidationError('corrected pad stem did not become quieter')
            if spatial['B-phase7-corrected-pads']['bands']['low_20_120']['mono_energy_retention']<.99:
                raise ValidationError('pad correction damages low-end mono retention')
            matched=stage/'listening';matched.mkdir();levels={}
            target=min(m['rms'] for m in metrics.values())
            for name,m in metrics.items():
                gain=target/m['rms']
                full=matched/(name+'-16bars-matched.wav')
                excerpt(stage/(name+'.wav'),full,0,m['frames'],gain)
                levels[name]={'gain_db':20*math.log10(gain),'audio':checked_audio(full)}
                start,stop=(round(beat*48000*60/126) for beat in (32,48))
                excerpt(full,matched/(name+'-bars9-12-matched.wav'),start,stop)
            report.update(native_verified=True,baseline_pcm_prefix_identical=True,metrics=metrics,
                spatial=spatial,stem_balance=balance,pad_stem_change_db=pad_change,
                wet_dry=deltas,rms_matching=levels,tail_seconds=5)
        return finish(stage,dest,roots,before,report)


def song_build(destination,*,executable=None,source=None):
    dest=fresh(destination)
    source=local(source) if source else None
    if executable and not source:raise ValidationError('native song requires the verified corrected pad directory')
    roots,before=sources(source,dest)
    p=arrange_house(load(source/'project.kuang.json') if source else None)
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='song-',dir=SCRATCH) as temp:
        stage=Path(temp)/'publish';stage.mkdir();symbolic(p,stage)
        write(stage/'arrangement.json',json.loads(p.metadata['arrangement_spec']))
        write(stage/'activity.json',activity_map(p))
        report={'phase':7,'part':'song','version':SONG_VERSION,'canonical_hash':state_hash(p),
                'source_hash':p.metadata['arrangement_source_hash'],'native_verified':False,
                'human_listening':False,'club_ready':False,'song_spec_role':'unaltered source provenance, 16 bars'}
        if executable:
            evidence=json.loads((source/'verification.json').read_text())
            corrected=load(source/'project.kuang.json')
            if not evidence.get('native_verified') or evidence['canonical_hash']!=state_hash(corrected):
                raise ValidationError('pad preview must be verified before native arrangement')
            a=SoundCraftAdapter(executable,timeout=240)
            if dumps(a.import_project(source/'native'))!=dumps(corrected):raise ValidationError('corrected source native drift')
            print('Rendering 64-bar song with six native section markers',flush=True)
            end=p.length/p.ppq*60/p.tempo_bpm+5
            bounce(a,p,stage/'native',stage/'C-phase7-house-64bars.wav',end)
            a.save(stage/'native',stage/'saved-native')
            native=a.inspect(stage/'native')['native']
            if native!=a.inspect(stage/'saved-native')['native']:raise ValidationError('song native roundtrip failed')
            regions=[(s.name,s.start/p.ppq*60/p.tempo_bpm,(s.start+s.length)/p.ppq*60/p.tempo_bpm) for s in p.sections]
            metrics=production_metrics(stage/'C-phase7-house-64bars.wav',regions)
            spectrum=section_spectra(stage/'C-phase7-house-64bars.wav',regions)
            spatial=spatial_metrics(stage/'C-phase7-house-64bars.wav')
            section=metrics['sections']
            if not section['Breakdown']['rms']<section['Main Drop']['rms']*.65:
                raise ValidationError('breakdown/drop energy contrast insufficient')
            if not section['DJ Intro']['rms']<section['Main Drop']['rms']:
                raise ValidationError('intro is not lower energy than main drop')
            if spatial['bands']['low_20_120']['mono_energy_retention']<.99 or spatial['bands']['high_over_500']['mono_energy_retention']<.7:
                raise ValidationError('song mono compatibility failed')
            if spatial['last_250ms']['rms']>10**(-65/20):raise ValidationError('song tail is truncated')
            report.update(native_verified=True,capabilities=a.capabilities(p),metrics=metrics,
                          section_spectrum=spectrum,spatial=spatial,tail_seconds=5,
                          markers=native['markers'],native_session='native/session.scraft')
        return finish(stage,dest,roots,before,report)


def package(root):
    root=local(root);archive=fresh(root/'phase7-house-listening.zip')
    pads,song=root/'pad-fix',root/'song'
    pr=json.loads((pads/'verification.json').read_text());sr=json.loads((song/'verification.json').read_text())
    if not pr['native_verified'] or not sr['native_verified']:raise ValidationError('package needs both real native proofs')
    # Verify every recorded file before publishing a download, including source
    # snapshots and native manifests. A successful old report is not authority
    # to package changed bytes.
    for directory,report in ((pads,pr),(song,sr)):
        for name,digest in report['artifact_sha256'].items():
            if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=digest:
                raise ValidationError('package source drift: '+name)
    readme=('Kuang Phase 7 — listen before judging quality\n\n'
        'A-phase6-old-pads-4bars.wav and B-phase7-corrected-pads-4bars.wav:\n'
        'identical bars 9–12 of the same 16-bar groove, matched to equal excerpt RMS by constant attenuation.\n'
        'Full 16-bar matched copies remain in the release pad-fix/listening directory outside this ZIP.\n'
        'C-phase7-house-64bars.wav: the complete new song, original native render level.\n'
        'C is NOT RMS matched against the differently arranged 16-bar A/B.\n'
        'All files stereo 48 kHz / 24-bit lossless PCM. No hidden mastering or crossfades.\n'
        'Form at 126 BPM: Intro 1–8, Groove 9–16, Build 17–24, Breakdown 25–32, Drop 33–48, Outro 49–64.\n'
        'Full song 121.905 seconds plus 5 seconds of release tail. Drop starts at 60.952 s.\n'
        'editable-song/ is the complete canonical/MIDI/native song; editable-pad-fix/ is the corrected 16-bar A/B source.\n'
        'Open native/session.scraft in SoundCraft 0.11.0, keeping all companion files together.\n'
        'Source SongSpec remains valid 16-bar provenance. arrangement.json describes the separate 64-bar expansion.\n'
        'Notes, inserts, envelopes, mixer, automation and markers are native/editable. Synth ADSR is static per track.\n'
        'No new external plugins, samples, models, downloads or paid services. Original music/core code MIT.\n'
        'Basic subtractive palette and linked stereo panners remain limitations. No human listening test or club/pro claim.\n')
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='package-',dir=SCRATCH) as temp:
        stage=Path(temp);zpath=stage/'listening.zip'
        pair=[('A-phase6-old-pads-bars9-12-matched.wav','A-phase6-old-pads-4bars.wav'),
              ('B-phase7-corrected-pads-bars9-12-matched.wav','B-phase7-corrected-pads-4bars.wav')]
        measured={out:checked_audio(pads/'listening'/name) for name,out in pair}
        target=min(v['rms'] for v in measured.values());excerpt_levels={}
        for name,out in pair:
            m=measured[out];gain=target/m['rms']
            excerpt(pads/'listening'/name,stage/out,0,m['frames'],gain)
            excerpt_levels[out]={'gain_from_full_matched_excerpt_db':20*math.log10(gain),
                                'audio':checked_audio(stage/out)}
        with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for _,out in pair:z.write(stage/out,out)
            z.write(song/'C-phase7-house-64bars.wav','C-phase7-house-64bars.wav')
            z.writestr('README.txt',readme)
            z.writestr('levels.json',json.dumps({'A_B_excerpt_rms_matching':excerpt_levels,
                'A_B_full16_rms_matching':pr['rms_matching'],
                'C_native_level':sr['metrics'],'C_matched_to_A_B':False},indent=2)+'\n')
            for directory,label in ((pads,'editable-pad-fix'),(song,'editable-song')):
                for f in sorted((directory/'native').iterdir()):
                    if f.is_file():z.write(f,label+'/native/'+f.name)
                for name in ('project.kuang.json','song.mid','source-song-spec.json','arrangement.json','activity.json'):
                    if (directory/name).is_file():z.write(directory/name,label+'/'+name)
            z.write(ROOT/'LICENSE','LICENSE')
        with zipfile.ZipFile(zpath) as z:
            if z.testzip() is not None:raise ValidationError('ZIP integrity failed')
        # Exclusive creation: an existing/racing ZIP is never overwritten.
        import os
        os.link(zpath,archive)
    return {'zip':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('pads','song','package'))
    parser.add_argument('--out-dir',required=True)
    parser.add_argument('--source')
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--symbolic',action='store_true');mode.add_argument('--soundcraft')
    args=parser.parse_args()
    if args.action=='package':r=package(args.out_dir)
    elif not (args.symbolic or args.soundcraft):parser.error('pads/song require --symbolic or --soundcraft')
    else:r=(pad_preview if args.action=='pads' else song_build)(args.out_dir,source=args.source,executable=args.soundcraft)
    print(json.dumps({k:v for k,v in r.items() if k in ('canonical_hash','native_verified','zip','sha256','bytes')},indent=2))
