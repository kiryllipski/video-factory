#!/usr/bin/env python3
"""Validate a Codex-authored v8/v9 content package before costly media generation."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def metadata_errors(
    pkg, strategy: dict, allowed_urls: set[str], allowed_claim_ids: set[str], lang: str
) -> list[str]:
    """Validate the discovery hypothesis without pretending metadata guarantees reach."""
    errors: list[str] = []
    title = pkg.title.strip()
    description = pkg.description.strip()
    if not title:
        errors.append("publish package title is empty")
    if len(title) > 100:
        errors.append("publish package title exceeds 100 characters")
    if len(description) > 5000:
        errors.append("publish package description exceeds 5000 characters")
    if lang == "pl" and re.search(r"[А-Яа-яЁё]", title + "\n" + description):
        errors.append("Polish publish package contains Cyrillic viewer-facing text")

    hashtags = [h.strip() for h in pkg.hashtags]
    if any(not h.startswith("#") for h in hashtags):
        errors.append("visible hashtags must start with #")
    if len({h.casefold() for h in hashtags}) != len(hashtags):
        errors.append("visible hashtags contain duplicates")
    forbidden = {"#viral", "#fyp", "#trending", "#explore"}
    if forbidden.intersection(h.casefold() for h in hashtags):
        errors.append("generic reach hashtags are not allowed")

    api_tags = [tag.strip() for tag in pkg.api_tags]
    if any(not tag or tag.startswith("#") for tag in api_tags):
        errors.append("api_tags must be non-empty phrases without #")
    if len({tag.casefold() for tag in api_tags}) != len(api_tags):
        errors.append("api_tags contain duplicates")

    if not (2 <= len(pkg.source_urls) <= 5):
        errors.append("publish package must contain 2–5 source_urls")
    for url in pkg.source_urls:
        if url not in allowed_urls:
            errors.append(f"publish package has unknown URL: {url}")
        elif url not in description:
            errors.append(f"source URL is not present in description: {url}")

    lane = pkg.distribution_lane
    if lane in {"search", "hybrid"}:
        query = pkg.primary_query.strip()
        if not query:
            errors.append(f"{lane} package requires primary_query")
        else:
            first_lines = "\n".join(description.splitlines()[:2]).casefold()
            if query.casefold() not in title.casefold() and query.casefold() not in first_lines:
                errors.append("primary_query must appear in title or the first two description lines")
    if not pkg.metadata_hypothesis.strip():
        errors.append("metadata_hypothesis is required")

    distribution = strategy.get("distribution")
    if not isinstance(distribution, dict):
        errors.append("codex_strategy.json requires a distribution object")
    else:
        strategy_lane = distribution.get("lane")
        if strategy_lane != lane:
            errors.append("distribution.lane and publish_package.distribution_lane disagree")
        if strategy_lane in {"search", "hybrid"} and not distribution.get("primary_query", "").strip():
            errors.append(f"strategy distribution lane {strategy_lane} requires primary_query")

    hook_lab = strategy.get("hook_lab")
    if not isinstance(hook_lab, dict):
        errors.append("codex_strategy.json requires a hook_lab object")
    else:
        variants = hook_lab.get("variants")
        if not isinstance(variants, list) or not (3 <= len(variants) <= 5):
            errors.append("hook_lab requires 3–5 variants")
        else:
            ids = []
            for index, variant in enumerate(variants, start=1):
                if not isinstance(variant, dict):
                    errors.append(f"hook_lab variant {index} must be an object")
                    continue
                variant_id = variant.get("id")
                ids.append(variant_id)
                for field in ("hook", "poster", "first_visual", "type"):
                    if not str(variant.get(field, "")).strip():
                        errors.append(f"hook_lab variant {index} missing {field}")
                proof = variant.get("first_proof_s")
                if not isinstance(proof, (int, float)) or not 0 <= proof <= 6:
                    errors.append(f"hook_lab variant {index} first_proof_s must be between 0 and 6")
                unknown_claims = set(variant.get("claim_ids", [])) - allowed_claim_ids
                if unknown_claims:
                    errors.append(
                        f"hook_lab variant {index} has unknown/rejected claim_ids: "
                        + ", ".join(sorted(unknown_claims))
                    )
            selected = hook_lab.get("selected_variant")
            if selected not in ids:
                errors.append("hook_lab.selected_variant must reference a variant id")

    # A small guard against description keyword dumps. This is intentionally conservative:
    # repeated source terms and normal Polish inflection are allowed.
    words = re.findall(r"[\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ-]{4,}", description.casefold())
    repeated = {word for word in words if words.count(word) >= 5}
    if repeated:
        errors.append("description repeats the same keyword too many times: " + ", ".join(sorted(repeated)))
    return errors


def structure_errors(strategy: dict) -> list[str]:
    """Require an auditable structural comparison, not just a new topic label."""
    errors: list[str] = []
    variation = strategy.get("structure_variation")
    if not isinstance(variation, dict):
        return ["codex_strategy.json requires a structure_variation object"]
    compared = variation.get("compared_runs")
    if not isinstance(compared, list) or len(compared) < 8:
        errors.append("structure_variation.compared_runs must contain at least 8 runs")
    signature = variation.get("signature")
    required = (
        "hook_mechanism", "first_proof", "turn_device", "evidence_device",
        "overlay_sequence", "payoff_device", "visual_rhythm",
    )
    if not isinstance(signature, dict):
        errors.append("structure_variation.signature must be an object")
    else:
        for field in required:
            value = signature.get(field)
            if field == "overlay_sequence":
                if not isinstance(value, list) or not value:
                    errors.append("structure_variation.signature.overlay_sequence must be non-empty")
            elif not str(value or "").strip():
                errors.append(f"structure_variation.signature.{field} is required")
    differences = variation.get("differs_from_recent")
    if not isinstance(differences, list) or len(differences) < 3:
        errors.append("structure_variation.differs_from_recent must list at least 3 differences")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_package.py <run-dir>", file=sys.stderr)
        return 2
    run_dir = Path(sys.argv[1]).resolve()
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "autopilot_factory"))
    sys.path.insert(0, str(root / "orchestration"))

    import engine_v8 as E  # pylint: disable=import-outside-toplevel
    import schemas_v8 as S  # pylint: disable=import-outside-toplevel
    retention_path = run_dir / "retention_plan.json"
    retention_plan = None
    v9_engine = None
    if retention_path.is_file():
        import engine_v9 as v9_engine  # pylint: disable=import-outside-toplevel
        import schemas_v9 as S9  # pylint: disable=import-outside-toplevel
        try:
            retention_plan = S9.RetentionPlan(**load(retention_path))
        except Exception as exc:
            print(f"schema error: retention_plan.json: {exc}", file=sys.stderr)
            return 1

    needed = {
        "research": ("research_pack.json", S.ResearchPack),
        "script": ("script.json", S.Script),
        "compliance": ("compliance.json", S.ComplianceVerdict),
        "fact": ("fact_review.json", S.FactReview),
        "plan": ("frame_plan.json", S.FramePlan),
        "qa": ("qa.json", S.QAReport),
        "publish": ("publish_package.json", S.PublishPackage),
    }
    missing = [filename for filename, _ in needed.values() if not (run_dir / filename).is_file()]
    if missing:
        print("missing: " + ", ".join(missing), file=sys.stderr)
        return 1
    try:
        values = {key: schema(**load(run_dir / filename)) for key, (filename, schema) in needed.items()}
        strategy = load(run_dir / "codex_strategy.json")
    except Exception as exc:
        print(f"schema error: {exc}", file=sys.stderr)
        return 1

    errors = []
    if strategy.get("authored_by") != "Codex":
        errors.append("codex_strategy.json must contain authored_by=Codex")
    errors.extend(structure_errors(strategy))
    if values["script"].lang != "pl" or values["research"].lang != "pl":
        errors.append("this skill expects a Polish package")
    if not values["compliance"].passed or values["compliance"].cleaned_script != values["script"]:
        errors.append("compliance must pass and preserve the accepted script")
    if not values["fact"].passed or values["fact"].unsupported_script_statements:
        errors.append("fact review must pass with no unsupported statements")
    if not values["qa"].passed:
        errors.append("semantic QA must pass")
    errors.extend(E.research_errors(values["research"]))
    if retention_plan is not None:
        errors.extend(v9_engine.v9_script_errors(values["script"], values["research"]))
    else:
        errors.extend(E.script_errors(values["script"], values["research"]))
    errors.extend(E.plan_errors(values["plan"], values["script"], values["research"]))

    # Format choice is a deliberate Codex editorial decision, not an incidental field copied
    # from a template. Keep the artifact auditable and aligned with the canonical catalog.
    format_selection = strategy.get("format_selection")
    if format_selection is not None and not isinstance(format_selection, dict):
        errors.append("codex_strategy.json format_selection must be an object when present")
    elif isinstance(format_selection, dict):
        selected_format = format_selection.get("format")
        expected_format = values["script"].format
        if selected_format != expected_format:
            errors.append("format_selection.format must match script.format")
        if selected_format not in S.FORMAT_BRIEFS:
            errors.append("format_selection.format is not in the canonical format catalog")
        expected_priority = S.FORMAT_PRIORITY.get(selected_format)
        if format_selection.get("priority") != expected_priority:
            errors.append("format_selection.priority does not match the format catalog")
        for field in ("reason", "comic_engine"):
            if not str(format_selection.get(field, "")).strip():
                errors.append(f"format_selection requires {field}")
        discarded = format_selection.get("discarded_alternatives", [])
        if not isinstance(discarded, list):
            errors.append("format_selection.discarded_alternatives must be a list")
        elif any(item not in S.FORMAT_BRIEFS for item in discarded):
            errors.append("format_selection.discarded_alternatives contains an unknown format")

    allowed_urls = {source.url for source in values["research"].sources}
    allowed_claim_ids = {
        claim.id for claim in values["research"].claims if claim.verdict != "rejected"
    }
    errors.extend(
        metadata_errors(
            values["publish"], strategy, allowed_urls, allowed_claim_ids, values["script"].lang
        )
    )

    if errors:
        print("package failed:", file=sys.stderr)
        for error in errors:
            print("- " + error, file=sys.stderr)
        return 1
    print(f"package passed: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
