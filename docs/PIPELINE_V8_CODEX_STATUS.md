# VitalLogic pipeline v8 — Codex production status

Updated: 2026-08-24

This is the active production contract for the Polish VitalLogic channel. Codex owns
research synthesis, Polish editorial decisions, scenario, metadata and English visual
prompts. Built-in ImageGen owns the approved visual frames; Gemini remains permitted for
Polish TTS and targeted semantic vision QA. Captions, overlays, source cards, assembly,
codecs, manifests and local QA remain deterministic and local.

## Current pilot

`Baton proteinowy po treningu: paliwo czy droga czekolada?` is a comic courtroom mini-trial.
The workout goal, label and ordinary food act as witnesses; the verdict distinguishes
logistical convenience from automatic superiority. It uses a lively conversational Polish
voice with light irony, approved ImageGen frames, a local package and local assembly. No
YouTube upload, scheduling or publisher-state mutation is part of the build.

## Active ownership

| Layer | Owner/tool | Rule |
|---|---|---|
| Research, hook, scenario, metadata | Codex + current primary sources | Current claims are recorded with source and `claim_id`. |
| Frames | Built-in `imagegen` | Inspect every frame and record it in `media_manifest.json`; no silent image-model substitution. |
| Voice | `orchestration/audio_agent.py` / Gemini TTS | Keep per-beat cache and delivery metadata. |
| Captions, cards, animation, codec | `autopilot_factory/assembly_v8.py` + HyperFrames + ffmpeg | Viewer text is deterministic and word-safe. |
| Content QA | `skills/codex-viral-shorts/scripts/check_package.py` | Validate before costly media work. |
| Media QA | release gate, layout inspect, ffprobe, visual review | Confirm 1080×1920, readable text, safe areas and frame meaning. |
| Upload/scheduling | `autopilot_factory/publishers/youtube.py` | Separate direct user command only. |

## v8 build boundary

The active media command is:

```bash
cd autopilot_factory
VITALLOGIC_TTS_VOICE=Charon python3 engine_v8.py \
  --build runs/vitallogic_bad_pl/<run> --asset-channel vitallogic_bad_pl
```

`engine_v8.py --build` requires an approved `media_manifest.json`. The manifest contains
the ordered frame paths, SHA-256 hashes, built-in ImageGen provenance and visual approval.
The build validates every entry and then passes those exact files to `assembly_v8.py`.
It never calls the legacy Gemini image generator. A missing or changed frame is a hard
stop, not an invitation to regenerate something different.

Do not use `engine_v8.py --go` for Codex-authored work: content is written and hydrated by
Codex, then checked, visually reviewed and built through the explicit media boundary.

## Editorial invariants

- The content remains educational, entertaining and ironic; the joke targets a myth,
  marketing claim, office absurdity or object behaviour, never illness or the viewer.
- The search map stays broad: food, body, sport, supplements, brain, sleep, research and
  productivity-through-biology are all valid inputs for research.
- New packages compare the latest eight same-channel runs and record `structure_variation`;
  changing the topic alone is not enough to avoid a repetitive skeleton.
- Critical visual content stays inside x=120..860, y=200..1500 of a 1080×1920 frame. The
  right rail and lower UI band contain only expendable background.
- Captions, posters, overlays, source cards and payoffs do not split or hyphenate words.
- Publishing is never implied by local generation or a passed QA gate.

## Accepted pilot evidence

The current pilot has 10 accepted built-in ImageGen frames in
`autopilot_factory/runs/vitallogic_bad_pl/2026-08-24_v8-baton-po-treningu-courtroom-imagegen-01/`.
The run's manifest records the frame hashes and the rejected robot variant, preserving the
reason it was not used. The artifact is a reference implementation of this v8 boundary.
