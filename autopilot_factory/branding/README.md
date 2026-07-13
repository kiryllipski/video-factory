# Branding — бренд-система каналов фабрики

Оформление и гайдлайны для 7 направлений портфеля. Источники: упаковка
[R46](../../orchestration/research/46_social_packaging_directions.md), верифицированный
комплаенс [R49](../../orchestration/research/49_pl_compliance_verified.md), монетизация
[R50](../../orchestration/research/50_platform_monetization_verified.md), живой аудит
[R43-live](../../orchestration/research/43_live_channel_audit.md).

## Каналы (каноничный нейминг)
| Slug | Канал | Handle | Гео/язык | Оператор | Гайдлайн |
|---|---|---|---|---|---|
| `vitallogic_bad_pl` | VitalLogic | @VitalLogic-nutriFlow (актив.) | PL | Владелец | [→](vitallogic_bad_pl/GUIDELINE.md) |
| `biz_failures` | TheFailFiles | @TheFailFiles | EN | Владелец | [→](biz_failures/GUIDELINE.md) |
| `psychology` | MindUnveiled | @MindUnveiled | EN | Владелец | [→](psychology/GUIDELINE.md) |
| `wealth_viz` | WealthVisuals | @WealthVisuals | EN | Владелец | [→](wealth_viz/GUIDELINE.md) |
| `dogs_psychology` | TheCanineCode | @TheCanineCode | EN | Жена | [→](dogs_psychology/GUIDELINE.md) |
| `longevity` | AgeHacker | @AgeHacker | EN | Сергей | [→](longevity/GUIDELINE.md) |
| `validator` | IdeaValidator | @IdeaValidator | EN | Владелец | [→](validator/GUIDELINE.md) |

Каждая папка: `avatar.png` (1:1), `banner.png` (16:9), `cover.png` (9:16 референс-фон обложки),
`GUIDELINE.md`. Картинки — Nano Banana 2 (`image_agent.py --model img`), промпты — в гайдлайнах.

## Кросс-брендовые правила (общие для всех)

### Safe-зоны 9:16 (1080×1920)
- Верх ~15% (≈280px), низ ~25% (≈480px), правые ~15% — под UI платформ, **держать свободными**.
- Весь текст и ключевой визуал — в центральном квадрате 1080×1080.

### Шаблон ролика (retention)
`0:00–0:03` жирный burned-in хук + смена кадра/звук → `0:03–0:15` мясо (смена визуала каждые
2–2.5с) → `0:15–…` CTA (link-in-bio). YT Shorts/IG Reels 30–40с; TikTok — версия 1:05.

### Обложка Shorts (P1 из аудита)
НЕ авто-кадр (обрывок субтитра). Делать **дизайн-обложку**: `cover.png` как фон + жирный
хук-текст крупным шрифтом канала. Первые 0.5с ролика = контрастный вопрос.

### «Живость» (P0 по R50 — условие охватов, не косметика)
Статика+TTS пессимизируется как «mass-produced». Обязательно: «дыхание» камеры (GSAP
`scale 1→1.05, yoyo, sine.inOut, 4s`), кинетическая типографика (SplitText, stagger 0.05,
`back.out(1.7)`), grain-overlay (`mix-blend: screen`), ffmpeg `noise=c0s=10:c0f=t+u,rgbashift`,
SSML-паузы в TTS. Детали — [R44b](../../orchestration/research/44b_graphics_liveliness_deepresearch.md).

### Комплаенс (верифицировано R49)
- **AI-пометка обязательна** (AI Act ст.50 с 02.08.2026): чекбокс «Altered/Synthetic» на YouTube,
  тумблер AIGC на TikTok/Meta при TTS-голосе/AI-кадрах. Сохранять C2PA при рендере;
  `altered_content=true` (YT API) / `AIGC=true` (TikTok API). Без пометки → страйк «Inauthentic».
- **Health-стоп-слова** (cure/heal/treat/disease/leczy/choroba) → support/optimize/balance.
- **Реклама**: только валидные теги (PL: `#Reklama`/`#MateriałSponsorowany`/`#WspółpracaReklamowa`;
  EN: `#ad` в первой строке) + встроенная метка платформы. Одного `#współpraca` недостаточно.
- Никаких общих эко-заявлений (`#eco`/`#natural`) без сертификата (Дир. 2024/825, штраф от 4%).

### Воронка
Единый Link-in-Bio (**Stan Store** или **Beacons**) → квиз (Typeform/Interact) → CPA/оффер/отчёт.

### Монетизация по платформам (R50)
Ставка на affiliate/квиз, не на RPM. TikTok CRP — гео US/UK/FR/DE/JP/KR/BR (**PL исключена**).
YPP: 1k подписчиков + 10M Shorts/90д. Meta ManyChat ≤200 DM/час, рандомизировать ответы.

## Чек-лист запуска аккаунта (оператор)
1. Отдельный Gmail `<channel>.collab@gmail.com`; чистый прокси/антидетект под гео (PL/US).
2. Регистрация YouTube + TikTok + IG на единый handle.
3. Установить `avatar.png` и `banner.png` на всех платформах.
4. Вставить Bio (YouTube — расширенное, TikTok/IG — короткое) + ключевые слова канала.
5. Link-in-Bio (Stan/Beacons) → квиз/CPA; проверить кликабельность.
6. Warm-up 2–3 дня (скролл/лайки конкурентов) перед первым заливом.
7. Batch 3–6 роликов; вручную ставить **дизайн-обложку** (не авто-кадр).
8. Pin лучший ролик с CTA на воронку.

## Регенерация ассетов
```bash
python3 orchestration/image_agent.py --model img --aspect 1:1 \
  --prompt "<промпт из GUIDELINE.md>" --out autopilot_factory/branding/<slug>/avatar.png
```
Аспект — через `--aspect` (image_config), не текстом. Для консистентности серии кадров можно
подать `--ref autopilot_factory/branding/<slug>/avatar.png`.
