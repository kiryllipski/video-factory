#!/usr/bin/env python3
"""Резюмирует прогон с готовыми script.json/frame_plan.json/frames/, если упал на audio/assembly/qa."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "orchestration"))

import engine
import schemas

run_dir_name = sys.argv[1]
channel = sys.argv[2]

run_dir = Path(__file__).resolve().parent / "runs" / run_dir_name
script = schemas.Script.model_validate_json((run_dir / "script.json").read_text())
plan = schemas.FramePlan.model_validate_json((run_dir / "frame_plan.json").read_text())
frames = sorted((run_dir / "frames").glob("frame_*.png"))

print(f"[resume] {run_dir_name}: {len(frames)} кадров, {len(script.beats)} битов")
voice_wav, durations, beat_words = engine.synth_audio(channel, script, run_dir / "audio")
print(f"  audio done, total={sum(durations):.1f}s")

out_mp4 = run_dir / "out.mp4"
engine.assemble(plan, script, frames, durations, beat_words, voice_wav, out_mp4, run_dir / "hf")
print(f"  -> {out_mp4}")

try:
    report = engine.qa(script, plan)
    (run_dir / "qa.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"  qa passed={report.passed}")
except Exception as e:
    print(f"  qa skipped: {e}")
