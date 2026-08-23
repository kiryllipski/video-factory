# ARCHITECTURE — техническая реализация фабрики

> Как устроен runtime-конвейер, который из темы делает готовый ролик 9:16. Версия 0.1 (2026-06-30).
> Принципы оркестрации — в `orchestration/GEMINI_ORCHESTRATION.md`.
>
> ⚠️ **Документ описывает контур v1–v6 (`engine.py` / `schemas.py`) и местами устарел** — фраза
> «производство не запущено» неверна с июля 2026. Актуальный продакшен-путь — **v7**:
> `engine_v7.py` · `assembly_v7.py` · `schemas_v7.py` (две оси контракта: рубрика и формат,
> слой инфографики, машинные гейты). Его краткая справка — [docs/PIPELINE_V7.md](docs/PIPELINE_V7.md),
> и именно она источник правды по текущему конвейеру.

## 1. Каталоги

```
orchestration/            # build-time: раннеры, роли, ресёрч (есть)
  gemini_agent.py         # текстовые саб-агенты (есть)
  image_agent.py          # генерация кадров, замена MCP nano-banana (есть)
  idea_miner.py           # майнер тем: autocomplete + YouTube Data API (outlier/top) + LLM-ранжирование (есть)
  idea_backlog/*.json     # результаты idea_miner: ранжированные бэклоги тем по каналам
  roles/*.md              # системные промпты build-time (есть)
  research/*.md           # сохранённые своды-принципы (есть; R54/R55 — запуск faceless + инструменты идей)
autopilot_factory/        # runtime-конвейер (СТРОИМ)
  engine.py               # оркестратор одного ролика (стадии ниже)
  cost_tracker.py         # учёт токенов по шагам (раннеры уже умеют писать в него)
  prompts/*.md            # runtime-роли: scriptwriter, compliance, visual, qa...
  schemas.py              # Pydantic-контракты между стадиями
  channels/               # по каналу: studio_context.md + brand.json + media_plan.md
    biz_failures/ psychology/ wealth_viz/ vitallogic_bad_pl/
  runs/<channel>/<date>_<slug>/  # артефакты ролика: script.json, frames/, audio/, captions, out.mp4, cost.json
  publishers/youtube.py   # автопостинг YouTube Data API v3 (есть, портировано 2026-07-10)
  tokens/<channel>.json   # OAuth-токен на канал (gitignored, не коммитится)
```
Прогоны разложены по каналам (реорганизовано 2026-07-04 — были общей кучей). Источник правды
для каждого ролика — папка `runs/<channel>/<...>`: всё воспроизводимо и логируемо.

**Хранение готовых видео (с 2026-07-07):** `runs/<channel>/<...>` остаётся рабочей копией прогона
(script/frames/audio/hf/json) локально на диске Mac. Финальный `out.mp4` дополнительно копируется
(не переносится) стадией 6 во внешнее хранилище:
`/Users/kirillipski/Library/Mobile Documents/com~apple~CloudDocs/external storage/video/0.5/<channel>/<date>_<slug>/out.mp4`
(iCloud — освобождает диск от накопления финальных роликов). Путь переопределяется переменной
окружения `VIDEO_DELIVERY_ROOT`. Копирование делает `engine.deliver()`, вызывается из
`engine.produce()` и `.claude/skills/video-factory/scripts/build_media.py`. Все ролики, собранные
до этой даты (~1.9GB, 21 прогон), перенесены (не скопированы) из `runs/` в это хранилище целиком
вместе с промежуточными артефактами — для них рабочая копия в `runs/` больше не существует.

## 2. Контракты данных (Pydantic, `schemas.py`)

Стадии общаются строго через JSON-схемы (`run_structured`), не свободным текстом.
`schemas.PIPELINE_VERSION` (сейчас **3.0**, factory_audit_2026-07-15) пишется в `run_meta.json`
(build_media) и `publish_log.jsonl` (publisher) — аналитика сравнивает версии по метрикам:
- **Script** — `hook` (≤3с, v2: симптом в первых словах), `beats[]` (каждый: `voiceover`,
  `on_screen_text`, `visual_cue`, `dur_s`), `cta`, `total_dur_s`, `lang`,
  **v2: `poster_text`** (постер-заголовок первого кадра, рендерится сборкой с t=0;
  **v3: ≤4 слов, `*акцент*` подсвечивается жёлтым**), **v3: `cta_plate`** (финальная
  плашка-вопрос ≤5 слов, стиль постера — петля «конец = начало»). v3-таргет длины 22–32с.
- **ComplianceVerdict** — `pass: bool`, `fixes[]`, `cleaned_script`.
- **FramePlan** — `frames[]` (каждый: `prompt`, `aspect="9:16"`, `ref_ids[]`, `motion` {ken_burns|zoom|parallax},
  `start_s`, `dur_s`), `grade`/`light`/`lens` (общие на ролик — для консистентности).
- **BuildManifest** — порядок кадров, тайминги, аудиодорожки, стиль субтитров → вход сборщику.
- **QAReport** — `pass: bool`, чек-лист (hook-match, статика >3с, плашки, safe-зоны), `notes[]`.
- **PublishPackage** — `title`/`description`/`hashtags`, **v2: `pinned_comment`** (вопрос-коммент
  владельца, постится после выхода в public) и **`title_template`** (метка ротации заголовков).

## 3. Стадии конвейера (`engine.py`)

```
тема (из channels/<niche>/media_plan.md)
 1. scriptwriter   flash35 temp~1.0  → Script(JSON)          [для vitallogic пишет Claude, см. ниже]
 2. compliance     pro temp~0.2      → ComplianceVerdict (стоп-слова/claims/дисклеймеры по нише)
 3. visual_director pro              → FramePlan(JSON) (единый грейд/свет/линза на ролик)
 4. images         image_agent.py    → frames/*.png (ВСЕГДА img = Nano Banana 2; refs для консистентности)
 4b. frame-QA v3   gemini-2.5-flash  → vision-чек каждого PNG (текст в кадре/рамки/анатомия/трети);
                                      fail → точечная перегенерация кадра (≤2) → frame_qa.json
 5. audio          Gemini TTS per-beat → audio/voice.wav (тайминг слов без ASR)
 6. assembly       hyperframes/ffmpeg→ out.mp4 (Ken Burns + v3: hook_punch кадра-0, постер со
                                      скримом и *акцентом*, CTA-плашка финала, BGM-подложка канала
                                      из channels/<ch>/assets/bgm/ на −21дБ под голосом)
                                     → копия out.mp4 в DELIVERY_ROOT (iCloud, см. §1)
 6b. video-QA v3   gemini-2.5-flash  → vision-чек 3 стоп-кадров out.mp4 (advisory) → video_qa.json
 7. qa             pro               → QAReport; fail → возврат на стадию-виновника
 8. metadata       Claude (текст)    → publish_package.json (PublishPackage: title/description/hashtags)
 9. publish        publishers/youtube.py → videos.insert (private/unlisted/public, опц. publishAt)
```
Каждая стадия пишет артефакт в `runs/<...>` и стоимость в `cost.json`. Падение на стадии N не теряет 1..N-1.
Стадия 9 — видимое вовне действие (публикует на реальный канал), запускается только по явному
подтверждению владельца, не автоматически по завершении сборки. Детали токенов/каналов — §7.

**Рабочий путь для vitallogic (и рекомендованный для всех):** текстовые стадии 1–3/7/8 пишет
Claude по скиллу `.claude/skills/video-factory` (Gemini-текст в engine.produce — legacy-путь
для необслуживаемых каналов); медиа-стадии 4–6b — `scripts/build_media.py`. Бэкап v2 до правок —
`autopilot_factory/_backup/pipeline_v2_2026-07-15/`; обоснование v3 —
`channels/vitallogic_bad_pl/factory_audit_2026-07-15.md`.

## 4. Сборка видео — РЕШЕНО: hyperframes (v0.7.22) как слой сборки

Кадры статичны → «премиум» создаётся движением. Проверены возможности CLI (R08) — hyperframes
покрывает весь наш конвейер нативно, поэтому он и есть слой сборки; ffmpeg живёт под ним (мукс/кодек),
руками его не пишем.

Что даёт hyperframes и куда ложится:
- `render` (HTML→MP4/WebM, детерминированный seek-safe) — **стадия 6**. WebM с альфой — для оверлеев.
- Kadr-движение (Ken Burns/зум/параллакс) — через CSS/GSAP в HTML-композиции (полный контроль, не `zoompan`).
- `transcribe` (word-level timestamps) + `embedded-captions`-скилл — **караоке-субтитры** в safe-зоне.
- `tts` (локальный Kokoro-82M, EN, бесплатно) — кандидат в **стадию 5** для англоязычных ниш (см. R09).
- `beats` — бит-синхронизация графики/склеек.
- `validate` / `lint` / `inspect` / `snapshot` — машинные проверки → кормят **стадию 7 (QA)**.
- `lambda` / `cloudrun` / `cloud` — распределённый рендер для масштаба (**Фаза 3**).
- `catalog` / `add` — переиспользуемые блоки/компоненты (лоу-тёрды, графики).

Практика: `engine.py` собирает HTML-композицию hyperframes из `FramePlan` (кадры Nano Banana 2 как
слои-картинки + CSS/GSAP-движение + караоке-субтитры из транскрипта), затем `hyperframes render` → mp4.

**v2 сборки (2026-07-13, `assembly.py`):**
- **Кадр ↔ бит:** при кадров == битов каждый кадр живёт ровно столько, сколько звучит его бит
  (по реальному TTS); раньше кадры раскладывались равномерно и уезжали от смысла озвучки на
  неравных битах. При несовпадении числа — прежний равномерный фолбэк.
- **Постер-заголовок:** `poster_text` сценария рендерится крупным текстом (92px, верхняя треть,
  ниже UI-зоны платформ) с t=0 БЕЗ входной анимации — кадр-0 является «обложкой» ролика в ленте
  Shorts; уходит fade-out'ом в конце первого бита (+⅓ второго, потолок 4с). Фолбэк для старых
  прогонов — `beats[0].on_screen_text`.
- **Node 20+ сам:** `assembly._node22_env()` подсовывает nvm-Node≥20 subprocess'ам рендера —
  сборка больше не требует Node 22 в PATH оболочки (раньше падала под системным v18).

**Скины сборки (2026-08-05, эксперимент v5-collage):** `assembly.build_and_render(..., skin=...)`
и `engine.assemble(..., skin=...)` выбирают типографический слой поверх одного и того же
таймлайна кадров:
- `skin="photo"` — продакшен: белый текст, скрим-градиент, караоке жёлтым. **Дефолт; вывод
  побайтово тот же, что до введения параметра** (регресс-тест 2026-08-05).
- `skin="collage"` — печатный коллаж: заголовок/субтитры/CTA на рваной кремовой бумаге
  (`clip-path`), караоке подсвечивается **маркером** (navy-блок + выворотка), а не цветом —
  на бумаге ink и navy читаются одинаково тёмными; поверх всего статичные растр и зерно.
  Наклон CTA-плашки задан в GSAP, не в CSS: твин пишет `transform` и затирает CSS-ный `rotate()`.
  Оверлеи не анимированы намеренно — рендер идёт перемоткой по таймлайну, и не-GSAP анимация
  была бы недетерминированной (см. §5 «Детерминизм»).
Кто чем пользуется — таблица вариантов в `.claude/skills/video-factory/SKILL.md`.

**Слоевая сборка (2026-08-05, T2 / `6.0-layers`)** — отдельный путь, не скин:
`.claude/skills/video-factory/scripts/assembly_layers.py`. Вместо одного `<img>` на бит —
плоский бумажный фон + несколько вырезок-слоёв, каждая со своим GSAP-треком (влёт/шлепок/
оседание/покачивание) плюс процедурная бумажная «мебель» (обрывки, скотч, газетные полосы),
рисуемая CSS'ом и потому бесплатная. Вырезки готовит `collage_elements.py`: «стикер-лист» из
4–6 объектов = ОДНА генерация Nano Banana 2, нарезка локальная (цветовой ключ + связные
компоненты, сведение к ячейкам сетки). Модуль аддитивный — `assembly.py` не правится,
типографика переиспользуется импортом из него.
Два правила, каждое найдено рендером и зашитое в код: альфа обнуляется вне жёсткой маски
компонента (иначе полупрозрачный прямоугольный ореол вокруг вырезки), и хотя бы один элемент
бита обязан быть виден с его первого кадра (иначе доли секунды голого фона на стыке).

## 5. Принципы реализации

- **Детерминизм:** фиксируем seed/версии, кадры и манифест — на диске; повторный рендер = тот же ролик.
- **Дёшево по умолчанию:** черновой проход на `img-lite`/`flash`, апгрейд тира только для финала/сложного.
- **Консистентность ролика:** один грейд/свет/линза во `FramePlan`; reference images между кадрами.
- **Комплаенс как гейт:** стадии 2 и 7 — обязательные; ролик без pass не уходит в сборку/паблиш.
- **Учёт экономики:** `cost_tracker` на каждом шаге → реальная цена ролика (R15, юнит-экономика).
- **Per-niche конфиг:** различия ниш живут в `channels/<niche>/` (тон, стоп-листы, визуальный код, дисклеймеры),
  ядро `engine.py` — общее.

## 6. Что нужно до первого рендера (вход в Фазу 1)

Готово (дизайн Фазы 0):
- ✅ R08+R17 → решение по §4 (hyperframes) зафиксировано.
- ✅ `schemas.py` (контракты, Pydantic 2, провалидированы) + `cost_tracker.py` (учёт по шагам).
- ✅ `prompts/` runtime-роли: scriptwriter, compliance, visual_director (JSON-выход по схемам).
- ✅ Канал #1 `channels/biz_failures/`: `studio_context.md` + `media_plan.md` (15 тем).
- ✅ Скелет `engine.py`: стадии 1–4 подключены к раннерам; 5–7 — заглушки с TODO. Проводка провалидирована.

Сделано (Фаза 1 запущена, первый ролик собран 2026-07-01):
- ✅ **R09/стадия 5** — озвучка = **Gemini TTS** (`orchestration/audio_agent.py`), per-beat для синка.
- ✅ **Стадия 6 (assembly)** — `autopilot_factory/assembly.py`: HTML+GSAP Ken Burns, субтитры в safe-зоне,
   рендер hyperframes → немой mp4, мукс озвучки ffmpeg. Дорожки кадров/субтитров независимы.
- ✅ **Стадия 7 (qa)** — судья `gemini-2.5-flash`, **advisory: только фиксирует, не блокирует**.
- ✅ Каналы #1/#2/#3 сконфигурированы (`studio_context.md` + `media_plan.md` + айдентика).
- ✅ **Первый прогон**: Blockbuster, 63с, A/V-синк, ~$0.54/ролик (cost.json).

Тюнинг (не блокирует, следующий шаг):
1. ✅ **[DONE 2026-07-03] Длина/темп**: причиной 63с при таргете 30-50с был не сценарий, а буквальное
   исполнение TTS-моделью слов `tired`/`measured pace` в style-промпте — убраны + добавлен `speed`
   (ffmpeg atempo) в `audio_agent.py`/`CHANNEL_VOICE` (`engine.py`). Детали — `BACKLOG.md` P0.1.
2. QA-нит: финальный CTA-кадр 3.4с (статика >3с) — правило пейсинга в visual_director.
3. BGM/SFX-слой; батч-производство очереди; стадия 8 (дистрибуция) — по разрешению.

Сделано (2026-07-03) — караоке-субтитры по словам:
- ✅ **Стадия 5 (`synth_audio`)**: per-beat WAV обрезается от служебной тишины TTS на стыках
  (`_trim_silence`, ffmpeg `silenceremove`, только края — паузы внутри речи не трогаем), затем
  транскрибируется через `npx hyperframes transcribe --json` (whisper) со сдвигом таймкодов на
  cumulative-время бита → пословные тайминги на всю озвучку (`_transcribe_words`).
- ✅ **Стадия 6 (`assembly.py`)**: субтитры больше не показывают целое предложение бита разом —
  текст режется на чанки по `CaptionStyle.words_on_screen` (2–3 слова, поле уже было в схеме, но не
  использовалось) с реальным началом/концом произнесения каждого чанка; внутри чанка — караоке-подсветка
  по словам (`CaptionStyle.karaoke`, GSAP-tween цвет/scale на каждый `<span class="word">`). Фолбэк на
  старое поведение (`on_screen_text` на весь бит), если whisper недоступен (`--optional` → `[]`).
  Проверено рендером двух реальных битов (`runs/2026-07-03_kodak-...`) — тайминг совпадает с речью,
  на экране одновременно 2–3 слова вместо всего предложения.

## 7. Публикация (YouTube Data API v3) — `autopilot_factory/publishers/youtube.py`

Портировано 2026-07-10 из `../creative production scheme` — это реальный механизм, которым уже
публиковался @VitalLogic-nutriFlow (см. историю экспериментов там же). Адаптирован под конвенции
этого репо: видео берётся из `<run_dir>/out.mp4` (не `final.mp4`), `categoryId` по умолчанию
`27` (Education, не мусорный `22` — см. `research/51`), `defaultLanguage` берётся по каналу
(`pl` для vitallogic_bad_pl, `en` для остальных) или флагом `--lang`.

- **Мультиканальность:** один Gmail-аккаунт может владеть несколькими YouTube-каналами (brand
  accounts) — OAuth привязывается к конкретному каналу на экране согласия. Токен хранится отдельно
  на канал: `autopilot_factory/tokens/<channel_label>.json` (gitignored). Уже авторизован
  `vitallogic_bad_pl` (реальный канал VitalLogic, 38 подписчиков на момент переноса). Для
  biz_failures/psychology/wealth_viz нужна разовая `auth` — но аккаунты этих каналов ещё не
  созданы владельцем.
- **Команды:**
  `youtube.py auth --channel <label> --client-secret client_secret.json` — разовая авторизация.
  `youtube.py whoami --channel <label>` — read-only проверка токена, без публикации.
  `youtube.py upload --channel <label> --run <run_dir> [--privacy private|unlisted|public] [--publish-at <RFC3339 UTC>] [--lang pl|en]` — заливка.
  `youtube.py retry-pending --channel <label>` — дозаливка роликов, упавших на суточном лимите канала.
  `youtube.py post-comments [--channel <label>]` — **v2:** постит владельческие комментарии-вопросы
  из `publishers/comment_queue.jsonl` под роликами, уже вышедшими в public.
- **v2 — комментарий-вопрос (`pinned_comment` в publish_package):** на private/scheduled ролик
  комментировать нельзя, поэтому `upload` ставит текст в очередь `comment_queue.jsonl`, а
  `post-comments` (запускать после каждого publishAt-слота, напр. из scheduled task) публикует его,
  когда ролик стал public. Требует scope `youtube.force-ssl` (свежие токены его имеют; старые — re-auth).
  Пиннинг через Data API невозможен — на свежем ролике владельческий коммент и так первый; закрепить
  можно вручную в Studio. В `publish_log.jsonl` пишутся `pipeline_version` (из `run_meta.json`) и
  `title_template` — по ним `orchestration/analytics_report.py` сравнивает версии/шаблоны.
- **Отложенная публикация:** `--publish-at` заливает ролик как `private`, YouTube сам делает его
  `public` в указанный момент (UTC). Так строится план публикаций на неделю вперёд одним прогоном аплоадов.
- **Защита от наложения слотов (2026-07-27):** `--publish-at auto` подбирает ближайший свободный слот
  по каденсу (`CADENCE_SLOTS_UTC`; с 2026-08-13 — 1/день, 06:00 Warsaw = 04:00 UTC) **живым запросом к каналу**
  (`_scheduled_occupied_utc` — все `private`-видео с `publishAt`), а не по локальным файлам. Даже при
  явном `--publish-at <время>` инструмент проверяет коллизию и сдвигает при необходимости. Причина:
  найдено 8+ роликов, задвоенных на одно время — минимум 2 независимых механизма (очередь-файл,
  логика «последняя строка publish_log.jsonl») подбирали слот независимо, не сверяясь с реальным
  расписанием. `publish_log.jsonl`/`upload_queue*.json` теперь только для истории/аналитики, не для
  выбора слота — не доверять им как источнику «что уже занято».
- **Раскрытие AI (обязательно):** `status.containsSyntheticMedia=true` ставится на `videos.insert`
  (дефолт вкл, `--no-synthetic` отключает) — кадры Nano Banana + голос TTS фотореалистичны/синтетичны,
  YouTube требует пометку и с мая 2026 авто-детектит нераскрытое. Правка УЖЕ загруженных (`videos.update`)
  требует scope `youtube.force-ssl` — старые токены без него, нужен повторный `auth` (или ручной тумблер
  «Altered content» в Studio).
- **Перенос в iCloud после заливки:** успешная загрузка перемещает весь прогон в
  `VIDEO_DELIVERY_ROOT/<channel>/<run>/` (`_archive_to_icloud`, дефолт вкл, `--no-archive` отключает) —
  локально загруженное не держим (договорённость 2026-07-10). Переиспользованный из iCloud прогон — no-op.
- **Мягкая проверка перед заливкой:** `publishers/prepublisher.py` (тоже портирован) — не блокирует,
  только пишет `<run_dir>/pre_publish_log.json` (размер видео, вертикальность 9:16, длительность
  Shorts-диапазона, наличие/длина title-description-hashtags). PL-специфичные wellness-проверки
  (дисклеймер, запрещённые claim-слова) включаются только при `lang=pl`.
- **Обложка:** если в `<run_dir>/thumbnail.jpg` есть файл — заливается через `thumbnails.set`;
  требует верифицированного номера телефона на канале, иначе тихо пропускается с warning в
  `post_result.json` (см. BACKLOG.md — верификация VitalLogic отложена, номера исчерпаны).
- **Не автоматизировано намеренно:** ничего не вызывает `upload` само по себе после сборки —
  публикация видима вовне (на реальном канале), поэтому всегда требует явного go от владельца.
