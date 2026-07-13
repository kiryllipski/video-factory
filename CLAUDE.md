# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Язык репозитория — русский (термины индустрии оставляем как принято: hook, retention,
> CPA, CTR и т.д.). Пиши документацию и роли по-русски.

## Что это за репозиторий

Это **фабрика контента** — система автоматического производства короткого вертикального
видео (Reels / Shorts / TikTok) с целью **монетизации** (бизнес, а не хобби). Конечная
цель любого решения здесь — деньги: реклама, партнёрские программы (CPA/affiliate),
монетизация YouTube или продвижение собственных продуктов.

**Модель работы:** Claude (Opus) = **менеджер-оркестратор**, Gemini-модели = **саб-агенты-исполнители**.
Claude держит цель, стратегию, архитектуру и качество; узкие задачи (сценарий, хуки, QA,
перевод, image-промпты, ресёрч) делегируются Gemini через единый раннер. Полная роль и
полномочия менеджера — в [PLAYBOOK.md](PLAYBOOK.md) §1.

## Карта документов (читай в этом порядке)

| Файл | Что внутри |
|---|---|
| [STATUS.md](STATUS.md) | **Начинай отсюда каждую сессию.** Живой борд: статус каждого направления/канала и пошаговый бэклог активных задач — рабочий документ владельца |
| [PLAYBOOK.md](PLAYBOOK.md) | Главный документ: роль/полномочия менеджера, команда агентов, пайплайн фабрики, медиапланирование, фазы разворачивания, монетизация, юнит-экономика |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Техническая реализация runtime-конвейера: каталоги, JSON-контракты, стадии `engine.py`, сборка видео |
| [BACKLOG.md](BACKLOG.md) | Состояние и следующие задачи (хендофф для нового чата): что работает, приоритетный бэклог P0–P2 |
| [RESEARCH_PLAN.md](RESEARCH_PLAN.md) | Бэклог ресёрча (build-time): что исследуем, какой моделью, куда сохраняем |
| [STRATEGY_QUESTIONNAIRE.md](STRATEGY_QUESTIONNAIRE.md) | Опросник стратегии/тактики/ограничений с вариантами ответов — заполняет владелец |
| [orchestration/GEMINI_ORCHESTRATION.md](orchestration/GEMINI_ORCHESTRATION.md) | Как устроено делегирование Gemini: реестр моделей, выбор по сложности, раннер |
| [orchestration/CHANNEL_LAUNCH_CHECKLIST.md](orchestration/CHANNEL_LAUNCH_CHECKLIST.md) | Чек-лист настройки YouTube-канала перед запуском: оформление, верификация, API-поля, монетизация — читать перед запуском любого нового канала |
| `orchestration/research/*.md` | Сохранённые своды принципов (build-time), переиспользуются как контекст |
| `orchestration/roles/*.md` | Системные промпты саб-агентов (build-time). Runtime-роли → `autopilot_factory/prompts/` |

## Команды

### Запуск Gemini-саб-агента (основной инструмент делегирования)
```bash
python3 orchestration/gemini_agent.py \
  --model <lite|flash|flash35|pro|ID> \
  --system <текст | путь к роли .md> \
  --task   <текст | путь к файлу> \
  [--search]   # grounding через Google Search (для ресёрча)
  [--json]     # response_mime_type=application/json
  [--temp 0.4] \
  [--out orchestration/research/output.md]   # без --out → stdout

python3 orchestration/gemini_agent.py --list-models   # реестр алиасов
```
Как библиотека (из пайплайна): `from gemini_agent import run_agent, run_structured`.
`run_structured(model, system, user, schema=PydanticModel)` гарантирует валидный JSON.

**Параллелизм:** для долгих независимых задач запускай раннер в фоне (один процесс на задачу,
**без** внутреннего `&`). Несколько ресёрчей (`gemini_agent.py`) идут одновременно.

**⚠️ Исключение — полная сборка ролика (`engine.py --go` / `scripts/build_media.py`):** ТОЛЬКО
последовательно, один прогон за раз, дожидаясь завершения перед следующим. Каждый прогон поднимает
headless Chrome для `hyperframes render` + параллельные вызовы генерации картинок — несколько таких
прогонов одновременно на локальной машине перегружают ресурсы (2026-07-03: 6 параллельных прогонов
подряд повесили компьютер, все процессы оборвались без сохранения). Ресёрч-раннеры (текст/поиск) это
ограничение не касается — только тяжёлая медиа-сборка (стадии 4-6: картинки/TTS/hyperframes render).

### Выбор модели (правило: начинай с самой дешёвой, поднимай тир только под рассуждение/креатив)
- `lite` / `flash` — структурный JSON, перевод, переформатирование, массовые задачи.
- `flash35` — креатив (хуки, сценарий), ресёрч с `--search`.
- `pro` — судейство/QA, регуляторика, арт-дирекшн, тонкие решения.
- `research` (deep-research) — **работает**: раннер сам ходит в Interactions API (REST,
  минуя SDK), может думать 5-15+ мин, запускай в фоне. Для «нанятого специалиста» по
  рынку/нише — `research`; быстрый/дешёвый ресёрч — `flash35`/`pro` + `--search`.
  ⚠️ Иногда возвращает отчёт без первых разделов — проверяй начало файла, недостающее
  дозаказывай `pro --search`. `antigravity` — не подключён.

### Майнинг тем/идей (проверяемые сигналы спроса вместо угадывания)
`orchestration/idea_miner.py` — пайплайн выбора тем: YouTube autocomplete (бесплатно, без ключа)
→ YouTube Data API v3 → опц. майнинг болей из комментов → опц. LLM-ранжирование в бэклог идей (Gemini).
Принцип: LLM **не выдумывает** темы, а ранжирует сигналы. Метод — `research/55`. Два способа выборки:
- `--mode full` (дефолт) — **outlier-детект** «залетевших» видео у **мелких** каналов (V/S ratio =
  views/subscribers). Ставь `--min-subs` (напр. 150), иначе 8–24-подписчиковые бренд-аккаунты дают
  раздутый VS-шум. VS-метод по природе не находит крупные каналы (у них база большая → VS<1.5).
- `--mode top` — самые просматриваемые ролики ниши (`search.list order=viewCount`) = **проверенные
  темы/форматы крупных** независимо от размера канала. Для «изучить подходы лидеров» (в т.ч. на другом
  языке — LLM переносит приём в поле `borrowed_approach` и адаптирует под язык/нишу канала).
```bash
# только семантика (бесплатно, без ключа):
python3 orchestration/idea_miner.py --mode autocomplete --seed "business failures" --lang en --depth 1
# outlier у мелких (нужен YOUTUBE_API_KEY в .env):
python3 orchestration/idea_miner.py --channel biz_failures --seed "company collapse" \
  --lang en --max-queries 5 --min-vs 3 --min-subs 150 --max-subs 500000 --comments --rank \
  --out orchestration/idea_backlog/biz_failures.json
# изучить крупных (в т.ч. англоязычных) → адаптировать к своему каналу:
python3 orchestration/idea_miner.py --channel <ch> --mode top --lang en --depth 0 \
  --seed "supplement mistakes" --max-queries 6 --published-after 2025-01-01 --min-views 100000 \
  --rank --out orchestration/idea_backlog/<ch>_market_study.json
```
⚠️ `search.list` = **100 юнитов** из дневных 10 000 (`--max-queries` лимитирует); остальные вызовы — 1 юнит.
Ключ `YOUTUBE_API_KEY` — в `.env` (проект Google Cloud `family-kitchen-480213`, там включён «YouTube
Data API v3»; ключ ограничь этим API). Только официальный API (HTML-скрейпинг YouTube запрещён ToS).

### Видео и медиа (НЕ используем AI-видео-модели — дорого)
- **Изображения / кадры:** ⛔ MCP-сервер `nano-banana` ЗАПРЕЩЁН (решение владельца). Используем
  собственный тул [orchestration/image_agent.py](orchestration/image_agent.py) на ключе проекта:
  ```bash
  python3 orchestration/image_agent.py --model <img-lite|img|img-pro> \
    --prompt "<текст|файл>" --aspect 9:16 [--ref refs/a.png ...] --out out/frame.png
  ```
  Как библиотека: `from image_agent import generate_image`. **СТАНДАРТ: всегда `img` = Nano Banana 2**
  (`gemini-3.1-flash-image`) — решение владельца; `img-lite`/`img-pro` только по согласованию.
  `--ref` (до 14) — для консистентности кадров.
  Формат всегда **9:16** через `image_config`, не текстом. Композиция — позитивным описанием, не «no text».
- **Сборка видео:** `hyperframes` (HTML→видео, установлен v0.7.21) + локальный `ffmpeg` (v8.1.1).
  Для captions/озвучки/QA смотри установленные скиллы `hyperframes-*`, `embedded-captions`.
- **Окружение:** Python 3.9 + `google-genai`, Node 22, ffmpeg 8.1.1.

## Архитектура (большая картина)

**Два типа делегирования** (детали — `GEMINI_ORCHESTRATION.md`):
- **Build-time (разово):** ресёрч принципов, «контекст студии», черновики промпт-контрактов.
  Результаты сохраняются в файлы и переиспользуются как контекст — не перегенерируются.
- **Runtime (на каждый ролик):** сценарий → хуки → image-промпты → QA → перевод. Живёт в
  `autopilot_factory/` (планируется): `engine.py` (пайплайн), `prompts/*.md` (runtime-роли),
  `studio_context.md` (бренд/safe-зоны), `cost_tracker.py` (учёт токенов; раннер пишет в него мягко).

**Принцип ролей:** одна роль = одна ответственность + узкий контракт + явный формат вывода.
Это держит качество стабильным и позволяет переиспользовать роль.

## Жёсткие ограничения продакшена (из ресёрча, соблюдать всегда)

- **Compliance БАД/wellness (PL/EU):** БАД — это еда, не лекарство. Стоп-слова (`leczy`,
  `zapobiega`, `choroba`, `ból`, `terapia`) запрещены; пользу формулировать только
  авторизованными EFSA-claim'ами; обязательная плашка «Suplement diety»; никаких «белых
  халатов». Полный свод — `orchestration/research/02_wellness_safe_claims_pl_eu.md`.
- **Retention:** хук в первые 1–3 сек; план кадра ≤2.5 сек; нет статики >3 сек;
  субтитры обязательны (работает на mute). Свод — `research/01_short_form_retention.md`.
- **Safe-зоны 9:16:** верхние ~15% и правая колонка — под UI платформ; ключевой визуал в
  верхних двух третях по центру/левее; нижняя треть — под наши субтитры. См. `research/04_*`.

## Конвенции

- Любую переиспользуемую находку/принцип сохраняй в `orchestration/research/*.md`
  **со ссылками на источники** (`[источник](URL)`) — это контекст для будущих запусков.
- Структурный вывод — через `response_schema` (Pydantic), не парсингом текста.
- Не смешивай `--search` (grounding) и жёсткий JSON-`response_schema` в одном вызове —
  это ломает структуру. Разделяй на шаг сбора фактов и шаг форматирования.
- Перед затратными прогонами сверяйся с открытыми решениями в `STRATEGY_QUESTIONNAIRE.md`.
