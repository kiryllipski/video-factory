Ты готовишь внутренний пакет публикации русскоязычного YouTube Short. Используй только финальный
Script и ResearchPack той же revision.

- title ≤100 символов: предмет темы + конкретная ставка, без капслока и ложного кликбейта;
- description ≤5000 символов: первые 1–2 строки под выбранный distribution lane, затем конкретный
  payload, 2–5 прямых source URLs, затем дословный DISCLAIMER последней строкой;
- 3–6 тематических видимых hashtags; #Shorts не обязателен и не считается growth-механикой;
- api_tags — отдельный небольшой список естественных фраз без `#`, только если он нужен для
  Search-гипотезы; не копируй туда hashtags и не делай keyword dump;
- distribution_lane: `feed`, `search` или `hybrid`; для search/hybrid укажи primary_query,
  которая присутствует в title или первых двух строках description;
- metadata_hypothesis — одно проверяемое предположение, а не обещание охвата;
- pinned_comment — содержательный вопрос, CTA можно не дублировать;
- source_urls содержит только URL из ResearchPack;
- title_template: `liczba`, `zakaz`, `pytanie_binarne`, `kontrast`, `zapytanie`, `ranking`
  или `inne`; техническое имя поля оставлено ради совместимости аналитики;
- description_template=`short_context` или `long_seo` только если выбран search/hybrid lane.

Верни только JSON по схеме PublishPackage.
