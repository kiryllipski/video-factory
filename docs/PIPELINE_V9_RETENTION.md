# Pipeline v9-retention

`v9-retention` is a fail-closed retention layer on top of the stable v8 evidence and media
contracts. It leaves `engine_v8.py`, `schemas_v8.py` and `assembly_v8.py` callable and unchanged as
the legacy v8 path.

The final v9 MP4 gate has an absolute 35-second ceiling. The `core` lane remains stricter at 26
seconds; `deep` targets 28-35 seconds and may not exceed 35 seconds.

## New artifacts

| File | Author | Purpose |
|---|---|---|
| `retention_plan.json` | Codex | duration lane, proof/turn/payoff beats, cadence context and creative fingerprint |
| `retention_timing.json` | `engine_v9.py --preflight` | measured WAV timing and hard-gate results |

All v8 package files and `media_manifest.json` remain required.

## Workflow

1. Author the complete evidence-led v8-compatible content package plus `retention_plan.json`.
2. Run timing preflight before ImageGen:

   ```bash
   cd autopilot_factory
   VITALLOGIC_TTS_VOICE=Charon uv run --with 'pydantic>=2,<3' --with google-genai \
     python3 engine_v9.py --preflight \
     runs/vitallogic_bad_pl/<run>
   ```

3. If `retention_timing.json.passed` is true, generate and inspect every frame with built-in
   ImageGen and write `media_manifest.json`.
4. Build through v9:

   ```bash
   cd autopilot_factory
   VITALLOGIC_TTS_VOICE=Charon uv run --with 'pydantic>=2,<3' --with google-genai \
     python3 engine_v9.py --build \
     runs/vitallogic_bad_pl/<run> --asset-channel vitallogic_bad_pl
   ```

5. Run the package checker and review the full MP4. A current v8/v9 release gate that is missing or
   false blocks the shared publisher.
6. Stop locally unless the user separately instructs an upload, schedule or publication.

## Version boundary

- v8 owns research/evidence schemas, visual frame assembly, captions, overlays, sound design and
  ImageGen manifest verification.
- v9 owns measured duration, retention timing, cadence metadata, perceptual variety and final
  fail-closed release status.
- Successful v9 builds record `pipeline_version: 9.0-retention` in `run_meta.json`.
