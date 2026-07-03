#!/usr/bin/env python3
"""
cost_tracker.py — мягкий учёт расхода токенов по шагам (юнит-экономика ролика, R15).

Раннеры (`gemini_agent.py`, `image_agent.py`) импортируют этот модуль по try/except и вызывают
`record_tokens(model_id, usage_metadata, step)`. Если задан RUN_COST_DIR — дописываем строку в
<RUN_COST_DIR>/cost.jsonl и обновляем сводку cost.json. Без RUN_COST_DIR — no-op (тихо).

Долларовую стоимость считаем по PRICES (USD за 1M токенов). Ставки — ПЛЕЙСХОЛДЕРЫ: перед выводами
по экономике сверить с актуальным прайсом Gemini (https://ai.google.dev/gemini-api/docs/pricing).
"""
from __future__ import annotations
import os
import json
import datetime
from pathlib import Path

# USD за 1_000_000 токенов (input, output). TODO(R15): подставить точные актуальные ставки.
PRICES = {
    "gemini-2.5-flash-lite":      (0.10, 0.40),
    "gemini-2.5-flash":           (0.30, 2.50),
    "gemini-3.5-flash":           (0.50, 3.00),
    "gemini-3.1-pro-preview":     (2.00, 12.00),
    # image-модели тарифицируются иначе (за изображение) — считаем как output-«токены» приблизительно
    "gemini-3.1-flash-image":     (0.30, 30.00),
    "gemini-3.1-flash-lite-image":(0.20, 15.00),
    "gemini-3-pro-image":         (2.00, 60.00),
    # Interactions API (deep research) — thought-токены дорогие; по факту тариф не за
    # токен, а $1-7/задача (документация), тут — грубая оценка per-token для порядка величины.
    "deep-research-preview-04-2026":     (2.00, 15.00),
    "deep-research-max-preview-04-2026": (2.00, 30.00),
    "deep-research-pro-preview-12-2025": (2.00, 20.00),
}


def _usd(model_id: str, tin: int, tout: int) -> float:
    pin, pout = PRICES.get(model_id, (0.0, 0.0))
    return (tin / 1_000_000) * pin + (tout / 1_000_000) * pout


def record_tokens(model_id: str, usage_metadata, step: str = "") -> None:
    """Безопасно логирует расход. usage_metadata — объект google-genai (может быть None)."""
    run_dir = os.environ.get("RUN_COST_DIR")
    if not run_dir:
        return
    try:
        tin = int(getattr(usage_metadata, "prompt_token_count", 0) or 0)
        tout = int(getattr(usage_metadata, "candidates_token_count", 0) or 0)
        rec = {
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "step": step, "model": model_id,
            "tokens_in": tin, "tokens_out": tout,
            "usd": round(_usd(model_id, tin, tout), 6),
        }
        d = Path(run_dir); d.mkdir(parents=True, exist_ok=True)
        with (d / "cost.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _update_summary(d)
    except Exception:
        return  # учёт не должен ронять пайплайн


def _update_summary(d: Path) -> None:
    total_usd = 0.0
    steps: dict[str, float] = {}
    for line in (d / "cost.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        total_usd += r.get("usd", 0.0)
        steps[r.get("step", "?")] = steps.get(r.get("step", "?"), 0.0) + r.get("usd", 0.0)
    (d / "cost.json").write_text(
        json.dumps({"total_usd": round(total_usd, 6),
                    "by_step": {k: round(v, 6) for k, v in steps.items()}},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
