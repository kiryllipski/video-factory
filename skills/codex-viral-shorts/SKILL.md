---
name: codex-viral-shorts
description: Create and optionally publish evidence-led but entertaining Polish VitalLogic YouTube Shorts when Codex must own the strategic choice, research synthesis, Polish scenario, metadata, and English image prompts. Use for high-upside Shorts experiments that need expressive character acting, varied shot scales, lively male narration, imagegen frame generation, visual and factual QA, and separate post-publish analytics.
---

# Codex Viral Shorts

Own the editorial decision. Use the built-in Codex imagegen tool for frame generation when the task requests imagegen; do not silently substitute Gemini/Nano Banana for images. Gemini is the required engine for Polish TTS: use the local `audio_agent.generate_speech` path (default model `gemini-3.1-flash-tts-preview`), not Kokoro or another TTS engine, unless the user explicitly asks. Gemini vision QA may still be used after Codex has written and reviewed all viewer-facing text and prompts.

## Non-negotiable rules

- Do not call `engine_v8.py --go`: it delegates research, script, visual plan, and metadata to Gemini.
- Start from channel evidence and current demand. A target such as 3k views is a hypothesis, never a guarantee.
- Write the Polish hook, every voice-over beat, on-screen text, image prompt, title, description, hashtags, API tags, pinned comment, and source-card finding yourself.
- Research health or nutrition claims from current primary or official sources. Link every meaningful claim, number, and practical rule to `claim_id`.
- Keep one Short to one tension, one reveal, and one immediately usable rule. Do not pad a 25–32 second story with extra claims.
- Separate evidence levels in strategy notes: `official`, `independent_dataset`, `vendor_case`, `community_anecdote`, and `hypothesis`. Never turn an external anecdote or benchmark into a hard release gate.
- Treat the approved ironic visual language below as a persistent house style for this project.
- Within one Short, use exactly one canonical hero description copied verbatim into every human-character image prompt. The hero may change between Shorts, but must not drift within a Short.
- Keep hero identity invariant but treat acting as variable: do not reuse one neutral face or one expression across the Short. Every human-containing frame must specify a distinct story-relevant emotion, gaze, mouth/eyebrow/eye state, and gesture. Adjacent frames must not repeat the same expression unless the repetition is an intentional visual joke.
- Use a clearly male Polish narrator for this channel by default (`VITALLOGIC_TTS_VOICE=Charon` in Gemini TTS unless the user explicitly selects another voice). The delivery must be bright, expressive, emotional, lively and conversational, with lightly ironic varied pitch and comic timing; it must not sound like a calm medical disclaimer or a flat audiobook.
- Write for a non-specialist, not for an internal medical chart. Do not use unexplained clinical abbreviations such as `LDL`, `ApoB` or `HbA1c` in voice-over, captions, posters, overlays, payoff cards, titles, descriptions or CTAs. Prefer a sourced everyday phrase; if the technical distinction is essential, explain it in plain language before using the abbreviation and keep the explanation in the same beat.
- Preserve the v8 gates. Build only a package that validates against `schemas_v8`, `engine_v8.script_errors`, and `engine_v8.plan_errors`.
- Prevent structural repetition, not only duplicate topics. Before authoring, inspect the latest 8 same-channel run packages (local runs plus the iCloud archive when needed). Do not repeat the same combination of format, hook mechanism, first proof, turn placement, evidence device, overlay sequence, and payoff device in adjacent releases. For a follow-up in the same topic family, change at least three of those dimensions. Record the chosen `structure_variation` and the compared runs in `codex_strategy.json`.
- Never upload, publish, schedule, reschedule, or otherwise change YouTube state unless the user gives a separate direct command for that action. Creating and validating a local MP4 does not authorize an upload. Before any explicitly authorized scheduling, inspect the live channel and confirm the requested slot is free.

## Editorial format selector

Treat format as the story's engine, not as a decorative label. Topic, rubric, and format are
separate decisions: research the broad topic first, assign the production rubric second, then
choose the format that makes the evidence easiest to understand and the joke easiest to see.
The canonical production pool below contains all fifteen approved formats. The priority is a
tie-breaker and a planning signal, not a quota.

| Machine format | Priority | Choose it when | Story skeleton | Ironic/entertaining engine |
|---|---:|---|---|---|
| `myth_autopsy` | P0 | A familiar belief can be tested honestly | claim → visible absurdity → origin → evidence → verdict | The myth behaves like an overconfident office expert; the joke targets the claim, not the viewer |
| `detective_case` | P0 | A strange everyday result has several plausible causes | result → suspects → clues → mechanism → rule | A kitchen/office object is wrongly accused before the real culprit appears |
| `timeline` | P0 | The effect unfolds over minutes, hours, days, or stages | t0 → time points → unexpected mark → practical result | Body or brain is treated like a calendar, release train, or overloaded ticket queue |
| `versus` | P0 | Two concrete options are being compared | A/B → 2–3 criteria → reversal → “what for whom” verdict | Two objects or habits hold a mock office debate; the winner is not obvious |
| `study_autopsy` | P0 | A new study or review is the actual news hook | headline → design → result → limitation → everyday meaning | Inflate the headline into a “major release”, then deflate it with sample, condition, or scope |
| `office_case` | P0 | The audience recognises a workday situation immediately | office scene → body/brain mechanism → one change → workday payoff | Screen, coffee, meeting, or deadline acts like a colleague under load |
| `number_shock` | P1 | One verified number is the clearest proof | expectation → household conversion → actual number → condition | Replace abstract units with spoons, cubes, minutes, glasses, or zł; never fake precision |
| `one_swap` | P1 | One small substitution is genuinely enough | default habit → one swap → mechanism → boundary | The workday's “default setting” is changed with one visible, slightly ridiculous switch |
| `mechanism_zoom` | P1 | The viewer needs to see what happens inside the body or brain | visible scene → visual zoom inside → one mechanism → action | Neurons or organs behave like a tiny office team; no horror, diagnosis, or magical anatomy |
| `self_test` | P1 | A safe observation can be done during the Short | safe action → observe → explain → boundary | A simple household check gets an over-serious lab treatment; it is never a diagnosis |
| `micro_experiment` | P1 | One variable can be changed or compared transparently | hypothesis → change one variable → observe/compare → caveat | A mug, timer, or sticky note becomes an absurdly formal laboratory |
| `tier_list` | P2 | Three to four options share one clear ranking criterion | criteria → reverse countdown → winner → conditions | Losing options receive readable comic reactions; “best” must be task-specific |
| `courtroom` | P2 | A disputed claim benefits from a two-sided frame | accusation → prosecution/defense → evidence → verdict | The belief is on trial; never put a patient, symptom, or real viewer on trial |
| `cause_chain` | P2 | Several supported steps connect a small choice to a workday result | small choice → mechanism → consequence → context | A domino chain of tickets, calendar blocks, or office objects; no catastrophe escalation |
| `comment_answer` | P2 | A real or recurring viewer question is the strongest entry point | question → direct answer → one nuance → rule | Warmly dramatise the everyday misunderstanding; never mock the person asking |

### Format choice procedure

After the research ledger is accepted and before writing the full Polish script:

1. Propose three candidate formats from the table. Reject any format whose proof type is absent:
   no `number_shock` without a verified number, no `study_autopsy` without a study, no
   `self_test` without a safe observable action, and no `versus` without two real alternatives.
2. Score each candidate from 0–2 for `topic_fit`, `visual_conflict`, `evidence_fit`,
   `irony_potential`, and `payoff_clarity`. Select the highest total; use the higher priority
   only when totals are tied. If the winner is P2, state why a P0/P1 format was weaker.
3. Put the selected machine name in `script.format` and record this decision in
   `codex_strategy.json`:

   ```json
   "format_selection": {
     "format": "detective_case",
     "priority": "P0",
     "reason": "The visible result has three plausible household causes and the label is the first proof.",
     "comic_engine": "The coffee mug is interrogated before the sleep debt is revealed.",
     "discarded_alternatives": ["number_shock", "study_autopsy"]
   }
   ```

4. Do not let a high-priority format override the research. Use `label_check`, `basket`,
   `anti_sell`, `escalation`, or `mistake` only as specialised compatibility formats when the
   topic genuinely requires them; they are not part of the fifteen-format default pool.

### Entertainment gate for every format

The format is not delivered unless the Short has all of these properties:

- a concrete visual conflict or comic action in the first 1.2 seconds, readable with sound off;
- the first evidence/proof by 4 seconds, not only a promise to explain later;
- one visible ironic reversal in the middle and one concrete payoff before the final 3 seconds;
- at least one changing shot scale or environment when the viewer question changes;
- a joke aimed at a myth, marketing claim, office absurdity, or object behaviour — never at illness,
  disability, anxiety, body shame, or a person asking a question;
- literal, sourced health claims underneath the joke, with no invented study result, diagnosis,
  treatment promise, or alarmist escalation.

If the topic is interesting but cannot support a visible conflict and a clean payoff, keep it in
the research backlog instead of forcing it into a format.

## Editorial workflow

1. Diagnose the opportunity.
   - Compare Shorts at the same age: `Shown in feed → chose to view → average percentage viewed → shares/subscribers per 1k`.
   - Use the channel's past outliers and fresh Poland demand signals as separate inputs. Prefer a topic only when both signal a broad, recognisable audience or the potential gain justifies an experiment.
   - Choose a distribution lane: `feed`, `search`, or `hybrid`. For `search`/`hybrid`, record the actual Polish primary query and secondary queries. For `feed`, record the viewer promise instead of inventing a keyword target.
   - Define a falsifiable hypothesis, e.g. `visible household-unit comparison will lift average percentage viewed above 75% without reducing chose-to-view below 50%`.
   - Define a structural signature before drafting: `hook_mechanism`, `first_proof`, `turn_device`, `evidence_device`, `overlay_sequence`, `payoff_device`, and `visual_rhythm`. Compare it with the latest eight releases. A new topic is not enough if its story skeleton would feel like the same Short again.
   - Run the editorial format selector above. Choose the best-fitting format after the evidence
     is known, not before. Record the candidates, scores, selected priority, reason, and comic
     engine in `codex_strategy.json`.

2. Choose and research the idea.
   - Prefer a familiar Polish object, a consequential choice, and a visible proof: a glass, spoon, receipt, package line, timer, plate, or comparison.
   - Build a compact research ledger with 3+ sources, 4+ claims, permitted wording, limitations, and rejected overclaims.
   - Source current product numbers from the labelled product or an official database; do not convert a general statistic into a fake product-specific fact.
   - Treat external hook/metadata research as strategy evidence, not health evidence. Keep health claims on current primary or official sources.

3. Write before generating media.
   - Create a Hook Lab with 3–5 materially different Polish openers. Record each hook, poster, first visual, hook type, first proof time, claim IDs, and a short score/rejection reason. Select one variant before writing the full script; render a second variant only as a controlled experiment.
   - Make the first frame understandable with the sound off: the object, result, or conflict must be visible immediately. Synchronise first visual, first word, poster, and audio accent around one promise.
   - Use 9–12 beats for the default 25–32 second format. Put the hook in 0–2s, action/proof in 2–10s, progression or escalation in 10–24s, and the concrete payoff in the final 3–6s. The middle must add evidence, a contrast, or a changed viewer question; it may not paraphrase the hook.
   - Make the selected format structurally visible: the first beat establishes its conflict,
     the middle performs its proof/reversal, and the payoff resolves the exact question promised
     by the format. Do not use the same generic `mistake → fix` arc under a new label.
   - For a 15-second test use one idea and one payoff. Use 45–60 seconds only when the evidence needs a real arc; record duration as an experiment variable rather than a universal rule.
   - Keep spoken sentences short. The payoff is a concrete rule, not a generic CTA. Put a natural binary prompt in the pinned comment after publication.
   - Treat every number as one complete evidence event: say the measured object, number and unit in the same natural sentence (for example, `duże jajko ma około 186 mg cholesterolu`, never a dangling `około 186 miligramów`). Put its deterministic number overlay in that same beat, entering with the spoken number or within 0.5 seconds after it. Do not break a grammatically unfinished thought across separately generated TTS beats; either finish the sentence before the cut or write an explicit continuing connector.
   - Plan at least three meaningful visual events in the first six seconds. Adjacent shots must change scale, evidence, or viewer question.
   - Build an emotion arc before writing image prompts. Map each beat to an emotion that supports the line: e.g. suspicious curiosity in the hook, overconfident comic certainty before the reveal, surprise at the evidence, awkward caution at the limitation, knowing relief at the rule, and a warm but serious safety finish. Name the emotion and acting direction in `visual_cue` and in the English prompt.
   - Use at least four shot scales across a normal 9–12-frame Short, selected from the v8 schema (`extreme_macro`, `macro`, `medium`, `wide`, `abstract`). Do not use the same scale for more than two adjacent frames. Change scale when the story changes from reaction to evidence, from evidence to metaphor, or from rule to safety.
   - Allow controlled comic absurdity: exaggerated but readable reactions, awkward office objects, visual misdirection, and slightly ridiculous metaphors are welcome when they reinforce the spoken claim. Keep the health claim itself literal, sourced, and non-alarmist; the joke must not invent evidence or imply a treatment.
   - Write English 9:16 image prompts that describe evidence and composition, not decorative filler. Each frame must make one claim when viewed silently.
   - Treat the YouTube Shorts UI as occupied space. For a 1080x1920 frame, keep irreplaceable faces, objects, evidence, labels, and planned readable in-image text inside the prompt-safe core: x=120..860 and y=200..1500. The right rail (x=860..1080, especially y=420..1560) and lower band (y=1540..1920) may contain only decorative or expendable background. The renderer owns captions and source cards; do not put a second thesis under them.
   - Every prompt must name the shot scale, composition center, eye path, emotion, gaze, gesture, and safe-area decision: what is sharpest/largest, where the hero is looking or gesturing, what is de-emphasized, and how the viewer moves to the next beat.

4. Hydrate the v8-compatible package.
   - Create `research_pack.json`, `script.json`, `compliance.json`, `fact_review.json`, `frame_plan.json`, `qa.json`, `publish_package.json`, and `codex_strategy.json` in a new run directory.
   - Use `references/artifact-contract.md` for the exact contract and commands.
   - Record `authored_by: "Codex"` in `codex_strategy.json`; it is an audit marker, not a performance claim.
   - Record `distribution`, `hook_lab`, `format_selection`, `structure_variation`, and optional `series` objects in
     `codex_strategy.json`. If the idea is part of a follow-up cluster, record the series ID,
     episode, and next two or three angles.
   - Run the deterministic check:

     ```bash
     python3 skills/codex-viral-shorts/scripts/check_package.py autopilot_factory/runs/<channel>/<run>
     ```

5. Generate, render, and review.
   - If the user requested imagegen, read the `imagegen` skill and generate every frame with the built-in imagegen tool, one frame/variant at a time. Inspect the outputs, copy accepted images into the run's `frames/` directory, and write `media_manifest.json` with ordered paths, SHA-256 hashes, `built_in_imagegen` provenance and approval for every frame. Assemble only from those manifest-approved files. Do not invoke a media command that silently regenerates the frames through Gemini.
   - Invoke only the media stage:

     ```bash
     cd autopilot_factory
     VITALLOGIC_TTS_VOICE=Charon \\
     python3 engine_v8.py --build runs/<channel>/<run> --asset-channel vitallogic_bad_pl
     ```

   - Require release gate pass, 1080×1920 H.264/AAC, readable poster/subtitles/source cards, and manual review of the first-frame, reveal, source-card, and payoff screenshots. During that review, verify that every spoken number names its object and unit, the matching overlay appears in the same beat, no word is split or hyphenated by the renderer, no important visual element sits under the right-side Shorts controls or bottom UI, and no cut leaves a sentence with an accidental terminal cadence. Record planned versus actual MP4 duration for pacing diagnosis, but never block release solely because a strong story runs a little longer or shorter than its beat plan.
   - Fix the smallest causal defect, then rerun the failed gate. Do not publish a merely technically valid but visually confusing Short.

6. Publish.
   - Treat publishing as a separate gated stage. Stop after local generation and QA unless the user explicitly says to upload/schedule this video now.
   - Check the live channel identity and occupied slots immediately before upload.
   - Schedule exactly the user-authorized slot using private scheduled status. Confirm the returned video ID, URL, privacy, and `publishAt` from the API response.
   - After publication, hand off to the separate analytics instruction. Do not mix post-publish diagnosis into the production decision unless the user explicitly asks for a combined review.

## Controlled growth experiments

- For a plateaued, low-search video, test one title or description refresh after 48–72 hours. Do not touch winners and do not change title, description, hook, and cadence at once.
- When a Short is an outlier, prepare 2–3 honest follow-ups in the same topic family within 24–48 hours. Use Related Video, playlists, and real viewer questions; do not seed fake comments or upload near-duplicate spam.
- Keep visible hashtags small and relevant. `hashtags` are not the same field as API `tags`; use API tags only for a small Search-lane experiment and never keyword-stuff either field.
- Do not use bots, fake engagement, engagement pods, mass duplicate reuploads, deceptive metadata, forced incomplete loops, or attempts to evade platform disclosure/policy systems.

## Separate analytics mode

Analytics is a post-publish workflow, not a production step. When the user asks to analyse channel or video performance, first read [`references/analytics.md`](references/analytics.md). It defines the 24-hour/7-day cohort, Feed/Search split, raw versus engaged views, diagnosis matrix, and experiment log. Do not use analytics benchmarks as automatic script gates.

## Targets for a high-upside 25–32 second test

- Chose to view: 50% floor; 55% target.
- Average percentage viewed: 75% floor; 80% target.
- Likes: 3% floor; 5% target.
- Shares and subscribers: positive per 1k engaged views.
- Zero unsupported claims, zero clipped viewer text, and zero generic scenes that could belong to another Short.
- These are internal test targets, not universal YouTube thresholds. Compare against the last 10–20 same-format Shorts and report sample size and age.

## Resources

- `references/artifact-contract.md` — v8 package requirements and safe build/publish commands.
- `references/analytics.md` — separate post-publish cohort analysis and learning protocol.
- `scripts/check_package.py` — local Pydantic and deterministic-gate validation for a Codex-authored package.

## Approved ironic style bible

Use this as the default creative language unless the user explicitly overrides it:

- Tone: relaxed, lightly sarcastic, observant and useful; office/IT metaphors such as stand-ups, tickets, releases, scope creep and night deployments; never alarmist, preachy or mean.
- Performance: entertaining first contact, with dry one-liners, playful overconfidence, quick reversals, comic pauses, and small visual jokes. The tone can be a little silly and ironic while the evidence remains precise.
- Viewer: Polish office workers and IT people who want an easy, entertaining explanation during a break. The information is evidence-led, but the delivery feels like a small comic sketch.
- Visual world: bright pastel 2D hand-drawn cartoon, thick black ink contours, flat cel shading, rounded organic shapes, candy-colored office merged with a whimsical wellness/fantasy environment; cyan, lemon, mint, pink, lilac and warm cream dominate.
- Composition: one obvious focal point per frame. State it explicitly in each prompt as `COMPOSITION CENTER`; use size, contrast, gaze, gesture, leading lines and empty space to direct attention. Do not let props, background decoration or generated lettering compete with the center.
- Shot rhythm: alternate extreme close-up, macro evidence, medium acting and wide metaphor. Adjacent frames must change scale, evidence or viewer question. The hook receives the highest visual density and fastest cuts. Do not create a slideshow of identical medium portraits.
- Hero continuity: define one original adult character with a short immutable identity descriptor, then paste that descriptor unchanged into every prompt containing the hero. Repeat outfit, hair, face, age, accessories and palette, but vary expression, gaze, posture, gesture, crop and camera distance per beat. Identity continuity is not expression continuity.
- IP safety: do not use or resemble Adventure Time/Finn or any other recognizable franchise character. Never use animal-ear hoods, white Finn-like hats, fantasy-hero silhouettes or copied facial design. Prefer an ordinary adult office/IT worker with an original silhouette and practical clothing; product brands and logos may appear when the storyboard calls for them.
- Text rendering: renderer-added captions, overlays and source cards remain deterministic, but the source image is allowed to carry intentional, readable content when the storyboard needs it. There is no blanket ban on text in labels, packaging, phones, monitors or tablet screens. Permit short printed labels, product names, ingredient lines, measurement marks, brand names, logos and planned device content such as a small UI, timer, pictogram, progress ring, chart-like shape or short heading; preserve planned wording and brand marks without distortion. Do not blank or remove a label/screen merely because video text will appear above the frame; instead reserve a safe area and avoid an exact duplicate or a competing second thesis. Keep embedded content short and legible. Forbid only random fake lettering, dense unreadable copy, floating AI captions and watermarks. `Completely unmarked` applies only to props intentionally chosen as neutral background elements.
- Viewer-text contrast: never reduce opacity of captions, numbers, versus values, versus labels, source-card text or other critical viewer-facing copy to make a layout fit. Preserve full text opacity; create hierarchy with font size, weight, spacing and position. If text collides or is too wide, shorten it or reduce its size/line count first, then rerender and inspect the frame. A losing comparison value may be smaller, but it must remain fully readable.
- Research-card composition: a source/research card is an editorial layer, not a full-frame scrim. Show the actual source title/publisher/domain directly; do not add a generic Russian `Источник`/Polish `Źródło` label. Make the card broad enough to read on a phone and place it slightly above center, leaving a visible lower or side area for the case visual. Keep the underlying image recognizable: use only a light vignette/contrast treatment, never blanket-darken the entire frame under the card. Inspect the source-card screenshot with the card visible and the key visual still identifiable.
- Evidence-limitation visuals: when the line says a study was small or controlled, use one unambiguous visual metaphor such as a neat small participant grid, clipboard, two clearly separated control/intervention groups, or a tiny lab setup. Do not combine unrelated props (for example, a party horn, magnifying glass and random tokens) unless the spoken joke explicitly requires all of them; the viewer must understand “small controlled study” without narration.
- Hook template for list-like topics: split the opening into separate close-ups rather than one overview frame. Example structure: word 1 + hero action, word 2 + hero action, word 3 + hero action, then the ironic reframe. Each opening frame must have a single composition center and a distinct emotion.
- Binary-choice hook: make both alternatives concrete in the first visual, not merely a generic fork, clock or abstract gesture. Put the recognizable object/action for option A and option B in frame at once (for example, post-meal sofa and plate versus walking shoes and path), then let the hero’s gaze or gesture choose a side. The poster and first spoken line must name the same two alternatives.
- Storyboarding rule: every visual must support the spoken sentence. Use the hero as narrator with an intentional look, hand gesture or reaction whenever an abstract claim needs a human anchor. A frame is incomplete if it has the same face, same scale and same emotional state as its neighbors without a deliberate comic reason.
