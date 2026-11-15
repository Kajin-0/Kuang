"""Locked MIDI and private-preset substitution tests; no native host needed."""
import unittest
from copy import deepcopy

from kuang import midi
from kuang.house_palette_compare import substitute, contextual_review_flags
from kuang.house_template import template
from kuang.schema import ValidationError, dumps, state_hash, Instrument
from kuang.song import rules_plan
from kuang.vitalium_patch import PLUGIN_ID


def source(seed):
    spec,_=rules_plan("deep house in C minor, 16 bars", seed)
    p,_=template(spec,profile="deep",harmony_profile="simple",include_pad=False)
    for role in ("track-bass","track-harmony"):
        track=next(t for t in p.tracks if t.id==role)
        track.instrument=Instrument(track.instrument.id,"plugin",PLUGIN_ID,
             "sha256:"+str(seed)+role,None,{"vitalium.param1":.2+seed/1000})
    p.parameters.append(
        __import__("kuang.schema",fromlist=["ParameterSpec"]).ParameterSpec(
            "vitalium.param1","normalized",0,1,0,["instrument"]))
    return p


class LockedSourceTests(unittest.TestCase):
    def test_context_level_change_is_review_not_subjective_rejection(self):
        self.assertEqual(contextual_review_flags(-25.65,-30.77,{'warnings':[]}),
                         ['large_premix_loudness_change_same_locked_midi'])
        self.assertEqual(contextual_review_flags(-25.65,-25.62,{'warnings':[]}),[])
        self.assertEqual(contextual_review_flags(-25.65,-25.62,
                         {'warnings':['kick_bass_sub_destructive_summation']}),
                         ['kick_bass_sub_destructive_summation'])
        with self.assertRaises(ValidationError):
            contextual_review_flags(float('nan'),-28.,{'warnings':[]})

    def test_swap_only_bass_instrument_and_keep_all_other_objects(self):
        a=source(17);b=source(18)
        original=dumps(a)
        changed=substitute(a,b,"bass")
        self.assertEqual(midi.export_bytes(a),midi.export_bytes(changed))
        self.assertEqual(a.sections,changed.sections)
        self.assertEqual(a.tempo_bpm,changed.tempo_bpm)
        self.assertEqual(changed.key_tonic,a.key_tonic)
        for x,y in zip(a.tracks,changed.tracks):
            if x.id=="track-bass":
                self.assertEqual(x.id,y.id)
                self.assertEqual(x.clips,y.clips)
                self.assertEqual(x.controls,y.controls)
                self.assertEqual(x.effects,y.effects)
                self.assertNotEqual(x.instrument.preset_ref,y.instrument.preset_ref)
                self.assertEqual(y.instrument.id,x.instrument.id)
            else:
                self.assertEqual(x,y)
        self.assertEqual(dumps(a),original)

    def test_swap_chord_only_and_ignore_source_song_key(self):
        a=source(17);b=source(18)
        changed=substitute(a,b,"chord")
        self.assertEqual(midi.export_bytes(a),midi.export_bytes(changed))
        self.assertNotEqual(next(t for t in changed.tracks if t.id=="track-harmony").instrument.preset_ref,
                            next(t for t in a.tracks if t.id=="track-harmony").instrument.preset_ref)

    def test_fail_closed_wrong_role_identical_or_incompatible(self):
        a=source(17);b=source(18)
        with self.assertRaises(ValidationError):substitute(a,b,"pad")
        with self.assertRaises(ValidationError):substitute(a,a,"bass")
        b=deepcopy(b)
        next(t for t in b.tracks if t.id=="track-bass").instrument.parameters["extra"]=1
        with self.assertRaises(ValidationError):substitute(a,b,"bass")
