# VitalLogic v9 Retention Sprint

Status: approved implementation plan  
Owner: Codex  
Channel: `vitallogic_bad_pl`  
Sprint size: 12 published Shorts  
Production base: Codex-authored Polish scripts + built-in OpenAI ImageGen frames

## Objective

Keep the new visual/editorial identity that raised `Stayed to watch`, while improving depth of
viewing after the initial decision. The sprint is not a promise of viral distribution. It tests
whether measured, shorter storytelling can preserve appeal and materially raise AVD/APV and
satisfaction signals.

Primary funnel:

`Shown in feed -> Stayed to watch -> Engaged views -> AVD/APV -> shares/subscribers`

The working diagnosis is that the first frame is no longer the main bottleneck. Recent v8 scripts
planned 25.4-30.7 seconds but rendered at 38.4-58.4 seconds. The v9 sprint therefore treats actual
TTS and MP4 timing as release data, not as a note.

## Fixed production foundation

- Codex owns topic choice, evidence synthesis, Hook Lab, Polish script, metadata and English image
  prompts.
- Built-in ImageGen produces every approved source frame; no silent image-model substitution.
- Gemini Charon remains the default Polish narrator.
- Existing evidence, compliance, media-manifest, safe-area, caption and source-link contracts stay.
- YouTube upload, scheduling, publication and rescheduling remain a separate user-authorized stage.

## Duration lanes

| Lane | Planned actual MP4 | Word target | Story contract |
|---|---:|---:|---|
| `core` | 18-24 s; hard ceiling 26 s | 40-55; hard ceiling 60 | one conflict, one proof, one turn, one rule |
| `deep` | 28-35 s; hard ceiling 35 s | 30-60 at natural TTS speed | one conflict, two evidence events, one turn, one rule |

No v9 Short may exceed 35 seconds. No 45-60 second Short enters this sprint; a later long-form
lane needs its own evidence.

## Actual-timing gates

- Combined hook ends by 3.2 s.
- First proof starts by 3.0 s and maps to accepted evidence.
- Turn starts by 45% of actual narration time.
- Payoff starts by 78% of actual narration time.
- No generic spoken CTA after the payoff; the viewer question belongs in the pinned comment.
- Actual narration and MP4 must be within `max(2 s, 8%)` of the declared target.
- Core beats cannot exceed 4.2 s; deep beats cannot exceed 5.0 s.
- Exact recurring scaffolding such as `I tu zwrot:` and `Werdykt:` is rejected during the sprint.

TTS preflight runs before ImageGen. A failed timing report sends the script back to editing before
frames are generated.

## Cadence: 1-4 public Shorts per day

The owner may choose any daily count from one to four. Cadence is recorded as an experimental
context, not treated as an algorithmic growth rule.

- Minimum planned public gap: four hours.
- Every run records `publications_today`, `slot_index` and `minimum_gap_hours`.
- Compare like with like: a slot-4 result is not judged against a single-release day without
  stating the mismatch.
- When two to four Shorts publish in a day, topics and creative fingerprints must be visibly
  different; do not release a block of interchangeable courtroom/detective stories.
- Production may run ahead, but publishing still requires a separate direct command.

Suggested Warsaw slot families when four releases are explicitly authorized: `06:00`, `11:00`,
`16:00`, `21:00`. Fewer-release days use a subset chosen against live occupied slots. These are
operational defaults, not claims about ranking.

## Twelve-position creative rotation

Topics are selected from fresh demand and evidence. The table fixes the creative grammar, not the
health claim.

| # | Lane | Story engine | Proof/media mode | Anti-template requirement |
|---:|---|---|---|---|
| 1 | core | `comment_answer` | direct object demonstration | no courtroom, no verdict stamp |
| 2 | core | `versus` | macro A/B evidence | both alternatives visible immediately |
| 3 | core | `office_case` | relationship sketch | named character action, no study card in hook |
| 4 | deep | `mechanism_zoom` | kinetic diagram + ImageGen world | no recurring office protagonist |
| 5 | core | `micro_experiment` | timer/household test | observable action by 3 s |
| 6 | core | `myth_autopsy` | result-first cold open | answer before origin story |
| 7 | deep | `timeline` | time-state transformation | no detective vocabulary |
| 8 | core | `one_swap` or `label_check` | packaging/macro proof | real decision, not abstract lecture |
| 9 | core | `detective_case` | non-office object mystery | wrong suspect resolved before midpoint |
| 10 | deep | `study_autopsy` | design/result/limitation | source is the story, not a decorative card |
| 11 | core | `number_shock` | household conversion | one number only |
| 12 | adaptive | winning mechanism follow-up | different protagonist and payoff | change at least three high-salience axes |

## Creative fingerprint

Every v9 run declares and validates:

- hook family;
- protagonist mode;
- story engine;
- proof device;
- environment;
- edit grammar;
- payoff device;
- TTS delivery mode;
- at least eight compared recent runs;
- at least three changed high-salience axes.

Brand invariants remain stable: evidence quality, Polish voice identity, caption system, visual
quality and the broad bright 2D world. Story mechanics must rotate. Personified
courtroom/detective/office stories should not occupy more than two of five adjacent sprint slots.

## Measurements

Capture at `1h`, `6h`, `24h`, `72h` and `7d` where available:

- public views and engaged views separately;
- shown in feed and stayed to watch;
- AVD and APV;
- likes, shares and subscribers per 1,000 engaged views;
- traffic source;
- daily release count, slot and gap from the previous public Short.

Internal sprint success targets, not YouTube-wide thresholds:

- median `Stayed to watch >= 60%`;
- core median `AVD >= 18 s` and `APV >= 75%`;
- no more than five percentage points of appeal loss versus the matched recent cohort;
- positive movement in shares/subscribers per 1,000 engaged views;
- at least 20% AVD improvement over a duration-matched current baseline.

After the first six Shorts, choose positions 7-12 using actual 24h/72h results. Do not rewrite the
conclusion to fit a single outlier.

## Stop conditions

- Any unsupported or over-broad health claim.
- Failed ImageGen visual approval or manifest mismatch.
- Failed actual-timing or final visual gate.
- Release package with `release_gate.passed != true`.
- A supposedly new run whose creative fingerprint changes fewer than three high-salience axes.
- Any YouTube mutation without a separate direct instruction.

## Execution log

All release-state rows below are live `videos.list` readbacks, not uploader logs. Times are UTC
unless explicitly labelled otherwise.

| Sprint position | Run / mechanism | YouTube ID | Requested schedule | Latest confirmed live state |
|---:|---|---|---|---|
| 1 | `2026-08-26_v9-dziesiec-tysiecy-krokow` / `comment_answer` | `8nHrN7550OE` | 2026-08-27 04:00 | Read at 2026-08-27 07:15: public, processed, HD, `PT19S`. |
| 2 | `2026-08-26_v9-mleko-czy-owsiany` / `versus` | `QLhk9gtOo2E` | 2026-08-27 09:00 | Read at 2026-08-27 07:15: public, processed, HD, `PT20S`; `publishAt` was null, so the precise release-time discrepancy is unresolved. |
| 3 | `2026-08-27_v9-maja-piec-minut-ekranu` / `office_case` | `jYHeKDjZOH4` | 2026-08-27 14:00 (16:00 Warsaw) | Read at 2026-08-27 07:17: private and scheduled; processed successfully in HD, `PT22S`. |

Position 3 passed the local v9 release gate before upload: 21.607 s actual duration, 54 words,
approved ImageGen manifest (9/9 frames), first proof at 2.643 s, turn at 7.662 s and payoff at
13.829 s. The channel API reported `containsSyntheticMedia: null` after upload; this does not
confirm server-side disclosure and remains an explicit follow-up item.
