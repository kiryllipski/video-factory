# VitalLogic — БАД / Wellness (PL)

> Гео PL · Оператор: владелец · Активный канал @VitalLogic-nutriFlow · монетизация: квиз→affiliate/CPA.
> Кросс-правила и комплаенс — в [../README.md](../README.md).

## Нейминг
- **Названия:** VitalLogic · NutriFlow PL · BioLogic Polska
- **Handle:** `@VitalLogic-nutriFlow` (оставить, актив.) / короткие для новых платформ: `@VitalLogicPL`, `@NutriFlow_PL`
- **Tagline:** *Odkryj swój potencjał zdrowia.*

## Био
- **YouTube (целевое, когда будет квиз-сайт):** Praktyczna wiedza o suplementach i biohackingu. Zrozum swoje ciało. Zrób darmowy quiz i dobierz witaminy idealne dla siebie! 👇
- **YouTube (актуальное, без ссылки — см. [`about_section.md`](about_section.md)):** без CTA на квиз, только позиционирование + дисклеймер.
- **TikTok/IG:** Suplementy bez tajemnic 🌿 Darmowy quiz zdrowotny w linku! 👇 (тоже отложить CTA до появления ссылки)
- **Ключевые слова:** #suplementy #zdrowie #biohacking #witaminy #wellnessPL

## Тон и позиционирование
Научно-обоснованный подход к БАДам без эзотерики. ToV: экспертный, заботливый, понятный.

## Визуальная айдентика
- **Палитра:** `#2A5C82` (глубокий синий) · `#4CAF50` (листовой зелёный) · `#F5F5F5` (белый)
- **Шрифты:** Montserrat (заголовки, Bold) · Open Sans (текст)
- **Система обложек:** split-screen — сверху хук на плашке `#2A5C82`, снизу залипательный макро (микроскоп, растворение, природа).

## Ассеты
| Файл | Аспект | Промпт (Nano Banana 2) |
|---|---|---|
| ~~`avatar.png`~~ | 1:1 | ⚠️ **Брак (2026-07-04):** модель самовольно впечатала текст «GENO-LEAF BIOTECH INNOVATIONS» — не тот бренд, не переживёт circle-crop. Не использовать. |
| `avatar_v2.png` | 1:1 | **Актуальный.** То же + явный запрет на текст: `..., icon only, no text, no wordmark, no letters, no typography, no company name`. Готов к загрузке. |
| `banner.png` | 16:9 | Abstract YouTube banner background, dark deep blue with glowing green soft waves, subtle microscopic cell patterns, clean empty space in the center, modern medical wellness aesthetic. ⚠️ Исходный рендер 1376×768 — ниже минимума YouTube (2048×1152). |
| `banner_v2.png` | 16:9 | **Актуальный.** `banner.png` апскейлен до 2560×1440 + текст наложен локально (PIL, Montserrat, а не Nano Banana — во избежание брака как с аватаром): заголовок «Suplementy bez mitów» + «Nowe filmy co tydzień · Obserwuj, by nie przegapić» в safe-zone 1546×423 по центру. Готов к загрузке. |
| `cover.png` | 9:16 | Macro photography of a glowing golden vitamin pill dissolving in clear water, dark background, cinematic lighting, highly detailed, 8k |

**Текст «О канале»** — готовый к вставке текст в [`about_section.md`](about_section.md).

**Правило на будущее:** для любого текста на ассетах (баннеры, обложки, лого) — генерировать
фон/иконку через Nano Banana **без текста**, накладывать текст локально (PIL/HTML) поверх.
Так же поступаем с субтитрами в видео — конвейеру нельзя доверять генерацию точного текста.

## Контент-столпы
1. Дефициты витаминов (симптомы) · 2. Синергия БАДов (что с чем) · 3. Разрушение мифов.

## Хуки
«3 sygnały, że brakuje ci magnezu» · «Nigdy nie łącz tych dwóch witamin» · «Kawa i magnez rano? Ten błąd osłabia suplementację».

## Воронка
Link-in-Bio (Stan/Beacons) → квиз на дефициты → результаты + affiliate-ссылки на БАД.

## Комплаенс (PL — верифицировано [R49](../../../orchestration/research/49_pl_compliance_verified.md))
- Дисклеймер в каждом описании: **«Materiał ma charakter edukacyjny i nie zastępuje porady lekarza. Suplement diety.»**
- Плашка «Suplement diety» — в кадре (safe-зона). Только EFSA-claim'ы, никакого «leczy/zapobiega/choroba».
- AI-пометка обязательна (TTS/AI-кадры). При affiliate — `#Reklama` в первой строке + метка платформы.
