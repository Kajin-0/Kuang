"""Exact symbolic overlap audit with explicitly supplied measured pitch offsets.

Not transcription, a consonance score or proof of listener preference. Minor
seconds/sevenths are recorded as intervals, not automatically called mistakes.
ADSR/FX tail analysis must be stated separately from MIDI-active intervals.
"""
from collections import Counter
from .schema import validate,ValidationError
from .ensemble_production import DRUMS


def context(project,offsets=None):
    validate(project);offsets=offsets or {}
    if any(type(v) is not int for v in offsets.values()):raise ValidationError('explicit integer measured semitone offsets required')
    events=[];out_of_scale=[];scale={(project.key_tonic+n)%12 for n in (0,2,3,5,7,8,10)}
    for t in project.tracks:
        if t.kind!='midi' or t.id in DRUMS:continue
        for c in t.clips:
            for n in c.notes:
                pitch=n.pitch+offsets.get(t.id,0);item=(t.id,n.id,pitch)
                events.extend([(c.start+n.start,1,item),(c.start+n.start+n.duration,0,item)])
                if pitch%12 not in scale:out_of_scale.append({'track':t.id,'id':n.id,'midi_pitch':n.pitch,'sounding_pitch':pitch,'start':c.start+n.start,'duration':n.duration})
    active={};rows=[];interval_time=Counter();previous=0
    for tick,kind,item in sorted(events):
        if tick>previous and active:
            voices=list(active.values());pairs=[]
            for i,a in enumerate(voices):
                for b in voices[i+1:]:
                    if a[0]==b[0]:continue
                    interval=abs(a[2]-b[2]);interval_time[interval%12]+=tick-previous
                    if interval%12 in (1,11):pairs.append({'tracks':[a[0],b[0]],'ids':[a[1],b[1]],'pitches':[a[2],b[2]],'semitones':interval})
            if pairs:rows.append({'start':previous,'end':tick,'close_intervals':pairs})
        previous=tick
        if kind:active[item[1]]=item
        else:active.pop(item[1],None)
    return {'method':'exact MIDI-active event sweep; supplied measured offsets, no guessed FX tails or perceptual score',
        'offsets':offsets,'out_of_scale_note_records':out_of_scale,'interval_pair_ticks':dict(interval_time),
        'minor_second_or_seventh_windows':rows,'minor_seconds_automatically_errors':False}
