"""Small local runtime helpers shared by the canonical v8 media layer.

This module deliberately contains no editor, schema or publisher imports.  Keeping the
audio/probing primitives here lets the v8 orchestrator assemble approved Codex frames
without importing the legacy v1-v6 runtime.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


CHANNEL_VOICE = {
    "biz_failures": ("Charon", "wise, cynical baritone, sharp", 1.25),
    "psychology": ("Kore", "intriguing, insightful, energetic", 1.15),
    "wealth_viz": ("Orus", "confident, clear, authoritative", 1.15),
    "vitallogic_bad_pl": (
        "Charon",
        "bright, expressive, emotionally engaged male Polish narration; lively conversational pace, "
        "clear Polish articulation, varied pitch, playful comic timing, light irony",
        1.15,
    ),
}


def _wav_dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return float(out or 0.0)


def _trim_silence(path: Path) -> None:
    """Trim only leading/trailing TTS silence; preserve pauses inside speech."""
    tmp = path.with_suffix(".trim.wav")
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(path), "-af",
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
            "areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
            "areverse", str(tmp),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tmp.replace(path)


def _estimate_word_timestamps(text: str, duration_sec: float, offset: float) -> list[dict]:
    """Lay out known spoken words proportionally; no ASR model is needed."""
    words = text.split()
    if not words:
        return []
    char_counts = [max(len(word), 1) for word in words]
    total_chars = sum(char_counts)
    gap_fraction = 0.05
    gap = (duration_sec * gap_fraction) / max(len(words) - 1, 1)
    usable = duration_sec * (1 - gap_fraction)
    result: list[dict] = []
    cursor = 0.0
    for word, chars in zip(words, char_counts):
        word_dur = usable * (chars / total_chars)
        result.append({
            "text": word,
            "start": round(offset + cursor, 3),
            "end": round(offset + cursor + word_dur, 3),
        })
        cursor += word_dur + gap
    return result
