#!/usr/bin/env python3
"""Разовый скрипт: пересинтез аудио (новый темп) + пересборка для уже готовых прогонов."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "orchestration"))

import engine
import schemas

RUNS = [
    ("2026-07-01_the-ceo-who-refused-to-buy-netflix-for-5", "biz_failures"),
    ("2026-07-03_kodak-invented-digital-cameras-and-sued-", "biz_failures"),
    ("2026-07-03_the-spotlight-effect:-why-nobody-notices", "psychology"),
]

ROOT = Path(__file__).resolve().parent / "runs"

for name, channel in RUNS:
    run_dir = ROOT / name
    print(f"=== {name} ({channel}) ===")
    script = schemas.Script.model_validate_json((run_dir / "script.json").read_text())
    plan = schemas.FramePlan.model_validate_json((run_dir / "frame_plan.json").read_text())
    frames = sorted((run_dir / "frames").glob("frame_*.png"))

    voice_wav, durations = engine.synth_audio(channel, script, run_dir / "audio_v2")
    print(f"  audio_v2 done, total={sum(durations):.1f}s")

    out_mp4 = run_dir / "out_v2.mp4"
    engine.assemble(plan, script, frames, durations, voice_wav, out_mp4, run_dir / "hf_v2")
    print(f"  -> {out_mp4}")
