import struct
import unittest
from collections import Counter

from kuang.generator import generate
from kuang.midi import export_bytes
from kuang.schema import BAR, dumps, state_hash, validate


def parse_midi(data):
    """Independent minimal parser: checks chunk sizes, VLQs and explicit event status."""
    if data[:4] != b"MThd" or struct.unpack(">I", data[4:8])[0] != 6:
        raise AssertionError("bad MIDI header")
    format_, count, ppq = struct.unpack(">HHH", data[8:14])
    position, tracks = 14, []
    for _ in range(count):
        if data[position:position+4] != b"MTrk": raise AssertionError("bad track")
        length = struct.unpack(">I", data[position+4:position+8])[0]
        position += 8
        end, tick, events = position + length, 0, []

        def vlq():
            nonlocal position
            value = 0
            for _ in range(4):
                b = data[position]
                position += 1
                value = (value << 7) | (b & 127)
                if b < 128: return value
            raise AssertionError("invalid VLQ")

        while position < end:
            tick += vlq()
            status = data[position]
            position += 1
            if status == 0xFF:
                kind = data[position]
                position += 1
                size = vlq()
                payload = data[position:position+size]
                position += size
                events.append((tick, status, kind, payload))
            elif 0x80 <= status < 0xF0:
                size = 1 if status >> 4 in (0xC, 0xD) else 2
                payload = data[position:position+size]
                position += size
                if any(x > 127 for x in payload): raise AssertionError("bad data byte")
                events.append((tick, status, None, payload))
            else:
                raise AssertionError("unexpected status")
        if position != end or events[-1][1:3] != (0xFF, 0x2F):
            raise AssertionError("bad end of track")
        tracks.append(events)
    if position != len(data): raise AssertionError("trailing MIDI bytes")
    return format_, ppq, tracks


class GeneratorMidiTests(unittest.TestCase):
    def test_seed_reproducibility_and_variation(self):
        a, b, c = generate(7), generate(7), generate(8)
        self.assertEqual(dumps(a), dumps(b))
        self.assertEqual(export_bytes(a), export_bytes(b))
        self.assertNotEqual(state_hash(a), state_hash(c))
        self.assertNotEqual(export_bytes(a), export_bytes(c))
        self.assertEqual([t.id for t in a.tracks], [t.id for t in c.tracks])

    def test_arrangement_is_32_bars_eight_tracks_in_a_minor(self):
        p = generate(7)
        validate(p)
        self.assertEqual((p.bars, p.tempo_bpm, p.key_tonic, p.key_mode), (32, 124, 9, "minor"))
        self.assertEqual(len(p.tracks), 8)
        self.assertEqual(sum(s.length for s in p.sections), 32 * BAR)
        self.assertEqual(sum(len(c.notes) for t in p.tracks for c in t.clips), 1083)
        for track in p.tracks[3:]:
            self.assertTrue(track.clips)
            self.assertTrue(all(n.pitch % 12 in {9, 11, 0, 2, 4, 5, 7} for c in track.clips for n in c.notes))
        for slug in ("kick", "snare", "hats", "bass", "lead"):
            self.assertFalse(any(c.start == 20 * BAR for t in p.tracks if t.id == f"track-{slug}" for c in t.clips))

    def test_midi_type_one_conductor_metadata_and_track_lengths(self):
        p = generate()
        format_, ppq, tracks = parse_midi(export_bytes(p))
        self.assertEqual((format_, ppq, len(tracks)), (1, 960, 9))
        meta = {event[2]: event[3] for event in tracks[0] if event[1] == 0xFF}
        self.assertEqual(int.from_bytes(meta[0x51], "big"), round(60_000_000 / 124))
        self.assertEqual(meta[0x58], bytes([4, 2, 24, 8]))
        self.assertEqual(meta[0x59], bytes([0, 1]))
        self.assertEqual(sum(e[1:3] == (0xFF, 6) for e in tracks[0]), 5)
        self.assertTrue(all(events[-1][0] == p.length for events in tracks))

    def test_midi_exact_notes_durations_channels_and_no_stuck_notes(self):
        p = generate()
        _, _, tracks = parse_midi(export_bytes(p))
        for canonical, events in zip(p.tracks, tracks[1:]):
            active, observed = {}, []
            for tick, status, _, payload in events:
                channel = status & 15
                if status >> 4 == 9:
                    pitch, velocity = payload
                    self.assertNotIn((channel, pitch), active)
                    active[(channel, pitch)] = (tick, velocity)
                elif status >> 4 == 8:
                    start, velocity = active.pop((channel, payload[0]))
                    observed.append((start, tick-start, channel, payload[0], velocity))
            self.assertFalse(active)
            expected = [(c.start+n.start, n.duration, n.channel, n.pitch, n.velocity) for c in canonical.clips for n in c.notes]
            self.assertEqual(Counter(observed), Counter(expected))

    def test_committed_examples_match_generator(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        self.assertEqual((root / "examples/demo.kuang.json").read_text(encoding="utf-8"), dumps(generate(7)))
        self.assertEqual((root / "examples/demo.mid").read_bytes(), export_bytes(generate(7)))

    def test_adjacent_same_pitch_notes_emit_note_off_before_note_on(self):
        from helpers import small_project
        p = small_project()
        p.tracks[0].clips[0].notes[1].start = 240
        _, _, tracks = parse_midi(export_bytes(p))
        simultaneous = [status >> 4 for tick, status, _, payload in tracks[1]
                        if tick == 240 and status >> 4 in (8, 9) and payload[0] == 36]
        self.assertEqual(simultaneous, [8, 9])
