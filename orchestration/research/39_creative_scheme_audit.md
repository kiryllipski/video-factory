<!-- аудит проведён вручную (Claude), 2026-07-02; источник: /Users/kirillipski/Desktop/mytools/creative production scheme -->
# Аудит проекта-аналога «creative production scheme»

## 0. Краткое резюме

`creative production scheme` (git-репозиторий, Obsidian-vault) — **работающая** фабрика
faceless-видео для польского wellness/БАД-канала **Nawigator Zdrowia** (YouTube-канал
`zdrowie_pl`, бренд VitalLogic). В отличие от нашего `autopilot_factory/` (скелет Фазы 0:
`engine.py` — 192 строки, стадии 5-6 — заглушки), там пайплайн **полностью реализован и
эксплуатируется**: на 2026-07-01 произведено и поставлено в очередь/опубликовано ~24 ролика,
подключены learning loop, YouTube Analytics, media-planning, очередь публикаций 2/день.

Технологический стек идентичен нашему (Claude-оркестратор + Gemini-саб-агенты через
`gemini_agent.py`, `gemini-3.1-flash-image` для кадров, HyperFrames+ffmpeg для сборки,
единственная зависимость — `GEMINI_API_KEY`, никаких OpenAI/ElevenLabs). Каталог
`orchestration/research/research 2/` побайтово совпадает с нашим `orchestration/research/` —
не пересказываю. Всё остальное — **другой, гораздо более зрелый инстанс той же архитектуры**,
с реальным production-опытом (баги, фиксы, аудиты, юнит-экономика по счетам).

**Что особенно ценно:** готовая техническая обвязка `engine.py` (TTS/ImageGen/HyperFrames
рендер на 1600+ строк, отлажена на реальных прогонах), детальный `cost_tracker.py`
(пер-модель/пер-вызов учёт в USD), система медиапланирования с guard'ами разнообразия
(`media_plan.py`), полноценный YouTube-паблишер с OAuth/мультиканальностью/Analytics API,
и 13-шаговая креативная цепочка с ролями, которых у нас пока нет (Style Director, Thumbnail
Director, HyperFrames Art Director, Creative QA-судья, Publisher-metadata).

---

## 1. Карта проекта

```
creative production scheme/                    (git-репозиторий, Obsidian-vault)
├── CLAUDE.md / AGENTS.md / README.md           — роль ассистента, обзор, карта документов
├── MEDIA_PLAN_TRACKER.md                       — живой трекер: медиаплан + гипотезы + метрики + costs
├── VIDEO_PRODUCTION_PLAYBOOK.md                — операционный плейбук (шаблон процесса)
├── STYLE_MODULES_FROM_MOODBOARD.md             — библиотека визуальных модулей (6 штук) из мудборда
├── MVP_AUTOPILOT_VIDEO_FACTORY.md              — исходный дизайн-план (историческая версия)
├── *.canvas                                    — Obsidian JSON Canvas диаграммы процесса
│
├── autopilot_factory/                          — РАБОЧИЙ КОД (это основной актив)
│   ├── pipeline.py            (702 стр.) — оркестратор рантайма, run_context, кэш шагов
│   ├── engine.py              (1604 стр.) — TTS+ImageGen+HyperFrames рендер (техническое ядро)
│   ├── schemas.py             (283 стр.) — Pydantic-контракты 13-шаговой креативной цепочки
│   ├── config.py                          — легаси-конфиг (модели, старые Pydantic-схемы engine)
│   ├── cost_tracker.py        (175 стр.) — учёт стоимости USD, пер-модель/пер-вызов, JSONL-лог
│   ├── media_plan.py          (218 стр.) — медиаплан-batch + guard разнообразия (hook/pillar/CTA)
│   ├── scheduling.py          (106 стр.) — единый источник правды по слотам публикации (2/день)
│   ├── learning_loop.py       (337 стр.) — collect (YouTube Data+Analytics API) → learn (pattern_bank)
│   ├── prepublisher.py        (216 стр.) — мягкая (non-blocking) проверка перед публикацией
│   ├── produce_queue.py       (149 стр.) — батч-продюсер + постановка в очередь публикации
│   ├── produce4.py                        — обёртка v4 продюсера
│   ├── rebuild_audio.py                   — пересборка ролика без перегенерации (фикс аудио-багов)
│   ├── import_studio_export.py            — импорт CSV YouTube Studio (impressions — недоступны в API)
│   ├── creative_prompts/      (13 файлов) — роли новой креативной цепочки (см. §1.1)
│   ├── prompts/                (4 файла) — легаси-промпты старого engine (scriptwriter/director/...)
│   ├── publishers/youtube.py  (237 стр.) — OAuth, мультиканальность, videos.insert, Analytics
│   ├── trend_scout/                       — поиск+скоринг тем (Google Trends, YouTube, LLM-fallback)
│   ├── learning/                          — experiments.jsonl, learnings.json/.md, pattern_bank.json,
│   │                                         ANALYTICS.md, studio_exports/ (ручные Studio CSV)
│   ├── assets/music/           (8 треков) — WAV-библиотека + generate_tracks.py (Lyria)
│   ├── tokens/zdrowie_pl.json             — OAuth-токен канала
│   ├── studio_context.md      (189 стр.) — «мозг студии»: бренд/аудитория/claims/визуал/пиллары
│   ├── BACKLOG.md / PRINCIPLES.md / PUBLISH_METADATA_GUIDE.md / README.md
│   ├── runs/run_*/                        — ~24 прогона: script→...→final.mp4→thumbnail.jpg
│   └── archive/                           — 2 снапшота предыдущих версий пайплайна (импл./промпты)
│
├── orchestration/                              — Gemini-оркестрация (build-time)
│   ├── gemini_agent.py        (172 стр.) — раннер (идентичен нашему по духу, другой реестр моделей)
│   ├── deep_research_agent.py             — раннер Deep Research саб-агентов (Interactions API, фон)
│   ├── GEMINI_ORCHESTRATION.md
│   ├── research/                          — build-time ресёрч; research/deep/ — Deep Research (A1-A4,B1,C1-C4)
│   ├── research/research 2/               — ⚠️ побайтовая копия нашего orchestration/research/ (не разбирал)
│   ├── roles/                             — deep_content_scout.md, deep_visual_researcher.md и др.
│   └── tasks/                             — брифы для Deep Research саб-агентов
│
└── moodboard_contact_sheets/                    — 4 контакт-листа референсов (JPG)
```

### 1.1. Стадии креативной цепочки (`pipeline.py:run_creative_chain`)

13 шагов, каждый — кэшируемый structured-output вызов Gemini через `gemini_agent.run_structured`:

| # | Роль (`creative_prompts/*.md`) | Модель | Артефакт | Комментарий |
|---|---|---|---|---|
| 1 | `attention_brief` | flash35 | `01_attention_brief.json` | viewer_situation, attention_button, experiment_hypothesis |
| 2 | `hook_writer` | flash35 | `02_hooks.json` | 5-8 хуков + selected |
| 3 | `scriptwriter` | flash35 | `03_script.json_rich` | сцены + attention_map |
| 4 | `creative_qa` (судья) | **pro** | `04_creative_qa.json` | hard-block по regulatory claims, 1 ретрай |
| 5 | `style_director` | flash35 | `05b_style_brief.json` | выбор визуального модуля (см. §1.2), идёт ДО montage |
| 6 | `montage_vision` | flash35 | `05_montage_vision.json` | ритм, voice (Gemini TTS), monage principle |
| 7 | `translator` | flash | `04_translation.json_rich` | RU→PL + TTS-режиссура (audio tags) |
| 8 | `visual_director` | flash35 | `06_visual_plan.json` | per-scene motion/infographic/safe-zones |
| 9 | `prompt_engineer` | flash35 | `07_image_prompts.json` | англ. промпты для Nano Banana 2, negative_prompt |
| 10 | `music_planner` | flash | `08_music_plan.json` | выбор трека из библиотеки |
| 11 | `hyperframes_director` | flash35 | `09_hyperframes_plan.json` | motion-оверлей, CTA(проговаривается), outro |
| 12 | `thumbnail_director` | flash35 | `10_thumbnail.json` | кадр+2-3 слова обложки под CTR |
| 13 | `publisher` | flash | `publish_package.json` | title/description/hashtags под YouTube SEO |

Затем **проекция** (`project_to_engine`) в legacy-совместимые `01_script/02_shots/03_prompts/
04_translation`, которые потребляет `engine.py --resume_dir` (только дорогие стадии: TTS,
ImageGen, HyperFrames-рендер).

### 1.2. Визуальная система — 6 модулей (`STYLE_MODULES_FROM_MOODBOARD.md`)

Отдельная роль `Style Director` (между Script/QA и Montage) выбирает 1 главный + 1
вспомогательный модуль из библиотеки: **Premium Bio Macro** (макро-субстанции, дефолт для
доверия), **Abstract Process Lab** (невидимые процессы, частицы/капли), **Editorial Formula
Board** (сравнения A vs B), **Soft Habit Characters** (эмоциональный персонаж для
поведенческих тем), **Surreal Scale Metaphor** (масштабный hook-контраст), **Human Editorial
Ritual** (финал/CTA, бытовой жест). У нас в основном проекте такого модульного подхода нет —
`orchestration/roles/visual_director.md` работает без промежуточного «выбора вселенной».

### 1.3. Статус завершённости (по git log, 8 коммитов, с `fd80a17` по `98c4ccd`)

Не черновик — работающая система с несколькими итерациями аудита: `v1.0` (первый рабочий
прогон) → `v1.1` → `v1.2` (CTA проговаривается, thumbnail director) → `v1.3` (Style→Montage
реордер, claims в §6 единый источник, чистые частицы vs mesh) → `v1.4` (медиаплан-driven
разнообразие). `BACKLOG.md` (700+ строк) документирует итеративные аудиты с найденными
багами и их фиксами (WAV-конкатенация щёлкала на стыках сцен — найдено и исправлено;
`VOICE_SPEED_UP=1.30` выше безопасного диапазона atempo — открытый вопрос; отсутствие
`loudnorm` на мастер-миксе — открытый вопрос).

---

## 2. Переиспользуемые наработки

### 2а. Для основной фабрики (`0-video production/autopilot_factory/`)

1. **`autopilot_factory/cost_tracker.py`** (175 строк) — прямой апгрейд нашего варианта.
   У нас `autopilot_factory/cost_tracker.py` пока не создан/минимален; здесь — готовый модуль
   с таблицей `PRICING` по моделям (in/out токены + per_image), JSONL-логом каждого вызова
   (`logs/cost_log.jsonl`) и агрегацией в `cost_log.json` (по модели + итог). Подключается
   мягким импортом в `gemini_agent.py`/`engine.py`/`pipeline.py` через `RUN_COST_DIR` — паттерн
   прямо переносим.

2. **HyperFrames-обвязка внутри `engine.py`** (строки ~1030-1600) — готовый генератор HTML-
   композиции: CSS для субтитров-чанков (word-level подсветка keyword, `paint-order: stroke
   fill`), инфографика (`checklist`/`comparison`/`graph_waves` с SVG-волнами), motion-оверлеи
   (`particles`/`droplets`/`powder_dust`/`light_streaks` через `.motion-layer span`), CTA-чип и
   brand-chip (сейчас отключены флагами `RENDER_CTA_OVERLAY`/`RENDER_BRAND_CHIP`), функция
   `get_camera_animation()` — маппинг словесного описания движения камеры в GSAP-параметры.
   У нас в `assembly.py` (120 строк) этого пока нет вообще — это самый прямой кандидат на
   перенос технической части (не бренд-специфичных CSS-констант).

3. **`schemas.py`** — их 13-стадийный набор Pydantic-схем (`AttentionBrief`, `Hooks`,
   `CreativeQA`, `StyleBrief`, `VisualPlan`, `ImagePrompts`, `HyperframesPlan`, `ThumbnailPlan`,
   `PublishPackage`) — готовая референсная модель декомпозиции ролей, гораздо детальнее нашей
   `schemas.py` (7 моделей). Особенно ценны `CreativeQA` (structured QA-судья с `blocking_issues`
   / `recommended_fixes` и score-полями) и `ThumbnailPlan` (у нас обложка вообще не спроектирована).

4. **`media_plan.py`** (218 строк) — готовый guard разнообразия батча: `recent_signals()`
   парсит `experiments.jsonl` и не даёт соседним роликам повторять hook-механику/attention-
   button/pillar/визуальный модуль; `follow_deficit()` принудительно вставляет `follow`-CTA,
   если 4+ роликов подряд без него; `directive_md()` генерирует markdown-директиву,
   инъектируемую в целевые роли. У нас в `autopilot_factory/channels/*` пока нет ничего
   подобного для батч-продакшена нескольких роликов подряд — прямое масштабирование за
   пределы одного ролика.

5. **`learning_loop.py`** (337 строк) — полный цикл `collect` (YouTube Data API v3 statistics +
   YouTube Analytics API v2 retention: `averageViewDuration`/`averageViewPercentage`/`shares`/
   `subscribersGained`/`engagedViews`) → `extract_features()` (сводит креатив-сигналы ролика) →
   `learn()` (Gemini `pro` синтезирует `Learnings` Pydantic-схему) → `pattern_bank.json`
   (агрегированный engagement по hook_mechanism/attention_button/music_track). У нас в `PLAYBOOK.md`
   петля обучения только описана как концепция — здесь есть рабочий код и реальные данные.

6. **`scheduling.py`** (106 строк) — простой, но полезный паттерн: единый источник правды по
   слотам публикации (`DAILY_SLOTS`), функция `next_slots()` находит первый свободный слот
   после последнего запланированного ролика (по `post_result.json` в `runs/*`). Пригодится, если
   решим публиковать больше 1 ролика в день.

7. **`prepublisher.py`** (216 строк) — non-blocking пре-публикационный чек-лист: regex-поиск
   запрещённых claims (`FORBIDDEN_CLAIM_PATTERNS`), проверка вертикальности видео через
   `ffprobe`, длины title/description, наличия `#Shorts`, кириллицы в польском тексте,
   дисклеймера. Прямо переносимый паттерн для наших roles/researcher или будущего QA-гейта.

8. **`publishers/youtube.py`** (237 строк) — рабочий, отлаженный YouTube-паблишер: OAuth per-
   channel (`tokens/<label>.json`, мультибрендовость), `videos.insert` + `thumbnails().set()`,
   `--publish-at` (RFC3339, авто-паблишинг из private), запись `post_result.json` +
   накопительный `experiments.jsonl`. У нас паблишер ещё не реализован вообще — это готовый
   к переносу модуль (только поменять claims-паттерны/лейблы каналов).

9. **`trend_scout/`** — модуль поиска и скоринга тем (Google Trends + YouTube trending + LLM-
   фоллбэк), с банком тем (`bank.py`), скорером (`scorer.py`, threshold ≥7.0) и HTML-репортером.
   У нас темы пока выбираются вручную/по медиаплану — этот модуль закрывает автоматизацию
   discovery-стадии.

### 2б. Для локальных пайплайнов на MacBook Air M3 / Mac M4 Pro

1. **Требования к окружению уже прожиты на 8 ГБ RAM** (`PRINCIPLES.md §7`): HyperFrames-рендер
   (Chromium на ~835 кадров 1080×1920 + ffmpeg) на 8 ГБ ловит OOM; решение — `pipeline.run_engine()`
   ретраит рендер (4 попытки по умолчанию) с `pkill -9 -f hyperframes` + пауза 25с перед каждой
   попыткой, TTS/кадры остаются кэшированными, повтор идёт сразу к рендеру. Это прямая
   инструкция для развёртывания на MacBook Air M3 16GB — тот же паттерн ретраев стоит взять
   как есть (`_engine_env()` + `run_engine()` в `pipeline.py`).

2. **Node ≥22 обязателен** для HyperFrames ≥0.7 (`styleText` из `util`) — `pipeline._engine_env()`
   ищет самую новую Node≥22 в `~/.nvm/versions/node` и подставляет в PATH перед вызовом
   `subprocess`. Полезный локальный паттерн, если на машинах команды разные версии Node через nvm.

3. **ffmpeg-рецепты, отлаженные вручную:**
   - Склейка WAV по сценам через `wave.readframes()` (не бинарная конкатенация — баг с
     44-байтным RIFF-заголовком в середине потока даёт щелчки на стыках, найден и
     задокументирован в `BACKLOG.md` A7).
   - `silenceremove` для обрезки тишины TTS-дорожек (`start_threshold=-45dB`).
   - `atempo` для ускорения голоса (но задокументирован **риск**: `VOICE_SPEED_UP=1.30`
     выше безопасного диапазона 1.10-1.25x — металлизация тембра на стыках, см. R2 в
     `BACKLOG.md`; для наших локальных пайплайнов держать ближе к 1.15-1.20).
   - Экспорт thumbnail из финального видео через `ffprobe`+`ffmpeg -ss ... -frames:v 1`
     с кропом под 1080×1920, наложение текста через PIL (`_compose_thumbnail_text`).
   - **Отсутствует, но нужно добавить:** `loudnorm`/`alimiter` на финальный микс (см. R1 в
     `BACKLOG.md`) — открытая рекомендация, которую стоит закрыть у нас сразу, а не повторять
     их баг.

4. **Единственная внешняя зависимость — `GEMINI_API_KEY`** (проверено через `.env`): TTS
   (`gemini-3.1-flash-tts-preview`, голоса Aoede/Sulafat/Achird/...), ImageGen
   (`gemini-3.1-flash-image`), текстовые модели — всё через один ключ Google AI Studio. Нет
   ElevenLabs/OpenAI/сторонних TTS. Минимизирует конфигурацию при разворачивании на новой
   машине — один `.env` с одной переменной плюс `pip install -r requirements.txt`
   (`google-genai`, `pydantic`, `soundfile`, `pillow`, `python-dotenv`, плюс
   `google-api-python-client`/`google-auth-oauthlib` для YouTube-паблишера).

5. **`assets/music/generate_tracks.py`** + `lyria_tracks.md` — рецепт локальной генерации
   8 BGM-треков через Lyria (Google) с сохранением в WAV-библиотеку — воспроизводимый паттерн
   «сгенерировать один раз, переиспользовать всегда», экономит на runtime-генерации музыки.

6. **`rebuild_audio.py`** — узкий скрипт «пересобери только звук/рендер без перегенерации
   дорогих TTS/ImageGen-шагов» — полезный паттерн для локальной итерации, когда генерация
   кадров стоит денег, а фиксить нужно только монтаж/звук.

---

## 3. Отличия и конфликты с основным проектом

| Аспект | `0-video production` (наш) | `creative production scheme` (аналог) |
|---|---|---|
| Статус рантайма | `engine.py` = скелет Фазы 0 (192 стр., стадии 5-6 — TODO-заглушки) | Полностью рабочий, 24+ прогона в проде |
| Реестр Gemini-моделей | `lite/flash/flash35/pro` + `antigravity`/`research*` (недоступны через SDK) | Идентичный принцип, но **другие ID**: `flash35`→`gemini-3.5-flash` (у нас тоже), модели помечены `estimated` в ценах по-другому; `orchestration/deep_research_agent.py` — отдельный раннер, обходит ограничение SDK (`400: only supports Interactions API`) прямыми REST-вызовами к `v1alpha/interactions` (фоновая задача + polling до 40 мин). У нас Deep Research зафиксирован как принципиально недоступный через SDK — это готовый рабочий обход, достойный переноса |
| Число креативных ролей | 4 (scriptwriter/compliance/visual_director/qa) в `autopilot_factory/prompts/` | 13 (attention_brief→hooks→script→QA→style→montage→translator→visual→prompt_engineer→music→hyperframes→thumbnail→publisher) — значительно более гранулярная декомпозиция |
| Compliance/claims | `compliance.md` — отдельная роль-стадия 2 | Единый источник правил в `studio_context.md §6`, все роли **ссылаются**, не дублируют (явный архитектурный принцип «single source of truth», применённый как урок после аудита рассинхрона) |
| Формат JSON-контрактов | `Script.beats[]` (voiceover/on_screen_text/visual_cue/dur_s), плоский `FramePlan.frames[]` | `Script.scenes[]` (text_ru/beat/duration_hint_sec) + отдельный `AttentionBeat[]` map; кадр описывается в 3 разнесённых артефактах (`visual_plan`→`image_prompts`→`hyperframes_plan`) — более многослойная, но менее компактная схема |
| Визуальный арт-дirección | Одна роль `visual_director.md`, без модульной библиотеки | Отдельная роль `Style Director` + библиотека 6 визуальных модулей (`STYLE_MODULES_FROM_MOODBOARD.md`) с явными правилами комбинирования — концептуально более развитая система |
| CTA/брендинг на экране | Не специфицировано в нашем `assembly.py`/промптах | Осознанное решение: CTA **проговаривается**, не рисуется плашкой (`RENDER_CTA_OVERLAY=False`); имя бренда никогда не на экране (`RENDER_BRAND_CHIP=False`) — прямая рекомендация к рассмотрению у нас |
| Cost tracking | `cost_tracker.py` есть, но менее детален (нет проверки) | Пер-вызов JSONL + агрегация по модели, реальные данные ($0.52-0.60/ролик, кадры = ~70% стоимости) |
| Паблишинг | Не реализован (`autopilot_factory/` не имеет `publishers/`) | Полный YouTube-паблишер с мультиканальностью, Analytics API, scheduled publish |
| Локальная генерация музыки | Не описано | Lyria-рецепт + готовая WAV-библиотека 8 треков |
| Trend discovery | Не реализовано (темы вручную/через `channels/*`) | `trend_scout/` — Google Trends + YouTube + LLM fallback + скоринг |
| Изображение-модель | `gemini-3.1-flash-image` = Nano Banana 2, тот же стандарт | Совпадает, включая форс через `image_config(aspect_ratio="9:16")` — то же самое известное ограничение модели, тот же фикс |
| Ниша/язык роликов | Нейтральная фабрика под несколько ниш (biz_failures/psychology/wealth_viz) | Жёстко заточено под один канал (PL wellness/БАД, VitalLogic) — большая часть `studio_context.md`/`media_plan.py` контента не переносима буквально, но архитектура и код — да |
| MCP nano-banana | У нас явно запрещён (решение владельца), используем `image_agent.py` | В их коде нет MCP вообще — прямой вызов `google-genai` SDK, что совпадает с нашим подходом через `image_agent.py`/`gemini_agent.py` |

**Конфликтов в смысле несовместимых решений нет** — это, по сути, наш же архитектурный
подход (Claude-оркестратор + Gemini-саб-агенты + Nano Banana 2 + HyperFrames/ffmpeg),
доведённый до продакшена на другой нише и полгода вперёд по времени разработки. Различия —
в глубине декомпозиции ролей и в том, что там уже пройден путь «граблей» (WAV-щелчки,
OOM-рендер, upload-лимиты YouTube, style/montage реордер), задокументированный в `BACKLOG.md`.

---

## 4. Рекомендации

### Забрать в основную фабрику (`autopilot_factory/`), в порядке приоритета

1. **`cost_tracker.py`** — портировать их версию почти as-is (пер-вызов JSONL + агрегация);
   у нас сейчас нет сопоставимой детализации.
2. **HyperFrames-генератор HTML** из `engine.py` (~600 строк CSS/GSAP-обвязки) — взять как
   референс для нашего `assembly.py`, вычистив бренд-специфичные цвета/константы (charcoal/
   forest-green — их бренд-палитра, не наша).
3. **`ThumbnailPlan` + `thumbnail_director.md`** — у нас обложка Shorts вообще не
   спроектирована как отдельная стадия; это готовый, отлаженный на практике контракт.
4. **`CreativeQA` схема + паттерн `_FRESH`-гейта** (одна перегенерация при провале QA, но
   только если шаг реально пересчитан в этом запуске, не поднят из кэша) — прямое решение
   проблемы рассинхрона на resume, которую мы ещё не встречали, но встретим.
5. **`publishers/youtube.py`** — готовый к адаптации паблишер (замена claims-паттернов и
   лейблов каналов на наши), закрывает у нас полностью отсутствующую стадию публикации.
6. **`media_plan.py`-паттерн guard разнообразия** — актуален, как только будем производить
   больше 1 ролика за раз по одному каналу.
7. **`orchestration/deep_research_agent.py`** — рабочий обход недоступности Interactions API
   через прямые REST-вызовы (создание фоновой interaction + polling по id). У нас в CLAUDE.md
   зафиксировано, что `research*`/`antigravity` принципиально недоступны через текущий SDK —
   стоит проверить, снимает ли этот обход ограничение и для нас, прежде чем продолжать
   довольствоваться `--search`-grounding как заменой глубокого ресёрча.
8. Изучить **`BACKLOG.md` раздел R1-R9** (их собственный аудит с привязкой к нашему
   `orchestration/research/`) — это готовый список известных рисков (loudnorm отсутствует,
   atempo>1.25 рискован, non-atomic JSON writes) с конкретными номерами строк кода, которые
   стоит проверить/предотвратить у нас заранее, до того как они проявятся как баги.

### Взять для локальных пайплайнов (MacBook Air M3 16GB / Mac M4 Pro 48GB)

1. **Ретрай-паттерн рендера на low-memory** (`pipeline.run_engine`, `pkill -9 -f hyperframes` +
   пауза 25с, до 4 попыток) — прямо для MacBook Air M3 16GB, где HyperFrames+Chromium+ffmpeg
   может испытывать давление на память при параллельной работе.
2. **Node≥22 auto-detect через nvm** (`_engine_env()`) — снимает ручную настройку PATH на
   машинах команды.
3. **ffmpeg-рецепты**: WAV-конкатенация через `wave.readframes()` (не бинарная), `silenceremove`
   тишины, кроп-экспорт thumbnail — переносить как проверенные сниппеты, а не переизобретать.
   Добавить `loudnorm`/`alimiter`, которого нет даже у них (их же открытый TODO).
4. **`assets/music/generate_tracks.py`** — рецепт локальной one-off генерации BGM-библиотеки
   через Lyria, снимающий необходимость платить за музыку на каждый ролик.
5. Единая зависимость на `GEMINI_API_KEY` подтверждает, что наш текущий подход (без
   MCP nano-banana, прямой SDK) — правильный курс для лёгкого разворачивания на нескольких
   машинах: один `.env`, один `pip install -r requirements.txt`, без OAuth-плясок кроме
   YouTube-паблишера (который нужен по требованию, не по умолчанию).
