#!/usr/bin/env python3
"""
engine_local.py — СКЕЛЕТ оркестратора локальной фабрики (реализует Codex, Задача 3 в AGENTS.md).

Это КАРКАС: функции стадий — заглушки с контрактом и TODO. Реализуй их по:
  - docs/ARCHITECTURE_LOCAL.md  (стадии, поток данных)
  - roles/*.md                  (что делает каждая стадия)
  - contracts/schemas_local.py  (Pydantic-контракты — вход/выход стадий)
  - docs/DEPLOY_M4PRO.md         (как вызывать Ollama / ComfyUI / Chatterbox / whisper.cpp / ffmpeg)

Жёсткие требования к реализации:
  * СТРОГО ЛОКАЛЬНО — никаких платных API/ключей.
  * Артефакт каждой стадии пишется в runs/<дата>_<slug>/ АТОМАРНО (.tmp + os.replace).
  * Перезапуск ПРОПУСКАЕТ стадии с готовым артефактом (idempotent resume).
  * На 48GB допустима параллель независимых роликов (asyncio/threads), контракты те же.
  * Каждая стадия логирует параметры (модель, seed, версия) для воспроизводимости.

Запуск (целевой интерфейс):
  python scaffold/engine_local.py --niche <name> --topic "..." --rubric "..." --config config/pipeline.config.json
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from datetime import date

# from contracts.schemas_local import (
#     Script, ComplianceVerdict, FramePlan, BuildManifest, QAReport,
# )


# --- утилиты -------------------------------------------------------------------
def atomic_write(path: Path, data: str) -> None:
    """TODO: записать через .tmp + os.replace (не терять артефакт при падении)."""
    raise NotImplementedError


def stage_done(run_dir: Path, artifact: str) -> bool:
    """TODO: True, если артефакт стадии уже готов (для resume)."""
    return (run_dir / artifact).exists()


def call_ollama(cfg: dict, system: str, user: str, stage: str) -> dict:
    """TODO: POST на {llm.endpoint}/api/chat, format=json, keep_alive из cfg.
    Вернуть распарсенный JSON; при невалиде — 1 retry с укороченным промптом."""
    raise NotImplementedError


# --- стадии --------------------------------------------------------------------
def stage_1_script(cfg, ctx, topic, rubric) -> "Script":
    """roles/01_scriptwriter.md → Script. TODO: собрать промпт (тема+рубрика+хук+studio_context),
    вызвать call_ollama, валидировать Script."""
    raise NotImplementedError


def stage_2_compliance(cfg, ctx, script) -> "ComplianceVerdict":
    """roles/02_compliance.md → ComplianceVerdict. TODO."""
    raise NotImplementedError


def stage_3_visual_director(cfg, ctx, script) -> "FramePlan":
    """roles/03_visual_director.md + docs/IMAGE_PROMPTING.md → FramePlan.
    TODO: один кадр на бит, единый grade/light/lens/style_anchor, промпт под выбранную модель,
    negative пустой для FLUX/Qwen/Z-Image."""
    raise NotImplementedError


def stage_4_images(cfg, frame_plan, run_dir) -> list:
    """roles/04_image_operator.md → frames/*.png. TODO: дёргать ComfyUI HTTP API по workflow_json,
    подставлять prompt/seed/params, писать кадры + frames/manifest.json."""
    raise NotImplementedError


def stage_5_audio(cfg, script, run_dir) -> list:
    """roles/05_voice_tts.md → audio/voice.wav (per-beat). TODO: Chatterbox mps, voice_reference,
    atempo пост-обработка."""
    raise NotImplementedError


def stage_6_captions(cfg, run_dir) -> dict:
    """roles/06_captions_stt.md → captions.json. TODO: whisper.cpp --max-len 1 --output-json,
    распарсить в [{word,start_s,end_s}]."""
    raise NotImplementedError


def stage_7_assembly(cfg, manifest, run_dir) -> Path:
    """roles/07_assembly.md → out.mp4. TODO: hyperframes (HTML+CSS/GSAP движение, караоке-субтитры
    в safe-зоне) или fallback ffmpeg zoompan; loudnorm; при кросспосте — N вариантов."""
    raise NotImplementedError


def stage_8_qa(cfg, run_dir) -> "QAReport":
    """roles/08_qa.md → QAReport. TODO: технические чеки кодом (safe-зоны/статика/LUFS/формат/плашка,
    по реальным PNG) блокирующие; креатив — advisory."""
    raise NotImplementedError


# --- оркестрация ---------------------------------------------------------------
def run_one(cfg: dict, niche: str, topic: str, rubric: str) -> Path:
    slug = topic.lower().replace(" ", "-")[:40]
    run_dir = Path(cfg["runs_dir"]) / f"{date.today().isoformat()}_{slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    ctx = load_channel_context(cfg, niche)  # TODO: читать config/channel/studio_context.md

    # TODO: для каждой стадии — if not stage_done(...): выполнить и atomic_write артефакт.
    #  1 script.json → 2 compliance.json → 3 frame_plan.json → 4 frames/ →
    #  5 audio/ → 6 captions.json → 7 out.mp4 → 8 qa.json
    raise NotImplementedError


def load_channel_context(cfg: dict, niche: str) -> dict:
    """TODO: загрузить studio_context канала из config/channel/ (тон, визуал, стоп-листы, дисклеймер)."""
    raise NotImplementedError


def main():
    p = argparse.ArgumentParser(description="Локальная фабрика faceless-видео (скелет)")
    p.add_argument("--niche", required=True)
    p.add_argument("--topic", required=True)
    p.add_argument("--rubric", default="")
    p.add_argument("--config", default="config/pipeline.config.json")
    args = p.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    out = run_one(cfg, args.niche, args.topic, args.rubric)
    print(f"[ok] {out}")


if __name__ == "__main__":
    main()
