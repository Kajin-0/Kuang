"""Source-first Phase20 production; the main-groove gate has no master chain.

The user explicitly authorized replacing original synth source designs after
rejecting a mastering-led approach. All music remains exact; patch changes are
declared, verified original content and fully live native instruments.
"""
import json,math
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from .schema import ValidationError,state_hash,validate
from .record_mix import mixed_record
from .external_synth import bound_project,read_patch
from .groove_sources import TRACKS
from .production_host import graph_contract
from .sample_assets import digest,read_asset
from .midi import export_bytes


def source_record(source,patches,*,kick=None,offsets=None):
    if not patches or not set(patches)<=set(TRACKS):raise ValidationError('explicit existing bass/stab/lead source assignments required')
    p,mix=mixed_record(source,master=False);before={t.id:deepcopy(t.instrument) for t in p.tracks};p=bound_project(p,patches)
    changes=[]
    for tid,path in patches.items():
        manifest,_=read_patch(path);t=next(t for t in p.tracks if t.id==tid)
        if t.instrument.preset_ref==before[tid].preset_ref:raise ValidationError('source-first production cannot relabel the incumbent patch as an upgrade')
        changes.append({'track_id':tid,'role':TRACKS[tid],'before':asdict(before[tid]),'after':asdict(t.instrument),
            'manifest_sha256':digest(Path(path)/'manifest.json'),'original_content_only':manifest['original_content_only']})
    sample=None
    if kick is not None:
        asset=read_asset(kick);mapping=asset['mapping']
        expected={'root_note':36,'key_low':36,'key_high':36,'velocity_low':1,'velocity_high':127,'key_tracking':False,'playback':'one_shot'}
        if mapping!=expected:raise ValidationError('replacement kick must preserve explicit trigger/key/velocity/one-shot semantics')
        t=next(t for t in p.tracks if t.id=='track-kick')
        if t.instrument is None or t.instrument.plugin_ref!='soundcraft:sampler' or any(n.pitch!=36 for c in t.clips for n in c.notes):
            raise ValidationError('replace only the established single-trigger native kick sampler')
        old=asdict(t.instrument);t.instrument.preset_ref='sha256:'+digest(Path(kick)/'asset.json')
        sample={'track_id':t.id,'before':old,'after':asdict(t.instrument),'asset_sha256':digest(Path(kick)/'asset.json'),'mapping':mapping}
    # Bass harmonic body and lead clarity occupy different slots. These are
    # native effect Hz/dB controls, distinct from plugin-internal cutoff units.
    bass=next(t for t in p.tracks if t.id=='track-bass');eq=bass.effects[0]
    eq.parameters.update({'soundcraft.lpf_freq':1000,'soundcraft.mid_freq':450,'soundcraft.mid_gain':-2})
    # Optional measured role corrections are explicit and bounded, never a
    # quality score. Source patch output calibration is retained in its state.
    offsets={} if offsets is None else offsets
    if type(offsets) is not dict or not set(offsets)<=set(TRACKS) or any(type(v) not in (int,float) or not math.isfinite(v) or not -12<=v<=12 for v in offsets.values()):raise ValidationError('bounded existing source-role offsets required')
    for tid,value in offsets.items():
        t=next(t for t in p.tracks if t.id==tid);t.controls['mixer.gain_db']+=value
        for lane in p.automation:
            if lane.target_id==tid and lane.parameter_id=='mixer.gain_db':
                for point in lane.points:point.value+=value
    p.metadata.update(phase20_source_priority='User correction: original source sound/role design first; no master at the16-bar gate',
        phase20_source_patch_changes=json.dumps([{k:v for k,v in x.items() if k not in ('before','after')} for x in changes],sort_keys=True),phase20_source_preference='unreviewed',
        phase20_scope='Exact Phase19 MIDI/sections, explicit original source patch replacements and optional licensed kick; native role processing and shared space, no master processing. Other source instruments stay exact.')
    if export_bytes(p)!=export_bytes(source) or p.sections!=source.sections:raise ValidationError('source production changed the music')
    for a,b in zip(source.tracks,p.tracks):
        if a.id!=b.id or a.clips!=b.clips:raise ValidationError('source production changed note/clip lineage')
        if a.id not in patches and not(kick is not None and a.id=='track-kick') and a.instrument!=b.instrument:raise ValidationError('unrequested source instrument replacement')
    graph_contract(p)
    return p,{'version':'phase20-source-production-1','source_hash':state_hash(source),'candidate_hash':state_hash(p),
        'MIDI_bytes_exact':True,'all_note_ids_fields_and_sections_exact':True,'patch_changes':changes,'sample_change':sample,
        'mix_recipe':mix,'role_offsets_db':offsets,'native_master':False,'quality_preference':'unreviewed',
        'research':'Sound On Sound Armin van Buuren2009: source combinations, synthesis, envelopes and spectral roles before mastering; original implementations, not copied sounds'}
