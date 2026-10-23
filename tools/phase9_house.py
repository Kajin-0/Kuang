#!/usr/bin/env python3
"""One editable translation mix, measured optional off-host master, one ZIP."""

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kuang.audio import compare_wavs
from kuang.depth import note_fingerprints
from kuang.gestures import crop,gesture_house
from kuang.groove_audio import low_end_interaction,stem_sum_error,transient_metrics
from kuang.loudness import measure
from kuang.lowend_audio import band_metrics
from kuang.mastering import apply_master,file_hash,match_lufs,plan_master
from kuang.midi import export
from kuang.production_audio import production_metrics
from kuang.schema import ValidationError,dumps,load,save,state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.spatial_audio import spatial_metrics
from kuang.translation import SOURCE_HASH,translation_house
from tools.phase4_reference import excerpt
from tools.phase5_house import checked_audio,inventory,write
from tools.phase7_house import hashes,local,publish

SCRATCH=ROOT/'.local/phase9'


def fresh(path):
    p=local(path)
    if p.exists():raise ValidationError('new Phase 9 output only')
    return p


def symbolic(p,dest):
    dest.mkdir(parents=True,exist_ok=True);save(p,dest/'project.kuang.json');export(p,dest/'song.mid')
    write(dest/'source-song-spec.json',json.loads(p.metadata['song_spec']))
    write(dest/'arrangement.json',json.loads(p.metadata['arrangement_spec']))


def bounce(a,p,dest):
    symbolic(p,dest);a.export(p,dest/'native');a.render(dest/'native',dest/'audio.wav',
        end_seconds=p.length/p.ppq*60/p.tempo_bpm+3)
    return checked_audio(dest/'audio.wav')


def stems(a,old,new,root):
    root.mkdir();report={};end=8*4*60/126
    for label,p in (('A',old),('B',new)):
        for role in ('kick','bass'):
            name=label+'-'+role;out=root/name;q=crop(p,32,8,['track-'+role])
            report[name]={'audio':bounce(a,q,out),'bands':band_metrics(out/'audio.wav',last=end),
                'transients':transient_metrics(out/'audio.wav',beats=32)}
        report[label+'-interaction']=low_end_interaction(root/(label+'-kick/audio.wav'),root/(label+'-bass/audio.wav'))
    q=crop(new,32,8,['track-kick','track-bass']);bounce(a,q,root/'B-low-end')
    report['B-stem-sum']=stem_sum_error(root/'B-low-end/audio.wav',
        [root/'B-kick/audio.wav',root/'B-bass/audio.wav'])
    dry=deepcopy(crop(new,32,8,['track-bass']))
    next(e for e in dry.tracks[0].effects if e.plugin_ref=='soundcraft:saturator').parameters['effect.bypass']=1
    bounce(a,dry,root/'B-bass-saturator-bypass')
    report['saturation_difference']=compare_wavs(root/'B-bass/audio.wav',root/'B-bass-saturator-bypass/audio.wav')
    if not report['saturation_difference']['measurable_change']:raise ValidationError('bass saturation is inert')
    old_b,new_b=report['A-bass'],report['B-bass']
    difference=lambda a,b:10*math.log10(b/a)
    upper=difference(old_b['bands']['band_mean_square']['harmonics_100_400'],new_b['bands']['band_mean_square']['harmonics_100_400'])
    level=new_b['audio']['rms_dbfs']-old_b['audio']['rms_dbfs']
    old_k,new_k=report['A-kick'],report['B-kick']
    transient=new_k['transients']['windows']['attack_0_20ms']['median_rms_dbfs']-old_k['transients']['windows']['attack_0_20ms']['median_rms_dbfs']
    tail=new_k['transients']['windows']['tail_100_200ms']['median_rms_dbfs']-old_k['transients']['windows']['tail_100_200ms']['median_rms_dbfs']
    if upper<3 or abs(level)>1:raise ValidationError('bass did not gain absolute harmonics at comparable level')
    if transient<1 or tail> -3:raise ValidationError('kick attack/tail contrast insufficient')
    if report['B-interaction']['interference_db']< -.5:raise ValidationError('destructive low-end interference')
    report['deltas']={'bass_absolute_100_400_db':upper,'bass_rms_change_db':level,
        'kick_attack_change_db':transient,'kick_tail_change_db':tail,
        'kick_rms_change_db':new_k['audio']['rms_dbfs']-old_k['audio']['rms_dbfs']}
    return report


def build(destination,*,source=None,executable=None,library=None):
    dest=fresh(destination);source=local(source) if source else None
    library=local(library) if library else None
    protected=[ROOT/'examples']
    if (ROOT/'artifacts').exists():
        protected += [p for p in (ROOT/'artifacts').iterdir() if p.is_dir() and p.name!='phase9-house']
    if source and not any(source.is_relative_to(p) for p in protected):protected.append(source)
    if any(dest.is_relative_to(p) for p in protected):raise ValidationError('output intersects historical inputs')
    before=inventory(protected)
    old=load(source/'project.kuang.json') if source else gesture_house();new=translation_house(old)
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='mix-',dir=SCRATCH) as d:
        stage=Path(d)/'publish';stage.mkdir();symbolic(new,stage)
        report={'phase':9,'source_hash':SOURCE_HASH,'canonical_hash':state_hash(new),
            'native_verified':False,'same_all_notes':note_fingerprints(new)==note_fingerprints(old),
            'same_all_automation':new.automation==old.automation,'note_deviations':[],
            'human_listening':False,'club_ready':False,'master_native_editable':False}
        if executable:
            if source is None:raise ValidationError('native build needs exact Phase 8 source')
            a=SoundCraftAdapter(executable,timeout=240)
            if dumps(a.import_project(source/'native'))!=dumps(old):raise ValidationError('Phase 8 source native drift')
            end=new.length/new.ppq*60/new.tempo_bpm+5
            print('Native full A/B and saved B',flush=True)
            ap,bp,cp=(stage/n for n in ('A-phase8-premaster.wav','B-phase9-premaster.wav','C-phase9-master-OFFHOST.wav'))
            a.render(source/'native',ap,end_seconds=end)
            if file_hash(ap)!=file_hash(source/'B-phase8-motion-64bars.wav'):raise ValidationError('Phase 8 reference PCM changed')
            a.export(new,stage/'native');a.render(stage/'native',bp,end_seconds=end);a.save(stage/'native',stage/'saved-native')
            if a.inspect(stage/'native')['native']!=a.inspect(stage/'saved-native')['native']:raise ValidationError('native save/reopen mismatch')
            report['stems']=stems(a,old,new,stage/'stems')
            print('Measuring native A/B and planning gentle off-host C',flush=True)
            metrics={label:measure(p,library=library) for label,p in (('A',ap),('B',bp))}
            recipe,plan=plan_master(bp,library=library);write(stage/'master-recipe.json',recipe)
            master=apply_master(bp,cp,recipe);metrics['C']=measure(cp,library=library)
            if metrics['C']['true_peak_dbtp']> -1.0:raise ValidationError('master true peak exceeds conservative ceiling')
            if not .05<master['maximum_reduction_db']<3:raise ValidationError('master compression is inert or excessive')
            for m in metrics.values():
                if m['integrated_lufs'] is None or m['clipped_samples'] or m['sample_peak']>=1:raise ValidationError('bad PCM')
                if m['frames']!=metrics['A']['frames']:raise ValidationError('unaligned full A/B/C')
            print('Integrated-LUFS audition matching',flush=True)
            listening=stage/'listening';listening.mkdir();target=min(m['integrated_lufs'] for m in metrics.values());matching={}
            for label,path in (('A',ap),('B',bp),('C',cp)):
                matching[label]=match_lufs(path,listening/(label+'-full-LUFS-matched.wav'),target,library=library)
            # Eight-bar comparisons are matched again locally, rather than
            # assuming whole-program loudness matching also matches the drop.
            drop=stage/'drop';drop.mkdir();drop_meters={}
            for label,path in (('A',ap),('B',bp),('C',cp)):
                out=drop/(label+'-drop-native-level.wav')
                excerpt(path,out,round(32*4*60/126*48000),round(40*4*60/126*48000))
                drop_meters[label]=measure(out,library=library)
            drop_target=min(m['integrated_lufs'] for m in drop_meters.values());drop_matching={}
            for label in ('A','B','C'):
                drop_matching[label]=match_lufs(drop/(label+'-drop-native-level.wav'),
                    listening/(label+'-drop8-LUFS-matched.wav'),drop_target,library=library)
            print('Spatial, band, section and 8x true-peak audits',flush=True)
            spatial={label:spatial_metrics(p) for label,p in (('A',ap),('B',bp),('C',cp))}
            spectra={label:band_metrics(p,first=32*4*60/126,last=40*4*60/126) for label,p in (('A',ap),('B',bp),('C',cp))}
            for m in spatial.values():
                if m['bands']['low_20_120']['mono_energy_retention']<.99 or m['bands']['high_over_500']['mono_energy_retention']<.7:
                    raise ValidationError('mono compatibility failed')
                if m['last_250ms']['rms']>10**(-65/20):raise ValidationError('tail truncated')
            regions=[(s.name,s.start/new.ppq*60/126,(s.start+s.length)/new.ppq*60/126) for s in new.sections]
            sections=production_metrics(bp,regions)['sections']
            if sections['Breakdown']['rms']>=sections['Main Drop']['rms']*.7:raise ValidationError('lost structural contrast')
            # A real short music excerpt, Python 4x/8x and C-reference at 4x.
            # Keep its length modest; this is an audit, not another candidate.
            audit=stage/'meter-music-audit.wav';excerpt(cp,audit,round(32*4*60/126*48000),round(33*4*60/126*48000))
            py4=measure(audit);py8=measure(audit,oversample=8);ref=measure(audit,library=library) if library else py4
            if abs(py4['integrated_lufs']-ref['integrated_lufs'])>.01 or abs(py4['true_peak_dbtp']-ref['true_peak_dbtp'])>.01:
                raise ValidationError('music meter/reference mismatch')
            if abs(py8['true_peak_dbtp']-py4['true_peak_dbtp'])>.1:raise ValidationError('4x/8x music true peak disagreement')
            report.update(native_verified=True,capabilities=a.capabilities(new),metrics=metrics,
                master={'recipe':recipe,'plan':plan,'processing':master,'native_editable':False,
                        'method':'linked compression + frozen headroom-constrained gain; NO limiter or master-bus claim'},
                matching=matching,drop_matching=drop_matching,drop_native_measurements=drop_meters,
                spatial=spatial,drop_bands=spectra,sections=sections,music_meter_audit={'python4':py4,'python8':py8,'reference4':ref})
        if inventory(protected)!=before:raise ValidationError('historical source changed')
        report.update(sources_unchanged=True,source_sha256=before,artifact_sha256=hashes(stage))
        write(stage/'verification.json',report);publish(stage,dest)
    return report


def reference_report(candidate,reference,destination,credit,license_text,*,library=None):
    candidate,reference=local(candidate),local(reference);dest=fresh(destination)
    if not credit or not credit.strip() or not license_text or not license_text.strip():raise ValidationError('reference requires attribution and license')
    result={'candidate_sha256':file_hash(candidate),'reference_sha256':file_hash(reference),
        'credit':credit,'user_supplied_license':license_text,'reference_audio_redistributed':False,
        'candidate':{'loudness':measure(candidate,library=library),'bands':band_metrics(candidate)},
        'reference':{'loudness':measure(reference,library=library),'bands':band_metrics(reference)},
        'ideal_eq_curve_claim':False}
    write(dest,result);return result


def package(root):
    root=local(root);out=fresh(root/'phase9-house-listening.zip');r=json.loads((root/'verification.json').read_text())
    if not r['native_verified']:raise ValidationError('ZIP needs verified native/audio proof')
    for name,digest in r['artifact_sha256'].items():
        if file_hash(root/name)!=digest:raise ValidationError('package source drift: '+name)
    readme=('Kuang Phase 9 — one source/mix experiment; human listening decides quality\n\n'
        'A/B/C-full-LUFS-matched.wav: full 64-bar Phase 8 control / Phase 9 native pre-master / off-host master.\n'
        'ALL THREE matched by constant attenuation ONLY to the same measured integrated LUFS (+/-0.001 LU).\n'
        'A/B/C-drop8-LUFS-matched.wav: bars 33–40, independently matched to the same excerpt integrated LUFS.\n'
        'C-phase9-master-OFFHOST.wav: intended master level, explicitly LOUDER than the matched audition C.\n'
        'Use matched B/C first to judge compression without a louder-is-better comparison.\n'
        'All audio lossless stereo 48 kHz/24-bit PCM; full songs 64 bars at 126 BPM in C minor plus 5s tail.\n'
        'All 1446 notes, IDs, velocities, timings and six sections are EXACT Phase 8. All Phase 8 automation retained.\n'
        'B: shorter native kick, slower transient compression, calibrated single-saw harmonic bass, small stab EQ/pan changes.\n'
        'Pad sounds/levels and prior delay/reverb/filter/pump gestures remain. Sub/kick/bass remain centred.\n'
        'editable-B/native/session.scraft is the editable PRE-MASTER. There is no verified native master bus.\n'
        'C is an OFF-HOST derivative: gentle linked compression plus measured-headroom gain, no limiter.\n'
        'reproduce/: deterministic frozen recipe, Python script and MIT Kuang source; no external dependency needed.\n'
        'From this extracted directory: python reproduce/master.py PATH_TO_RAW_B.wav new-C.wav --recipe reproduce/master-recipe.json\n'
        'The recipe checks RAW B SHA256; matched B is attenuated and will be rejected. Raw B must match the hash in the recipe.\n'
        'RAW B is included as B-phase9-premaster.wav for this reason. Raw A remains on the server.\n'
        'Optional libebur128 1.2.6 was separately built under project scratch for validation; no binary bundled.\n'
        'K weighting, 400ms/100ms-hop absolute -70 / relative -10 LU gating; 4x/8x finite sinc FIR true peak.\n'
        'Synthetic/analytical and independent reference tests passed; NOT formal EBU certification or a commercial loudness target.\n'
        'No professional reference audio is included; user-licensed reference comparison interface is documented.\n'
        'No paid services/models/plugins; original music/core MIT. Libebur128 MIT attribution in source/notices.\n'
        'Stereo remains modest; headphone/speaker response can change perceived weight. No club-ready claim.\n')
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='zip-',dir=SCRATCH) as d:
        tmp=Path(d)/'listen.zip'
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('README.txt',readme);z.writestr('measurements.json',json.dumps({k:v for k,v in r.items() if k not in ('artifact_sha256','source_sha256')},indent=2)+'\n')
            for p in sorted((root/'listening').iterdir()):z.write(p,p.name)
            for name in ('B-phase9-premaster.wav','C-phase9-master-OFFHOST.wav'):z.write(root/name,name)
            for f in sorted((root/'native').iterdir()):
                if f.is_file():z.write(f,'editable-B/native/'+f.name)
            for name in ('project.kuang.json','song.mid','source-song-spec.json','arrangement.json'):z.write(root/name,'editable-B/'+name)
            z.write(root/'master-recipe.json','reproduce/master-recipe.json')
            z.writestr('reproduce/master.py','import runpy\nrunpy.run_module("kuang.mastering",run_name="__main__")\n')
            for f in sorted((ROOT/'kuang').iterdir()):
                if f.is_file() and f.suffix in ('.py','.lua'):z.write(f,'reproduce/kuang/'+f.name)
            z.write(ROOT/'LICENSE','LICENSE');z.write(ROOT/'docs/licenses/libebur128-MIT.txt','reproduce/libebur128-MIT.txt')
        with zipfile.ZipFile(tmp) as z:
            if z.testzip():raise ValidationError('ZIP integrity failed')
        os.link(tmp,out)
    report={'zip':str(out),'bytes':out.stat().st_size,'sha256':file_hash(out)};write(root/'download.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('build','package','reference'),nargs='?',default='build')
    p.add_argument('--out-dir',required=True);p.add_argument('--source');p.add_argument('--meter-library')
    p.add_argument('--reference');p.add_argument('--reference-credit');p.add_argument('--reference-license');p.add_argument('--candidate')
    mode=p.add_mutually_exclusive_group();mode.add_argument('--symbolic',action='store_true');mode.add_argument('--soundcraft')
    args=p.parse_args()
    if args.action=='package':r=package(args.out_dir)
    elif args.action=='reference':r=reference_report(args.candidate,args.reference,args.out_dir,args.reference_credit,args.reference_license,library=args.meter_library)
    elif not(args.symbolic or args.soundcraft):p.error('select --symbolic or --soundcraft')
    else:r=build(args.out_dir,source=args.source,executable=args.soundcraft,library=args.meter_library)
    print(json.dumps({k:v for k,v in r.items() if k in ('canonical_hash','native_verified','zip','bytes','sha256')},indent=2))
