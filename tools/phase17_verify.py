#!/usr/bin/env python3
"""Actual native tuning, returns, echo timing and MIDI-kick gain controls."""
import argparse,bisect,json,math,sys,wave
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.schema import load,Clip,Note,BAR,AutomationLane,AutomationPoint,ValidationError
from kuang.production_host import trim_id,graph_contract
from kuang.ensemble_production import isolate,DRUMS
from kuang.pitch_audio import note_pitch,spectrum,hz,cents
from kuang.sample_assets import digest,write
from kuang.production_audio import _decode
from kuang.audio import compare_wavs,analyze_wav
from kuang.ensemble_production import PAN_COMPENSATION_DB
from tools.phase15_pitch import held,ON,WINDOWS
from tools.phase17_house import adapter,assets_and_patches,END,AUDIO

def pitch_gate(root,out,host,plugin):
    root=Path(root);out=Path(out);out.mkdir();a=adapter(host,plugin);p=load(root/'B/project.kuang.json')
    _,patches=assets_and_patches(root/'B',p);report={}
    for tid,n in [('track-lead',67),('track-lead',63),('track-bass',36)]:
        name=tid+'-'+str(n);q=held(p,tid,[n]);a.export(q,{}, {tid:patches[tid]},out/name);wav=out/(name+'.wav');a.render(out/name,wav)
        rows=[note_pitch(wav,n,ON+lo,ON+hi) for lo,hi in WINDOWS]
        if any(abs(x['fft_cents'])>5 or abs(x['period_cents'])>5 for x in rows):raise ValidationError('new mix native pitch failed')
        a.save(out/name,out/(name+'-saved'));a.render(out/(name+'-saved'),out/(name+'-repeat.wav'))
        if digest(wav)!=digest(out/(name+'-repeat.wav')):raise ValidationError('tuning PCM reload changed')
        report[name]=rows
    chords={}
    for tid in ('track-harmony','track-depth-pad'):
        notes=[51,55,58,62];q=held(p,tid,notes);a.export(q,{}, {tid:patches[tid]},out/tid);a.render(out/tid,out/(tid+'.wav'))
        peaks=spectrum(out/(tid+'.wav'),ON+.5,ON+.9)[2][:100]
        rows=[{'midi':n,'nearest_peak_cents':min(abs(cents(x['hz'],hz(n))) for x in peaks)} for n in notes]
        if any(x['nearest_peak_cents']>5 for x in rows):raise ValidationError('new mix Cm9 pitch failed')
        chords[tid]=rows
    native=a.inspect(root/'B/native')['native']
    for t,h in zip(p.tracks,native['tracks']):
        if t.instrument and t.instrument.plugin_ref.startswith('vst3:'):
            if h['instrument']['params']['1835232641']!=.5:raise ValidationError('synthetic pitch input not neutral')
    result={'version':'phase17-native-pitch-1','notes':report,'chords':chords,'maximum_allowed_cents':5,
            'saved_reopened_PCM_exact':True,'native_input_1835232641':.5,'MIDI_transposition':False}
    write(out/'verification.json',result);return result

def wet_return(p,bid):
    owners={t.id for t in p.tracks if any(s.target_track_id==bid for s in t.sends)}
    q=isolate(p,owners);q.tracks=[t for t in q.tracks if t.id in owners|{bid}]
    for t in q.tracks:
        if t.id in owners:t.output_master=False;t.sends=[s for s in t.sends if s.target_track_id==bid]
    ids={x for t in q.tracks for x in (t.id,*([t.instrument.id] if t.instrument else []),*(e.id for e in t.effects))}
    q.automation=[a for a in q.automation if a.target_id in ids and
        (not a.parameter_id.startswith('route.') or any(a.parameter_id==trim_id(s) for t in q.tracks for s in t.sends))]
    # Strip channel-owned trims for removed sends; registry itself may be unused.
    for t in q.tracks:t.controls={k:v for k,v in t.controls.items() if not k.startswith('route.') or k in {trim_id(s) for s in t.sends}}
    graph_contract(q);return q

def energy(path,start,end):
    with wave.open(str(path),'rb') as w:
        rate=w.getframerate();w.setpos(round(start*rate));data=_decode(w.readframes(round((end-start)*rate)),w.getsampwidth(),w.getnchannels())
        return sum(x*x for row in data for x in row)/max(1,round((end-start)*rate)*2)

def controls(root,out,host,plugin):
    root=Path(root);out=Path(out);out.mkdir();a=adapter(host,plugin);p=load(root/'B/project.kuang.json');old=load(root/'A/project.kuang.json')
    assets,patches=assets_and_patches(root/'B',p)
    def render(name,q):
        aa={t.id:assets[t.id] for t in q.tracks if t.id in assets};pp={t.id:patches[t.id] for t in q.tracks if t.id in patches}
        a.export(q,aa,pp,out/(name+'-native'));a.render(out/(name+'-native'),out/(name+'.wav'),end_seconds=END);return out/(name+'.wav')
    delta={}
    for label,bid in [('dark','phase17-dark-space'),('echo','phase17-echo'),('room','phase15-shared-room')]:
        q=deepcopy(p);next(t for t in q.tracks if t.id==bid).controls['mixer.mute']=1
        wav=render(label+'-off',q);delta[label]=compare_wavs(root/AUDIO['B'],wav)
        if delta[label]['difference_to_original_rms_ratio']<.001:raise ValidationError('inert shared '+label)
        print(label,'actual on/off',delta[label]['difference_to_original_rms_ratio'],flush=True)
    wet={}
    for label,bid in [('dark','phase17-dark-space'),('echo','phase17-echo')]:
        wav=render(label+'-wet',wet_return(p,bid));wet[label]=analyze_wav(wav)
    # The short extra bass duck was rejected: the incumbent pattern already
    # leaves this window clear. Prove bass signal identity instead of claiming
    # inaudible processing as a win.
    bass_new=render('bass-approved-B',isolate(p,{'track-bass'}))
    bass_old=render('bass-approved-A',isolate(old,{'track-bass'}))
    if digest(bass_new)!=digest(bass_old):raise ValidationError('approved bass dynamics/sound changed')
    # Verify the ACTUAL gain envelope on the dense wet return. Disable only
    # kick attenuation, retaining its section-level gains at identical points.
    on=wet_return(p,'phase17-dark-space');off=deepcopy(on)
    baseline=next(x for x in off.automation if x.target_id=='phase17-dark-space' and x.parameter_id=='mixer.gain_db')
    for point in baseline.points:
        bar=point.tick/BAR
        point.value=PAN_COMPENSATION_DB+(1 if 24<=bar<32 else -2 if 32<=bar<48 else -1)
    onwav=out/'dark-wet.wav';offwav=render('dark-duck-off',off)
    gain=next(x for x in on.automation if x.target_id=='phase17-dark-space' and x.parameter_id=='mixer.gain_db')
    def sampled(lane):
        times=[a.base._samples(p,x.tick) for x in lane.points];values=[x.value for x in lane.points]
        def at(frame):
            i=bisect.bisect_right(times,frame)-1
            if i<0:return values[0]
            if i>=len(times)-1:return values[-1]
            return values[i]+(values[i+1]-values[i])*(frame-times[i])/(times[i+1]-times[i])
        return at
    actual_gain=sampled(gain);base_gain=sampled(baseline)
    errors=[];onpow=offpow=body_on=body_off=0.;checked=0
    with wave.open(str(onwav),'rb') as w,wave.open(str(offwav),'rb') as v:
        frame=0
        while raw:=w.readframes(8192):
            other=v.readframes(8192)
            for left,right in zip(_decode(raw,3,2),_decode(other,3,2)):
                if frame%97==0 and max(abs(x) for x in right)>.0001:
                    db=actual_gain(frame)-base_gain(frame);predicted=10**(db/20)
                    errors.extend(abs(x-y*predicted) for x,y in zip(left,right));checked+=1
                    if db<-2:onpow+=sum(x*x for x in left);offpow+=sum(x*x for x in right)
                    if abs(db)<.001:body_on+=sum(x*x for x in left);body_off+=sum(x*x for x in right)
                frame+=1
    if not errors or not offpow or onpow/offpow>=.7 or abs(body_on/body_off-1)>.01:
        raise ValidationError('actual return duck/recovery not verified')
    duck={'compared_sample_frames':checked,'max_abs_PCM_vs_declared_gain_error':max(errors),
          'attenuated_window_power_ratio':onpow/offpow,'recovered_body_power_ratio':body_on/body_off,
          'difference':compare_wavs(offwav,onwav),'type':'scheduled MIDI-kick return gain, not audio-triggered sidechain',
          'approved_bass_PCM_exact':True,'rejected_extra_bass_duck_relative_RMS':.00015958539318014394}
    # Echo impulse-like note: prove actual repeats at the declared musical time.
    q=held(p,'track-lead',[67]);t=q.tracks[0];t.clips[0].notes[0].duration=96
    echo=deepcopy(next(t for t in p.tracks if t.id=='phase17-echo'));q.tracks.append(echo)
    s=deepcopy(next(s for s in next(t for t in p.tracks if t.id=='track-lead').sends if s.target_track_id==echo.id))
    t.sends=[s];t.output_master=False;t.controls[trim_id(s)]=-60
    q.automation=[AutomationLane('probe-echo-gate',t.id,trim_id(s),[
        AutomationPoint('probe-before',0,-60,'linear'),AutomationPoint('probe-start',479,-60,'linear'),
        AutomationPoint('probe-open',480,0,'linear'),AutomationPoint('probe-hold',580,0,'linear'),
        AutomationPoint('probe-close',620,-60,'linear'),AutomationPoint('probe-end',BAR,-60,'linear')])]
    a.export(q,{}, {'track-lead':patches['track-lead']},out/'echo-probe');a.render(out/'echo-probe',out/'echo-probe.wav')
    delay=60/126*.75;windows=[energy(out/'echo-probe.wav',ON+i*delay-.015,ON+i*delay+.12) for i in (1,2,3)]
    before=energy(out/'echo-probe.wav',ON,ON+delay-.035)
    if windows[0]<max(1e-12,10*before) or not windows[0]>windows[1]>windows[2]>1e-14:raise ValidationError('rhythmic echo trail not verified')
    # Stop all phrase sends. Residual -60dB trim is measured, never called zero.
    quiet=wet_return(p,'phase17-echo')
    quiet.automation=[a for a in quiet.automation if not a.parameter_id.startswith('route.')]
    for t in quiet.tracks:
        for k in t.controls:
            if k.startswith('route.'):t.controls[k]=-60
    quietwav=render('echo-all-throws-closed',quiet)
    leakage=analyze_wav(quietwav)['rms']/wet['echo']['rms']
    if leakage>.003:raise ValidationError('echo send leakage too high')
    # Actual summed compressor versus bypass, with every other input unchanged.
    drum=isolate(p,DRUMS)
    for t in drum.tracks:
        if t.kind=='bus' and t.id!='phase15-drum-sum':t.controls['mixer.mute']=1
    dry=deepcopy(drum);next(t for t in dry.tracks if t.id=='phase15-drum-sum').effects[0].parameters['effect.bypass']=1
    processed=render('drum-sum-on',drum);bypass=render('drum-sum-bypass',dry)
    drumdelta=compare_wavs(bypass,processed)
    if drumdelta['difference_to_original_rms_ratio']<.001:raise ValidationError('summed compressor inert')
    result={'version':'phase17-controls-1','same_input_aux_on_off':delta,'wet_returns':wet,'return_duck':duck,
            'echo':{'interval_seconds':delay,'repeat_window_mean_square':windows,'pre_echo_mean_square':before,'closed_send_RMS_ratio':leakage,
                    'off_trim_db':-60,'reset_diagnostic':'short held G4, same source patch; not a slice of running song'},
            'actual_summed_compressor_bypass':drumdelta,'preference':'unreviewed'}
    write(out/'verification.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('pitch','controls'));ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--soundcraft',required=True);ap.add_argument('--plugin',required=True);z=ap.parse_args()
    (pitch_gate if z.action=='pitch' else controls)(z.root,z.out,z.soundcraft,z.plugin)
