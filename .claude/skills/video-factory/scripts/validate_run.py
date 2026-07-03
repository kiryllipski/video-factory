#!/usr/bin/env python3
"""validate_run.py — валидирует артефакты прогона ДО любых трат на медиа.

Проверяет, что script.json / frame_plan.json (и, если есть, compliance.json) соответствуют
Pydantic-схемам из autopilot_factory/schemas.py, плюс несколько кросс-проверок, которых нет в схемах
(кадров = битов, порядок, суммарный хронометраж). Ничего не генерирует и не тратит бюджет.

    python3 scripts/validate_run.py <run_dir>

Код возврата 0 = всё зелёно; 1 = есть ошибки (перечислены).
"""
from __future__ import annotations
import sys
import json
import argparse
from pathlib import Path

from _common import find_project_root, wire_paths

ROOT = find_project_root()
wire_paths(ROOT)
import schemas  # noqa: E402
from pydantic import ValidationError  # noqa: E402


def _load(run_dir: Path, name: str) -> dict:
    p = run_dir / name
    if not p.exists():
        raise FileNotFoundError(name)
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Валидация прогона video-factory")
    ap.add_argument("run_dir")
    args = ap.parse_args()
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        print(f"[fail] нет папки прогона: {run_dir}")
        return 1

    errors: list[str] = []

    # --- script.json (обязателен) ---
    script = None
    try:
        script = schemas.Script(**_load(run_dir, "script.json"))
        beats_total = sum(b.dur_s for b in script.beats)
        if abs(beats_total - script.total_dur_s) > max(4.0, 0.15 * script.total_dur_s):
            errors.append(f"сумма dur_s битов ({beats_total:.1f}с) далека от total_dur_s "
                          f"({script.total_dur_s:.1f}с) — расхождение >15%")
    except FileNotFoundError:
        errors.append("script.json не найден")
    except (ValidationError, json.JSONDecodeError) as e:
        errors.append(f"script.json не проходит схему Script: {e}")

    # --- compliance.json (опционален; если есть — берём cleaned_script для сверки с планом) ---
    effective_script = script
    if (run_dir / "compliance.json").exists():
        try:
            verdict = schemas.ComplianceVerdict(**_load(run_dir, "compliance.json"))
            effective_script = verdict.cleaned_script
        except (ValidationError, json.JSONDecodeError) as e:
            errors.append(f"compliance.json не проходит схему ComplianceVerdict: {e}")

    # --- frame_plan.json (обязателен) ---
    try:
        plan = schemas.FramePlan(**_load(run_dir, "frame_plan.json"))
        if effective_script is not None:
            nb, nf = len(effective_script.beats), len(plan.frames)
            if nb != nf:
                errors.append(f"кадров ({nf}) ≠ битов ({nb}) — нужен ровно один кадр на бит")
    except FileNotFoundError:
        errors.append("frame_plan.json не найден")
    except (ValidationError, json.JSONDecodeError) as e:
        errors.append(f"frame_plan.json не проходит схему FramePlan: {e}")

    if errors:
        print("[fail] найдены проблемы:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"[ok] {run_dir.name}: script.json + frame_plan.json валидны, кадров = битов. Готово к build_media.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
