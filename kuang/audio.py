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
