"""Measured PCM WAV properties, without third-party analysis dependencies."""

import math
import wave

from .schema import ValidationError


def analyze_wav(path) -> dict:
    try:
        with wave.open(str(path), "rb") as stream:
            channels, width, rate, frames = stream.getnchannels(), stream.getsampwidth(), stream.getframerate(), stream.getnframes()
            if stream.getcomptype() != "NONE" or width not in (2, 3, 4) or frames <= 0:
                raise ValidationError("expected a nonempty 16/24/32-bit integer PCM WAV")
            count = peak = squares = clipped = 0
            limit = 1 << (width * 8 - 1)
            while data := stream.readframes(65536):
                if len(data) % (width * channels):
                    raise ValidationError("truncated WAV frame")
                for offset in range(0, len(data), width):
                    value = int.from_bytes(data[offset:offset+width], "little", signed=True)
                    magnitude = abs(value)
                    peak = max(peak, magnitude)
                    squares += value * value
                    clipped += magnitude >= limit - 1
                    count += 1
            if count != frames * channels:
                raise ValidationError("truncated WAV data")
    except (wave.Error, EOFError) as exc:
        raise ValidationError(f"invalid PCM WAV: {exc}") from exc
    rms = math.sqrt(squares / count) / limit
    amplitude = peak / limit
    return {"sample_rate": rate, "channels": channels, "bits_per_sample": width*8, "frames": frames,
            "duration_seconds": frames/rate, "peak": amplitude, "rms": rms,
            "peak_dbfs": 20*math.log10(amplitude) if amplitude else None,
            "rms_dbfs": 20*math.log10(rms) if rms else None,
            "clipped_samples": clipped, "non_silent": peak > 0}


def compare_wavs(original, revised) -> dict:
    """Sample-aligned PCM delta. No resampling, gain normalization or guessed offset."""
    try:
        with wave.open(str(original), "rb") as left, wave.open(str(revised), "rb") as right:
            format_left = (left.getnchannels(), left.getsampwidth(), left.getframerate(), left.getnframes(), left.getcomptype())
            format_right = (right.getnchannels(), right.getsampwidth(), right.getframerate(), right.getnframes(), right.getcomptype())
            channels, width, rate, frames, compression = format_left
            if format_left != format_right or compression != "NONE" or width not in (2, 3, 4) or frames <= 0:
                raise ValidationError("A/B requires equal nonempty integer PCM formats, frame counts and sample rates")
            count = changed = squares = reference = peak = 0
            limit = 1 << (width*8 - 1)
            while a := left.readframes(65536):
                b = right.readframes(65536)
                if len(a) != len(b) or len(a) % (width * channels):
                    raise ValidationError("truncated A/B WAV data")
                for offset in range(0, len(a), width):
                    old = int.from_bytes(a[offset:offset+width], "little", signed=True)
                    new = int.from_bytes(b[offset:offset+width], "little", signed=True)
                    delta = new - old
                    changed += delta != 0
                    squares += delta * delta
                    reference += old * old
                    peak = max(peak, abs(delta))
                    count += 1
            if count != frames * channels or right.readframes(1):
                raise ValidationError("truncated A/B WAV data")
    except (wave.Error, EOFError) as exc:
        raise ValidationError(f"invalid A/B PCM WAV: {exc}") from exc
    rms = math.sqrt(squares / count) / limit
    ratio = math.sqrt(squares / reference) if reference else None
    return {"alignment": "sample zero; equal format/frame count; no shift, resampling or gain normalization",
            "offset_frames": 0, "frames": frames, "sample_rate": rate, "channels": channels,
            "changed_samples": changed, "changed_fraction": changed / count, "difference_peak": peak / limit,
            "difference_rms": rms, "difference_rms_dbfs": 20*math.log10(rms) if rms else None,
            "difference_to_original_rms_ratio": ratio,
            "measurable_change": changed > 0 and rms > 1e-5 and ratio is not None and ratio > 0.01}
