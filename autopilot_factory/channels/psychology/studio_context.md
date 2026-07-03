# studio_context — Канал «Психология и когнитивные искажения»

> Per-channel конфиг (роли scriptwriter/compliance/visual/qa). Источники: R16/R19 (контент/медиаплан),
> R17 (визуал), R21 (айдентика). Гео/язык: EN/global. Голос TTS: Kore, «calm, intriguing, insightful».

## 1. Позиционирование
- **Обещание:** показываем, как твой мозг тайно обманывает тебя каждый день, и даём элегантные
  ментальные инструменты его переиграть.
- **Отстройка:** никакой токсичной «dark psychology» и клише — строгая наука (когнитивистика,
  поведенческая экономика) в эстетике «тихой роскоши» и практической пользы.
- **ЦА:** 18–35, саморазвитие, отношения, карьера.

## 2. Рубрики
1. **Brain Glitches** — баги восприятия/памяти (узнавание «я так и делаю»).
2. **The Price Tag Trap** — психология потребления и уловки маркетинга (высокие share, экономят деньги).
3. **Human Decoders** — невербалика, чтение людей без токсичных манипуляций (соц. безопасность).
4. **Mental Armor** — ментальные модели, решения, эмоц. гигиена (лидер по сохранениям).

## 3. Хук (формулы)
- Brain Glitches: `Your brain is lying to you about [X], and here is the proof.`
- Price Tag Trap: `This is the psychological trick that makes you spend more on [X].`
- Human Decoders: `Here's how to instantly tell if someone is [lying / interested].`
- Mental Armor: `Use this mental model to never [make bad decision] again.`
- Контр-интуиция: `Being [smart/nice] is secretly ruining your [X]. Here's why.`

## 4. Тон и голос
Спокойный, глубокий, слегка гипнотический, авторитетный, но дружелюбный. Без криков и фальшивого
энтузиазма. EN, ~150 wpm.

## 5. Визуальный код (единый на ролик, ревизия R41 — variety pack против монотонности)
- **Grade:** *Neon Void* (смоляной чёрный + фиолетовый `#2B00FF`/розовый `#FF007F`/циан `#00FFFF`)
  ИЛИ *Quiet Luxury* (шалфей/графит/тёплый беж, кинематографичный софтбокс) — один грейд на ролик.
- **Юр-чистота:** без сгенерированных лиц. Разрешено: силуэты со спины, руки, тени, манекены,
  абстрактные объекты.
- **Композиция:** 9:16, нижние ~30% всегда в тень/чистый фон под субтитры.
- **5 категорий кадров** (промпт-скелеты и объективы — `orchestration/research/41_psychology_visual_revision.md`):
  1. **The Anchor** (заземлённый человек, силуэт/со спины) — 35mm/50mm.
  2. **The Object** (предметная метафора, руки+предмет) — 85mm, мелкая ГРИП.
  3. **The Environment** (пространство/масштаб, liminal space) — 14-24mm ультра-ширик.
  4. **The Logic** (инфографика/типографика, изометрия) — под цифры/термины.
  5. **The Emotion** (абстрактное макро — прежняя база) — 100mm макро.
- **Правило чередования:** не больше 2 кадров одной категории подряд. Паттерн на ~60с:
  Anchor (хук) → Object/Emotion (проблема) → Environment (вау-смена масштаба) →
  Logic/Object (факты) → Anchor/Emotion/Environment (развитие) → Logic/Anchor (CTA).
- **Motion по категории:** Environment — pan (scale 1.15, drift по X); Anchor/Object — dolly in
  (scale 1.0→1.08 к центру); Emotion — dolly out (scale 1.1→1.0); Logic — tilt по Y (scale 1.05).
  План 1.5–2.5с; нет статики >3с.
- **Типографика:** заголовки Anton/Bebas Neue (капс), субтитры Inter; 1–3 слова, караоке-подсветка
  пастельно-жёлтым/циан; нижняя треть (safe-зона).

## 6. CTA и петли
- **CTA:** `Save this to outsmart your own brain.` / `Share with someone who needs to see this.`
- Open loop на 10–12с; сильный эффект узнавания в первые 2 сек.

## 7. Комплаенс (гейт 2/7)
- Не диагностируем и не лечим: без обещаний терапии/лечения психзаболеваний; депрессия/РПП — не
  пессимизируемые темы, держим фокус на поп-психологии и социальной динамике.
- Никакой «тёмной психологии»/манипулятивных техник во вред.
- Плашка-дисклеймер по умолчанию не нужна (не YMYL).

## 8. Айдентика (R21)
- **Названия:** Mind Traps / Bias Brain / The Psyche Shift · **@MindTraps / @BiasBrain / @PsycheShift**
- **Tagline:** *Your brain is lying to you.*
- **Bio (TikTok/IG):** Your brain is lying to you. Unlocking cognitive biases & mind traps. 🧠🔓
- **Теги:** #Psychology #CognitiveBias #MentalModels #MindTricks #BehavioralScience
- **Промпт аватара (1:1):** `Abstract glowing human brain with a digital glitch effect, neon purple and
  cyan colors, pitch black background, optical illusion style, minimal, sharp focus, mind-bending`
- **Референсы:** Aperture, Einzelgänger.
