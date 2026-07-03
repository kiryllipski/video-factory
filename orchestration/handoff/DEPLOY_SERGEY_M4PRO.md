# План разворачивания локального пайплайна — Mac M4 Pro, 48 GB (Сергей)

> Хендофф-документ: передай этот файл Codex-агенту на целевой машине и попроси развернуть
> по шагам. Основа — ресёрч `orchestration/research/37_local_opensource_stack.md` (2026-07-02).
> ⚠️ Названия моделей и размеры файлов проверяй на момент установки — экосистема быстро меняется.

## Что строим

Локальная фабрика faceless-видео 9:16 (Shorts/Reels/TikTok) без затрат на API.
Конвейер повторяет стадии основного проекта (`autopilot_factory/engine.py`):

```
тема → сценарий (LLM, JSON) → кадры 9:16 (диффузия) → озвучка (TTS)
     → word-level субтитры (STT) → сборка (HTML/CSS + ffmpeg)
```

## Возможности устройства

48 GB unified memory (~273 GB/s) — **весь стек живёт в памяти одновременно**, паттерн
«асинхронная фабрика»: пока LLM пишет сценарий ролика №3, диффузия рендерит кадры №1,
TTS озвучивает №2. Реалистичная цель — 3-5 роликов в день на автопилоте.

## Целевой стек

| Узел | Инструмент | Модель | RAM | Скорость (M4 Pro) |
|---|---|---|---|---|
| Сценарии/JSON | Ollama (HTTP API) | `qwen2.5:32b` (Q4_K_M) | ~20 GB | ~20-25 ток/с |
| Изображения 9:16 | ComfyUI (+ нода ComfyUI-GGUF) | FLUX.1-dev GGUF Q8 + IP-Adapter FaceID PlusV2 (консистентность) | ~12-14 GB | 40-50 с/кадр |
| Озвучка | Python (torch, `device="mps"`) | Chatterbox Multilingual V3 (MIT; 23 языка, zero-shot клонирование голоса по 5-10 с сэмпла) | ~5 GB | ~0.1 RTF |
| Субтитры | whisper.cpp (Metal) | `large-v3-turbo` (ggml) | ~3 GB | 2-3 с на ролик |
| Сборка | ffmpeg (+ hyperframes для HTML-анимации, как в основном проекте) | — | ~2 GB | — |
| Музыка/SFX | ⛔ НЕ генерировать локально | локальная папка готовых треков | — | — |

Чем жертвуем vs облако: практически ничем, кроме сырой скорости рендера кадров.
Chatterbox в слепых тестах обходит ElevenLabs; Qwen2.5-32B закрывает сценарии целиком.

## Шаги разворачивания (для Codex)

Диск: суммарно **~60-70 GB**. Предустановлено: Homebrew, Git, Python 3.10+.

1. **База**: `brew install ffmpeg` (+ `node@22` и hyperframes, если собираем HTML-анимацию).
2. **LLM**: установить Ollama → `ollama pull qwen2.5:32b` (~19 GB).
   В оркестраторе: `"keep_alive": -1` (модель закреплена в памяти), `"format": "json"` для схем.
3. **STT**: `git clone https://github.com/ggerganov/whisper.cpp && cd whisper.cpp && make metal`
   → `bash ./models/download-ggml-model.sh large-v3-turbo`.
   Word-level таймкоды: `./main -m models/ggml-large-v3-turbo.bin --max-len 1 --output-json voice.wav`.
4. **TTS**: `git clone https://github.com/resemble-ai/chatterbox && pip install -r requirements.txt`.
   Модель (~2 GB) подтянется при первом `ChatterboxTTS.from_pretrained(device="mps")`.
   Записать 10-секундный референс голоса канала → зафиксировать как voice-preset;
   параметр `exaggeration` — выразительность под динамичные Reels.
5. **Изображения**: `git clone https://github.com/comfyanonymous/ComfyUI && pip install -r requirements.txt`;
   установить ComfyUI-Manager (в `custom_nodes/`). Скачать `flux1-dev-Q8_0.gguf` (~12 GB) в
   `models/unet` + нода `ComfyUI-GGUF`. Консистентность кадров: нода `ComfyUI_IPAdapter_plus`,
   веса InsightFace + `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` (в `models/clip_vision`) +
   `ip-adapter-faceid-plusv2` (в `models/ipadapter`). Workflow сохранять как JSON — дальше
   дёргать через HTTP API ComfyUI из оркестратора. ⚠️ Лицензия FLUX.1-dev — non-commercial
   для прямой продажи генераций; для нашего use-case (кадры внутри видео) считается
   допустимой зоной, но проверь актуальные условия BFL; полностью чистая альтернатива —
   FLUX.1-schnell (Apache 2.0) или Z-Image Turbo.
6. **Оркестратор**: python-скрипт со стадиями как в основном проекте, артефакты на диск
   (`runs/<дата>_<тема>/`), атомарная запись + пропуск готовых стадий; стадии независимых
   роликов — в параллель (asyncio/threads), память позволяет.

## Приёмочный smoke-тест
1. `ollama run qwen2.5:32b` — сценарий 12 реплик в JSON по схеме.
2. ComfyUI: 3 кадра 9:16 с одним IP-Adapter-референсом — персонаж/стиль не «прыгает».
3. Chatterbox: клонировать голос по 10-с сэмплу, озвучить 3 реплики; whisper.cpp — пословные таймкоды.
4. ffmpeg: кадры + WAV + субтитры → mp4 1080×1920 (h264, yuv420p, 30fps).
5. Два ролика параллельно end-to-end — без swap (Activity Monitor: memory pressure зелёный).

## Что остаётся на облаке (гибрид, по желанию)
- Финальный QA-судья и тонкий креатив — Gemini pro/flash по ключу проекта (копейки).
- Музыка — готовая библиотека треков (не генерировать).
