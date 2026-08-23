#!/usr/bin/env python3
"""
engine_v7g.py — экспериментальный прогон v7 в теме «clinical glass» (v7g).

Зачем. Владелец дал мудборд: медицинские лендинги/дашборды 2025 — светлый воздух,
стеклянные светящиеся объекты, матовые белые карточки, тёмно-синяя типографика. Гипотеза
H11: канал говорит числами, а выглядит как фотосток с кухни; визуальный язык, который сам
выглядит как измерение, должен поднять и удержание, и CTR миниатюры. Побочная выгода —
стеклянный рендер не требует фотореализма кожи и рук, то есть убирает главный источник
брака генерации (принцип «ограничение → приём»).

Как устроено. Это НЕ форк пайплайна: драматургия, гейты, звук, тайминги и контракты v7
остаются ровно те же, меняется только визуальный язык. Модуль подменяет в `engine_v7`
четыре точки на время прогона и возвращает всё обратно:

  · `_channel_ctx`     → `studio_context_v7g.md` (в нём переписан только §4 «визуальный код»)
  · `_role`            → `prompts/v7g/` с фолбэком на `prompts/v7/`
                         (переопределён только `visual_director`; сценарист, комплаенс и
                          судья остаются общими — тема не меняет то, ЧТО мы говорим)
  · `generate_frames`  → тот же вызов, но со стилевым блоком темы в промпте
  · `A`                → `assembly_v7g` (светлая тема CSS вместо тёмной)

Запуск:
    python3 engine_v7g.py --topic "<тема>" [--format number_shock] [--go]
    python3 engine_v7g.py --rebuild runs/<ch>/<run>      # пересобрать, без вызовов API
    python3 engine_v7g.py --remix   runs/<ch>/<run>      # перебрать звуковые профили
"""
from __future__ import annotations
import os
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import engine_v7 as E7                                          # noqa: E402
import assembly_v7g as A7G                                      # noqa: E402
import schemas_v7 as S                                          # noqa: E402
from image_agent import generate_image                          # noqa: E402

PROMPTS_G = Path(__file__).resolve().parent / "prompts" / "v7g"

# --- стилевой блок темы ---------------------------------------------------------
# Едет в КАЖДЫЙ промпт кадра. Живёт здесь, а не в роли визуального директора, по той же
# причине, по которой в v7 здесь живёт негатив: сцена обязана быть побитово одинаковой во
# всех кадрах, а модель, переписывающая её своими словами, даёт дрейф материала — и тема
# рассыпается на «немного стеклянные» кадры разного вида.
_STYLE = (
    "STYLE — clinical glass visualization. This describes the SCENE and MATERIAL and "
    "overrides any conflicting scene wording above; the sentence above describes the OBJECT. "
    "The subject is rendered in translucent frosted glass with a luminous interior: internal "
    "structure visible through the surface, a gradient of emerald green through cyan into deep "
    "sapphire blue, crisp specular highlights, soft volumetric glow from within, like a "
    "high-end 3D medical visualization. "
    "Background: seamless high-key gradient from pure white through pale ice blue to a faint "
    "mint, with a soft radial bloom behind the subject — no table, no room, no floor, no "
    "horizon line, no props, no hands. The object floats weightless in clean light. "
    "Lighting: one large soft studio source from the upper left, high key, gentle contact "
    "shadow, no dark corners, no dramatic shadow. "
    "Finish: immaculate, glossy, weightless, cool colour temperature, ultra-clean commercial "
    "3D render, sharp focus on the subject, shallow depth of field behind it."
)

# Негатив темы. Отличия от v7 умышленные и их два:
#   · снят запрет «3d render» — в этой теме рендер и есть приём, а не брак;
#   · добавлен запрет на UI. Мудборд — это макет дашборда, и модель охотно рисует свои
#     карточки, шкалы и стрелки. Они дерутся с нашим слоем графики, который рендерит код.
_NEGATIVE_G = (
    "NEGATIVE: dark background, black background, moody low-key lighting, heavy shadows, "
    "dark corners, wooden table, kitchen counter, bathroom shelf, cluttered props, "
    "photorealistic human face, human skin close-up, doctor, white lab coat, medical uniform, "
    "film grain, noise, gritty texture, dust, dirt, worn or scratched or peeling surfaces, "
    "dashboard, UI panels, cards, charts, gauges, progress bars, arrows, callout lines, "
    "floating text, caption overlays, infographic text, paragraphs of body copy, "
    "watermark, channel logo, white border, photo frame, polaroid frame, paper margin, "
    "rounded photo corners, cartoon, mutated geometry, extra limbs, "
    "concrete, stone, rough matte texture, "
    "real-world brand names or trademarks, "
    # По умолчанию НИКАКИХ букв. Первый прогон 2026-08-12: разрешение «гравировка на стекле»
    # стояло глобально, и модель дописала на капсулу «PROBIOTIC 20 BCFU» в ролике про
    # омегу-3, а на голову — «SAPPHIRE PATHWAY NEURO-MAP V.20». Она не читает сценарий и
    # сочиняет содержание надписи сама, поэтому право на буквы выдаётся точечно (`_LETTERING`)
    # и только тем кадрам, которые про этикетку и заявлены такими в промпте.
    "any lettering, letters, numbers, words, engraved or embossed text on the object — "
    "image must bleed to all four edges of the canvas."
)

# Выдаётся кадру, только если он сам просит надпись (кадр про этикетку/состав).
_LETTERING = (
    " EXCEPTION to the lettering ban: this frame MAY carry short generic wording "
    "(ingredient name, dosage, form) etched or frosted into the glass surface of the object "
    "itself — small, crisp, belonging to the object, never floating over the frame. "
    "Invent no brand names and no product categories other than the one described above."
)
_WANTS_LETTERING = re.compile(r"etch|engrav|label|letter|wording|inscri", re.IGNORECASE)


def _channel_ctx_g(channel: str) -> str:
    """Конфиг канала темы. Фолбэк на v7 нужен для каналов, где темы ещё нет."""
    p = E7.CHANNELS / channel / "studio_context_v7g.md"
    return p.read_text(encoding="utf-8") if p.exists() else E7._channel_ctx(channel)


def _role_g(name: str) -> str:
    """Роли темы с фолбэком на v7: переопределяем только те, что реально отличаются."""
    p = PROMPTS_G / f"{name}.md"
    return p.read_text(encoding="utf-8") if p.exists() else (E7.PROMPTS / f"{name}.md").read_text(
        encoding="utf-8")


def _generate_frames_g(plan: S.FramePlan, out_dir: Path) -> list[Path]:
    """Тот же порядок, что в v7 (включая resume по существующим файлам), но со стилевым
    блоком темы. Refs здесь важнее, чем в v7: одинаковая стеклянная подача от кадра к кадру
    — это и есть тема, а держится она на референсах, а не на словах в промпте."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, fr in enumerate(plan.frames):
        p = out_dir / f"frame_{i:02d}.png"
        if p.exists() and p.stat().st_size > 1000:
            print(f"[frames] {p.name} уже есть — пропускаю (resume)")
            paths.append(p)
            continue
        refs = [str(x) for x in paths[-3:]] if (fr.ref_ids and paths) else []
        neg = _NEGATIVE_G + (_LETTERING if _WANTS_LETTERING.search(fr.prompt) else "")
        prompt = (f"{fr.prompt}\n{_STYLE}\n"
                  f"GRADE: {plan.grade}. LIGHT: {plan.light}. LENS: {plan.lens}.\n"
                  f"{neg}")
        generate_image("img", prompt, aspect_ratio="9:16", out=str(p), refs=refs)
        paths.append(p)
    return paths


def build_from_artifacts(run_dir: Path, channel: str,
                         sfx_profile: str = A7G.DEFAULT_SFX_PROFILE) -> Path:
    """Доводит УЖЕ посчитанный прогон до видео: кадры → озвучка → сборка.

    Нужно именно для экспериментов со стилем. Обычный `--go` заново пишет сценарий, то есть
    посмотреть план кадров, а потом собрать ИМЕННО его, было нельзя — каждый просмотр стоил
    нового сценария. Здесь: `--topic` без `--go` даёт сценарий и план на чтение, `--build`
    собирает то, что прочитали. `--rebuild` этого не умеет: он требует уже готовых кадров."""
    import json
    plan = S.FramePlan(**json.loads((run_dir / "frame_plan.json").read_text(encoding="utf-8")))
    _generate_frames_g(plan, run_dir / "frames")
    return E7.rebuild(run_dir, channel, sfx_profile=sfx_profile)


def _apply_theme() -> None:
    """Подменяет точки расширения в v7. Вызывается один раз на процесс: прогон целиком идёт
    в теме, обратной совместимости внутри одного процесса тут не требуется (в отличие от
    сборки, где подмена CSS живёт только на время рендера)."""
    E7._channel_ctx = _channel_ctx_g
    E7._role = _role_g
    E7.generate_frames = _generate_frames_g
    E7.A = A7G


def main():
    p = argparse.ArgumentParser(description="engine_v7g.py — прогон v7 в теме clinical glass")
    p.add_argument("--channel", default="vitallogic_bad_pl")
    p.add_argument("--topic", default="")
    p.add_argument("--format", default="", help=f"один из: {', '.join(S.FORMAT_BRIEFS)}")
    # Рубрика и угол появились в v7 2026-08-14. Тема их не меняет — она про визуальный язык,
    # а не про то, о чём ролик, — но прокинуть их надо, иначе экспериментальный прогон
    # нельзя поставить рядом с продакшенным на ту же тему.
    p.add_argument("--rubric", default="",
                   help=f"рубрика (по умолчанию — ротация): {', '.join(S.ACTIVE_RUBRICS)}")
    p.add_argument("--angle", default="", help="угол подачи темы (из медиаплана)")
    p.add_argument("--slug", default="")
    p.add_argument("--go", action="store_true", help="запустить генерацию кадров/озвучки/сборку")
    p.add_argument("--build", default="", metavar="RUN_DIR",
                   help="доделать посчитанный прогон: кадры → озвучка → сборка")
    p.add_argument("--rebuild", default="", metavar="RUN_DIR",
                   help="пересобрать ролик из артефактов прогона, без вызовов API")
    p.add_argument("--sfx", default=A7G.DEFAULT_SFX_PROFILE, choices=list(A7G.SFX_PROFILES))
    p.add_argument("--remix", default="", metavar="RUN_DIR")
    a = p.parse_args()

    _apply_theme()

    if a.remix:
        E7.remix(Path(a.remix), a.channel, list(A7G.SFX_PROFILES))
        return
    if a.build:
        run = Path(a.build)
        os.environ["RUN_COST_DIR"] = str(run)
        build_from_artifacts(run, a.channel, sfx_profile=a.sfx)
        return
    if a.rebuild:
        E7.rebuild(Path(a.rebuild), a.channel, sfx_profile=a.sfx)
        return
    # Префикс в slug — чтобы экспериментальные прогоны были видны в списке runs невооружённым
    # глазом и не путались с продакшеном при загрузке.
    slug = a.slug or ("v7g-" + re.sub(r"[^a-z0-9]+", "-", a.topic.lower()).strip("-")[:36])
    E7.produce(a.channel, a.topic, a.format, slug, go=a.go,
               rubric=a.rubric, angle=a.angle)


if __name__ == "__main__":
    main()
