# VitalLogic Shorts analytics

Use this instruction only after a Short has been published or when the user explicitly asks for a channel/video performance analysis. It is deliberately separate from the production workflow: analytics diagnoses the result and chooses the next experiment; it does not rewrite the already approved script retroactively.

## Required context

Before interpreting a result, record:

- video ID, title, run, pipeline version, distribution lane, series ID/episode, and publish time;
- age of the video at measurement (`24h` or `7d`), timezone, and source export/API readback;
- duration, language, topic family, title template, description template, hook variant, and whether it was a follow-up;
- comparison set: the last 10–20 Shorts with the same language, approximate duration, lane, and age.

Never compare a fresh Short with a 7-day-old outlier without stating the mismatch.

## Metric order

Read the viewer path in this order:

1. `Shown in feed` — did the platform provide a meaningful test?
2. `Chose to view` / `Stayed to watch` / viewed-vs-swiped — did the first frame and promise stop the scroll?
3. `Engaged views` and average view duration — did viewers stay beyond the initial decision?
4. `Average percentage viewed`, completion, and retention drops — did the script progress and pay off?
5. Shares per 1k engaged views — did the idea feel useful or worth forwarding?
6. Subscribers per 1k engaged views — did the Short create a reason to expect another episode?
7. Search versus Shorts Feed share — did the selected distribution lane work?

Log raw public views and engaged views separately. Raw Shorts views can include starts/replays under the current counting model; engaged views are the safer comparison field when formats or publication dates differ.

## Diagnosis matrix

| Pattern | Primary hypothesis | Next test |
|---|---|---|
| Low `Shown in feed` across several same-format videos | topic demand, competition, lane, or channel-level distribution issue | test a different demand signal or Search-native packaging; do not rewrite the script first |
| Normal feed exposure, low chose-to-view | first frame, first words, poster, or promise is weak | change one opening variable; keep body and topic fixed |
| Good chose-to-view, sharp early retention drop | promise mismatch or opening does not deliver evidence | move result/proof earlier; remove greeting and setup |
| Good first 3–6 seconds, middle drop | repetition, no escalation, decorative visual, or too many claims | remove one beat and add a new comparison/evidence event |
| Good retention, low shares/subscribers | useful but not memorable, unclear channel promise, or weak follow-up path | strengthen the practical rule, series connection, or real pinned question |
| Good Feed metrics, weak Search share | Search lane was not actually packaged for a query | test exact query in title, first description lines, and first spoken answer |
| Good Search share, weak chose-to-view | query is relevant but the opener is not compelling | keep query, replace first frame/hook |
| One outlier beats the median | topic/angle may have demand worth clustering | publish 2–3 distinct follow-ups within 24–48 hours; do not copy the video frame-for-frame |

## Experiment discipline

- Change one principal variable at a time: first frame, spoken hook, title, description, lane, duration, or series follow-up.
- Do not conclude from a single video. Mark the result as `directional` until the matched set has enough comparable entries.
- Do not attribute a result simultaneously to topic, retention, cadence, and metadata.
- Treat creator posts, vendor case studies, and small scrapes as hypotheses. They may suggest a test but cannot create a hard threshold.
- Keep a control where practical. For example, compare a Feed-native and Search-native title on two otherwise matched topics rather than changing the whole channel strategy.

## Gray but reversible actions

- Refresh the title or first description lines of a plateaued, low-search video after 48–72 hours; log the before/after package and do not touch a winner.
- Follow a genuine outlier with related episodes and a Related Video link.
- Use real comments as demand research and answer them with a new Short.
- Test a second opening frame or voice-over only in a separately identified upload or supported native experiment.

Do not use fake engagement, bots, engagement pods, mass duplicate uploads, keyword stuffing, fake comments, or incomplete loops designed only to manufacture replays.

## Required report

Return:

1. cohort and comparison set;
2. raw views and engaged views;
3. Feed exposure, chose-to-view, retention, shares/1k, subs/1k, Search share;
4. one primary diagnosis and the evidence for it;
5. one next experiment with the changed variable, control, success criterion, and stop condition;
6. unresolved verification gaps.

The local CSV report remains useful for weekly summaries:

```bash
python3 orchestration/analytics_report.py "<YouTube Studio export>" \
  --out orchestration/research/<date>_analytics.md
```

That report is a measurement aid, not a substitute for age-matched diagnosis.
