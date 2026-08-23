#!/usr/bin/env python3
"""build_media.py — единственная «тратящая» стадия навыка video-factory.

Берёт готовые script.json + frame_plan.json (их пишет Claude) и делает ТОЛЬКО то, что Claude не может:
  4) кадры  — Nano Banana 2 через image_agent.generate_image (референс — опционально, по ref_ids);
  5) голос  — Gemini TTS через engine.synth_audio (per-beat, обрезка тишины, whisper-транскрипт);
  6) сборка — hyperframes + ffmpeg через engine.assemble (Ken Burns, караоке-субтитры, мукс аудио).

Текстовые стадии Gemini (scriptwriter/compliance/visual/qa из engine.produce) НЕ вызываются —
их заменил Claude. Ключ Gemini раннеры читают из <root>/.env. Стоимость → <run_dir>/cost.json.

    python3 scripts/build_media.py <run_dir> --channel <biz_failures|psychology|wealth_viz>

Улучшение относительно engine.generate_frames (обоснование — research/29_nanobanana_consistency.md):
  GRADE/LIGHT/LENS в начале промпта + негатив-блок держат стиль текстом. Референс-картинки
  (2026-07-17: раньше — hybrid anchor, кадр-0 + предыдущий, ВСЕГДА) теперь ОПЦИОНАЛЬНЫ — только
  по явному `Frame.ref_ids` от автора плана (для консистентности конкретного персонажа/сцены).
  Причина смены: якорь на кадр-0 утекал композицию кадра-постера (нарочно пустая верхняя треть
  под заголовок) в кадры, которым эта пустота не нужна — см. factory_audit_2026-07-17.
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
import vision_qa                     # noqa: E402  (v3: машинный QA пикселей)

_NEGATIVE = ("NEGATIVE: over-saturated, deep-fried colors, 3d render, plastic skin, cartoon, "
             "mutated geometry, random fake lettering, watermark, "
             "white border, photo frame, polaroid frame, paper margin, framed print, "
             "rounded photo corners, floating captions, subtitle overlays, unplanned callouts, "
             "dense infographic text, paragraphs, image must bleed to all four edges of the canvas. "
             "Short planned printed labels, brand marks and device-screen UI are allowed when "
             "the storyboard calls for them.")


def _load(run_dir: Path, name: str, model):
    return model(**json.loads((run_dir / name).read_text(encoding="utf-8")))


def generate_frames_hybrid(plan: schemas.FramePlan, out_dir: Path,
                           qa_report: list | None = None) -> list[Path]:
    """Кадры Nano Banana 2 — референс-картинки ОПЦИОНАЛЬНЫ (2026-07-17, factory_audit):
    раньше каждый кадр всегда получал frame_0 + предыдущий как image-референс ("hybrid anchor",
    R29) — это держало грейд, но не давало режиссёру выбора и утекало КОМПОЗИЦИЮ (не только
    стиль) в кадры, которым это не нужно: например кадр-постер нарочно имеет пустую верхнюю
    треть под заголовок — и эта пустота копировалась в кадры, чей текст её не просил, давая
    поля/леттербокс в готовых кадрах при живом object-fit:cover в сборке.

    Теперь референс — то, что явно укажет автор плана в `Frame.ref_ids` (список вида
    ["frame_00"]) — ТОЛЬКО когда кадр должен буквально повторить конкретного персонажа/сцену
    (напр. кадр-петля в конце = тот же человек, что в кадре-постере). Без ref_ids — без
    референс-картинок вообще; консистентность держит только текстовый GRADE/LIGHT/LENS префикс
    (уже расписан с hex-кодами палитры). Это же снижает клонирование композиции между
    кадрами — что играет на руку правилу разнообразия сцен (research/56).

    v3 (factory_audit_2026-07-15): каждый кадр сразу проходит машинный frame-QA (vision_qa):
    впечатанный текст / рамки / анатомия / грязная нижняя треть / (для кадра-0) занятая верхняя
    треть. Fail → точечная перегенерация ЭТОГО кадра (до 2 доп. попыток), принимается лучшая
    попытка. Историю пишем в qa_report (→ frame_qa.json)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    by_id: dict[str, Path] = {}
    prefix = f"GRADE: {plan.grade}. LIGHT: {plan.light}. LENS: {plan.lens}."
    max_attempts = 3  # 1 базовая + 2 перегенерации
    for i, fr in enumerate(plan.frames):
        refs: list[str] = []
        for rid in fr.ref_ids:
            cand = by_id.get(rid)
            if cand is not None:
                s = str(cand)
                if s not in refs:
                    refs.append(s)
        prompt = f"{prefix}\n{fr.prompt}\nvertical 9:16 composition, clean lower third.\n{_NEGATIVE}"
        p = out_dir / f"frame_{i:02d}.png"
        attempts = []
        for attempt in range(1, max_attempts + 1):
            generate_image("img", prompt, aspect_ratio="9:16", out=str(p), refs=refs)  # ВСЕГДА Nano Banana 2
            check = vision_qa.check_image(p, poster=(i == 0))
            attempts.append({"attempt": attempt, "passed": check.passed, "issues": check.issues})
            if check.passed:
                break
            print(f"  [frame-qa] frame_{i:02d} attempt {attempt} FAIL: {'; '.join(check.issues)[:200]}"
                  f"{' → regen' if attempt < max_attempts else ' → принят последний (лимит попыток)'}")
        if qa_report is not None:
            qa_report.append({"frame": i, "attempts": attempts})
        paths.append(p)
        by_id[f"frame_{i:02d}"] = p
    return paths


def video_stills_qa(out_mp4: Path, run_dir: Path, script: schemas.Script) -> dict:
    """v3: 3 стоп-кадра готового ролика (t≈0 / 40% / конец) → vision-проверка (advisory):
    постер читается на кадре-0, субтитры в safe-зоне, CTA-плашка в финале."""
    import subprocess
    stills_dir = run_dir / "video_qa"
    stills_dir.mkdir(exist_ok=True)
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(out_mp4)],
        capture_output=True, text=True).stdout.strip() or 0.0)
    poster = (getattr(script, "poster_text", "") or "").replace("*", "").strip()
    cta = (getattr(script, "cta_plate", "") or "").replace("*", "").strip()
    points = [(0.0, "t0", [poster] if poster else None),
              (dur * 0.4, "mid", None),
              (max(dur - 0.4, 0.0), "end", [cta] if cta else None)]
    report = {"video_duration_s": round(dur, 2), "stills": []}
    for t, name, expect in points:
        png = stills_dir / f"{name}.png"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(out_mp4),
                        "-vframes", "1", str(png)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        check = vision_qa.check_image(png, still=True, expect_texts=expect)
        report["stills"].append({"t": round(t, 2), "name": name,
                                 "passed": check.passed, "issues": check.issues})
    return report


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

    print(f"[4/6] кадры (Nano Banana 2, hybrid refs) + frame-QA (vision): {len(plan.frames)} шт …")
    frame_qa: list = []
    frames = generate_frames_hybrid(plan, run_dir / "frames", qa_report=frame_qa)
    (run_dir / "frame_qa.json").write_text(
        json.dumps(frame_qa, ensure_ascii=False, indent=2), encoding="utf-8")
    n_regen = sum(1 for f in frame_qa if len(f["attempts"]) > 1)
    n_fail = sum(1 for f in frame_qa if not f["attempts"][-1]["passed"])
    print(f"  [frame-qa] перегенераций: {n_regen}; принято с непройденным чеком: {n_fail}")

    print(f"[5/6] озвучка (Gemini TTS, per-beat) канал={channel} …")
    voice_wav, durations, beat_words = engine.synth_audio(channel, script, run_dir / "audio")

    print("[6/6] сборка (hyperframes → mp4, мукс озвучки; v3: BGM канала + CTA-плашка) …")
    out_mp4 = run_dir / "out.mp4"
    engine.assemble(plan, script, frames, durations, beat_words, voice_wav, out_mp4, run_dir / "hf",
                    channel=channel)
    engine.deliver(run_dir, channel, out_mp4)  # копия финала в DELIVERY_ROOT (iCloud)

    # v3: video-QA готового файла (advisory — фиксирует, не блокирует)
    try:
        vqa = video_stills_qa(out_mp4, run_dir, script)
        (run_dir / "video_qa.json").write_text(
            json.dumps(vqa, ensure_ascii=False, indent=2), encoding="utf-8")
        bad = [s for s in vqa["stills"] if not s["passed"]]
        print(f"  [video-qa] {len(vqa['stills'])} стоп-кадров, замечаний: "
              + (", ".join(f"{s['name']}: {'; '.join(s['issues'])[:120]}" for s in bad) if bad else "нет"))
    except Exception as e:
        print(f"  [video-qa] пропущен (не критично): {e}")

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
