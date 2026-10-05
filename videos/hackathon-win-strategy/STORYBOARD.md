---
format: 1080x1920
duration: 68.44s
message: "Победный хакатон — это не максимальный объём работы, а одна ясная боль, работающее демо и понятный питч."
arc: how-to-process
audience: "Участники хакатонов — от новичков до опытных команд"
mode: autonomous
music: none
---

## Video direction

- Palette system: BlockFrame only — cream, blue, green, pink and off-white cycle as grounds; black is the structural ink; white carries cards; yellow is reserved for the most useful action and the final close-frame shadow.
- Motion grammar: every verbal unit arrives on its Gemini narration cue, on a smooth long-tail settle; the lower caption band remains clear. Hold frames 2 and 7 deliberately after their last reveal; all other scenes progress through the back half of their voice-over.
- World: a lively 2D cartoon hackathon universe — thick black outlines, square sticker cards, comic office objects, expressive original figures and device-free diagrams. Decorations are structural: dot grids, tilted badges, star bursts and cables, never filler.
- Negative list: no real logos, no browser chrome, no generated fake text, no blue-purple AI gradients, no stock imagery, no front-loaded slideshow, no floating screensaver motion, no lazy breathing.

## Frame 1 — Не строй космолёт

- scene: Мультяшный участник пытается удержать падающую башню из вкладок, а над ней мигает наклейка «КОСМОЛЁТ ЗА НОЧЬ».
- voiceover: "Хочешь выиграть хакатон? Не строй космолёт за ночь. Жюри не платит за количество вкладок."
- duration: 7.52s
- poster: 2.8s
- transition_in: cut
- status: outline
- src: compositions/frames/01-no-spaceship.html
- type: hook
- persuasion: Pain validation + comic exaggeration
- beat: Recognition + surprise
- blueprint: kinetic-type-beats (Adapt)
- focal: слово «КОСМОЛЁТ» и шаткая башня вкладок
- roles: башня вкладок = foreground subject; заголовок = supporting hero type; персонаж и звёздная наклейка = supporting comic actors; кремовый dot-grid = background

narrativeRole: Снимает героический миф о «сделать всё» и создаёт узнаваемый конфликт.
keyMessage: Большой объём сам по себе не приближает к победе.

Adapt: сохраняем фиксированный центр и ударную смену слов; вместо абстрактных фраз — одна мультяшная башня, которая разваливается ровно на слове «вкладок».
Scene 1 (0.0–2.2s): На кремовом поле с угловой dot-grid герой-стикер в верхних двух третях пытается удержать одну огромную вкладку; слово «ВЫИГРАТЬ?» появляется per-word reveal (`dynamic-content-sequencing`) слева от него, asymmetric 60/40, три слоя.
Scene 2 (2.2–5.0s): На «не строй космолёт» карточки вкладок нарастают вверх через cluster-to-outward expansion (`center-outward-expansion`); ярлык «КОСМОЛЁТ» жёстко въезжает сверху через kinetic beat-slam (`kinetic-beat-slam`), герой смотрит на башню.
Scene 3 (5.0–7.52s): На «количество вкладок» башня мягко складывается в одну крупную карточку «НЕ ПРОЕКТ», а слово «ВКЛАДОК» делает flash word-swap (`discrete-text-sequence`) и остаётся читаемым; статичный hold без дрейфа.

## Frame 2 — Что видит жюри

- scene: Стол жюри превращается в игровую панель: три крупные карточки «БОЛЬ», «РЕШЕНИЕ», «ДЕМО» включаются одна за другой.
- voiceover: "Побеждает не самый большой проект. Побеждает тот, у которого сразу видно: боль, решение и работающий результат."
- duration: 9.12s
- poster: 3.6s
- transition_in: push-slide LEFT
- status: outline
- src: compositions/frames/02-judge-dashboard.html
- type: product_intro
- persuasion: Frame-then-fill + rule of three
- beat: Orientation + clarity
- blueprint: grid-card-assemble (Adapt)
- focal: вертикальная тройка карточек «БОЛЬ», «РЕШЕНИЕ», «ДЕМО»
- roles: три карточки = foreground subject; стол жюри = midground stage; фоновые билетики и точечная сетка = background; бирка «ЖЮРИ СЧИТЫВАЕТ» = supporting chrome

narrativeRole: Формулирует универсальную структуру сильного хакатон-проекта.
keyMessage: Оценке помогает мгновенно считываемая связка из боли, решения и результата.

Adapt: сохраняем каскадную сборку карточек; широкая сетка превращается в вертикальный стек, приспособленный к 9:16.
Scene 1 (0.0–2.1s): На голубом поле и плоском столе жюри появляется только заголовок «ЧТО ВИДИТ ЖЮРИ?» через line-by-line reveal (`discrete-text-sequence`), сверху label-pill, stacked editorial layout.
Scene 2 (2.1–6.2s): На словах «боль, решение» две белые карточки входят в свои вертикальные слоты коротким stagger-assemble (`center-outward-expansion`); у каждой маленькая жёлтая точка-метка, карточки наклонены в разные стороны.
Scene 3 (6.2–9.12s): На «работающий результат» третья зелёная карточка «ДЕМО» въезжает и зажигает соединяющую чёрную линию SVG self-draw (`svg-path-draw`); весь стек остаётся на hold, без дополнительного push.

## Frame 3 — Одна настоящая боль

- scene: Огромный воздушный шар «СПАСЁМ МИР» сдувается, а маленькая карточка «УБРАТЬ ОЧЕРЕДЬ» превращается в яркую мишень.
- voiceover: "Шаг первый: выбери одну боль. Не «спасём мир», а «уберём очередь на приём». Уже задача — громче демо."
- duration: 12s
- poster: 3.8s
- transition_in: push-slide LEFT
- status: outline
- src: compositions/frames/03-one-pain.html
- type: feature_showcase
- persuasion: Contrast + concretization
- beat: Focus + relief
- blueprint: comparison-split (Reproduce)
- focal: две большие карточки «СПАСЁМ МИР» и «УБРАТЬ ОЧЕРЕДЬ»
- roles: левая и правая карточки = foreground subjects; целевая мишень = midground payoff; розовый и зелёный glows = background; верхняя подпись = supporting type

narrativeRole: Показывает, как сузить амбицию до демонстрируемого кейса.
keyMessage: Одна конкретная проблема заметнее абстрактной миссии.

Scene 1 (0.0–2.6s): На розовом фоне верхняя подпись «ОДНА БОЛЬ» садится в верхней трети smooth slide-down (`discrete-text-sequence`), под ней остаётся пустая ось сравнения.
Scene 2 (2.6–7.8s): На «спасём мир» и «уберём очередь» две карточки разъезжаются в вертикальный stacked split, обе через mirrored split-tilt cards (`split-tilt-cards`); левая раздута и неуклюжа, правая компактна и указывает на мишень.
Scene 3 (7.8–12.0s): На «громче демо» правая карточка получает жёлтый badge «ДЕМОНСТРИРУЕМО», который приземляется через spring-pop entrance (`spring-pop-entrance`); левая сдувается в полупрозрачный воздушный шар, итог держится статично.

## Frame 4 — Роли до кофе

- scene: Три персонажа на мультяшной кухне хватают карточки «ПРОДУКТ», «КОД», «ПИТЧ», пока четвёртая карточка «КТО ДЕЛАЛ БЭКЕНД?» улетает в мусорный бак.
- voiceover: "Шаг второй: роли — до кофе. Продукт, код, питч. Иначе утром команда проходит квест «кто вообще делал бэкенд?»"
- duration: 9.92s
- poster: 4.1s
- transition_in: push-slide LEFT
- status: outline
- src: compositions/frames/04-roles-before-coffee.html
- type: feature_showcase
- persuasion: Numbered enumeration + causal chain
- beat: Momentum + comic unease
- blueprint: grid-card-assemble (Adapt)
- focal: три роль-карты с персонажами «ПРОДУКТ», «КОД», «ПИТЧ»
- roles: роль-карты = foreground subjects; кофейная станция = midground stage; карточка «КТО ДЕЛАЛ БЭКЕНД?» = supporting comic antagonist; мятный паттерн = background

narrativeRole: Переводит стратегию в простой способ не потерять время команды.
keyMessage: Чёткое распределение ролей предотвращает хаос в самый дорогой момент.

Adapt: сохраняем вертикальную карту-каскад, но каждая карточка несёт оригинального мультяшного участника и свой инструмент.
Scene 1 (0.0–2.4s): На мятной кухне появляется ярлык «РОЛИ — ДО КОФЕ» и один стаканчик, который делает короткий press-release (`press-release-spring`); title-safe зона сверху.
Scene 2 (2.4–6.6s): На перечислении «продукт, код, питч» три белые карточки собираются сверху вниз через stagger-assemble (`center-outward-expansion`): продукт с маркером, код с фигурными скобками, питч с микрофоном; vertical stack, три глубины.
Scene 3 (6.6–9.92s): На вопросе про бэкенд красная карточка-вопрос пытается влететь сбоку, но её мягко выталкивает собранный стек через reactive displacement (`reactive-displacement`); финальный стек держит взгляд на карточке «КОД».

## Frame 5 — Демо раньше слайдов

- scene: Гигантская кнопка «ЗАПУСТИТЬ ДЕМО» нажимается, показатель на экране оживает, а скринкаст в спасательном круге приземляется рядом.
- voiceover: "Шаг третий: демо раньше слайдов. Кнопка нажимается, цифра меняется, запасной скринкаст уже на ноутбуке."
- duration: 8.84s
- poster: 3.4s
- transition_in: zoom-through
- status: outline
- src: compositions/frames/05-demo-before-slides.html
- type: feature_showcase
- persuasion: Demonstration + contingency framing
- beat: Confidence + delight
- blueprint: cursor-ui-demo (Adapt)
- focal: большая кнопка «ЗАПУСТИТЬ ДЕМО» и меняющееся число на экране
- roles: кнопка и результат-карточка = foreground subject; спасательный круг со скринкастом = supporting safety net; ноутбук-рамка = midground stage; жёлтые искры = background accent

narrativeRole: Даёт приоритет самому убедительному доказательству — рабочему действию.
keyMessage: Живое демо и план Б сильнее набора красивых обещаний.

Adapt: сохраняем одного курсорного актёра и действие→результат; вместо интерфейса продукта используем очень простую мультяшную панель демонстрации.
Scene 1 (0.0–2.1s): На жёлтом поле появляется короткая надпись «СНАЧАЛА ДЕМО» и простая ноутбук-панель; чёрный курсор входит в верхней безопасной зоне через cursor click + ripple (`cursor-click-ripple`).
Scene 2 (2.1–5.9s): На «кнопка нажимается» курсор физически давит на кнопку через button press (`press-release-spring`); на «цифра меняется» большая карточка результата scale-swaps из «—» в «ГОТОВО» (`scale-swap-transition`) и получает визуальный счётчик-галочку.
Scene 3 (5.9–8.84s): На «запасной скринкаст» спасательный круг с камерой всплывает из нижней безопасной зоны через spring-pop entrance (`spring-pop-entrance`), пока результат держится крупным и резким; статичный hold.

## Frame 6 — Питч без героизма

- scene: Микрофон-громкоговоритель выпускает три комикс-плашки «ПРОБЛЕМА», «МАГИЯ», «ПОЛЬЗА», а таймер-пицца смешно остывает на заднем плане.
- voiceover: "Финал: питч — не дневник страданий. Проблема, магия, польза. Жюри должно понять всё до остывшей пиццы."
- duration: 9.44s
- poster: 4s
- transition_in: zoom-through
- status: outline
- src: compositions/frames/06-pitch-not-suffering.html
- type: benefit_highlight
- persuasion: Distillation + rule of three
- beat: Conviction + amusement
- blueprint: kinetic-type-beats (Adapt)
- focal: три комикс-плашки «ПРОБЛЕМА», «МАГИЯ», «ПОЛЬЗА» и микрофон
- roles: три плашки = foreground sequence; микрофон = midground anchor; таймер-пицца = supporting comic prop; розовый stripe-block = background

narrativeRole: Упаковывает результат в запоминаемую формулу презентации.
keyMessage: Питч должен объяснять ценность, а не перечислять ночные подвиги команды.

Adapt: сохраняем ритмический текстовый relay, но привязываем каждое слово к одному чёткому комикс-объекту, а не к абстрактному экрану.
Scene 1 (0.0–2.3s): На розовом stripe-block микрофон собирается из двух чёрных форм; фраза «НЕ ДНЕВНИК СТРАДАНИЙ» входит per-word staggered reveal (`dynamic-content-sequencing`) в верхнем 60% кадра.
Scene 2 (2.3–6.7s): На «проблема, магия, польза» три отдельные плашки по очереди делают hard-cut word-swap (`discrete-text-sequence`) перед микрофоном; каждая получает маленький marker burst (`css-marker-patterns`) в момент произнесения.
Scene 3 (6.7–9.44s): На «остывшей пиццы» появляется таймер-пицца с одной уходящей паровой линией, микрофон и три плашки остаются как читаемая формула; hold без дальнейшей анимации.

## Frame 7 — Сделай главное

- scene: Чёрный финальный постер: три собранные карточки «БОЛЬ», «ДЕМО», «ПИТЧ» складываются в победный кубок; рядом подпись «НЕ ВСЁ. ГЛАВНОЕ.».
- voiceover: "Одна боль. Рабочее демо. Питч без героизма. Побеждает не тот, кто сделал всё, а тот, кто сделал главное."
- duration: 11.6s
- poster: 4.4s
- transition_in: crossfade
- status: outline
- src: compositions/frames/07-do-the-main-thing.html
- type: cta
- persuasion: Callback + distillation
- beat: Resolve + satisfaction
- blueprint: titlecard-reveal (Adapt)
- focal: финальная белая рамка с фразой «НЕ ВСЁ. ГЛАВНОЕ.»
- roles: финальная фраза = foreground subject; три мини-карточки = midground proof; кубок = supporting payoff; чёрный фон и розовая звезда = background/frame accent

narrativeRole: Возвращает зрителя к тезису и оставляет готовую ментальную модель.
keyMessage: Победная стратегия — намеренно ограничить объём и идеально показать главное.

Adapt: сохраняем единственное спокойное открытие карточки, но перед hold даём трём мини-картам сложиться в кубок — это визуальный callback ко всей стратегии.
Scene 1 (0.0–3.2s): На чёрном поле три маленькие карточки «БОЛЬ», «ДЕМО», «ПИТЧ» собираются в верхних двух третях по одной через короткий stagger-assemble (`center-outward-expansion`); розовая звезда остаётся в углу.
Scene 2 (3.2–7.0s): На «сделал всё» карточки scale-swap (`scale-swap-transition`) в один простой кубок; вокруг него появляется белая close-frame.
Scene 3 (7.0–11.6s): На «сделал главное» внутри белой рамки спокойным titlecard reveal (`scale-swap-transition`) появляется «НЕ ВСЁ. ГЛАВНОЕ.»; длинный неподвижный hold до конца, только маленькая звезда делает один конечный jitter.
