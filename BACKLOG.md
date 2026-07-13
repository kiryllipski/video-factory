# BACKLOG / HANDOFF — состояние и следующие шаги

> Живой документ для продолжения из нового чата. Читай после `CLAUDE.md` → `PLAYBOOK.md` → `ARCHITECTURE.md`.
> Обновлено: 2026-07-07 (сессия — готовые видео переведены на внешнее хранилище iCloud).

## 🆕 Хранение готовых видео перенесено на iCloud (2026-07-07)
Все ранее собранные ролики (21 прогон, ~1.9GB) перенесены (не скопированы) из
`autopilot_factory/runs/<channel>/...` целиком в
`/Users/kirillipski/Library/Mobile Documents/com~apple~CloudDocs/external storage/video/0.5/<channel>/<date>_<slug>/`
— локальной рабочей копии для них больше нет. Для НОВЫХ прогонов пайплайн не меняет `runs/` как
рабочую директорию (frames/audio/hf/json остаются там), но добавлена новая стадия `engine.deliver()`
(`autopilot_factory/engine.py`) — копирует финальный `out.mp4` в `DELIVERY_ROOT` (env
`VIDEO_DELIVERY_ROOT`, дефолт — путь выше) сразу после сборки. Вызывается из `engine.produce()`
и `.claude/skills/video-factory/scripts/build_media.py`. Детали — `ARCHITECTURE.md` §1/§3.

## 🆕 Майнер тем `idea_miner.py` + ресёрч запуска (2026-07-06)
Разовый ресёрч → два свода с проверяемыми источниками:
- [orchestration/research/54_faceless_youtube_launch_playbook.md](orchestration/research/54_faceless_youtube_launch_playbook.md) — запуск faceless-каналов 2025–2026: выбор ниши, RPM по нишам, медиаплан/каденс, метрики-пороги (swipe-away <40%, APV), YPP-2026, политика Inauthentic Content, масштабирование, чек-лист.
- [orchestration/research/55_content_ideation_tools.md](orchestration/research/55_content_ideation_tools.md) — откуда брать темы и чем измерять спрос программно (YouTube Data API, autocomplete, DataForSEO, pytrends), парсинг конкурентов, outlier-метод.

Из R55 собран рабочий тул **`orchestration/idea_miner.py`** (документирован в `CLAUDE.md`, зафиксирован в `ARCHITECTURE.md` §1):
autocomplete (бесплатно) → YouTube Data API v3 → `--mode full` (outlier у мелких, порог `--min-subs`) ИЛИ
`--mode top` (самые просматриваемые = подходы крупных) → опц. комменты-боли → LLM-ранжирование (Gemini) в JSON-бэклог.
Ключ `YOUTUBE_API_KEY` в `.env` (GCP-проект `family-kitchen-480213`, там включён YouTube Data API v3; ключ ограничен этим API, без service-account-binding).
Первые бэклоги — `orchestration/idea_backlog/vitallogic_bad_pl.json` + `vitallogic_EN_market_study.json`.
**Находка ниши:** PL-органика тонкая (outlier ≈ бренд-реклама NOYO®); для PL сильнее autocomplete + адаптация англоязычного `top`. TODO: прогнать biz_failures/psychology/wealth_viz.

## Где мы сейчас (works)
Runtime-конвейер **работает end-to-end** (Фаза 1). `autopilot_factory/engine.py` из темы делает ролик:
scriptwriter(flash35) → compliance(pro) → visual_director(pro) → **image_agent.py `img`=Nano Banana 2** →
**audio_agent.py Gemini TTS** → **assembly.py hyperframes+ffmpeg** → QA(gemini-2.5-flash, **advisory, не блокирует**).
Первый ролик: `runs/2026-07-01_the-ceo-who-refused-to-buy-netflix-for-5/out.mp4` (63с, A/V-синк, ~$0.54).
3 канала сконфигурированы: `channels/{biz_failures,psychology,wealth_viz}/` (studio_context + media_plan + айдентика).

Запуск: `python3 autopilot_factory/engine.py --channel biz_failures --topic "..." --rubric "..." --go`

### 🧪 Эксперимент: навык Claude Code `video-factory` (2026-07-03)
`.claude/skills/video-factory/` — тот же ролик, но текстовые стадии (сценарий/комплаенс/план кадров/QA)
пишет **сам Claude (Opus)**, а не Gemini flash35/pro; в Gemini уходит только то, что Claude не умеет —
кадры (Nano Banana 2) и озвучка (Gemini TTS), сборка локальная (hyperframes+ffmpeg). Claude готовит
`script.json`/`compliance.json`/`frame_plan.json`, валидирует `scripts/validate_run.py`, затем запускает
`scripts/build_media.py <run_dir> --channel <ch>` (стадии 4–6). Переиспользует `engine.synth_audio`/
`engine.assemble` и `image_agent`; ключ Gemini — из `.env`. Улучшение против engine: hybrid-референсы
кадров (якорь+предыдущий вместо `[-14:]`, R29) + GRADE/LIGHT/LENS в начале промпта + негатив-блок.
Плюсы: 4 текстовых вызова Gemini убраны из цены, качество текста выше. Не публикует, только `out.mp4`.
Гейт: `build_media` тратит деньги — запускать после «go» владельца по сценарию.

### ⚠️ Грабли окружения: Node.js версия
`hyperframes render` (стадия 6) требует **Node 20+** (`util.styleText`) — системный дефолт `nvm`
на этой машине был **v18.17.0**, из-за чего рендер падал в конце прогона (после того как сценарий/
кадры/озвучка уже оплачены) с `SyntaxError`. **⚠️ 2026-07-03 (video-factory): `nvm alias default`
из прошлой сессии НЕ подхватился — `build_media.py` снова стартовал под v18.17.0 и упал на рендере.**
Надёжный обходной путь на прогон: `export PATH="$HOME/.nvm/versions/node/v22.22.3/bin:$PATH"` перед
`build_media.py`. Если рендер падает с `SyntaxError...styleText` — первым делом `node -v`.

### 🛠️ Фикс `image_agent.py`: ретрай на пустой `candidates` (2026-07-03, video-factory)
Nano Banana 2 иногда отдаёт ответ с `candidates=None` (транзиент) → `generate_image` падал на
`resp.candidates[0]` и **обрывал всю пакетную сборку на одном кадре** (уже после части оплаченных
вызовов). Добавлен цикл на **3 попытки** с backoff 2s/4s; при финальном провале — внятная ошибка с
`prompt_feedback`. Затрагивает всех потребителей `generate_image` (engine + skill).

### ✅ video-factory: первые 2 ролика biz_failures (2026-07-03)
`runs/2026-07-03_fedex-saved-by-5000-in-vegas/out.mp4` (39.5с, $1.23 — включает оплату упавшей
первой попытки до фикса ретрая) и `runs/2026-07-03_xerox-gave-away-the-pc-to-jobs/out.mp4` (44.6с,
$0.69, чистый прогон). Оба 9:16, AAC-дорожка; комплаенс: Джобс силуэтом со спины без лица, бренды не
воспроизведены. TTS в `cost.json` = $0.0 (Gemini TTS не трекается по токенам — проверить учёт).

## Аудит пайплайна 2026-07-01 (R22-R32)

Свежий взгляд на весь пайплайн через 10 параллельных ресёрчей (4 `deep-research` + 6 `flash35`/`pro`+search)
по каждому узлу конвейера + сравнение с индустрией/n8n. Сводка с конкретными рецептами (ffmpeg-команды,
промпт-шаблоны, код-скелеты) → [orchestration/research/32_pipeline_audit_summary.md](orchestration/research/32_pipeline_audit_summary.md).
Полные отчёты — `orchestration/research/22-31_*.md`. Ниже — обновлённый бэклог: те же пункты, что и
раньше, но с конкретными рецептами вместо «подобрать», плюс новые находки (retry/resume, QA-гейт, баг
референсов).

### P0 — Аудио и корректность
1. ✅ **[DONE 2026-07-03] TTS темп**: убраны из style-промпта `tired`/`measured pace`/`calm` (модель
   Gemini TTS воспринимала их буквально — это и было причиной аномально медленной речи, не сам голос
   Charon). `orchestration/audio_agent.py`: промпт теперь явно просит `fast, energetic pace, no long
   pauses`; добавлен параметр `speed` — гибридный постпроцесс `ffmpeg atempo` поверх WAV (не меняет тембр,
   в отличие от растяжения видео). `engine.py CHANNEL_VOICE`: `biz_failures`/Charon `speed=1.25`
   (мужской голос жаловались сильнее — «как накуренный»), `psychology`/Kore и `wealth_viz`/Orus
   `speed=1.15`. Эффект на реальных прогонах: 63с→30с, 78с→36с, 87с→54с (основной вклад — убранные
   слова, atempo сверху). Услышано и подтверждено владельцем на 2 из 3 роликов.
   **Открыто:** `speed` не в media_plan/studio_context, а хардкод в `engine.py` — если понадобится
   тонкая настройка per-канал без правки кода, вынести в `studio_context.md`.
2. **Добавить роль «саунд-дизайнер»** (`orchestration/roles/sound_designer.md`): брифы под музыку/атмосферу
   каждого канала (жанр, темп, настроение, референсы), выбор трека под конкретный ролик. Создание
   библиотеки звуков и музыки для последующего переиспользования (запускается один раз для канала —
   наработка аудио-библиотеки под канал и гайдлайнов их использования). Промпт-паттерны Lyria по жанру
   канала — R27 §3.
3. **Сгенерировать по 5 фоновых треков на канал.** Инструмент: новый `orchestration/music_agent.py` на
   **Lyria** (`lyria-3-pro-preview` / `lyria-3-clip-preview`), по образцу image_agent/audio_agent. Не
   генерировать SFX на лету (задержка 5-15с, нестабильно) — собрать один локальный пак ~15 WAV
   (whoosh/click/impact) вместо этого. Складывать в `channels/<niche>/music/track_{1..5}.wav` +
   `music/manifest.json` (mood/bpm/описание).
4. **Sidechain-ducking — готовая ffmpeg-команда** (не подбирать с нуля):
   `[1:a]volume=0.12[bg_pre];[bg_pre][0:a]sidechaincompress=threshold=0.03:ratio=5:attack=15:release=350:makeup=1:knee=2.8[bg_ducked];[0:a][bg_ducked]amix=inputs=2:duration=first:weights=1 1[mixed];[mixed]alimiter=limit=0.89:level=1[aout]`
   + финальный `loudnorm=I=-14:TP=-1:LRA=11` на мастер-микс. Целевые LUFS: voice -15..-16, BGM под
   голосом -26..-30, BGM соло -18..-22. Рецепт — R27.
5. **Баг референсов Nano Banana**: `engine.py generate_frames` шлёт `paths[-14:]` как refs, но
   официальный лимит style-референсов API — **3 изображения** — это не консистентность, а style
   drift/шум. Заменить на fixed-anchor (`paths[0]` + последние 1-2). Переместить GRADE/LIGHT/LENS в
   начало промпта. Рецепт — R29.
6. **CTA-кадр «статика 3.4с»** — не переделывать пейсинг, а добавить CSS progress-bar/pulsing слой на
   CTA (гарантирует движение пикселей на каждом фрейме). Рецепт — R23.

### P1 — Надёжность и качество (новое: R31/R24 нашли структурный гэп, не только «доделать»)
7. **Retry/resume в `engine.py`**: сейчас падение на любой стадии (например, 10-й из 12 TTS-вызовов)
   теряет весь прогон и уже оплаченные шаги. Атомарная запись (`.tmp` + `os.replace`) + пропуск стадий
   с готовым артефактом + `tenacity`-retry на все внешние вызовы. Код-скелет — R31.
8. **QA: technical-флаги сделать блокирующими** (safe-zone/LUFS/статика — считать кодом, не LLM) с
   targeted retry только стадии сборки; creative-оценку (хук) оставить advisory. Сейчас весь QA
   только советует — R24 предлагает конкретное разделение.
9. ✅ **[DONE 2026-07-03] Караоке-субтитры по словам** — было по биту (всё предложение разом),
   стало: `hyperframes transcribe` (whisper) на per-beat WAV → пословные тайминги → чанки по
   2–3 слова (`CaptionStyle.words_on_screen`) с караоке-подсветкой (`CaptionStyle.karaoke`).
   Швы на стыках per-beat WAV закрыты обрезкой краевой тишины (`_trim_silence`) до транскрипции/склейки.
   Детали и код — `autopilot_factory/engine.py` (`_trim_silence`, `_transcribe_words`), `assembly.py`
   (`_chunk_words`, `_caption_clips`); свод подхода — `orchestration/research/28_wordlevel_captions.md`.
   Проверено рендером на реальных битах (`runs/2026-07-03_kodak-...`).
10. Паттерн-интерапты на статичных AI-кадрах (Ken Burns один зум уже недостаточен в 2026): SVG
    feTurbulence на длинных планах + CSS-glitch на сменах блоков каждые 4-5с — R23.
11. **[НАЙДЕНО 2026-07-03] Баг: scriptwriter иногда обрывает CTA на полуслове.** На 2 из 2 прогонов
    `biz_failures` (temperature=1.0) поле `cta` и voiceover последнего бита обрывались буквально
    посреди фразы (`"...reality check on how"`, `"...so they don't end up in..."`) — не truncation
    по токен-лимиту (JSON валиден), просто плохой генеративный исход модели на высокой температуре.
    На слух ощущается как «вырезанный кусок видео». Временный фикс (вручную) — на runs Kodak/Netflix.
    **Нужно системно:** добавить в QA-роль (`autopilot_factory/prompts/qa.md`) явный чек
    «CTA/последний бит заканчивается законченным предложением, без обрыва/многоточия» — дешёвая
    проверка, ловит именно этот паттерн.
12. **[2026-07-03] Визуальная ревизия психологии (R41) внедрена, но эффект частичный.**
    `channels/psychology/studio_context.md` обновлён 5 категориями кадров + правилом чередования
    (не больше 2 одной категории подряд) — см. `orchestration/research/41_psychology_visual_revision.md`.
    На тестовом прогоне (`runs/2026-07-03_the-spotlight-effect.../frame_plan_v2.json`) `visual_director`
    (pro) подхватил категории лишь частично (в основном всё ещё «glowing neon X floating in void»,
    только 1-2 кадра из 18 явно из новых категорий Anchor/Logic) — модель трактует правило как
    рекомендацию, не как жёсткое ограничение. **Следующий шаг, если разнообразия всё ещё мало:**
    не полагаться на то, что pro сам чередует — явно передавать категорию по индексу кадра в промпте
    (`frames[i].category = cycle(["Anchor","Object","Environment","Logic","Emotion"])`), т.е. усилить
    контракт `FramePlan`/`visual_director.md`, а не только `studio_context.md`.

### P2 — Масштаб и деньги (нужно разрешение владельца)
11. `batch_runner.py` — простой for-цикл с try/except на ролик, БЕЗ task queue (R31: для нашего
    масштаба 5-50 роликов очередь избыточна, файловый state-machine достаточен).
12. Стадия 9 — публикация: **YouTube готова** — `autopilot_factory/publishers/youtube.py`
    (портировано 2026-07-10 из `../creative production scheme`, см. ARCHITECTURE.md §7),
    поддерживает отложенную публикацию (`--publish-at`). Остаётся: TikTok/Reels — при разрешении,
    Unified API (Zernio/PostEverywhere) вместо нативных SDK, экономит на TikTok app review;
    раздельные метаданные под платформу. **Вне текущих полномочий** (см. PLAYBOOK §1). Архитектура — R30.
13. Стадия 9 — аналитика: YouTube Analytics API (точный retention) + сторонний скрейпер для TikTok
    (официальный Research API закрыт для коммерции) → метрики как контекст для сценариста.
14. Монетизация — по триггеру (PLAYBOOK §6), когда каналы наберут тягу.

### Дозаполнение бэклога — сверка R22-R31 vs аудит-сводка (2026-07-01)
Есть отдельный проект-аналог с идентичным сводом ресёрчей (`.../creative production scheme/orchestration/research/research 2/` — побайтово совпадает с нашей `orchestration/research/`). При сверке сводки R32 против списка выше нашлись 4 пункта, которые были в синтезе, но не попали в актуальный бэклог:

15. **Кэш API-вызовов по хэшу.** Перед вызовом Nano Banana 2 / TTS считать `SHA-256(prompt + seed + settings)`
    и проверять `cache/<hash>.{png,wav}` — при повторном прогоне (например, QA забраковал 1 кадр из 12 и
    перегенерация меняет только его промпт) остальные артефакты берутся из кэша, а не оплачиваются заново.
    Хранить рядом с атомарной записью из P1.7. Рецепт — R22 §«Внедрение кэша и идемпотентности», R31 §3.
16. **QA технических флагов — по реальному рендеру, не по JSON-плану.** Вместо оценки плана кадров LLM-судьёй,
    прогонять `npx hyperframes render --format png-sequence`, брать 3 репрезентативных PNG и проверять на них
    отступы safe-zone (top/bottom) и читаемость текста мультимодальным Gemini-2.5-Flash. Уточняет P1.8 —
    R24 §«Рекомендации для нашего пайплайна».
17. **Актуализировать `cost_tracker.PRICES`.** Nano Banana 2 тарифицируется per-image (~$0.055/кадр, R22), не
    per-token — текущие ставки в `cost_tracker.py` для deep-research/interactions и картинок — грубые
    placeholder'ы. Свести в отдельный расчёт. (Было в сводке аудита как P1.12, выпало при переносе в этот
    список.)
18. **HITL-чекпоинт на этапе одобрения сценария** (JSON-скелет до генерации кадров/TTS) — наивысший ROI по
    R22: отсекает логический брак до траты денег на медиа. Технически — Telegram/Slack-кнопка + вебхук,
    без n8n. (Было в сводке аудита как P2.16, выпало при переносе; относится к той же категории, что и
    P2.12/13 — нужно решение владельца по объёму полномочий на автопостинг/апрув-флоу.)

## Волна ресёрча «направления и локальные пайплайны» 2026-07-02 (R33-R40)

По запросу владельца проведён ресёрч новых направлений и локальных пайплайнов. Сводка —
[orchestration/research/40_directions_summary.md](orchestration/research/40_directions_summary.md).
Итоговый портфель-рекомендация: собаки→Dog Psychology (жене), Сергею→Longevity или
фитнес-наука, владельцу→канал продукта-валидатора (синергия с biz_failures); СДВГ в лоб и
детское здоровье — исключены; ИИ для дизайнеров — в резерв.

Новые артефакты:
- Хендоффы локальных пайплайнов (передать команде, разворачивают через Codex):
  `orchestration/handoff/DEPLOY_NADYA_M3AIR.md` (M3 Air 16GB), `orchestration/handoff/DEPLOY_SERGEY_M4PRO.md` (M4 Pro 48GB).
- Универсальный плейбук каналов: `orchestration/research/38_universal_channel_strategy.md`
  (VvS-метрика, правило 30 роликов, kill/pivot/scale, этапы 0-12 мес).
- Аудит проекта-аналога `creative production scheme`: `orchestration/research/39_creative_scheme_audit.md`.

Новые пункты бэклога из волны:
19. **Переиспользуемый квиз-движок** (P1): один движок под все воронки (БАДы, собаки,
    longevity, валидатор) вместо одноразовых no-code сайтов — квиз-паттерн применим к 4 из
    5 направлений (R33/R34/R36).
20. **Забрать наработки из `creative production scheme`** (P1): cost_tracker (пер-вызов
    JSONL, USD), HTML/GSAP-генератор рендера, `publishers/youtube.py` (OAuth, --publish-at),
    ThumbnailPlan/CreativeQA-контракты, ffmpeg-рецепты; для 16GB-машины — OOM-ретрай-протокол (R39).
21. **A/B хуков в engine.py** (P1, из R38): 3 варианта первых 3 секунд на сценарий → 3 сборки.
22. **Две длины из одного сценария** (P2, из R38): ~40с (YT Shorts) и ~65с (TikTok CRP) +
    анти-дедупликация ffmpeg при кросспостинге (шум, сдвиг аудио 50мс, метаданные).
23. **Чекбокс Altered/Synthetic при публикации** (обязательное правило всех каналов, R34/R36) +
    вычистка MMO-лексики из скриптов канала валидатора (banned-words checker).

### Открытые вопросы владельцу (найдены аудитом, не решаются технически)
- **Целевая длина ролика**: наш таргет 30-50с vs TikTok Creator Rewards Program требует >60с для
  монетизации. Первый ролик (63с) случайно попал в «правильный для TikTok» диапазон — то есть вопрос
  не «починить длину», а решить, какая платформа первична (R25, детали — аудит §Часть 3).
- **Порядок пилотных ниш**: R25 (юнит-экономика) ранжирует иначе, чем R05 — психология/биасы дают
  более быструю тягу при коротком формате; «факапы бизнеса» экономически лучше на 60+с. R05 не
  отменяется, но приоритет пилота стоит пересмотреть с учётом экономики (аудит §Часть 3).

## Новая рубрика biz_failures: Old Money Sins (2026-07-03, R42)

По запросу владельца — расширение канала за пределы затёртых историй XIX-XXI века (Blockbuster/Kodak/
Enron видели на десятках других каналов). Добавлена рубрика **Old Money Sins**: торговля/банки/схемы
допромышленной эпохи (Месопотамия → Ганза → Ост-Индские компании) с обязательной параллелью
«история повторяется» к современной бизнес-практике в CTA/твисте — это и есть крючок, не сам факт
древности. 20 сюжетов с источниками — `orchestration/research/42_ancient_business_history_topics.md`;
внедрено в `channels/biz_failures/studio_context.md` (рубрика + 3 хук-формулы `Ancient → Modern`) и
`media_plan.md` (очередь #16-35).

**Комплаенс для рубрики (важно для scriptwriter/compliance):** чем древнее история, тем выше риск
уверенно присочинённой детали. Правило зафиксировано в `studio_context.md` §7: точные суммы только
если источник их даёт (иначе `by some estimates`), спорные/полулегендарные истории (например, кожаные
деньги Карфагена — источники расходятся) помечать как `according to some accounts`, даты — `circa`/век
без подтверждённой точности. Ещё не проверено сборкой полного ролика по этой рубрике — стоит собрать
пилот (кандидат: Ea-nasir — уже вирусный интернет-мем, хорошо узнаваем) прежде чем ставить в батч.

## Карта (что где)
- Оркестрация/тулы: `orchestration/` — `gemini_agent.py`, `image_agent.py`, `audio_agent.py`, роли `roles/*`, ресёрч `research/*`.
- Конвейер: `autopilot_factory/` — `engine.py`, `assembly.py`, `schemas.py`, `cost_tracker.py`, `prompts/*`, `channels/<niche>/*`, `runs/*`.
- Правила: `CLAUDE.md` (операционка), `PLAYBOOK.md` (стратегия/роль), `ARCHITECTURE.md` (тех), `RESEARCH_PLAN.md`.

## Ключевые решения (не менять без владельца)
- Изображения — **всегда Nano Banana 2** (`img`); ⛔ MCP `nano-banana` запрещён (deny в `.claude/settings.json`).
- Озвучка — **Gemini TTS**. QA — **advisory, не блокирует** (gemini-2.5-flash).
- Монетизация отложена: сначала трафик. Гео EN/global. Полномочия сейчас: ресёрч+архитектура+продакшен, без публикации.
