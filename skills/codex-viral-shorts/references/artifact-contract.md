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
  "series": {
    "series_id": "",
    "episode": 1,
    "followup_topics": []
  }
}
```

Create 3–5 materially different hook variants. A series object is optional for a standalone idea, but must be filled when the Short is a follow-up or an outlier response.

Use only these stages after package validation:

```bash
cd autopilot_factory
python3 engine_v8.py --build runs/vitallogic_bad_pl/<run> --asset-channel vitallogic_bad_pl
python3 publishers/youtube.py whoami --channel vitallogic_bad_pl
python3 publishers/youtube.py upload --channel vitallogic_bad_pl --run runs/vitallogic_bad_pl/<run> \
  --privacy private --lang pl --publish-at 2026-08-19T04:00:00Z
```

`04:00:00Z` equals 06:00 in Warsaw in August. Use the time explicitly authorized by the user; the upload command refuses occupied scheduled slots and chooses the next valid slot only with `--publish-at auto`.

Never create a `PublishPackage` with facts or URLs absent from `ResearchPack`. Never call `engine_v8.py --go` for a Codex-authored Short.
