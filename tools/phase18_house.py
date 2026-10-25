#!/usr/bin/env python3
"""Build a fresh editable extended record from the human-approved Phase17 B."""
import argparse,json,os,shutil,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.house_composition import compose_record,SOURCE_HASH
from kuang.composition_analysis import audit_composition
from kuang.schema import load,save,state_hash,ValidationError
from kuang.production_host import ProductionAdapter
from kuang.midi import export_bytes
from kuang.sample_assets import digest,inventory,write
from kuang.loudness import measure
from kuang.mastering import match_lufs
from kuang.production_audio import production_metrics
from kuang.spatial_audio import spatial_metrics
from kuang.lowend_audio import band_metrics

END=160*4*60/126+5
AUDIO={'A':'A-Phase17-approved-native.wav','B':'B-Phase18-extended-native.wav'}

def adapter(host,plugin):
 return ProductionAdapter(host,plugin=plugin,workspace=ROOT,scratch=ROOT/'.local/phase18/tmp',center_pitch_bend=True)

def media(root,p):
 root=Path(root)
 return ({t.id:root/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'},
         {t.id:root/'native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')})

def assert_audit(a):
 for key in ('out_of_key_intervals','non_chord_harmonic_layer_intervals','non_chord_bass_intervals','bridge_wrong_root_note_ids'):
  if a[key]:raise ValidationError('arrangement harmony audit failed '+key)
 if a['unique_eight_bar_signatures_without_velocity']<18:raise ValidationError('arrangement lacks declared phrase developments')

def build(dest,host,plugin,meter=None):
 dest=Path(dest).resolve()
 if dest.exists() or dest.is_symlink() or not dest.is_relative_to(ROOT/'.local/phase18'):raise ValidationError('fresh project-local Phase18 staging required')
 src=ROOT/'artifacts/phase17-house/B';before=inventory(src);old=load(src/'project.kuang.json');p,receipt=compose_record(old)
 audit=audit_composition(old,p,receipt);assert_audit(audit);a=adapter(host,plugin);assets,patches=media(src,p)
 dest.mkdir()
 try:
  (dest/'source').mkdir();save(old,dest/'source/phase17-approved.kuang.json');(dest/'source/phase17-approved.mid').write_bytes(export_bytes(old))
  (dest/'B').mkdir();save(p,dest/'B/project.kuang.json');(dest/'B/song.mid').write_bytes(export_bytes(p));write(dest/'B/source-song-spec.json',json.loads(old.metadata['song_spec']))
  write(dest/'composition-receipt.json',receipt);write(dest/'harmonic-audit.json',audit)
  shutil.copyfile(src.parent/'B-Phase17-mix-native.wav',dest/AUDIO['A'])
  a.export(p,assets,patches,dest/'B/native');a.render(dest/'B/native',dest/AUDIO['B'],end_seconds=END)
  with tempfile.TemporaryDirectory(dir=a.scratch) as d:
   d=Path(d);a.save(dest/'B/native',d/'saved');a.render(d/'saved',d/'repeat.wav',end_seconds=END)
   if a.inspect(dest/'B/native')['native']!=a.inspect(d/'saved')['native'] or digest(dest/AUDIO['B'])!=digest(d/'repeat.wav'):raise ValidationError('full160-bar native state/PCM reload failed')
  for tid,path in patches.items():
   if inventory(path)!=inventory(dest/'B/native/patches'/tid):raise ValidationError('approved patch changed')
  for tid,path in assets.items():
   if inventory(path)!=inventory(dest/'B/native/assets'/tid):raise ValidationError('approved sample changed')
  levels={k:measure(dest/name,library=meter) for k,name in AUDIO.items()}
  if any(x['clipped_samples'] or x['true_peak_dbtp']>-1 or x['rms']<=0 for x in levels.values()):raise ValidationError('non-silence/headroom gate failed')
  (dest/'listening').mkdir();target=min(x['integrated_lufs'] for x in levels.values())
  matching={k:match_lufs(dest/name,dest/'listening'/(k+'-'+('Phase17-approved-2min' if k=='A' else 'Phase18-extended-5min')+'-LUFS-matched.wav'),target,library=meter) for k,name in AUDIO.items()}
  regions=[(s.name,s.start/p.ppq*60/126,(s.start+s.length)/p.ppq*60/126) for s in p.sections]
  spatial=spatial_metrics(dest/AUDIO['B']);sections=production_metrics(dest/AUDIO['B'],regions)['sections']
  bands={name:band_metrics(dest/AUDIO['B'],first=lo,last=hi,windows=4) for name,lo,hi in regions}
  if spatial['bands']['low_20_120']['mono_energy_retention']<.9999 or spatial['mono_sum']['rms_loss_db']<-.25:raise ValidationError('mono compatibility failed')
  report={'version':'phase18-verification-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),
   'incumbent':'Phase17 B: user approved sound/production, requested fuller arrangement','candidate_preference':'unreviewed','professional_quality_claimed':False,
   'performance':{'bars':160,'bpm':126,'key':'C minor','sections':8,'note_records':len(receipt['note_origins']),'source_note_records':1536,'MIDI_bytes_exact':False,'original_instruments_graph_patches_samples_exact':True,
    'approved_statement_note_fields_exact':audit['approved_first_statement_exact'],'approved_translated_return_note_fields_exact':audit['approved_translated_return_exact'],'unique_eight_bar_signatures_excluding_velocity':audit['unique_eight_bar_signatures_without_velocity']},
   'native_state_and_PCM_reopen_exact':True,'A_PCM_exact':digest(dest/AUDIO['A'])==digest(src.parent/'B-Phase17-mix-native.wav'),
   'levels':levels,'matching':matching,'spatial_B':spatial,'sections_B':sections,'section_bands_B':bands,
   'comparison':'Two COMPLETE records of different duration; same integrated loudness, NOT an aligned null comparison or a same-length mix A/B',
   'sidechain':'Retained scheduled MIDI-derived attenuation, not an audio-triggered detector route','mastering':'none; constant attenuation listening copies only'}
  write(dest/'verification.json',report)
  write(dest/'recipe.json',{'version':'phase18-replay-1','source_hash':SOURCE_HASH,'candidate_hash':state_hash(p),'raw_A_sha256':digest(dest/AUDIO['A']),'raw_B_sha256':digest(dest/AUDIO['B']),'end_seconds':END,
     'patch_manifest_sha256':{k:digest(v/'manifest.json') for k,v in patches.items()},'composition_receipt_sha256':digest(dest/'composition-receipt.json')})
  shutil.copytree(src.parent/'licenses',dest/'licenses')
  if inventory(src)!=before:raise ValidationError('incumbent source changed')
 except BaseException:shutil.rmtree(dest);raise
 return report

def prepare_download(root):
 root=Path(root)
 if any((root/n).exists() for n in ('README.md','reproduce.py','reproduction')):raise ValidationError('new download inputs required')
 shutil.copyfile(ROOT/'docs/PHASE18_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase18_reproduce.py',root/'reproduce.py')
 frozen=root/'reproduction';(frozen/'kuang').mkdir(parents=True)
 for p in (ROOT/'kuang').rglob('*'):
  if p.is_file() and p.suffix in ('.py','.lua','.json'):
   if p.is_symlink():raise ValidationError('frozen source symlink')
   target=frozen/'kuang'/p.relative_to(ROOT/'kuang');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 shutil.copyfile(ROOT/'LICENSE',frozen/'LICENSE');write(frozen/'source-manifest.json',inventory(frozen))

def package(root):
 root=Path(root);target=root/'phase18-house-listening.zip'
 if target.exists() or target.is_symlink():raise ValidationError('fresh listening ZIP required')
 files=[p for name in ('B','source','listening','licenses','reproduction') for p in (root/name).rglob('*') if p.is_file()]
 files += [root/n for n in ('README.md','reproduce.py','recipe.json','composition-receipt.json','harmonic-audit.json','verification.json','pitch-verification.json','gesture-verification.json')]
 if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files):raise ValidationError('unsupported bundled binary/media')
 manifest={str(p.relative_to(root)):digest(p) for p in files}
 with tempfile.TemporaryDirectory(dir=root) as d:
  zpath=Path(d)/'pack.zip'
  with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(files):z.write(p,str(p.relative_to(root)))
   z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
  with zipfile.ZipFile(zpath) as z:
   if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP integrity failed')
   if len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')])!=2:raise ValidationError('exactly two full song listening WAVs required')
  if zpath.stat().st_size>180_000_000:raise ValidationError('listening ZIP size limit')
  os.link(zpath,target)
 return {'bytes':target.stat().st_size,'sha256':digest(target)}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','package'));ap.add_argument('--out-dir',required=True);ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--meter-library');a=ap.parse_args()
 if a.action=='build' and not(a.soundcraft and a.plugin):ap.error('explicit reviewed host and plugin required')
 print(json.dumps(build(a.out_dir,a.soundcraft,a.plugin,a.meter_library) if a.action=='build' else package(a.out_dir),indent=2))
