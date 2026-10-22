"""Small Standard MIDI File type-1 writer; no synthesis or audio rendering."""

import struct

from .schema import Project, ValidationError, atomic_write, validate


def _vlq(number: int) -> bytes:
    if not 0 <= number <= 0x0FFFFFFF:
        raise ValidationError("MIDI delta exceeds VLQ range")
    result = [number & 0x7F]
    while number >> 7:
        number >>= 7
        result.insert(0, (number & 0x7F) | 0x80)
    return bytes(result)


def _meta(kind, payload):
    return bytes([0xFF, kind]) + _vlq(len(payload)) + payload


def _chunk(events, length):
    events = sorted(events, key=lambda e: (e[0], e[1], e[2]))
    result = bytearray()
    previous = 0
    for tick, _, payload in events:
        result.extend(_vlq(tick - previous))
        result.extend(payload)
        previous = tick
    result.extend(_vlq(length - previous))
    result.extend(b"\xff\x2f\x00")
    return b"MTrk" + struct.pack(">I", len(result)) + result


def export_bytes(project: Project) -> bytes:
    validate(project)
    tempo = round(60_000_000 / project.tempo_bpm)
    # Circle-of-fifths signatures, indexed by MIDI tonic pitch class.
    major = [0, -5, 2, -3, 4, -1, 6, 1, -4, 3, -2, 5]
    minor = [-3, 4, -1, 6, 1, -4, 3, -2, 5, 0, -5, 2]
    signature = (minor if project.key_mode == "minor" else major)[project.key_tonic]
    conductor = [(0, 0, _meta(3, project.name.encode("utf-8"))),
                 (0, 1, _meta(0x51, tempo.to_bytes(3, "big"))),
                 (0, 2, _meta(0x58, bytes([4, 2, 24, 8]))),
                 (0, 3, _meta(0x59, bytes([signature & 0xFF, int(project.key_mode == "minor")]))) ]
    conductor.extend((s.start, 4, _meta(6, s.name.encode("utf-8"))) for s in project.sections)
    chunks = [_chunk(conductor, project.length)]
    for track in project.tracks:
        if track.kind != "midi":
            continue
        events = [(0, 0, _meta(3, track.name.encode("utf-8")))]
        channels = {n.channel for c in track.clips for n in c.notes}
        if track.instrument.midi_program is not None:
            events.extend((0, 1, bytes([0xC0 | channel, track.instrument.midi_program])) for channel in sorted(channels))
        for clip in track.clips:
            events.append((clip.start, 2, _meta(6, clip.name.encode("utf-8"))))
            for note in clip.notes:
                tick = clip.start + note.start
                events.append((tick, 4, bytes([0x90 | note.channel, note.pitch, note.velocity])))
                events.append((tick + note.duration, 3, bytes([0x80 | note.channel, note.pitch, 0])))
        chunks.append(_chunk(events, project.length))
    return b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), project.ppq) + b"".join(chunks)


def export(project: Project, path):
    atomic_write(path, export_bytes(project))
