#!/usr/bin/env python3
"""Build four editable main16 auditions; never extend an unselected theme."""
import argparse,json,os,shutil,sys,tempfile,zipfile
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kuang.house_shortlist import main_reference,compose_candidate,SOURCE_HASH,REFERENCE_HASH
from kuang.shortlist_audit import audit_shortlist,require_shortlist
from kuang.schema import load,save,state_hash,ValidationError,validate
from kuang.master_bus import MasterBusAdapter,terminal_projection
from kuang.midi import export_bytes
from kuang.sample_assets import digest,inventory,write
from kuang.loudness import measure
from kuang.mastering import match_lufs
from kuang.audio import compare_wavs
from kuang.spatial_audio import spatial_metrics
END=16*4*60/126+5
OPTIONS={'A':'Phase21-incumbent','B':'Soulful-Amber-conversation','C':'Progressive-The-long-way-home','D':'Hypnotic-Afterimage'}
DIRECTIONS={'B':'soulful','C':'progressive','D':'hypnotic'}

def adapter(host,plugin,workspace=ROOT):
 return MasterBusAdapter(host,plugin=plugin,workspace=workspace,scratch=Path(workspace)/'.local/phase22/tmp',center_pitch_bend=True)

def media(root,p):
 root=Path(root)
 return ({t.id:root/'native/assets'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref=='soundcraft:sampler'},
         {t.id:root/'native/patches'/t.id for t in p.tracks if t.instrument and t.instrument.plugin_ref.startswith('vst3:')})

def stem(project,ids):
 terminal_projection(project);ids=set(ids);by={t.id:t for t in project.tracks};pending=list(ids)
 while pending:
  for s in by[pending.pop()].sends:
   if s.target_track_id not in ids:ids.add(s.target_track_id);pending.append(s.target_track_id)
 q=deepcopy(project);q.tracks=[t for t in q.tracks if t.id in ids]
 owners={x for t in q.tracks for x in (t.id,*([t.instrument.id] if t.instrument else []),*(e.id for e in t.effects))}
 q.automation=[a for a in q.automation if a.target_id in owners];q.locks=[];terminal_projection(q);return q

def build(destination,host,plugin,meter=None):
 if Path(destination).is_symlink():raise ValidationError('symlink staging prohibited')
 dest=Path(destination).resolve()
 if dest.exists() or dest.is_symlink() or not dest.is_relative_to(ROOT/'.local/phase22'):raise ValidationError('fresh Phase22 staging required')
 src=ROOT/'artifacts/phase21-house/B';before=inventory(src);source=load(src/'project.kuang.json');reference=main_reference(source)
 if state_hash(reference)!=REFERENCE_HASH:raise ValidationError('main16 incumbent drift')
 assets,patches=media(src,reference);a=adapter(host,plugin);dest.mkdir();(dest/'raw').mkdir();(dest/'listening').mkdir()
 results={};receipts={};audits={};levels={}
 for label,title in OPTIONS.items():
  if label=='A':p=reference
  else:
   p,r=compose_candidate(reference,DIRECTIONS[label]);audits[label]=require_shortlist(audit_shortlist(reference,p,r));receipts[label]=r
  folder=dest/label;folder.mkdir();save(p,folder/'project.kuang.json');(folder/'song.mid').write_bytes(export_bytes(p))
  if label!='A':write(folder/'composition-receipt.json',r);write(folder/'score-audit.json',audits[label])
  a.export(p,assets,patches,folder/'native');raw=dest/'raw'/(label+'-'+title+'-native.wav');a.render(folder/'native',raw,end_seconds=END)
  with tempfile.TemporaryDirectory(dir=a.scratch) as d:
   d=Path(d);a.save(folder/'native',d/'saved');a.render(d/'saved',d/'repeat.wav',end_seconds=END)
   if a.inspect(folder/'native')['native']!=a.inspect(d/'saved')['native'] or digest(raw)!=digest(d/'repeat.wav'):raise ValidationError('native state/PCM reopen drift '+label)
  for tid,path in {**assets,**patches}.items():
   if inventory(path)!=inventory(folder/'native'/('assets' if tid in assets else 'patches')/tid):raise ValidationError('approved palette drift')
  levels[label]=measure(raw,library=meter)
  if levels[label]['clipped_samples'] or levels[label]['rms']<=0:raise ValidationError('invalid actual PCM')
  results[label]={'title':title,'canonical_hash':state_hash(p),'raw_sha256':digest(raw),'native_state_and_PCM_reopen_exact':True,'spatial':spatial_metrics(raw)}
  if results[label]['spatial']['bands']['low_20_120']['mono_energy_retention']<.999:raise ValidationError('sub no longer mono-safe')
  print(label,title,'native16/reopen/media/PCM pass',flush=True)
 expected=json.loads((ROOT/'artifacts/phase21-house/main16/verification.json').read_text())['B']['sha256']
 if results['A']['raw_sha256']!=expected:raise ValidationError('incumbent16 audio not exact')
 target=min(v['integrated_lufs'] for v in levels.values());matches={}
 for label,title in OPTIONS.items():matches[label]=match_lufs(dest/'raw'/(label+'-'+title+'-native.wav'),dest/'listening'/(label+'-'+title+'-MATCHED.wav'),target,library=meter)
 differences={}
 for i,x in enumerate(OPTIONS):
  for y in list(OPTIONS)[i+1:]:
   delta=compare_wavs(dest/'raw'/(x+'-'+OPTIONS[x]+'-native.wav'),dest/'raw'/(y+'-'+OPTIONS[y]+'-native.wav'))
   if delta['difference_to_original_rms_ratio']<.05:raise ValidationError('composition pair barely changes actual audio')
   differences[x+y]=delta
 report={'version':'phase22-native-shortlist-1','full_source_hash':SOURCE_HASH,'reference_hash':REFERENCE_HASH,'bars':16,'bpm':126,'key':'C minor family','duration_seconds':END,
         'results':results,'raw_levels':levels,'matching':matches,'pairwise_PCM_differences':differences,'all_four_original_patch_and_sample_states_exact':True,
         'A_is_exact_existing_Phase21_main16_PCM':True,'same_mix_and_expression':True,'new_full_song':False,'mastering':False,'human_preference':'unreviewed','professional_quality_claimed':False}
 write(dest/'verification.json',report)
 write(dest/'recipe.json',{'version':'phase22-replay-1','source_hash':SOURCE_HASH,'reference_hash':REFERENCE_HASH,'end_seconds':END,
       'projects':{k:{'hash':v['canonical_hash'],'raw_sha256':v['raw_sha256'],'receipt_sha256':digest(dest/k/'composition-receipt.json') if k!='A' else None} for k,v in results.items()},
       'asset_manifests':{k:digest(v/'asset.json') for k,v in assets.items()},'patch_manifests':{k:digest(v/'manifest.json') for k,v in patches.items()}})
 shutil.copytree(ROOT/'artifacts/phase21-house/licenses',dest/'licenses')
 if inventory(src)!=before:raise ValidationError('historical source changed')
 return report

def prepare(root):
 root=Path(root);frozen=root/'reproduction'
 if frozen.exists():raise ValidationError('fresh preparation required')
 shutil.copyfile(ROOT/'docs/PHASE22_LISTENING_README.md',root/'README.md');shutil.copyfile(ROOT/'tools/phase22_reproduce.py',root/'reproduce.py')
 for p in (ROOT/'kuang').rglob('*'):
  if p.is_file() and p.suffix in ('.py','.lua','.json'):
   if p.is_symlink():raise ValidationError('source symlink')
   out=frozen/'kuang'/p.relative_to(ROOT/'kuang');out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
 shutil.copyfile(ROOT/'LICENSE',frozen/'LICENSE');write(frozen/'source-manifest.json',inventory(frozen))

def package(root):
 root=Path(root);target=root/'phase22-composer-shortlist.zip'
 if target.exists() or target.is_symlink():raise ValidationError('fresh shortlist ZIP required')
 files=[p for n in (*OPTIONS,'listening','licenses','reproduction') for p in (root/n).rglob('*') if p.is_file()]
 files += [root/n for n in ('README.md','reproduce.py','recipe.json','verification.json','pitch-verification.json','context-verification.json')]
 if any(p.is_symlink() or p.suffix in ('.so','.dll','.mp3') for p in files):raise ValidationError('foreign binary/content prohibited')
 manifest={str(p.relative_to(root)):digest(p) for p in files}
 with tempfile.TemporaryDirectory(dir=root) as d:
  out=Path(d)/'pack.zip'
  with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(files):z.write(p,str(p.relative_to(root)))
   z.writestr('zip-manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
  with zipfile.ZipFile(out) as z:
   if z.testzip() or any(__import__('hashlib').sha256(z.read(k)).hexdigest()!=v for k,v in manifest.items()):raise ValidationError('ZIP corruption')
   if len([n for n in z.namelist() if n.startswith('listening/') and n.endswith('.wav')])!=4:raise ValidationError('four primary full-mix auditions required')
  if out.stat().st_size>100_000_000:raise ValidationError('shortlist pack exceeds100MB')
  os.link(out,target)
 return {'bytes':target.stat().st_size,'sha256':digest(target)}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('build','prepare','package'));ap.add_argument('--out-dir',required=True);ap.add_argument('--soundcraft');ap.add_argument('--plugin');ap.add_argument('--meter-library');z=ap.parse_args()
 if z.action=='build' and not(z.soundcraft and z.plugin):ap.error('reviewed host/plugin required')
 result=build(z.out_dir,z.soundcraft,z.plugin,z.meter_library) if z.action=='build' else prepare(z.out_dir) if z.action=='prepare' else package(z.out_dir)
 print(json.dumps(result,indent=2))
