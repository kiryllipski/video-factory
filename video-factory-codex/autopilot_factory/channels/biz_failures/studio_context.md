# studio_context — Канал «Исторические факапы бизнеса»

> Per-channel конфиг для runtime-конвейера (читают роли scriptwriter/compliance/visual/qa).
> Источники: `research/16_content_strategy_3niches.md` (ниша 1), `research/17_visual_artdirection_3niches.md` (ниша 1),
> `research/01_short_form_retention.md`, `research/04_2026_image_montage_update.md`. Гео/язык: EN/global.

## 1. Позиционирование
- **Обещание:** реальная история бизнеса без фальшивого лоска; крах — нормальная часть пути, а не конец.
- **Отстройка:** пока инфоцыгане продают «успешный успех», мы с ироничной аналитикой и архивными
  фактами показываем, как ошибки миллиардеров и корпораций стирали их за 24 часа.
- **ЦА:** предприниматели, менеджеры, бизнес-энтузиасты 25–45, уставшие от «успешного успеха».

## 2. Рубрики (content pillars)
1. **The Dead Giants** — крах монопольных корпораций XIX–XX вв. (ностальгия + schadenfreude).
2. **Fatal Decisions** — одна ошибка CEO/фаундера, запустившая лавину (саспенс, «я бы так не облажался»).
3. **The Snake Oil Era** — пузыри и аферы прошлого (шок абсурдной жадности).
4. **Saved from the Brink** — фатальный факап, но выжили за счёт антикризиса (терапевтический эффект).
5. **Old Money Sins** *(R42, добавлена по решению владельца 2026-07-03)* — торговля/банки/схемы/крахи
   допромышленной эпохи (Месопотамия → Ганза → Ост-Индские компании), не обязательно факап в узком
   смысле. Ключевой механизм — не «крах», а разрыв шаблона «история повторяется»: явная параллель
   к современной бизнес-практике/компании в CTA/финальном твисте. Отстройка от конкурентов: Kodak/Enron/Blockbuster
   видели все, а Ea-nasir/Publicani/Suftaja — нет. Темы и источники —
   `orchestration/research/42_ancient_business_history_topics.md`.

## 3. Хук (формулы, первые 1–3 сек; без приветствий)
- Противоречие фактов: `In [Year], this company made [Sum], but a single [Action] destroyed it in [Time].`
- Унижение авторитета: `We're told [Founder] was a genius, but they made the dumbest mistake in business history.`
- Шок упущенной выгоды: `How a [Small Amount] decision cost [Company] over [Huge Amount].`
- Абсурдный финал: `How did the world's most successful [X] end up [Ridiculous Situation]?`
- Прямой вызов: `If you think your business is struggling, wait until you hear how this [person] lost [Amount] in [Time].`
- **Old Money Sins (древность→сегодня, R42):**
  - `You think [modern scam/trend] is a 21st-century invention? [N] years ago, [ancient figure] was doing the exact same thing...`
  - `Long before [modern company] existed, [ancient civilization/bank] ran the exact same [business model]... and it ended in ruin.`
  - `History is just a copy-paste. What [modern company/practice] is doing today is identical to how [ancient civilization] collapsed their economy.`

## 4. Тон и голос
Ироничный, циничный, но аналитический. Войсовер — «уставший, но мудрый бизнес-консультант»:
глубокий баритон, размеренный темп, без восторга. EN. Темп ~150 wpm.

## 5. Визуальный код (для FramePlan — единый на ролик)
- **Grade:** «корпоративный нуар / старые деньги» — глубокий изумрудный, графит, приглушённое золото;
  сепия/монохром для архивных вставок; акцентный грязно-красный (печать/маркер).
- **Light:** мягкий направленный key, глубокие тени, лёгкий film grain и виньетка.
- **Lens:** 35mm документальный / 85mm для деталей (патенты, газеты).
- **Кадры:** архивные ч/б фото с параллаксом (3D-объём), медленный zoom-in, ретро газетные вырезки,
  старые чертежи/патенты, графики падения акций.
- **Типографика:** заголовки — serif (Playfair Display/Georgia); субтитры — sans (Inter/Montserrat),
  мягкое свечение; 3 слова на экране, караоке-подсветка, нижняя треть (safe-зона).
- **Motion:** ken_burns_in по умолчанию; план 1.5–2.5с; нет статики >3с.

## 6. CTA и петли
- **CTA:** `Save this so you don't repeat their mistake.` / `Share with a founder who needs a reality check.`
- **Cliffhanger:** катастрофический финал показать в первые 2 сек, но компанию не называть до середины.
- **Seamless loop:** последнее слово ролика связать с первым словом хука.

## 7. Комплаенс и юр-чистота (гейт стадии 2/7)
- **Только прошлое:** компании/люди из истории → риск диффамации минимален; современных не берём.
- **Визуал:** реальные лица/логотипы — только public-domain, иначе жёсткая стилизация/генерация.
  В промптах Nano Banana 2 не воспроизводить действующие товарные знаки узнаваемо.
- **Факты:** имена/суммы/даты сверять; хук не должен обещать то, чего нет в теле (clickbait drop).
- **Old Money Sins — историческая точность (R42):** чем древнее история, тем выше риск, что модель
  уверенно присочинит деталь. Правила: (1) точные суммы/цифры — только если source их даёт; иначе
  формулировки «by some estimates», «according to historians», без выдуманной точности; (2) если
  источник историю называет спорной/полулегендарной (напр. кожаные деньги Карфагена) — явно
  пометить в сценарии («according to some accounts») вместо подачи как бесспорный факт; (3) даты —
  «circa»/век, если точная дата не подтверждена.
- Плашка-дисклеймер по умолчанию не нужна (не YMYL), в отличие от канала wealth_viz.

## 8. Айдентика (R21)
- **Названия:** Boardroom Blunders / Tycoon Tears / Ruined Fortunes · **@BoardroomBlunders / @TycoonTears / @RuinedFortunes**
- **Tagline:** *Billion-dollar mistakes, served cold.*
- **Bio (TikTok/IG):** Billion-dollar mistakes, served cold. History's biggest business fuckups. 📉💼
- **Теги:** #BusinessHistory #CorporateFailures #OldMoney #FinancialDisasters #InvestingMistakes
- **Палитра:** изумруд `#023020`, графит `#2E2E2E`, старое золото `#D4AF37`, сепия `#E3DAC9`, акцент `#8A0303`.
- **Шрифты:** Playfair Display (заголовки) / Lato (текст).
- **Промпт аватара (1:1):** `A melting antique gold coin with a cracked surface, deep emerald green
  background, corporate noir style, old money aesthetic, dramatic cinematic lighting, highly detailed`
- Полная айдентика (баннер, тамбнейлы, промпты) — `research/21_channel_branding.md`.

## 9. Референсы
MagnatesMedia, Business Casual, Company Man — изучить параллакс, подачу бизнес-драмы, работу с архивами.
Полный 30-дневный медиаплан + долгосрочная стратегия — `research/18_mediaplan_biz_failures.md`.
