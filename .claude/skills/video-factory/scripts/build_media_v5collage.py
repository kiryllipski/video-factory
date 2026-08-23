#!/usr/bin/env python3
"""build_media_v5collage.py — дубль build_media.py под эксперимент v5-collage (2026-08-05).

⚠️ Это дубль, а не замена. Продакшен (`build_media.py`) и предыдущий эксперимент
(`build_media_v4exp.py`) не тронуты — правило владельца: «пайплайн текущий не меняй, продублируй».

Что здесь отличается от продакшена (и почему это ЖИВЁТ В КОДЕ, а не в JSON-контрактах, как
было у v4exp): визуальный язык меняется на **ручной бумажный коллаж** — а это меняет сразу три
вещи, каждая из которых иначе ломала бы прогон.

1. **Стилевой префикс кадра.** Вместо `GRADE/LIGHT/LENS` в промпт уходит инвариантный
   СТИЛЕВОЙ БЛОК коллажа, дословно одинаковый на КАЖДОМ кадре — именно повторение блока
   слово-в-слово делает 12 разных кадров одним фильмом (vox-director, prompt-guide §1).
   Поля схемы `FramePlan` при этом не меняются, у них просто коллажная семантика:
     lens  → medium/technique (например «torn-paper collage, riso overprint»)
     grade → палитра и печатная фактура
     light → характер «съёмки» листа (flat scanned light)
   Так `schemas.py` и `validate_run.py` остаются нетронутыми.

2. **Негатив-блок.** Продакшенный банит «white border, photo frame, paper margin, random text» —
   в коллаже это ровно те признаки, ради которых стиль и выбран. Здесь негатив короткий и бьёт
   только по реальному браку (читаемые слова, 3D-рендер, внешнее паспарту вокруг всего постера).

3. **frame-QA профиль.** `vision_qa.check_image(profile="collage")` — фотореалистичный свод
   валит коллажный кадр за рваные края и плоский фон (проверено 2026-08-05: тот же кадр
   photo-профиль → 5 замечаний и FAIL, collage-профиль → passed). Без этого каждый годный
   кадр оплачивался бы трижды.

4. **Скин сборки.** `engine.assemble(..., skin="collage")` — заголовок/субтитры/CTA на рваной
   бумажной плашке (ink на cream), караоке-подсветка маркером, печатный растр и зерно поверх
   кадра. Скин `photo` при этом даёт побайтово тот же HTML, что и раньше (регресс-тест 2026-08-05).

Дизайн эксперимента и гипотеза H8 — docs/experiments/2026-08-05_v5collage.md.
Как писать сценарий и промпты кадров под коллаж — references/collage_style.md.

    python3 scripts/build_media_v5collage.py <run_dir> --channel vitallogic_bad_pl
"""
from __future__ import annotations
import os
import json
import argparse
from pathlib import Path

from _common import find_project_root, wire_paths

ROOT = find_project_root()
wire_paths(ROOT)

import schemas                       # noqa: E402
import engine                        # noqa: E402
from image_agent import generate_image  # noqa: E402
import vision_qa                     # noqa: E402

PIPELINE_VERSION_EXP = "5.0-collage"

# Инвариантный стилевой блок. Идёт ПЕРВЫМ в каждом промпте и дословно одинаков на всех кадрах —
# это главный носитель консистентности в коллаже (референс-картинки для стиля не нужны, ср.
# authoring_guide §ref_ids: они утекают композицию).
_COLLAGE_STYLE = (
    "Mixed-media hand-cut PAPER COLLAGE, editorial zine style. Torn and scissor-cut paper edges, "
    "matte tape corners, halftone print dots, newspaper clipping fragments, paper-stencil shapes, "
    "real soft paper drop shadows under every piece. Figures are PRINTED-texture cut-outs of real "
    "photography — keep the print grain and the paper imperfections. Flat and hand-assembled, "
    "photographed straight-on under flat even light like a scanned page."
)

# Технический хвост промпта. Две вещи, которые ломались на первых рендерах:
#   - нижняя пятая часть кадра должна быть ПЛОТНЫМ ЦВЕТОМ, не кремовой: сборка кладёт туда
#     кремовую бумажную плашку субтитров, и на кремовом фоне она исчезала (рендер 2026-08-05);
#   - газетные обрывки просить как ФАКТУРУ: модель охотно печатает псевдо-заголовки, а любое
#     читаемое слово в кадре — это и брак по QA, и риск по комплаенсу (неавторизованный клейм).
_COLLAGE_TECH = (
    "Vertical 9:16 poster composition; the flat colour paper background bleeds to all four edges "
    "of the canvas. Keep the lower fifth of the frame as quiet BOLD-COLOUR background paper with "
    "no cut-outs on it — never cream or white there. Newspaper fragments carry only fine "
    "illegible print texture, never readable words or headlines."
)

_NEGATIVE = ("NEGATIVE: random fake lettering, dense copy, floating captions, watermarks, "
             "3d render, CGI, photorealistic scene, smooth airbrushed "
             "gradients, an outer frame or mat around the whole poster. Short planned labels "
             "and planned labels, brand marks and screen content are allowed when called for by the storyboard.")


def _load(run_dir: Path, name: str, model):
    return model(**json.loads((run_dir / name).read_text(encoding="utf-8")))


def generate_frames_collage(plan: schemas.FramePlan, out_dir: Path,
                            qa_report: list | None = None) -> list[Path]:
    """Кадры-коллажи Nano Banana 2. Отличия от продакшенного `generate_frames_hybrid`:
    коллажный стилевой префикс, короткий негатив-блок и frame-QA с профилем `collage`.
    Референс-картинки — по-прежнему только по явному `Frame.ref_ids` (см. factory_audit
    2026-07-17); стиль держит текстовый блок, а не якорь-картинка.

    RESUME сохранён из v4exp: готовый кадр не перегенерируем — падение на середине партии
    (или зависший вызов image_agent, у него нет таймаута) иначе оплачивается заново целиком."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    by_id: dict[str, Path] = {}
    prefix = (f"{_COLLAGE_STYLE}\nMEDIUM: {plan.lens}. PALETTE AND PRINT FINISH: {plan.grade}. "
              f"CAPTURE: {plan.light}.")
    max_attempts = 3  # 1 базовая + 2 перегенерации
    for i, fr in enumerate(plan.frames):
        refs: list[str] = []
        for rid in fr.ref_ids:
            cand = by_id.get(rid)
            if cand is not None and str(cand) not in refs:
                refs.append(str(cand))
        prompt = f"{prefix}\n{fr.prompt}\n{_COLLAGE_TECH}\n{_NEGATIVE}"
        p = out_dir / f"frame_{i:02d}.png"

        if p.exists() and p.stat().st_size > 10_000:
            print(f"  [resume] frame_{i:02d} уже готов — пропускаю генерацию")
            if qa_report is not None:
                qa_report.append({"frame": i, "attempts": [{"attempt": 0, "passed": True,
                                                            "issues": ["resumed: файл уже существовал"]}]})
            paths.append(p)
            by_id[f"frame_{i:02d}"] = p
            continue

        attempts = []
        for attempt in range(1, max_attempts + 1):
            generate_image("img", prompt, aspect_ratio="9:16", out=str(p), refs=refs)
            check = vision_qa.check_image(p, poster=(i == 0), profile="collage")
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


def build(run_dir: Path, channel: str) -> Path:
    os.environ.setdefault("RUN_COST_DIR", str(run_dir))

    if (run_dir / "compliance.json").exists():
        script = _load(run_dir, "compliance.json", schemas.ComplianceVerdict).cleaned_script
    else:
        script = _load(run_dir, "script.json", schemas.Script)
    plan = _load(run_dir, "frame_plan.json", schemas.FramePlan)

    if len(plan.frames) != len(script.beats):
        raise SystemExit(f"[v5collage] кадров ({len(plan.frames)}) ≠ битов ({len(script.beats)}). "
                         f"Прогони validate_run.py и почини план.")

    print(f"[4/6] кадры-коллажи (Nano Banana 2) + frame-QA (профиль collage): {len(plan.frames)} шт …")
    frame_qa: list = []
    frames = generate_frames_collage(plan, run_dir / "frames", qa_report=frame_qa)
    (run_dir / "frame_qa.json").write_text(
        json.dumps(frame_qa, ensure_ascii=False, indent=2), encoding="utf-8")
    n_regen = sum(1 for f in frame_qa if len(f["attempts"]) > 1)
    n_fail = sum(1 for f in frame_qa if not f["attempts"][-1]["passed"])
    print(f"  [frame-qa] перегенераций: {n_regen}; принято с непройденным чеком: {n_fail}")

    print(f"[5/6] озвучка (Gemini TTS, per-beat) канал={channel} …")
    voice_wav, durations, beat_words = engine.synth_audio(channel, script, run_dir / "audio")

    print("[6/6] сборка (hyperframes → mp4, скин collage: бумажные плашки + печатная фактура) …")
    out_mp4 = run_dir / "out.mp4"
    engine.assemble(plan, script, frames, durations, beat_words, voice_wav, out_mp4, run_dir / "hf",
                    channel=channel, skin="collage")
    engine.deliver(run_dir, channel, out_mp4)

    # video-QA стоп-кадров — advisory, свод `_STILL_RULES` от скина не зависит: там проверяется
    # читаемость нашего собственного текста, а он рисуется сборкой одинаково в любом стиле.
    try:
        import build_media_v4exp as _v4  # переиспользуем video_stills_qa, не копируя её третий раз
        vqa = _v4.video_stills_qa(out_mp4, run_dir, script)
        (run_dir / "video_qa.json").write_text(
            json.dumps(vqa, ensure_ascii=False, indent=2), encoding="utf-8")
        bad = [s for s in vqa["stills"] if not s["passed"]]
        print(f"  [video-qa] {len(vqa['stills'])} стоп-кадров, замечаний: "
              + (", ".join(f"{s['name']}: {'; '.join(s['issues'])[:120]}" for s in bad) if bad else "нет"))
    except Exception as e:
        print(f"  [video-qa] пропущен (не критично): {e}")

    import datetime
    (run_dir / "run_meta.json").write_text(json.dumps({
        "pipeline_version": PIPELINE_VERSION_EXP,
        "channel": channel,
        "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "experiment": "v5collage",
        "visual_skin": "collage",
        "baseline_pipeline_version": schemas.PIPELINE_VERSION,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[done] {out_mp4}")
    cost = run_dir / "cost.json"
    if cost.exists():
        print(f"[cost] {cost}")
    return out_mp4


def main():
    ap = argparse.ArgumentParser(description="v5-collage — кадры-коллажи + голос + сборка (стадии 4–6)")
    ap.add_argument("run_dir")
    ap.add_argument("--channel", default="vitallogic_bad_pl")
    args = ap.parse_args()
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        raise SystemExit(f"[v5collage] нет папки прогона: {run_dir}")
    build(run_dir, args.channel)


if __name__ == "__main__":
    main()
