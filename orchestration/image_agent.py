#!/usr/bin/env python3
"""
image_agent.py — генерация изображений (кадров) для фабрики через Nano Banana (Gemini Image).

Собственный инструмент студии ВМЕСТО MCP-сервера `nano-banana` (его использование запрещено).
Ключ берётся ТОЛЬКО из GEMINI_API_KEY (.env в корне проекта имеет приоритет над окружением).

Зачем свой тул:
- единый ключ проекта, предсказуемая стоимость, учёт токенов (cost_tracker), как у gemini_agent.py;
- нативный 9:16 через image_config, reference images для консистентности кадров внутри ролика.

CLI:
    python3 orchestration/image_agent.py \
        --model img \
        --prompt "архивное фото в стиле ..." \   # текст ИЛИ путь к .md/.txt
        --aspect 9:16 \
        --ref refs/hero.png --ref refs/hero2.png \  # 0..14 референсов для консистентности
        --out out/frame_01.png

Как библиотека (из пайплайна):
    from image_agent import generate_image
    path = generate_image("img", "prompt...", aspect_ratio="9:16", out="out/f1.png", refs=[...])

Документация:
  - Nano Banana / image generation: https://ai.google.dev/gemini-api/docs/image-generation
  - Aspect ratio / ImageConfig:      https://ai.google.dev/gemini-api/docs/image-generation
"""
import os
import sys
import time
import argparse
import mimetypes
from pathlib import Path

# --- .env loader (.env проекта приоритетнее системного окружения) ---
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

# --- Реестр image-моделей (проверено через models.list на ключе, 2026-06-30) ---
# СТАНДАРТ СТУДИИ (решение владельца): ВСЕГДА `img` = Nano Banana 2. Другие тиры — только
# по явному согласованию. Дефолт CLI и пайплайна — `img`.
IMAGE_MODELS = {
    "img":      "gemini-3.1-flash-image",       # ★ Nano Banana 2 — СТАНДАРТ, всегда используем это
    "img-lite": "gemini-3.1-flash-lite-image",  # дешевле; только по согласованию
    "img-pro":  "gemini-3-pro-image",           # Nano Banana Pro; только по согласованию
    "img-25":   "gemini-2.5-flash-image",       # прежнее поколение (fallback)
}

def resolve_image_model(name: str) -> str:
    return IMAGE_MODELS.get(name, name)

_client = None
def client() -> "genai.Client":
    global _client
    if _client is None:
        if not os.environ.get("GEMINI_API_KEY"):
            raise SystemExit("GEMINI_API_KEY не найден (.env в корне проекта).")
        _client = genai.Client()
    return _client


def _ref_part(path: str):
    data = Path(path).read_bytes()
    mime = mimetypes.guess_type(path)[0] or "image/png"
    return types.Part.from_bytes(data=data, mime_type=mime)


def generate_image(model: str, prompt: str, aspect_ratio: str = "9:16",
                   out: str = "", refs=None, image_size=None) -> bytes:
    # NB: без `from __future__ import annotations` этот модуль исполняет аннотации на Python 3.9,
    # где `str | None` — TypeError. Поэтому у image_size аннотации нет намеренно.
    """Генерирует один кадр. Возвращает байты изображения; если out задан — пишет файл.

    refs: список путей к референсным изображениям (для консистентности персонажа/стиля, до 14).
    image_size: "1K" | "2K" | "4K" (строго с ЗАГЛАВНОЙ K — «1k» API отклоняет). None = дефолт
        модели (1K) и прежнее поведение. Нужен там, где кадр потом РЕЖЕТСЯ на части и куски
        масштабируются вверх: «стикер-лист» v6-layers на 1K даёт объект ~400px, который на
        холсте 1080 растягивается до ~650px и мылится (2026-08-05).
    """
    contents = []
    for r in (refs or []):
        contents.append(_ref_part(r))
    contents.append(prompt)

    img_cfg = {"aspect_ratio": aspect_ratio}
    if image_size:
        img_cfg["image_size"] = image_size
    try:
        image_config = types.ImageConfig(**img_cfg)
    except Exception:
        # google-genai 1.47 (стоит сейчас) знает у ImageConfig только aspect_ratio; image_size
        # появился позже. Не роняем прогон и не тянем апгрейд SDK ради одного поля — молча
        # откатываемся на дефолтное разрешение модели (1K). Когда SDK обновят, параметр
        # заработает сам. Апгрейд SDK — отдельная задача с широким радиусом (TTS, ресёрч, QA).
        image_config = types.ImageConfig(aspect_ratio=aspect_ratio)
        if os.environ.get("IMAGE_AGENT_VERBOSE"):
            print(f"[image_agent] image_size={image_size} не поддержан этой версией SDK — 1K")
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=image_config,
    )
    mid = resolve_image_model(model)

    # Nano Banana иногда возвращает пустой candidates (транзиент) — короткий ретрай,
    # чтобы длинная пакетная сборка не падала с нуля на одном кадре.
    img_bytes = None
    last_resp = None
    for attempt in range(3):
        resp = client().models.generate_content(model=mid, contents=contents, config=config)
        last_resp = resp
        if _cost:
            _cost.record_tokens(mid, getattr(resp, "usage_metadata", None), step="generate_image")
        cands = getattr(resp, "candidates", None)
        # 2026-07-05: cands может быть непустым, но cands[0].content/.parts — None (safety-блок
        # без явного prompt_feedback) — раньше падало TypeError и обрывало весь batch на кадре.
        parts = getattr(getattr(cands[0], "content", None), "parts", None) if cands else None
        if parts:
            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    img_bytes = inline.data
                    break
        if img_bytes is not None:
            break
        time.sleep(2 * (attempt + 1))  # 2s, 4s backoff перед повтором

    if img_bytes is None:
        # после ретраев так и нет картинки: либо отказ (текст), либо блок (prompt_feedback)
        txt = getattr(last_resp, "text", None) or "<нет изображения в ответе>"
        fb = getattr(last_resp, "prompt_feedback", None)
        raise SystemExit(f"[image_agent] модель не вернула изображение после 3 попыток. "
                         f"prompt_feedback={fb}. Ответ: {txt[:500]}")

    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(img_bytes)
    return img_bytes


def _read_prompt(value: str) -> str:
    if value and "\n" not in value and len(value) < 4096:
        try:
            p = Path(value)
            if p.is_file():
                return p.read_text(encoding="utf-8")
        except OSError:
            pass
    return value or ""


def main():
    p = argparse.ArgumentParser(description="Генератор кадров (Nano Banana / Gemini Image)")
    p.add_argument("--model", default="img", help="img-lite|img|img-pro|img-25 или полный ID")
    p.add_argument("--prompt", help="промпт: текст или путь к файлу")
    p.add_argument("--aspect", default="9:16", help="соотношение сторон (9:16 по умолчанию)")
    p.add_argument("--ref", action="append", default=[], help="референс-изображение (можно повторять)")
    p.add_argument("--size", default=None, choices=["1K", "2K", "4K"],
                   help="разрешение (по умолчанию дефолт модели = 1K)")
    p.add_argument("--out", required=False, help="путь для PNG (обязателен в CLI)")
    p.add_argument("--list-models", action="store_true")
    args = p.parse_args()

    if args.list_models:
        for alias, mid in IMAGE_MODELS.items():
            print(f"{alias:10s} -> {mid}")
        return
    if not args.prompt or not args.out:
        p.error("--prompt и --out обязательны (кроме --list-models)")

    prompt = _read_prompt(args.prompt)
    t0 = time.time()
    data = generate_image(args.model, prompt, aspect_ratio=args.aspect, out=args.out,
                          refs=args.ref, image_size=args.size)
    dt = time.time() - t0
    print(f"[ok] {resolve_image_model(args.model)} -> {args.out} "
          f"({dt:.1f}s, {len(data)} bytes, {args.aspect}, size={args.size or 'default'}, "
          f"refs={len(args.ref)})")


if __name__ == "__main__":
    main()
