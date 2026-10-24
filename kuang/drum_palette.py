"""Explicit pitch partitioning for live one-sample instruments, schema 0.1.

This changes track topology, never a note. Original and projected identities
are recorded independently of any sample selection or musical preference.
"""
import json
import math
from copy import deepcopy
from dataclasses import asdict

from .schema import ValidationError, state_hash, validate


def note_inventory(project):
    """Every original field plus clip timing; independent of track partition."""
    return {n.id: (c.start, c.length, n.start, n.duration, n.pitch, n.velocity, n.channel)
            for t in project.tracks for c in t.clips for n in c.notes}


def _owned_ids(track):
    ids = {track.id, *(e.id for e in track.effects)}
    if track.instrument is not None:
        ids.add(track.instrument.id)
    ids.update(c.id for c in track.clips)
    ids.update(n.id for c in track.clips for n in c.notes)
    return ids


def split_by_pitch(source, plan):
    """plan: {track_id: [(pitch, role), ...]}; first role retains old IDs.

    All pitches must occur and be covered exactly. Secondary objects receive
    a deterministic .pNN suffix; note IDs never do. Track/device automation is
    projected exactly, including point shapes and endpoint values. Shared
    nonlinear processing is NOT implied by duplicated per-role inserts.
    """
    validate(source)
    if type(plan) is not dict or not plan or not set(plan) <= {t.id for t in source.tracks}:
        raise ValidationError('explicit known drum tracks required')
    if any(k in source.metadata for k in ('drum_split_parent_hash', 'drum_split_map')):
        raise ValidationError('drum split provenance collision')
    candidate = deepcopy(source)
    tracks, mappings, projections = [], [], {}
    for track in source.tracks:
        if track.id not in plan:
            tracks.append(deepcopy(track))
            continue
        roles = plan[track.id]
        if (track.kind != 'midi' or track.instrument is None or track.sends or not track.output_master or
                type(roles) not in (list, tuple) or not roles):
            raise ValidationError('split requires master-routed MIDI without sends')
        if any(type(x) not in (list, tuple) or len(x) != 2 or type(x[0]) is not int or not 0 <= x[0] <= 127 or
               type(x[1]) is not str or not x[1] or len(x[1]) > 48 for x in roles):
            raise ValidationError('explicit integer MIDI pitches and role labels required')
        pitches = [x[0] for x in roles]
        if len(set(pitches)) != len(pitches) or set(pitches) != {n.pitch for c in track.clips for n in c.notes}:
            raise ValidationError('pitch partition must cover each original pitch exactly once')
        owned = _owned_ids(track)
        if any(lock.target_id in owned for lock in source.locks):
            raise ValidationError('cannot repartition a locked drum track or child')
        if any(lane.target_id == track.instrument.id for lane in source.automation):
            raise ValidationError('instrument automation requires an explicit new backend mapping')
        maps = []
        for i, (pitch, role) in enumerate(roles):
            suffix = '' if i == 0 else '.p' + str(pitch)
            part = deepcopy(track)
            ids = {old: old + suffix for old in [track.id, track.instrument.id,
                   *(e.id for e in track.effects), *(c.id for c in track.clips)]}
            part.id = ids[track.id]
            part.name = track.name + ' / ' + role
            part.instrument.id = ids[track.instrument.id]
            for effect in part.effects:
                effect.id = ids[effect.id]
            for clip in part.clips:
                clip.id = ids[clip.id]
                clip.notes = [n for n in clip.notes if n.pitch == pitch]
            tracks.append(part)
            maps.append((suffix, ids))
            mappings.append({'source_track': track.id, 'track': part.id, 'pitch': pitch, 'role': role,
                'identities': ids, 'notes': [n.id for c in part.clips for n in c.notes]})
        projections[track.id] = maps
    lanes = []
    for lane in source.automation:
        owner = next((t for t in source.tracks if lane.target_id in _owned_ids(t)), None)
        for suffix, ids in projections.get(owner.id if owner else None, [('', {})]):
            clone = deepcopy(lane)
            clone.id += suffix
            clone.target_id = ids.get(lane.target_id, lane.target_id)
            for point in clone.points:
                point.id += suffix
            lanes.append(clone)
    candidate.tracks, candidate.automation = tracks, lanes
    candidate.metadata['drum_split_parent_hash'] = state_hash(source)
    candidate.metadata['drum_split_map'] = json.dumps(mappings, sort_keys=True)
    validate(candidate)  # Also rejects any pre-existing suffixed ID collision.
    if note_inventory(candidate) != note_inventory(source):
        raise ValidationError('drum partition changed original note/clip fields')
    return candidate, {'version': 'drum-split-1', 'source_hash': state_hash(source),
        'candidate_hash': state_hash(candidate), 'mapping': mappings,
        'original_tracks': [asdict(t) for t in source.tracks if t.id in plan],
        'original_automation': [asdict(a) for a in source.automation],
        'note_fields_exact': True, 'note_count': len(note_inventory(source)),
        'insert_semantics': 'Per-role copies, not a summed bus. Source notes are partitioned, never duplicated.'}


def assert_articulation(project, open_track, closed_track, release_ms):
    """Prove a gated open hat releases before the next closed-hat onset.

    No cross-track choke is invented. This requires a gate patch whose native
    release is separately verified. MIDI durations remain original.
    """
    tracks = {t.id: t for t in project.tracks}
    if (open_track not in tracks or closed_track not in tracks or open_track == closed_track or
            type(release_ms) not in (float, int) or not math.isfinite(release_ms) or not 0 <= release_ms <= 10000):
        raise ValidationError('valid distinct hat roles and finite release required')
    closed = sorted(c.start+n.start for c in tracks[closed_track].clips for n in c.notes)
    gaps = []
    for clip in tracks[open_track].clips:
        for note in clip.notes:
            start = clip.start+note.start
            following = next((x for x in closed if x > start), None)
            if following is not None:
                gap = (following-start-note.duration)/project.ppq*60/project.tempo_bpm*1000-release_ms
                if gap < 0:
                    raise ValidationError('open hat would outlive the next closed hat; explicit choke unsupported')
                gaps.append(gap)
    return {'method': 'native gate + release, not cross-track choke', 'release_ms': release_ms,
            'minimum_clearance_ms': min(gaps) if gaps else None, 'events_checked': len(gaps)}
