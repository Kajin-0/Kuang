#!/usr/bin/env python3
"""One live Vitalium instrument milestone over the exact Phase 10 song."""
import argparse
import json
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
from kuang.atmosphere import atmosphere_house
from kuang.depth import note_fingerprints
from kuang.external_synth import ExternalSynthAdapter,bound_project,digest,inventory,read_patch,write
from kuang.gestures import crop
from kuang.loudness import measure
from kuang.lowend_audio import band_metrics
from kuang.mastering import match_lufs
from kuang.midi import export as midi_export
from kuang.production_audio import production_metrics
from kuang.schema import ValidationError,dumps,load,save,state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.spatial_audio import spatial_metrics
from tools.phase4_reference import excerpt
from tools.phase5_house import inventory as source_inventory
from tools.phase7_house import local,publish

SCRATCH=ROOT/'.local/phase11'
ROLES={'pad':'track-depth-pad','bass':'track-bass','pluck':'track-arp'}


def build(destination,source,plugin,patches,mod_off,executable,library=None):
    dest=local(destination);source=local(source)
    if dest.exists():raise ValidationError('new Phase 11 output directory required')
    protected=[ROOT/'examples']+[p for p in (ROOT/'artifacts').iterdir() if p.is_dir() and p.name!='phase11-vital']
    if any(dest.is_relative_to(p) for p in protected):raise ValidationError('Phase 11 output intersects history')
    before=source_inventory(protected);old=load(source/'project.kuang.json')
    if dumps(old)!=dumps(atmosphere_house()):raise ValidationError('exact released Phase 10 source required')
    a=ExternalSynthAdapter(plugin,executable,workspace=ROOT);legacy=SoundCraftAdapter(executable)
    if dumps(legacy.import_project(source/'native'))!=dumps(old):raise ValidationError('Phase 10 native drift')
    assignments={track:local(patches[role]) for role,track in ROLES.items()}
    asset_before={k:inventory(v) for k,v in assignments.items()};off=local(mod_off);off_before=inventory(off)
    p=bound_project(old,assignments)
    if note_fingerprints(p)!=note_fingerprints(old):raise ValidationError('source note identities changed')
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=SCRATCH,prefix='production-') as d:
        work=Path(d);stage=work/'publish';stage.mkdir();stems=stage/'stems';stems.mkdir()
        report={'phase':11,'source_hash':state_hash(old),'canonical_hash':state_hash(p),'capabilities':a.capabilities(),
                'official_vital_binary_available_locally':False,'candidate_is':'DISTRHO Vitalium 1.0.6, not current official Vital',
                'human_listening':False,'club_ready':False,'all_source_notes_exact':True,'stems':{}}
        duration=8*4*60/126
        # Gain calibration was measured beforehand at the actual native input,
        # not applied to WAVs. These final independent stem renders gate it.
        for role,track in ROLES.items():
            q=crop(old,32,8,[track]);asset=assignments[track];pair={}
            for label in ('A','B'):
                folder=stems/(role+'-'+label);wav=stems/(role+'-'+label+'.wav')
                print('Native '+role+' '+label,flush=True)
                if label=='A':legacy.export(q,folder);legacy.render(folder,wav,end_seconds=duration+8)
                else:a.export(bound_project(q,{track:asset}),{track:asset},folder);a.render(folder,wav,end_seconds=duration+8)
                pair[label]={'meter':measure(wav,library=library),
                    'active':production_metrics(wav,[('active',0,duration)])['sections']['active'],
                    'bands':band_metrics(wav,last=duration),'spatial':spatial_metrics(wav)}
            error=pair['B']['meter']['integrated_lufs']-pair['A']['meter']['integrated_lufs']
            pair['native_integrated_lufs_delta']=error
            print(role+' native LUFS delta '+str(error),flush=True)
            write(SCRATCH/('calibration-'+role+'.json'),pair)
            if abs(error)>.6:raise ValidationError('instrument needs measured native trim calibration: '+role+' '+str(error))
            report['stems'][role]=pair
        print('Full original A / live Vitalium B, 64 bars',flush=True)
        legacy.save(source/'native',stage/'baseline-native')
        legacy.render(stage/'baseline-native',stage/'A-phase10-builtins.wav',end_seconds=64*4*60/126+5)
        if digest(stage/'A-phase10-builtins.wav')!=digest(source/'D-phase10-combined-native.wav'):
            raise ValidationError('baseline identity failed')
        a.export(p,assignments,stage/'native');a.save(stage/'native',stage/'reopened-native')
        if a.inspect(stage/'native')['native']!=a.inspect(stage/'reopened-native')['native']:raise ValidationError('full native state differs')
        a.render(stage/'native',stage/'B-live-vitalium.wav',end_seconds=64*4*60/126+5)
        a.render(stage/'reopened-native',work/'repeated.wav',end_seconds=64*4*60/126+5)
        if digest(work/'repeated.wav')!=digest(stage/'B-live-vitalium.wav'):raise ValidationError('full reopened plugin PCM differs')
        save(p,stage/'project.kuang.json');midi_export(p,stage/'song.mid')
        if (stage/'song.mid').read_bytes()!=(source/'song.mid').read_bytes():raise ValidationError('complete source MIDI bytes changed')
        write(stage/'source-song-spec.json',json.loads(p.metadata['song_spec']))
        write(stage/'arrangement.json',json.loads(p.metadata['arrangement_spec']))
        metrics={k:measure(stage/name,library=library) for k,name in [('A','A-phase10-builtins.wav'),('B','B-live-vitalium.wav')]}
        if any(m['frames']!=6091429 or m['clipped_samples'] or m['true_peak_dbtp']> -1 for m in metrics.values()):
            raise ValidationError('full audio/true peak gate failed')
        spatial={k:spatial_metrics(stage/name) for k,name in [('A','A-phase10-builtins.wav'),('B','B-live-vitalium.wav')]}
        for v in spatial.values():
            if v['bands']['low_20_120']['mono_energy_retention']<.99 or v['bands']['high_over_500']['mono_energy_retention']<.8 or v['last_250ms']['rms']>10**(-65/20):
                raise ValidationError('mono/release-tail gate failed')
        print('Same-MIDI original patch internal LFO on/off',flush=True)
        on_spec=json.loads((assignments[ROLES['pad']]/'patch.vital').read_text());off_spec=json.loads((off/'patch.vital').read_text())
        on_spec['settings']['modulations']=[]
        if on_spec!=off_spec:raise ValidationError('modulation control changes other patch inputs')
        q=crop(old,32,8,[ROLES['pad']]);q.tracks[0].effects=[];q.automation=[]
        q.tracks[0].controls.update({'mixer.gain_db':-6,'mixer.pan':0})
        controls=stage/'controls';controls.mkdir()
        for label,asset in [('ON',assignments[ROLES['pad']]),('OFF',off)]:
            bundle=controls/('pad-LFO-'+label)
            a.export(bound_project(q,{ROLES['pad']:asset}),{ROLES['pad']:asset},bundle)
            a.render(bundle,controls/('pad-LFO-'+label+'.wav'),end_seconds=duration+8)
        delta=compare_wavs(controls/'pad-LFO-ON.wav',controls/'pad-LFO-OFF.wav')
        if not delta['measurable_change'] or delta['difference_to_original_rms_ratio']<.05:raise ValidationError('internal LFO control is inert')
        windows={label:[band_metrics(controls/('pad-LFO-'+label+'.wav'),first=x,last=x+.5) for x in (1,2,3,4,5,6)] for label in ('ON','OFF')}
        listening=stage/'listening';listening.mkdir();target=min(m['integrated_lufs'] for m in metrics.values())
        matching={k:match_lufs(stage/name,listening/(k+'-full-LUFS-matched.wav'),target,library=library) for k,name in [('A','A-phase10-builtins.wav'),('B','B-live-vitalium.wav')]}
        drops=work/'drops';drops.mkdir();drop_m={}
        for label,name in [('A','A-phase10-builtins.wav'),('B','B-live-vitalium.wav')]:
            excerpt(stage/name,drops/(label+'.wav'),round(32*4*60/126*48000),round(40*4*60/126*48000));drop_m[label]=measure(drops/(label+'.wav'),library=library)
        target=min(m['integrated_lufs'] for m in drop_m.values())
        drop_matching={k:match_lufs(drops/(k+'.wav'),listening/(k+'-drop8-LUFS-matched.wav'),target,library=library) for k in ('A','B')}
        stem_matching={}
        for role,pair in report['stems'].items():
            target=min(pair[k]['meter']['integrated_lufs'] for k in ('A','B'))
            stem_matching[role]={k:match_lufs(stems/(role+'-'+k+'.wav'),listening/(role+'-'+k+'-LUFS-matched.wav'),target,library=library) for k in ('A','B')}
        report.update(native_verified=True,full_save_reopen_pcm_exact=True,full_midi_bytes_exact=True,
            metrics=metrics,spatial=spatial,full_matching=matching,drop_matching=drop_matching,stem_matching=stem_matching,
            internal_lfo_difference=delta,internal_lfo_windows=windows,
            section_metrics=production_metrics(stage/'B-live-vitalium.wav',[(s.name,s.start/960*60/126,(s.start+s.length)/960*60/126) for s in p.sections]),
            limitations=['Official Vital account/download unavailable; no official binary tried','Live Vitalium 1.0.6 only, pinned older GPL fork',
                'GUI editor/display not tested on VPS','Normalized static plugin controls only; no instrument-automation mapping',
                'Host shell preset label stays <factory default>; embedded state contains verified original Kuang patch name',
                'Human preference unknown; no claim of matching Suno or professional quality'])
        if source_inventory(protected)!=before or any(inventory(v)!=asset_before[k] for k,v in assignments.items()) or inventory(off)!=off_before:
            raise ValidationError('history or prepared source assets changed')
        report.update(historical_sha256=before,history_unchanged=True,artifact_sha256=inventory(stage))
        write(stage/'verification.json',report);publish(stage,dest)
    return report


def package(root):
    root=local(root);out=root/'phase11-vitalium-listening.zip'
    if out.exists():raise ValidationError('new ZIP only')
    r=json.loads((root/'verification.json').read_text())
    if r.get('native_verified') is not True:raise ValidationError('real plugin proof required')
    if any(digest(root/k)!=v for k,v in r['artifact_sha256'].items()):raise ValidationError('package input drift')
    text=('Kuang Phase 11: LIVE DISTRHO VITALIUM 1.0.6, not official Vital 1.6.x.\n'
      'Official Vital Basic requires account/download; no login or credentials used.\n'
      'A=unchanged Phase10 built-ins. B=three original Vitalium pad/bass/pluck patches, identical complete MIDI.\n'
      'Start with full A/B LUFS-matched; eight-bar drop and individual matched stems follow.\n'
      'Raw native input levels are in measurements.json. Only audition copies receive labelled constant attenuation.\n'
      'Pad-LFO ON/OFF: identical notes/gain/FX, only internal modulation connections differ; no matching gain applied.\n'
      'Open native/session.scraft with the separately installed exact Vitalium VST3. No plugin binary is included.\n'
      'The session is live MIDI + embedded oscillator/wavetable/LFO state, not frozen audio.\n'
      'Native host shell preset label stays <factory default>; actual embedded patch and plugin UI state are original Kuang.\n'
      'native/project.kuang.json + song.mid + patches/* preserve IDs and editable normalized controls.\n'
      'Plugin/patch hashes and full native save/reopen/repeated PCM were verified. GUI editor was not tested on VPS.\n'
      'Kuang/patch/wave source MIT; separate external Vitalium GPL-3.0-or-later, optional preparer Pedalboard GPL-3.0.\n'
      'No factory presets/samples, official Vital binaries, Suno/reference recordings or third-party host binaries included.\n'
      'Exact Linux plugin fingerprint is required by the experimental Kuang adapter; old defaults remain unchanged.\n'
      'No instrument automation mapping or automatic reconciliation of GUI edits. Human audition decides quality.\n')
    with tempfile.TemporaryDirectory(dir=SCRATCH,prefix='package-') as d:
        tmp=Path(d)/'listening.zip'
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            z.writestr('README.txt',text);z.writestr('measurements.json',json.dumps({k:v for k,v in r.items() if k not in ('historical_sha256','artifact_sha256')},indent=2)+'\n')
            for f in sorted((root/'listening').iterdir()):z.write(f,f.name)
            for label in ('ON','OFF'):z.write(root/'controls'/('pad-LFO-'+label+'.wav'),'controls/pad-LFO-'+label+'.wav')
            for f in sorted((root/'native').rglob('*')):
                if f.is_file():z.write(f,'native/'+str(f.relative_to(root/'native')))
            for name in ('project.kuang.json','song.mid','arrangement.json','source-song-spec.json'):z.write(root/name,name)
            z.write(ROOT/'LICENSE','LICENSE')
        with zipfile.ZipFile(tmp) as z:
            if z.testzip():raise ValidationError('ZIP CRC failed')
            if any(name.lower().endswith(('.so','.clap','.mp3','.whl')) for name in z.namelist()):raise ValidationError('foreign binary/audio in ZIP')
        os.link(tmp,out)
    result={'zip':str(out),'bytes':out.stat().st_size,'sha256':digest(out)};write(root/'download.json',result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',nargs='?',default='build',choices=('build','package'))
    parser.add_argument('--out-dir',required=True);parser.add_argument('--source');parser.add_argument('--plugin');parser.add_argument('--soundcraft')
    parser.add_argument('--patch-pad');parser.add_argument('--patch-bass');parser.add_argument('--patch-pluck');parser.add_argument('--pad-mod-off');parser.add_argument('--meter-library')
    args=parser.parse_args()
    if args.action=='package':r=package(args.out_dir)
    else:r=build(args.out_dir,args.source,args.plugin,{'pad':args.patch_pad,'bass':args.patch_bass,'pluck':args.patch_pluck},args.pad_mod_off,args.soundcraft,args.meter_library)
    print(json.dumps({k:v for k,v in r.items() if k in ('canonical_hash','native_verified','zip','bytes','sha256')},indent=2))
