# Медиаплан VitalLogic — 18 августа … 16 октября 2026

> Составлен 2026-08-15 под расширенный набор рубрик (решение владельца 2026-08-14).
> С 2026-08-22 действует более широкая политика
> [`editorial_policy.md`](editorial_policy.md): питание, тело, спорт, мозг, продуктивность
> через биологию, добавки и новые исследования. Этот календарь остаётся текущей очередью,
> но не ограничивает следующий ресёрч.
> Источник тем — [research/68](../../../orchestration/research/68_topic_landscape_pl_2026-08.md)
> (внешние сигналы спроса, собственная статистика канала намеренно не использовалась).
>
> **Каденс 1 ролик/день, слот 06:00 Warsaw.** 60 выпусков.
> ⚠️ Срез спроса живёт ~месяц: около **15 сентября** пересобрать `topic_signals.py` и
> сверить вторую половину плана — темы второй половины помечены как «проверить перед
> производством».

## Цель периода и KPI

Задача — **не просмотры, а способность цеплять и удерживать людей**: лайки, подписки,
пересылки. Просмотры остаются диагностикой раздачи, а не целью.

База на старте (68 роликов старше 7 дней, выгрузка Studio 05.08):

| Метрика | Сейчас | Цель к 16.10 |
|---|---|---|
| лайки, % от просмотров (медиана) | 3.9% | **≥5.0%** |
| доля роликов с лайками ≥5% | 41% | **≥55%** |
| подписки на 1000 просмотров (медиана) | **0.0** | **≥1.0** |
| доля роликов, давших хоть одного подписчика | 26% | **≥50%** |
| пересылки на 1000 просмотров (медиана) | **0.0** | **>0** |

Медианный ролик канала сегодня не приносит ни одного подписчика и ни одной пересылки —
это и есть то, что мы чиним. Просмотры считаем только как контроль: если медиана просмотров
упадёт больше чем вдвое от 167, расширение тем себя не оправдало и план пересматриваем.

**Как снимать:** ручная выгрузка Studio раз в 2 недели (лайки/подписки/пересылки есть и в
API, но `Stayed to watch` и показы — только выгрузкой). Разрез по рубрикам берётся из
`learning_loop table` — рубрика пишется в рычаги с 2026-08-14.

## Правила плана

1. **Тема приходит из широкой редакционной карты, затем получает рубрику и формат.**
   Старые доли `plate/day_body/how_much/really_true/label` больше не являются обязательным
   медиамиксом; веса в `schemas_v7.ACTIVE_RUBRICS` — мягкий анти-монокультурный fallback.
   Для скользящего батча из 20 выпусков держим минимум 4 области и не более 40% одной области.
2. **Серии по 2 ролика** в одной рубрике подряд — норма, три подряд — нет.
3. **Формат не повторяется**, пока не выйдут два других (следит `pick_format`).
4. **Payload бытовых рубрик — действие, выполнимое сегодня и бесплатно.**
5. Тема из плана запускается так (рубрика, формат и угол передаются явно):
   ```bash
   cd autopilot_factory && python3 engine_v7.py --go \
     --rubric day_body --format mistake \
     --topic "kawa zaraz po przebudzeniu" \
     --angle "kortyzol utrzymuje czuwanie sam; kofeina w tym oknie buduje tolerancję"
   ```

---

## Неделя 1 (18–24 августа) — вход в новые рубрики

| # | Дата | Рубрика | Формат | Тема (PL) | Угол |
|---|---|---|---|---|---|
| 1 | 18.08 | how_much | number_shock | Ile cukru jest w kajzerce | Перевести в ложки сахара: не граммы, а то, что видно |
| 2 | 19.08 | how_much | versus | Sok jabłkowy czy cola | Сок считается здоровым — разрыв меньше, чем кажется |
| 3 | 20.08 | day_body | mistake | Kawa zaraz po przebudzeniu | Кортизол уже держит бодрость; кофе в этом окне строит толерантность |
| 4 | 21.08 | day_body | timeline | Pierwsze 90 minut po pobudce | Хронология утра: когда вода, когда свет, когда кофе |
| 5 | 22.08 | plate | number_shock | Ile żelaza zostaje ze szpinaku | Миф Попая: железо есть, усваивается доля; что меняет витамин C |
| 6 | 23.08 | plate | tier_list | Źródła żelaza od najgorszego do najlepszego | Обратный отсчёт по усвоению, не по содержанию |
| 7 | 24.08 | really_true | myth_autopsy | Cytryna do gorącej herbaty | Польский миф про `cytrynian glinu` — откуда взялся и что на самом деле |

## Неделя 2 (25–31 августа)

| # | Дата | Рубрика | Формат | Тема (PL) | Угол |
|---|---|---|---|---|---|
| 8 | 25.08 | label | label_check | «Węglowodany, w tym cukry» na etykiecie | Разбор одной строки состава, которую все видят и никто не читает |
| 9 | 26.08 | how_much | escalation | Ile kofeiny zbiera się w twoim dniu | Накопление: кофе + кола + энергетик; период полувыведения |
| 10 | 27.08 | plate | versus | Mrożone czy świeże warzywa | Заморозка ловит момент сбора; «свежее» лежало неделю |
| 11 | 28.08 | plate | myth_autopsy | Czy mikrofalówka niszczy witaminy | Разрушает не прибор, а вода и время |
| 12 | 29.08 | day_body | self_test | Senność po obiedzie | Тест: что было первым на тарелке — и почему это решает |
| 13 | 30.08 | day_body | escalation | Wilczy głód wieczorem | Вечерний срыв начинается с утреннего завтрака |
| 14 | 31.08 | how_much | number_shock | Ile godzin snu naprawdę wystarczy | Число, которое все называют, и то, что показывают нормы |

## Неделя 3 (1–7 сентября) — школа, возврат к рутине

| # | Дата | Рубрика | Формат | Тема (PL) | Угол |
|---|---|---|---|---|---|
| 15 | 01.09 | plate | basket | Śniadaniówka, która nie zmięknie do 11 | Четыре позиции + почему именно они держат форму |
| 16 | 02.09 | plate | tier_list | Kanapka do szkoły: od najgorszej do najlepszej | Рейтинг по тому, через сколько снова хочется есть |
| 17 | 03.09 | day_body | mistake | Zjadasz i zaraz znowu jesteś głodny | Порядок еды на тарелке меняет длину сытости |
| 18 | 04.09 | really_true | versus | Kabanosy jako źródło białka | Народное «белковое» решение против реальных цифр |
| 19 | 05.09 | how_much | versus | Ile białka w jajku a ile w kabanosie | Прямое сравнение того, что кладут в ланчбокс |
| 20 | 06.09 | day_body | versus | Spacer przed czy po jedzeniu | Два варианта, разный эффект, простое правило |
| 21 | 07.09 | label | versus | Jogurt naturalny czy owocowy | Ложки сахара на баночку — та же механика, что в №1 |

## Неделя 4 (8–14 сентября)

| # | Дата | Рубрика | Формат | Тема (PL) | Угол |
|---|---|---|---|---|---|
| 22 | 08.09 | plate | number_shock | Ile wapnia jest w szklance mleka | Норма дня в стаканах — наглядная единица |
| 23 | 09.09 | plate | myth_autopsy | Wapń ze skorupki jajka | Народное средство: что с ним не так |
| 24 | 10.09 | how_much | tier_list | Napoje od najsłodszego do najmniej słodkiego | Рейтинг с сюрпризом в «здоровой» части списка |
| 25 | 11.09 | day_body | timeline | Co robi z tobą kolacja o 22:00 | Хронология ночи: пищеварение против сна |
| 26 | 12.09 | day_body | mistake | Picie wody duszkiem | Один большой объём против распределённого |
| 27 | 13.09 | really_true | myth_autopsy | Czy jajka podnoszą cholesterol | Самый живучий пищевой страх Польши |
| 28 | 14.09 | label | number_shock | Ile naprawdę kosztuje cię «wzbogacone» | Наценка за приписку на упаковке |

## Неделя 5 (15–21 сентября) — витамин D, свет, энергия

⚠️ С этого места перед производством пересобрать сигналы (`topic_signals.py`) — срез
устареет.

| # | Дата | Рубрика | Формат | Тема (PL) | Угол |
|---|---|---|---|---|---|
| 29 | 15.09 | day_body | escalation | Dlaczego wieczorem nie możesz się wyłączyć | Свет вечером как накопительный эффект |
| 30 | 16.09 | day_body | self_test | Sprawdź, ile światła widzisz rano | Тест прямо в ролике: что считается «утренним светом» |
| 31 | 17.09 | label | label_check | Witamina D: co czytać na opakowaniu | Официальная рекомендация MZ: сентябрь–апрель |
| 32 | 18.09 | how_much | number_shock | Ile witaminy D daje wrześniowe słońce | Число под угол падения солнца в PL |
| 33 | 19.09 | plate | tier_list | Produkty z witaminą D | Рейтинг: сколько нужно съесть, чтобы закрыть норму |
| 34 | 20.09 | plate | versus | Masło czy margaryna | Вечный спор у полки, разбор по составу |
| 35 | 21.09 | really_true | myth_autopsy | Czy tran działa lepiej niż kapsułki | Детская травма поколения против фактов |

## Неделя 6 (22–28 сентября) — осень началась

| # | Дата | Рубрика | Формат | Тема (PL) | Угол |
|---|---|---|---|---|---|
| 36 | 22.09 | day_body | timeline | Pierwszy tydzień krótszych dni | Что происходит с ритмом, когда темнеет раньше |
| 37 | 23.09 | day_body | mistake | Drzemka po 15:00 | Длина и время сна днём решают всё |
| 38 | 24.09 | plate | number_shock | Ile witamin zostaje w zupie | Отвар: где остаются вещества — в овощах или в бульоне |
| 39 | 25.09 | plate | myth_autopsy | Rosół na przeziębienie | Народное лекарство: что там реально работает |
| 40 | 26.09 | how_much | escalation | Ile soli zjadasz, nie solą | Соль приходит из хлеба и колбасы, а не из солонки |
| 41 | 27.09 | really_true | versus | Kiszone czy kwaszone | Брожение против уксуса — спор, который поляки любят |
| 42 | 28.09 | label | label_check | Co znaczy «bez dodatku cukru» | Разбор формулировки, разрешённой законом |

## Неделя 7 (29 сентября – 5 октября)

| # | Дата | Рубрика | Формат | Тема (PL) | Угол |
|---|---|---|---|---|---|
| 43 | 29.09 | plate | tier_list | Pieczywo od najgorszego do najlepszego | По времени сытости, не по «полезности» |
| 44 | 30.09 | plate | versus | Chleb na zakwasie czy na drożdżach | Разница, которую видно по тому, как быстро снова голоден |
| 45 | 01.10 | day_body | mistake | Jesz przy ekranie | Внимание и насыщение: механизм, а не мораль |
| 46 | 02.10 | day_body | timeline | Co się dzieje po ostatnim kęsie | Хронология 3 часов после еды |
| 47 | 03.10 | how_much | number_shock | Ile kroków to naprawdę «dużo» | Разбор цифры 10 000 и откуда она взялась |
| 48 | 04.10 | really_true | myth_autopsy | Czy ziemniaki tuczą | Не продукт, а способ приготовления и остывание |
| 49 | 05.10 | label | versus | Płatki owsiane błyskawiczne czy górskie | Одна упаковка, две скорости |

## Неделя 8 (6–12 октября) — отопление, сухой воздух, настроение

| # | Дата | Рубрика | Формат | Тема (PL) | Угол |
|---|---|---|---|---|---|
| 50 | 06.10 | day_body | escalation | Suche powietrze w mieszkaniu | Отопление включили — что меняется в ночи |
| 51 | 07.10 | day_body | self_test | Sprawdź, czy pijesz wystarczająco | Тест без взвешиваний и подсчётов |
| 52 | 08.10 | plate | number_shock | Ile błonnika jest w jednym jabłku | Норма дня, переведённая в яблоки |
| 53 | 09.10 | plate | basket | Trzy rzeczy z jesiennego warzywniaka | Сезонная корзина: что дёшево именно сейчас |
| 54 | 10.10 | really_true | escalation | Cukier a nastrój | День психического здоровья: связь без обещаний |
| 55 | 11.10 | how_much | versus | Kawa czy herbata: ile kofeiny | Одинаковое ожидание, разные числа |
| 56 | 12.10 | label | number_shock | Ile płacisz za wodę w «izotoniku» | Цена за состав |

## Неделя 9 (13–16 октября) — подготовка к переводу часов

| # | Дата | Рубрика | Формат | Тема (PL) | Угол |
|---|---|---|---|---|---|
| 57 | 13.10 | day_body | timeline | Tydzień przed zmianą czasu | Как готовить сон заранее, по дням |
| 58 | 14.10 | day_body | mistake | Odsypianie w weekend | Отсыпание не возвращает долг, а сдвигает ритм |
| 59 | 15.10 | plate | myth_autopsy | Ciepła kolacja pomaga zasnąć | Проверка бытового убеждения |
| 60 | 16.10 | how_much | number_shock | Ile czasu naprawdę zajmuje zaśnięcie | Норма против ожидания |

---

## Резерв

Если тема выпадает (устарела, не проходит комплаенс, дубль) — брать из резерва той же
рубрики, а не сдвигать план:

- **plate:** ile magnezu wypłukuje kawa · smażenie na oleju czy smalcu · podgrzewanie w
  plastiku · ile białka w 100 g kurczaka · co niszczy witaminy z grupy B
- **day_body:** telefon przed snem · budzenie się w nocy co 2 godziny · picie wody z
  cytryną na czczo · kolejność jedzenia na talerzu
- **how_much:** ile cukru w jabłku · ile kofeiny w energetyku · ile wody dziennie ·
  ile jajek dziennie
- **really_true:** czy mleko nawadnia · czy gluten szkodzi zdrowym · czy owoce wieczorem
  tuczą · czy sól morska jest lepsza
- **label:** jaka forma magnezu na sen · przyswajalność cynku · co oznacza «naturalny
  aromat»

## Что делаем с результатом

Через 25–30 выпусков (примерно к 15 сентября) считаем медианы лайков и подписок **по
рубрикам** (`learning_loop table`) и решаем: какую рубрику расширять, какую убирать в запас,
какую из резервных (`body_signals`, `at_shelf`, `kitchen_chem`) вводить в ротацию.
Раньше 25 роликов не судить — разброс раздачи в ленте это съест.
