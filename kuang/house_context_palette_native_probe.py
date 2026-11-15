"""Real SoundCraft per-role source audibility for bounded post-generation review.

The solo is generated in a private scratch copy of the native session, not by
editing the source track. All WAVs are deleted after numeric verification.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .house_mix_roles import _rms_region
from .schema import ValidationError,state_hash,validate

VERSION="house-context-palette-native-probe-v2"
ROLES=("kick","bass","harmony")


def probe_native_roles(project,native,session,private_scratch,*,bars=16,include_waveform=False):
    if type(include_waveform) is not bool:
        raise ValidationError("explicit waveform fingerprint flag required")
    validate(project)
    if type(bars) is not int or not 4<=bars<=16:
        raise ValidationError("native source probe limited to 4–16 bars")
    section=next((s for s in project.sections if s.name in ("Groove A","Groove")),None)
    if section is None or section.length<bars*project.ppq*4:
        raise ValidationError("full native source must have a sufficiently long Groove section")
    root=Path(private_scratch)
    session=Path(session)
    if not root.is_dir() or not (session/"session.scraft").is_file():
        raise ValidationError("real verified native project and private scratch required")
    original_hash=state_hash(project)
    if native.inspect(session)["canonical_hash"]!=original_hash:
        raise ValidationError("source native canonical hash mismatch")
    start=section.start/project.ppq*60/project.tempo_bpm
    duration=bars*4*60/project.tempo_bpm
    levels={}
    fingerprints={}
    for role in ROLES:
        track=next((x for x in project.tracks if x.id=="track-"+role),None)
        if track is None:raise ValidationError("missing expected real native role "+role)
        # Sandbox allows host output only in a private temporary working
        # directory with its own copied complete native/asset bundle.
        with tempfile.TemporaryDirectory(prefix=".context-palette-role-",dir=root) as folder:
            work=Path(folder)
            copy=work/"native"
            shutil.copytree(session,copy)
            target=work/"solo.wav"
            ops=[("mix.mute",{"track":t.name,"value":t.id!=track.id})
                 for t in project.tracks if t.kind=="midi"]
            ops.append(("file.bounce_mix",{
               "path":str(target),"format":"wav","bit_depth":24,"dither":False,
               "start":{"seconds":start},"end":{"seconds":start+duration}}))
            native.base._run(ops,folder,source=copy/"session.scraft")
            # Host bounce rounds end time to an integer frame. At e.g.
            # 127 BPM the returned PCM may be one frame shorter than the
            # ideal fractional-duration request. Measure the *actual* tail,
            # rejecting a materially truncated bounce.
            import wave
            with wave.open(str(target),"rb") as pcm:
                actual=pcm.getnframes()/pcm.getframerate()
            if actual<duration-.01:
                raise ValidationError("native role bounce materially truncated")
            meter=_rms_region(target,{"start_seconds":0.,
                                      "end_seconds":min(duration,actual)-1e-6})
            levels[role]={"rms_dbfs":round(meter["rms_dbfs"],3),
                          "peak_dbfs":round(meter["sample_peak_dbfs"],3)}
            if include_waveform:
                from .house_sound_fingerprint import fingerprint
                fingerprints[role]=fingerprint(target,start_seconds=0.,
                                                 duration_seconds=min(duration,actual)-1e-6,windows=16)
    if native.inspect(session)["canonical_hash"]!=original_hash:
        raise ValidationError("private native probe unexpectedly altered project")
    return {
      "version":VERSION,"native_canonical_sha256":original_hash,
      "source_preserved":True,"measured_region":section.name+" first "+str(bars)+" bars",
      "role_stems":levels,"actual_native_host":True,
      "physical_stem_files_retained":False,
      "waveform_fingerprints":fingerprints if include_waveform else None,
    }
