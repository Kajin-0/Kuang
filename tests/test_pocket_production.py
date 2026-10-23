import json
import tempfile
import unittest
import wave
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from kuang.atmosphere import atmosphere_house
from kuang.depth import note_fingerprints
from kuang.gestures import crop
from kuang.midi import export_bytes
from kuang.pocket_audio import event_map, gain_fit_residual, note_windows
from kuang.pocket_production import (GROOVE_TRACKS, SOUND_TRIMS, SOURCE_HASH, apply_stage, baseline,
    experiment, groove_operations, note_changes, sound_operations)
from kuang.schema import BAR, PPQ, Lock, ValidationError, dumps, save, state_hash, validate
from kuang.soundcraft import SoundCraftAdapter
from kuang.transactions import LockedError, ScopeError, receipt_from_dict, replay
from soundcraft_fake import CONTRACT
from tools.phase12_house import ROOT, SCRATCH, build, package
from tools.phase12_routing import probe


class PocketProducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = atmosphere_house()
        cls.projects, cls.receipts = experiment(cls.source)

    def test_frozen_source_and_exact_mechanical_eight_bar_crop(self):
        self.assertEqual(state_hash(self.source), SOURCE_HASH)
        a = self.projects['A']
        expected = crop(self.source, 32, 8, [t.id for t in self.source.tracks])
        self.assertEqual(dumps(a), dumps(expected))
        self.assertEqual(state_hash(a), '0010864525aaae998a4a768ad99ab730955a22b855f4f5076c3254146d4b8e08')
        self.assertEqual(json.loads(a.metadata['gesture_diagnostic_window'])['native_dsp_reset'], True)
        selected={(t.id,c.id,n.id):(asdict(n),c.start-32*BAR)
                  for t in self.source.tracks for c in t.clips for n in c.notes
                  if 32*BAR<=c.start+n.start<40*BAR}
        actual={(t.id,c.id,n.id):(asdict(n),c.start) for t in a.tracks for c in t.clips for n in c.notes}
        self.assertEqual(actual,selected)

    def test_exact_form_key_all_ids_and_no_random_added_or_removed_notes(self):
        ids = None
        for p in self.projects.values():
            validate(p)
            self.assertEqual((p.version, p.bars, p.tempo_bpm, p.key_tonic, p.key_mode), ('0.1', 8, 126, 0, 'minor'))
            self.assertEqual(sum(s.length for s in p.sections), 8*BAR)
            notes = {n.id: (t.id, c.id, n.pitch, n.channel) for t in p.tracks for c in t.clips for n in c.notes}
            self.assertEqual(len(notes), 296)
            if ids is None: ids = notes
            self.assertEqual(notes, ids)
            for t in p.tracks:
                if t.id in ('track-kick', 'track-snare', 'track-hats', 'track-percussion'): continue
                for c in t.clips:
                    for n in c.notes: self.assertIn(n.pitch % 12, (0, 2, 3, 5, 7, 8, 10))

    def test_groove_only_exact_instruments_inserts_mixer_automation_and_metadata(self):
        a, b = self.projects['A'], self.projects['B']
        expected = deepcopy(a)
        for t, u in zip(expected.tracks, b.tracks): t.clips = deepcopy(u.clips)
        self.assertEqual(dumps(expected), dumps(b))
        self.assertNotEqual(note_fingerprints(a), note_fingerprints(b))
        self.assertEqual(a.automation, b.automation)

    def test_sound_only_exact_every_note_field_clip_order_and_midi_byte(self):
        a, c = self.projects['A'], self.projects['C']
        self.assertEqual(note_fingerprints(a), note_fingerprints(c))
        self.assertEqual(export_bytes(a), export_bytes(c))
        for t, u in zip(a.tracks, c.tracks):
            self.assertEqual(t.clips, u.clips)
            controls=deepcopy(t.controls)
            controls['mixer.gain_db']+=SOUND_TRIMS.get(t.id,0)
            self.assertEqual((controls, t.sends, t.output_master), (u.controls, u.sends, u.output_master))
            self.assertEqual([e.id for e in t.effects], [e.id for e in u.effects])
        expected=deepcopy(a.automation)
        for lane in expected:
            if lane.parameter_id=='mixer.gain_db' and lane.target_id in SOUND_TRIMS:
                for point in lane.points:point.value+=SOUND_TRIMS[lane.target_id]
        self.assertEqual(expected,c.automation)

    def test_combined_factorial_commutes_with_exact_full_project_equality(self):
        a, b, c, d = (self.projects[k] for k in 'ABCD')
        other, _ = apply_stage(c, groove_operations(c), groove=True)
        self.assertEqual(dumps(other), dumps(d))
        self.assertEqual(note_fingerprints(d), note_fingerprints(b))
        self.assertEqual(export_bytes(d), export_bytes(b))
        for t, u in zip(c.tracks, d.tracks):
            self.assertEqual((t.instrument, t.effects, t.controls), (u.instrument, u.effects, u.controls))

    def test_exact_kick_anchor_hook_pads_and_pulse_are_never_recomposed(self):
        a = self.projects['A']
        for key in ('B', 'C', 'D'):
            p = self.projects[key]
            for old, new in zip(a.tracks, p.tracks):
                if old.id == 'track-kick': self.assertEqual(old.clips, new.clips)
                if old.id in ('track-lead', 'track-arp', 'track-depth-pad', 'track-depth-air', 'track-sub-pulse'):
                    self.assertEqual(old, new)
        kick = next(t for t in a.tracks if t.id == 'track-kick')
        self.assertEqual([c.start+n.start for c in kick.clips for n in c.notes], list(range(0, 8*BAR, PPQ)))

    def test_role_specific_backbeat_ghost_shuffle_and_velocity_hierarchy(self):
        p = self.projects['B']
        for t in p.tracks:
            for c in t.clips:
                for n in c.notes:
                    at = c.start+n.start
                    if t.id == 'track-snare':
                        if n.pitch == 39:
                            self.assertEqual(at % PPQ, 18); self.assertGreaterEqual(n.velocity, 96)
                        else:
                            self.assertEqual(at % (PPQ//4), 56); self.assertLessEqual(n.velocity, 34)
                    if t.id == 'track-hats':
                        if n.pitch == 46:
                            self.assertEqual(at % (PPQ//4), 8); self.assertGreaterEqual(n.velocity, 75)
                        elif at//(PPQ//4) % 4 == 3:
                            self.assertEqual(at % (PPQ//4), 60); self.assertLessEqual(n.velocity, 41)
                    if t.id == 'track-percussion':
                        self.assertEqual(at % (PPQ//4), 60); self.assertLessEqual(n.velocity, 48)

    def test_bass_gates_leave_postrelease_air_before_next_kick(self):
        p = self.projects['D']; bass = next(t for t in p.tracks if t.id == 'track-bass')
        release = bass.instrument.parameters['soundcraft.amp_release']
        lengths = set()
        for c in bass.clips:
            for n in c.notes:
                at = c.start+n.start; following = (at//PPQ+1)*PPQ
                gap_ms = (following-at-n.duration)*60000/(126*PPQ)-release
                self.assertGreater(gap_ms, 20)
                self.assertGreater(at % PPQ, 240)
                lengths.add(n.duration)
        self.assertGreater(len(lengths), 3)

    def test_chord_voicing_roll_and_call_response_articulation(self):
        p = self.projects['B']; t = next(t for t in p.tracks if t.id == 'track-harmony')
        events = {}
        for c in t.clips:
            for n in c.notes:
                step = (c.start+n.start)//240
                events.setdefault(step, []).append(n)
        for step, notes in events.items():
            self.assertEqual(len(notes), 4)
            starts = sorted(n.start for n in notes)
            self.assertEqual([b-a for a,b in zip(starts,starts[1:])], [4,4,4])
            if step % 16 == 11:
                self.assertEqual({n.duration for n in notes}, {110})
                self.assertLessEqual(max(n.velocity for n in notes), 58)
            else: self.assertGreaterEqual(max(n.velocity for n in notes), 66)

    def test_deterministic_generation_exact_receipt_replay_and_source_unchanged(self):
        before = dumps(self.source)
        ps, rs = experiment(self.source)
        self.assertEqual(dumps(self.source), before)
        self.assertEqual(rs, self.receipts)
        for k in ps:
            self.assertEqual(dumps(ps[k]), dumps(self.projects[k]));self.assertEqual(export_bytes(ps[k]), export_bytes(self.projects[k]))
        for label, old, new in [('B-from-A','A','B'), ('C-from-A','A','C'), ('D-from-B','B','D')]:
            r = receipt_from_dict(self.receipts[label])
            self.assertEqual(dumps(replay(self.projects[old], r, undo=False)), dumps(self.projects[new]))
            self.assertEqual(dumps(replay(self.projects[new], r, undo=True)), dumps(self.projects[old]))

    def test_source_drift_locks_and_operations_outside_authorized_roles_rejected(self):
        p = deepcopy(self.source);p.metadata['unreviewed']='drift'
        with self.assertRaises(ValidationError): baseline(p)
        p = deepcopy(self.projects['A']);p.locks.append(Lock('lock-bass', 'track-bass', None))
        with self.assertRaises(LockedError): apply_stage(p, groove_operations(p), groove=True)
        p = deepcopy(self.projects['A']);p.locks.append(Lock('lock-kick', 'instrument-kick', 'soundcraft.kick_decay'))
        with self.assertRaises(LockedError): apply_stage(p, sound_operations(p), groove=False)

    def test_existing_pinned_fx_units_and_discrete_rejections_remain_strict(self):
        a = SoundCraftAdapter('/bin/true');a._discovery = deepcopy(CONTRACT)
        for name in ('soundcraft-production-plugins.json', 'soundcraft-depth-plugins.json', 'soundcraft-pulse-eq1.json'):
            a._discovery['plugins'].update(json.loads((ROOT/'tests/fixtures'/name).read_text()))
        self.assertTrue(a.capabilities(self.projects['D'])['supported'])
        p = deepcopy(self.projects['D']);next(x for x in p.parameters if x.id=='soundcraft.kick_decay').unit='Hz'
        self.assertFalse(a.capabilities(p)['supported'])
        p = deepcopy(self.projects['D']);p.tracks[0].instrument.parameters['soundcraft.kick_tune']=2
        with self.assertRaisesRegex(ValidationError, 'unregistered parameter'):
            a.capabilities(p)

    def test_every_note_deviation_has_precise_provenance(self):
        changes = note_changes(self.projects['A'], self.projects['B'])
        self.assertEqual(len(changes), 186)
        for row in changes:
            a,b=row['before'],row['after']
            self.assertEqual((a['id'],a['pitch'],a['channel']), (b['id'],b['pitch'],b['channel']))
            self.assertIn(row['track'], GROOVE_TRACKS)
            self.assertAlmostEqual(row['onset_delta_ms'], (b['start']-a['start'])*60000/(126*960))

    def test_symbolic_cli_source_preservation_collision_and_invalid_source_no_publication(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            root=Path(d);source=root/'source';source.mkdir();save(self.source,source/'project.kuang.json')
            before=(source/'project.kuang.json').read_bytes()
            build(root/'result',source=source,symbolic_only=True)
            self.assertEqual((source/'project.kuang.json').read_bytes(),before)
            self.assertEqual((root/'result/A/song.mid').read_bytes(),export_bytes(self.projects['A']))
            with self.assertRaises(ValidationError):build(root/'result',source=source,symbolic_only=True)
            with self.assertRaises(ValidationError):build(source/'nested',source=source,symbolic_only=True)
            p=deepcopy(self.source);p.tempo_bpm=125;save(p,source/'project.kuang.json')
            with self.assertRaises(ValidationError):build(root/'failed',source=source)
            self.assertFalse((root/'failed').exists())
            with self.assertRaises(ValidationError):probe(root/'result')

    def test_package_requires_real_proof(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            p=Path(d);(p/'verification.json').write_text('{}')
            with self.assertRaises(ValidationError):package(p)
            self.assertFalse((p/'phase12-house-listening.zip').exists())
            (p/'A/native').mkdir(parents=True)
            save(self.projects['A'],p/'A/project.kuang.json')
            (p/'A/native/manifest.json').write_text('{}')
            (p/'verification.json').write_text(json.dumps({'all_native_state_and_PCM_reopened':True,
                'native':{'A':{'canonical_hash':'0'*64}}}))
            with self.assertRaisesRegex(ValidationError,'package input drift'):package(p)
            self.assertFalse((p/'phase12-house-listening.zip').exists())


class PocketAudioTests(unittest.TestCase):
    def test_known_scalar_fit_rejects_loudness_only_as_a_shape_change(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            paths=[Path(d)/(k+'.wav') for k in ('original','gain','shape')]
            for j,path in enumerate(paths):
                with wave.open(str(path),'wb') as w:
                    w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000)
                    data=bytearray()
                    for i in range(4800):
                        v=200000 if i%4<2 else -200000
                        if j==1:v//=2
                        if j==2 and i%2:v=-v
                        data+=v.to_bytes(3,'little',signed=True)*2
                    w.writeframes(data)
            same=gain_fit_residual(paths[0],paths[1]);different=gain_fit_residual(paths[0],paths[2])
            self.assertEqual(same['best_scalar'],.5);self.assertEqual(same['residual_to_changed_rms_ratio'],0)
            self.assertAlmostEqual(different['residual_to_changed_rms_ratio'],1)

    def test_event_map_uses_actual_clip_offsets_and_role_delays(self):
        a=baseline();b,_=apply_stage(a,groove_operations(a),groove=True);m=event_map(b)
        self.assertEqual(m['track-kick']['offsets_ms'], [0])
        self.assertAlmostEqual(m['track-snare']['events'][0]['sixteenth_offset_ms'],18*60000/(126*960))
        self.assertIn(29.761905,m['track-percussion']['offsets_ms'])
        self.assertTrue(any(e['bar']>4 for e in m['track-bass']['events']))

    def test_actual_onset_window_measurement_known_pcm_not_grid_guess(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            p=baseline();t=p.tracks[0];c=t.clips[0];n=c.notes[0]
            t.clips=[c];c.notes=[n];n.start=96;n.duration=120
            onset=round(n.start*60/(126*960)*48000)
            path=Path(d)/'known.wav';amp=2**20
            with wave.open(str(path),'wb') as w:
                w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000)
                w.writeframes(bytes(onset*6)+(amp.to_bytes(3,'little',signed=True)*2)*12000)
            r=note_windows(path,p,t.id)
            for v in r['mean_energy'].values():self.assertAlmostEqual(v,1/64,places=12)
            self.assertAlmostEqual(r['attack_to_tail_db'],0)
            with self.assertRaises(ValidationError):note_windows(path,p,'absent')
            path=Path(d)/'bad.wav'
            with wave.open(str(path),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(bytes(96000))
            with self.assertRaises(ValidationError):note_windows(path,p,t.id)
