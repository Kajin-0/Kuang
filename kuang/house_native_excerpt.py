"""Prepare SoundCraft-compatible native excerpts from validated long-form songs.

The generic gesture crop keeps MIDI tracks that become silent in a chosen
section. Native SoundCraft requires every MIDI channel to sound. Drop only
those silent channels and all automation owned by them or their effects.
Never modify the original project or remove a connected bus silently.
"""
from __future__ import annotations

from .gestures import crop
from .production_host import graph_contract
from .schema import ValidationError, state_hash, validate


def crop_sounding_native(project, first_bar, bars):
    """Return an independent excerpt suitable for native export and its proof.

    The crop's DSP starts at rest. It is *not* an identical interval from
    a continuously rendering full song, which may have effect/voice carry.
    """
    validate(project)
    before=state_hash(project)
    ids=[t.id for t in project.tracks]
    excerpt=crop(project,first_bar,bars,ids)
    removed={t.id for t in excerpt.tracks
             if t.kind=="midi" and not any(c.notes for c in t.clips)}
    excerpt.tracks=[t for t in excerpt.tracks if t.id not in removed]
    kept={t.id for t in excerpt.tracks}
    for track in excerpt.tracks:
        if any(s.target_track_id in removed for s in track.sends):
            raise ValidationError("cropped native project has sends to silent channels")
    # A lane may target an insert Effect, not just its channel.
    owners=kept|{fx.id for t in excerpt.tracks for fx in t.effects}
    excerpt.automation=[lane for lane in excerpt.automation
                        if lane.target_id in owners]
    clips={c.id for t in excerpt.tracks for c in t.clips}
    excerpt.locks=[lock for lock in excerpt.locks
                   if lock.target_id in owners or lock.target_id in clips]
    validate(excerpt)
    graph_contract(excerpt)
    if state_hash(project)!=before:
        raise ValidationError("excerpt generation modified original song")
    if not any(t.kind=="midi" and t.id=="track-kick" for t in excerpt.tracks):
        raise ValidationError("excerpt lacks an active native kick")
    if not any(t.kind=="midi" and t.id=="track-bass" for t in excerpt.tracks):
        raise ValidationError("excerpt lacks an active native bass")
    return excerpt,{
       "source_hash":before,
       "excerpt_hash":state_hash(excerpt),
       "removed_silent_track_ids":sorted(removed),
       "remaining_audio_roles":[t.id for t in excerpt.tracks if t.kind=="midi"],
       "native_graph_verified":True,
       "dsp_reset":True,
       "continuous_render_exact_slice":False,
    }
