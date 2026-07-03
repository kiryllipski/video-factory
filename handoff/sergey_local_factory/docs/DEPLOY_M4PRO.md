# DEPLOY_M4PRO.md — разворачивание стека (Mac M4 Pro, 48 GB)

> Порядок установки «с нуля». **Ставь только то, чего нет по аудиту (Задача 0)** — если у
> Сергея уже стоит ComfyUI/модели, переиспользуй. Строго локально, ключей нет. Диск: ~60-70 GB.
> ⚠️ Имена моделей/версии проверяй на момент установки — экосистема быстро меняется.

## Паттерн устройства

48 GB unified memory (~273 GB/с) — весь стек помещается в памяти одновременно. Можно писать
асинхронный оркестратор (пока LLM пишет сценарий ролика №3, ComfyUI рендерит кадры №1, TTS
озвучивает №2). Реалистичная цель — 3-5 роликов в день.

## Целевой стек

| Узел | Инструмент | Модель/настройки | RAM | Скорость |
|---|---|---|---|---|
| Сценарии/JSON | Ollama (HTTP) | `qwen2.5:32b` Q4_K_M, `keep_alive:-1`, `format:json` | ~20 GB | ~20-25 ток/с |
| Кадры 9:16 | ComfyUI | выбор из IMAGE_PROMPTING (старт: Z-Image Turbo / FLUX.1-schnell) | ~12-14 GB | 15-50 с/кадр |
| Озвучка | Chatterbox V3 (mps) | MIT, 23 языка, zero-shot клон голоса по 10с | ~5 GB | ~0.1 RTF |
| Субтитры | whisper.cpp (Metal) | `large-v3-turbo` ggml | ~3 GB | 2-3 с/ролик |
| Сборка | ffmpeg (+ hyperframes опц.) | — | ~2 GB | — |
| Музыка/SFX | ⛔ не генерировать | папка готовых лицензированных треков | — | — |

## Шаги

Предустановлено: Homebrew, Git, Python 3.10+. (Если нет — поставить: `xcode-select --install`, затем Homebrew.)

1. **База**
   - `brew install ffmpeg`
   - Если собираем HTML/CSS-анимацию через hyperframes: `brew install node@22` → `npm i -g hyperframes` (или `npx hyperframes`). Иначе Ken Burns делаем голым ffmpeg `zoompan`.

2. **LLM (Ollama)**
   - Установить Ollama (ollama.com) → `ollama pull qwen2.5:32b` (~19 GB).
   - В оркестраторе: вызовы `http://localhost:11434/api/chat` с `"format":"json"`, `"keep_alive":-1` (держать модель в памяти).

3. **STT (whisper.cpp)**
   - `git clone https://github.com/ggerganov/whisper.cpp && cd whisper.cpp && make metal`
   - `bash ./models/download-ggml-model.sh large-v3-turbo`
   - Word-level: `./main -m models/ggml-large-v3-turbo.bin --max-len 1 --output-json audio/voice.wav`

4. **TTS (Chatterbox)**
   - `git clone https://github.com/resemble-ai/chatterbox && pip install -r requirements.txt`
   - Модель (~2 GB) подтянется при первом `ChatterboxTTS.from_pretrained(device="mps")`.
   - Записать 10-сек референс голоса канала → сохранить как voice-preset. `exaggeration` — выразительность.

5. **Изображения (ComfyUI)**
   - Если ещё нет: `git clone https://github.com/comfyanonymous/ComfyUI && pip install -r requirements.txt`; поставить ComfyUI-Manager в `custom_nodes/`.
   - Скачать выбранную модель (см. `docs/IMAGE_PROMPTING.md`): например Z-Image Turbo (FP16) или `flux1-schnell`/`flux1-dev-Q8_0.gguf` в `models/unet` + нода ComfyUI-GGUF.
   - Запуск на Mac: `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 python main.py --force-fp16 --highvram` (лечит сброс на CPU, ускоряет FLUX 3-4×).
   - Консистентность: seed-стратегия и/или Style LoRA под канал (IP-Adapter на MPS для FLUX медленный — см. IMAGE_PROMPTING §4).
   - Сохрани рабочий workflow как JSON → дёргай его из оркестратора через HTTP API ComfyUI (`/prompt`).

6. **Оркестратор** — реализовать `scaffold/engine_local.py` по контрактам и ролям (см. AGENTS.md, задачи 3-5).

7. **Библиотека музыки** — положить папку `assets/bgm/*.wav` (лицензированные треки) + `manifest.json` (mood/bpm). Не генерировать.

## Smoke-тест приёмки

1. `ollama run qwen2.5:32b` — сценарий 12 реплик валидным JSON по схеме `Script`.
2. ComfyUI: 3 кадра 9:16 с одним seed/Style-LoRA — персонаж/стиль не «прыгает».
3. Chatterbox: клон голоса по 10с-сэмплу, озвучить 3 реплики; whisper.cpp — пословные таймкоды.
4. ffmpeg: кадры + WAV + субтитры → `out.mp4` 1080×1920 (h264, yuv420p, 30fps), громкость по `loudnorm I=-14`.
5. Два ролика параллельно end-to-end — без swap (Activity Monitor: memory pressure зелёный).

## Что остаётся вне локалки
- Музыка — готовая библиотека (не генерируем).
- Публикация/аналитика — отдельная фаза, по решению владельца (не в этом архиве).
