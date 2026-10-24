"""Real optional full-song sampler palette and conversion lifecycle gates."""
import hashlib
import json
import math
import os
import subprocess
import sys
import shutil
import tempfile
import unittest
import wave
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

from kuang.drum_palette import note_inventory
from kuang.loudness import measure
from kuang.octalsamples import inspect_pack
from kuang.sample_assets import create_asset,digest,inventory,read_asset,write
from kuang.gestures import crop
from kuang.sample_conversion import SincConverter
from kuang.schema import ValidationError,dumps,load,state_hash
from kuang.transactions import Scope,SetParameter,receipt_from_dict,replay
from tools.phase13_house import adapter,window_rms,prepare_library,package
from tools.phase13_reproduce import reproduce

ROOT=Path(__file__).resolve().parents[1]
SCRATCH=ROOT/'.local/phase13/tests'


@unittest.skipUnless(os.environ.get('KUANG_PHASE13_INTEGRATION')=='1','opt in to separately prepared CC0 palette and real SoundCraft')
class Phase13IntegrationTests(unittest.TestCase):
    def test_full_song_notes_native_reopen_zip_relocation_and_exact_reproduction(self):
        root=Path(os.environ['KUANG_PHASE13_RELEASE']);before=inventory(root)
        p=load(root/'A/project.kuang.json');q=load(root/'B/project.kuang.json');r=json.loads((root/'verification.json').read_text())
        self.assertEqual(note_inventory(p),note_inventory(q));self.assertEqual(len(note_inventory(q)),1536)
        self.assertEqual((q.bars,q.tempo_bpm,q.key_tonic,q.key_mode),(64,126,0,'minor'))
        self.assertEqual(q.sections,p.sections);self.assertEqual(q.metadata['song_spec'],p.metadata['song_spec'])
        self.assertEqual(digest(root/'A-phase10-original-native.wav'),digest(ROOT/'artifacts/phase10-house/D-phase10-combined-native.wav'))
        self.assertTrue(all(x['peak_error_lsb']<=2 for x in r['independent_reconstruction'].values()))
        self.assertEqual(r['human_preference'],'unreviewed');self.assertFalse(r['professional_quality_established'])
        for m in r['levels'].values():
            self.assertEqual((m['sample_rate'],m['channels'],m['bits_per_sample'],m['frames']),(48000,2,24,6091429))
            self.assertEqual(m['clipped_samples'],0);self.assertLess(m['true_peak_dbtp'],-1)
        a=adapter(os.environ['KUANG_SOUNDCRAFT']);native=a.inspect(root/'B/native')['native']
        self.assertEqual(len(native['markers']),6)
        for t,h in zip(q.tracks,native['tracks']):
            got=Counter((n['start'],n['length'],n['pitch'],n['velocity'],n['channel']) for c in h['playlists'][0]['clips'] for n in c['content']['Midi']['sequence']['notes'])
            want=Counter((c.start+n.start,n.duration,n.pitch,n.velocity,n.channel) for c in t.clips for n in c.notes)
            self.assertEqual(got,want)
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            work=Path(d);a.save(root/'B/native',work/'saved')
            self.assertEqual(a.inspect(work/'saved')['native'],native)
            self.assertEqual(dumps(a.import_project(work/'saved')),dumps(q))
            zpath=root/'phase13-house-listening.zip'
            with zipfile.ZipFile(zpath) as z:
                self.assertIsNone(z.testzip());manifest=json.loads(z.read('zip-manifest.json'))
                self.assertEqual(set(z.namelist()),set(manifest)|{'zip-manifest.json'})
                self.assertTrue(all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in manifest.items()))
                self.assertEqual(len([k for k in z.namelist() if k.startswith('listening/') and k.endswith('.wav')]),2)
                self.assertFalse(any('internal-controls' in k for k in z.namelist()))
                z.extractall(work/'extracted')
            extracted=work/'extracted'
            # Physically hide the currently prepared original library, source
            # checkout and source native bundle. Restore every path in finally.
            hiding=[]
            try:
                for path in (ROOT/'.local/phase13/library-headroom',ROOT/'.local/phase13/octalsrc',root/'B/native'):
                    if path.exists():
                        target=path.with_name(path.name+'-hidden-gate')
                        self.assertFalse(target.exists());path.rename(target);hiding.append((path,target))
                a.render(extracted/'B/native',work/'relocated.wav',end_seconds=r['levels']['B']['duration_seconds'])
                self.assertEqual(digest(work/'relocated.wav'),digest(root/'B-phase13-drum-palette-native.wav'))
                process=subprocess.run([sys.executable,'-I',str(extracted/'reproduce.py'),'--source',str(extracted),
                    '--out',str(work/'reproduced'),'--workspace',str(ROOT),'--soundcraft',os.environ['KUANG_SOUNDCRAFT']],
                    cwd=work,capture_output=True,text=True,timeout=240,check=True)
                self.assertTrue(json.loads(process.stdout)['PCM_exact'])
            finally:
                for path,target in reversed(hiding):target.rename(path)
            op=SetParameter('set_parameter','instrument-hats.p46','sample.release_ms',60)
            a.apply(root/'B/native',work/'edited',[op],Scope(['track-hats.p46'],[],['sample.release_ms'],None,None),state_hash(q))
            expected=json.loads(json.dumps(native));i=next(i for i,t in enumerate(q.tracks) if t.id=='track-hats.p46')
            expected['tracks'][i]['instrument']['params']['release']=60
            self.assertEqual(a.inspect(work/'edited')['native'],expected)
            receipt=receipt_from_dict(json.loads((work/'edited/receipt.json').read_text()));edited=a.import_project(work/'edited')
            self.assertEqual(dumps(replay(edited,receipt,undo=True)),dumps(q));self.assertEqual(dumps(replay(q,receipt,undo=False)),dumps(edited))
            # Same one-note input and source PCM, gate versus one-shot. This
            # independently checks an actual envelope tail, not just a selector.
            hat=crop(q,32,1,['track-hats.p46']);hat.automation=[];hat.tracks[0].effects=[]
            clips=[c for c in hat.tracks[0].clips if c.notes];hat.tracks[0].clips=clips
            first=clips[0].notes[0];clips[0].notes=[first]
            for c in clips[1:]:c.notes=[]
            original_asset=root/'B/native/assets/track-hats.p46';m=read_asset(original_asset)
            a.export(hat,{'track-hats.p46':original_asset},work/'gate')
            a.render(work/'gate',work/'gate.wav',end_seconds=3)
            mp=dict(m['mapping']);mp['playback']='one_shot'
            create_asset(original_asset/m['file'],work/'one-shot-asset',m['provenance'],mp)
            control=deepcopy(hat);control.tracks[0].instrument.preset_ref='sha256:'+digest(work/'one-shot-asset/asset.json')
            a.export(control,{'track-hats.p46':work/'one-shot-asset'},work/'one-shot')
            a.render(work/'one-shot',work/'one-shot.wav',end_seconds=3)
            onset=(clips[0].start+first.start)/hat.ppq*60/hat.tempo_bpm
            tail_start=onset+first.duration/hat.ppq*60/hat.tempo_bpm+.10
            gate_db=window_rms(work/'gate.wav',tail_start,tail_start+.12)
            one_db=window_rms(work/'one-shot.wav',tail_start,tail_start+.12)
            self.assertTrue(gate_db is None or gate_db < -85)
            self.assertIsNotNone(one_db);self.assertGreater(one_db,-80)
            write(ROOT/'.local/phase13/gate-control.json',{'gate_tail_rms_dbfs':gate_db,
                'one_shot_tail_rms_dbfs':one_db,'same_input_note_fields':True,'source_PCM_identical':True,
                'window_after_note_off_seconds':[.10,.22]})
            meters=[measure(x,library=os.environ.get('KUANG_EBUR128')) for x in sorted((root/'listening').glob('*.wav'))]
            self.assertAlmostEqual(meters[0]['integrated_lufs'],meters[1]['integrated_lufs'],delta=.002)
            with self.assertRaises(ValidationError):reproduce(extracted,work/'reproduced',os.environ['KUANG_SOUNDCRAFT'],ROOT)
            with self.assertRaises(ValidationError):package(root)
        self.assertEqual(inventory(root),before)

    def test_reviewed_source_and_actual_best_sinc_analytical_vectors(self):
        pack=Path(os.environ['KUANG_PHASE13_PACK']);self.assertEqual(inspect_pack(pack)['samples'],44)
        c=SincConverter(os.environ['KUANG_SAMPLE_RATE_LIBRARY']);SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as d:
            root=Path(d);source=root/'tones.wav';data=bytearray()
            for i in range(11025):
                for f in (1000,18000):data+=round(.3*math.sin(2*math.pi*f*i/44100)*2**23).to_bytes(3,'little',signed=True)
            with wave.open(str(source),'wb') as w:w.setparams((2,3,44100,0,'NONE',''));w.writeframes(data)
            r=c.convert(source,root/'out.wav');c.convert(source,root/'repeat.wav')
            self.assertEqual(digest(root/'out.wav'),digest(root/'repeat.wav'));self.assertEqual(r['gain_db'],0)
            with wave.open(str(root/'out.wav'),'rb') as w:w.setpos(2400);raw=w.readframes(7200)
            channels=[[int.from_bytes(raw[i*6+ch*3:i*6+ch*3+3],'little',signed=True)/2**23 for i in range(7200)] for ch in (0,1)]
            errors=[]
            for ch,f in enumerate((1000,18000)):
                error=math.sqrt(sum((x-.3*math.sin(2*math.pi*f*(i+2400)/48000))**2 for i,x in enumerate(channels[ch]))/7200)
                self.assertLess(error,1e-5);errors.append(error)
            image=2*abs(sum(x*complex(math.cos(2*math.pi*21900*i/48000),math.sin(2*math.pi*21900*i/48000)) for i,x in enumerate(channels[1])))/7200
            self.assertLess(image/.3,10**(-95/20))
            impulse=root/'impulse.wav';raw=bytearray(11025*3);raw[2205*3:2205*3+3]=round(.3*2**23).to_bytes(3,'little',signed=True)
            with wave.open(str(impulse),'wb') as w:w.setparams((1,3,44100,0,'NONE',''));w.writeframes(raw)
            c.convert(impulse,root/'impulse-out.wav')
            with wave.open(str(root/'impulse-out.wav'),'rb') as w:out=w.readframes(w.getnframes())
            values=[int.from_bytes(out[i:i+3],'little',signed=True) for i in range(0,len(out),3)]
            self.assertEqual(max(range(len(values)),key=lambda i:abs(values[i])),2400)
            with self.assertRaises(ValidationError):c.convert(source,root/'out.wav')
            for gain in (1,float('nan'),-99):
                with self.assertRaises(ValidationError):c.convert(source,root/'bad.wav',gain_db=gain)
            self.assertFalse((root/'bad.wav').exists())
            copied=root/'tampered-pack';shutil.copytree(pack,copied,ignore=shutil.ignore_patterns('.git'))
            changed=copied/'samples/kicks/punch-02.wav';b=bytearray(changed.read_bytes());b[-11]^=1;changed.write_bytes(b)
            with self.assertRaises(ValidationError):inspect_pack(copied)
            with self.assertRaises(ValidationError):prepare_library(copied,root/'bad-library',os.environ['KUANG_SAMPLE_RATE_LIBRARY'])
            self.assertFalse((root/'bad-library').exists())
            prepared=root/'prepared-library';result=prepare_library(pack,prepared,os.environ['KUANG_SAMPLE_RATE_LIBRARY'])
            self.assertEqual(result['assets'],16)
            original=ROOT/'.local/phase13/library-headroom'
            for asset in prepared.iterdir():
                if asset.is_dir():self.assertEqual(digest(asset/'asset.json'),digest(original/asset.name/'asset.json'))
            with self.assertRaises(ValidationError):prepare_library(pack,prepared,os.environ['KUANG_SAMPLE_RATE_LIBRARY'])
            write(ROOT/'.local/phase13/conversion-golden.json',{'passband_1k_18k_rms_errors':errors,
                'image_21900_relative_amplitude':image/.3,'image_required_below_db':-95,'impulse_50ms_frame':2400,
                'repeat_PCM_exact':True,'converter':r})
