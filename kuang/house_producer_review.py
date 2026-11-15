"""Bounded source-aware production hypotheses for a verified house premix.

Stage 1 scaffold/Stage 2 house fundamentals are preserved exactly.
Stage 3 proposes one reversible native routing patch from *actual* measurements.
This does NOT implement an autonomous LLM listener or automatic artistic ranking.
"""
from __future__ import annotations

import math
from copy import deepcopy

from . import midi
from .production_host import add_spread,graph_contract
from .schema import Effect,Send,Track,ParameterSpec,ValidationError,state_hash,validate

VERSION="house-context-producer-review-v1"
BUS_ID="producer-chord-space-v1"
SEND_ID="producer-chord-space-send-v1"
# These are conservative bounded candidate levels, NOT Phase44 FX copies.
CANDIDATES={
    "soft": {"send_gain_db":-19.0,"delay_beats":.75,"feedback":.17,"room_wet":.10,
             "wet_spread":.35,"wet_gain_db":-3.0,"hpf_hz":550.0,"lpf_hz":5600.0},
    "present":{"send_gain_db":-15.0,"delay_beats":.50,"feedback":.21,"room_wet":.14,
               "wet_spread":.48,"wet_gain_db":-2.0,"hpf_hz":650.0,"lpf_hz":6200.0},
    # Stage-3 second hypothesis after the wet-only experiment had negligible
    # effect: gently bring dry harmony forward, with stereo-safe spread.
    "body":{"send_gain_db":-15.,"delay_beats":.5,"feedback":.19,"room_wet":.13,
            "wet_spread":.45,"wet_gain_db":-2.5,"hpf_hz":550.,"lpf_hz":5800.,
            "dry_chord_gain_db":3.0,"dry_chord_spread":.30}
}

def diagnose(project,*,audio_evidence,reference_evidence):
    """Prepare an evidence-backed hypothesis; no assertion of aesthetic benefit.

    Evidence is provided by a separately measured audio analyzer; this
    function never fabricates an auditory score or hidden model inference.
    """
    validate(project)
    if type(audio_evidence) is not dict or type(reference_evidence) is not dict:
        raise ValidationError("actual audio and declared reference metrics required")
    required=("side_to_mid_db","presence_1_4k_vs_kick_bass_db","groove_section")
    if not all(type(audio_evidence.get(k)) is (int if k.endswith("_bar") else str if k=="groove_section" else float)
               for k in required):
        raise ValidationError("measured stereo, presence and section required")
    if not all(math.isfinite(audio_evidence[k]) for k in required[:2]):
        raise ValidationError("nonfinite audio readings")
    if not all(type(reference_evidence.get(k)) is float and math.isfinite(reference_evidence[k])
               for k in ("side_to_mid_db","presence_1_4k_vs_kick_bass_db")):
        raise ValidationError("reference must contain independently supplied finite metrics")
    if not any(s.name==audio_evidence["groove_section"] for s in project.sections):
        raise ValidationError("measured region not in song")
    active={t.id:t for t in project.tracks}
    if "track-harmony" not in active or "track-bass" not in active or "track-kick" not in active:
        raise ValidationError("cannot review incomplete rhythm/harmony mix")
    if BUS_ID in active or any(x.id==SEND_ID for t in project.tracks for x in t.sends):
        raise ValidationError("cannot reapply the same production proposal")
    presence_delta=round(reference_evidence["presence_1_4k_vs_kick_bass_db"]-
                         audio_evidence["presence_1_4k_vs_kick_bass_db"],3)
    width_delta=round(reference_evidence["side_to_mid_db"]-
                      audio_evidence["side_to_mid_db"],3)
    # The reference is not a recipe: it only prioritizes which question to test.
    if presence_delta<2 or width_delta<5:
        return {"version":VERSION,"source_hash":state_hash(project),
                "decision":"NO_CHANGE","reason":"reference-relative gap below the specific experiment thresholds",
                "presence_gap_db":presence_delta,"width_gap_db":width_delta,
                "perceptual_quality":"NOT_EVALUATED"}
    return {"version":VERSION,"source_hash":state_hash(project),
            "decision":"AUDITION_WET_CHORD_SPACE",
            "hypothesis":"Independent filtered wet chord reflection may improve presence/width without touching the low-end or dry chord stabs.",
            "presence_gap_db":presence_delta,"width_gap_db":width_delta,
            "candidate_names":list(CANDIDATES),"candidate_ranking":"NONE",
            "scope":["new wet-only chord send","new filtered time/room aux bus"],
            "source_audio_evidence":dict(audio_evidence),
            "reference_evidence":dict(reference_evidence),
            "expected_safety_gates":["native save/reopen","MIDI exact","dry instruments/FX/gains exact",
                                     "low-band mid/side preservation","true peak no clipping"],
            "perceptual_quality":"NEEDS_LISTENING"}


def candidate(project,review,*,variant):
    if variant not in CANDIDATES:raise ValidationError("unknown producer candidate")
    validate(project)
    if (type(review) is not dict or review.get("version")!=VERSION or
        review.get("decision")!="AUDITION_WET_CHORD_SPACE" or
        review.get("source_hash")!=state_hash(project)):
        raise ValidationError("explicit same-project evidence-backed review required")
    if any(t.kind=="bus" for t in project.tracks):
        raise ValidationError("first proof must be against a direct-track baseline")
    settings=CANDIDATES[variant]
    out=deepcopy(project)
    for name in ("hpf_slope","lpf_slope"):
        parameter_id="soundcraft."+name
        spec=ParameterSpec(parameter_id,"normalized",0.,1.,1/3,["effect"])
        existing=next((x for x in out.parameters if x.id==parameter_id),None)
        if existing is not None and existing!=spec:
            raise ValidationError("incompatible host EQ slope registration")
        if existing is None:
            out.parameters.append(spec)
    chord=next(t for t in out.tracks if t.id=="track-harmony")
    dry_before=deepcopy(chord)
    fx=[
      Effect("producer-wet-eq","soundcraft:eq_7band",None,{
        "effect.bypass":0.,"soundcraft.hpf_on":1.,"soundcraft.hpf_freq":settings["hpf_hz"],
        "soundcraft.hpf_slope":1/3,"soundcraft.lpf_on":1.,
        "soundcraft.lpf_freq":settings["lpf_hz"],"soundcraft.lpf_slope":1/3}),
      Effect("producer-wet-delay","soundcraft:mod_delay",None,{
        "effect.bypass":0.,"effect.wet":1.,"soundcraft.time":(60000/out.tempo_bpm)*settings["delay_beats"],
        "soundcraft.feedback":settings["feedback"],"soundcraft.lpf":settings["lpf_hz"],
        "soundcraft.mod_depth":0.,"soundcraft.mod_rate":.2}),
      Effect("producer-wet-room","soundcraft:room_reverb",None,{
        "effect.bypass":0.,"effect.wet":settings["room_wet"],
        "soundcraft.decay_ms":800.,"soundcraft.pre_delay":18.,
        "soundcraft.low_cut":settings["hpf_hz"],"soundcraft.damping":settings["lpf_hz"],
        "soundcraft.width":.76}),
    ]
    bus=Track(BUS_ID,"Producer chord-space return",'bus',None,{
        "mixer.gain_db":settings["wet_gain_db"],
        "mixer.pan":0.,"mixer.mute":0.},fx,[],[],True)
    out.tracks.append(bus)
    add_spread(out,bus,settings["wet_spread"])
    chord.sends.append(Send(SEND_ID,BUS_ID,settings["send_gain_db"],0.,"post_fader"))
    dry_gain=settings.get("dry_chord_gain_db",0.)
    if dry_gain:
        # Controlled source-context adjustment; keep original gain envelopes
        # and automation semantics rather than overlaying a second duck.
        chord.controls["mixer.gain_db"]+=dry_gain
        for lane in out.automation:
            if lane.target_id==chord.id and lane.parameter_id=="mixer.gain_db":
                for point in lane.points:point.value+=dry_gain
        add_spread(out,chord,settings["dry_chord_spread"])
    validate(out);graph_contract(out)
    if midi.export_bytes(out)!=midi.export_bytes(project) or out.sections!=project.sections:
        raise ValidationError("producer patch unexpectedly altered original music")
    for before_lane in project.automation:
        after_lane=next(l for l in out.automation if l.id==before_lane.id)
        if (before_lane.target_id,before_lane.parameter_id,[p.tick for p in before_lane.points]) != (
           after_lane.target_id,after_lane.parameter_id,[p.tick for p in after_lane.points]):
            raise ValidationError("producer changed original envelope timing")
        offset=dry_gain if (before_lane.target_id==chord.id and before_lane.parameter_id=="mixer.gain_db") else 0.
        if any(abs(p.value+offset-q.value)>1e-9 for p,q in zip(before_lane.points,after_lane.points)):
            raise ValidationError("producer changed original envelope shapes")
    if chord.instrument!=dry_before.instrument or chord.effects!=dry_before.effects or chord.clips!=dry_before.clips:
        raise ValidationError("dry chord tone or MIDI changed")
    if dry_gain==0 and chord.controls!=dry_before.controls:
        raise ValidationError("dry chord fader changed in wet-only control")
    for original in project.tracks:
        new=next(t for t in out.tracks if t.id==original.id)
        if original.id!="track-harmony" and original!=new:
            raise ValidationError("unrelated instrument or rhythm path changed")
    out.metadata["producer_review_version"]=VERSION
    out.metadata["producer_review_candidate"]=variant
    receipt={"version":VERSION,"hypothesis":review["hypothesis"],"variant":variant,
             "source_hash":review["source_hash"],"candidate_hash":state_hash(out),
             "settings":dict(settings),
             "source_midi_exact":True,"source_automation_timing_exact":True,
             "source_dry_chord_instrument_fx_and_notes_exact":True,
             "source_dry_chord_static_gain_offset_db":dry_gain,
             "source_kick_bass_exact":True,
             "changed_only":("one chord gain/spread move plus one new post-fader chord send and filtered wet-only aux return"
                            if dry_gain else "one new post-fader chord send and one filtered wet-only aux return"),
             "quality_judgment":"UNREVIEWED","automatic_winner":None}
    return out,receipt


def evaluate_candidate_effect(review,baseline_features,candidate_features,*,candidate_id):
    """A non-perceptual decision to STOP ineffectual patch trials."""
    if (review.get("decision")!="AUDITION_WET_CHORD_SPACE" or candidate_id not in CANDIDATES or
        not all(type(x) is dict for x in (baseline_features,candidate_features))):
        raise ValidationError("invalid producer trial")
    keys=("side_to_mid_db","presence_1_4k_vs_kick_bass_db")
    if any(type(x.get(k)) not in (int,float) or not math.isfinite(x[k])
           for x in (baseline_features,candidate_features) for k in keys):
        raise ValidationError("missing measured before/after features")
    delta={k:round(candidate_features[k]-baseline_features[k],3) for k in keys}
    # Ineffective effects do not become "better" merely because a DAW
    # successfully rendered them. A candidate with real change is still NOT
    # ranked aesthetically without controlled listening.
    ineffective=delta["side_to_mid_db"]<.5 and delta["presence_1_4k_vs_kick_bass_db"]<.5
    return {"version":VERSION,"candidate":candidate_id,
            "observed_change":delta,
            "technical_decision":"REJECT_INEFFECTIVE" if ineffective else "ELIGIBLE_FOR_LISTENING",
            "perceptual_preference":None,
            "quality_improvement_proven":False}


def producer_context_packet(project,review,*,native_audio_features,previous_trials=()):
    """Small bounded summary of the entire song for a future model-based planner.

    Private patches/asset paths and full audio content do not enter the
    context packet. A human/model proposes a typed high-level patch rather
    than arbitrary DAW commands.
    """
    import hashlib,json
    validate(project)
    if (type(review) is not dict or review.get("source_hash")!=state_hash(project) or
        review.get("version")!=VERSION or type(native_audio_features) is not dict):
        raise ValidationError("stale producer context")
    if type(previous_trials) not in (tuple,list) or len(previous_trials)>5:
        raise ValidationError("bounded previous producer trials required")
    song=[]
    for t in project.tracks:
        if t.kind!="midi":continue
        song.append({
          "role":t.id,"midi_notes":sum(len(c.notes) for c in t.clips),
          "fader_db":round(t.controls["mixer.gain_db"],3),
          "pan":round(t.controls["mixer.pan"],3),
          "has_stereo_spread":bool(t.controls.get("mixer.stereo_spread",0.)),
          "dry_effect_types":[e.plugin_ref for e in t.effects],
          "send_count":len(t.sends)
        })
    packet={
        "version":VERSION,
        "source_sha256":state_hash(project),
        "song_structure":[{"name":s.name,"bars":s.length//3840} for s in project.sections],
        "tempo_bpm":project.tempo_bpm,"key_tonic":project.key_tonic,"key_mode":project.key_mode,
        "roles":song,
        "automation_summary":[{"id":a.id,"target":a.target_id,"parameter":a.parameter_id,
                               "points":len(a.points)} for a in project.automation],
        "hypothesis":review.get("hypothesis"),
        "measured_audio_features":dict(native_audio_features),
        "reference_comparison":{"presence_gap_db":review.get("presence_gap_db"),
                                "width_gap_db":review.get("width_gap_db")},
        "previous_trials":list(previous_trials),
        "allowed_actions":["NO_CHANGE","AUDITION_EXISTING_BOUNDED_CANDIDATE"],
        "allowed_candidates":list(CANDIDATES),
        "no_arbitrary_midi_or_plugin_state_edits":True,
        "quality_judgment":"UNREVIEWED"
    }
    packet["context_digest"]=hashlib.sha256(json.dumps(packet,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return packet


def validate_producer_proposal(context,proposal):
    """Fail-closed boundary for a model/human suggestion, not an LLM implementation."""
    if (type(context) is not dict or type(proposal) is not dict or
        set(proposal)!={"context_digest","action","candidate","reason","evidence"} or
        proposal["context_digest"]!=context.get("context_digest") or
        context.get("version")!=VERSION):
        raise ValidationError("missing or stale strict producer proposal fields")
    import hashlib,json
    raw=dict(context);saved=raw.pop("context_digest")
    if hashlib.sha256(json.dumps(raw,sort_keys=True,allow_nan=False).encode()).hexdigest()!=saved:
        raise ValidationError("producer context was modified after measurement")
    if proposal["action"] not in context["allowed_actions"]:
        raise ValidationError("unsupported producer action")
    if proposal["action"]=="NO_CHANGE":
        if proposal["candidate"] is not None:raise ValidationError("no change cannot select a patch")
    elif proposal["candidate"] not in context["allowed_candidates"]:
        raise ValidationError("model cannot request unbounded DAW patch")
    if (type(proposal["reason"]) is not str or not 16<=len(proposal["reason"])<=1000 or
        type(proposal["evidence"]) is not list or not proposal["evidence"] or
        len(proposal["evidence"])>6 or
        any(type(x) is not str or x not in context["measured_audio_features"] for x in proposal["evidence"])):
        raise ValidationError("proposal requires specific available measured evidence")
    return {"accepted":True,"action":proposal["action"],"candidate":proposal["candidate"],
            "source_hash":context["source_sha256"],"reason":proposal["reason"],
            "automatically_good":False,
            "human_preference":None}


def revise_from_native_stems(review,stem_metrics,*,explicit_chord_prominence=False,
                             previous_trials=()):
    """Revise a failed context hypothesis using actual SoundCraft solo stems.

    A quiet chord is allowed in minimalist arrangements. Only when the prompt
    explicitly emphasizes the chord does a large measured deficit justify a
    *candidate* source audition. No preset is automatically replaced.
    """
    if (review.get("version")!=VERSION or
        type(explicit_chord_prominence) is not bool or
        type(stem_metrics) is not dict or
        not {"kick","bass","harmony"}<=set(stem_metrics) or
        type(previous_trials) not in (list,tuple) or len(previous_trials)>5):
        raise ValidationError("missing bounded fullmix and native-stem context")
    values={}
    for role in ("kick","bass","harmony"):
        payload=stem_metrics[role]
        if type(payload) is not dict or type(payload.get("rms_dbfs")) not in (int,float) or not math.isfinite(payload["rms_dbfs"]):
            raise ValidationError("invalid real native stem metric")
        values[role]=payload["rms_dbfs"]
    chord_vs_kick=round(values["harmony"]-values["kick"],3)
    trials=[x.get("technical_decision") for x in previous_trials]
    failed=trials.count("REJECT_INEFFECTIVE")>=1
    if explicit_chord_prominence and failed and chord_vs_kick < -24:
        return {
           "version":VERSION,"decision":"AUDITION_VERIFIED_CHORD_SOURCE",
           "source_hash":review["source_hash"],
           "native_chord_vs_kick_rms_db":chord_vs_kick,
           "reason":"Prompt requests chord presence, but actual isolated native chord is extremely recessed; bounded wet effects barely changed the complete mix.",
           "changed_midi_or_presets":False,
           "next_step":"Audition no more than two previously runtime-verified alternate chord presets under locked MIDI/mix; do not replace without listening.",
           "perceptual_quality":"NOT_EVALUATED"}
    return {"version":VERSION,"decision":"NO_SOURCE_CHANGE_RECOMMENDED",
            "native_chord_vs_kick_rms_db":chord_vs_kick,
            "reason":"Role audibility deficit/prompt emphasis/failed effect trial conditions not all met.",
            "perceptual_quality":"NOT_EVALUATED"}
