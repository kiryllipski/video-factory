# ARCHITECTURE_LOCAL.md — как устроен локальный конвейер

> Зеркалит проверенную облачную фабрику, но каждый узел — локальный open-source. Источник
> правды одного ролика — папка `runs/<дата>_<slug>/`: всё воспроизводимо, ничего в облако.

## Каталоги проекта

```
sergey_local_factory/
  AGENTS.md                 # инструкции Codex (Задача 0 — обязательна первой)
  README.md                 # быстрый старт для Сергея (человека)
  docs/                     # ARCHITECTURE_LOCAL, DEPLOY_M4PRO, IMAGE_PROMPTING, STRATEGY
  roles/                    # системные промпты по стадиям (для локальной LLM/оператора)
  contracts/schemas_local.py# Pydantic-контракты между стадиями
  config/
    pipeline.config.example.json  # пути, модели, параметры (без ключей)
    channel.template/       # ниша-агностичный шаблон канала
  scaffold/engine_local.py  # СКЕЛЕТ оркестратора (реализует Codex)
  runs/<дата>_<slug>/       # артефакты ролика (создаётся движком)
```

## Контракты данных (`contracts/schemas_local.py`)

Стадии общаются строго через JSON-схемы (Pydantic), не свободным текстом. Локальная LLM
(Ollama) должна отдавать структурный JSON — вызывай Ollama с `"format": "json"` и валидируй
ответ Pydantic-моделью; при невалиде — один retry с укороченным промптом.

- **Script** — `hook` (≤3с), `beats[]` (`voiceover`, `on_screen_text`, `visual_cue`, `dur_s`), `cta`, `total_dur_s`, `lang`.
- **ComplianceVerdict** — `passed`, `fixes[]`, `cleaned_script`.
- **FramePlan** — общие на ролик `grade`/`light`/`lens` + `frames[]` (`prompt`, `aspect="9:16"`,
  `seed`, `ref_ids[]`, `motion`, `start_s`, `dur_s`).
- **BuildManifest** — `frame_plan` + `audio[]` + `captions` + `disclaimer_overlay` + `fps` → вход сборщику.
- **QAReport** — `passed`, чек-лист (hook-match, статика >3с, safe-зоны, LUFS), `notes[]`.

## Стадии (`scaffold/engine_local.py`)

```
тема (из config/channel.template/media_plan.md)
 1. scriptwriter    Ollama LLM (format=json)     → Script
 2. compliance      Ollama LLM                   → ComplianceVerdict (стоп-слова/дисклеймеры ниши)
 3. visual_director Ollama LLM                   → FramePlan (единый грейд/свет/линза; промпты по docs/IMAGE_PROMPTING)
 4. images          ComfyUI HTTP API (:8188)     → frames/*.png (выбранная модель; seed/LoRA для консистентности)
 5. audio           Chatterbox (mps)             → audio/voice.wav (+ bgm из локальной библиотеки)
 6. captions        whisper.cpp --max-len 1      → captions.json (word-level таймкоды)
 7. assembly        hyperframes/ffmpeg           → out.mp4 (Ken Burns/зум, караоке-субтитры в safe-зоне)
 8. qa              Ollama LLM + машинные чеки    → QAReport (advisory; технические флаги можно сделать блокирующими)
```

Каждая стадия пишет артефакт в `runs/<...>` **атомарно** (`.tmp` + `os.replace`). Падение на
стадии N не теряет 1..N-1; перезапуск пропускает стадии с готовым артефактом. 48GB позволяют
считать несколько роликов параллельно («асинхронная фабрика»), но контракты те же.

## Стадии ↔ роли ↔ инструмент

| # | Стадия | Роль (`roles/`) | Инструмент | Ключевой документ |
|---|---|---|---|---|
| 1 | Сценарий | `01_scriptwriter.md` | Ollama qwen2.5:32b | STRATEGY (retention, длины) |
| 2 | Комплаенс | `02_compliance.md` | Ollama | STRATEGY (YMYL, маркировка AI) |
| 3 | План кадров | `03_visual_director.md` | Ollama | IMAGE_PROMPTING (T5/CLIP, safe-зоны) |
| 4 | Кадры | `04_image_operator.md` | ComfyUI | IMAGE_PROMPTING (модель, параметры) |
| 5 | Озвучка | `05_voice_tts.md` | Chatterbox V3 | DEPLOY (голос-сэмпл) |
| 6 | Субтитры | `06_captions_stt.md` | whisper.cpp | — |
| 7 | Сборка | `07_assembly.md` | hyperframes/ffmpeg | STRATEGY (динамика статики) |
| 8 | QA | `08_qa.md` | Ollama + чеки | STRATEGY (бенчмарки) |

## Принципы

- **Детерминизм**: фиксируем seed/версии; повторный рендер = тот же ролик.
- **Строго локально**: никаких платных API/ключей. Не хватает узла локально — локальная замена, не облако.
- **Консистентность ролика**: один грейд/свет/линза во FramePlan; seed-стратегия и/или Style LoRA (см. IMAGE_PROMPTING §4).
- **Комплаенс как гейт**: стадии 2 и 8 обязательны для health-ниш (YMYL); чекбокс Altered/Synthetic при публикации.
- **Per-niche конфиг**: различия ниш — в `config/channel.template/` (тон, стоп-листы, визуальный код, дисклеймеры); ядро движка общее.
