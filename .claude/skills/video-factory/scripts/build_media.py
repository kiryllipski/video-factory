#!/usr/bin/env python3
"""build_media.py — единственная «тратящая» стадия навыка video-factory.

Берёт готовые script.json + frame_plan.json (их пишет Claude) и делает ТОЛЬКО то, что Claude не может:
  4) кадры  — Nano Banana 2 через image_agent.generate_image (hybrid-референсы, R29);
  5) голос  — Gemini TTS через engine.synth_audio (per-beat, обрезка тишины, whisper-транскрипт);
  6) сборка — hyperframes + ffmpeg через engine.assemble (Ken Burns, караоке-субтитры, мукс аудио).

Текстовые стадии Gemini (scriptwriter/compliance/visual/qa из engine.produce) НЕ вызываются —
их заменил Claude. Ключ Gemini раннеры читают из <root>/.env. Стоимость → <run_dir>/cost.json.

    python3 scripts/build_media.py <run_dir> --channel <biz_failures|psychology|wealth_viz>

Улучшение относительно engine.generate_frames (обоснование — research/29_nanobanana_consistency.md):
  вместо sliding-window refs=paths[-14:] используем hybrid anchor (кадр-0 + предыдущий кадр),
  выносим GRADE/LIGHT/LENS в начало промпта и добавляем негатив-блок — меньше style-drift/deep-frying.
"""
from __future__ import annotations
import os
import sys
import json
import argparse
from pathlib import Path

from _common import find_project_root, wire_paths

ROOT = find_project_root()
wire_paths(ROOT)

import schemas                       # noqa: E402
import engine                        # noqa: E402  (переиспользуем synth_audio + assemble)
from image_agent import generate_image  # noqa: E402

_NEGATIVE = ("NEGATIVE: over-saturated, deep-fried colors, 3d render, plastic skin, cartoon, "
             "mutated geometry, extra limbs, random text, watermark, logo, white border, "
             "photo frame, polaroid frame, paper margin, framed print, rounded photo corners, "
             "readable text, typography, captions, subtitles, labels, diagram annotations, "
             "infographic text, paragraphs, written words rendered in the image, text overlays — "
             "image must bleed to all four edges of the canvas and contain NO letters or words anywhere.")


def _load(run_dir: Path, name: str, model):
    return model(**json.loads((run_dir / name).read_text(encoding="utf-8")))


def generate_frames_hybrid(plan: schemas.FramePlan, out_dir: Path) -> list[Path]:
    """Кадры Nano Banana 2 с hybrid-референсами (R29): якорь = кадр-0 (держит грейд/свет),
    плюс предыдущий кадр (держит композицию/сцену). GRADE/LIGHT/LENS — в начале промпта."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    prefix = f"GRADE: {plan.grade}. LIGHT: {plan.light}. LENS: {plan.lens}."
    for i, fr in enumerate(plan.frames):
        refs: list[str] = []
        if i > 0:
            # якорь + предыдущий (макс. 2, без дублей) — против style-drift
            for cand in (paths[0], paths[i - 1]):
                s = str(cand)
                if s not in refs:
                    refs.append(s)
        prompt = f"{prefix}\n{fr.prompt}\nvertical 9:16 composition, clean lower third.\n{_NEGATIVE}"
        p = out_dir / f"frame_{i:02d}.png"
        generate_image("img", prompt, aspect_ratio="9:16", out=str(p), refs=refs)  # ВСЕГДА Nano Banana 2
        paths.append(p)
    return paths


def build(run_dir: Path, channel: str) -> Path:
    os.environ.setdefault("RUN_COST_DIR", str(run_dir))  # cost_tracker пишет сюда

    # источник сценария — cleaned_script из комплаенса, если он есть; иначе script.json
    if (run_dir / "compliance.json").exists():
        script = _load(run_dir, "compliance.json", schemas.ComplianceVerdict).cleaned_script
    else:
        script = _load(run_dir, "script.json", schemas.Script)
    plan = _load(run_dir, "frame_plan.json", schemas.FramePlan)

    if len(plan.frames) != len(script.beats):
        raise SystemExit(f"[build_media] кадров ({len(plan.frames)}) ≠ битов ({len(script.beats)}). "
                         f"Прогони validate_run.py и почини план.")

    print(f"[4/6] кадры (Nano Banana 2, hybrid refs): {len(plan.frames)} шт …")
    frames = generate_frames_hybrid(plan, run_dir / "frames")

    print(f"[5/6] озвучка (Gemini TTS, per-beat) канал={channel} …")
    voice_wav, durations, beat_words = engine.synth_audio(channel, script, run_dir / "audio")

    print("[6/6] сборка (hyperframes → mp4, мукс озвучки) …")
    out_mp4 = run_dir / "out.mp4"
    engine.assemble(plan, script, frames, durations, beat_words, voice_wav, out_mp4, run_dir / "hf")
    engine.deliver(run_dir, channel, out_mp4)  # копия финала в DELIVERY_ROOT (iCloud)

    # run_meta: версия пайплайна → publish_log → аналитика сравнивает v1/v2-ролики по метрикам
    import datetime
    (run_dir / "run_meta.json").write_text(json.dumps({
        "pipeline_version": schemas.PIPELINE_VERSION,
        "channel": channel,
        "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[done] {out_mp4}")
    cost = run_dir / "cost.json"
    if cost.exists():
        print(f"[cost] {cost}")
    return out_mp4


def main():
    ap = argparse.ArgumentParser(description="build_media — кадры + голос + сборка (стадии 4–6)")
    ap.add_argument("run_dir")
    ap.add_argument("--channel", default="biz_failures",
                    help="biz_failures | psychology | wealth_viz (определяет голос/подачу TTS)")
    args = ap.parse_args()
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        raise SystemExit(f"[build_media] нет папки прогона: {run_dir}")
    build(run_dir, args.channel)


if __name__ == "__main__":
    main()
