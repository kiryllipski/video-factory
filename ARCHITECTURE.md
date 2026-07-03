# ARCHITECTURE — техническая реализация фабрики

> Как устроен runtime-конвейер, который из темы делает готовый ролик 9:16. Версия 0.1 (2026-06-30),
> уточняется по итогам R08 (hyperframes), R17 (визуал/сборка), R09 (озвучка). Сейчас это план реализации —
> производство не запущено (Фаза 0). Принципы оркестрации — в `orchestration/GEMINI_ORCHESTRATION.md`.

## 1. Каталоги

```
orchestration/            # build-time: раннеры, роли, ресёрч (есть)
  gemini_agent.py         # текстовые саб-агенты (есть)
  image_agent.py          # генерация кадров, замена MCP nano-banana (есть)
  roles/*.md              # системные промпты build-time (есть)
  research/*.md           # сохранённые своды-принципы (есть)
autopilot_factory/        # runtime-конвейер (СТРОИМ)
  engine.py               # оркестратор одного ролика (стадии ниже)
  cost_tracker.py         # учёт токенов по шагам (раннеры уже умеют писать в него)
  prompts/*.md            # runtime-роли: scriptwriter, compliance, visual, qa...
  schemas.py              # Pydantic-контракты между стадиями
  channels/               # по каналу: studio_context.md + brand.json + media_plan.md
    biz_failures/ psychology/ wealth_viz/
  runs/<date>_<slug>/     # артефакты ролика: script.json, frames/, audio/, captions, out.mp4, cost.json
```
Источник правды для каждого ролика — папка `runs/<...>`: всё воспроизводимо и логируемо.

## 2. Контракты данных (Pydantic, `schemas.py`)

Стадии общаются строго через JSON-схемы (`run_structured`), не свободным текстом:
- **Script** — `hook` (≤3с), `beats[]` (каждый: `voiceover`, `on_screen_text`, `visual_cue`, `dur_s`),
  `cta`, `total_dur_s`, `lang`. Лимиты длины зашиты в схему (retention).
- **ComplianceVerdict** — `pass: bool`, `fixes[]`, `cleaned_script`.
- **FramePlan** — `frames[]` (каждый: `prompt`, `aspect="9:16"`, `ref_ids[]`, `motion` {ken_burns|zoom|parallax},
  `start_s`, `dur_s`), `grade`/`light`/`lens` (общие на ролик — для консистентности).
- **BuildManifest** — порядок кадров, тайминги, аудиодорожки, стиль субтитров → вход сборщику.
- **QAReport** — `pass: bool`, чек-лист (hook-match, статика >3с, плашки, safe-зоны), `notes[]`.

## 3. Стадии конвейера (`engine.py`)

```
тема (из channels/<niche>/media_plan.md)
 1. scriptwriter   flash35 temp~1.0  → Script(JSON)
 2. compliance     pro temp~0.2      → ComplianceVerdict (стоп-слова/claims/дисклеймеры по нише)
 3. visual_director pro              → FramePlan(JSON) (единый грейд/свет/линза на ролик)
 4. images         image_agent.py    → frames/*.png (ВСЕГДА img = Nano Banana 2; refs для консистентности)
 5. audio          TTS + музыка/SFX  → audio/voice.wav (+bgm) — провайдер по R09 (EN)
 6. assembly       hyperframes/ffmpeg→ out.mp4 (Ken Burns, субтитры-караоке в safe-зоне, плашки)
 7. qa             pro               → QAReport; fail → возврат на стадию-виновника
 8. (Фаза 2+) distribution/analytics — вне ядра рендера
```
Каждая стадия пишет артефакт в `runs/<...>` и стоимость в `cost.json`. Падение на стадии N не теряет 1..N-1.

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
