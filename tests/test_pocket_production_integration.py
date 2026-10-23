"""Independent native/PCM tests of the eight-bar experiment; no downloads."""
import json
import os
import tempfile
import unittest
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.audio import compare_wavs
from kuang.depth import note_fingerprints
from kuang.loudness import measure
from kuang.mastering import file_hash
from kuang.pocket_production import SOUND_TRIMS, experiment, sound_operations
from kuang.pocket_audio import gain_fit_residual
from kuang.schema import dumps, load, state_hash
from kuang.soundcraft import AdapterError, SoundCraftAdapter
from kuang.transactions import Scope, SetParameter
from tools.phase5_house import inventory
from tools.phase4_reference import excerpt
from tools.phase12_house import ACTIVE, LABELS, ROOT, SCRATCH, TAIL, build, package
from tools.phase12_routing import probe


@unittest.skipUnless(os.environ.get('KUANG_SOUNDCRAFT_INTEGRATION') == '1', 'opt in to actual SoundCraft eight-bar producer proof')
class PocketProducerIntegrationTests(unittest.TestCase):
    def test_factorial_all_note_fields_native_state_restore_pcm_stems_levels_and_zip(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as folder:
            work = Path(folder)
            supplied = os.environ.get('KUANG_PHASE12_RELEASE')
            if supplied:
                release = Path(supplied).resolve()
            else:
                release = work/'release'
                build(release, source=ROOT/'artifacts/phase10-house',
                      executable=os.environ['KUANG_SOUNDCRAFT'], library=os.environ.get('KUANG_EBUR128'))
                package(release)
            before = inventory([release])
            a = SoundCraftAdapter(timeout=240)
            report = json.loads((release/'verification.json').read_text())
            projects, _ = experiment()
            native = {}
            for label, p in projects.items():
                self.assertEqual(dumps(load(release/label/'project.kuang.json')), dumps(p))
                a.export(p, work/label)
                a.save(work/label, work/(label+'-saved'))
                n = a.inspect(work/(label+'-saved'))['native']
                self.assertEqual(n, a.inspect(release/label/'native')['native'])
                self.assertEqual(dumps(a.import_project(work/(label+'-saved'))), dumps(p))
                native[label] = n
                for track, actual in zip(p.tracks, n['tracks']):
                    observed = [(x['start'], x['length'], x['pitch'], x['velocity'], x['channel'], x['release_velocity'])
                        for c in actual['playlists'][0]['clips'] for x in c['content']['Midi']['sequence']['notes']]
                    expected = [(c.start+x.start, x.duration, x.pitch, x.velocity, x.channel, 0)
                                for c in track.clips for x in c.notes]
                    self.assertEqual(Counter(observed), Counter(expected))
                    self.assertEqual([e['plugin'] for e in actual['mixer']['inserts'] if e],
                                     [e.plugin_ref.split(':')[1] for e in track.effects])
                    if track.id in ('track-kick', 'track-bass', 'track-sub-pulse'):
                        self.assertEqual(actual['mixer']['pan'], [0, 0])
                a.render(work/(label+'-saved'), work/(label+'.wav'), end_seconds=ACTIVE+TAIL)
                self.assertEqual(file_hash(work/(label+'.wav')), file_hash(release/label/'raw-with-release.wav'))
                full = report['metrics'][label]['full']
                self.assertEqual((full['sample_rate'], full['channels'], full['bits_per_sample']), (48000, 2, 24))
                self.assertEqual(full['frames'], round((ACTIVE+TAIL)*48000))
                self.assertEqual(full['clipped_samples'], 0)
                self.assertLess(full['true_peak_dbtp'], -1)
                self.assertGreater(full['rms'], 1e-6)
                self.assertLess(report['metrics'][label]['spatial']['last_250ms']['rms'], 10**(-65/20))
                self.assertLessEqual(report['recombination'][label]['peak_error_lsb'], 12)
                matched = release/'listening'/(label+'-'+LABELS[label]+'-LUFS-matched.wav')
                excerpt(matched,work/(label+'-matched-active.wav'),0,round(ACTIVE*48000))
                measured = measure(work/(label+'-matched-active.wav'), library=os.environ.get('KUANG_EBUR128'))
                self.assertAlmostEqual(measured['integrated_lufs'], report['matching'][label]['target_lufs'], delta=.002)
                self.assertLessEqual(report['matching'][label]['gain_db'], 0)
            # Entire native state comparison, with MIDI notes the ONLY allowed
            # paths in the groove-only export. Clip/mixer/FX/automation unchanged.
            for old, new in [('A','B'), ('C','D')]:
                expected = deepcopy(native[old])
                for track, target, observed in zip(projects[new].tracks, expected['tracks'], native[new]['tracks']):
                    for playlist, actual in zip(target['playlists'], observed['playlists']):
                        for c,d in zip(playlist['clips'], actual['clips']):
                            c['content']['Midi']['sequence']['notes'] = d['content']['Midi']['sequence']['notes']
                            # The native MIDI importer merges clips and sizes
                            # their sample region to the last note-off, using
                            # the SMF integer-microsecond tempo. Canonical clip
                            # bounds stay exact in the manifest/snapshot.
                            last=max(v.start+n.start+n.duration for v in track.clips for n in v.notes)
                            extent=round(last/projects[new].ppq*round(60_000_000/projects[new].tempo_bpm)/1_000_000*48000)
                            self.assertAlmostEqual(d['length'],extent,delta=1)
                            c['length']=d['length']
                self.assertEqual(expected, native[new])
            # Sound-only: only the declared existing parameter paths may differ.
            expected = deepcopy(native['A'])
            for op in sound_operations(projects['A']):
                if not isinstance(op,SetParameter) or op.target_id in SOUND_TRIMS:
                    continue
                for index, track in enumerate(projects['A'].tracks):
                    if op.target_id == track.instrument.id:
                        e = expected['tracks'][index]['instrument']['params']
                        observed = native['C']['tracks'][index]['instrument']['params'];break
                    slot = next((s for s,v in enumerate(track.effects) if v.id == op.target_id), None)
                    if slot is not None:
                        e = expected['tracks'][index]['mixer']['inserts'][slot]['params']
                        observed = native['C']['tracks'][index]['mixer']['inserts'][slot]['params'];break
                name = 'cutoff' if op.parameter_id == 'synth.cutoff_hz' else 'mix' if op.parameter_id == 'effect.wet' else 'decay' if op.parameter_id == 'soundcraft.decay_ms' else op.parameter_id.removeprefix('soundcraft.')
                spec = next(v for v in projects['A'].parameters if v.id == op.parameter_id)
                value = op.value/1000 if op.parameter_id == 'soundcraft.decay_ms' else op.value*100 if spec.unit == 'normalized' else op.value
                self.assertAlmostEqual(observed[name], value, delta=.001)
                e[name] = observed[name]
            for index, track in enumerate(projects['A'].tracks):
                if track.id not in SOUND_TRIMS:continue
                trim=SOUND_TRIMS[track.id];e=expected['tracks'][index];observed=native['C']['tracks'][index]
                self.assertAlmostEqual(observed['mixer']['volume_db'],e['mixer']['volume_db']+trim,delta=.001)
                e['mixer']['volume_db']=observed['mixer']['volume_db']
                for lane,actual in zip(e['automation'],observed['automation']):
                    if lane['param']!='Volume':continue
                    self.assertEqual([v['at'] for v in lane['points']],[v['at'] for v in actual['points']])
                    for x,y in zip(lane['points'],actual['points']):
                        self.assertAlmostEqual(y['value'],x['value']+trim,delta=.001);x['value']=y['value']
            self.assertEqual(expected, native['C'])
            self.assertEqual(note_fingerprints(projects['A']), note_fingerprints(projects['C']))
            self.assertEqual((release/'A/song.mid').read_bytes(), (release/'C/song.mid').read_bytes())
            for row in report['causal_PCM'].values():
                self.assertTrue(row['measurable_change']);self.assertGreater(row['difference_to_original_rms_ratio'], .01)
            # Same-input C/A source processing and B/A groove have separate
            # real stem deltas; a parameter list cannot stand in for PCM proof.
            for role in ('kick', 'bass', 'clap', 'hats-percussion', 'stabs'):
                delta = compare_wavs(release/'controls'/('A-'+role+'.wav'), release/'controls'/('C-'+role+'.wav'))
                self.assertTrue(delta['measurable_change'], role)
                residual=gain_fit_residual(release/'controls'/('A-'+role+'.wav'),release/'controls'/('C-'+role+'.wav'))
                self.assertGreater(residual['residual_to_changed_rms_ratio'],.01)
                level=report['stems']['C'][role]['active']['rms_dbfs']-report['stems']['A'][role]['active']['rms_dbfs']
                self.assertLess(abs(level),.25)
            for role in ('bass', 'clap', 'hats-percussion', 'stabs'):
                self.assertTrue(compare_wavs(release/'controls'/('A-'+role+'.wav'),
                                            release/'controls'/('B-'+role+'.wav'))['measurable_change'])
            # A fresh supported native edit remains exact, editable and audible.
            p=projects['D'];op=SetParameter('set_parameter','instrument-kick','soundcraft.kick_decay',270)
            with self.assertRaisesRegex(AdapterError,'native apply does not yet edit instrument'):
                a.apply(release/'D/native',work/'unsupported',[op],Scope(['track-kick'],[],['soundcraft.kick_decay'],None,None),state_hash(p))
            self.assertFalse((work/'unsupported').exists())
            op=SetParameter('set_parameter','effect-kick-compression','soundcraft.attack',8)
            a.apply(release/'D/native', work/'edited', [op], Scope(['track-kick'],[],['soundcraft.attack'],None,None), state_hash(p))
            expected=deepcopy(native['D']);expected['tracks'][0]['mixer']['inserts'][1]['params']['attack']=8
            self.assertEqual(a.inspect(work/'edited')['native'],expected)
            a.save(work/'edited',work/'edit-saved');self.assertEqual(a.inspect(work/'edit-saved')['native'],expected)
            a.render(work/'edit-saved',work/'edited.wav',end_seconds=ACTIVE+TAIL)
            self.assertTrue(compare_wavs(release/'D/raw-with-release.wav',work/'edited.wav')['measurable_change'])
            self.assertFalse(report['human_listening']);self.assertFalse(report['full_song_expansion'])
            with zipfile.ZipFile(release/'phase12-house-listening.zip') as z:
                self.assertIsNone(z.testzip())
                for label in projects:
                    self.assertEqual(z.read('editable/'+label+'/native/session.scraft'), (release/label/'native/session.scraft').read_bytes())
                    self.assertEqual(z.read('editable/'+label+'/project.kuang.json'), (release/label/'project.kuang.json').read_bytes())
                self.assertFalse(any(n.endswith(('.so','.vst3','.dll','.mp3','.clap')) for n in z.namelist()))
            self.assertEqual(inventory([release]), before)

    def test_real_static_postfader_send_aux_prototype_and_exact_bypass(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            root=Path(d)/'routing'
            r=probe(root,os.environ['KUANG_SOUNDCRAFT'])
            self.assertTrue(r['host_native_send_aux_proven'])
            self.assertTrue(r['full_native_reopen_equal']);self.assertTrue(r['send_off_dry_PCM_exact'])
            self.assertFalse(r['production_adapter_support']['supported'])
            self.assertFalse(r['production_bus_used'])
            self.assertGreater(r['difference']['difference_to_original_rms_ratio'],.01)
            dry=r['tail']['dry']['after_notes']['rms'];wet=r['tail']['wet']['after_notes']['rms']
            self.assertGreater(wet,dry+1e-9)
