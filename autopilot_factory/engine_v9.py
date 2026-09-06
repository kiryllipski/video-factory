#!/usr/bin/env python3
"""v9-retention runner: measured audio preflight + fail-closed v8 media build."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import assembly_v9 as A9
import engine_v8 as E8
import schemas_v8 as S8
import schemas_v9 as S9


FILTERED_V8_PREFIXES = (
    "плановый хронометраж ",
    "слов в озвучке ",
    "hook-битов ",
)
V8_SCRIPT_ERRORS = E8.script_errors


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def v9_script_errors(script: S8.Script, pack: S8.ResearchPack) -> list[str]:
    """Reuse v8 evidence/editorial checks, replacing v8-only timing and hook-count gates."""
    return [
        error for error in V8_SCRIPT_ERRORS(script, pack)
        if not error.startswith(FILTERED_V8_PREFIXES)
    ]


def _load_package(run_dir: Path):
    required = {
        "research_pack.json": S8.ResearchPack,
        "script.json": S8.Script,
        "compliance.json": S8.ComplianceVerdict,
        "fact_review.json": S8.FactReview,
        "frame_plan.json": S8.FramePlan,
        "qa.json": S8.QAReport,
        "publish_package.json": S8.PublishPackage,
        "retention_plan.json": S9.RetentionPlan,
    }
    missing = [name for name in required if not (run_dir / name).is_file()]
    if missing:
        raise SystemExit("[v9] missing: " + ", ".join(missing))
    loaded = {
        name: model.model_validate_json((run_dir / name).read_text(encoding="utf-8"))
        for name, model in required.items()
    }
    return loaded


def _content_checks(loaded: dict) -> list[S9.TimingCheck]:
    pack = loaded["research_pack.json"]
    script = loaded["script.json"]
    compliance = loaded["compliance.json"]
    fact = loaded["fact_review.json"]
    frames = loaded["frame_plan.json"]
    qa = loaded["qa.json"]
    plan = loaded["retention_plan.json"]

    def check(name: str, errors: list[str]) -> S9.TimingCheck:
        return S9.TimingCheck(name=name, passed=not errors, detail="; ".join(errors))

    proof_beat = script.beats[plan.first_proof_beat]
    proof_has_evidence = bool(proof_beat.claim_ids) or any(
        overlay.beat_idx == plan.first_proof_beat and overlay.claim_ids
        for overlay in script.overlays
    )
    index_errors = []
    if plan.turn_beat != script.turn_beat_idx:
        index_errors.append(
            f"retention turn_beat={plan.turn_beat} != script.turn_beat_idx={script.turn_beat_idx}"
        )
    if script.beats[plan.payoff_beat].act != "payoff":
        index_errors.append("retention payoff_beat must reference a payoff beat")
    if not proof_has_evidence:
        index_errors.append("first_proof_beat must carry accepted claim evidence")

    return [
        check("research_pack", E8.research_errors(pack)),
        check("script_contract", v9_script_errors(script, pack)),
        check("frame_plan", E8.plan_errors(frames, script, pack)),
        check("semantic_qa", E8.qa_issues(qa)),
        S9.TimingCheck(
            name="compliance",
            passed=compliance.passed,
            detail="; ".join(compliance.fixes),
        ),
        S9.TimingCheck(
            name="fact_review",
            passed=fact.passed,
            detail="; ".join(fact.unsupported_script_statements),
        ),
        check("retention_indices", index_errors),
    ]


def preflight(run_dir: Path) -> S9.RetentionTimingReport:
    run_dir = run_dir.resolve()
    loaded = _load_package(run_dir)
    script = loaded["script.json"]
    plan = loaded["retention_plan.json"]
    E8.LANG = script.lang
    _, durations, _ = E8.synth_audio(script, run_dir / "audio")
    timing = A9.build_timing_report(script, plan, durations)
    content_checks = _content_checks(loaded)
    merged_checks = content_checks + timing.checks
    timing = timing.model_copy(update={
        "passed": all(item.passed for item in merged_checks),
        "checks": merged_checks,
    })
    _write(run_dir / "retention_timing.json", timing.model_dump())
    if not timing.passed:
        failed = [item.name for item in timing.checks if not item.passed]
        raise SystemExit("[v9] retention preflight failed: " + ", ".join(failed))
    print(
        f"[v9] preflight passed · lane={timing.lane} words={timing.word_count} "
        f"actual={timing.actual_narration_s:.1f}s target={timing.target_duration_s:.1f}s"
    )
    return timing


def build(run_dir: Path, asset_channel: str, sfx_profile: str) -> Path:
    run_dir = run_dir.resolve()
    timing = preflight(run_dir)
    plan = S9.RetentionPlan.model_validate_json(
        (run_dir / "retention_plan.json").read_text(encoding="utf-8")
    )

    original_script_errors = E8.script_errors
    E8.script_errors = v9_script_errors
    try:
        E8.build_media_from_artifacts(
            run_dir,
            asset_channel=asset_channel,
            sfx_profile=sfx_profile,
        )
    finally:
        E8.script_errors = original_script_errors

    media_meta = E8._probe_video(run_dir / "out.mp4")
    mp4_check = A9.mp4_duration_check(plan, float(media_meta["duration_s"]))
    release_path = run_dir / "release_gate.json"
    release = _load(release_path)
    release.setdefault("checks", []).extend(
        [item.model_dump() for item in timing.checks] + [mp4_check.model_dump()]
    )
    release["passed"] = bool(release.get("passed")) and timing.passed and mp4_check.passed
    release["pipeline_version"] = S9.PIPELINE_VERSION
    _write(release_path, release)
    if not release["passed"]:
        raise SystemExit("[v9] final release gate failed after media build")

    meta_path = run_dir / "run_meta.json"
    meta = _load(meta_path)
    meta["pipeline_version"] = S9.PIPELINE_VERSION
    meta["retention"] = {
        "lane": timing.lane,
        "target_duration_s": timing.target_duration_s,
        "actual_narration_s": timing.actual_narration_s,
        "actual_mp4_s": media_meta["duration_s"],
        "word_count": timing.word_count,
    }
    _write(meta_path, meta)

    artifact_path = run_dir / "artifact_manifest.json"
    artifact = _load(artifact_path) if artifact_path.exists() else {}
    artifact["pipeline_version"] = S9.PIPELINE_VERSION
    artifact.setdefault("sha256", {})["retention_plan.json"] = _sha256(
        run_dir / "retention_plan.json"
    )
    artifact["sha256"]["retention_timing.json"] = _sha256(
        run_dir / "retention_timing.json"
    )
    _write(artifact_path, artifact)
    print(f"[v9] release-ready · {media_meta['duration_s']:.1f}s -> {run_dir / 'out.mp4'}")
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="v9 measured-retention build layer")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", metavar="RUN_DIR")
    mode.add_argument("--build", metavar="RUN_DIR")
    parser.add_argument("--asset-channel", default="vitallogic_bad_pl")
    parser.add_argument("--sfx", default="data", choices=list(E8.A.SFX_PROFILES))
    args = parser.parse_args()
    if args.preflight:
        preflight(Path(args.preflight))
        return
    build(Path(args.build), args.asset_channel, args.sfx)


if __name__ == "__main__":
    main()
