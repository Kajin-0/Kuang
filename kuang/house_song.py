"""Authored pad correction and 64-bar arrangement, ordinary schema 0.1.

The original SongSpec stays immutable source provenance (16 bars). The separate
arrangement document describes 64 bars; no SongSpec/schema/adapter migration.
"""

import json
from copy import deepcopy
from dataclasses import asdict

from .depth import PAD_IDS, depth_house, note_fingerprints
from .schema import (BAR, PPQ, AutomationLane, AutomationPoint, Clip, Note,
                     Section, ValidationError, state_hash, validate)

PHASE6_HASH='6d5aba34cdc0dbf6401b3d1e4f6526e716dfcddaee192f7c12a7b0283e933e3b'
SONG_VERSION='house-arrangement-v1'
FORM=(('intro','DJ Intro',0,8),('groove','Groove',8,8),('build','Build',16,8),
      ('break','Breakdown',24,8),('drop','Main Drop',32,16),('outro','DJ Outro',48,16))


def corrected_pads(source=None):
    source=depth_house() if source is None else source
    validate(source)
    if state_hash(source)!=PHASE6_HASH:
        raise ValidationError('pad correction requires the unchanged released Phase 6 source')
    p=deepcopy(source)
    p.name='Kuang pocket / softer pad mix'
    for t in p.tracks:
        if t.id not in PAD_IDS:continue
        air=t.id==PAD_IDS[1]
        t.controls['mixer.gain_db']-=6
        # Lower BOTH the base fader and its existing read automation. A base
        # edit alone would be overridden by the native beat gain lane.
        for lane in p.automation:
            if lane.target_id==t.id and lane.parameter_id=='mixer.gain_db':
                for point in lane.points:point.value-=6
            if lane.target_id==t.effects[0].id and lane.parameter_id=='soundcraft.lpf_freq':
                for point in lane.points:
                    point.value=max(2500 if air else 1600,min(9000 if air else 4200,point.value*.65))
        t.controls['mixer.pan']=.48 if air else -.44
        t.instrument.parameters.update({
            'soundcraft.osc2_wave':1 if air else 2/3,
            'soundcraft.osc_mix':.18 if air else .20,
            'synth.cutoff_hz':5500 if air else 2800,
            'synth.resonance':.08,
            'soundcraft.filter_env_amount':.08 if air else .10,
            'soundcraft.amp_attack':500 if air else 850,
            'soundcraft.amp_sustain':.32 if air else .55,
            'soundcraft.amp_release':1100 if air else 1250,
            # The gentler phaser restores substantial dry-path energy. Trim
            # that instrument in native dB as well; no render-level processing.
            'soundcraft.level':-6 if air else -9,
            'soundcraft.filter_attack':900 if air else 1400,
            'soundcraft.filter_decay':1400 if air else 1900,
            'soundcraft.filter_release':1100 if air else 1250})
        for effect in t.effects:
            if effect.plugin_ref=='soundcraft:chorus':
                effect.parameters.update({'effect.wet':.30 if air else .28,
                    'soundcraft.rate':.24 if air else .17,'soundcraft.depth':.26 if air else .24})
            elif effect.plugin_ref=='soundcraft:phaser':
                effect.parameters.update({'effect.wet':.10,'soundcraft.rate':.09,
                    'soundcraft.depth':.22,'soundcraft.feedback':.12})
            elif effect.plugin_ref=='soundcraft:plate_reverb':
                effect.parameters.update({'effect.wet':.34 if air else .38,
                    'soundcraft.decay_ms':2400 if air else 2800,'soundcraft.width':.75,
                    'soundcraft.low_cut':650 if air else 500,'soundcraft.pre_delay':28,
                    'soundcraft.damping':7000 if air else 5500})
    p.metadata.update(production='pad-mix-correction',pad_mix_source_hash=PHASE6_HASH,
        pad_mix_notes='Pad/air base and gain lanes -6 dB; body instrument -3 dB compensates energy restored by reduced phaser; softer sustain/timbre/filter envelope and slower gentler modulation; longer highpassed reverb. All original MIDI unchanged. Listening preference unknown.')
    validate(p)
    if note_fingerprints(p)!=note_fingerprints(source):raise ValidationError('pad correction changed MIDI')
    return p


def _keep(role,bar,note):
    """Authored entrances/exits; bar is zero-based. Drop is an exact snapshot."""
    if 32<=bar<48:return True
    beat=(note.start%BAR)/PPQ
    step=(note.start%BAR)//(PPQ//4)
    if role=='kick':
        return bar<20 or 48<=bar or (20<=bar<23 and int(beat) in (0,2)) or (bar==23 and beat<2)
    if role=='bass':
        return (8<=bar<20 or 48<=bar<52 or
                ((20<=bar<23 or 52<=bar<60) and step in (2,10)))
    if role=='snare':
        return (4<=bar<24 or 30<=bar<32 or 48<=bar<60) and (note.pitch==39 or 8<=bar<24 or 48<=bar<56)
    if role=='hats':
        if bar<2 or 24<=bar<28:return False
        if bar<4 or bar>=60:return note.pitch==42 and step in (2,10)
        if bar<8 or 28<=bar<32 or 56<=bar<60:return step in (2,6,10,14)
        return not (8<=bar<12 and step not in (2,6,10,14))
    if role=='percussion':
        if bar<6 or 24<=bar<31 or bar>=60:return False
        return step in (7,15) if bar<12 or bar>=56 else True
    if role=='harmony':
        if bar<6 or 24<=bar<30 or bar>=56:return False
        return step==3 if bar<12 or 20<=bar<24 or bar>=52 or 30<=bar<32 else True
    if role=='lead':
        if 12<=bar<20:return True
        return (20<=bar<24 or 28<=bar<32 or 48<=bar<52) and step==0
    if role=='arp':
        if 8<=bar<24:return True
        return (28<=bar<32 or 48<=bar<56) and note.pitch==67
    if role=='depth-pad':return 12<=bar<32 or 48<=bar<56
    if role=='depth-air':return 16<=bar<32 or 48<=bar<52
    raise ValidationError('unknown authored track role')


def arrange_house(source=None):
    source=corrected_pads() if source is None else source
    validate(source)
    if state_hash(source)!=state_hash(corrected_pads()):
        raise ValidationError('arrangement requires the exact corrected pad snapshot')
    p=deepcopy(source);p.bars=64;p.name='Kuang / Pocket into space'
    p.sections=[Section('song-section-'+key,name,start*BAR,length*BAR) for key,name,start,length in FORM]
    origin={}
    for t in p.tracks:
        old=deepcopy(t.clips);t.clips=[]
        role=t.id.removeprefix('track-')
        for cell in range(16):
            # The complete original sixteen bars, IDs and velocities live at
            # bars 33–48. Other cells select/revoice no new harmony or hook.
            index=(cell if cell<8 else cell-8)%4
            original=old[index]
            clip=deepcopy(original);clip.start=cell*4*BAR
            if 8<=cell<12:
                for n in clip.notes:origin[n.id]=n.id
            else:
                clip.id=f'song-clip-{role}-{cell:02d}'
                clip.name=t.name+f' / bars {cell*4+1}-{cell*4+4}'
                notes=[]
                for n in clip.notes:
                    bar=cell*4+n.start//BAR
                    if not _keep(role,bar,n):continue
                    origin_id=n.id;n.id=f'song-{role}-{cell:02d}-{len(notes):03d}'
                    if role=='depth-pad' and (12<=bar<16 or 52<=bar<56):
                        if n.pitch in (67,70,79):continue
                    if role in ('depth-pad','depth-air'):
                        n.velocity=max(1,n.velocity-5)
                    # Quiet late-break hat/lead teasers, not a second drop.
                    if 28<=bar<32 and role in ('hats','lead','arp'):
                        n.velocity=max(1,n.velocity-18)
                    origin[n.id]=origin_id;notes.append(n)
                clip.notes=notes
                # Short, purposeful snare pickup, only before section changes.
                if role=='snare' and cell in (5,7):
                    for i,beat in enumerate((2,2.5,3,3.5)):
                        tick=3*BAR+round(beat*PPQ)
                        clip.notes.append(Note(f'song-snare-pickup-{cell}-{i}',tick,90,38,52+i*7,9))
            if clip.notes:t.clips.append(clip)
    # Repeat source parameter curves without introducing IDs on load or new
    # operations. Ordinary absolute lanes are then authored across the form.
    p.automation=[]
    for original in source.automation:
        points={}
        for block in range(4):
            for i,point in enumerate(original.points):
                tick=point.tick+block*16*BAR
                pid=point.id if block==2 else f'song-{original.id}-{block}-{i}'
                points[tick]=AutomationPoint(pid,tick,point.value,point.shape)
        p.automation.append(AutomationLane(original.id,original.target_id,original.parameter_id,
                                          [points[t] for t in sorted(points)]))

    def curve(label,owner,param,values):
        p.automation=[a for a in p.automation if (a.target_id,a.parameter_id)!=(owner,param)]
        p.automation.append(AutomationLane('song-'+label,owner,param,
            [AutomationPoint(f'song-{label}-{i}',round(bar*BAR),value,'linear')
             for i,(bar,value) in enumerate(values)]))

    for t in p.tracks:
        role=t.id.removeprefix('track-')
        if role in ('harmony','arp'):
            t.controls['mixer.pan']=-.40 if role=='harmony' else .50
        if role in ('harmony','lead','arp'):
            curve(role+'-tone',t.effects[0].id,'soundcraft.lpf_freq',
                [(0,2000),(8,2800),(12,4200),(16,4800),(20,7800),(23.75,9500),
                 (24,1800),(28,2300),(31.75,8500),(32,6500),(40,7500),(47.75,6500),
                 (48,5500),(52,3600),(56,2000),(64,1500)])
        if role in ('hats','percussion'):
            curve(role+'-shine',t.effects[0].id,'soundcraft.lpf_freq',
                [(0,5000),(8,8500),(16,10000),(23.75,16000),(24,4000),
                 (28,6000),(31.75,14000),(32,16000),(48,13000),(56,8500),(64,5000)])
        if t.id in PAD_IDS:
            air=t.id==PAD_IDS[1]
            curve(role+'-tone',t.effects[0].id,'soundcraft.lpf_freq',
                [(0,2500 if air else 1600),(16,5500 if air else 2800),
                 (23.75,8000 if air else 4200),(24,4000 if air else 2400),
                 (28,6500 if air else 3200),(31.75,9000 if air else 4000),
                 (32,6500 if air else 2800),(40,8000 if air else 3600),
                 (48,5500 if air else 2500),(56,3000 if air else 1600),(64,2500 if air else 1600)])
            # More space when pads carry the breakdown; settle at the drop.
            verb=t.effects[-1]
            curve(role+'-space',verb.id,'effect.wet',[(0,.34 if air else .38),(23,.38),
                 (24,.46),(28,.42),(31.5,.48),(32,.34 if air else .38),(48,.40),(56,.30),(64,.30)])
        if role=='lead':
            curve('lead-pan',t.id,'mixer.pan',[(0,.12),(16,.26),(24,-.26),(31.5,-.12),
                  (32,.25),(40,-.25),(47,.26),(48,.12),(64,.12)])
            curve('lead-space',t.effects[-1].id,'effect.wet',[(0,.20),(20,.25),(23.5,.34),
                  (24,.28),(31.5,.34),(32,.20),(46,.24),(48,.28),(56,.20),(64,.20)])
    p.metadata.update(production='house-song-arrangement',arrangement_version=SONG_VERSION,
        arrangement_source_hash=state_hash(source),arrangement_origin_notes=json.dumps(origin,sort_keys=True),
        arrangement_spec=json.dumps({'version':SONG_VERSION,'bars':64,'sections':[
            {'id':key,'name':name,'start_bar':start+1,'bars':length} for key,name,start,length in FORM]},sort_keys=True),
        arrangement_notes='SongSpec is unchanged source provenance, not a 64-bar SongSpec. Intro entrances; build kick thinning; eight-bar kick/bass-free breakdown and late pickup; exact original 16-bar pocket in Main Drop; progressive DJ outro. No human listening-quality claim.')
    validate(p)
    return p


def activity_map(project):
    """Per-bar authored activity, note onsets and source hook provenance."""
    result=[]
    for s in project.sections:
        bars=[]
        for b in range(s.start//BAR,(s.start+s.length)//BAR):
            tracks={}
            for t in project.tracks:
                onsets=[];held=0
                for c in t.clips:
                    for n in c.notes:
                        start=c.start+n.start
                        if b*BAR<=start<(b+1)*BAR:
                            onsets.append({'tick':start-b*BAR,'pitch':n.pitch,'velocity':n.velocity,'id':n.id})
                        if start<(b+1)*BAR and start+n.duration>b*BAR:held+=1
                if held:tracks[t.id]={'onsets':onsets,'sounding_notes':held}
            bars.append({'bar':b+1,'tracks':tracks})
        result.append({'id':s.id,'name':s.name,'start_bar':s.start//BAR+1,'bars':s.length//BAR,'activity':bars})
    return result


def control_changes(before,after):
    """Explicit changed device/mixer scalars and every changed lane point."""
    result={}
    for a,b in zip(before.tracks,after.tracks):
        changes={}
        pairs=[('mixer',a.controls,b.controls),('instrument',a.instrument.parameters,b.instrument.parameters)]
        pairs += [(e.id,e.parameters,f.parameters) for e,f in zip(a.effects,b.effects)]
        for owner,old,new in pairs:
            for key,value in old.items():
                if value!=new[key]:changes[owner+'/'+key]={'before':value,'after':new[key]}
        if changes:result[a.id]=changes
    result['automation']={a.id:[{'tick':x.tick,'before':x.value,'after':y.value}
                               for x,y in zip(a.points,b.points) if x.value!=y.value]
        for a,b in zip(before.automation,after.automation) if asdict(a)!=asdict(b)}
    return result
