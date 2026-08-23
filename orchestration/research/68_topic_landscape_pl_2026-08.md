# Ландшафт тем: Польша, еда и привычки — срез 2026-08-15

> **Собрано:** 2026-08-15. **Срок годности:** ~1 месяц.
> ⚠️ **Если сегодня позже 2026-09-15 — предложи владельцу обновить этот файл перед тем,
> как строить по нему план.** Поисковые подсказки и топ роликов меняются, сезонный раздел
> устаревает быстрее всего: он написан под конкретное окно август–октябрь.
>
> **Как обновить** (бесплатно, ~3 минуты):
> ```bash
> python3 orchestration/topic_signals.py --out /tmp/signals.json
> ```
> Плюс перечитать топ ниши (802 юнита квоты YouTube из дневных 10 000):
> `idea_miner.py --mode top --lang pl --seed "<запрос>" --published-after <дата>`.

Это **внешний** срез: собственная статистика канала сюда намеренно не подмешана (решение
владельца 2026-08-14 — она отражает историю канала, а не спрос рынка, и загоняет темы в
повтор). Проверка доступности источников — [research/67](67_external_demand_sources.md).

---

## 1. Что реально выигрывает в польской нише прямо сейчас

Выборка: `search.list order=viewCount`, 8 запросов, ролики с 2025-08-01, порог 50 000
просмотров, 69 роликов. Музыка, мультики и клипы отфильтрованы вручную.

| Просмотры | Канал | Заголовок | Приём |
|---:|---|---|---|
| 708 тыс. | Michał Wrzosek | NAJLEPSZE vs NAJGORSZE źródła białka! Tego nie jedz! | рейтинг + запрет |
| 613 тыс. | Interia (dr Oleszczuk) | Dwa tygodnie bez cukru wystarczą, żeby poczuć… | срок + обещание |
| 589 тыс. | Menthly | **Kajzerka to 6 łyżek cukru** | перевод в бытовые единицы |
| 557 тыс. | Marek Skoczylas | Kawa o tej porze to potężny LEK | время суток как сюжет |
| 542 тыс. | Policzona Szama | 1 ŚNIADANIE NA CAŁE ŻYCIE | одна вещь навсегда |
| 481 тыс. | Michał Wrzosek | To najgorsze i najlepsze śniadania według dietetyka | рейтинг |
| 428 тыс. | Naturalne Uzdrowienie | PRZESTAŃ JEŚĆ TE 3 RZECZY RANO | запрет + число |
| 376 тыс. | Michał Wrzosek | Obalam NAJBARDZIEJ SZKODLIWE mity dietetyczne | разоблачение |
| 366 тыс. | Marek Skoczylas | Zamień śniadanie i patrz jak brzuch znika | замена одного действия |

**Что из этого следует:**
1. **В топе ниши нет ни одного ролика про формы и дозировки добавок.** Выигрывают еда,
   привычки, время суток и мифы — ровно те четыре рубрики, которые мы вводим.
2. **Сильнейший приём — перевод в бытовые единицы.** «Kajzerka to 6 łyżek cukru» — это не
   «12 г сахара», это ложки, которые видно. Наша графика (`stat`, `bar`) под это создана.
3. **Работает «замени одно действие»**, а не «делай 7 вещей». Совпадает с решением
   владельца: payload — одно действие, выполнимое сегодня и бесплатно.
4. **Завтрак и утро — самая плотная зона** (4 ролика из 9). Это и наш слот публикации 06:00.
5. Конкуренты — врачи и диетологи с лицом. Наше отличие не в авторитете, а в плотности
   и наглядности: мы показываем цифру на экране, а не говорим её.

---

## 2. Сигналы спроса по рубрикам

Собрано `topic_signals.py`: Google Suggest + YouTube Suggest + DuckDuckGo, засев по рубрикам,
после фильтра — 400+ формулировок. Ниже кластеры, а не сырьё: одинаковые по смыслу запросы
свёрнуты, в скобках — как это реально пишут.

### `plate` — Тарелка (что на самом деле в еде)
- **Железо в конкретных продуктах**: «ile żelaza w szpinaku / w jajku / w wątróbce /
  w pestkach dyni / w płatkach owsianych». Шпинат — миф Попая, готовая тема.
- **Белок в конкретных продуктах**: «ile białka w jajku / w 100g kurczaka / w mleku»,
  плюс «ile białka w jednym posiłku» (сколько усваивается за раз — спорная тема).
- **Кальций**: «ile wapnia w mleku / w kefirze / w twarogu / w serku wiejskim / w skyrze»,
  и отдельно «ile wapnia w skorupce jajka» — народное поверье.
- **Что разрушает витамины**: «co niszczy witaminy z grupy b», «czy wysoka temperatura
  niszczy witaminy», «gotowanie warzyw», «mrożone warzywa» (мороженые против свежих).
- **Разогрев и хранение**: «podgrzewanie jedzenia w mikrofali / w plastiku / w folii
  aluminiowej» — высокий интерес и бытовой страх.
- **Жарка**: «smażenie na oleju czy smalcu», «smażenie na oleju rzepakowym».
- **Магний в еде**: «ile magnezu w kakao / w bananie / w pestkach dyni / w wodzie z kranu»
  и особенно «**ile magnezu wypłukuje kawa**» — прямой мост от нашей старой ниши к новой.

### `day_body` — День тела (привычки)
- **Кофе и утро**: «kawa rano na czczo», «kawa rano a kortyzol», «kawa rano na pusty żołądek».
- **Усталость после еды**: «zmęczenie po jedzeniu przyczyny», «senność po obiedzie
  co oznacza», «czy senność po obiedzie jest normalna» — очень частый запрос.
- **Ночные пробуждения**: «budzenie się w nocy co 2 godziny / co godzinę / przyczyny».
- **Вечерний голод**: «wilczy głód wieczorem», «jak powstrzymać / oszukać głód wieczorem».
- **Ужин и сон**: «jedzenie przed snem ile godzin», «czy jedzenie wieczorem tuczy».
- **Прогулка после еды**: «spacer po jedzeniu czy przed», «kiedy spacer po jedzeniu».
- **Вода**: «picie wody na czczo», «picie wody z cytryną efekty», «picie wody przed snem».
- **Экран вечером**: «kiedy odłożyć telefon przed snem», «czy telefon szkodzi przed snem».

### `how_much` — Сколько на самом деле
- **Сахар в напитках**: «ile cukru w coli / w pepsi / w sokach / w napojach / w szklance»
  — и в еде, которая считается безобидной: «ile cukru w jabłku / w arbuzie / w truskawkach».
- **Кофеин**: «ile kofeiny ma kawa / espresso / red bull / cola».
- **Нормы дня**: «ile wody dziennie», «ile białka dziennie», «ile soli dziennie»,
  «ile błonnika dziennie», «ile godzin snu wystarczy», «ile jajek dziennie».
- **Шаги**: «ile kroków dziennie dla zdrowia / żeby schudnąć / robi przeciętny człowiek»
  — с возрастными хвостами (40, 50, 70 лет), то есть тема живёт у взрослой аудитории.

### `really_true` — А правда ли
- **Яйца**: «czy jajka są zdrowe / szkodliwe / dobre na cholesterol / tuczące /
  ciężkostrawne», плюс бытовое «jak sprawdzić czy jajka są świeże».
- **Молоко**: «czy mleko jest zdrowe / nawadnia / dobre na zgagę», «czy mleko owsiane /
  bez laktozy / UHT jest zdrowe».
- **Микроволновка, глютен, картофель, соль, хлеб** — весь набор бытовых страхов.
- **Локальный миф-звезда**: лимон в горячий чай (якобы образуется `cytrynian glinu`).
  Это польская городская легенда, её знает вся страна — идеальный `myth_autopsy`.

### `label` — Этикетка (держим малой долей)
- «jaka forma magnezu najlepsza / na sen / na skurcze / na stres» — тема ещё живая.
- «co oznacza na etykiecie: węglowodany w tym cukry» — расшифровка строки состава,
  бытовая и не привязанная к добавкам.

---

## 3. Сезонность: середина августа — середина октября

- **Конец августа:** последние грили, массовая закупка слив (`węgierki`) под повидло и
  помидоров под пассату, локальные овощи на минимуме цены.
- **Сентябрь:** возврат к рутине, 1 сентября — школа и ланчбоксы (`śniadaniówki`),
  переход с холодных супов на тёплые, `grzybobranie` (сбор грибов) как национальное хобби.
- **Октябрь:** старт отопительного сезона — сухой воздух в квартирах, хуже сон, первые
  простуды; сезон тыквы и корнеплодов.
- **Витамин D:** в Польше [официальная рекомендация Минздрава](https://pacjent.gov.pl/aktualnosc/witamina-d-zima-to-za-malo)
  — принимать с сентября по апрель. Сезонный пик запросов «witamina D dawkowanie»
  начинается в сентябре; для рубрики `label` это главный повод года.
- **Иммунитет:** «jak wzmocnić odporność» разгоняется с середины сентября;
  «syrop z cebuli przepis» — народное средство, которое ищут массово.
- **Осенняя хандра** (`jesienna chandra`): сокращение светового дня, тема энергии и еды.

**Даты, вокруг которых строим выпуски:**

| Дата | Событие | Что выпускать |
|---|---|---|
| 1 сентября | начало учебного года | завтрак и ланчбокс, концентрация |
| 23 сентября | астрономическая осень | старт витамина D, свет и энергия |
| 10 октября | День психического здоровья | еда и настроение, сахар и тревожность |
| 25 октября | переход на зимнее время | сон, ужин, вечерняя тяга к сладкому (греть тему с 15 октября) |

---

## 4. Польские бытовые детали (иначе ролик звучит как перевод)

- **Завтрак** — это `kanapki`: хлеб, масло, ветчина или сыр, сверху помидор или огурец.
  Овсянку едят, но бутерброд — король.
- **В школу** дают яблоко, бутерброд и `kabanosy` — местный снек, который родители считают
  источником белка.
- **`Rosół`** (куриный бульон) — воскресное блюдо и народное «лекарство» от простуды.
- **`Herbata z cytryną`** — лимон в горячий чай, см. миф выше.
- **`Tran`** (рыбий жир) — детская травма поколения, осенью массово дают детям.
- **`Kiszone` против `kwaszone`** — натуральное брожение против уксуса. Поляки спорят об
  этом всерьёз; тема одновременно бытовая и «разоблачительная».
- **`Czosnek, miód, imbir`** — осенняя троица «зимнего чая».

---

## 5. Чего в этом срезе НЕ брать

- **Мусор подсказок.** По «czy to prawda że» приходят сплетни про блогеров, по «magnez» —
  `magnus carlsen`, по «ile żelaza» — Minecraft и аквариумистика. Фильтр в
  `topic_signals.py` их режет, но глазами проверять всё равно нужно.
- **Беременность, дети, грудное вскармливание.** Подсказки этим переполнены
  («ile żelaza w ciąży», «ile godzin snu potrzebuje 3-latek»), но это медицински
  чувствительные группы — YMYL-риск непропорционален выигрышу. В фильтре отсекаются.
- **Похудение как обещание.** «Ile kroków żeby schudnąć» — огромный спрос, но обещание
  результата в этой формулировке ведёт прямо в запрещённые заявления. Тему брать можно,
  формулировку — нет.
- **Темы про болезни** (щитовидка, печень, рефлюкс, холестерин как диагноз). В подсказках
  их много; для нас это только контекст, а не сюжет: говорим о еде и самочувствии.

---

## 6. Что дальше

Медиаплан, построенный на этом срезе, —
[channels/vitallogic_bad_pl/media_plan_v7.md](../../autopilot_factory/channels/vitallogic_bad_pl/media_plan_v7.md).
При обновлении файла обновлять и его: план ссылается на кластеры отсюда.
