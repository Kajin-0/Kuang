import os,json,unittest,tempfile,subprocess,sys,zipfile,shutil
from pathlib import Path
from kuang.schema import load
from kuang.groove_direction import audit_direction
from kuang.sample_assets import digest,inventory
from kuang.loudness import measure
from tools.phase26_house import adapter,RAW,END,LISTEN,ROOT
from tools.phase26_pitch import pitch
@unittest.skipUnless(os.environ.get('KUANG_PHASE26_INTEGRATION')=='1','optional real Phase26 composition')
class DirectionNativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(os.environ['KUANG_PHASE26_RELEASE']);cls.host=os.environ['KUANG_SOUNDCRAFT'];cls.plugin=os.environ['KUANG_VITALIUM_PLUGIN'];cls.a=adapter(cls.host,cls.plugin);cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.local/phase26/tmp');cls.w=Path(cls.temp.name)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_actual_new_notes_chords_in_two_hosts(self):
  r=pitch(self.root,self.w/'pitch',self.host,self.plugin,os.environ['KUANG_VITALIUM_HOST_PYTHON']);self.assertEqual(r['native_pitch_center'],.5)
 def test_native_full_score_sources_and_reopen_PCM(self):
  s=load(self.root/'phase25-source.kuang.json');p=load(self.root/'project/project.kuang.json');audit_direction(s,p,json.loads((self.root/'composition-receipt.json').read_text()))
  for name in ('assets','patches'):self.assertEqual(inventory(self.root/'project/native'/name),inventory(ROOT/'artifacts/phase25-house/project/native'/name))
  self.a.save(self.root/'project/native',self.w/'saved');self.a.render(self.w/'saved',self.w/'repeat.wav',end_seconds=END);self.assertEqual(digest(self.w/'repeat.wav'),digest(self.root/RAW));self.assertEqual(self.a.inspect(self.w/'saved')['native'],self.a.inspect(self.root/'project/native')['native'])
 def test_full_matched_audio_and_anchor_evidence(self):
  levels=[measure(self.root/'listening'/LISTEN[k],library=os.environ['KUANG_EBUR128']) for k in ('A','B')]
  self.assertLess(abs(levels[0]['integrated_lufs']-levels[1]['integrated_lufs']),.001)
  for x in levels:self.assertEqual((x['sample_rate'],x['bits_per_sample'],x['channels'],x['clipped_samples']),(48000,24,2,0));self.assertGreater(x['rms'],0)
  v=json.loads((self.root/'verification.json').read_text());self.assertTrue(v['full_reset_anchor_PCM_exact']);self.assertFalse(v['mastering'])
 def test_extracted_relocation_with_original_sources_hidden(self):
  with zipfile.ZipFile(self.root/'phase26-house-listening.zip') as z:
   self.assertIsNone(z.testzip());self.assertEqual(len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')]),2);z.extractall(self.w/'extracted')
  cloned=self.w/'plugin/vitalium.vst3';cloned.parent.mkdir();shutil.copytree(self.plugin,cloned);hidden=[]
  try:
   for path in (self.root/'project/native',ROOT/'artifacts/phase25-house/project/native',Path(self.plugin)):
    target=path.with_name(path.name+'-phase26-hidden');self.assertFalse(target.exists());path.rename(target);hidden.append((path,target))
   r=subprocess.run([sys.executable,'-I',str(self.w/'extracted/reproduce.py'),'--source',str(self.w/'extracted'),'--out',str(self.w/'replay'),'--workspace',str(ROOT),'--soundcraft',self.host,'--plugin',str(cloned)],capture_output=True,text=True,timeout=600);self.assertEqual(r.returncode,0,r.stderr[-4000:]);self.assertTrue(json.loads(r.stdout)['raw_and_matched_PCM_exact'])
  finally:
   for a,b in reversed(hidden):b.rename(a)
