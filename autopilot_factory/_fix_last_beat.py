#!/usr/bin/env python3
"""Пересинтез только последнего бита (после правки обрезанного CTA) + полная пересборка."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "orchestration"))

import engine
import schemas

ROOT = Path(__file__).resolve().parent / "runs"
RUNS = [
    ("2026-07-01_the-ceo-who-refused-to-buy-netflix-for-5", "biz_failures"),
    ("2026-07-03_kodak-invented-digital-cameras-and-sued-", "biz_failures"),
]

for name, channel in RUNS:
    run_dir = ROOT / name
    print(f"=== {name} ({channel}) ===")
    script = schemas.Script.model_validate_json((run_dir / "script.json").read_text())
    plan = schemas.FramePlan.model_validate_json((run_dir / "frame_plan.json").read_text())
    frames = sorted((run_dir / "frames").glob("frame_*.png"))

    voice, style, speed = engine.CHANNEL_VOICE[channel]
    audio_dir = run_dir / "audio_v2"
    last_i = len(script.beats) - 1
    w = audio_dir / f"beat{last_i}.wav"
    engine.generate_speech(script.beats[last_i].voiceover, voice=voice, style=style, out=str(w), speed=speed)
    print(f"  regenerated beat{last_i}.wav")

    # пересчитать durations по уже существующим wav (beat0..beatN, N уже актуален)
    beat_wavs = [audio_dir / f"beat{i}.wav" for i in range(len(script.beats))]
    durs = [engine._wav_dur(w) for w in beat_wavs]
    lst = audio_dir / "concat.txt"
    lst.write_text("".join(f"file '{w.name}'\n" for w in beat_wavs), encoding="utf-8")
    voice_wav = audio_dir / "voice.wav"
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(voice_wav)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  audio_v2 rebuilt, total={sum(durs):.1f}s")

    out_mp4 = run_dir / "out_v2.mp4"
    engine.assemble(plan, script, frames, durs, voice_wav, out_mp4, run_dir / "hf_v2")
    print(f"  -> {out_mp4}")
