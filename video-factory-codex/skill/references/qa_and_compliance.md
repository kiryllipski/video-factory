# qa_and_compliance — комплаенс и QA (делает Claude)

Оба гейта Claude выполняет сам. Комплаенс (стадия 4) может ПРАВИТЬ сценарий; QA (стадия 7) —
только фиксирует выводы и не блокирует продакшен. Источники: `research/02_wellness_safe_claims_pl_eu.md`
(YMYL/БАД), `research/24_qa_judge_patterns.md`, `research/01` (ретеншен), studio_context канала.

---

## Комплаенс → `compliance.json` (схема `ComplianceVerdict`)

Формат:
```json
{
  "passed": true,
  "fixes": ["что заменили и почему — по одной строке на правку"],
  "cleaned_script": { "...полный объект Script..." }
}
```
- Если всё чисто: `passed=true`, `fixes=[]`, `cleaned_script` = исходный сценарий без изменений.
- Если правил: `passed=false` (или true с правками), внеси **минимальные** правки прямо в `cleaned_script`,
  перечисли их в `fixes`. Дальше пайплайн использует `cleaned_script`.

Что проверяешь (в порядке важности):
1. **Стоп-листы канала** из studio_context. Никаких мед./фин. обещаний, если канал YMYL.
2. **YMYL (finance/health, напр. wealth_viz):** только образовательные формулировки, без гарантий доходности
   и мед. эффекта; обязательная плашка-дисклеймер, если канал её требует (см. studio_context).
   Для БАД/wellness (PL/EU) — БАД это еда, не лекарство: запрещены `leczy/zapobiega/choroba/ból/terapia`,
   пользу — только авторизованными EFSA-claim'ами, обязательна плашка «Suplement diety», без «белых халатов».
   Полный свод — `orchestration/research/02_wellness_safe_claims_pl_eu.md`.
3. **Факт-чек:** имена/суммы/даты/события правдоподобны и не выдуманы. Для древних/спорных историй —
   «by some estimates / according to some accounts / circa», без выдуманной точности (см. biz_failures §7).
4. **Товарные знаки/лица:** нет призыва воспроизводить действующие бренды/реальных живых лиц вне public-domain;
   исторические — ок.
5. **Хук ↔ тело:** хук не обещает того, чего нет в теле (анти-clickbait).
6. **Тон** соответствует studio_context.

---

## QA → `qa.json` (схема `QAReport`) — advisory, НЕ блокирует

Формат:
```json
{
  "passed": true,
  "checks": [ { "name": "hook_strength", "passed": true, "detail": "" } ],
  "notes": ["1–5 коротких конкретных замечаний на будущее"],
  "blame_stage": ""
}
```
Оцени сценарий (`cleaned_script`) + `frame_plan` по чек-листу — по одному `QACheck{name,passed,detail}` на пункт:
- `hook_strength` — хук цепляет в первые 1–3 сек, без приветствий.
- `hook_match` — обещание хука раскрыто в теле (нет clickbait-drop).
- `pacing` — биты 1.5–2.5с; нет запланированной статики >3с (проверь `motion`/`dur_s` кадров).
- `caption_len` — `on_screen_text` 2–4 слова, safe-зона (нижняя треть).
- `visual_consistency` — единый grade/light/lens во всём FramePlan; кадров = битов, порядок совпадает.
- `open_loop` — есть петля/мостик, удерживающий внимание (~10–12с).
- `cta` — есть внятный CTA (save/share).
- `compliance_flags` — нет мед./фин. обещаний вне правил канала; для YMYL — дисклеймер присутствует.

Правила вывода:
- `passed=true`, если критичных провалов нет (это подсказка, а не блокировка).
- `blame_stage` — куда бы вернуть при желании доработать: `scriptwriter` | `visual` | `assembly` | `""`.
- Пиши честно, но не блокируй прогон. Если видишь дешёвую правку — лучше внеси её в артефакт до build_media.
