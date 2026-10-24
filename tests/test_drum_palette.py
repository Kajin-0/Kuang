"""Independent symbolic and source-boundary contracts; no music quality score."""
import json
import tempfile
import unittest
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from kuang.atmosphere import atmosphere_house
from kuang.drum_palette import assert_articulation, note_inventory, split_by_pitch
from kuang.midi import export_bytes
from kuang.octalsamples import COMMIT, catalog, import_sound, inspect_pack
from kuang.record_palette import KITS, PITCHES, PLAN, sampled_house, split_house
from kuang.sample_assets import create_asset, read_asset, write
from kuang.sample_conversion import SincConverter
from kuang.schema import Lock, Send, ValidationError, dumps, state_hash, validate
from test_generator_midi import parse_midi
from test_sample_assets import credit, mapping, wav

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT/'.local/phase13/tests'


def make_assets(root):
    result = {}
    for tid, pitch in PITCHES.items():
        out = root/tid
        mode = 'gate' if tid in ('track-hats.p46', 'track-snare.p38') else 'one_shot'
        create_asset(wav(root/(tid+'.wav')), out, credit(), mapping(root_note=pitch,
            key_low=pitch, key_high=pitch, playback=mode))
        result[tid] = out
    return result


def midi_notes(data):
    result = Counter()
    for events in parse_midi(data)[2][1:]:
        for tick, status, _, payload in events:
            if status >> 4 in (8, 9):
                result[(tick, status, payload)] += 1
    return result


class DrumPartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.source = atmosphere_house()

    def test_all_1536_original_fields_clip_timing_and_source_untouched(self):
        before = dumps(self.source); p, r = split_house(self.source)
        self.assertEqual(len(p.tracks), len(self.source.tracks)+2)
        self.assertEqual(note_inventory(p), note_inventory(self.source))
        self.assertEqual(len(note_inventory(p)), 1536)
        self.assertEqual(dumps(self.source), before)
        self.assertEqual(p.sections, self.source.sections)
        self.assertEqual(p.metadata['song_spec'], self.source.metadata['song_spec'])
        self.assertEqual(r['source_hash'], state_hash(self.source))
        self.assertEqual(r['candidate_hash'], state_hash(p))

    def test_independent_smf_note_on_off_multiset_and_channels_exact(self):
        p, _ = split_house(self.source)
        self.assertEqual(midi_notes(export_bytes(p)), midi_notes(export_bytes(self.source)))
        self.assertEqual(sum(v for k,v in midi_notes(export_bytes(p)).items() if k[1] >> 4 == 9),1536)

    def test_deterministic_ids_receipt_and_midi(self):
        a, ar = split_house(self.source); b, br = split_house(self.source)
        self.assertEqual(dumps(a), dumps(b)); self.assertEqual(ar, br)
        self.assertEqual(export_bytes(a), export_bytes(b))
        self.assertEqual(a.metadata['drum_split_parent_hash'], state_hash(self.source))
        self.assertEqual(json.loads(a.metadata['drum_split_map']), ar['mapping'])

    def test_pitch_roles_partition_without_reinterpreting_38_39_42_46(self):
        p, r = split_house(self.source)
        for entry in r['mapping']:
            t = next(t for t in p.tracks if t.id == entry['track'])
            self.assertEqual({n.pitch for c in t.clips for n in c.notes}, {entry['pitch']})
            self.assertEqual([n.id for c in t.clips for n in c.notes], entry['notes'])
        all_ids = [n for e in r['mapping'] for n in e['notes']]
        self.assertEqual(len(all_ids), len(set(all_ids)))

    def test_projected_fx_mixer_and_each_automation_point_exact(self):
        p, r = split_house(self.source); by_id = {t.id:t for t in p.tracks}
        for e in r['mapping']:
            old = next(t for t in self.source.tracks if t.id == e['source_track']); t = by_id[e['track']]
            self.assertEqual((old.controls, old.sends, old.output_master), (t.controls,t.sends,t.output_master))
            for x,y in zip(old.effects,t.effects):
                self.assertEqual((x.plugin_ref,x.preset_ref,x.parameters),(y.plugin_ref,y.preset_ref,y.parameters))
            for lane in self.source.automation:
                if lane.target_id in e['identities']:
                    projected = next(a for a in p.automation if a.target_id == e['identities'][lane.target_id] and a.parameter_id == lane.parameter_id)
                    self.assertEqual([(x.tick,x.value,x.shape) for x in lane.points],[(x.tick,x.value,x.shape) for x in projected.points])

    def test_non_drum_tracks_lanes_locks_sections_and_song_spec_exact(self):
        p,_ = split_house(self.source)
        for t in self.source.tracks:
            if t.id not in PLAN: self.assertEqual(t,next(x for x in p.tracks if x.id == t.id))
        protected = {t.id for t in self.source.tracks if t.id not in PLAN}
        protected.update(e.id for t in self.source.tracks if t.id not in PLAN for e in t.effects)
        self.assertEqual([a for a in self.source.automation if a.target_id in protected], [a for a in p.automation if a.target_id in protected])
        self.assertEqual(p.locks,self.source.locks)

    def test_missing_duplicate_boolean_unknown_pitches_fail_closed(self):
        for plan in ({'unknown':[(36,'kick')]},{'track-hats':[(42,'closed')]},
                     {'track-hats':[(42,'closed'),(42,'duplicate'),(46,'open')]},
                     {'track-kick':[(True,'kick')]},{'track-kick':[(36,'')]}):
            with self.subTest(plan=plan),self.assertRaises(ValidationError): split_by_pitch(self.source,plan)

    def test_parent_child_locks_and_routing_fail_closed(self):
        for target in ('track-snare','instrument-snare',self.source.tracks[1].clips[0].id,'effect-snare-eq'):
            p=deepcopy(self.source);p.locks.append(Lock('locked-partition',target,None))
            with self.assertRaises(ValidationError): split_house(p)
        p=deepcopy(self.source);p.tracks[0].sends=[Send('test-send','track-hats',-12,0,'post_fader')]
        with self.assertRaises(ValidationError): split_house(p)

    def test_metadata_and_generated_identity_collisions_fail(self):
        p,_=split_house(self.source)
        with self.assertRaises(ValidationError):split_house(p)
        p=deepcopy(self.source);p.tracks[3].id='track-hats.p46'
        # Existing bass automation still references its old owner; validation
        # catches that before any candidate can be published.
        with self.assertRaises(ValidationError):split_house(p)

    def test_native_gate_release_clearance_without_midi_note_edit(self):
        p,_=split_house(self.source);r=assert_articulation(p,'track-hats.p46','track-hats',70)
        self.assertGreater(r['minimum_clearance_ms'],20);self.assertEqual(r['events_checked'],103)
        for release in (1000,-1,float('nan')):
            with self.assertRaises(ValidationError):assert_articulation(p,'track-hats.p46','track-hats',release)


class PaletteBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=atmosphere_house()
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=SCRATCH);self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()

    def test_reviewed_catalog_licenses_roles_hashes_and_source_commit(self):
        c=catalog();self.assertEqual(c['commit'],COMMIT);self.assertEqual(c['license'],'CC0-1.0')
        self.assertEqual(len(c['samples']),44)
        self.assertEqual(Counter(x['type'] for x in c['samples'].values()),Counter(kick=12,hat_closed=9,hat_open=4,clap=3,snare=2,perc=10,crash=1,ride=1,riser=1,noise=1))
        for x in c['samples'].values():
            self.assertEqual(len(x['sha256']),64);self.assertIn('Origin:',x['audit']);self.assertIn('Processing:',x['audit'])
        for kit in KITS.values():self.assertTrue(all(c['samples'][k]['license_source'].startswith('own synthesis') for k in kit.values()))

    def test_missing_or_forged_pack_and_unreviewed_cymbal_mapping_rejected(self):
        with self.assertRaises(ValidationError):inspect_pack(self.root)
        (self.root/'LICENSE').write_text('CC0')
        with self.assertRaises(ValidationError):inspect_pack(self.root)
        for key in ('unknown','house.crash.wash-01','house.ride.ping-01'):
            with self.assertRaises(ValidationError):import_sound(self.root,key,36,self.root/'out',None)
        self.assertFalse((self.root/'out').exists())

    def test_complete_native_sample_bindings_preserve_all_musical_fields(self):
        assets=make_assets(self.root);p,r=sampled_house(self.source,assets)
        self.assertEqual(note_inventory(p),note_inventory(self.source));self.assertTrue(r['non_drum_tracks_exact'])
        self.assertEqual(sum(t.instrument.plugin_ref=='soundcraft:sampler' for t in p.tracks),6)
        for t in p.tracks:
            if t.id in assets:
                self.assertEqual(t.instrument.parameters['sample.velocity_sensitivity'],1)
                self.assertEqual(t.instrument.parameters['sample.attack_ms'],.1)
                self.assertEqual(read_asset(assets[t.id])['mapping']['key_tracking'],False)

    def test_incomplete_palette_invalid_level_and_one_shot_choke_claim_rejected(self):
        assets=make_assets(self.root)
        with self.assertRaises(ValidationError):sampled_house(self.source,dict(list(assets.items())[:-1]))
        with self.assertRaises(ValidationError):sampled_house(self.source,assets,{tid:99 for tid in assets})
        m=read_asset(assets['track-hats.p46']);m['mapping']['playback']='one_shot';write(assets['track-hats.p46']/'asset.json',m)
        with self.assertRaises(ValidationError):sampled_house(self.source,assets)

    def test_no_mandatory_resampler_discovery_or_library_fallback(self):
        with self.assertRaises(ValidationError):SincConverter(self.root/'missing.so')
        (self.root/'link.so').symlink_to('/bin/true')
        with self.assertRaises(ValidationError):SincConverter(self.root/'link.so')

    def test_other_style_cannot_silently_enter_fixed_song_experiment(self):
        p=deepcopy(self.source);p.tempo_bpm=124
        with self.assertRaises(ValidationError):split_house(p)

    def test_publication_cannot_pollute_source_pack_or_asset_library(self):
        from tools.phase13_house import build,prepare_library
        for name in ('source','pack','library'):(self.root/name).mkdir()
        for name in ('source','pack','library'):
            out=self.root/name/'new-release'
            with self.assertRaises(ValidationError):build(out,self.root/'source',self.root/'library',{},self.root/'pack',None)
            self.assertFalse(out.exists())
        with self.assertRaises(ValidationError):prepare_library(self.root/'pack',self.root/'pack/new-library','missing')
        self.assertFalse((self.root/'pack/new-library').exists())
