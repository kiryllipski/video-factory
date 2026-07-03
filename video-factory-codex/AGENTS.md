# AGENTS.md — video-factory (Codex-порт)

> Codex CLI читает этот файл автоматически как инструкции проекта. Это порт навыка Claude Code
> `video-factory` (фабрика одного вертикального ролика 9:16 для Reels/Shorts/TikTok). Оригинальный
> навык и все правила — в `skill/` (не удалять: `skill/SKILL.md` + `skill/references/*.md`).
> Язык проекта — русский; отраслевые термины (hook, retention, grade, safe-зона) — как принято.

## Что делает пайплайн

Из **темы + канала** делает готовый `out.mp4`. Разделение труда — жёсткое:

| Пишет **агент** (ты, Codex) — бесплатно | Внешние сервисы — тратят деньги | Локально |
|---|---|---|
| Сценарий → `script.json` | Кадры (image-модель) → `image_agent.py` | Сборка — hyperframes + ffmpeg (`assembly.py`) |
| Комплаенс → `compliance.json` | Озвучка (TTS) → `audio_agent.py` | Транскрипт для караоке (whisper через hyperframes) |
| План кадров → `frame_plan.json` | | Мукс аудио/видео (ffmpeg) |
| QA → `qa.json` | | |

**Ключевая идея порта:** весь ТЕКСТ (сценарий/комплаенс/план кадров/QA) пишет сама модель-агент —
в оригинале это Claude Opus, здесь это твоя модель в Codex. Наружу (Gemini) уходит ТОЛЬКО то, что
модель не умеет физически: пиксели и голос. Не зови текстовые стадии Gemini из `engine.produce` —
они заменены тобой.

## Контракты — это закон

Текст, который ты пишешь, ОБЯЗАН валидироваться Pydantic-схемами из `autopilot_factory/schemas.py`
(`Script`, `ComplianceVerdict`, `FramePlan`, `QAReport`). Примеры валидных артефактов — в `examples/`.
Полные правила КАК писать каждый артефакт — `skill/references/authoring_guide.md`; правила комплаенса
и чек-лист QA — `skill/references/qa_and_compliance.md`. **Читай нужный reference ПЕРЕД тем, как
писать соответствующий JSON.**

## Рабочий процесс (по шагам)

1. **Вход.** Определи `channel` (`biz_failures` | `psychology` | `wealth_viz`) и `topic`.
   Если тема не задана — предложи из `autopilot_factory/channels/<channel>/media_plan.md`.
   Создай папку прогона: `autopilot_factory/runs/<YYYY-MM-DD>_<slug>/` (slug: тема, lower, пробелы→`-`, ≤40).
2. **Контекст канала.** Прочитай `autopilot_factory/channels/<channel>/studio_context.md` целиком —
   источник правды по тону, рубрикам, формулам хука, визуальному коду, стоп-листам, CTA.
3. **Сценарий → `script.json`** (reference §Сценарий). Пиши на EN по правилам ретеншена.
   ⚠️ Озвучивается ТОЛЬКО `beats[].voiceover` (см. `engine.synth_audio`) — поле `hook` НЕ читается TTS,
   поэтому текст хука клади в `beats[0].voiceover`, а `hook` дублирует его как заголовок.
   **Покажи владельцу хук + сценарий и получи «go» до генерации медиа** — текст бесплатен, медиа тратит.
4. **Комплаенс → `compliance.json`** (reference qa_and_compliance). Проверь по стоп-листам канала;
   при правках запиши `cleaned_script` + `fixes[]`. Дальше используется `cleaned_script`.
5. **План кадров → `frame_plan.json`** (reference §Кадры). Ровно один кадр на бит, единый
   grade/light/lens, промпты image-модели по формуле, safe-зоны 9:16.
6. **Валидация:** `python3 skill/scripts/validate_run.py <run_dir>` — проверяет оба JSON схемами
   до любых трат. Чини ошибки до зелёного.
7. **QA → `qa.json`** (reference §QA). Advisory, не блокирует. Запиши отчёт.
8. **Медиа + сборка (тратит деньги, после «go»):**
   ```bash
   python3 skill/scripts/build_media.py <run_dir> --channel <channel>
   ```
   Генерит кадры → озвучивает по битам → транскрибирует для караоке → собирает hyperframes →
   немой mp4 → мукс озвучки → `out.mp4`. По завершении покажи путь и сводку `cost.json`.

## Гейты и деньги

- Стадии 2–7 (весь текст) — бесплатны, свободно итерируй.
- Стадия 8 (`build_media`) — тратит (кадры + TTS ≈ $0.3–1.2/ролик). **Не запускай без явного «go».**
- ⚠️ **Тяжёлую сборку запускай строго последовательно, один прогон за раз** — параллельные прогоны
  поднимают несколько headless-Chrome и перегружают машину.

## Окружение (критично)

- **Node ≥ 20** (лучше 22) — `hyperframes render` падает под Node 18 с `SyntaxError ... styleText`.
  Перед `build_media.py`: `export PATH="<nvm>/versions/node/v22.x/bin:$PATH"` и проверь `node -v`.
- **Python 3.9+** с `google-genai`, `pydantic`, `requests` (см. `requirements.txt`).
- **ffmpeg 8.x**, **Node 22**, `npx --yes hyperframes` (тянется автоматически при первом рендере).
- Ключ image/TTS-провайдера — из `.env` в корне бандла (`GEMINI_API_KEY`). См. `.env.example`.

## Адаптация под свой стек

Точки замены — в `README_SERGEY.md`. Коротко: `orchestration/image_agent.py` (кадры) и
`orchestration/audio_agent.py` (TTS) — единственные места, завязанные на Gemini; их можно заменить
на любого провайдера, сохранив сигнатуры `generate_image(...)` / `generate_speech(...)`.
Контракты (`schemas.py`) и сборка (`assembly.py`) от провайдера не зависят.
