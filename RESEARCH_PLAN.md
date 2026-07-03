# RESEARCH PLAN — бэклог ресёрча (build-time)

> Что мы исследуем, чтобы фабрика принимала верные решения. Каждый пункт делегируется
> Gemini-саб-агенту через `gemini_agent.py` и сохраняется в `orchestration/research/`
> со ссылками на источники. Дешёвую модель — первой; `--search` — для всего, что про рынок.
>
> Статус: ✅ готово · 🔜 следующее (после ответов по стратегии) · ⏳ зависит от выбора ниши/монетизации.

## Уже собрано ✅
- `01_short_form_retention.md` — механики хуков, open loops, пейсинг, субтитры, ошибки retention.
- `02_wellness_safe_claims_pl_eu.md` — комплаенс БАД PL/EU: стоп-слова, EFSA-claims, плашки, GIS/UOKiK.
- `03_gemini3_prompting.md` — промптинг Gemini 3 + Nano Banana (JSON-схемы, temp, 9:16, консистентность).
- `04_2026_image_montage_update.md` — апдейт 2026: формула промпта, safe-зоны 9:16, цифры пейсинга.

## Приоритет 1 — экономика и выбор направления
- **R05. Валидация ниш под трафик ✅** → `05_niche_traffic_validation.md`. Ранжирование (трафик ×
  стек × монетизация): **1) Исторические факапы бизнеса (720), 2) Психология/когнитивные искажения
  (700), 3) Визуализация богатства/макроэкономика (640), 4) Спорт/здоровье (630, ред-оушен),
  5) Нейросети для начинающих (432, не evergreen)**. Рекомендация: пилот #1+#2, гео EN/global.
  ⚠️ **Уточнено R25**: с учётом реальной юнит-экономики психология/биасы дают более быструю тягу
  (широкая ЦА, короткий формат ок), а «факапы бизнеса» экономически тянет к 60+с (TikTok CRP) —
  см. R25 ниже, решение по итоговому приоритету пилота — за владельцем.
- **R06. Партнёрки/офферы PL/EU.** CPA-сети и affiliate-программы по wellness и смежным; ставки,
  правила, гео. → `06_affiliate_offers_pl_eu.md` (остаётся открытым — ниши сейчас EN/global, не PL/wellness).
- **R07. Пороги и правила монетизации платформ.** ✅ Частично закрыто через R25/R30 (YPP-пороги,
  TikTok CRP >60с, лимиты API). Отдельный полный свод пока не собирался.

## Приоритет 2 — производство и качество
- **R16. Контент-стратегия 3 ниш ✅** → `16_content_strategy_3niches.md`.
- **R17. Визуальный арт-дирекшн 3 ниш ✅** → `17_visual_artdirection_3niches.md`.
- **R08. Возможности hyperframes ✅** → решение в `ARCHITECTURE.md` §4.
- **R09. Темп TTS + музыка ✅** → закрыто через `26_tts_pacing.md` (Director's Notes + inline tags +
  atempo=1.15 гибрид) и `27_bgm_sfx_ducking.md` (Lyria-промпты + sidechain-ducking + LUFS).
- **R10. Консистентность визуала между кадрами ✅** → `29_nanobanana_consistency.md`. Важная находка:
  официальный лимит style-референсов Nano Banana 2 — **3 изображения**, у нас передаётся до 14
  (`paths[-14:]` в `engine.py generate_frames`) — это баг, не фича; менять на fixed-anchor+2.

## Приоритет 3 — дистрибуция и рост
- **R11/R12/R13/R14 объединены и закрыты ✅** → `30_distribution_publishing.md` (API-лимиты
  YouTube/TikTok/Meta 2026, анти-бан через OAuth vs эмуляцию, Unified API вместо самописной
  интеграции 3 SDK, feedback loop метрик → сценарист). Стадии 8-9 пока не реализованы (нужно
  разрешение владельца на публикацию), но архитектура решена.

## Медиапланы и айдентика (саб-агенты) ✅
- **R18/R19/R20. Медиапланы 30 дней + долгосрочная стратегия** по 3 каналам → `18_/19_/20_*.md`.
- **R21. Айдентика 3 каналов** → `21_channel_branding.md`.

## Сквозное — аудит пайплайна 2026-07-01 ✅
- **R22. Архитектура пайплайна целиком + сравнение с n8n** → `22_pipeline_architecture_n8n.md`.
- **R23. Retention-редактирование/пейсинг статичных AI-кадров** → `23_retention_editing_pacing.md`.
- **R24. QA-as-judge паттерны (blocking vs advisory)** → `24_qa_judge_patterns.md`.
- **R25. Юнит-экономика faceless-каналов ✅** (закрывает многолетний R15) → `25_unit_economics_faceless.md`.
- **R26. Темп Gemini TTS** → `26_tts_pacing.md`.
- **R27. BGM/SFX + sidechain ducking** → `27_bgm_sfx_ducking.md`.
- **R28. Word-level караоке-субтитры** → `28_wordlevel_captions.md`.
- **R29. Консистентность кадров Nano Banana 2** → `29_nanobanana_consistency.md`.
- **R30. Дистрибуция/публикация API-паттерны** → `30_distribution_publishing.md`.
- **R31. Надёжность оркестрации (retry/resume/идемпотентность)** → `31_pipeline_reliability.md`.
- Сводный отчёт и приоритизированный список улучшений → `32_pipeline_audit_summary.md`.

## Волна «направления и локальные пайплайны» 2026-07-02 ✅
Запрос владельца: новые ниши (собаки, варианты для Сергея, ИИ для дизайнеров), GTM для
продукта-валидатора гипотез, open-source стек под машины команды, универсальная стратегия.
4 deep-research + 2 pro+search + sonnet-саб-агент, параллельно.

- **R33. Ниша «собаки» ✅** → `33_niche_dogs.md`. Вердикт: заходить в поднишу **Dog Psychology**
  (гео US/Tier-1); квиз-паттерн БАДов переносится идеально; pet insurance CPA до $125,
  fresh food $50-60/продажа. Дрессировка и AI-rescue-истории — исключить.
- **R34. Ниши для Сергея ✅** → `34_niches_sergey_health.md`. Топ-2: **Longevity/биохакинг**
  и **фитнес-наука/метаболизм** (готовые хуки/темы/воронки). СДВГ в лоб — нет (YMYL+статика
  не работает), пивот → ноотропы/«оптимизация мозга». Детское здоровье — исключить.
- **R35. ИИ для дизайнеров ✅** → `35_niche_ai_for_designers.md`. GO с условием: разовая
  инвестиция в HTML-шаблоны UI вместо скринкастов; EN-only; Krea 25% RevShare, Figma-плагины
  до 40% recurring.
- **R36. GTM продукта-валидатора гипотез ✅** → `36_ai_validator_gtm.md` (+pro+search
  дополнение: конкуренты/позиционирование). One-off отчёт $39-49 (не подписка), лид-магнит
  квиз «Startup Viability Score», позиционирование «убийца потраченных месяцев» → «Evidence
  Engine», кросс-промо из biz_failures, план запуска на 7+ недель.
- **R37. Локальный open-source стек ✅** → `37_local_opensource_stack.md`. M3 Air 16GB:
  Ollama qwen2.5:7b + Draw Things Z-Image Turbo + Kokoro + whisper.cpp («строгая
  последовательность»); M4 Pro 48GB: qwen2.5:32b + FLUX.1-dev Q8 + IP-Adapter + Chatterbox V3
  («асинхронная фабрика»). Музыку локально не генерировать. Хендоффы для Codex →
  `orchestration/handoff/DEPLOY_NADYA_M3AIR.md`, `orchestration/handoff/DEPLOY_SERGEY_M4PRO.md`.
- **R38. Универсальная стратегия каналов ✅** → `38_universal_channel_strategy.md`. Метрика №1 —
  Viewed-vs-Swiped; правило 30 роликов; kill/pivot/scale-пороги; YT 30-40с vs TikTok >61с;
  анти-дедупликация кросспостинга; практики мультиоператорной фабрики.
- **R39. Аудит проекта-аналога ✅** → `39_creative_scheme_audit.md` (sonnet-саб-агент).
  `creative production scheme` — рабочая production-система (польский wellness): забрать
  cost_tracker, HTML/GSAP-обвязку, YouTube-паблишер, ThumbnailPlan/CreativeQA, OOM-ретрай.
- **R40. Сводка направлений ✅** → `40_directions_summary.md`: рейтинг портфеля, сквозные
  находки (переиспользуемый квиз-движок!), открытые вопросы владельцу.

---
**Как запускать (пример):**
```bash
python3 orchestration/gemini_agent.py --model pro --search \
  --system orchestration/roles/researcher.md \
  --task "R06: собери CPA/affiliate-сети для wellness в PL/EU: ставки, правила, гео, ссылки" \
  --out orchestration/research/06_affiliate_offers_pl_eu.md
```
Несколько независимых пунктов — параллельно (раннер в фоне, один процесс на задачу).
Каждый новый свод по завершении: краткий вывод в этот файл + при необходимости правка PLAYBOOK.
