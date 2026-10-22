"""Bounded musical intent, independent of canonical project schema and host state."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal

from .schema import ValidationError, decode

ROLES = ("kick", "snare", "hats", "bass", "harmony", "arp", "lead")
LIMITATIONS = [
    "Template-based instrumental sketches: trap, house and ambient; no quality or artist imitation guarantee.",
    "Constant 40–200 BPM, major/natural minor, 4/4, 8/16/32 bars, diatonic triads only.",
    "Free built-in subtractive/drum synths, EQ and room reverb; no vocals, samples, external plugins, glides or sidechain compressor.",
    "SoundCraft notes are editable; native changes are not automatically reconciled into the canonical snapshot.",
]


@dataclass
class SongSpec:
    version: Literal["1"]
    genre: Literal["trap", "house", "ambient"]
    bpm: int
    tonic: int
    mode: Literal["major", "minor"]
    mood: Literal["dark", "uplifting", "dreamy"]
    energy: Literal["low", "medium", "high"]
    seed: int
    bars: Literal[8, 16, 32]
    arrangement: Literal["song", "evolving"]
    progression: list[int]  # four zero-based diatonic root degrees
    palette: Literal["dark", "warm", "bright"]
    instruments: list[Literal["kick", "snare", "hats", "bass", "harmony", "arp", "lead"]]
    space: Literal["dry", "room", "wide"]
    automation: Literal["fade", "pulse"]


def validate_spec(spec: SongSpec) -> SongSpec:
    spec = decode(SongSpec, asdict(spec))
    for name, low, high in (("bpm", 40, 200), ("tonic", 0, 11), ("seed", 0, 2**32 - 1)):
        if not low <= getattr(spec, name) <= high:
            raise ValidationError(f"SongSpec {name} must be {low}..{high}")
    if len(spec.progression) != 4 or any(not 0 <= n <= 6 for n in spec.progression):
        raise ValidationError("SongSpec progression requires four diatonic degrees 0..6")
    if len(spec.instruments) != len(set(spec.instruments)) or not {"bass", "harmony"} <= set(spec.instruments):
        raise ValidationError("SongSpec instruments must be unique and include bass and harmony")
    return spec


def spec_schema() -> dict:
    """Small explicit JSON Schema for the local model's structured output grammar."""
    enums = {
        "version": ["1"], "genre": ["trap", "house", "ambient"], "mode": ["major", "minor"],
        "mood": ["dark", "uplifting", "dreamy"], "energy": ["low", "medium", "high"],
        "bars": [8, 16, 32], "arrangement": ["song", "evolving"], "palette": ["dark", "warm", "bright"],
        "space": ["dry", "room", "wide"], "automation": ["fade", "pulse"],
    }
    props = {k: {"type": "integer" if k == "bars" else "string", "enum": v} for k, v in enums.items()}
    for name, low, high in (("bpm", 40, 200), ("tonic", 0, 11), ("seed", 0, 2**32 - 1)):
        props[name] = {"type": "integer", "minimum": low, "maximum": high}
    props["progression"] = {"type": "array", "minItems": 4, "maxItems": 4,
                            "items": {"type": "integer", "minimum": 0, "maximum": 6}}
    props["instruments"] = {"type": "array", "minItems": 2, "maxItems": 7, "uniqueItems": True,
                           "items": {"type": "string", "enum": list(ROLES)}}
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def check_prompt(prompt: str):
    if type(prompt) is not str or not prompt.strip() or len(prompt) > 4000:
        raise ValidationError("prompt must contain 1..4000 characters")
    if any(ord(c) < 32 and c not in "\n\t" for c in prompt):
        raise ValidationError("prompt contains control characters")
    try:
        prompt.encode("utf-8")
    except UnicodeError as exc:
        raise ValidationError("prompt must be UTF-8") from exc


def rules_plan(prompt: str, seed: int = 7) -> tuple[SongSpec, list[str]]:
    check_prompt(prompt)
    text = prompt.lower()
    messages = ["Rules planner understands a limited vocabulary; other descriptions remain annotations, not promises."]
    styles = [g for g, pattern in (("trap", r"\btrap\b"), ("house", r"\bhouse\b"),
                                   ("ambient", r"\b(?:ambient|cinematic)\b")) if re.search(pattern, text)]
    genre = styles[0] if styles else "trap"
    if len(styles) != 1:
        messages.append(f"Genre {'ambiguous' if styles else 'unspecified/unsupported'}; selected {genre} sketch.")
    bpm, tonic, mode, mood, energy, progression, palette, space = {
        "trap": (140, 9, "minor", "dark", "high", [0, 5, 3, 4], "dark", "wide"),
        "house": (126, 0, "major", "uplifting", "high", [0, 4, 5, 3], "bright", "room"),
        "ambient": (72, 2, "minor", "dreamy", "low", [0, 3, 5, 2], "warm", "wide"),
    }[genre]
    tempos = re.findall(r"\b(\d+(?:\.\d+)?)\s*bpm\b|\bbpm\s*(\d+(?:\.\d+)?)\b", text)
    if tempos:
        values = {float(a or b) for a, b in tempos}
        if len(values) != 1 or not next(iter(values)).is_integer():
            raise ValidationError("use one integer constant BPM")
        bpm = int(next(iter(values)))
    keys = re.findall(r"\b([a-g])\s*([#b♯♭]?)\s+(major|minor)\b", text)
    if keys:
        values = {(({"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}[n] +
                     {"": 0, "#": 1, "♯": 1, "b": -1, "♭": -1}[acc]) % 12, m) for n, acc, m in keys}
        if len(values) != 1:
            raise ValidationError("use one major/minor key")
        tonic, mode = next(iter(values))
    if re.search(r"\b(dark|haunting|ominous)\b", text):
        mood, palette = "dark", "dark"
    elif re.search(r"\b(uplifting|happy|bright)\b", text):
        mood, palette = "uplifting", "bright"
    elif re.search(r"\b(dreamy|gentle|warm)\b", text):
        mood, palette = "dreamy", "warm"
    if re.search(r"\b(low energy|gentle|sparse|calm)\b", text):
        energy = "low"
    elif re.search(r"\b(medium energy|moderate)\b", text):
        energy = "medium"
    elif re.search(r"\b(high energy|heavy|driving)\b", text):
        energy = "high"
    if "dry" in text:
        space = "dry"
    elif re.search(r"\b(spacious|atmospheric|lush)\b", text):
        space = "wide"
    bars_match = re.search(r"\b(\d+)\s*bars?\b", text)
    bars = int(bars_match[1]) if bars_match else 16
    instruments = list(ROLES if genre == "house" else ("bass", "harmony", "arp", "lead") if genre == "ambient" else
                       ("kick", "snare", "hats", "bass", "harmony", "lead"))
    if re.search(r"\b(no drums|without drums|drumless)\b", text):
        instruments = [r for r in instruments if r not in ("kick", "snare", "hats")]
    if re.search(r"\b(no lead|without lead)\b", text):
        instruments.remove("lead")
    # A small explicit chord vocabulary; arbitrary harmonic text is not evaluated.
    romans = re.search(r"\b([ivIV]+(?:\s*[-–]\s*[ivIV]+){3})\b", prompt)
    if romans:
        mapping = {"i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6}
        try:
            progression = [mapping[n.strip().lower()] for n in re.split(r"[-–]", romans[1])]
        except KeyError as exc:
            raise ValidationError("unsupported Roman progression; use I..VII") from exc
    for pattern, message in (
        (r"\b(vocals?|singing|lyrics?|guitar|piano|orchestra|strings)\b", "Acoustic instruments/vocals are not modeled; output uses synthesized instrumental voices."),
        (r"\b(vst|vital|serum|sidechain|glide|portamento)\b", "External devices, sidechain compression and 808 pitch slides are unsupported."),
        (r"\b(?:[1-9]\d*/(?:4|8|16)|tempo map|tempo change)\b", "Only constant-tempo 4/4 is generated."),
    ):
        if re.search(pattern, text):
            messages.append(message)
    spec = SongSpec("1", genre, bpm, tonic, mode, mood, energy, seed, bars,
                    "evolving" if genre == "ambient" else "song", progression, palette, instruments,
                    space, "pulse" if genre == "house" else "fade")
    return validate_spec(spec), messages
