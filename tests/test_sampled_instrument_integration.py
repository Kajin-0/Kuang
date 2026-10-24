"""Actual sampler asset lifecycle and full-song context; no downloads."""
import json
import os
import shutil
import tempfile
import unittest
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.atmosphere import atmosphere_house
from kuang.audio import compare_wavs
from kuang.depth import note_fingerprints
from kuang.gestures import crop
from kuang.loudness import measure
from kuang.producer import package_preferred,read_audition,review_history
from kuang.sample_assets import create_asset,digest,inventory,read_asset,verify_native_audio,write
from kuang.sampled_instrument import SampledInstrumentAdapter
from kuang.schema import ValidationError,dumps,load,state_hash
from kuang.transactions import Scope,SetParameter,receipt_from_dict,replay
from test_sample_assets import ROOT,SCRATCH,credit,mapping,wav
from tools.producer_reference import build


@unittest.skipUnless(os.environ.get('KUANG_SOUNDCRAFT_INTEGRATION')=='1','opt in to installed SoundCraft sampler proof')
class SampledInstrumentIntegrationTests(unittest.TestCase):
    def test_full_phase10_instrument_audition_notes_state_context_and_no_false_promotion(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as folder:
            work=Path(folder);supplied=os.environ.get('KUANG_PRODUCER_RELEASE')
            if supplied:release=Path(supplied)
            else:
                release=work/'release'
                build(release,ROOT/'artifacts/phase10-house',os.environ['KUANG_SOUNDCRAFT'],os.environ.get('KUANG_EBUR128'))
            root=release/'full-song-audition';before=inventory(release);r=read_audition(root)
            p=load(root/'A/project.kuang.json');q=load(root/'B/project.kuang.json')
            self.assertEqual(dumps(p),dumps(atmosphere_house()))
            self.assertEqual((q.bars,q.tempo_bpm,q.key_tonic,q.key_mode),(64,126,0,'minor'))
            self.assertEqual(q.sections,p.sections);self.assertEqual(q.automation,p.automation)
            self.assertEqual(q.metadata['song_spec'],p.metadata['song_spec'])
            self.assertEqual(note_fingerprints(q),note_fingerprints(p));self.assertEqual(sum(len(c.notes) for t in q.tracks for c in t.clips),1536)
            self.assertEqual((root/'A/song.mid').read_bytes(),(root/'B/song.mid').read_bytes())
            self.assertEqual(digest(root/'A/raw.wav'),digest(ROOT/'artifacts/phase10-house/D-phase10-combined-native.wav'))
            a=SampledInstrumentAdapter(os.environ['KUANG_SOUNDCRAFT'],workspace=ROOT)
            a.save(root/'B/native',work/'saved');n=a.inspect(work/'saved')['native']
            self.assertEqual(n,a.inspect(root/'B/native')['native']);self.assertEqual(dumps(a.import_project(work/'saved')),dumps(q))
            self.assertEqual(len(n['markers']),6)
            for t,h in zip(q.tracks,n['tracks']):
                observed=[(x['start'],x['length'],x['pitch'],x['velocity'],x['channel'],x['release_velocity'])
                    for c in h['playlists'][0]['clips'] for x in c['content']['Midi']['sequence']['notes']]
                expected=[(c.start+x.start,x.duration,x.pitch,x.velocity,x.channel,0) for c in t.clips for x in c.notes]
                self.assertEqual(Counter(observed),Counter(expected))
                self.assertEqual([e['plugin'] for e in h['mixer']['inserts'] if e],[e.plugin_ref.split(':')[1] for e in t.effects])
            a.render(work/'saved',work/'repeated-full.wav',end_seconds=64*4*60/126+5)
            self.assertEqual(digest(work/'repeated-full.wav'),digest(root/'B/raw.wav'))
            # The independent unchanged context plus the instrument reconstructs
            # both full mixes, including original automation, to quantization.
            for label in ('A','B'):
                self.assertLessEqual(r['independent_context_sum'][label]['peak_error_lsb'],12)
                m=r['levels'][label];self.assertEqual((m['sample_rate'],m['channels'],m['bits_per_sample']),(48000,2,24))
                self.assertEqual(m['clipped_samples'],0);self.assertLess(m['true_peak_dbtp'],-1)
                self.assertEqual(m['frames'],6091429)
            for view in ('full','instrument'):
                meters=[measure(root/'listening'/(label+'-'+view+'-LUFS-matched.wav'),library=os.environ.get('KUANG_EBUR128')) for label in ('A','B')]
                self.assertAlmostEqual(meters[0]['integrated_lufs'],meters[1]['integrated_lufs'],delta=.002)
            self.assertTrue(compare_wavs(root/'A/raw.wav',root/'B/raw.wav')['measurable_change'])
            self.assertEqual(r['preference'],'unreviewed');self.assertFalse(r['quality_improvement_established'])
            self.assertEqual(review_history(root),[])
            with self.assertRaises(ValidationError):package_preferred(root,work/'false-music-release.zip')
            self.assertFalse((work/'false-music-release.zip').exists());self.assertEqual(inventory(release),before)

    def test_mono_stereo_multiasset_relocation_live_edit_exact_receipts_and_drift(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as folder:
            work=Path(folder);library=work/'library';library.mkdir()
            create_asset(wav(library/'kick.wav'),library/'kick',credit(),mapping())
            create_asset(wav(library/'tone.wav',width=2,channels=2),library/'tone',credit(),
                mapping(root_note=60,key_low=60,key_high=72,key_tracking=True,playback='gate'))
            p=crop(atmosphere_house(),32,2,['track-kick','track-lead'])
            # Diagnostic isolates sample envelopes; it does not rewrite the
            # released song or masquerade as a chosen production patch.
            p.automation=[]
            for t in p.tracks:t.effects=[];t.controls['mixer.gain_db']=-12
            a=SampledInstrumentAdapter(os.environ['KUANG_SOUNDCRAFT'],workspace=ROOT)
            assignments={'track-kick':library/'kick','track-lead':library/'tone'}
            a.export(p,assignments,work/'native');q=a.import_project(work/'native')
            before=a.inspect(work/'native')['native'];self.assertEqual(len(before['sources']),2)
            self.assertEqual([x['channels'] for x in before['sources']],[1,2])
            self.assertEqual(before['tracks'][1]['instrument']['params']['root_note'],60)
            self.assertEqual(before['tracks'][1]['instrument']['params']['key_track'],1)
            for t,h in zip(q.tracks,before['tracks']):
                m=read_asset(work/'native/assets'/t.id);source=next(s for s in before['sources'] if s['id']==h['instrument']['sample'])
                verify_native_audio(work/'native'/source['path'],m['audio'])
            a.render(work/'native',work/'first.wav',end_seconds=8)
            with self.assertRaisesRegex(ValidationError,'truncate'):
                a.render(work/'native',work/'truncated.wav',end_seconds=1)
            self.assertFalse((work/'truncated.wav').exists())
            a.save(work/'native',work/'saved');shutil.copytree(work/'saved',work/'relocated')
            (work/'native').rename(work/'hidden-native');(work/'saved').rename(work/'hidden-saved');library.rename(work/'hidden-library')
            a.render(work/'relocated',work/'second.wav',end_seconds=8)
            self.assertEqual(digest(work/'first.wav'),digest(work/'second.wav'))
            self.assertEqual(a.inspect(work/'relocated')['native'],before)
            self.assertEqual(dumps(a.import_project(work/'relocated')),dumps(q))
            op=SetParameter('set_parameter','instrument-lead','sample.level_db',-9)
            a.apply(work/'relocated',work/'edited',[op],Scope(['track-lead'],[],['sample.level_db'],None,None),state_hash(q))
            expected=deepcopy(before);expected['tracks'][1]['instrument']['params']['level']=-9
            self.assertEqual(a.inspect(work/'edited')['native'],expected)
            r=receipt_from_dict(json.loads((work/'edited/receipt.json').read_text()));new=a.import_project(work/'edited')
            self.assertEqual(dumps(replay(new,r,undo=True)),dumps(q));self.assertEqual(dumps(replay(q,r,undo=False)),dumps(new))
            a.save(work/'edited',work/'edit-saved');a.render(work/'edit-saved',work/'edited.wav',end_seconds=8)
            self.assertTrue(compare_wavs(work/'first.wav',work/'edited.wav')['measurable_change'])
            # Changed native sources/paths are negative fixtures only. They
            # are never written to a host to invent unsupported functionality.
            shutil.copytree(work/'relocated',work/'corrupt')
            n=json.loads((work/'corrupt/session.scraft').read_text());n['sources'][0]['path']='../outside.wav'
            write(work/'corrupt/session.scraft',n)
            m=json.loads((work/'corrupt/manifest.json').read_text());files=inventory(work/'corrupt');files.pop('manifest.json');m['files']=files
            write(work/'corrupt/manifest.json',m)
            with self.assertRaises(ValidationError):a.render(work/'corrupt',work/'bad.wav',end_seconds=8)
            self.assertFalse((work/'bad.wav').exists())
            media=next((work/'relocated/Audio Files').glob('*.wav'));media.unlink()
            with self.assertRaises(ValidationError):a.save(work/'relocated',work/'missing-source')
            self.assertFalse((work/'missing-source').exists())
