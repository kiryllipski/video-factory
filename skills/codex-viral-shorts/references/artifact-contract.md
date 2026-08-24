# Codex-authored v8 package

Create a run under `autopilot_factory/runs/vitallogic_bad_pl/<date>_v8-<slug>/`.

Required content files:

| File | Contract |
|---|---|
| `research_pack.json` | `schemas_v8.ResearchPack`; 3–12 sources, 4–12 claims |
| `script.json` | `schemas_v8.Script`; 8–18 beats, 3–6 overlays |
| `compliance.json` | `schemas_v8.ComplianceVerdict`; `cleaned_script` equals the accepted script |
| `fact_review.json` | `schemas_v8.FactReview`; every script claim maps to an accepted claim |
| `frame_plan.json` | `schemas_v8.FramePlan`; exactly one frame per beat |
| `qa.json` | `schemas_v8.QAReport`; include all required v8 QA checks |
| `publish_package.json` | `schemas_v8.PublishPackage`; source URLs must be in the research pack; visible hashtags and API tags are separate |
| `codex_strategy.json` | Human-readable hypothesis, audience, risk decision, `distribution`, `hook_lab`, optional `series`, evidence levels, and `authored_by: "Codex"` |

`codex_strategy.json` must contain this minimum strategy contract:

```json
{
  "authored_by": "Codex",
  "distribution": {
    "lane": "feed",
    "primary_query": "",
    "secondary_queries": [],
    "metadata_hypothesis": ""
  },
  "hook_lab": {
    "variants": [
      {
        "id": "H1",
        "type": "contradiction",
        "hook": "...",
        "poster": "...",
        "first_visual": "...",
        "first_proof_s": 3.5,
        "claim_ids": ["CLM-01"],
        "score": 8,
        "rejection_reason": ""
      }
    ],
    "selected_variant": "H1"
  },
  "format_selection": {
    "format": "detective_case",
    "priority": "P0",
    "reason": "The visible result has several plausible causes and the first proof is an object-level clue.",
    "comic_engine": "The wrong household object is interrogated before the real mechanism is revealed.",
    "discarded_alternatives": ["number_shock", "study_autopsy"]
  },
  "structure_variation": {
    "compared_runs": ["2026-08-22_v8-example"],
    "signature": {
      "hook_mechanism": "binary choice with a visible object conflict",
      "first_proof": "product label appears by 3 seconds",
      "turn_device": "the apparent winner loses on a second label column",
      "evidence_device": "three-way 100 g comparison",
      "overlay_sequence": ["versus", "source", "list"],
      "payoff_device": "four-item shelf rule",
      "visual_rhythm": "macro object, medium acting, label evidence, wide shelf payoff"
    },
    "differs_from_recent": [
      "uses a label reversal instead of a body-mechanism reveal",
      "opens with three concrete products rather than a person-only reaction",
      "ends with a shopping rule rather than a timing rule"
    ]
  },
  "series": {
    "series_id": "",
    "episode": 1,
    "followup_topics": []
  }
}
```

Create 3–5 materially different hook variants. A series object is optional for a standalone idea, but must be filled when the Short is a follow-up or an outlier response.

`structure_variation` is required for new Codex-authored packages. Compare the last eight same-channel releases, using iCloud archive metadata when local `runs/` is incomplete. Do not accept a new topic whose format label changes while its actual hook, proof, turn, evidence, overlay and payoff sequence remain recognisably the same.

After each frame has been generated with built-in ImageGen, visually inspected and copied into
the run directory, add `media_manifest.json`:

```json
{
  "image_generation": "built_in_imagegen",
  "image_model_substitution": "none",
  "frames": [
    {
      "index": 0,
      "path": "frames/frame00.png",
      "sha256": "<sha256 of the accepted file>",
      "approval": "accepted_after_visual_inspection"
    }
  ]
}
```

The manifest must contain one ordered entry per `frame_plan.json` frame. `engine_v8.py --build`
checks the path, file type, approval and SHA-256 before assembly; a missing or changed frame
stops the build and never triggers an image-generation fallback.

Use only these local stages after package validation and frame approval:

```bash
cd autopilot_factory
VITALLOGIC_TTS_VOICE=Charon python3 engine_v8.py --build \
  runs/vitallogic_bad_pl/<run> --asset-channel vitallogic_bad_pl
```

Publishing is a separate operation. Only after a new direct user command may the publisher
inspect live YouTube state and upload or schedule the approved run. Local build success never
authorizes a YouTube mutation.

Never create a `PublishPackage` with facts or URLs absent from `ResearchPack`. Never call `engine_v8.py --go` for a Codex-authored Short.
