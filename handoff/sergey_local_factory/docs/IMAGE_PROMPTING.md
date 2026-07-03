# IMAGE_PROMPTING.md — промпты для локальной генерации кадров 9:16

> Гайд для роли `visual_director` (стадия 3) и оператора ComfyUI (стадия 4). Модель ещё не
> зафиксирована — здесь кандидаты и матрица выбора. Ключевое правило: **структура промпта
> зависит от энкодера** (T5 vs CLIP), смешивать подходы нельзя. Источник: ресёрч R41 (2026-07).

## 1. Структура промпта (T5 vs CLIP)

- **T5-модели (FLUX, Qwen-Image, Z-Image Turbo)** — понимают естественный язык, синтаксис,
  предлоги. **Игнорируют** весовые скобки `(word:1.5)` и «тег-салат».
  Шаблон: `[Формат кадра] + [Субъект и действие] + [Окружение/детали] + [Освещение] + [Стиль/камера]`.
  Пример: *"A cinematic vertical portrait of a cybernetic owl on a neon sign reading 'NIGHT'.
  Rainy cyberpunk street background, volumetric blue lighting, shot on 35mm lens, photorealistic."*
- **CLIP-модели (SDXL)** — ассоциации, теги через запятую, чувствительны к весам и порядку.
  Шаблон: `[Качество/стиль], [Субъект], [Детали], [Фон], [Освещение], [Камера]`.
  Пример: *"masterpiece, best quality, vertical framing, 1 cybernetic owl, neon sign, text 'NIGHT',
  (rainy cyberpunk street:1.2), volumetric blue lighting, 35mm lens, 8k."*

## 2. Параметры генерации (ComfyUI на M4 Pro)

Для M4 Pro 48GB тяжёлые модели (FLUX-dev, Qwen) — только в GGUF (Q8_0/Q5_K_M), иначе сброс на CPU.

| Модель | Steps | CFG/Guidance | Sampler | Scheduler | Особенности на M4 |
|---|---|---|---|---|---|
| FLUX.1-schnell | 4 | 1.0 | euler | simple/normal | Дистиллят, ~15с/кадр, самая быстрая |
| FLUX.1-dev | 20-25 | 3.0-3.5 | euler | simple | Баланс, GGUF обязателен, ~50с |
| Qwen-Image | 20-28 | 3.0-4.0 | euler | normal | Топ по тексту/реализму, 20B, только GGUF |
| Z-Image Turbo | 6-8 | 1.5-2.0 | euler | normal | 6B, FP16 без квантования, очень быстрая |
| SDXL | 25-30 | 6.0-7.0 | dpmpp_2m | karras | База устарела, но лучший ControlNet |

## 3. Формат 9:16 и safe-зоны

- Нативные разрешения: FLUX/Qwen/Z-Image — **896×1152** (~3:4, потом кроп/апскейл) или **832×1408**
  (ближе к 9:16); SDXL — **832×1216**. Если модель режет головы на 832×1408 — генерируй 1024×1024 и
  получай 9:16 центрированным CSS/ffmpeg-кропом.
- Safe-зоны задаём **композицией через промпт, не словами про UI**:
  - низ (под субтитры): `"...with empty dark space at the bottom foreground"`;
  - верх и правый край (кнопки платформ): `"...expansive clear sky at the top, uncluttered background on the right side"`.
- ⛔ Не писать `UI, buttons, text layout` — модель нарисует фейковый интерфейс на картинке.

## 4. Консистентность между кадрами (без AI-видео)

- **Якорная фраза стиля**: каждый промпт ролика начинай одной и той же строкой
  (напр. *"A dark fantasy polaroid photo, muted colors, film grain..."*) — для T5 работает лучше всего.
- **Seed**: один seed для статичных сцен (меняешь только действие субъекта), разный seed при смене локации.
- **Лица/персонаж на FLUX (Mac)**: IP-Adapter от XLabs на MPS нестабилен и ограничивает выбор
  сэмплеров. Надёжнее узел **`ComfyUI-PuLID-Flux`** — локально, бесплатно, высокая точность ID
  без обучения LoRA. Для SDXL — `IPAdapter FaceID PlusV2` (нужен InsightFace).
- **Style LoRA**: на 48GB грузится без потери скорости; **вес фиксировать 0.7-0.8** — выше даёт
  искажения цвета/геометрии. Лёгкая style-LoRA (50-100 MB) под канал — основной способ держать стиль.
- **ControlNet для T5** на Mac ещё багует (MPS) — для жёсткой фиксации позы пока SDXL.

## 5. Negative prompt — где нужен, где ломает

- **SDXL**: обязателен. Типовой: `ugly, deformed, text, watermark, low quality, cropped`.
- **FLUX / Qwen / Z-Image**: **оставлять ПУСТЫМ**. T5-модели архитектурно не поддерживают negative;
  запрет типа `no hands` даёт эффект «розового слона» — модель акцентирует запрещённое.
  Метод для T5 — **Inclusion-Based Steering** (описывать желаемое позитивно): вместо `no text, no
  extra fingers` → `clean image without text, hands hidden out of frame, uncluttered background`.
  LLM-агенту запретить генерировать negative для этих моделей.

## 6. Типовые провалы и фиксы

- «Пластиковая» кожа (Qwen/FLUX): CFG −0.5 + `"weathered skin, visible pores, micro-details, raw unedited photo"`.
- Кадр тесный, непригоден для CSS-зума: `"Extreme wide shot, full body visible, massive headroom, sprawling environment"`.
- Нет параллакса/глубины для зума (плоский кадр — планы не разделяются при увеличении): добавить
  оптические токены глубины `"shallow depth of field, foreground blur framing the subject, sharp
  focus on midground, extreme bokeh background"` — даёт слои под Ken Burns/параллакс.
- Кривой текст на вывесках: бери Qwen или Z-Image (лучше в типографике), текст в кавычках: `sign reading "TEXT"`.
- Ломается 9:16: генерируй 1024×1024 → кроп в ffmpeg.

## 7. От бита сценария к промпту (мини-алгоритм)

1. Извлечь из бита Субъект + Локацию, убрать метафоры.
2. Добавить якорный стиль канала.
3. Добавить композиционные фразы под зум/safe-зоны.

Пример. Бит: «Стоики считали разум крепостью. Философ в бурю».
- T5 (FLUX/Z-Image): *"A cinematic vertical shot of an ancient Greek philosopher standing calm in a
  fierce rainstorm. Lightning in the dark sky at the top. Philosopher centered in the middle third.
  Empty wet stone floor at the bottom. Somber mood, 85mm lens, photorealistic."*
- CLIP (SDXL): *"masterpiece, best quality, 1 ancient Greek philosopher, standing calm, fierce
  rainstorm, (lightning in dark sky:1.2), centered, empty stone floor at bottom, somber, 85mm lens."*

## 8. Матрица выбора модели (M4 Pro 48GB)

| Тип контента | Модель | Почему |
|---|---|---|
| Быстрые тесты, абстракция, faceless-блоги | **Z-Image Turbo** | Баланс, без GGUF, ~10-15с, понимает сложные сцены |
| Кадры с инфографикой/текстом (в т.ч. кириллица) | **Qwen-Image** | Топ по рендеру текста и adherence; GGUF |
| Сложный фотореализм, кино-стиль | **FLUX.1-dev** | Стандарт, огромная база LoRA; ~50с (GGUF). ⚠️ лицензия non-commercial |
| Жёсткая фиксация позы (ControlNet) | **SDXL** | Экосистема ControlNet (на Mac ещё с багами MPS) |

**Старт тестов:** Z-Image Turbo (лучшая скорость/качество на Mac без плясок) или FLUX.1-schnell
(GGUF, Apache-лицензия — коммерчески чисто). FLUX.1-dev для монетизации — по лицензии рискованно.

## Action items для реализации

- **ComfyUI на Mac** запускать с `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 --force-fp16 --highvram` —
  это лечит «Device: cpu» и ускоряет FLUX в 3-4 раза. Модели FLUX/Qwen грузить через ноду GGUF-Org.
  Опц. узел `MPS-Accelerate` даёт ещё ~2.2× инференса на Apple Silicon.
- **Консистентность лиц**: поставить `ComfyUI-PuLID-Flux` (для FLUX) / `IPAdapter FaceID PlusV2` (SDXL);
  style-LoRA держать на весе 0.7-0.8.
- **LLM-агенту (visual_director)**: не генерировать negative для FLUX/Qwen/Z-Image; не использовать
  веса `(word:1.2)` для T5; вшить в системный промпт суффикс safe-зоны `"...with empty space at the
  bottom for subtitles"`.

## Источники
- [Qwen-Image (GitHub, 2025)](https://github.com/QwenLM/Qwen-Image)
- [Z-Image Turbo (HuggingFace, 2025)](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- Supercharge ComfyUI on Mac M4 Pro 48GB (2026) — обход лимитов MPS
- Mac M4 ComfyUI benchmark (2026) — скорость FLUX на 48GB

> Расширенная версия (deep-research) — в основном проекте `orchestration/research/41_local_image_prompting.md`.
