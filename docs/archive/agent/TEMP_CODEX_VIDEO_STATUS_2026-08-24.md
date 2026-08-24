# Codex video production — temporary working status

Updated: 2026-08-24

## Current target

Codex owns research, Polish editorial decisions, scenario, metadata and image prompts. Visual frames use the built-in `imagegen` skill; Gemini stays only where a local deterministic alternative is not appropriate, primarily TTS and optional semantic vision QA. Assembly, captions, source cards, codecs, manifests and logs remain local.

## Active pilot

| Field | Decision |
|---|---|
| Topic | `Baton proteinowy po treningu: paliwo czy droga czekolada?` |
| Structure | A comic mini-trial: the goal of the workout, the ingredient list and ordinary food act as witnesses; the ending rejects both automatic praise and automatic ridicule of the bar. |
| Voice | Natural, lively conversational Polish: short phrases, small pauses and light irony, never a textbook or advertisement. |
| Production boundary | ImageGen frames plus local package/assembly/QA. Gemini is allowed only for TTS if required. No YouTube upload, scheduling or publisher-log mutation. |
| Acceptance | Current evidence, recorded structural variation, approved frame review, `check_package.py`, final local QA and an explicit report of any unresolved blocker. |

## Architecture snapshot

| Layer | Owner/tool | Where it runs | Rule |
|---|---|---|---|
| Research, hook, scenario, metadata | Codex + current primary sources | Codex / web | Do not use `engine_v8.py --go` for Codex-authored work |
| Frame generation | Built-in `imagegen` | External image model | One inspected and accepted image per frame; keep important content inside the Shorts prompt-safe core |
| Voice | `orchestration/audio_agent.py` / Gemini TTS | External TTS | Gemini is used for voice, not for editorial writing |
| Captions, cards, animation, codec | `assembly_v7.py`, HyperFrames, ffmpeg | Local | Viewer text is deterministic and word-safe |
| Technical QA | `check_package.py`, release gate, ffprobe | Local | Required before any publication decision |
| Semantic visual QA | Gemini Vision | External, targeted | Use after local checks only when a visual question remains |
| Upload and scheduling | `publishers/youtube.py` | YouTube API | Separate direct user command only |

## Known implementation gap

`engine_v8.py --build` still calls the legacy Gemini image path through `V7.generate_frames`. This contradicts the Codex imagegen route and is deliberately the next implementation item below; until it is replaced, a Codex agent must not invoke that build command after creating imagegen frames.

## Context routing

| Task mode | Load | Do not load unless needed |
|---|---|---|
| Research / media plan | editorial rules, channel history, analytics | image generation, assembly, YouTube publisher |
| Scenario / package | artifact contract, compliance, structure variation | TTS, renderer internals, publishing |
| Visual production | `imagegen`, visual style, prompt-safe grid | analytics and YouTube rules |
| Assembly / QA | media contract, TTS, renderer and release checks | research backlog and full creative history |
| Publishing / analytics | only the matching reference and live API rules | visual-production context |

## Implemented now

| Area | Change | Verification |
|---|---|---|
| Structural variety | New Codex packages must compare their structural signature with the latest eight releases and record the difference in `codex_strategy.json`. A mere topic change is not sufficient. | Skill and artifact contract updated |
| YouTube UI safe areas | Image prompts must reserve the right-side controls and lower metadata band. Critical visual content belongs in x=120..860, y=200..1500 of a 1080x1920 frame. | Skill updated |
| Word-safe typography | Captions, poster, payoff and key overlays forbid word splitting. If a whole word does not fit, the generated HTML reduces its font size down to the declared readable minimum. | Renderer test added |

## Operating rules

1. For visual production, load `imagegen` before generating frames. Create one built-in imagegen asset per frame or approved variant; inspect it and copy the accepted result into the run folder.
2. Use Gemini TTS through `orchestration/audio_agent.py`; keep its per-beat cache and metadata.
3. Build the final MP4 locally through `assembly_v7.py`/HyperFrames/ffmpeg. Do not call `engine_v8.py --go` for a Codex-authored Short.
4. Stop before upload unless the user gives a separate direct YouTube command. Preserve run JSON, release gates, manifests and publish logs when archiving media.

## In progress / next small improvements

| Priority | Item | Definition of done |
|---|---|---|
| Next 1 | Add a deterministic cross-run `structure_signature` checker | `check_package.py` compares new signatures with recent local and iCloud run metadata and fails an explicit near-duplicate skeleton |
| Next 2 | Add a media manifest for Codex imagegen frames | `engine_v8 --build` accepts approved Codex frames and never silently invokes Gemini Image when the manifest is present |

## Five additional items now committed to the work queue

These are deliberately independent and small. They increase repeatability and reduce the amount of historical package data an agent must load; they do not authorize publication or require another external model by default.

| Order | Item | Scope and definition of done |
|---|---|---|
| 3 | Compact run index | Write a small, queryable `run_index.jsonl` record when a package passes release QA: run/slug, language, topic, structural signature, key claim IDs, frame hashes, final artefact path, and later the YouTube ID. Planning and duplicate checks read this index before opening full packages or iCloud archives. |
| 4 | Deterministic safe-area audit | Add a local renderer check for captions, cards, poster, payoff and scripted overlays: their computed bounds must not occupy the right control rail or lower metadata band. For in-image content, retain the prompt-safe declaration and require the existing human frame review; do not pretend local code can infer visual salience from pixels. |
| 5 | Voice-to-overlay timing audit | Derive the spoken numeric/measurement facts per beat and confirm the matching deterministic overlay appears in the same beat or within 0.5 seconds. Fail the release gate when a required number is spoken without an eligible matching card. |
| 6 | Resumable TTS integrity check | Validate cached WAVs with `ffprobe`, duration and a content signature before reuse; write a clear reason when regenerating. A partial/corrupt file must never silently reach assembly. |
| 7 | Strict exact-slot publishing mode | Add an explicit strict mode for a user-provided `publishAt`: if the live YouTube schedule is occupied, stop with the conflicting slot and video ID instead of shifting the time. Keep today's automatic-slot behaviour only for an explicitly automatic request. |

## Deferred intentionally

- Gemini Vision QA remains a targeted advisory review after local layout and visual checks, not a first-line gate.
