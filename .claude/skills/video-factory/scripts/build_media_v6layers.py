#!/usr/bin/env python3
"""build_media_v6layers.py — «живой коллаж»: вырезки-слои вместо кадра на бит (T2, v6-layers).

Третий дубль стадий 4–6. Прод (`build_media.py`), v4-exp и v5-collage не тронуты.

Чем отличается от v5-collage: там на каждый бит генерировался ЦЕЛЫЙ кадр-постер и двигался
целиком (Ken Burns). Здесь на бит приходится плоский бумажный фон + несколько ВЫРЕЗОК, каждая
из которых анимируется отдельно (влёт, шлепок, оседание, покачивание). Видео-модель по-прежнему
не используется — всё рисует GSAP в композиции hyperframes.

Экономика (ради чего всё): вырезки берутся не по одной, а «стикер-листами» — один запрос к
Nano Banana 2 рисует 4–6 изолированных объектов на плоском фоне, лист режется локально и
бесплатно (`collage_elements.py`). Один лист обслуживает несколько битов, поэтому число
генераций перестаёт быть равным числу битов.

Контракт — `collage_plan.json` рядом со `script.json` (пишет Claude, схема ниже). Число битов
в плане обязано совпадать со сценарием: слой раскладки заменяет `frame_plan.json`, а не дополняет.

    python3 scripts/build_media_v6layers.py <run_dir> --channel vitallogic_bad_pl
"""
from __future__ import annotations
import os
import json
import argparse
from pathlib import Path
from typing import List

from _common import find_project_root, wire_paths

ROOT = find_project_root()
wire_paths(ROOT)

from pydantic import BaseModel, Field       # noqa: E402
import schemas                              # noqa: E402
import engine                               # noqa: E402
from image_agent import generate_image      # noqa: E402
import vision_qa                            # noqa: E402
import collage_elements                     # noqa: E402
import assembly_layers                      # noqa: E402

PIPELINE_VERSION_EXP = "6.0-layers"

# Тот же инвариантный стилевой блок, что в v5 — вырезки обязаны выглядеть из одного фильма.
_SHEET_STYLE = (
    "Editorial paper-collage cut-outs: each object is a PRINTED-texture photographic cut-out with "
    "a clean scissor-cut white paper border and visible print grain, as if scissored out of a "
    "magazine and laid on a table."
)
_SHEET_TECH = (
    "Arrange the objects in a neat grid. Each object is rendered LARGE and highly detailed, "
    "filling most of its own cell, but with a clear band of empty background between neighbours — "
    "they must never touch or overlap. Photograph straight down under soft even light. "
    "Every object is cleanly isolated and casts NO shadow at all onto the background — the "
    "background stays perfectly even right up to each object's edge. "
    "Background: " + collage_elements.SHEET_BG_HINT + "."
)
_SHEET_NEGATIVE = ("NEGATIVE: readable words, printed labels, brand names, logos, watermarks, "
                   "objects touching or overlapping, busy or patterned background, 3d render.")


# --- контракт раскладки ----------------------------------------------------------
# Живёт здесь, а не в `schemas.py`: это экспериментальный слой, и прод-схемы трогать нельзя.
class Sheet(BaseModel):
    id: str
    prompt: str = Field(..., description="перечисление объектов листа, по строкам слева направо")
    # max_length=4 (было 8): SDK 1.47 не даёт запросить 2K, лист приходит 1024×1024, и объект
    # в ячейке 3×2 выходит ~330px — на холсте 1080 при w≥0.5 это апскейл и мыло. При 4 объектах
    # (2×2) ячейка ~500px, что уже сопоставимо с экранным размером. Когда SDK обновят и
    # sheet_size начнёт работать, лимит можно поднимать обратно.
    names: List[str] = Field(..., min_length=2, max_length=4)
    cols: int = Field(2, ge=1, le=4, description="колонок в сетке листа; строки считаются от len(names)")
    rmbg: List[str] = Field(default_factory=list, description=(
        "имена, которые резать через hyperframes remove-background, а не цветовым ключом — "
        "прозрачные объекты (стекло, вода) иначе дырявятся"))


class Element(BaseModel):
    name: str
    x: float = Field(..., ge=0.0, le=1.0, description="центр по ширине, доля холста")
    y: float = Field(..., ge=0.0, le=1.0, description="центр по высоте, доля холста")
    w: float = Field(0.4, gt=0.02, le=1.4, description="ширина как доля холста")
    rot: float = 0.0
    enter: str = "pop"
    enter_at: float = Field(0.0, ge=0.0)
    z: int = 0
    breathe: bool = True


class LayerBeat(BaseModel):
    bg_color: str = "#2A5C82"
    scraps: int = Field(4, ge=0, le=9)
    # min_length=3 — требование владельца 2026-08-05: кадр из одной вырезки на плоском фоне
    # читается как клипарт, а не как коллаж. Три предмета дают композицию и перекрытия.
    elements: List[Element] = Field(..., min_length=3, max_length=6)


class CollagePlan(BaseModel):
    sheets: List[Sheet] = Field(..., min_length=1)
    beats: List[LayerBeat] = Field(..., min_length=3)
    # 2K по умолчанию: на 1K объект в ячейке листа выходит ~400px, а на холсте 1080 живёт
    # при w=0.6 как ~650px — то есть апскейлится и мылится (владелец 2026-08-05: «генерируй
    # лист с объектами побольше»). На 2K тот же объект ~800px и масштабируется ВНИЗ.
    sheet_size: str = Field("2K", pattern="^(1K|2K|4K)$")


def _load(run_dir: Path, name: str, model):
    return model(**json.loads((run_dir / name).read_text(encoding="utf-8")))


def generate_sheets(plan: CollagePlan, out_dir: Path, qa_report: list | None = None) -> dict[str, Path]:
    """Генерит и режет стикер-листы. Возвращает {имя элемента: путь к PNG с альфой}.

    Гейт качества здесь — САМ СЛАЙСЕР: если на листе нашлось не столько объектов, сколько имён
    в плане, лист перегенерируется. Это бесплатная и более строгая проверка, чем vision (модель
    любит слепить два объекта вплотную — тогда компонент один и раскладка поехала бы молча).
    Дополнительно лист проходит vision-чек профилем `sheet` (НЕ `collage`: коллажный свод
    судит кадр ролика и валил лист за «объекты в зоне субтитров», которой на листе нет) —
    он ловит то, чего слайсер увидеть не может: читаемые надписи на предметах."""
    out_dir.mkdir(parents=True, exist_ok=True)
    elems: dict[str, Path] = {}
    max_attempts = 3
    for sh in plan.sheets:
        png = out_dir / f"sheet_{sh.id}.png"
        prompt = (f"{_SHEET_STYLE}\nThe sheet holds exactly {len(sh.names)} separate objects:\n"
                  f"{sh.prompt}\n{_SHEET_TECH}\n{_SHEET_NEGATIVE}")
        attempts = []
        sliced = None
        for attempt in range(1, max_attempts + 1):
            if not (png.exists() and png.stat().st_size > 10_000 and attempt == 1):
                generate_image("img", prompt, aspect_ratio="1:1", out=str(png),
                               image_size=plan.sheet_size)
            check = vision_qa.check_image(png, profile="sheet")
            try:
                sliced = collage_elements.slice_sheet(png, sh.names, out_dir / sh.id,
                                                      rmbg_names=set(sh.rmbg), cols=sh.cols)
                ok = check.passed
                issues = check.issues
            except ValueError as e:
                ok, issues, sliced = False, [str(e)], None
            attempts.append({"attempt": attempt, "passed": ok, "issues": issues})
            if ok and sliced:
                break
            print(f"  [sheet-qa] {sh.id} attempt {attempt} FAIL: {'; '.join(issues)[:200]}"
                  f"{' → regen' if attempt < max_attempts else ' → принят последний'}")
            png.unlink(missing_ok=True)
        if sliced is None:
            raise SystemExit(f"[v6layers] лист {sh.id} не удалось нарезать за {max_attempts} попыток. "
                             f"Упростите промпт листа или уменьшите число объектов.")
        if qa_report is not None:
            qa_report.append({"sheet": sh.id, "attempts": attempts})
        for n, p in sliced.items():
            if n in elems:
                raise SystemExit(f"[v6layers] имя элемента «{n}» встречается в двух листах — "
                                 f"имена должны быть уникальны на весь ролик")
            elems[n] = p
    return elems


def build(run_dir: Path, channel: str) -> Path:
    os.environ.setdefault("RUN_COST_DIR", str(run_dir))

    if (run_dir / "compliance.json").exists():
        script = _load(run_dir, "compliance.json", schemas.ComplianceVerdict).cleaned_script
    else:
        script = _load(run_dir, "script.json", schemas.Script)
    plan = _load(run_dir, "collage_plan.json", CollagePlan)

    if len(plan.beats) != len(script.beats):
        raise SystemExit(f"[v6layers] битов в раскладке ({len(plan.beats)}) ≠ битов сценария "
                         f"({len(script.beats)}).")
    known = {n for sh in plan.sheets for n in sh.names}
    missing = {e.name for b in plan.beats for e in b.elements} - known
    if missing:
        raise SystemExit(f"[v6layers] элементы не объявлены ни в одном листе: {', '.join(sorted(missing))}")

    n_sheets = len(plan.sheets)
    n_elems = sum(len(b.elements) for b in plan.beats)
    print(f"[4/6] стикер-листы: {n_sheets} генераций на {len(known)} вырезок "
          f"({n_elems} появлений в {len(plan.beats)} битах) …")
    sheet_qa: list = []
    elem_paths = generate_sheets(plan, run_dir / "elements", qa_report=sheet_qa)
    (run_dir / "sheet_qa.json").write_text(
        json.dumps(sheet_qa, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/6] озвучка (Gemini TTS, per-beat) канал={channel} …")
    voice_wav, durations, beat_words = engine.synth_audio(channel, script, run_dir / "audio")

    print("[6/6] сборка слоями (hyperframes → mp4) …")
    out_mp4 = run_dir / "out.mp4"
    beats = [b.model_dump() for b in plan.beats]
    assembly_layers.build_and_render(
        beats, {k: str(v) for k, v in elem_paths.items()}, beat_words,
        [(b.on_screen_text or "") for b in script.beats], durations,
        schemas.CaptionStyle(), voice_wav, out_mp4, run_dir / "hf",
        headline=(getattr(script, "poster_text", "") or "").strip(),
        cta_text=(getattr(script, "cta_plate", "") or "").strip(),
        bgm_wav=engine._channel_bgm(channel))
    engine.deliver(run_dir, channel, out_mp4)

    try:
        import build_media_v4exp as _v4
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
        "experiment": "v6layers",
        "visual_skin": "collage-layers",
        "sheets": n_sheets,
        "elements": len(known),
        "baseline_pipeline_version": schemas.PIPELINE_VERSION,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[done] {out_mp4}")
    cost = run_dir / "cost.json"
    if cost.exists():
        print(f"[cost] {cost}")
    return out_mp4


def main():
    ap = argparse.ArgumentParser(description="v6-layers — стикер-листы + слои + голос + сборка")
    ap.add_argument("run_dir")
    ap.add_argument("--channel", default="vitallogic_bad_pl")
    args = ap.parse_args()
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        raise SystemExit(f"[v6layers] нет папки прогона: {run_dir}")
    build(run_dir, args.channel)


if __name__ == "__main__":
    main()
