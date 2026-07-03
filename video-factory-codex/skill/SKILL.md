---
name: video-factory
description: >-
  Производит один готовый вертикальный ролик (9:16, Reels/Shorts/TikTok) для фабрики
  контента этого проекта. Claude сам пишет весь текст — сценарий, комплаенс, план кадров, QA —
  по правилам ретеншена из ресёрча; в Gemini уходит ТОЛЬКО то, что Claude не может сделать
  (кадры через Nano Banana 2 и озвучка через Gemini TTS), сборка — локально (hyperframes + ffmpeg).
  Используй, когда просят «сделай ролик / сценарий для Shorts / собери видео по теме / прогони
  фабрику / video-factory» по каналам biz_failures, psychology, wealth_viz. Ключ Gemini берётся
  из .env этого проекта.
---

# video-factory — фабрика одного ролика

Навык превращает **тему + канал** в готовый `out.mp4` (9:16). Он переносит текстовую часть
пайплайна (`autopilot_factory/engine.py`, стадии 1–3 и 7) с Gemini-саб-агентов на **самого Claude**:
Opus пишет сценарий/комплаенс/план кадров/QA лучше и без затрат на текстовые вызовы Gemini.
В Gemini остаётся только то, что Claude физически не умеет — **пиксели и голос**.

## Разделение труда (жёсткое правило)

| Делает Claude (в этом навыке) | Делегируется Gemini | Локально |
|---|---|---|
| Сценарий (`script.json`) | Кадры — Nano Banana 2 (`image_agent.py`) | Сборка — hyperframes + ffmpeg (`assembly.py`) |
| Комплаенс (`compliance.json`) | Озвучка — Gemini TTS (`audio_agent.py`) | Транскрипт для караоке (whisper через hyperframes) |
| План кадров (`frame_plan.json`) | | Мукс аудио/видео (ffmpeg) |
| QA (`qa.json`) | | |

Всё, что уходит в Gemini и локальную сборку, инкапсулировано в один скрипт
`scripts/build_media.py`. Claude его не переписывает — он готовит JSON-контракты и запускает скрипт.

## Контракты — это закон

Текст, который пишет Claude, обязан валидироваться Pydantic-схемами из
`autopilot_factory/schemas.py` (`Script`, `ComplianceVerdict`, `FramePlan`, `QAReport`).
Полное описание полей, лимитов и того, КАК писать каждый артефакт — в
[references/authoring_guide.md](references/authoring_guide.md). Правила комплаенса и чек-лист QA —
в [references/qa_and_compliance.md](references/qa_and_compliance.md). Прочитай нужный reference
ПЕРЕД тем, как писать соответствующий артефакт.

## Рабочий процесс

1. **Вход.** Определи `channel` (`biz_failures` | `psychology` | `wealth_viz`) и `topic`.
   Если тема не задана — предложи из `autopilot_factory/channels/<channel>/media_plan.md`.
   Создай папку прогона: `autopilot_factory/runs/<YYYY-MM-DD>_<slug>/` (slug = тема, lower, пробелы→`-`, ≤40 симв).

2. **Контекст канала.** Прочитай `autopilot_factory/channels/<channel>/studio_context.md` целиком —
   это источник правды по тону, рубрикам, формулам хука, визуальному коду, стоп-листам, CTA.

3. **Сценарий → `script.json`.** Прочитай [authoring_guide.md](references/authoring_guide.md) §Сценарий.
   Напиши `Script` (EN) по правилам ретеншена. **Покажи владельцу хук + сценарий и получи «go»
   перед генерацией медиа** — текст бесплатен, а стадия 6 тратит деньги (кадры + TTS).

4. **Комплаенс → `compliance.json`.** Прочитай [qa_and_compliance.md](references/qa_and_compliance.md).
   Проверь сценарий по стоп-листам канала; при правках запиши очищенный `cleaned_script` и `fixes[]`.
   Если правил — дальше используешь `cleaned_script`.

5. **План кадров → `frame_plan.json`.** Прочитай [authoring_guide.md](references/authoring_guide.md)
   §Кадры. Ровно один кадр на бит, единый grade/light/lens, промпты Nano Banana 2 по формуле.

6. **Валидация.** Прогони `python3 scripts/validate_run.py <run_dir>` — он проверит оба JSON
   схемами до любых трат. Чини ошибки, пока не станет зелёным.

7. **QA → `qa.json`.** Прочитай [qa_and_compliance.md](references/qa_and_compliance.md) §QA.
   Оцени сценарий+план по чек-листу (advisory, не блокирует). Запиши отчёт.

8. **Медиа + сборка (тратит деньги).** После «go» владельца:
   ```bash
   python3 scripts/build_media.py <run_dir> --channel <channel>
   ```
   Скрипт: генерит кадры (Nano Banana 2, hybrid-референсы), озвучивает по битам (Gemini TTS),
   транскрибирует для караоке, собирает через hyperframes → немой mp4 → мукс озвучки → `out.mp4`.
   По завершении покажи путь к `out.mp4` и сводку `cost.json`.

## Гейты и деньги

- **Стадии 2–7 (весь текст) бесплатны** — их делает Claude. Свободно итерируй сценарий.
- **Стадия 8 (build_media) тратит** — кадры Nano Banana 2 + TTS. **Не запускай без явного согласия.**
- Стоимость каждого прогона пишется в `<run_dir>/cost.json` (`cost_tracker`). Один ролик ≈ $0.3–0.6.
- Ничего не публикуется. Навык только производит файл на диске.

## Улучшения относительно engine.py (заложены здесь)

- **Текст пишет Opus, а не flash35/pro** — качество выше, 4 текстовых вызова Gemini убраны из цены.
- **Референсы кадров — hybrid anchor** (кадр-0 как якорь стиля + предыдущий кадр), а не sliding-window
  `[-14:]`: убирает style-drift / deep-frying (обоснование — `orchestration/research/29_nanobanana_consistency.md`).
- **GRADE/LIGHT/LENS в начале промпта + негатив-блок** — как рекомендует R29 для Nano Banana 2.

Ключ Gemini (`GEMINI_API_KEY`) все раннеры читают из `.env` в корне проекта — отдельно настраивать не нужно.
