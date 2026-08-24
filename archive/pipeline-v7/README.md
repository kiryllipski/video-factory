# Archived pipeline v7 and legacy Codex-adjacent path

Archived on 2026-08-24 after v8 became the canonical Codex production path.

This directory is recoverable history, not a deletion. It contains the superseded v7
runtime, prompts, VitalLogic v7 context/media plan, the old `.claude` video-factory skill,
and v7 tests. New VitalLogic work must use `skills/codex-viral-shorts/`, `schemas_v8.py`,
`engine_v8.py --build`, `assembly_v8.py` and an approved `media_manifest.json`.

Generated runs under `autopilot_factory/runs/` remain in place. They are provenance and
duplicate-detection history, not active source code; moving or deleting the large media
archive would make old package verification and editorial comparisons harder.

The v8 media layer copied the required deterministic renderer and vision-QA boundary before
this archive was created. Its active dependencies no longer point into `.claude` or import
v7 runtime modules.
