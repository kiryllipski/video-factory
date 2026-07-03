#!/usr/bin/env python3
"""Разовый скрипт: пересборка Spotlight Effect с новым визуальным кодом (R41).
Сценарий и озвучка (уже ускоренная, audio_v2) не меняются — перегенерируем только
frame_plan (visual_director читает обновлённый studio_context) и кадры."""
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "orchestration"))

import engine
import schemas

run_dir = Path(__file__).resolve().parent / "runs" / "2026-07-03_the-spotlight-effect:-why-nobody-notices"
channel = "psychology"

script = schemas.Script.model_validate_json((run_dir / "script.json").read_text())

print("[1/3] plan_frames (новый визуальный код)...")
plan = engine.plan_frames(channel, script)
(run_dir / "frame_plan_v2.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
for i, fr in enumerate(plan.frames):
    print(f"  {i}: {fr.motion:14s} {fr.prompt[:70]}")

print("[2/3] generate_frames (Nano Banana 2)...")
frames = engine.generate_frames(plan, run_dir / "frames_v2")
print(f"  {len(frames)} кадров -> {run_dir / 'frames_v2'}")

print("[3/3] assemble (переиспользуем audio_v2)...")
audio_dir = run_dir / "audio_v2"
beat_wavs = [audio_dir / f"beat{i}.wav" for i in range(len(script.beats))]
durs = [engine._wav_dur(w) for w in beat_wavs]
voice_wav = audio_dir / "voice.wav"
out_mp4 = run_dir / "out_v3.mp4"
engine.assemble(plan, script, frames, durs, voice_wav, out_mp4, run_dir / "hf_v3")
print(f"  -> {out_mp4}")
