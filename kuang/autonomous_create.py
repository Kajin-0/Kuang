"""Private one-prompt house sketch using auditioned third-party Vital presets.

This separate opt-in workflow never changes the original-only adapter validator.
Third-party states and outputs are private, and their licenses are not established.
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from . import midi
from .autonomous_palette import (MAX_CATALOG_BYTES, _bounded_read, _plugin_info, _read_preset, _validate_patch,
                                 select_palette)
from ._private_vital_worker import wave_frames
from .composer import compose
from .external_synth import (ExternalSynthAdapter, HOST_SHA, CONTRACT, LAYOUT_SHA,
                             PLUGIN_ID, VERSION, _SandboxSoundCraft, digest, inventory, write)
from .generator import generate
from .loudness import measure
from .production import refine_house
from .production_host import ProductionAdapter
from .schema import BAR, Clip, Instrument, Note, ParameterSpec, Section, ValidationError, save, strict_json, validate
from .song import rules_plan, validate_spec
from .soundcraft import _hash, _read_json
from .vitalium_patch import chunks, component_patch


def read_private_patch(path, selected, preset_root, plugin_sha):
    """Recheck private bundle, live catalog source and all controller identities."""
    path = Path(path)
    m = _read_json(path/'manifest.json')
    if (type(m) is not dict or m.get('version') != 'private-selected-vital-1' or
        m.get('plugin') != PLUGIN_ID or m.get('plugin_version') != VERSION or
        m.get('plugin_sha256') != plugin_sha or m.get('license') != 'unknown; private local use only'):
        raise ValidationError('unverified private preset manifest')
    sha = m.get('source_sha256')
    entry = selected.get(sha)
    if not entry or entry.get('status') != 'accepted' or entry.get('runtime_verified') is not True:
        raise ValidationError('preset was not selected by verified audition')
    source = _read_preset(preset_root, entry['path'], entry['catalog_size'], sha)
    patch = _validate_patch(source, {'compatibility':'version_candidate','synth_version':entry['catalog_version']})
    files = {'patch.vital','patch.vstpreset','component.bin','bindings.json'}
    if (set(m.get('sha256',{})) != files or inventory(path) != {**m['sha256'],'manifest.json':digest(path/'manifest.json')} or
        any((path/f).stat().st_size > 4*1024*1024 for f in files) or
        (path/'patch.vital').read_bytes() != source or m.get('source_version') != entry['catalog_version'] or
        m.get('source_name') != patch['preset_name'] or m.get('source_author') != patch.get('author')):
        raise ValidationError('private preset or original source changed')
    state = (path/'component.bin').read_bytes()
    actual = component_patch(state)
    if (chunks((path/'patch.vstpreset').read_bytes())[b'Comp'] != state or
        actual.get('preset_name') != patch['preset_name'] or actual.get('author') != patch.get('author') or
        actual.get('settings',{}).get('sample_on') != 0 or wave_frames(actual) != wave_frames(patch)):
        raise ValidationError('private component identity or sample state differs')
    rows = _read_json(path/'bindings.json'); defaults = m.get('native_defaults')
    if (type(defaults) is not dict or len(defaults) != 2851 or
        any(not k.isdecimal() or type(v) not in (int,float) or not math.isfinite(v) for k,v in defaults.items()) or
        type(rows) is not list or len(rows) != 771 or
        _hash([{k:v for k,v in row.items() if k != 'normalized'} for row in rows]) != LAYOUT_SHA):
        raise ValidationError('private controller layout/defaults differ')
    seen = set()
    for row in rows:
        idx = row['index']; native = 0
        for ch in str(idx): native = (31*native+ord(ch)) & 0x7fffffff
        value = row['normalized']; scale = row['scale']
        if (idx in seen or row['native_id'] != str(native) or str(native) not in defaults or
            row['canonical_id'] != 'vitalium.param'+str(idx) or
            type(value) not in (int,float) or not math.isfinite(value) or not 0 <= value <= 1 or
            abs(defaults[str(native)]-row['default_normalized']*scale) > .00002 or
            (row['steps'] and abs(value*scale-round(value*scale)) > .00002)):
            raise ValidationError('private controller value or identity differs')
        seen.add(idx)
    return m, rows


class PrivateExternal(ExternalSynthAdapter):
    """Narrow separate adapter; no changes to the public original-only guard."""
    def __init__(self, plugin, executable, workspace, scratch, selection):
        info = _plugin_info(plugin)
        self.plugin_sha = info['module_sha256']; self.center_pitch_bend = True
        self.workspace = Path(workspace).resolve(); self.plugin = self.local(info['path'])
        self.module = self.plugin/'Contents/x86_64-linux/vitalium.so'
        self.scratch = self.local(scratch); self.scratch.mkdir(parents=True,exist_ok=True)
        self.bwrap = shutil.which('bwrap'); self.base = _SandboxSoundCraft(self,executable)
        if digest(self.base.executable) != HOST_SHA: raise ValidationError('unreviewed SoundCraft binary')
        self._caps = None
        self.selection = {v['source_sha256']:v for v in selection['roles'].values()}
        self.preset_root = Path(selection['preset_root'])

    def call(self, argv, cwd):
        # The existing public adapter permits workspace writes. Foreign states
        # use a narrower sandbox: only this private staging tree is writable.
        writable = self.scratch.parent
        if not Path(cwd).resolve().is_relative_to(writable):
            # SoundCraft's discovery and inspection helpers use read-only
            # temporary directories; execute those calls from private scratch.
            cwd = self.scratch
        prefix = [self.bwrap,'--die-with-parent','--ro-bind','/','/',
                  '--bind',str(writable),str(writable),'--unshare-net']
        for key,path in {'VST3_PATH':self.plugin.parent,'XDG_CONFIG_HOME':writable/'config',
                         'XDG_CACHE_HOME':writable/'cache','XDG_DATA_HOME':writable/'data',
                         'XDG_DOCUMENTS_DIR':writable/'documents','TMPDIR':self.scratch}.items():
            if key != 'VST3_PATH': path.mkdir(parents=True,exist_ok=True)
            prefix += ['--setenv',key,str(path)]
        argv = list(map(str,argv)); script = None
        if len(argv) > 8000 and argv[1] == 'run':
            from .soundcraft import COMMANDS
            lines=[]; flags=[]; i=2
            while i < len(argv):
                flag=argv[i]
                if flag not in ('--cmd','--in','--save') or i+1 >= len(argv):
                    raise ValidationError('unsupported long private host argv')
                value=argv[i+1]; i+=2
                if flag == '--cmd':
                    name,sep,data=value.partition('=')
                    if name not in COMMANDS: raise ValidationError('unsupported private host operation')
                    data=data if sep else '{}'; strict_json(data); lines.append(name+' '+data)
                else: flags.extend([flag,value])
            fd,name=tempfile.mkstemp(prefix='commands-',suffix='.txt',dir=self.scratch); script=Path(name)
            with os.fdopen(fd,'w') as f: f.write('\n'.join(lines)+'\n')
            argv=[argv[0],'script',str(script),*flags]
        try:
            result=subprocess.run([*prefix,*argv],cwd=cwd,capture_output=True,text=True,timeout=240)
        finally:
            if script is not None: script.unlink()
        if result.returncode or result.stderr.strip():
            raise ValidationError('private host failed: '+result.stderr[:1200]+result.stdout[-1000:])
        if len(result.stdout)>32*2**20: raise ValidationError('oversized private host output')
        return result.stdout

    def capabilities(self):
        if _plugin_info(self.plugin)['module_sha256'] != self.plugin_sha or digest(self.base.executable) != HOST_SHA:
            raise ValidationError('plugin or host changed')
        if self._caps is None:
            if _hash(self.base._discover()) != CONTRACT: raise ValidationError('host contract drift')
            for command in ('engine.vst3_plugins','mix.insert_state'):
                if json.loads(self.base._call(['describe',command],self.scratch)).get('id') != command:
                    raise ValidationError('missing native VST command')
            line = self.base._call(['run','--cmd','engine.vst3_plugins'],self.scratch)
            if not line.startswith('engine.vst3_plugins: '): raise ValidationError('bad VST discovery')
            matches = [x for x in json.loads(line.split(': ',1)[1]) if x.get('id') == PLUGIN_ID]
            if (len(matches) != 1 or matches[0]['name'] != 'Vitalium' or matches[0]['version'] != VERSION or
                not matches[0]['is_instrument'] or Path(matches[0]['path']).resolve() != self.plugin):
                raise ValidationError('requested Vitalium not discovered')
            self._caps = {'adapter':'private-selected-vital-1','plugin':matches[0],
                'plugin_sha256':self.plugin_sha,'soundcraft_sha256':HOST_SHA,'contract_hash':CONTRACT,
                'midi_pitch_initialization':{'version':'vitalium-ch1-center-1','native_id':'1835232641',
                    'normalized':.5,'channel':0,'reason':'JUCE synthetic channel-1 pitch-bend input defaults to zero; actual multi-register PCM calibration required'}}
        return deepcopy(self._caps)

    def _values(self, p, track, path):
        manifest, rows = read_private_patch(path,self.selection,self.preset_root,self.plugin_sha)
        if (track.instrument.plugin_ref != PLUGIN_ID or track.instrument.preset_ref != 'sha256:'+digest(Path(path)/'manifest.json') or
            track.instrument.midi_program is not None or set(track.instrument.parameters) != {r['canonical_id'] for r in rows} or
            any(a.target_id == track.instrument.id for a in p.automation)):
            raise ValidationError('private canonical instrument mismatch')
        result = deepcopy(manifest['native_defaults'])
        for row in rows:
            spec = next(x for x in p.parameters if x.id == row['canonical_id'])
            if (spec.unit,spec.minimum,spec.maximum,spec.targets) != ('normalized',0,1,['instrument']):
                raise ValidationError('private control registry differs')
            value = track.instrument.parameters[row['canonical_id']]
            if row['steps'] and abs(value*row['scale']-round(value*row['scale'])) > .00002:
                raise ValidationError('fractional discrete private control')
            result[row['native_id']] = round(value*row['scale']) if row['steps'] else value
        if result.get('1835232641') != 0 or any(n.channel != 0 for c in track.clips for n in c.notes):
            raise ValidationError('pitch-center contract mismatch')
        result['1835232641'] = .5
        return result


def _probe_defaults(adapter, work):
    p = generate(); p.bars = 2; p.sections = [Section('section-gate','Gate',0,2*BAR)]
    p.tracks = p.tracks[:1]; p.automation = []; p.locks = []
    t = p.tracks[0]; t.instrument = Instrument(t.instrument.id,'plugin','soundcraft:subtractive_synth',None,None,{})
    t.effects = []; t.controls.update({'mixer.gain_db':-18,'mixer.pan':0})
    t.clips = [Clip('clip-gate','Gate','midi',0,2*BAR,[Note('note-gate',192,3840,60,90,0)],None)]
    adapter.base.export(p,work/'probe'); native = _read_json(work/'probe/session.scraft')
    adapter.script([('mix.instrument',{'track':native['tracks'][0]['id'],'plugin':PLUGIN_ID})],
                   work/'probe/session.scraft',work/'probe-vital.scraft',work)
    return _read_json(work/'probe-vital.scraft')['tracks'][0]['instrument']['params']


def _prepare(adapter, entry, defaults, directory, timeout):
    directory.mkdir(mode=0o700)
    source = _read_preset(adapter.preset_root,entry['path'],entry['catalog_size'],entry['source_sha256'])
    (directory/'input.vital').write_bytes(source)
    request = {'plugin':str(adapter.plugin),'plugin_sha':adapter.plugin_sha,'source':str(directory/'input.vital'),
        'source_sha':entry['source_sha256'],'version':entry['catalog_version'], 'defaults':defaults,'out':str(directory/'patch')}
    write(directory/'request.json',request)
    pythonpath = os.pathsep.join(dict.fromkeys([str(Path(__file__).resolve().parent.parent)] + [str(Path(x).resolve()) for x in sys.path if x]))
    cmd = [adapter.bwrap,'--die-with-parent','--unshare-net','--ro-bind','/','/',
           '--bind',str(directory),str(directory),'--chdir',str(directory),'--clearenv']
    for k,v in {'PATH':'/usr/bin:/bin','PYTHONPATH':pythonpath,'HOME':str(directory),'TMPDIR':str(directory),
                'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}.items(): cmd += ['--setenv',k,v]
    cmd += [sys.executable,'-m','kuang._private_vital_worker',str(directory/'request.json')]
    try:
        result = subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ValidationError('private preset worker timed out') from exc
    if result.returncode: raise ValidationError('private preset worker failed: '+result.stderr[-600:])
    read_private_patch(directory/'patch',adapter.selection,adapter.preset_root,adapter.plugin_sha)
    return directory/'patch'


def _bind(project, assignments, adapter):
    p = deepcopy(project); registry = {x.id for x in p.parameters}; found = set()
    for track in p.tracks:
        if track.id not in assignments: continue
        path = assignments[track.id]; _,rows = read_private_patch(path,adapter.selection,adapter.preset_root,adapter.plugin_sha)
        if any(a.target_id == track.instrument.id for a in p.automation): raise ValidationError('instrument automation unsupported')
        track.instrument = Instrument(track.instrument.id,'plugin',PLUGIN_ID,'sha256:'+digest(path/'manifest.json'),None,
                                      {r['canonical_id']:r['normalized'] for r in rows})
        found.add(track.id)
        for row in rows:
            if row['canonical_id'] not in registry:
                p.parameters.append(ParameterSpec(row['canonical_id'],'normalized',0,1,0,['instrument'])); registry.add(row['canonical_id'])
    if found != set(assignments): raise ValidationError('unknown private instrument assignment')
    p.metadata.update(private_vital='Third-party license unknown; private local use only', composition='rules-based house template')
    validate(p); return p


def create(prompt,catalog,plugin,soundcraft,out_dir,*,seed=17,bars=16,private=False,max_candidates=12,per_role=3,timeout=15):
    if private is not True: raise ValidationError('explicit --private-third-party-presets is required')
    if bars not in (16,32): raise ValidationError('bars must be 16 or 32')
    workspace = Path.cwd().resolve(); dest = Path(out_dir).absolute()
    if dest.exists() or dest.is_symlink() or not dest.parent.is_dir() or not dest.parent.resolve().is_relative_to(workspace):
        raise ValidationError('new output inside workspace with existing parent required')
    catalog = Path(catalog).absolute(); plugin = Path(plugin).absolute()
    library = catalog.parent.parent.resolve()
    if dest.resolve().is_relative_to(library) or dest.resolve().is_relative_to(plugin.resolve()):
        raise ValidationError('output cannot be inside preset library or plugin')
    spec,notes = rules_plan(prompt,seed)
    if spec.genre != 'house': raise ValidationError('this opt-in workflow currently supports house only')
    import re
    explicit = re.search(r'\b(\d+)\s*bars?\b',prompt.lower())
    if explicit and int(explicit.group(1)) != bars: raise ValidationError('prompt bar count conflicts with --bars')
    spec.bars = bars; validate_spec(spec)
    with tempfile.TemporaryDirectory(prefix='.autonomous-create-',dir=dest.parent) as temp:
        stage = Path(temp); os.chmod(stage,0o700)
        select_palette(prompt,catalog,plugin,stage/'palette',seed=seed,per_role=per_role,max_candidates=max_candidates,timeout=timeout)
        selection = _read_json(stage/'palette/selection.json')
        if selection['status'] != 'complete' or set(selection['roles']) != {'chord','pad','bass'}:
            raise ValidationError('complete chord, pad and bass selection required')
        palette_before = inventory(stage/'palette')
        adapter = PrivateExternal(plugin,soundcraft,workspace,stage/'scratch',selection)
        adapter.capabilities(); defaults = _probe_defaults(adapter,stage)
        role_tracks = {'chord':'track-harmony','pad':'track-pad','bass':'track-bass'}
        assignments = {role_tracks[r]:_prepare(adapter,selection['roles'][r],defaults,stage/('prepare-'+r),timeout)
                       for r in role_tracks}
        project = refine_house(spec,compose(spec))
        # Generous pre-fader headroom for independent third-party patch levels.
        for track in project.tracks:
            track.controls['mixer.gain_db'] -= 15
        for lane in project.automation:
            if lane.parameter_id == 'mixer.gain_db':
                for point in lane.points: point.value -= 15
        project = _bind(project,assignments,adapter)
        native = ProductionAdapter(soundcraft,workspace=workspace,scratch=stage/'scratch')
        native.external = adapter; native.samples.base = adapter.base; native.base = adapter.base
        duration = project.length/project.ppq*60/project.tempo_bpm
        native.export(project,{},assignments,stage/'calibration-native')
        native.render(stage/'calibration-native',stage/'calibration.wav',end_seconds=duration+12)
        library_path = workspace/'.local/producer/libebur128.so'
        calibration = measure(stage/'calibration.wav',library=str(library_path) if library_path.is_file() else None)
        if calibration['clipped_samples'] or calibration['rms'] < 1e-6:
            raise ValidationError('calibration render clipped or silent')
        # Raise all existing track gains together, preserving their balance and
        # gain lanes, while leaving a conservative margin for VST variation.
        adjustment = min(9., max(-30., -4. - calibration['true_peak_dbtp']))
        for track in project.tracks:
            track.controls['mixer.gain_db'] += adjustment
        for lane in project.automation:
            if lane.parameter_id == 'mixer.gain_db':
                for point in lane.points: point.value += adjustment
        validate(project)
        native.export(project,{},assignments,stage/'native')
        native.save(stage/'native',stage/'reopened')
        render = native.render(stage/'native',stage/'preview.wav',end_seconds=duration+12)
        audio = measure(stage/'preview.wav',library=str(library_path) if library_path.is_file() else None)
        if audio['clipped_samples'] or audio['true_peak_dbtp'] > -1 or audio['rms'] < 1e-6:
            raise ValidationError('render failed true-peak, clipping or silence gate')
        if (inventory(stage/'palette') != palette_before or
            hashlib.sha256(_bounded_read(catalog,MAX_CATALOG_BYTES)).hexdigest() != selection['catalog_sha256'] or
            _plugin_info(plugin)['module_sha256'] != adapter.plugin_sha):
            raise ValidationError('catalog, palette evidence or plugin changed during production')
        save(project,stage/'project.kuang.json'); (stage/'song.mid').write_bytes(midi.export_bytes(project))
        write(stage/'song-spec.json',asdict(spec))
        write(stage/'report.json',{'version':'private-autonomous-create-1','prompt':prompt,'seed':seed,
            'composition':'rules-based house template, not neural music generation','selection':'palette/selection.json',
            'native':'native/session.scraft','audio':'preview.wav','render':render,'measurement':audio,
            'native_save_reopen_equal':True,'calibration_true_peak_dbtp':calibration['true_peak_dbtp'],
            'native_track_gain_adjustment_db':adjustment,
            'source_presets':'license unknown; private use only','notes':notes})
        # The native bundle contains copies of third-party states and must remain private.
        for name in ['scratch','probe','probe-vital.scraft','commands.txt','reopened','calibration-native','calibration.wav',
                     'cache','config','data','documents']:
            path=stage/name
            if path.is_dir(): shutil.rmtree(path)
            elif path.exists(): path.unlink()
        for path in stage.glob('prepare-*'): shutil.rmtree(path)
        dest.mkdir(mode=0o700)
        try:
            for child in stage.iterdir(): child.rename(dest/child.name)
        except BaseException:
            shutil.rmtree(dest); raise
    return {'output':str(dest),'native':str(dest/'native/session.scraft'),'audio':str(dest/'preview.wav'),
            'report':str(dest/'report.json'),'roles':{r:v['source_preset_name'] for r,v in selection['roles'].items()}}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prompt'); parser.add_argument('--catalog',required=True); parser.add_argument('--plugin',required=True)
    parser.add_argument('--soundcraft',required=True); parser.add_argument('--out-dir',required=True)
    parser.add_argument('--seed',type=int,default=17); parser.add_argument('--bars',type=int,choices=(16,32),default=16)
    parser.add_argument('--private-third-party-presets',action='store_true'); parser.add_argument('--per-role',type=int,default=3)
    parser.add_argument('--max-candidates',type=int,default=12); parser.add_argument('--timeout',type=float,default=15)
    args=parser.parse_args(argv)
    try:
        result=create(args.prompt,args.catalog,args.plugin,args.soundcraft,args.out_dir,seed=args.seed,bars=args.bars,
                      private=args.private_third_party_presets,per_role=args.per_role,max_candidates=args.max_candidates,timeout=args.timeout)
    except (ValidationError,OSError,ValueError,KeyError,TypeError) as exc:
        print('autonomous-create: '+str(exc),file=sys.stderr); return 2
    print(json.dumps(result,indent=2,sort_keys=True)); return 0


if __name__ == '__main__': raise SystemExit(main())
