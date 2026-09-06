# v9 retention sprint contract

Use this contract for the active 12-Short VitalLogic experiment. The full strategy is in
`docs/experiments/2026-08-26_v9_retention_sprint.md`; the runnable pipeline is documented in
`docs/PIPELINE_V9_RETENTION.md`.

## Required new artifact

Create `retention_plan.json` before ImageGen:

```json
{
  "version": "9.0-retention",
  "duration_lane": "core",
  "target_duration_s": 22.0,
  "first_proof_beat": 1,
  "turn_beat": 3,
  "payoff_beat": 6,
  "spoken_cta": false,
  "cadence": {
    "publications_today": 1,
    "slot_index": 1,
    "minimum_gap_hours": 4.0
  },
  "creative_fingerprint": {
    "hook_family": "direct object demonstration",
    "protagonist_mode": "topic object",
    "story_engine": "comment answer",
    "proof_device": "visible household comparison",
    "environment": "kitchen macro",
    "edit_grammar": "fast proof then two state changes",
    "payoff_device": "single practical rule",
    "tts_delivery": "lively conversational",
    "compared_runs": [
      "run-01", "run-02", "run-03", "run-04",
      "run-05", "run-06", "run-07", "run-08"
    ],
    "changed_axes": ["hook_family", "proof_device", "environment"]
  }
}
```

Replace every placeholder with an actual recent run or creative decision. The cadence object is
production metadata, not upload authorization.

## Core lane

- Target 18-24 seconds; hard actual ceiling 26 seconds.
- Target 40-55 Polish words; hard ceiling 60.
- One conflict, one accepted proof, one turn and one rule.

## Deep lane

- Target 28-35 seconds; hard actual ceiling 35 seconds.
- Target 30-60 Polish words at natural TTS speed; hard ceiling 60.
- A second evidence event must change the viewer question. Extra caveats alone do not justify deep.

## Sequence

1. Validate the v8-compatible content package and retention plan.
2. Run `uv run --with 'pydantic>=2,<3' --with google-genai python3 engine_v9.py --preflight <run>` before ImageGen.
3. Rewrite until `retention_timing.json.passed` is true.
4. Generate and inspect built-in ImageGen frames; write the approved manifest.
5. Run `uv run --with 'pydantic>=2,<3' --with google-genai python3 engine_v9.py --build <run>`.
6. Inspect the full MP4, release gate and media metadata.
7. Stop locally unless the user separately authorizes a YouTube mutation.
