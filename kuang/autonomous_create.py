"""Private one-prompt house sketch using auditioned third-party Vital presets.

This separate opt-in workflow never changes the original-only adapter validator.
Third-party states and outputs are private, and their licenses are not established.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from . import midi
from .autonomous_palette import (MAX_CATALOG_BYTES, _bounded_read, _plugin_info, _read_preset, _validate_patch,
                                 select_palette, _intent)
from ._private_vital_worker import wave_frames
from .composer import compose
from .external_synth import (ExternalSynthAdapter, HOST_SHA, CONTRACT, LAYOUT_SHA,
                             PLUGIN_ID, VERSION, _SandboxSoundCraft, digest, inventory, write)
from .generator import generate
from .loudness import measure
from .production import refine_house
from .house_template import template as groove_template_project, select_profile
from .house_full_arranger import arrange_full_song, parse_long_form
from .house_master_preview import render_previews
from .house_harmony import select_harmony
from .house_musical_plan import enrich_house_spec
from .house_sources import prepare_kit
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


def create(prompt,catalog,plugin,soundcraft,out_dir,*,seed=17,bars=16,private=False,max_candidates=12,per_role=3,timeout=15,
           groove_template=False, sample_pack=None, groove_profile='auto', harmony_profile='auto', drum_variant=0,
           full_song_bars=None, master_preview=False, contextual_shortlist=False, chord_level_calibration=False,
           groove_impact=False, preferred_bass_source_sha=None, musical_plan_v2=False,
           groove_pocket_diagnostics=False, groove_identity_v2=False):
    if private is not True: raise ValidationError('explicit --private-third-party-presets is required')
    if bars not in (16,32): raise ValidationError('bars must be 16 or 32')
    workspace = Path.cwd().resolve(); dest = Path(out_dir).absolute()
    if dest.exists() or dest.is_symlink() or not dest.parent.is_dir() or not dest.parent.resolve().is_relative_to(workspace):
        raise ValidationError('new output inside workspace with existing parent required')
    catalog = Path(catalog).absolute(); plugin = Path(plugin).absolute()
    library = catalog.parent.parent.resolve()
    if dest.resolve().is_relative_to(library) or dest.resolve().is_relative_to(plugin.resolve()):
        raise ValidationError('output cannot be inside preset library or plugin')
    if full_song_bars is not None and not groove_template:
        raise ValidationError('--full-song-bars requires --groove-template')
    if type(master_preview) is not bool:
        raise ValidationError('master_preview must be boolean')
    if master_preview and not groove_template:
        raise ValidationError('--master-preview requires --groove-template')
    if type(contextual_shortlist) is not bool:
        raise ValidationError('contextual_shortlist must be boolean')
    if type(chord_level_calibration) is not bool:
        raise ValidationError('chord_level_calibration must be boolean')
    if chord_level_calibration and not groove_template:
        raise ValidationError('--chord-level-calibration requires --groove-template')
    if type(groove_impact) is not bool or (groove_impact and (not groove_template or sample_pack is None)):
        raise ValidationError('--groove-impact requires --groove-template and licensed --sample-pack')
    if (type(groove_identity_v2) is not bool or
            (groove_identity_v2 and
             (not groove_template or not groove_impact or sample_pack is None))):
        raise ValidationError("--groove-identity-v2 requires groove-template, groove-impact and audited sample-pack")
    if type(groove_pocket_diagnostics) is not bool or (groove_pocket_diagnostics and not groove_template):
        raise ValidationError("groove pocket diagnostics require a house groove template")
    if type(musical_plan_v2) is not bool or (musical_plan_v2 and not groove_template):
        raise ValidationError('--musical-plan-v2 requires --groove-template and boolean option')
    if preferred_bass_source_sha is not None and (
            not groove_impact or type(preferred_bass_source_sha) is not str or
            not re.fullmatch(r'[0-9a-f]{64}',preferred_bass_source_sha)):
        raise ValidationError('--preferred-bass-source-sha requires --groove-impact and valid SHA256')
    if contextual_shortlist and (not groove_template or per_role < 2 or max_candidates < 4):
        raise ValidationError('--contextual-shortlist requires groove-template, per-role>=2, max-candidates>=4')
    planning_prompt = re.sub(r'\b(96|112|128|160)\s*bars?\b','32 bars',prompt,flags=re.I) if groove_template else prompt
    spec,notes = rules_plan(planning_prompt,seed)
    if spec.genre != 'house': raise ValidationError('this opt-in workflow currently supports house only')
    full_length,_ = parse_long_form(prompt,full_song_bars,bpm=spec.bpm) if groove_template else (None,prompt)
    if groove_pocket_diagnostics and full_length is not None:
        raise ValidationError('--groove-pocket-diagnostics supports short groove nuclei only, not full songs')
    explicit = re.search(r'\b(\d+)\s*bars?\b',prompt.lower())
    if not full_length and explicit and int(explicit.group(1)) != bars:
        raise ValidationError('prompt bar count conflicts with --bars')
    spec.bars = 32 if full_length else bars
    validate_spec(spec)
    if type(groove_template) is not bool:
        raise ValidationError('groove_template must be boolean')
    if (sample_pack is not None or groove_profile != 'auto' or harmony_profile != 'auto' or drum_variant != 0) and not groove_template:
        raise ValidationError('sample pack and groove/harmony options require --groove-template')
    if type(drum_variant) is not int or drum_variant not in (0,1):
        raise ValidationError('drum_variant must be 0 or 1')
    gp = select_profile(prompt,seed,groove_profile) if groove_template else None
    hp = select_harmony(prompt,gp,harmony_profile) if groove_template else None
    plan_receipt = None
    if musical_plan_v2:
        spec,plan_receipt = enrich_house_spec(spec,prompt,gp)
    expected_roles = set(_intent(prompt)['roles'])
    if not {'chord','bass'} <= expected_roles:
        raise ValidationError('this house composer requires chord and bass roles')
    with tempfile.TemporaryDirectory(prefix='.autonomous-create-',dir=dest.parent) as temp:
        stage = Path(temp); os.chmod(stage,0o700)
        palette_kw=({'preferred_bass_source_sha':preferred_bass_source_sha}
                    if preferred_bass_source_sha else {})
        select_palette(prompt,catalog,plugin,stage/'palette',seed=seed,per_role=per_role,
                       max_candidates=max_candidates,timeout=timeout,musical_spec=spec,**palette_kw)
        selection = _read_json(stage/'palette/selection.json')
        if selection['status'] != 'complete' or set(selection['roles']) != expected_roles:
            raise ValidationError('complete selection for every requested role required')
        palette_before = inventory(stage/'palette')
        adapter = PrivateExternal(plugin,soundcraft,workspace,stage/'scratch',selection)
        if contextual_shortlist:
            for role, candidates in selection.get('shortlist',{}).items():
                for entry in candidates:
                    if entry.get('status') != 'accepted' or entry.get('runtime_verified') is not True:
                        raise ValidationError('one-prompt source must be verified before binding')
                    adapter.selection[entry['source_sha256']] = entry
        adapter.capabilities(); defaults = _probe_defaults(adapter,stage)
        role_tracks = {'chord':'track-harmony','pad':'track-pad','bass':'track-bass'}
        assignments = {role_tracks[r]:_prepare(adapter,selection['roles'][r],defaults,stage/('prepare-'+r),timeout)
                       for r in selection['roles']}
        groove_receipt = None
        arrangement_receipt = None
        sound_assets = {}
        drum_evidence = None
        if groove_template:
            project,groove_receipt = groove_template_project(spec,profile=gp,harmony_profile=hp,
                                               include_pad='pad' in expected_roles,
                                               impact_pocket=groove_impact,
                                               groove_identity_v2=groove_identity_v2)
            if full_length and not contextual_shortlist:
                project,arrangement_receipt = arrange_full_song(project,bars=full_length,
                                                               profile=gp,seed=seed)
            if sample_pack is not None:
                project,sound_assets,drum_evidence = prepare_kit(project,sample_pack,
                                               stage/'drum-assets',gp,drum_variant,
                                               impact_pocket=groove_impact,
                                               groove_identity_v2=groove_identity_v2)
        else:
            project = refine_house(spec,compose(spec),include_pad='pad' in expected_roles,kick_aligned_ducking=True)
        if plan_receipt is not None:
            project.metadata['musical_plan_version'] = plan_receipt['version']
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
        if contextual_shortlist:
            from .house_one_prompt_context import short_audition_project
            from .house_mix_roles import _window
            audition=short_audition_project(project,_window(project)['end_tick'])
            audition_duration=audition.length/audition.ppq*60/audition.tempo_bpm+6
        else:
            audition=project
            audition_duration=duration+12
        native.export(audition,sound_assets,assignments,stage/'calibration-native')
        native.render(stage/'calibration-native',stage/'calibration.wav',end_seconds=audition_duration)
        library_path = workspace/'.local/producer/libebur128.so'
        context_receipt = None
        if contextual_shortlist:
            from .house_one_prompt_context import choose_sources
            assignments,context_receipt=choose_sources(project,assignments,
                    selection.get('shortlist',{}),adapter,defaults,native,
                    sound_assets,stage,duration=audition_duration,timeout=timeout,
                    library=str(library_path) if library_path.is_file() else None)
            project = _bind(project,assignments,adapter)
            for comparison in context_receipt['comparisons']:
                if comparison.get('chosen'):
                    selection['roles'][comparison['role']]=next(
                        e for e in selection['shortlist'][comparison['role']]
                        if e['source_sha256']==comparison['source_sha256'])
            write(stage/'palette/selection.json',selection)
            palette_before=inventory(stage/'palette')
        role_level_evidence = None
        if chord_level_calibration:
            from .house_role_level import apply_chord_calibration
            project,role_level_evidence=apply_chord_calibration(project,selection)
        if full_length and contextual_shortlist:
            project,arrangement_receipt=arrange_full_song(project,bars=full_length,
                                                         profile=gp,seed=seed)
            duration=project.length/project.ppq*60/project.tempo_bpm
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
        native.export(project,sound_assets,assignments,stage/'native')
        native.save(stage/'native',stage/'reopened')
        render = native.render(stage/'native',stage/'preview.wav',end_seconds=duration+12)
        audio = measure(stage/'preview.wav',library=str(library_path) if library_path.is_file() else None)
        if audio['clipped_samples'] or audio['true_peak_dbtp'] > -1 or audio['rms'] < 1e-6:
            raise ValidationError('render failed true-peak, clipping or silence gate')
        if (inventory(stage/'palette') != palette_before or
            hashlib.sha256(_bounded_read(catalog,MAX_CATALOG_BYTES)).hexdigest() != selection['catalog_sha256'] or
            _plugin_info(plugin)['module_sha256'] != adapter.plugin_sha):
            raise ValidationError('catalog, palette evidence or plugin changed during production')
        pocket_receipt = None
        if groove_pocket_diagnostics:
            from .house_groove_pocket import evaluate_pocket
            pocket_receipt=evaluate_pocket(project,stage/'preview.wav')
            write(stage/'groove-pocket-evidence.json',pocket_receipt)
        save(project,stage/'project.kuang.json'); (stage/'song.mid').write_bytes(midi.export_bytes(project))
        write(stage/'song-spec.json',asdict(spec))
        if plan_receipt is not None: write(stage/'musical-plan-evidence.json',plan_receipt)
        if groove_receipt is not None: write(stage/'groove-evidence.json',groove_receipt)
        if arrangement_receipt is not None: write(stage/'arrangement-evidence.json',arrangement_receipt)
        if drum_evidence is not None: write(stage/'sample-selection.json',drum_evidence)
        if context_receipt is not None: write(stage/'context-shortlist-evidence.json',context_receipt)
        if role_level_evidence is not None: write(stage/'chord-level-evidence.json',role_level_evidence)
        write(stage/'report.json',{'version':'private-autonomous-create-1','prompt':prompt,'seed':seed,
            'composition':'rules-based house template, not neural music generation','selection':'palette/selection.json',
            'native':'native/session.scraft','audio':'preview.wav','render':render,'measurement':audio,
            'native_save_reopen_equal':True,'calibration_true_peak_dbtp':calibration['true_peak_dbtp'],
            'native_track_gain_adjustment_db':adjustment,
            'source_presets':'license unknown; private use only','notes':notes,
            'groove_template':groove_template,'groove_profile':gp,'harmony_profile':hp,
            'groove_evidence':'groove-evidence.json' if groove_receipt else None,
            'arrangement_evidence':'arrangement-evidence.json' if arrangement_receipt else None,
            'actual_project_bars':project.bars,'source_nucleus_bars':spec.bars,
            'sample_selection':'sample-selection.json' if drum_evidence else None,
            'sample_pack':'locally supplied CC0 house-core' if drum_evidence else None,
            'quality_judgment':'unreviewed; no professional audio quality established',
            'master_preview_requested':master_preview,
            'groove_impact_requested':groove_impact,
            'groove_identity_v2_requested':groove_identity_v2,
            'preferred_bass_source_sha':preferred_bass_source_sha,
            'chord_level_calibration_requested':chord_level_calibration,
            'chord_level_evidence':'chord-level-evidence.json' if role_level_evidence else None,
            'contextual_shortlist_requested':contextual_shortlist,
            'contextual_audition_bars':audition.bars if contextual_shortlist else None,
            'contextual_source_decisions':context_receipt['comparisons'] if context_receipt else None,
            **({'groove_pocket_evidence':'groove-pocket-evidence.json'} if pocket_receipt else {}),
            **({'musical_plan_v2_requested': True,
                'musical_plan_evidence': 'musical-plan-evidence.json'} if plan_receipt else {})})
        if master_preview:
            # The standalone mastering API deliberately forbids modifying its
            # source tree. Use a separate scratch root and import the verified
            # derivatives only after both pass their independent PCM gates.
            with tempfile.TemporaryDirectory(prefix='.private-preview-',dir=dest.parent) as preview_temp:
                pending = Path(preview_temp)/'verified'
                render_previews(stage,pending,
                                library=str(library_path) if library_path.is_file() else None)
                shutil.move(str(pending),str(stage/'master-preview'))
        # The native bundle contains copies of third-party states and must remain private.
        for name in ['scratch','probe','probe-vital.scraft','commands.txt','reopened','calibration-native','calibration.wav',
                     'drum-assets','context-shortlist',
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
    parser.add_argument('--groove-template',action='store_true',help='use the curated groove-first MIDI template')
    parser.add_argument('--sample-pack',help='optional locally audited CC0 house-core pack for native drums')
    parser.add_argument('--groove-profile',choices=('auto','straight','deep','jackin','minimal'),default='auto')
    parser.add_argument('--harmony-profile',choices=('auto','simple','extended'),default='auto')
    parser.add_argument('--drum-variant',type=int,choices=(0,1),default=0)
    parser.add_argument('--preferred-bass-source-sha',
                        help='private user-approved Vital source SHA256; opt-in human-producer bass priority after independent audition, not a generic quality score')
    parser.add_argument('--groove-identity-v2',action='store_true',
                        help='opt-in distinct bass motifs and audited style-specific kick; requires --groove-impact and --sample-pack')
    parser.add_argument('--groove-pocket-diagnostics',action='store_true',
                        help='opt-in fullmix 25-90/90-250Hz kick-to-offbeat pocket diagnostics; not musical quality')
    parser.add_argument('--musical-plan-v2',action='store_true',
                        help='experimental style-conditioned harmonic planning on existing SongSpec; preserves explicit Roman progression')
    parser.add_argument('--groove-impact',action='store_true',
                        help='opt-in Phase44-reference-derived kick/sample balance, rhythmic bass accents and shuffled hats; not a music quality guarantee')
    parser.add_argument('--chord-level-calibration',action='store_true',
                        help='experimental bounded +/-3dB chord-source audition RMS gain trim, no creative quality claim')
    parser.add_argument('--contextual-shortlist',action='store_true',
                        help='evaluate up to 1 additional independently vetted Vital preset per bass/chord role on the locked groove')
    parser.add_argument('--master-preview',action='store_true',
                        help='produce measured transparent and gentle-compression WAV derivatives')
    parser.add_argument('--full-song-bars',type=int,choices=(96,112,128,160),
                        help='opt-in full-length editable arrangement from 32-bar nucleus')
    args=parser.parse_args(argv)
    try:
        result=create(args.prompt,args.catalog,args.plugin,args.soundcraft,args.out_dir,seed=args.seed,bars=args.bars,
                      private=args.private_third_party_presets,per_role=args.per_role,max_candidates=args.max_candidates,timeout=args.timeout,
                      groove_template=args.groove_template,sample_pack=args.sample_pack,groove_profile=args.groove_profile,
                      harmony_profile=args.harmony_profile,drum_variant=args.drum_variant,
                      full_song_bars=args.full_song_bars,master_preview=args.master_preview,
                      contextual_shortlist=args.contextual_shortlist,
                      chord_level_calibration=args.chord_level_calibration,
                      groove_impact=args.groove_impact,
                      musical_plan_v2=args.musical_plan_v2,
                      groove_pocket_diagnostics=args.groove_pocket_diagnostics,
                      groove_identity_v2=args.groove_identity_v2,
                      preferred_bass_source_sha=args.preferred_bass_source_sha)
    except (ValidationError,OSError,ValueError,KeyError,TypeError) as exc:
        print('autonomous-create: '+str(exc),file=sys.stderr); return 2
    print(json.dumps(result,indent=2,sort_keys=True)); return 0


if __name__ == '__main__': raise SystemExit(main())
