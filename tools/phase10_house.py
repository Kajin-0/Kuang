#!/usr/bin/env python3
"""Native pad-space/pulse experiment with isolated controls and one download."""
import argparse
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
from kuang.atmosphere import PULSE_ID,SOURCE_HASH,atmosphere_house
from kuang.atmosphere_audio import pulse_windows,reference_guide,sample_steps,speaker_approx,sub_power
from kuang.audio import compare_wavs
from kuang.depth import PAD_IDS,note_fingerprints
from kuang.gesture_audio import echo_peak_timing,echo_trails,window_metrics
from kuang.gestures import crop,control
from kuang.groove_audio import low_end_interaction,stem_sum_error
from kuang.loudness import measure
from kuang.lowend_audio import band_metrics
from kuang.mastering import apply_master,file_hash,match_lufs,plan_master
from kuang.midi import export
from kuang.production_audio import production_metrics
from kuang.schema import BAR,ValidationError,dumps,load,save,state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.spatial_audio import spatial_metrics
from kuang.translation import translation_house
from tools.phase4_reference import excerpt
from tools.phase5_house import checked_audio,inventory,write
from tools.phase7_house import hashes,local,publish

SCRATCH=ROOT/'.local/phase10'
RAW={'A':'A-phase9-native.wav','B':'B-pulse-only.wav','C':'C-pad-space-only.wav',
     'D':'D-phase10-combined-native.wav','E':'E-phase10-master-OFFHOST.wav'}


def fresh(path):
    p=local(path)
    if p.exists():raise ValidationError('new Phase 10 outputs only')
    return p


def symbolic(p,d):
    d.mkdir(parents=True,exist_ok=True);save(p,d/'project.kuang.json');export(p,d/'song.mid')
    write(d/'source-song-spec.json',json.loads(p.metadata['song_spec']))
    write(d/'arrangement.json',json.loads(p.metadata['arrangement_spec']))


def bounce(a,p,d,tail=8):
    symbolic(p,d);a.export(p,d/'native');a.render(d/'native',d/'audio.wav',
        end_seconds=p.length/p.ppq*60/p.tempo_bpm+tail)
    return checked_audio(d/'audio.wav')


def wet_dry(p,ids):
    q=deepcopy(p);owners=set()
    for t in q.tracks:
        if t.id not in ids:continue
        for e in t.effects:
            if e.plugin_ref.endswith('reverb') or e.plugin_ref=='soundcraft:mod_delay':
                e.parameters['effect.wet']=0;owners.add(e.id)
    q.automation=[x for x in q.automation if not(x.target_id in owners and x.parameter_id=='effect.wet')]
    return q


def controls(a,old,new,stage):
    root=stage/'controls';root.mkdir();report={};duration=8*4*60/126
    pairs=[('kick',old,['track-kick']),('bass',old,['track-bass']),('pulse',new,[PULSE_ID]),
        ('lowend-OFF',old,['track-kick','track-bass']),('lowend-ON',new,['track-kick','track-bass',PULSE_ID]),
        ('pads-original',old,list(PAD_IDS)),('pads-wet',new,list(PAD_IDS)),
        ('pads-dry',wet_dry(new,PAD_IDS),list(PAD_IDS))]
    for name,p,ids in pairs:
        print('Native control '+name,flush=True);q=crop(p,32,8,ids)
        report[name]={'audio':bounce(a,q,root/name),'bands':band_metrics(root/name/'audio.wav',last=duration)}
    pulse_rms=report['pulse']['audio']['rms_dbfs']-report['bass']['audio']['rms_dbfs']
    if not -20<=pulse_rms<=-10:raise ValidationError('pulse is outside quiet stem balance')
    if report['pulse']['bands']['band_power_fraction']['250_500']+report['pulse']['bands']['band_power_fraction']['500_2000']>.005:
        raise ValidationError('sine pulse has excessive upper leakage')
    interaction=low_end_interaction(root/'bass/audio.wav',root/'pulse/audio.wav')
    if interaction['interference_db']< -.1:raise ValidationError('pulse/bass cancellation')
    windows=pulse_windows(root/'lowend-ON/audio.wav',root/'lowend-OFF/audio.wav')
    if windows['minimum_db']< -.75:raise ValidationError('pulse creates a local bass hole')
    sub={key:sub_power(root/(key+'/audio.wav'),duration) for key in ('lowend-ON','lowend-OFF')}
    sub_change=10*math.log10(sub['lowend-ON']['mean_square']/sub['lowend-OFF']['mean_square'])
    if not -.15<=sub_change<=.35:raise ValidationError('pulse piles up or cancels 20–60Hz: '+str(sub_change))
    band_changes={k:10*math.log10(report['lowend-ON']['bands']['band_mean_square'][k]/report['lowend-OFF']['bands']['band_mean_square'][k])
                  for k in ('20_40','40_80','80_120','120_250')}
    if any(abs(v)>.4 for v in band_changes.values()):raise ValidationError('pulse low-band change too large')
    speaker={key:speaker_approx(root/(key+'/audio.wav')) for key in ('lowend-ON','lowend-OFF')}
    speaker_delta=speaker['lowend-ON']['rms_dbfs']-speaker['lowend-OFF']['rms_dbfs']
    if abs(speaker_delta)>.15:raise ValidationError('pulse alters speaker-translation body excessively')
    steps=sample_steps(root/'pulse/audio.wav')
    if steps['maximum_adjacent_sample_step']>.005:raise ValidationError('pulse discontinuity')
    regions=[('active',0,duration)]
    pad_levels={key:production_metrics(root/(key+'/audio.wav'),regions)['sections']['active']
                for key in ('pads-original','pads-wet')}
    pad_change=pad_levels['pads-wet']['rms_dbfs']-pad_levels['pads-original']['rms_dbfs']
    if not -1.8<=pad_change<=.4:raise ValidationError('pad balance drifted: '+str(pad_change))
    pad_delta=compare_wavs(root/'pads-wet/audio.wav',root/'pads-dry/audio.wav')
    if not pad_delta['measurable_change']:raise ValidationError('pad space is inert')
    # An actual single authored pulse, then silence: no stuck sine voices.
    single=crop(new,32,2,[PULSE_ID]);single.tracks[0].clips=single.tracks[0].clips[:1]
    single.tracks[0].clips[0].notes=single.tracks[0].clips[0].notes[:1]
    bounce(a,single,root/'pulse-one-note',tail=3)
    leakage=production_metrics(root/'pulse-one-note/audio.wav',[('before',0,.25),('released',1,2)])['sections']
    if leakage['before']['rms'] or leakage['released']['rms']>1e-6:raise ValidationError('sine voice leaks outside its note')
    # Separate static synth envelopes from reverb/delay tails, same MIDI and
    # native level/pan. Disable wet FX and mixer gain lanes in BOTH diagnostics.
    envelope=crop(new,32,2,[PAD_IDS[0]])
    first=envelope.tracks[0].clips[0];first.notes=[n for n in first.notes if n.start==min(x.start for x in first.notes)]
    envelope.tracks[0].clips=[first];t=envelope.tracks[0]
    for e in t.effects:
        if 'effect.wet' in e.parameters:e.parameters['effect.wet']=0
    envelope.automation=[x for x in envelope.automation if x.parameter_id not in ('effect.wet','mixer.gain_db')]
    previous=deepcopy(envelope);original=next(t for t in old.tracks if t.id==PAD_IDS[0])
    for key in ('amp_attack','amp_decay','amp_sustain','amp_release','filter_attack','filter_decay','filter_sustain','filter_release'):
        previous.tracks[0].instrument.parameters['soundcraft.'+key]=original.instrument.parameters['soundcraft.'+key]
    for key,p in (('envelope-new',envelope),('envelope-old',previous)):bounce(a,p,root/key)
    onset=first.notes[0].start/960*60/126;end=(first.notes[0].start+first.notes[0].duration)/960*60/126
    times=[('attack',onset+.03,onset+.2),('release',end+1.35,end+1.75)]
    envelopes={key:window_metrics(root/(key+'/audio.wav'),times) for key in ('envelope-old','envelope-new')}
    if not compare_wavs(root/'envelope-old/audio.wav',root/'envelope-new/audio.wav')['measurable_change']:
        raise ValidationError('static envelope change is inert')
    # Existing short lead note exposes identifiable rhythmic echoes, separate
    # from pad ADSR/reverb tails. IDs/pitch/velocity/duration unchanged.
    lead=wet_dry(crop(new,12,4,['track-lead']),['track-lead'])
    source_lead=next(t for t in new.tracks if t.id=='track-lead')
    delay=next(e for e in lead.tracks[0].effects if e.plugin_ref=='soundcraft:mod_delay')
    delay.parameters=deepcopy(next(e for e in source_lead.effects if e.id==delay.id).parameters)
    source_lane=next(x for x in new.automation if x.target_id==delay.id and x.parameter_id=='effect.wet')
    cropped_lead=crop(new,12,4,['track-lead'])
    lead.automation.append(deepcopy(next(x for x in cropped_lead.automation if x.target_id==delay.id and x.parameter_id=='effect.wet')))
    last=max((c.start+n.start,n.id) for c in lead.tracks[0].clips for n in c.notes)[1]
    for c in lead.tracks[0].clips:c.notes=[n for n in c.notes if n.id==last]
    lead.tracks[0].clips=[c for c in lead.tracks[0].clips if c.notes]
    dry=wet_dry(lead,['track-lead'])
    bounce(a,lead,root/'echo-wet');bounce(a,dry,root/'echo-dry')
    n=lead.tracks[0].clips[0].notes[0];c=lead.tracks[0].clips[0]
    timing=echo_peak_timing(root/'echo-wet/audio.wav',(c.start+n.start)/960*60/126,60000/126*.75)
    if timing['max_spacing_error_ms']>10:raise ValidationError('echo timing differs from tempo')
    echo=echo_trails(root/'echo-wet/audio.wav',root/'echo-dry/audio.wav',(c.start+n.start+n.duration)/960*60/126,60000/126*.75)
    if sum(v['wet_rms']>max(1e-5,v['dry_rms']*2) for v in echo.values())<2:raise ValidationError('no distinct echo trails')
    return {'stems':report,'pulse_relative_bass_db':pulse_rms,'pulse_bass_interaction':interaction,
        'pulse_windows':windows,'sub20_60':sub,'sub_change_db':sub_change,'low_band_changes_db':band_changes,
        'speaker120':speaker,'speaker120_change_db':speaker_delta,'pulse_steps':steps,'voice_leakage':leakage,
        'pad_levels':pad_levels,'pad_rms_change_db':pad_change,'pad_wet_dry_difference':pad_delta,
        'envelope_windows':envelopes,'echo_timing':timing,'echo_windows':echo,
        'pulse_accepted':True,'pulse_acceptance_note':'Quiet, band-limited and no significant measured cancellation; no claim of human preference. Speaker approximation adds negligible pulse benefit.'}


def build(destination,*,source=None,executable=None,library=None,guide=None):
    dest=fresh(destination);source=local(source) if source else None;library=local(library) if library else None
    guide=local(guide) if guide else None
    protected=[ROOT/'examples']+[p for p in (ROOT/'artifacts').iterdir() if p.is_dir() and p.name!='phase10-house'] if (ROOT/'artifacts').exists() else [ROOT/'examples']
    if source and not any(source.is_relative_to(p) for p in protected):protected.append(source)
    if any(dest.is_relative_to(p) for p in protected):raise ValidationError('output intersects preserved inputs')
    before=inventory(protected);guide_hash=file_hash(guide) if guide else None
    old=load(source/'project.kuang.json') if source else translation_house()
    projects={'A':old,'B':atmosphere_house(old,space=False),'C':atmosphere_house(old,pulse=False),'D':atmosphere_house(old)}
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='production-',dir=SCRATCH) as d:
        stage=Path(d)/'publish';stage.mkdir();symbolic(projects['D'],stage)
        for label in ('A','B','C'):symbolic(projects[label],stage/'variants'/label)
        report={'phase':10,'source_hash':SOURCE_HASH,'canonical_hash':state_hash(projects['D']),
            'native_verified':False,'human_listening':False,'club_ready':False,
            'original_notes_exact':all(note_fingerprints(p)[k]==v for p in projects.values() for k,v in note_fingerprints(old).items()),
            'variants':{k:state_hash(v) for k,v in projects.items()},'master_native_editable':False,
            'reference':reference_guide(guide) if guide else {'provided':False,'source_audio_used':False},'reference_guide_sha256':guide_hash}
        if executable:
            if source is None:raise ValidationError('native Phase 10 build requires unchanged Phase 9 source')
            a=SoundCraftAdapter(executable,timeout=240)
            if dumps(a.import_project(source/'native'))!=dumps(old):raise ValidationError('Phase 9 native drift')
            end=64*4*60/126+5
            print('Native full A / B pulse / C space / D combined',flush=True)
            for label,p in projects.items():
                bundle=stage/'native' if label=='D' else stage/'variants'/label/'native'
                if label=='A':a.save(source/'native',bundle)
                else:a.export(p,bundle)
                a.render(bundle,stage/RAW[label],end_seconds=end);checked_audio(stage/RAW[label])
            if file_hash(stage/RAW['A'])!=file_hash(source/'B-phase9-premaster.wav'):raise ValidationError('baseline PCM changed')
            a.save(stage/'native',stage/'saved-native')
            if a.inspect(stage/'native')['native']!=a.inspect(stage/'saved-native')['native']:raise ValidationError('native full reopen differs')
            print('Isolated controls and acceptance gates',flush=True)
            report['controls']=controls(a,old,projects['D'],stage)
            metrics={label:measure(stage/RAW[label],library=library) for label in projects}
            recipe,plan=plan_master(stage/RAW['D'],library=library);write(stage/'master-recipe.json',recipe)
            master=apply_master(stage/RAW['D'],stage/RAW['E'],recipe);metrics['E']=measure(stage/RAW['E'],library=library)
            for m in metrics.values():
                if m['frames']!=6091429 or m['clipped_samples'] or m['sample_peak']>=1 or m['integrated_lufs'] is None:raise ValidationError('bad full PCM')
            if metrics['E']['true_peak_dbtp']> -1:raise ValidationError('off-host master exceeds ceiling')
            spatial={label:spatial_metrics(stage/RAW[label]) for label in ('A','C','D','E')}
            for m in spatial.values():
                if m['bands']['low_20_120']['mono_energy_retention']<.99 or m['bands']['high_over_500']['mono_energy_retention']<.85:
                    raise ValidationError('mono compatibility failed')
                if m['last_250ms']['rms']>10**(-65/20):raise ValidationError('full release tail truncated')
            oldside=spatial['A']['bands']['high_over_500']['side_to_mid_power_ratio']
            newside=spatial['D']['bands']['high_over_500']['side_to_mid_power_ratio']
            if newside<oldside*1.15:raise ValidationError('upper-band width increase too small')
            regions=[(s.name,s.start/960*60/126,(s.start+s.length)/960*60/126) for s in old.sections]
            section_metrics=production_metrics(stage/RAW['D'],regions)
            if section_metrics['sections']['Breakdown']['rms']>=section_metrics['sections']['Main Drop']['rms']*.7:
                raise ValidationError('breakdown/drop contrast lost')
            print('Whole-program and independent drop LUFS matching',flush=True)
            listening=stage/'listening';listening.mkdir();matching={};target=min(metrics[k]['integrated_lufs'] for k in ('A','D','E'))
            for label in ('A','D','E'):
                matching[label]=match_lufs(stage/RAW[label],listening/(label+'-full-LUFS-matched.wav'),target,library=library)
            drops=stage/'drop';drops.mkdir();drop_metrics={};drop_matching={}
            for label in projects:
                p=drops/(label+'-drop.wav');excerpt(stage/RAW[label],p,round(32*4*60/126*48000),round(40*4*60/126*48000));drop_metrics[label]=measure(p,library=library)
            drop_target=min(m['integrated_lufs'] for m in drop_metrics.values())
            for label in projects:
                drop_matching[label]=match_lufs(drops/(label+'-drop.wav'),listening/(label+'-drop8-LUFS-matched.wav'),drop_target,library=library)
            diagnostic=stage/'speaker-diagnostic';diagnostic.mkdir()
            speaker={label:speaker_approx(listening/(label+'-drop8-LUFS-matched.wav'),diagnostic/(label+'-drop-HP120.wav')) for label in ('A','B','D')}
            report.update(native_verified=True,capabilities=a.capabilities(projects['D']),metrics=metrics,spatial=spatial,
                section_metrics=section_metrics,matching=matching,drop_matching=drop_matching,speaker_diagnostic=speaker,
                master={'processing':master,'recipe':recipe,'plan':plan,'native_editable':False},
                differences={label:compare_wavs(stage/RAW['A'],stage/RAW[label]) for label in ('B','C','D')})
        if inventory(protected)!=before or (guide and file_hash(guide)!=guide_hash):raise ValidationError('preserved source or guide changed')
        report.update(sources_unchanged=True,source_sha256=before,artifact_sha256=hashes(stage))
        write(stage/'verification.json',report);publish(stage,dest)
    return report


def package(root):
    root=local(root);out=fresh(root/'phase10-house-listening.zip');r=json.loads((root/'verification.json').read_text())
    if not r['native_verified']:raise ValidationError('package requires real native/audio proof')
    for name,digest in r['artifact_sha256'].items():
        if file_hash(root/name)!=digest:raise ValidationError('package input drift: '+name)
    readme=('Kuang Phase 10 — original song, pad space and quiet mono sine\n\n'
        'A = unchanged Phase9 B NATIVE pre-master (not the louder Phase9 C).\n'
        'B = optional sine pulse only; C = pads/envelopes/space only; D = combined native candidate.\n'
        'E = optional OFF-HOST gentle compression/gain of D; NOT native editable.\n'
        'Start with A-full-LUFS-matched vs D-full-LUFS-matched; E-full is also matched.\n'
        'The drop A/B/C/D versions on the server are independently matched; ZIP includes focused A/D plus causal controls.\n'
        'lowend-OFF/ON: identical kick/bass with pulse absent/present. pads-wet/dry: same revised ADSR/pan/notes, only delay/reverb wet differs.\n'
        'Control WAVs retain native render levels, and measured levels are in measurements.json.\n'
        'All lossless stereo 48k/24bit. Full songs 64 bars at 126 BPM C minor plus 5 seconds of release tail.\n'
        'Original 1446 note/clip identities/timing/velocity exact. New quiet sine adds 90 notes in groove/drop only.\n'
        'Pulse: single sine, same bass roots, late offbeat, synth filter120Hz + actual EQ1 LPF140Hz, HPF30Hz, centred.\n'
        'No verified oscillator phase reset or input-triggered sidechain; gain duck is programmed.\n'
        'Pad faders/gain lanes unchanged; static ADSR/instrument trims calibrated for quieter average, clearer entries and longer releases.\n'
        'Actual native plate/tempo delays and separate pad pans; no oscillator LFO/wavetable claim.\n'
        'Suno numeric guide is directional only: different duration/arrangement/vocals. No Suno recording, MP3, motifs or stems included or used.\n'
        'Source notes and sections are Kuang original. No reference LUFS chase, new plugins, samples, cloud APIs or models.\n'
        'editable-D/native/session.scraft is the main editable pre-master; variants/A,B,C contain full native/canonical/MIDI controls.\n'
        'D raw is included for frozen E replay: python reproduce/master.py D-phase10-combined-native.wav new-E.wav --recipe reproduce/master-recipe.json\n'
        'E raw is intentionally louder; use matched D/E to judge processing without a gain advantage.\n'
        'Python-only frozen recipe; optional reference library not bundled. Finite FIR LUFS/TP validation is not formal EBU certification.\n'
        'Additional voice-leak/envelope/echo/speaker diagnostics remain on the server; no hidden production postprocessing.\n'
        'MIT core/original music, notices included. Human listening decides preference; no club-ready/pro claim.\n')
    SCRATCH.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='zip-',dir=SCRATCH) as d:
        tmp=Path(d)/'listening.zip'
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            z.writestr('README.txt',readme);z.writestr('measurements.json',json.dumps({k:v for k,v in r.items() if k not in ('source_sha256','artifact_sha256')},indent=2)+'\n')
            for name in ('A-full-LUFS-matched.wav','D-full-LUFS-matched.wav','E-full-LUFS-matched.wav','A-drop8-LUFS-matched.wav','D-drop8-LUFS-matched.wav'):
                z.write(root/'listening'/name,name)
            for name in (RAW['D'],RAW['E']):z.write(root/name,name)
            for name in ('lowend-OFF','lowend-ON','pads-wet','pads-dry'):
                z.write(root/'controls'/name/'audio.wav','controls/'+name+'-8bars.wav')
            for label,directory in [('editable-D',root),*[(f'variants/{v}',root/'variants'/v) for v in ('A','B','C')]]:
                for f in sorted((directory/'native').iterdir()):
                    if f.is_file():z.write(f,label+'/native/'+f.name)
                for name in ('project.kuang.json','song.mid','source-song-spec.json','arrangement.json'):z.write(directory/name,label+'/'+name)
            z.write(root/'master-recipe.json','reproduce/master-recipe.json')
            z.writestr('reproduce/master.py','import runpy\nrunpy.run_module("kuang.mastering",run_name="__main__")\n')
            for f in sorted((ROOT/'kuang').iterdir()):
                if f.is_file() and f.suffix in ('.py','.lua'):z.write(f,'reproduce/kuang/'+f.name)
            z.write(ROOT/'LICENSE','LICENSE');z.write(ROOT/'docs/licenses/libebur128-MIT.txt','reproduce/libebur128-MIT.txt')
        with zipfile.ZipFile(tmp) as z:
            if z.testzip():raise ValidationError('ZIP integrity failed')
        if tmp.stat().st_size>180000000:raise ValidationError('ZIP exceeds 180MB listening budget')
        os.link(tmp,out)
    result={'zip':str(out),'sha256':file_hash(out),'bytes':out.stat().st_size};write(root/'download.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('build','package'),nargs='?',default='build')
    p.add_argument('--out-dir',required=True);p.add_argument('--source');p.add_argument('--reference-guide');p.add_argument('--meter-library')
    mode=p.add_mutually_exclusive_group();mode.add_argument('--symbolic',action='store_true');mode.add_argument('--soundcraft')
    args=p.parse_args()
    if args.action=='package':r=package(args.out_dir)
    elif not(args.symbolic or args.soundcraft):p.error('select --symbolic or --soundcraft')
    else:r=build(args.out_dir,source=args.source,executable=args.soundcraft,library=args.meter_library,guide=args.reference_guide)
    print(json.dumps({k:v for k,v in r.items() if k in ('canonical_hash','native_verified','zip','sha256','bytes')},indent=2))
