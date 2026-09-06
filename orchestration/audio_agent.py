#!/usr/bin/env python3
"""
audio_agent.py — озвучка (TTS) для фабрики через Gemini TTS. Ключ из GEMINI_API_KEY (.env проекта).

Решение владельца: озвучка = Gemini TTS (не Kokoro). Модель по умолчанию — gemini-3.1-flash-tts-preview.
Gemini TTS возвращает сырой PCM (24 kHz, 16-bit, mono) — оборачиваем в WAV.

CLI:
    python3 orchestration/audio_agent.py --text "..."|файл --voice Charon --out out/voice.wav
    python3 orchestration/audio_agent.py --list-voices

Как библиотека:
    from audio_agent import generate_speech
    generate_speech("текст", voice="Charon", style="tired, wise, cynical baritone", out="voice.wav")

Документация: https://ai.google.dev/gemini-api/docs/speech-generation
"""
import os
import sys
import time
import wave
import argparse
import subprocess
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
def _load_env():
    env_path = _PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()
_load_env()

from google import genai
from google.genai import types

try:
    import cost_tracker as _cost
except Exception:
    _cost = None

TTS_MODELS = {
    "tts":      "gemini-3.1-flash-tts-preview",   # ★ стандарт
    "tts-25":   "gemini-2.5-flash-preview-tts",
    "tts-pro":  "gemini-2.5-pro-preview-tts",
}
# Готовые голоса Gemini (подмножество). Baritone-ish для бизнес-нуара: Charon/Orus/Fenrir.
VOICES = ["Charon", "Orus", "Fenrir", "Puck", "Kore", "Aoede", "Leda", "Zephyr"]

_client = None
def client():
    global _client
    if _client is None:
        if not os.environ.get("GEMINI_API_KEY"):
            raise SystemExit("GEMINI_API_KEY не найден (.env в корне проекта).")
        _client = genai.Client()
    return _client


def _write_wav(path: str, pcm: bytes, rate: int = 24000, width: int = 2, channels: int = 1):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(pcm)


def _speed_up(path: str, factor: float):
    """Ускоряет WAV на месте через ffmpeg atempo (0.5-2.0 — без пересэмплирования по высоте тона)."""
    if not factor or abs(factor - 1.0) < 1e-3:
        return
    tmp = path + ".fast.wav"
    subprocess.run(["ffmpeg", "-y", "-i", path, "-filter:a", f"atempo={factor}", tmp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(tmp, path)


def _audio_from_response(resp):
    """Return the first PCM payload, tolerating an intermittent empty Gemini response."""
    for candidate in getattr(resp, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                return inline.data
    return None


def _empty_response_detail(resp) -> str:
    candidates = getattr(resp, "candidates", None) or []
    reasons = [str(getattr(candidate, "finish_reason", None)) for candidate in candidates]
    feedback = getattr(resp, "prompt_feedback", None)
    return f"candidates={len(candidates)} finish_reasons={reasons} prompt_feedback={feedback}"


def generate_speech(text: str, voice: str = "Charon", style: str = "",
                    model: str = "tts", out: str = "", speed: float = 1.0) -> bytes:
    """Synthesize speech without changing its natural playback rate by default.

    ``speed`` is an explicit ffmpeg ``atempo`` override; 1.0 leaves the generated
    speech untouched. Do not use it as a way to fit a dense script into a time cap.
    """
    delivery = (
        "in a lively, friendly, conversational way, as if telling a friend something "
        "genuinely amusing; clear articulation, varied pitch, comic timing, light irony"
    )
    prompt = f"Say in a {style} voice, {delivery}: {text}" if style else f"Say {delivery}: {text}"
    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
        ),
    )
    mid = TTS_MODELS.get(model, model)
    pcm = None
    last_detail = "no response"
    for attempt in range(1, 4):
        resp = client().models.generate_content(model=mid, contents=prompt, config=config)
        if _cost:
            _cost.record_tokens(mid, getattr(resp, "usage_metadata", None), step="tts")
        pcm = _audio_from_response(resp)
        if pcm is not None:
            break
        last_detail = _empty_response_detail(resp)
        if attempt < 3:
            print(
                f"[audio_agent] empty audio response; retry {attempt}/2 ({last_detail})",
                file=sys.stderr,
            )
            time.sleep(1.5 * attempt)
    if pcm is None:
        raise SystemExit(
            "[audio_agent] модель не вернула аудио после 3 попыток: " + last_detail
        )
    if out:
        _write_wav(out, pcm)
        _speed_up(out, speed)
        with open(out, "rb") as f:
            return f.read()
    return pcm


def _read_arg(value: str) -> str:
    if value and "\n" not in value and len(value) < 4096:
        try:
            p = Path(value)
            if p.is_file():
                return p.read_text(encoding="utf-8")
        except OSError:
            pass
    return value or ""


def main():
    p = argparse.ArgumentParser(description="Озвучка через Gemini TTS")
    p.add_argument("--text", help="текст или путь к файлу")
    p.add_argument("--voice", default="Charon")
    p.add_argument("--style", default="", help="подача, напр. 'wise, cynical baritone'")
    p.add_argument("--model", default="tts")
    p.add_argument("--out", help="путь для WAV")
    p.add_argument("--speed", type=float, default=1.0, help="ffmpeg atempo постпроцесс, напр. 1.15")
    p.add_argument("--list-voices", action="store_true")
    args = p.parse_args()
    if args.list_voices:
        print("voices:", ", ".join(VOICES))
        print("models:", ", ".join(f"{k}->{v}" for k, v in TTS_MODELS.items()))
        return
    if not args.text or not args.out:
        p.error("--text и --out обязательны (кроме --list-voices)")
    import time
    t0 = time.time()
    data = generate_speech(_read_arg(args.text), voice=args.voice, style=args.style,
                           model=args.model, out=args.out, speed=args.speed)
    print(f"[ok] {TTS_MODELS.get(args.model, args.model)} -> {args.out} "
          f"({time.time()-t0:.1f}s, {len(data)} bytes pcm, voice={args.voice})")


if __name__ == "__main__":
    main()
