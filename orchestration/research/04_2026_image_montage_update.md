# Обновление 2026: промптинг Gemini 3 Image (Nano Banana) + монтаж short-form

> Дополнение к `03_gemini3_prompting.md` и `01_short_form_retention.md`.
> Собрано из свежих гайдов (2026) и применено в промптах пайплайна.

---

## 1. Gemini 3 / Nano Banana (Pro) — что реально двигает качество

- **Структурный промпт, а не набор тегов.** Рабочая формула:
  `[Action] + [Subject] + [Pose/State] + [Setting] + [Style] + [Technical]`.
  Модель «режиссируется» предложением-сценой, а не списком слов.
- **Кинематографические констрейнты дают премиум.** Явно задавать:
  объектив/линзу («85mm macro», «35mm»), грейд («muted teal-orange», «warm charcoal grade»),
  свет («single soft key light, soft falloff»), глубину резкости. Это и есть «студийный контроль».
- **Композиция через позитив, а не отрицание.** Диффузионная часть игнорирует «no text».
  Чистоту кадра описывать утвердительно: «clean uncluttered surface, free of any writing or branding».
  Запреты — только в `negative_prompt`.
- **Соотношение сторон — через API** (`image_config.aspect_ratio="9:16"`), не текстом.
- **Консистентность внутри ролика:** один грейд / направление света / семейство фона во всех кадрах.
  Для строгой консистентности персонажа/объекта — reference images (до 14) + явная фиксация черт.
- **Итерация диалогом** дешевле рестарта: «make textures more tactile» вместо нового промпта.

**Применено:** `prompt_engineer.md` — формула-скелет промпта, обязательные lens+grade+light,
позитивное описание чистой нижней трети, негатив только в `negative_prompt`.

## 2. Safe zones вертикали 9:16 (1080×1920) — 2026

Зоны, которые перекрывает UI платформ (Shorts/Reels/TikTok), и их нельзя занимать важным:
- **Верхние ~15% (≈0–280px):** место под логотип/watermark и системный бар. НЕ ставить туда смысл.
- **Правая колонка действий (≈правые 140px):** лайк/шер/аватар. Держать субъект левее центра/центр.
- **Нижние ~250–300px:** подпись, ник, музыка, CTA платформы.

**Вывод для нас:** ключевой визуал — в **центрально-верхней зоне (верхние две трети, но ниже top-15%)**,
по центру или левее центра. **Нижняя треть свободна под наши субтитры**, правый край — без важного.

**Применено:** `studio_context.md` §7 (safe-зоны), `visual_director.md`, `prompt_engineer.md`
(`subject in the upper-central two-thirds, clean lower third, nothing critical on the right edge`).

## 3. Монтаж и удержание — уточнённые цифры 2026

- **Средняя длина плана 1.5–2.5 сек**; кадр не живёт дольше, чем «живёт идея».
- **Длина Shorts с лучшим completion: 30–50 сек** (наш диапазон 30–45 ок).
- **Субтитры обязательны:** 85% смотрят без звука; +40% к удержанию. Должно «работать на mute».
  По 2–4 (до 5) слова на экране, крупно, караоке-подсветка, в safe-зоне.
- **Нет статике >3 сек** без смены крупности/графики/нового вопроса (QC-правило).

**Применено:** `montage_vision.md` — явные числа пейсинга и QC-правило статики; субтитры —
чанками по 3–5 слов (реализовано в `engine.py`, см. §7 PRINCIPLES).

## Источники
- [Nano Banana Pro prompting tips — Google](https://blog.google/products-and-platforms/products/gemini/prompting-tips-nano-banana-pro/)
- [Ultimate prompting guide for Nano Banana — Google Cloud](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana)
- [Nano Banana image generation — Gemini API docs](https://ai.google.dev/gemini-api/docs/interactions/image-generation)
- [9:16 Aspect Ratio 2026: Safe Zones](https://edicionvideopro.com/en/editing-techniques/916-aspect-ratio-guide-vertical-video-for-tiktok-reels/)
- [Vertical Video 2026: Safe Zones, Text, Editing — Postmypost](https://postmypost.io/resources/vertical-video-2026-safe-zones-text-and-editing-how-to-create-content-that-doesn-t-cut-through-algorithms)
- [Short-Form Video Strategy & AI Creation 2026 — LTX](https://ltx.io/blog/short-form-video)
