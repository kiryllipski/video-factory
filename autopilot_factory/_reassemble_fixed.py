#!/usr/bin/env python3
"""Переассемблирование прогонов, пострадавших от бага тихого отказа транскрипции (2026-07-04):
whisper падал под Node18, субтитры откатывались на короткий on_screen_text для всего ролика.
Фикс — engine._transcribe_words (Node22 в PATH + явный WARN). Здесь НЕ трогаем TTS/кадры —
только заново транскрибируем уже готовые per-beat WAV и пересобираем HTML/видео. Бесплатно
(никаких новых вызовов Gemini), кроме fedex, где дополнительно кропаем впечатанную белую рамку.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "orchestration"))

import engine
import schemas

ROOT = Path(__file__).resolve().parent / "runs"

# (run_dir_name, channel, audio_subdir, frames_subdir, frame_plan_file, out_name, hf_name, crop_border)
JOBS = [
    ("2026-07-01_the-ceo-who-refused-to-buy-netflix-for-5", "biz_failures",
     "audio_v2", "frames", "frame_plan.json", "out_v3.mp4", "hf_v3", False),
    ("2026-07-03_kodak-invented-digital-cameras-and-sued-", "biz_failures",
     "audio_v2", "frames", "frame_plan.json", "out_v3.mp4", "hf_v3", False),
    ("2026-07-03_the-spotlight-effect:-why-nobody-notices", "psychology",
     "audio_v2", "frames_v2", "frame_plan_v2.json", "out_v4.mp4", "hf_v4", False),
    ("2026-07-03_fedex-saved-by-5000-in-vegas", "biz_failures",
     "audio", "frames_clean", "frame_plan.json", "out_v2.mp4", "hf_v2", True),
]


def _detect_border(arr, thresh=235):
    h, w, _ = arr.shape
    top = bottom = left = right = 0
    while top < h and np.mean(arr[top, :, :]) > thresh:
        top += 1
    while bottom < h and np.mean(arr[h - 1 - bottom, :, :]) > thresh:
        bottom += 1
    while left < w and np.mean(arr[:, left, :]) > thresh:
        left += 1
    while right < w and np.mean(arr[:, w - 1 - right, :]) > thresh:
        right += 1
    return top, bottom, left, right


def _make_clean_frames(run_dir: Path) -> Path:
    """Кропает впечатанную белую рамку (баг vignette, 2026-07-04) там, где она реально есть —
    per-frame детект, не трогает кадры без рамки (напр. frame_08/09/14 в fedex были чистые)."""
    src_dir = run_dir / "frames"
    dst_dir = run_dir / "frames_clean"
    dst_dir.mkdir(exist_ok=True)
    for f in sorted(src_dir.glob("frame_*.png")):
        im = Image.open(f).convert("RGB")
        arr = np.array(im)
        h, w, _ = arr.shape
        top, bottom, left, right = _detect_border(arr)
        if max(top, bottom, left, right) > 5:
            im = im.crop((left, top, w - right, h - bottom))
            print(f"    {f.name}: cropped border t{top}/b{bottom}/l{left}/r{right} -> {im.size}")
        im.save(dst_dir / f.name)
    return dst_dir


def main():
    for name, channel, audio_sub, frames_sub, plan_file, out_name, hf_name, crop in JOBS:
        run_dir = ROOT / name
        print(f"=== {name} ({channel}) ===")

        if crop:
            print("  [1/3] cropping baked-in white border (free, local)...")
            _make_clean_frames(run_dir)

        script = schemas.Script.model_validate_json((run_dir / "script.json").read_text())
        plan = schemas.FramePlan.model_validate_json((run_dir / plan_file).read_text())
        frames = sorted((run_dir / frames_sub).glob("frame_*.png"))
        print(f"  {len(frames)} frames from {frames_sub}, {len(script.beats)} beats")

        audio_dir = run_dir / audio_sub
        beat_wavs = [audio_dir / f"beat{i}.wav" for i in range(len(script.beats))]
        missing = [w for w in beat_wavs if not w.exists()]
        if missing:
            print(f"  !! missing wavs, skipping: {missing}")
            continue

        print("  [2/3] re-transcribing per-beat WAV (fixed Node22 path, free/local)...")
        durations, beat_words = [], []
        cumulative = 0.0
        for i, w in enumerate(beat_wavs):
            d = engine._wav_dur(w)
            durations.append(d)
            words = engine._transcribe_words(w, script.lang, cumulative, audio_dir)
            beat_words.append(words)
            print(f"    beat{i}: {d:.2f}s, {len(words)} words"
                  + ("  [FALLBACK on_screen_text]" if not words else ""))
            cumulative += d

        voice_wav = audio_dir / "voice.wav"
        if not voice_wav.exists():
            print(f"  !! no voice.wav in {audio_dir}, skipping")
            continue

        out_mp4 = run_dir / out_name
        print(f"  [3/3] assembling -> {out_mp4}")
        engine.assemble(plan, script, frames, durations, beat_words, voice_wav, out_mp4, run_dir / hf_name)
        print(f"  done: {out_mp4}\n")


if __name__ == "__main__":
    main()
