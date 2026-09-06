# Studio — локальный пульт фабрики роликов
Спека информационной архитектуры и UX для прототипа в Google Stitch. 2026-09-02.

## 1. Что это и чем не является

**Работа сервиса:** превратить прогон пайплайна из папки с JSON и PNG в объект, который
можно смотреть, проверять и разворачивать назад на любом шаге. Сегодня качество ролика
зависит от того, откроешь ли ты вовремя нужный файл; сервис делает проверку неизбежной
и дешёвой.

**Чем не является:**
- не видеоредактор — монтаж остаётся за HyperFrames/ffmpeg;
- не CMS и не планировщик — публикация и расписание YouTube в интерфейсе отсутствуют,
  есть только передача пакета владельцу;
- не база данных — источник правды остаётся `runs/<channel>/<run>/`, сервис читает и
  пишет те же файлы. На каждом экране есть «показать JSON» и «открыть в Finder».

**Пользователь один — владелец фабрики.** Оптимизируем не под обучение новичка, а под
скорость повторной работы: горячие клавиши, плотные таблицы, минимум модалок.

## 2. Объектная модель

| Объект | Что это в файлах | Зачем в интерфейсе |
|---|---|---|
| **Канал** | `channels/<ch>/` | Контекст: бренд, голос, safe-зоны, слот каденса |
| **Прогон (Run)** | папка `runs/<ch>/<дата>_<slug>/` | Главный объект. Всё остальное — его части |
| **Стадия** | группа артефактов | Единица проверки. Их 10, порядок жёсткий |
| **Артефакт** | json / png / mp3 / mp4 | То, что смотришь. У каждого sha256 |
| **Гейт (Check)** | запись в `release_gate.json`, `qa.json` | Автопроверка: прошла / упала / устарела |
| **Claim** | `claim_id` в `research_pack.json` | Сквозной id факта: связывает источник → фразу → оверлей → описание |
| **Ревизия** | `content_revision` (хэш) | Метка версии контента. Смена ревизии обесценивает нижние проверки |
| **Решение** | приёмка кадра, принятие стадии | Твой след: кто, когда, с каким комментарием |

Статусы прогона: `черновик` → `идёт` → **`ждёт тебя`** → `собран` → `передан владельцу` →
`в архиве`. Плюс поперечные: `заблокирован` (упал блокирующий гейт), `устарел`
(правка выше по потоку).

## 3. Конвейер: 10 стадий

Каждая стадия устроена одинаково: **вход (артефакт) → автопроверки → твоё решение**.
Это главный ритм интерфейса, он не меняется от экрана к экрану.

| # | Стадия | Артефакты | Автопроверки | Твоё решение |
|---|---|---|---|---|
| 1 | Бриф | `run_meta.json`, `codex_strategy.json` | формат ↔ тип доказательства, анти-повтор по 8 прогонам | запустить / сменить формат |
| 2 | Ресёрч | `research_raw.md`, `research_pack.json` | high-risk claim ≥2 источников, rejected-claims | принять пакет фактов |
| 3 | Сценарий | `script.json` | биты, тайминги, привязка чисел к `claim_id` | принять текст / переписать бит |
| 4 | Проверки текста | `compliance.json`, `fact_review.json`, `qa.json` | стоп-слова PL/EU, абсолютные формулировки, аббревиатуры, кириллица | снять замечание / вернуть в сценарий |
| 5 | Упаковка | `publish_package.json` | длина title, URL из ResearchPack в описании, primary query | принять метаданные |
| 6 | Раскадровка | `frame_plan.json` | кадр ≤3 с, 9–15 кадров, оверлей ≥35% битов, safe-зоны | принять план кадров |
| 7 | Кадры | `frames/*.png`, `media_manifest.json` | vision-QA пикселей, sha256, provenance | **приёмка каждого кадра** |
| 8 | Озвучка | `audio/*` | обрыв мысли, пауза перед финалом, кэш | принять дорожку / перегенерировать бит |
| 9 | Сборка | `out.mp4`, `final_qa.json` | 1080×1920, H.264/AAC, три стоп-кадра, text-layout | принять ролик |
| 10 | Релиз | `release_gate.json`, `cost.json`, `artifact_manifest.json` | 12 проверок гейта | передать владельцу |

Стадии 1–5 текстовые и дешёвые, 6–9 стоят денег. Граница между 5 и 6 — **платный порог**:
интерфейс обязан показать её явно (разделитель в спине стадий + подтверждение расхода).

## 4. Девять решений, на которых держится UX

1. **Один язык статусов на всех экранах.** Пять состояний, один цвет и одна иконка на
   каждое: `ждёт входа` (серый) / `идёт` (синий, с прогрессом) / `ждёт решения` (акцент,
   единственный яркий цвет в интерфейсе) / `принято` (зелёный контур, без заливки) /
   `устарело` (штриховка). Ничего больше акцентным цветом не красим — тогда «где я нужен»
   читается с одного взгляда.

2. **Панель решения одна и та же в десяти местах.** Внизу рабочей области: `Принять` ·
   `Вернуть с комментарием` · `Стоп`. Комментарий обязателен только для возврата и
   уходит в артефакт как причина ревизии.

3. **Правка выше по потоку не удаляет, а помечает.** До подтверждения правки — список
   последствий: «отменится 4 проверки, 12 принятых кадров, озвучка 9 битов; повторная
   сборка ≈ $0.74». Отмена задним числом — главный риск такого пайплайна, и его надо
   показывать до действия, а не после.

4. **`claim_id` кликабелен везде.** Число в сценарии, подпись в оверлее, ссылка в
   описании — всё ведёт в одну карточку факта: формулировка, уровень доказательности,
   издатель, год, домен, ограничения. Это превращает «поверить тексту» в «проверить за
   два клика».

5. **Проверка — это сравнение, а не чтение.** Везде, где есть пара, показываем её рядом:
   бит ↔ кадр, план ↔ факт по времени, кадр ↔ его предыдущая версия, прогон ↔ восемь
   прошлых по осям повтора.

6. **Стоимость на кнопке, а не в отчёте.** Счётчик прогона `$0.62 / $3.00` в шапке;
   цена стоит на самой кнопке действия («Перегенерировать кадр · $0.07»).

7. **Публикации в интерфейсе нет.** Ни кнопки, ни поля даты, ни «запланировать».
   Единственный выход — `Собрать пакет и передать владельцу`, рядом постоянная плашка
   `publication_authorized = false`. Интерфейс не должен создавать иллюзию, что отсюда
   что-то улетает на канал.

8. **Плеер с маркерами структуры.** Под 9:16 плеером — дорожка: смены кадров, оверлеи,
   и четыре именованных маркера (`хук`, `первый пруф`, `поворот`, `выплата`) с
   допустимыми окнами. Клик по маркеру перематывает и подсвечивает нужный бит.

9. **Свайп-тест как отдельный режим.** Кнопка «Первые 2 секунды»: луп первых 2 с без
   звука во весь экран. Это первое, что смотрит зритель, и единственное, что стоит
   смотреть отдельно от ролика.

## 5. Навигация

Левый рельс, пять пунктов:

1. **Сегодня** — что ждёт решения, что идёт, что готово к передаче.
2. **Прогоны** — библиотека и сравнение.
3. **Темы** — бэклог идей и медиаплан.
4. **Результаты** — гипотезы и метрики.
5. **Настройки** — канал, голос, потолок стоимости, слот каденса, пути.

Внутри прогона — своя вертикальная спина из 10 стадий. Глубина навигации не больше трёх:
`раздел → прогон → стадия`. Всё остальное — панели и оверлеи внутри стадии.

## 6. Экраны

### S1. Сегодня
**Задача:** за 5 секунд понять, нужен ли я сейчас.
Шапка канала одной строкой: слот 06:00 Warsaw, что стоит в очереди, вчерашние просмотры.
Три секции сверху вниз: **Ждут решения** (карточки: превью-кадр или постер, тема,
стадия, что именно решить, сколько ждёт) → **В работе** (прогресс по спине стадий,
текущее действие, потраченное) → **Готово к передаче**.
Пустое состояние — не иллюстрация, а действие: «Ничего не ждёт. Запустить прогон».
Блокеры — отдельной красной полосой над всем.

### S2. Новый прогон
Один экран, не мастер. Слева форма: тема, угол, рубрика, формат (карточки с подсказкой
«выбирай, когда…»), полоса распространения `feed / search / hybrid` (+ основной запрос
для двух последних), лейн длительности `core 18–24 с` / `deep 28–35 с`.
Справа — **панель анти-повтора**: восемь последних прогонов по осям (механика хука,
первый пруф, поворот, приём доказательства, среда, ритм монтажа, приём выплаты).
Совпадения подсвечиваются, счётчик «изменено осей: 2 из 3 требуемых» блокирует запуск
подсказкой, а не запретом.
Внизу: оценка стоимости и `Запустить текстовый прогон` (медиа не трогается).

### S3. Рабочий стол прогона
Хаб, из которого не выходишь. Три зоны:
- **Спина (слева, 240px):** 10 стадий, статус, короткий хэш ревизии, разделитель
  «дальше платно» между 5 и 6.
- **Центр:** содержимое активной стадии + панель решения внизу.
- **Контекст (справа, 320px, сворачивается):** карточка факта / стоимость / история
  решений и ревизий.
Шапка: тема, канал, формат · рубрика · лейн, `content_revision`, `$0.62 / $3.00`,
плашка `публикация не авторизована`, кнопки «JSON» и «Finder».

### S4. Ресёрч
Таблица утверждений: `claim_id`, разрешённая формулировка, уровень доказательности
(`официальный` / `независимые данные` / `данные производителя` / `сообщество` /
`гипотеза`), число источников, метка «высокий риск» с требованием ≥2.
Отдельным блоком — **отклонённые утверждения** с причиной; они блокируют прогон, и это
надо видеть, а не искать.
Правая панель по клику: источник — тип, издатель, год, домен, дата обращения, открыть.

### S5. Сценарий
Сверху — **линейка структуры**: хук заканчивается ≤3.2 с, первый пруф ≤3.0 с, поворот
≤45%, выплата ≤78%. Отклонение подсвечивается на самой линейке.
Ниже — таблица битов: №, роль (`хук` / `пруф` / `поворот` / `выплата` — цветные метки),
польский текст (правится по месту), измеренная длительность, накопленное время, чипы
`claim_id`, тип и текст оверлея.
Справа — режим **«прочти вслух»**: один бит крупно, кнопки «дальше/назад». Требование
скилла читать текст вслух перед TTS должно быть кнопкой, а не памяткой.

### S6. Проверки текста
Список замечаний: правило, вердикт, цитата из текста с подсветкой, номер бита.
Фильтр `только блокирующие` включён по умолчанию. Действия на замечании: `снять` (с
комментарием) или `править бит` — уводит в S5 с фокусом на нужной строке и возвращает
обратно. Сверху — счётчик `3 блокирующих · 5 предупреждений`.

### S7. Раскадровка
Горизонтальный таймлайн: кадр = блок, ширина = его длительность, под блоком — биты,
которые он покрывает. Автоматически подсвечивается: кадр длиннее 3 с, кадров меньше 9,
две соседние одинаковые крупности, повтор эмоции героя.
Выбор кадра → правая панель: промпт на английском, дескриптор героя (общий на весь
ролик, показывается неизменным), оверлей, превью safe-зон поверх макета — верхние 15%,
правая колонка, нижняя треть.

### S8. Кадры — приёмка
Самый частый ручной шаг, поэтому отдельный полноэкранный режим.
Сетка миниатюр 9:16 с номером и статусом: `сгенерирован` / `принят` /
`на перегенерации` / `провал vision-QA` (с причиной: впечатанный текст, рамка, руки).
Клик → просмотрщик: кадр во весь рост, накладка safe-зон и оверлея включается тумблером,
стрелки между кадрами, слева — бит, который этот кадр иллюстрирует.
Горячие клавиши: `A` принять, `R` перегенерировать, `←/→` навигация, `O` наложение.
Внизу — прогресс `7 из 12 принято` и кнопка `Записать manifest`, активная только когда
принято всё. Мелким моноширинным — sha256 и происхождение кадра: именно это сверяет гейт.

### S9. Озвучка
Голос, стиль, скорость сверху. Список битов: волна, длительность, play, статус кэша
(`переиспользован` / `новый`), кнопка перегенерации одного бита.
Подсветки: бит обрывает незаконченную мысль, пауза 0.48 с перед финальной фразой,
замедление финального бита.

### S10. Просмотр и релизный гейт
Слева плеер 9:16 в натуральной пропорции, под ним дорожка с маркерами структуры и
кадрами. Справа — чек-лист гейта построчно: имя проверки, результат, деталь
(`длительность: план 22.8 с, факт 51.1 с — диагностика темпа, не блокер`).
Отдельно кнопка `Первые 2 секунды` (луп без звука) и три стоп-кадра vision-QA
кликабельными миниатюрами.

### S11. Пакет публикации
Превью карточки YouTube слева (заголовок и первые строки описания как их увидит зритель),
поля справа: заголовок (счётчик до 100), описание с обязательными URL источников
(URL, которых нет в ResearchPack, подсвечиваются как ошибка), видимые хештеги, API-теги,
закреплённый комментарий, полоса распространения и основной запрос с проверкой
«запрос есть в заголовке или первых двух строках описания».
Одна кнопка: `Собрать пакет и передать владельцу`. Ни даты, ни времени, ни «опубликовать».

### S12. Библиотека прогонов
Таблица: дата, тема, формат, рубрика, лейн, длительность, стоимость, статус, ревизия.
Фильтры и поиск по теме и `claim_id`. Выбор до 4 прогонов → **сравнение по осям**
творческого отпечатка: одинаковые значения окрашиваются как риск повтора.

### S13. Результаты
Гипотеза → прогоны, которые её проверяют → метрики. Сравнение только сопоставимых:
`просмотров в сутки` при указанном возрасте ролика. Явная пометка на карточке метрик:
показы и «досмотрели до…» через API недоступны, только ручная выгрузка Studio.

### S14. Настройки
Канал, голос по умолчанию, потолок стоимости прогона, слот каденса, пути к папкам
прогонов и архиву, ключи (только статус «есть/нет», без значений).

## 7. Что важно не сделать

- Не прятать провалившиеся проверки в аккордеоны — они и есть содержание экрана.
- Не показывать прогресс-бар без имени текущего действия: «идёт сборка» бесполезно,
  «озвучка бита 7 из 11» — работает.
- Не делать приёмку кадров модалкой поверх списка: это отдельный полноэкранный режим,
  в нём человек проводит больше всего времени.
- Не заводить второй источник правды. Всё, что интерфейс показывает, лежит в папке
  прогона; всё, что он меняет, пишется туда же.

---

# 8. Промпты для Google Stitch

Английский, по одному экрану. Первый промпт — общий стиль, дальше экраны ссылаются на
него. Прогоняй по порядку: Stitch держит консистентность лучше, когда стиль задан заранее.

## P0 · Design system seed
```
Desktop web app for a single professional user: a local control room for an automated
short-video production pipeline. Dark, dense, calm. One single accent color used ONLY for
"needs your decision" states; everything else is neutral grays with a thin green outline for
approved and a hatched pattern for stale. Compact typography, 14px base, monospace for IDs,
hashes and file names. Tables over cards for data; cards only for pending decisions.
No illustrations, no gradients, no marketing language. 12-column grid, 8px spacing scale.
Persistent left rail with 5 items: Today, Runs, Topics, Results, Settings.
```

## P1 · Today
```
Screen "Today". Top: one-line channel bar — publishing slot 06:00 Warsaw, queue count,
yesterday's views. Below, three stacked sections with counts in their headers:
1) "Waiting for you" — cards, each with a 9:16 thumbnail, video topic, current stage,
   the exact decision required, and how long it has been waiting; primary button "Review".
2) "In progress" — rows with a 10-step stage spine, the current action in words
   ("voice-over beat 7 of 11"), elapsed time and money spent.
3) "Ready to hand off" — rows with a "Build package" button.
A red blocker strip can appear above everything. Empty state is a single line of text plus
a "Start a run" button. Top-right: "New run".
```

## P2 · New run
```
Screen "New run", two columns. Left: a form — topic, angle, rubric select, format picker as
a grid of small selectable cards each with a one-line "choose when…" hint, distribution lane
segmented control (feed / search / hybrid) with a primary-query field revealed for search and
hybrid, duration lane radio (core 18-24s / deep 28-35s).
Right: an "anti-repetition" panel — a compact matrix of the last 8 runs across 7 creative axes
(hook mechanism, first proof, turn device, evidence device, environment, edit grammar, payoff
device); cells matching the current selection are highlighted as a repetition risk, with a
counter "2 of 3 required axes changed".
Sticky footer: estimated cost and a primary button "Run text-only pass (no media)".
```

## P3 · Run workspace
```
Screen "Run workspace", three columns. Left 240px: a vertical spine of 10 pipeline stages
(Brief, Research, Script, Text checks, Package, Storyboard, Frames, Voice-over, Build, Release),
each with a status dot, and a labeled divider between stage 5 and 6 reading "paid stages below".
Center: the active stage content area with a fixed bottom decision bar containing three
buttons — "Approve", "Send back with a comment", "Stop".
Right 320px collapsible context panel showing a claim card, cost breakdown and a decision history
timeline. Header: video topic, channel, format · rubric · lane, short content revision hash,
a cost meter "$0.62 / $3.00", a static badge "publishing not authorized", and small "JSON" and
"Finder" buttons.
```

## P4 · Research review
```
Screen "Research". A dense table of claims: claim ID (monospace), the approved wording, an
evidence-level chip (official / independent dataset / vendor / community / hypothesis), source
count, and a "high risk — needs 2+ sources" flag. Below it a clearly separated block
"Rejected claims" with the reason for each and a note that they block the run.
Clicking a row opens the right panel with the source: type, publisher, year, domain, access date
and an external-link button. Bottom decision bar: Approve / Send back / Stop.
```

## P5 · Script review
```
Screen "Script". Top: a horizontal structure ruler over the total duration with four named
markers and their allowed windows — hook ends by 3.2s, first proof by 3.0s, turn by 45%,
payoff by 78%; violations are highlighted on the ruler itself.
Below: an editable table of beats — number, role chip (hook / proof / turn / payoff), Polish
text with inline editing, measured audio duration, cumulative time, claim-ID chips, overlay type
and overlay text.
Right panel: a "read aloud" mode showing one beat in large type with previous/next controls.
Editing any beat shows an inline warning that downstream checks will become stale.
```

## P6 · Text checks
```
Screen "Text checks". Header counters: "3 blocking · 5 warnings" with a filter toggle
"blocking only", on by default. A list of findings; each row shows the rule name, verdict,
the offending quote with the exact words highlighted, and the beat number. Each row has two
actions: "Dismiss with a comment" and "Fix the beat". Findings cover forbidden health wording,
absolute claims, unexplained clinical abbreviations and wrong-alphabet text.
```

## P7 · Storyboard
```
Screen "Storyboard". A horizontal timeline where each frame is a block whose width equals its
duration; inside is a 9:16 thumbnail or a placeholder, and under it the beats it covers.
Automatic warnings appear on blocks: longer than 3 seconds, fewer than 9 frames total, two
adjacent shots with the same scale, repeated character expression.
Selecting a block opens the right panel: the English image prompt, the invariant hero
descriptor, the overlay, and a 9:16 preview with toggleable safe-zone overlays — top 15%,
right column, bottom third.
```

## P8 · Frame approval (full screen)
```
Screen "Frame approval", a dedicated full-screen mode. Grid of 9:16 frame thumbnails with an
index and status: generated / approved / regenerating / failed visual QA with a short reason
(burned-in text, unwanted border, malformed hands).
Clicking a frame opens a viewer: the frame large at true 9:16, a toggle for safe-zone and
overlay overlays, left/right navigation, and the beat text this frame illustrates shown beside
it. Keyboard hints displayed: A approve, R regenerate, arrows navigate, O overlay.
Bottom bar: progress "7 of 12 approved", the sha256 and provenance of the current frame in small
monospace, and a primary button "Write manifest" that stays disabled until every frame is
approved. Regenerate button shows its cost on the button itself.
```

## P9 · Voice-over
```
Screen "Voice-over". Header: voice, delivery style, speed. A list of beats, each row with a
waveform, duration, play button, cache status chip (reused / new) and a per-beat regenerate
button showing its cost. Rows can carry warnings: sentence cut mid-thought, missing 0.48s pause
before the final line, final beat not slowed down. Bottom decision bar as elsewhere.
```

## P10 · Preview and release gate
```
Screen "Preview". Left: a 9:16 video player at true aspect ratio, with a timeline underneath
showing frame changes, overlay markers and four named structure markers (hook, first proof,
turn, payoff). A secondary button "First 2 seconds" plays a silent loop of the opening.
Right: the release gate as a checklist — one row per check with name, pass/fail state and a
detail line, for example "duration: planned 22.8s, actual 51.1s — pacing diagnostic, not a
blocker". Below the checklist, three clickable visual-QA still thumbnails.
```

## P11 · Publish package
```
Screen "Publish package", two columns. Left: a preview of how the video card will look to a
viewer — title and the first lines of the description. Right: fields — title with a 100-character
counter, description with source URLs (any URL not present in the research pack is flagged as an
error), visible hashtags, API tags, pinned comment, distribution lane and primary query with a
validation line "query must appear in the title or the first two description lines".
A single primary button "Build package and hand to owner". No date field, no schedule control, no
publish button anywhere. A persistent badge reads "publishing not authorized".
```

## P12 · Runs library
```
Screen "Runs". A dense table: date, topic, format, rubric, duration lane, length, cost, status,
revision hash. Filters above the table and a search field that matches topics and claim IDs.
Checkboxes allow selecting up to 4 runs; a "Compare" button opens a side-by-side matrix of their
creative axes where identical values across runs are highlighted as repetition risk.
```

## P13 · Results
```
Screen "Results". Top: a list of active hypotheses, each expandable into the runs testing it.
For each run: views per day with the video's age stated next to it, chose-to-view rate, average
percentage viewed, subscribers per 1k. A persistent note on the metrics card states that
impressions and "stayed to watch" are not available through the API and come only from a manual
export.
```
