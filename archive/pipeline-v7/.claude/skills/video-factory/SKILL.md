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
| Комплаенс (`compliance.json`) | Озвучка — Gemini TTS (`audio_agent.py`) | Тайминг субтитров без ASR (`engine._estimate_word_timestamps`) |
| План кадров (`frame_plan.json`) | | Мукс аудио/видео (ffmpeg) |
| QA (`qa.json`) | | |
| Пакет публикации (`publish_package.json`) | | |

Всё, что уходит в Gemini и локальную сборку, инкапсулировано в один скрипт
`scripts/build_media.py`. Claude его не переписывает — он готовит JSON-контракты и запускает скрипт.

## Контракты — это закон

Текст, который пишет Claude, обязан валидироваться Pydantic-схемами из
`autopilot_factory/schemas.py` (`Script`, `ComplianceVerdict`, `FramePlan`, `QAReport`).
Полное описание полей, лимитов и того, КАК писать каждый артефакт — в
[references/authoring_guide.md](references/authoring_guide.md). Правила комплаенса и чек-лист QA —
в [references/qa_and_compliance.md](references/qa_and_compliance.md). Прочитай нужный reference
ПЕРЕД тем, как писать соответствующий артефакт.

## Варианты сборки (какой скрипт стадии 8 запускать)

| Вариант | Скрипт | Когда |
|---|---|---|
| Продакшен | `scripts/build_media.py` | по умолчанию |
| v4-exp «под запрос» | `scripts/build_media_v4exp.py` | когорта H7 (метка `4.0-exp`) |
| **v5-collage** (T1) | `scripts/build_media_v5collage.py` | когорта H8 (метка `5.0-collage`) — печатный бумажный коллаж вместо фотореализма, кадр-постер на бит + Ken Burns. Пишется обычный `frame_plan.json`. |
| **v6-layers** (T2) | `scripts/build_media_v6layers.py` | когорта H8 (метка `6.0-layers`) — «живой коллаж»: стикер-листы → вырезки → анимация слоёв. Вместо `frame_plan.json` пишется **`collage_plan.json`**. Кадры дешевле в ~3 раза (2 генерации на 15 битов). |

Для обоих коллажных вариантов **прочитай [references/collage_style.md](references/collage_style.md) ПЕРЕД написанием плана**:
стилевой блок и негатив приклеивает сам скрипт, поля `lens`/`grade`/`light` имеют коллажную
семантику (T1), а раскладка листов и битов имеет свои правила (T2). Дизайн эксперимента и
гипотеза H8 — [docs/experiments/2026-08-05_v5collage.md](../../../docs/experiments/2026-08-05_v5collage.md).

Дубли не заменяют продакшен и не меняют его поведение — правило владельца «текущий пайплайн
не трогай, продублируй».

## Рабочий процесс

1. **Вход.** Определи `channel` (`biz_failures` | `psychology` | `wealth_viz` | `vitallogic_bad_pl`) и `topic`.
   Если тема не задана — предложи из `autopilot_factory/channels/<channel>/media_plan.md`.
   Создай папку прогона: `autopilot_factory/runs/<channel>/<YYYY-MM-DD>_<slug>/` (slug = тема, lower,
   пробелы→`-`, ≤40 симв) — прогоны разложены по каналам, не общей кучей (реорганизовано 2026-07-04).

2. **Контекст канала.** Прочитай `autopilot_factory/channels/<channel>/studio_context.md` целиком —
   это источник правды по тону, рубрикам, формулам хука, визуальному коду, стоп-листам, CTA.

3. **Сценарий → `script.json`.** Прочитай [authoring_guide.md](references/authoring_guide.md) §Сценарий.
   Напиши `Script` (язык канала) по правилам ретеншена. **v2:** обязательно `poster_text`,
   симптом-хук ≤1.5с, бит 2 без пересказа хука, петля в финале. **v3 (2026-07-15):**
   хук-лаборатория (3 варианта «хук+постер», выбор по чек-листу), постер ≤4 слов с
   *акцент-словом*, `cta_plate` (финальная плашка ≤5 слов), таргет 22–32с.
   **Покажи владельцу хук + сценарий и получи «go» перед генерацией медиа** — текст бесплатен,
   а стадия 6 тратит деньги (кадры + TTS).

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
   Скрипт: генерит кадры (Nano Banana 2, hybrid-референсы) **+ v3 frame-QA (vision) с
   автоперегенерацией бракованных кадров (≤2 попытки, итог — `frame_qa.json`)**, озвучивает по
   битам (Gemini TTS), оценивает пословный тайминг для караоке (без ASR —
   `engine._estimate_word_timestamps`, 2026-07-05: whisper убран, см. authoring_guide.md),
   собирает через hyperframes → немой mp4 → мукс озвучки **+ v3: BGM-подложка канала
   (`channels/<ch>/assets/bgm/`, −21дБ) и финальная CTA-плашка** → `out.mp4`, затем **v3
   video-QA** (3 стоп-кадра, advisory → `video_qa.json`) и копия `out.mp4` (`engine.deliver`,
   с 2026-07-07) во внешнее хранилище iCloud —
   `.../external storage/video/0.5/<channel>/<date>_<slug>/out.mp4`
   (`VIDEO_DELIVERY_ROOT` в `engine.py`; `run_dir` с рабочими файлами остаётся локально). По
   завершении покажи путь к `out.mp4` (локальный и доставленный), сводку `cost.json` и
   замечания frame/video-QA.

9. **Пакет публикации → `publish_package.json`** (схема `PublishPackage`, добавлена 2026-07-05 —
   раньше эта стадия отсутствовала вообще, ни один ролик не имел готовых title/description/hashtags).
   Пиши на языке канала: `title` (≤100 симв, с ключевым словом темы), `description` (3-5 абзацев:
   раскрытие темы → практический вывод → призыв поделиться, обязательный дисклеймер канала последним
   абзацем — бери из studio_context §7), `hashtags` (3-6, первые topic-specific, включая `#Shorts`).
   **v2 (growth_plan):** плюс `pinned_comment` (острый бинарный вопрос зрителю — паблишер запостит
   его владельческим комментом после выхода ролика в public, команда `post-comments`) и
   `title_template` (метка шаблона заголовка: `blad|liczba|zakaz|pytanie_binarne|kontrast|inne`;
   ротацию смотри в studio_context канала — «Ten błąd» ≤30% выпусков).
   Бесплатно, делает Claude, как и весь остальной текст.

## Гейты и деньги

- **Стадии 2–7 и 9 (весь текст) бесплатны** — их делает Claude. Свободно итерируй.
- **Стадия 8 (build_media) тратит** — кадры Nano Banana 2 + TTS. **Не запускай без явного согласия.**
- Стоимость каждого прогона пишется в `<run_dir>/cost.json` (`cost_tracker`). Один ролик ≈ $0.3–0.6.
- Навык сам по себе ничего не публикует — только производит файлы на диске (включая
  `publish_package.json`). **Автозагрузка возможна** (портирована 2026-07-10 из `../creative
  production scheme`) — `autopilot_factory/publishers/youtube.py upload`, поддерживает отложенную
  публикацию (`--publish-at`, RFC3339 UTC). Токен уже есть для `vitallogic_bad_pl`
  (`autopilot_factory/tokens/vitallogic_bad_pl.json`); для biz_failures/psychology/wealth_viz нужен
  `youtube.py auth --channel <label> --client-secret client_secret.json` (аккаунты ещё не созданы).
  **Публикация — видимое вовне действие: всегда подтверждай с владельцем перед вызовом `upload`**,
  даже если файлы уже собраны.

## Улучшения относительно engine.py (заложены здесь)

- **Текст пишет Opus, а не flash35/pro** — качество выше, 4 текстовых вызова Gemini убраны из цены.
- **Референсы кадров — hybrid anchor** (кадр-0 как якорь стиля + предыдущий кадр), а не sliding-window
  `[-14:]`: убирает style-drift / deep-frying (обоснование — `orchestration/research/29_nanobanana_consistency.md`).
- **GRADE/LIGHT/LENS в начале промпта + негатив-блок** — как рекомендует R29 для Nano Banana 2.

Ключ Gemini (`GEMINI_API_KEY`) все раннеры читают из `.env` в корне проекта — отдельно настраивать не нужно.
