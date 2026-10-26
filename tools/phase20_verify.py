#!/usr/bin/env python3
"""Causal native mix/master and actual tuning controls, never preference scores."""
import argparse,json,math,shutil,sys,wave
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,ValidationError
from kuang.gestures import crop
from kuang.production_host import graph_contract
from kuang.master_bus import SINK_KEY,terminal_projection
from kuang.ensemble_production import isolate,DRUMS
from kuang.audio import compare_wavs,analyze_wav
from kuang.sample_assets import digest,write
from kuang.mix_diagnostics import linked_gain_audit,envelope_gain_audit,shortterm_trace
from kuang.loudness import measure
from kuang.lowend_audio import band_metrics
from kuang.pitch_audio import note_pitch,spectrum,hz,cents
from tools.phase15_pitch import held,ON,WINDOWS
from tools.phase20_house import adapter,media


def window(p,first=32,bars=8):
    q=crop(p,first,bars,[t.id for t in p.tracks]);q.tracks=[t for t in q.tracks if t.kind=='bus' or any(c.notes for c in t.clips)]
    owners={x for t in q.tracks for x in (t.id,*([t.instrument.id] if t.instrument else []),*(e.id for e in t.effects))}
    q.automation=[a for a in q.automation if a.target_id in owners]
    for lane in q.automation:
        if lane.parameter_id=='mixer.gain_db':
            next(t for t in q.tracks if t.id==lane.target_id).controls['mixer.gain_db']=lane.points[0].value
    terminal_projection(q) if SINK_KEY in q.metadata else graph_contract(q)
    return q


def pitch_gate(root,out,host,plugin):
    root=Path(root);out=Path(out);out.mkdir();p=load(root/'B/project.kuang.json');a=adapter(host,plugin,master=False);_,patches=media(root/'B',p);notes={};chords={}
    for tid,n in [('track-lead',67),('track-lead',63),('track-bass',36)]:
        q=held(p,tid,[n]);name=tid+'-'+str(n);a.export(q,{}, {tid:patches[tid]},out/name);a.render(out/name,out/(name+'.wav'))
        rows=[note_pitch(out/(name+'.wav'),n,ON+lo,ON+hi) for lo,hi in WINDOWS]
        if any(abs(x['fft_cents'])>5 or abs(x['period_cents'])>5 for x in rows):raise ValidationError('Phase20 played pitch failed')
        a.save(out/name,out/(name+'-saved'));a.render(out/(name+'-saved'),out/(name+'-repeat.wav'))
        if digest(out/(name+'.wav'))!=digest(out/(name+'-repeat.wav')):raise ValidationError('pitch PCM reload drift')
        notes[name]=rows
    for tid in ('track-harmony','track-depth-pad'):
        pitches=[51,55,58,62];q=held(p,tid,pitches);a.export(q,{}, {tid:patches[tid]},out/tid);a.render(out/tid,out/(tid+'.wav'))
        peaks=spectrum(out/(tid+'.wav'),ON+.5,ON+.9)[2][:100];rows=[{'midi':n,'nearest_peak_cents':min(abs(cents(x['hz'],hz(n))) for x in peaks)} for n in pitches]
        if any(x['nearest_peak_cents']>5 for x in rows):raise ValidationError('Phase20 polyphonic pitch failed')
        chords[tid]=rows
    native=adapter(host,plugin).inspect(root/'B/native')['native'];center=[]
    for t in native['tracks']:
        if t['instrument'] and t['instrument']['plugin'].startswith('vst3:'):
            value=t['instrument']['params']['1835232641'];center.append(value)
    if center!=[.5]*4:raise ValidationError('native pitch bend not centered')
    result={'version':'phase20-native-pitch-1','notes':notes,'chords':chords,'maximum_allowed_cents':5,'native_center_values':center,'saved_reopened_PCM_exact':True,'original_patches_changed':False}
    write(out/'verification.json',result);return result


def controls(root,out,host,plugin,meter=None):
    root=Path(root);out=Path(out);out.mkdir();p=load(root/'B/project.kuang.json');pre=load(root/'premaster/project.kuang.json');assets,patches=media(root/'B',p)
    def render(name,q):
        a=adapter(host,plugin,master=SINK_KEY in q.metadata);aa={t.id:assets[t.id] for t in q.tracks if t.id in assets};pp={t.id:patches[t.id] for t in q.tracks if t.id in patches}
        a.export(q,aa,pp,out/name);wav=out/(name+'.wav');a.render(out/name,wav);return wav
    # Actual native summed drum compressor, without the color insert on either
    # side so the measured envelope ratio isolates compression and its wet mix.
    drum=window(isolate(pre,DRUMS));bus=next(t for t in drum.tracks if t.id=='phase15-drum-sum');bus.effects=[e for e in bus.effects if e.id!='phase20-drum-color']
    bypass=deepcopy(drum);next(t for t in bypass.tracks if t.id==bus.id).effects[0].parameters['effect.bypass']=1
    on=render('drum-compression-on',drum);off=render('drum-compression-off',bypass)
    comp=bus.effects[0].parameters;nominal=20*math.log10(1-comp['effect.wet']+comp['effect.wet']*10**(comp['soundcraft.makeup']/20))
    compression=linked_gain_audit(off,on,nominal_gain_db=nominal)
    if compression['p01_attenuation_below_nominal_db']<.15:raise ValidationError('native drum compression is inert')
    # New shared space is causal in exactly the same MIDI/FX input context.
    mixed=window(pre);dry=deepcopy(mixed)
    for t in dry.tracks:
        if t.id in ('phase15-shared-room','phase17-dark-space','phase17-echo'):t.controls['mixer.mute']=1
    wet=render('space-on',mixed);without=render('space-off',dry);space=compare_wavs(without,wet)
    if space['difference_to_original_rms_ratio']<.02:raise ValidationError('shared space too small in actual context')
    # Distinguish limiter gain from real peak attenuation at matched input.
    limited=window(p);unlimited=deepcopy(limited);unlimited.tracks[-1].effects[-1].parameters['effect.bypass']=1
    on=render('master-limiter-on',limited);off=render('master-limiter-off',unlimited)
    threshold=limited.tracks[-1].effects[-1].parameters['soundcraft.threshold'];limit=envelope_gain_audit(off,on,nominal_gain_db=-threshold)
    levels={k:measure(v,library=meter) for k,v in [('on',on),('off',off)]}
    limit['file_maximum_sample_peak_attenuation_below_nominal_db']=-threshold+levels['off']['sample_peak_dbfs']-levels['on']['sample_peak_dbfs']
    if levels['on']['true_peak_dbtp']>-1 or limit['file_maximum_sample_peak_attenuation_below_nominal_db']<.5:raise ValidationError('native limiter did not control actual peaks')
    # Master EQ/glue has its own same-input causal control before limiting.
    glue=deepcopy(unlimited);glue.tracks[-1].effects[1].parameters['effect.bypass']=1
    glueoff=render('master-glue-off',glue);glueaudit=linked_gain_audit(glueoff,off)
    if glueaudit['maximum_observed_attenuation_below_nominal_db']<.05:raise ValidationError('native master glue is inert')
    # The nonlinear drum color is tested separately on exactly the same sum.
    color=window(isolate(pre,DRUMS));plain=deepcopy(color);next(t for t in plain.tracks if t.id=='phase15-drum-sum').effects[-1].parameters['effect.bypass']=1
    a=render('drum-color-on',color);b=render('drum-color-off',plain);color_delta=compare_wavs(b,a)
    if color_delta['difference_to_original_rms_ratio']<.001:raise ValidationError('drum color is inert')
    full=deepcopy(p);full.tracks[-1].effects[-1].parameters['effect.bypass']=1
    full_off=render('full-record-limiter-off',full);full_on=root/'B-Phase20-record-master-native.wav'
    full_envelope=envelope_gain_audit(full_off,full_on,nominal_gain_db=-threshold)
    full_levels={'on':measure(full_on,library=meter),'off':measure(full_off,library=meter)}
    full_envelope['file_maximum_sample_peak_attenuation_below_nominal_db']=-threshold+full_levels['off']['sample_peak_dbfs']-full_levels['on']['sample_peak_dbfs']
    if full_envelope['whole_file_attenuation_below_nominal_db']>2 or full_levels['on']['true_peak_dbtp']>-1:raise ValidationError('full-record limiting exceeds the conservative experiment budget')
    result={'version':'phase20-causal-controls-1','native_drum_parallel_compression':compression,'drum_wet_fraction':comp['effect.wet'],'drum_compressor_native_ratio':4,
        'drum_compression_difference':compare_wavs(out/'drum-compression-off.wav',out/'drum-compression-on.wav'),'shared_space_on_off':space,
        'native_master_glue':glueaudit,'native_limiter':limit,'limiter_levels':levels,'drum_color_difference':color_delta,'full_record_limiter':full_envelope,'full_record_limiter_levels':full_levels,
        'controls_sha256':{x.name:digest(x) for x in out.glob('*.wav')},'scope':'Same32-40bar MIDI, fresh native DSP reset; controls isolate named processing. This is not a slice of running-song tails, a listening vote or an audio-triggered sidechain.'}
    write(out/'verification.json',result);return result


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('pitch','controls'));ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);ap.add_argument('--meter-library');z=ap.parse_args()
    print(json.dumps(pitch_gate(z.root,z.out,z.soundcraft,z.plugin) if z.action=='pitch' else controls(z.root,z.out,z.soundcraft,z.plugin,z.meter_library),indent=2))
