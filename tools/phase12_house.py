#!/usr/bin/env python3
"""Frozen eight-bar factorial groove/articulation study; no model or downloads."""
import argparse
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kuang.atmosphere import atmosphere_house
from kuang.audio import compare_wavs
from kuang.depth import note_fingerprints
from kuang.groove_audio import low_end_interaction, stem_sum_error
from kuang.loudness import measure
from kuang.lowend_audio import band_metrics
from kuang.mastering import attenuate, file_hash, match_lufs
from kuang.midi import export
from kuang.pocket_audio import event_map, gain_fit_residual, note_windows
from kuang.pocket_production import SOURCE_HASH, baseline, experiment, note_changes
from kuang.production_audio import production_metrics
from kuang.schema import ValidationError, dumps, load, save, state_hash
from kuang.soundcraft import SoundCraftAdapter
from kuang.spatial_audio import spatial_metrics
from tools.phase4_reference import excerpt
from tools.phase5_house import checked_audio, inventory, subset, write
from tools.phase7_house import local, publish

SCRATCH = ROOT/'.local/phase12'
ACTIVE = 8*4*60/126
TAIL = 8
LABELS = {'A': 'frozen-phase10', 'B': 'groove-only', 'C': 'sound-only', 'D': 'combined'}
ROLES = {'kick': ['track-kick'], 'bass': ['track-bass'], 'clap': ['track-snare'],
         'hats-percussion': ['track-hats', 'track-percussion'], 'stabs': ['track-harmony'],
         'hook-pads-pulse': ['track-lead', 'track-arp', 'track-depth-pad', 'track-depth-air', 'track-sub-pulse']}


def symbolic(p, root):
    root.mkdir(parents=True)
    save(p, root/'project.kuang.json')
    export(p, root/'song.mid')


def render(a, p, bundle, wav):
    a.export(p, bundle)
    a.render(bundle, wav, end_seconds=ACTIVE+TAIL)
    return checked_audio(wav)


def protected_sources():
    artifacts = ROOT/'artifacts'
    roots = [ROOT/'examples']
    if artifacts.is_dir():
        roots += [p for p in artifacts.iterdir() if p.is_dir()]
    return roots


def build(destination, *, source, executable=None, library=None, symbolic_only=False):
    dest, source = local(destination), local(source)
    if dest.exists():
        raise ValidationError('new Phase 12 output directory required')
    if not dest.is_relative_to(SCRATCH) and not dest.is_relative_to(ROOT/'artifacts/phase12-house'):
        raise ValidationError('Phase 12 outputs belong in .local/phase12 or artifacts/phase12-house')
    if dest.is_relative_to(source):
        raise ValidationError('output must be outside the preserved source')
    old = atmosphere_house() if symbolic_only else load(source/'project.kuang.json')
    projects, receipts = experiment(old)
    protected = protected_sources()
    if any(dest.is_relative_to(p) for p in protected):
        raise ValidationError('output intersects a historical artifact directory')
    before = inventory(protected) if not symbolic_only else {}
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=SCRATCH, prefix='build-') as folder:
        stage = Path(folder)/'release'
        stage.mkdir()
        for key, p in projects.items():
            symbolic(p, stage/key)
        write(stage/'receipts.json', receipts)
        provenance = {'version': 'phase12-factorial-1', 'source_hash': SOURCE_HASH,
            'source': 'Phase 10 D, zero-based bars 32..40 (human bars 33..40)',
            'labels': LABELS, 'active_seconds': ACTIVE, 'tail_seconds': TAIL,
            'A_is_exact_canonical_crop': True, 'all_variants_native_dsp_reset': True,
            'A_running_history_PCM_claim': False,
            'boundary_notes': 'Crop has a clipping guard, but no note is actually clipped in this pinned window. All 296 note fields/IDs are original; clip time origins shift by 32 bars.',
            'groove_changes': note_changes(projects['A'], projects['B']),
            'sound_changes': receipts['C-from-A']['operations'],
            'no_added_or_removed_notes': True, 'no_added_or_removed_effects': True,
            'human_preference_known': False, 'professional_quality_established': False}
        write(stage/'provenance.json', provenance)
        write(stage/'event-map.json', {key: event_map(p) for key, p in projects.items()})
        if symbolic_only:
            publish(stage, dest)
            return provenance
        a = SoundCraftAdapter(executable, timeout=240)
        if dumps(a.import_project(source/'native')) != dumps(old):
            raise ValidationError('Phase 10 native snapshot drift')
        report = {'version': 'phase12-proof-1', 'source_hash': state_hash(old),
            'symbolic': provenance, 'metrics': {}, 'stems': {}, 'native': {}}
        for key, p in projects.items():
            print('Native eight-bar '+key+' '+LABELS[key], flush=True)
            wav = stage/key/'raw-with-release.wav'
            render(a, p, stage/key/'native', wav)
            a.save(stage/key/'native', stage/key/'reopened-native')
            native = a.inspect(stage/key/'native')['native']
            if native != a.inspect(stage/key/'reopened-native')['native']:
                raise ValidationError('full native reopen differs: '+key)
            if dumps(a.import_project(stage/key/'reopened-native')) != dumps(p):
                raise ValidationError('canonical snapshot recovery differs: '+key)
            repeated = Path(folder)/(key+'-reopened.wav')
            a.render(stage/key/'reopened-native', repeated, end_seconds=ACTIVE+TAIL)
            if file_hash(repeated) != file_hash(wav):
                raise ValidationError('save/reopen changed actual PCM: '+key)
            report['native'][key] = {'full_state_equal': True, 'reopened_PCM_identical': True,
                'canonical_hash': state_hash(p), 'wav_sha256': file_hash(wav)}
            active = Path(folder)/(key+'-active.wav')
            excerpt(wav, active, 0, round(ACTIVE*48000))
            report['metrics'][key] = {'full': measure(wav, library=library),
                'active': measure(active, library=library), 'bands': band_metrics(wav, last=ACTIVE),
                'spatial': spatial_metrics(wav), 'context': production_metrics(wav, [('groove', 0, ACTIVE)])}
        controls = stage/'controls'
        controls.mkdir()
        for key, p in projects.items():
            report['stems'][key] = {}
            for role, ids in ROLES.items():
                # These inputs truly do not change in B/C/D; reuse A's stem.
                origin = 'A' if role == 'hook-pads-pulse' or (role == 'kick' and key == 'B') else 'C' if role == 'kick' and key == 'D' else key
                out = controls/(key+'-'+role+'.wav')
                if origin != key:
                    shutil.copyfile(controls/(origin+'-'+role+'.wav'), out)
                    report['stems'][key][role] = report['stems'][origin][role]
                    continue
                print('Native stem '+key+' '+role, flush=True)
                q = subset(p, ids)
                render(a, q, Path(folder)/(key+'-'+role), out)
                m = {'audio': checked_audio(out), 'bands': band_metrics(out, last=ACTIVE),
                     'active': production_metrics(out, [('active', 0, ACTIVE)])['sections']['active']}
                if role in ('kick', 'bass', 'clap', 'stabs'):
                    m['onsets'] = note_windows(out, q, ids[0], pitch=39 if role == 'clap' else None)
                report['stems'][key][role] = m
        report['recombination'] = {key: stem_sum_error(stage/key/'raw-with-release.wav',
            [controls/(key+'-'+role+'.wav') for role in ROLES]) for key in projects}
        report['low_end_interaction'] = {key: low_end_interaction(controls/(key+'-kick.wav'),
            controls/(key+'-bass.wav')) for key in projects}
        report['causal_PCM'] = {label: compare_wavs(stage/left/'raw-with-release.wav', stage/right/'raw-with-release.wav')
            for label, left, right in [('groove', 'A', 'B'), ('sound', 'A', 'C'),
                                       ('combined', 'A', 'D'), ('groove_given_sound', 'C', 'D'),
                                       ('sound_given_groove', 'B', 'D')]}
        report['same_input_sound_controls'] = {}
        for role in ('kick', 'bass', 'clap', 'hats-percussion', 'stabs'):
            residual = gain_fit_residual(controls/('A-'+role+'.wav'), controls/('C-'+role+'.wav'))
            level_delta = report['stems']['C'][role]['active']['rms_dbfs']-report['stems']['A'][role]['active']['rms_dbfs']
            if abs(level_delta) > .25 or residual['residual_to_changed_rms_ratio'] < .01:
                raise ValidationError('same-input sound control is a level cheat or inert: '+role)
            report['same_input_sound_controls'][role] = {'native_active_RMS_delta_db': level_delta, **residual}
        listening = stage/'listening'
        listening.mkdir()
        target = min(v['active']['integrated_lufs'] for v in report['metrics'].values())
        report['matching'] = {}
        for key in projects:
            calibration = match_lufs(Path(folder)/(key+'-active.wav'),
                Path(folder)/(key+'-matched-active.wav'), target, library=library)
            output = listening/(key+'-'+LABELS[key]+'-LUFS-matched.wav')
            attenuate(stage/key/'raw-with-release.wav', output, calibration['gain_db'])
            report['matching'][key] = {**calibration, 'active_measurement': calibration['measurement'],
                'measurement': measure(output, library=library),
                'interval': 'exactly the first eight active bars; same constant attenuation also applied to untouched natural release'}
        # A separate exact PCM archive cut proves the old running source is
        # untouched. It is NOT mixed into the reset-state factorial comparison.
        old_wav = source/'D-phase10-combined-native.wav'
        excerpt(old_wav, stage/'phase10-D-exact-historical-drop8.wav',
            round(32*4*60/126*48000), round(40*4*60/126*48000))
        report['historical_excerpt'] = {'parent_sha256': file_hash(old_wav),
            'excerpt_sha256': file_hash(stage/'phase10-D-exact-historical-drop8.wav'),
            'comparison_policy': 'A/B/C/D all start native DSP from rest; running-history archive cut is separate.'}
        # Matched stems are optional diagnostics, separately paired by role.
        report['stem_matching'] = {}
        for role in ('kick', 'bass', 'clap', 'hats-percussion', 'stabs'):
            meter = {key: measure(controls/(key+'-'+role+'.wav'), library=library) for key in ('A', 'D')}
            stem_target = min(v['integrated_lufs'] for v in meter.values())
            report['stem_matching'][role] = {key: match_lufs(controls/(key+'-'+role+'.wav'),
                listening/(key+'-'+role+'-stem-LUFS-matched.wav'), stem_target, library=library) for key in ('A', 'D')}
        for key, m in report['metrics'].items():
            if m['full']['clipped_samples'] or m['full']['true_peak_dbtp'] > -1:
                raise ValidationError('clipping/headroom gate: '+key)
            bands = m['spatial']['bands']
            if bands['low_20_120']['mono_energy_retention'] < .99 or bands['high_over_500']['mono_energy_retention'] < .8:
                raise ValidationError('mono compatibility gate: '+key)
            if m['spatial']['last_250ms']['rms'] > 10**(-65/20):
                raise ValidationError('release tail is not settled: '+key)
            if report['recombination'][key]['peak_error_lsb'] > 12:
                raise ValidationError('independent stem sum changed the mix: '+key)
        if any(not d['measurable_change'] or d['difference_to_original_rms_ratio'] < .01 for d in report['causal_PCM'].values()):
            raise ValidationError('factorial comparison contains an inert change')
        if inventory(protected) != before:
            raise ValidationError('historical files changed')
        report.update(history_unchanged=True, historical_sha256=before, human_listening=False,
                      full_song_expansion=False, all_native_state_and_PCM_reopened=True)
        write(stage/'verification.json', report)
        publish(stage, dest)
    return report


def package(root):
    root = local(root)
    r = json.loads((root/'verification.json').read_text())
    if not r.get('all_native_state_and_PCM_reopened'):
        raise ValidationError('real native proof is required before packaging')
    # Do not turn an old successful report into a false claim about changed
    # sessions, MIDI or PCM. No host process is needed for this packaging check.
    from kuang.midi import export_bytes
    for key in LABELS:
        p = load(root/key/'project.kuang.json')
        native = root/key/'native'
        manifest = json.loads((native/'manifest.json').read_text())
        if (state_hash(p) != r['native'][key]['canonical_hash'] or
                manifest['canonical_hash'] != state_hash(p) or
                file_hash(native/'session.scraft') != manifest['native_file_sha256'] or
                file_hash(root/key/'raw-with-release.wav') != r['native'][key]['wav_sha256'] or
                (root/key/'song.mid').read_bytes() != export_bytes(p)):
            raise ValidationError('package input drift: '+key)
    out = root/'phase12-house-listening.zip'
    if out.exists():
        raise ValidationError('new ZIP only')
    text = ('Kuang Phase 12: eight-bar producer experiment, not a professional-quality claim.\n'
      'A=frozen Phase10 D drop; B=groove only; C=sound only; D=combined.\n'
      '126 BPM, C minor. Each file: 8 active bars (15.238095 s) + 8 s natural release.\n'
      'All four are fresh native bounces with identical DSP-reset policy. Original note IDs retained.\n'
      'Integrated LUFS matched across exactly the first eight active bars, with the same labelled constant attenuation on their natural tails.\n'
      'No mastering, boosts or other waveform processing. Whole-file tail-inclusive measurements are also reported.\n'
      'An exact historical running-Phase10 PCM cut is also supplied separately; old reverb memory differs from a new excerpt.\n'
      'Start with listening/A..D. Matched stems are diagnostics; compare them in the mix as well.\n'
      'Each editable letter contains canonical schema 0.1, MIDI, native session.scraft, manifest and native snapshot.\n'
      'Open editable/LETTER/native/session.scraft in separately installed SoundCraft 0.11.0.\n'
      'Raw editable native gain differs from audition attenuation documented in verification.json.\n'
      'provenance.json and receipts.json enumerate every changed note/control and exact reversible transaction.\n'
      'No Vital/Vitalium, third-party samples, reference recording or factory presets. MIT original code/music.\n'
      'Human listening preference remains unknown. No full-song extension until this experiment is preferred.\n')
    (root/'README.txt').write_text(text)
    with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted((root/'listening').glob('*.wav')):
            z.write(path, 'listening/'+path.name)
        for key in LABELS:
            for path in sorted((root/key).rglob('*')):
                if path.is_file() and path.suffix != '.wav' and 'reopened-native' not in path.parts:
                    z.write(path, 'editable/'+key+'/'+str(path.relative_to(root/key)))
        for name in ('README.txt', 'provenance.json', 'receipts.json', 'event-map.json', 'verification.json',
                     'phase10-D-exact-historical-drop8.wav'):
            z.write(root/name, name)
        routing = root/'routing-prototype'
        if routing.exists():
            for name in ('prototype.kuang.json', 'verification.json', 'routed/session.scraft',
                         'dry/session.scraft', 'dry/song.mid'):
                path = routing/name
                if path.is_file():
                    z.write(path, 'experimental-routing/'+name)
        z.write(ROOT/'docs/PHASE12.md', 'PHASE12.md')
        z.write(ROOT/'LICENSE', 'LICENSE')
    with zipfile.ZipFile(out) as z:
        if z.testzip():
            raise ValidationError('ZIP integrity failure')
    write(root/'artifact-sha256.json', {str(p.relative_to(root)): file_hash(p)
          for p in sorted(root.rglob('*')) if p.is_file()})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--source', default=str(ROOT/'artifacts/phase10-house'))
    parser.add_argument('--symbolic', action='store_true')
    parser.add_argument('--soundcraft')
    parser.add_argument('--meter-library', default=os.environ.get('KUANG_EBUR128'))
    args = parser.parse_args()
    build(args.out_dir, source=args.source, executable=args.soundcraft, library=args.meter_library, symbolic_only=args.symbolic)
    if not args.symbolic:
        print(package(args.out_dir))


if __name__ == '__main__':
    main()
