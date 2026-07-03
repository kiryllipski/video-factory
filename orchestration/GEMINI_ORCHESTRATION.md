# Оркестрация Gemini-саб-агентов

> Как устроено делегирование задач Gemini-моделям в этом проекте, какие модели
> использовать под какую сложность, и каким инструментом их вызывать.
> Дата: 2026-06-28.

---

## 1. Модель работы: Claude = оркестратор, Gemini = саб-агенты

- **Claude (Opus)** держит цель, архитектуру и качество. Он решает, какую задачу
  делегировать, какой модели, с каким системным промптом, и проверяет результат.
- **Gemini-модели** выполняют отдельные узкие задачи через единый раннер
  `orchestration/gemini_agent.py`. Они не видят весь проект — только то, что им
  передали в `--system` и `--task`.

Два типа делегирования:

| Тип | Когда | Пример |
|---|---|---|
| **Разовое (build-time)** | Один раз при сборке системы | ресёрч принципов, генерация «контекста студии», черновики промпт-контрактов |
| **Runtime (в пайплайне)** | На каждый ролик | сценарий, хуки, QA, перевод, image-промпты |

Разовые результаты сохраняются в файлы (`orchestration/research/*`,
`autopilot_factory/studio_context.md`) и дальше переиспользуются как контекст —
их не нужно перегенерировать на каждый запуск.

---

## 2. Реестр моделей и выбор по сложности

Все ID проверены через `models.list` на текущем ключе (2026-06-28).

| Алиас | Модель | Когда использовать |
|---|---|---|
| `lite` | `gemini-2.5-flash-lite` | тривиальные/массовые задачи, максимально дёшево |
| `flash` | `gemini-2.5-flash` | рабочий конь: структурный JSON, перевод, форматирование |
| `flash35` | `gemini-3.5-flash` | креативная генерация (хуки, сценарий), ресёрч с поиском |
| `pro` | `gemini-3.1-pro-preview` | высокое рассуждение: QA-судья, montage vision, регуляторика |
| TTS | `gemini-3.1-flash-tts-preview` | озвучка (голос `Aoede`, PL) |
| Image | `gemini-3.1-flash-image` | генерация кадров (Nano Banana 2), 9:16 |
| Музыка | `lyria-3-pro-preview` | генерация фоновых треков |

**Правило выбора:** начинай с самой дешёвой модели, поднимай тир только если
задача требует рассуждения или креативного качества.
- Структурный вывод по чёткой схеме, перевод, переформатирование → `flash`/`lite`.
- Генерация креатива, где важно «попадание» → `flash35`.
- Оценка, судейство, тонкие решения, регуляторные формулировки → `pro`.

### Недоступные модели (важно)

| Модель | Статус |
|---|---|
| `antigravity-preview-05-2026` | есть по ключу, но **только Interactions API** — не поддерживается SDK 1.47.0 |
| `deep-research-preview-04-2026` (и `-max`, `-pro`) | то же: **только Interactions API** — не подключены |

Поэтому **глубокий ресёрч с веб-поиском делаем через `flash35`/`pro` + `--search`**
(grounding через Google Search). Если в будущем появится поддержка Interactions API
в SDK — можно подключить deep-research отдельным каналом.

---

## 3. Инструмент: `gemini_agent.py`

Единая точка вызова. Читает `GEMINI_API_KEY` из `.env` в корне проекта.

### CLI (Claude вызывает через Bash)

```bash
python3 orchestration/gemini_agent.py \
  --model pro \
  --system orchestration/roles/researcher.md \
  --task   "текст задачи ИЛИ путь к файлу" \
  --search \              # включить grounding через Google Search
  --json \                # ответ как application/json (без жёсткой схемы)
  --temp 0.4 \
  --out    orchestration/research/output.md
```

- `--system` и `--task` принимают либо строку, либо путь к файлу (авто-определение).
- Без `--out` ответ идёт в stdout.
- `--list-models` печатает реестр алиасов.

### Как библиотека (из пайплайна)

```python
from gemini_agent import run_agent, run_structured
text = run_agent("flash35", system=SYS, user=TASK, temperature=0.7)
obj  = run_structured("pro", system=SYS, user=TASK, schema=MyPydanticModel)
```

`run_structured` использует `response_schema` (Pydantic) → гарантированный валидный JSON.

### Запуск в фоне (параллелизм)

Для долгих/независимых задач Claude запускает раннер в фоне (один процесс на задачу,
**без** внутреннего `&` — иначе процесс осиротеет). Несколько ресёрчей идут параллельно.

---

## 4. Роли (системные промпты)

Системные промпты саб-агентов лежат в `orchestration/roles/*.md` (build-time) и
`autopilot_factory/prompts/*.md` (runtime). Роль = одна ответственность, узкий контракт,
явный формат вывода. Это позволяет переиспользовать роль и держать качество стабильным.

---

## 5. Документация (источники)

- google-genai Python SDK — https://googleapis.github.io/python-genai/
- Список моделей — https://ai.google.dev/gemini-api/docs/models
- Структурированный вывод — https://ai.google.dev/gemini-api/docs/structured-output
- Grounding (Google Search) — https://ai.google.dev/gemini-api/docs/google-search
- Генерация речи (TTS) — https://ai.google.dev/gemini-api/docs/speech-generation
- Генерация изображений — https://ai.google.dev/gemini-api/docs/image-generation
- Lyria (музыка) — https://ai.google.dev/gemini-api/docs/music-generation
