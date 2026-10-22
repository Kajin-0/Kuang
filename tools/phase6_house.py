#!/usr/bin/env python3
"""Extend the exact Phase 5 source with editable depth; staged new outputs only.

--symbolic can reproduce the source without host/artifacts. A native proof needs
the unchanged Phase 5 bundle, installed SoundCraft and no downloaded component.
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

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from kuang.audio import compare_wavs
from kuang.depth import DEPTH_VERSION, PAD_IDS, SOURCE_HASH, depth_house, note_fingerprints
from kuang.groove import house_loop
from kuang.groove_audio import low_end_interaction, stem_sum_error
from kuang.midi import export
from kuang.production_audio import production_metrics
from kuang.schema import ValidationError, dumps, load, save, state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.spatial_audio import spatial_metrics
from tools.phase4_reference import excerpt
from tools.phase5_house import checked_audio, inventory, subset, write

STEMS={'kick':['track-kick'],'bass':['track-bass'],
       'drums':['track-snare','track-hats','track-percussion'],
       'original-music':['track-harmony','track-lead','track-arp'],
       'pad':[PAD_IDS[0]],'air':[PAD_IDS[1]]}


def local_path(path):
    path=Path(path).expanduser()
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise ValidationError('Phase 6 paths must be inside Kuang, without a final symlink')
    return path.resolve()


def control(project, mode):
    """Same MIDI and devices; only explicitly listed scalar/lane changes."""
    q=deepcopy(project)
    for t in q.tracks:
        for e in t.effects:
            if mode=='reverb-dry' and (t.id in PAD_IDS or e.id in
                    ('effect-depth-lead-plate','effect-harmony-room')) and e.plugin_ref.endswith('reverb'):
                e.parameters['effect.wet']=0
            if (mode=='mod-depth-zero' and t.id in PAD_IDS and e.plugin_ref in
                    ('soundcraft:chorus','soundcraft:phaser')):
                e.parameters['soundcraft.depth']=0
    if mode=='filter-static':
        for lane in q.automation:
            if lane.id in ('depth-pad-filter','depth-air-filter'):
                for point in lane.points:
                    point.value=9000 if 'air' in lane.id else 4000
    elif mode not in ('reverb-dry','mod-depth-zero'):
        raise ValidationError('unknown control render')
    if note_fingerprints(q)!=note_fingerprints(project):
        raise ValidationError('control changed its MIDI input')
    return q


def pcm_prefix_equal(old,new):
    """Fresh baseline must equal every historical PCM frame, including its tail."""
    with wave.open(str(old),'rb') as a,wave.open(str(new),'rb') as b:
        if a.getparams()[:3]!=b.getparams()[:3] or a.getnframes()>b.getnframes():
            return False
        while data:=a.readframes(65536):
            if data!=b.readframes(len(data)//(a.getnchannels()*a.getsampwidth())):
                return False
    return True


def render_bundle(adapter,project,bundle,wav,end):
    adapter.export(project,bundle)
    adapter.render(bundle,wav,end_seconds=end)
    return checked_audio(wav)


def build(destination, *, executable=None, source=None):
    raw=Path(destination).expanduser()
    if raw.is_symlink() or raw.exists():
        raise ValidationError('output already exists; new paths only')
    destination=local_path(raw)
    source=local_path(source or ROOT/'artifacts/phase5-house') if executable or source else None
    roots=[ROOT/'examples']+([r for r in (ROOT/'artifacts').iterdir()
                               if r.is_dir() and not r.name.startswith('phase6')]
                           if (ROOT/'artifacts').exists() else [])
    if source and source not in roots:roots.append(source)
    if any(destination.is_relative_to(r) for r in roots):
        raise ValidationError('output must be outside preserved sources')
    before=inventory(roots)
    original=load(source/'project.kuang.json') if source else house_loop()
    p=depth_house(original)
    scratch=ROOT/'.local/phase6';scratch.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='depth-',dir=scratch) as directory:
        stage=Path(directory)/'publish';stage.mkdir()
        save(p,stage/'project.kuang.json');export(p,stage/'song.mid')
        write(stage/'song-spec.json',json.loads(p.metadata['song_spec']))
        report={'version':'1','experiment':DEPTH_VERSION,'source_hash':SOURCE_HASH,
            'canonical_hash':state_hash(p),'note_fingerprints_before':note_fingerprints(original),
            'note_fingerprints_after':note_fingerprints(p),'native_verified':False,
            'listening_performed':False,'club_quality_established':False,
            'external_plugins':'not retried; Phase 5 silent-render gate remains failed',
            'postprocessing':'native PCM only; listening copies use documented constant RMS attenuation',
            'reference':'no independently licensed professional reference; human audition required'}
        for key,value in note_fingerprints(original).items():
            if note_fingerprints(p).get(key)!=value:raise ValidationError('source notes changed')
        if executable:
            a=SoundCraftAdapter(executable,timeout=120)
            if dumps(a.import_project(source/'native'))!=dumps(original):
                raise ValidationError('source native/canonical mismatch')
            # Four seconds of identical render allowance captures slow release
            # and reverb tails in A and B; no crossfade, limiter or trim.
            end=p.length/p.ppq*60/p.tempo_bpm+4
            render_bundle(a,p,stage/'native',stage/'B-phase6-depth.wav',end)
            a.save(stage/'native',stage/'saved-native')
            native=a.inspect(stage/'native')['native']
            if native!=a.inspect(stage/'saved-native')['native'] or dumps(a.import_project(stage/'native'))!=dumps(p):
                raise ValidationError('full native/canonical roundtrip mismatch')
            a.render(source/'native',stage/'A-phase5-unchanged.wav',end_seconds=end)
            checked_audio(stage/'A-phase5-unchanged.wav')
            prefix=pcm_prefix_equal(source/'candidate.wav',stage/'A-phase5-unchanged.wav')
            if not prefix:raise ValidationError('fresh Phase 5 PCM differs from historical baseline')
            stems=stage/'stems';stems.mkdir()
            for name,ids in STEMS.items():
                render_bundle(a,subset(p,ids),stems/(name+'-native'),stems/(name+'.wav'),end)
            recombine=stem_sum_error(stage/'B-phase6-depth.wav',[stems/(n+'.wav') for n in STEMS])
            if recombine['peak_error_lsb']>6:raise ValidationError('stems failed to recombine')
            pads=subset(p,PAD_IDS)
            render_bundle(a,pads,stems/'pads-native',stems/'pads.wav',end)
            proof=stage/'controls';proof.mkdir()
            differences={}
            for mode in ('reverb-dry','mod-depth-zero','filter-static'):
                q=control(p,mode)
                scopes={'pads':subset(q,PAD_IDS)}
                if mode!='filter-static':scopes['context']=q
                for scope,variant in scopes.items():
                    name=mode+'-'+scope
                    render_bundle(a,variant,proof/(name+'-native'),proof/(name+'.wav'),end)
                    ref=stems/'pads.wav' if scope=='pads' else stage/'B-phase6-depth.wav'
                    delta=compare_wavs(ref,proof/(name+'.wav'))
                    if not delta['measurable_change'] or delta['difference_to_original_rms_ratio']<.025:
                        raise ValidationError('effect control difference too small: '+name)
                    differences[name]={'same_midi':True,'delta':delta}
            regions=[(s.name.lower(),s.start/p.ppq*60/p.tempo_bpm,
                       (s.start+s.length)/p.ppq*60/p.tempo_bpm) for s in p.sections]
            metrics={n:production_metrics(stage/(n+'.wav'),regions)
                     for n in ('A-phase5-unchanged','B-phase6-depth')}
            spatial={n:spatial_metrics(stage/(n+'.wav')) for n in metrics}
            spatial_stems={n:spatial_metrics(stems/(n+'.wav')) for n in ('kick','bass','pad','air','pads')}
            for name in ('kick','bass'):
                if spatial_stems[name]['bands']['high_over_500']['side']!=0:
                    raise ValidationError('low-end stem is not exactly mono')
            b=spatial['B-phase6-depth']
            if (b['mono_sum']['clipped'] or b['bands']['high_over_500']['mono_energy_retention']<.7
                    or b['bands']['low_20_120']['mono_energy_retention']<.99):
                raise ValidationError('mono compatibility bounds failed')
            if b['last_250ms']['rms']>10**(-65/20):
                raise ValidationError('render tail is still too loud at boundary')
            matched=stage/'listening';matched.mkdir()
            target=min(v['rms'] for v in metrics.values());levels={}
            for n,m in metrics.items():
                gain=target/m['rms']
                excerpt(stage/(n+'.wav'),matched/(n+'-matched.wav'),0,m['frames'],gain)
                levels[n]={'gain_db':20*math.log10(gain),'audio':checked_audio(matched/(n+'-matched.wav'))}
                # Identical bars 9-12, including the same timing grid.
                start,stop=(round(beat*48000*60/126) for beat in (32,48))
                excerpt(matched/(n+'-matched.wav'),matched/(n+'-bars9-12.wav'),start,stop)
            if abs(levels['A-phase5-unchanged']['audio']['rms_dbfs']-levels['B-phase6-depth']['audio']['rms_dbfs'])>1e-5:
                raise ValidationError('listening RMS match failed')
            readme=('Kuang Phase 6 depth experiment — listen before judging quality\n\n'
                'A-phase5-unchanged-matched.wav: exact Phase 5 notes, instruments, FX and mix.\n'
                'B-phase6-depth-matched.wav: same groove plus sustained ninth pad/air, reverb and native modulation.\n'
                'Full files: 16 bars at 126 BPM plus 4 seconds of release tail; aligned at sample zero.\n'
                'Stereo 48 kHz / 24-bit PCM. Same full-file RMS via constant attenuation only, not LUFS matching.\n'
                'Bars9-12 excerpts use those same gains; no separate excerpt normalization or crossfade.\n'
                'editable/ contains the complete candidate canonical, MIDI and native bundle. Keep all native files together.\n'
                'Open editable/native/session.scraft in SoundCraft 0.11.0. All notes, ADSRs, inserts and lanes are editable.\n'
                'Movement is chorus/phaser DSP and EQ LPF automation, not oscillator LFO/wavetable or ADSR automation.\n'
                'Built-in panner mapping links both stereo panners; width is measured, not assumed.\n'
                'No independent professional reference or new human listening test; no club readiness claim.\n'
                'Original Kuang music/code MIT; no samples, models, external plugins or third-party assets bundled.\n')
            (matched/'README.txt').write_text(readme);write(matched/'levels.json',levels)
            report.update(native_verified=True,capabilities=a.capabilities(p),baseline_pcm_prefix_identical=prefix,
                render_tail_seconds=4,metrics=metrics,spatial=spatial,spatial_stems=spatial_stems,
                stem_metrics={n:checked_audio(stems/(n+'.wav')) for n in (*STEMS,'pads')},
                stem_recombination=recombine,controls=differences,rms_matching=levels,
                low_end=low_end_interaction(stems/'kick.wav',stems/'bass.wav'),
                aligned_difference=compare_wavs(stage/'A-phase5-unchanged.wav',stage/'B-phase6-depth.wav'),
                download='phase6-house-listening.zip',native_session='native/session.scraft')
            for f in stage.rglob('report.json'):
                value=json.loads(f.read_text())
                if isinstance(value.get('output'),str):value['output']=value['output'].replace(str(stage),str(destination),1)
                write(f,value)
            archive=stage/'phase6-house-listening.zip'
            with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
                for f in sorted(matched.iterdir()):z.write(f,f.name)
                for f in sorted((stage/'native').iterdir()):
                    if f.is_file():z.write(f,'editable/native/'+f.name)
                for name in ('project.kuang.json','song.mid','song-spec.json'):z.write(stage/name,'editable/'+name)
                z.write(ROOT/'LICENSE','editable/LICENSE')
            with zipfile.ZipFile(archive) as z:
                if z.testzip() is not None:raise ValidationError('ZIP integrity failed')
        after=inventory(roots)
        if before!=after:raise ValidationError('preserved sources changed')
        report.update(sources_unchanged=True,source_before=before,source_after=after,
            artifact_sha256={str(f.relative_to(stage)):hashlib.sha256(f.read_bytes()).hexdigest()
                             for f in sorted(stage.rglob('*')) if f.is_file()})
        write(stage/'verification.json',report)
        destination.parent.mkdir(parents=True,exist_ok=True);destination.mkdir()
        try:
            for child in stage.iterdir():child.rename(destination/child.name)
        except BaseException:
            shutil.rmtree(destination);raise
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--symbolic',action='store_true');mode.add_argument('--soundcraft')
    parser.add_argument('--source',help='unchanged Phase 5 directory; default artifacts/phase5-house for native proof')
    args=parser.parse_args()
    r=build(args.out_dir,executable=args.soundcraft,source=args.source)
    print(json.dumps({'canonical_hash':r['canonical_hash'],'native_verified':r['native_verified'],
                      'report':str(Path(args.out_dir)/'verification.json')},indent=2))
