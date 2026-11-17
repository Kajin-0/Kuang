"""Opt-in House-v3 canonical room/plate routing.

Verified native role-based values from the November 16 3-style SoundCraft A/B.
No requirement to load the private Phase44 project at runtime. No defaults.
"""
from __future__ import annotations
from copy import deepcopy

from . import midi
from .production_host import add_spread, graph_contract
from .schema import Effect, ParameterSpec, Send, Track, ValidationError, validate

VERSION="house-v3-space-scene-v1"
ROOM={
    "effect.bypass":0., "effect.wet":1.,
    "soundcraft.damping":6500., "soundcraft.decay_ms":900.,
    "soundcraft.low_cut":650., "soundcraft.pre_delay":32.,
    "soundcraft.width":.92}
PLATE={
    "effect.bypass":0., "effect.wet":1.,
    "soundcraft.damping":6000., "soundcraft.decay_ms":3000.,
    "soundcraft.low_cut":700., "soundcraft.pre_delay":42.,
    "soundcraft.width":1.}
# These exact schema-0.1 registry values were verified in the native
# Phase44 → real 3-song room/plate render. Do not derive from user assets.
SPECS=(
    ParameterSpec("effect.bypass","boolean",0.,1.,0.,["effect"]),
    ParameterSpec("effect.wet","normalized",0.,1.,1.,["effect"]),
    ParameterSpec("soundcraft.damping","Hz",1000.,20000.,6000.,["effect"]),
    ParameterSpec("soundcraft.decay_ms","ms",101.,20000.,1200.,["effect"]),
    ParameterSpec("soundcraft.low_cut","Hz",20.,1000.,20.,["effect"]),
    ParameterSpec("soundcraft.pre_delay","ms",0.,250.,10.,["effect"]),
    ParameterSpec("soundcraft.width","normalized",0.,1.,1.,["effect"]),
)
# A measured starting recipe, not a globally validated preference.
# The source-role routing is explicit; kick, bass, drums never feed returns.
ROUTING={
    "room":{"track-harmony":-6., "track-pad":-11.},
    "plate":{"track-harmony":-10., "track-pad":-7.},
}


def house_v3_space(project, *, strength="reference"):
    if strength!="reference":
        raise ValidationError("only native-vetted reference strength supported")
    source=deepcopy(project)
    graph_contract(source)
    if any(t.id in ("house-v3-room","house-v3-plate") for t in source.tracks):
        raise ValidationError("space recipe already applied")
    registry={spec.id:spec for spec in source.parameters}
    for spec in SPECS:
        if spec.id not in registry:
            source.parameters.append(deepcopy(spec))
            registry[spec.id]=spec
        elif registry[spec.id]!=spec:
            raise ValidationError("native spatial parameter-spec collision")
    by={t.id:t for t in source.tracks}
    bus_specs=(("room",ROOM,"soundcraft:room_reverb"),
               ("plate",PLATE,"soundcraft:plate_reverb"))
    if "track-harmony" not in by:
        raise ValidationError("missing chord role for native shared space")
    for name,settings,plugin in bus_specs:
        bid="house-v3-"+name
        bus=Track(bid,"House-v3 shared "+name,"bus",None,
            {"mixer.gain_db":6.020599913279624,
             "mixer.pan":0.,"mixer.mute":0.},
            [Effect(bid+"-fx",plugin,None,dict(settings))],[],[],True)
        source.tracks.append(bus)
        add_spread(source,bus,1.)
        for tid,db in ROUTING[name].items():
            if tid in by:
                by[tid].sends.append(Send("house-v3-"+name+"-"+tid,
                                         bid,db,0.,"post_fader"))
    source.metadata["house_v3_space_scene"]=VERSION
    validate(source)
    graph_contract(source)
    if midi.export_bytes(source)!=midi.export_bytes(project):
        raise ValidationError("native spatial recipe changed source notes")
    for old,new in zip(project.tracks,source.tracks):
        copy=deepcopy(new)
        copy.sends=deepcopy(old.sends)
        if copy!=old:
            raise ValidationError("native spatial recipe modified source track")
    for id in ("track-kick","track-bass"):
        t=by.get(id)
        if t and t.sends:
            raise ValidationError("bass/kick cannot feed spatial returns")
    return source
