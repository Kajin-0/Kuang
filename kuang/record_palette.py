"""Phase13 full-song source choices; protected Phase10 music stays exact."""
from copy import deepcopy

from .drum_palette import assert_articulation, note_inventory, split_by_pitch
from .sampled_instrument import bind_samples
from .sample_assets import read_asset
from .schema import ValidationError, state_hash, validate

PLAN = {'track-kick': [(36, 'kick')], 'track-snare': [(39, 'clap'), (38, 'ghost snare')],
        'track-hats': [(42, 'closed hat'), (46, 'open hat')], 'track-percussion': [(44, 'shaker')]}
PITCHES = {'track-kick': 36, 'track-snare': 39, 'track-snare.p38': 38,
           'track-hats': 42, 'track-hats.p46': 46, 'track-percussion': 44}
# Independent source alternatives, not automatically ranked as quality scores.
KITS = {
    'punch': {'track-kick': 'house.kick.punch-02', 'track-snare': 'house.clap.classic-01',
        'track-snare.p38': 'house.snare.snap-01', 'track-hats': 'house.hat.closed-06',
        'track-hats.p46': 'house.hat.open-01', 'track-percussion': 'house.perc.shaker-02'},
    'round': {'track-kick': 'house.kick.deep-01', 'track-snare': 'house.clap.classic-02',
        'track-snare.p38': 'house.snare.body-01', 'track-hats': 'house.hat.closed-05',
        'track-hats.p46': 'house.hat.open-02', 'track-percussion': 'house.perc.shaker-01'},
    'tight': {'track-kick': 'house.kick.tight-02', 'track-snare': 'house.clap.classic-03',
        'track-snare.p38': 'house.snare.snap-01', 'track-hats': 'house.hat.closed-04',
        'track-hats.p46': 'house.hat.open-01', 'track-percussion': 'house.perc.tick-01'}}


def split_house(source):
    if (source.bars, source.tempo_bpm, source.key_tonic, source.key_mode) != (64, 126, 0, 'minor'):
        raise ValidationError('this experiment requires the 64-bar 126 BPM C-minor source')
    return split_by_pitch(source, PLAN)


def sampled_house(source, assets, levels=None):
    split, receipt = split_house(source)
    if set(assets) != set(PITCHES):
        raise ValidationError('explicit complete six-voice drum palette required')
    for tid, path in assets.items():
        expected = {'root_note': PITCHES[tid], 'key_low': PITCHES[tid], 'key_high': PITCHES[tid],
            'velocity_low': 1, 'velocity_high': 127, 'key_tracking': False,
            'playback': 'gate' if tid in ('track-hats.p46', 'track-snare.p38') else 'one_shot'}
        if read_asset(path)['mapping'] != expected:
            raise ValidationError('explicit per-role pitch/gate/velocity mapping differs: '+tid)
    p = bind_samples(split, assets)
    if levels is None:
        levels = {tid: -12 for tid in PITCHES}
    if set(levels) != set(PITCHES):
        raise ValidationError('explicit six-voice source calibration required')
    for track in p.tracks:
        if track.id not in assets:
            continue
        track.instrument.parameters.update({'sample.attack_ms': .1, 'sample.decay_ms': 1,
            'sample.sustain': 1, 'sample.velocity_sensitivity': 1, 'sample.level_db': levels[track.id],
            'sample.release_ms': 70 if track.id == 'track-hats.p46' else 35 if track.id == 'track-snare.p38' else 1})
    # The short gate patches give open hats/ghosts their explicit original MIDI
    # articulation. No inferred inter-track voice choke or changed note-off.
    articulation = assert_articulation(p, 'track-hats.p46', 'track-hats', 70)
    validate(p)
    if note_inventory(p) != note_inventory(source):
        raise ValidationError('source selection changed original note identity')
    original = {t.id: t for t in source.tracks if t.id not in PLAN}
    if any(t != original[t.id] for t in p.tracks if t.id in original):
        raise ValidationError('source selection changed a protected musical track')
    return p, {'split': receipt, 'articulation': articulation, 'source_levels_db': levels,
        'source_hash': state_hash(source), 'candidate_hash': state_hash(p),
        'all_original_note_fields_exact': True, 'non_drum_tracks_exact': True,
        'inserts_and_mixer': 'Original controls and projected FX/automation preserved; source trims are native sampler levels.'}
