#!/usr/bin/env python3
"""
engine.py — оркестратор ОДНОГО ролика (runtime-конвейер). См. ARCHITECTURE.md §3.

СТАТУС: скелет Фазы 0 (дизайн, НЕ продакшен). Стадии 1–4 подключены к реальным раннерам;
стадии 5–6 (audio/assembly через hyperframes) — заглушки с TODO. Запуск требует явного флага
и не публикует ничего. Цель файла — зафиксировать проводку стадий и контрактов.

Проводка:
    тема → scriptwriter → compliance → visual_director → image_agent(Nano Banana 2)
         → [audio TODO] → [assembly hyperframes TODO] → qa
Каждая стадия пишет артефакт в runs/<date>_<slug>/ и стоимость в cost.json (cost_tracker).
"""
from __future__ import annotations
import os
import sys
import json
import argparse
import datetime
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "orchestration"))  # gemini_agent, image_agent
sys.path.insert(0, str(Path(__file__).resolve().parent))  # schemas

from gemini_agent import run_structured, run_agent           # noqa: E402
from image_agent import generate_image                       # noqa: E402
from audio_agent import generate_speech                       # noqa: E402
import schemas                                                # noqa: E402
import assembly                                               # noqa: E402

PROMPTS = Path(__file__).resolve().parent / "prompts"
CHANNELS = Path(__file__).resolve().parent / "channels"

# Голос/подача/скорость озвучки по каналу (Gemini TTS).
# "tired"/"measured pace"/"calm" в style модель воспринимает буквально и говорит медленно —
# убраны из формулировок; speed — доп. ffmpeg atempo поверх сгенерированного WAV (см. audio_agent.py).
CHANNEL_VOICE = {
    "biz_failures": ("Charon", "wise, cynical baritone, sharp", 1.25),
    "psychology":   ("Kore",   "intriguing, insightful, energetic", 1.15),
    "wealth_viz":   ("Orus",   "confident, clear, authoritative", 1.15),
}


def _role(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def _channel_ctx(channel: str) -> str:
    return (CHANNELS / channel / "studio_context.md").read_text(encoding="utf-8")


# --- Стадия 1: сценарий ---------------------------------------------------------
def write_script(channel: str, topic: str, rubric: str, hook_formula: str) -> schemas.Script:
    ctx = _channel_ctx(channel)
    user = f"STUDIO_CONTEXT:\n{ctx}\n\nTOPIC: {topic}\nRUBRIC: {rubric}\nHOOK_FORMULA: {hook_formula}"
    data = run_structured("flash35", system=_role("scriptwriter"), user=user,
                          schema=schemas.Script, temperature=1.0)
    return schemas.Script(**data)


# --- Стадия 2: комплаенс --------------------------------------------------------
def check_compliance(channel: str, script: schemas.Script) -> schemas.ComplianceVerdict:
    ctx = _channel_ctx(channel)
    user = f"STUDIO_CONTEXT:\n{ctx}\n\nSCRIPT_JSON:\n{script.model_dump_json()}"
    data = run_structured("pro", system=_role("compliance"), user=user,
                          schema=schemas.ComplianceVerdict, temperature=0.2)
    return schemas.ComplianceVerdict(**data)


# --- Стадия 3: план кадров ------------------------------------------------------
def plan_frames(channel: str, script: schemas.Script) -> schemas.FramePlan:
    ctx = _channel_ctx(channel)
    user = f"STUDIO_CONTEXT:\n{ctx}\n\nSCRIPT_JSON:\n{script.model_dump_json()}"
    data = run_structured("pro", system=_role("visual_director"), user=user,
                          schema=schemas.FramePlan, temperature=0.6)
    return schemas.FramePlan(**data)


# --- Стадия 4: кадры (Nano Banana 2, refs для консистентности) ------------------
def generate_frames(plan: schemas.FramePlan, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, fr in enumerate(plan.frames):
        # консистентность: подаём уже сгенерированные кадры как refs (до 14)
        refs = [str(p) for p in paths[-14:]] if fr.ref_ids else []
        style = f"{fr.prompt}\nGRADE: {plan.grade}. LIGHT: {plan.light}. LENS: {plan.lens}."
        p = out_dir / f"frame_{i:02d}.png"
        generate_image("img", style, aspect_ratio="9:16", out=str(p), refs=refs)  # ВСЕГДА Nano Banana 2
        paths.append(p)
    return paths


# --- Стадия 5: аудио (Gemini TTS, per-beat для точного тайминга) -----------------
def _wav_dur(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0.0)


def _trim_silence(path: Path) -> None:
    """Срезает служебную тишину TTS в начале/конце файла (не трогает паузы внутри речи) —
    иначе она накапливается при склейке per-beat WAV и субтитры уезжают от голоса к концу ролика.

    ВАЖНО: `stop_periods` в silenceremove реагирует на ЛЮБУЮ внутреннюю паузу между словами/фразами
    (не умеет отличать «пауза перед новой фразой» от «конец файла») — со start_silence/stop_silence=0.05с
    это обрезало речь на середине первой же межсловной паузы (баг, найден 2026-07-03 на реальном
    прогоне: биты 3.5-4с превращались в 0.1-0.7с). Правильный приём — трим только `start_periods`
    (реагирует один раз, на самый первый силенс от начала потока), а для конца — тот же трюк
    в развёрнутом (`areverse`) аудио, что превращает хвостовую тишину в головную."""
    tmp = path.with_suffix(".trim.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(path), "-af",
         "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
         "areverse,"
         "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
         "areverse",
         str(tmp)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp.replace(path)


def _transcribe_words(wav_path: Path, lang: str, offset: float, out_dir: Path) -> list[dict]:
    """Пословные тайминги бита через `hyperframes transcribe` (whisper), сдвинутые на offset (сек)
    так, чтобы лечь в общую шкалу времени склеенной озвучки. --optional → тихо возвращает [], если
    whisper недоступен (пайплайн продолжает работать на фолбэке on_screen_text)."""
    proc = subprocess.run(
        ["npx", "--yes", "hyperframes", "transcribe", str(wav_path),
         "--json", "--language", lang, "--dir", str(out_dir), "--optional"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    try:
        meta = json.loads(proc.stdout)
        transcript_path = meta.get("transcriptPath")
        if not meta.get("ok") or not transcript_path:
            return []
        words = json.loads(Path(transcript_path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [{"text": w["text"], "start": round(w["start"] + offset, 3),
             "end": round(w["end"] + offset, 3)} for w in words]


def synth_audio(channel: str, script: schemas.Script, out_dir: Path):
    """Озвучивает каждый бит отдельно (Gemini TTS), обрезает тишину на стыках, транскрибирует
    (whisper через hyperframes) для пословных караоке-субтитров, склеивает в voice.wav.
    Возвращает (voice_wav, per_beat_durations, per_beat_words)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    voice, style, speed = CHANNEL_VOICE.get(channel, ("Charon", "", 1.15))
    beat_wavs, durs, beat_words = [], [], []
    cumulative = 0.0
    for i, beat in enumerate(script.beats):
        w = out_dir / f"beat{i}.wav"
        generate_speech(beat.voiceover, voice=voice, style=style, out=str(w), speed=speed)
        _trim_silence(w)
        beat_wavs.append(w)
        d = _wav_dur(w)
        durs.append(d)
        beat_words.append(_transcribe_words(w, script.lang, cumulative, out_dir))
        cumulative += d
    # склейка concat-демуксером (одинаковый формат WAV у всех битов)
    lst = out_dir / "concat.txt"
    lst.write_text("".join(f"file '{w.name}'\n" for w in beat_wavs), encoding="utf-8")
    voice_wav = out_dir / "voice.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(voice_wav)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return voice_wav, durs, beat_words


# --- Стадия 6: сборка (hyperframes → немой mp4 → мукс озвучки) -------------------
def assemble(plan: schemas.FramePlan, script: schemas.Script, frames: list[Path],
             durations: list[float], beat_words: list[list[dict]], voice_wav: Path,
             out_mp4: Path, work_dir: Path) -> Path:
    # субтитры — пословные (whisper-тайминг), группами по CaptionStyle.words_on_screen;
    # если для бита распознавание не удалось — фолбэк на on_screen_text на весь бит.
    fallback_captions = [(b.on_screen_text or "") for b in script.beats]
    cap_style = schemas.CaptionStyle()
    motions = [f.motion for f in plan.frames]
    return assembly.build_and_render(frames, beat_words, fallback_captions, durations, motions,
                                     cap_style, voice_wav, out_mp4, work_dir)


# --- Стадия 7: QA (advisory, gemini-2.5-flash, НЕ блокирует прогон) --------------
def qa(script: schemas.Script, plan: schemas.FramePlan) -> schemas.QAReport:
    user = f"SCRIPT_JSON:\n{script.model_dump_json()}\n\nFRAME_PLAN_JSON:\n{plan.model_dump_json()}"
    data = run_structured("flash", system=_role("qa"), user=user,
                          schema=schemas.QAReport, temperature=0.3)
    return schemas.QAReport(**data)


def produce(channel: str, topic: str, rubric: str, hook_formula: str, go: bool = False) -> Path:
    """Один ролик end-to-end. Без go=True выполняет только безопасные стадии (script/compliance/frameplan)."""
    slug = topic.lower().replace(" ", "-")[:40]
    run_dir = _ROOT / "autopilot_factory" / "runs" / f"{datetime.date.today()}_{slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("RUN_COST_DIR", str(run_dir))  # cost_tracker пишет сюда

    script = write_script(channel, topic, rubric, hook_formula)
    (run_dir / "script.json").write_text(script.model_dump_json(indent=2), encoding="utf-8")

    verdict = check_compliance(channel, script)
    (run_dir / "compliance.json").write_text(verdict.model_dump_json(indent=2), encoding="utf-8")
    if not verdict.passed:
        script = verdict.cleaned_script  # используем очищенный вариант

    plan = plan_frames(channel, script)
    (run_dir / "frame_plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    if not go:
        print(f"[dry] script/compliance/frame_plan готовы → {run_dir} (стадии 4–7 требуют --go)")
        return run_dir

    frames = generate_frames(plan, run_dir / "frames")                             # стадия 4
    voice_wav, durations, beat_words = synth_audio(channel, script, run_dir / "audio")  # стадия 5
    out_mp4 = run_dir / "out.mp4"
    assemble(plan, script, frames, durations, beat_words, voice_wav, out_mp4, run_dir / "hf")  # стадия 6

    # стадия 7 — QA ТОЛЬКО фиксирует выводы, не останавливает прогон
    try:
        report = qa(script, plan)
        (run_dir / "qa.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        print(f"[qa] passed={report.passed} (advisory, не блокирует). Заметки: {len(report.notes)}")
    except Exception as e:
        print(f"[qa] пропущен (не критично): {e}")

    print(f"[done] {out_mp4}")
    return run_dir


def main():
    p = argparse.ArgumentParser(description="engine.py — оркестратор одного ролика (скелет Фазы 0)")
    p.add_argument("--channel", default="biz_failures")
    p.add_argument("--topic", required=True)
    p.add_argument("--rubric", default="Fatal Decisions")
    p.add_argument("--hook", default="Противоречие фактов")
    p.add_argument("--go", action="store_true", help="запустить стадии 4–7 (генерация/сборка) — по согласованию")
    args = p.parse_args()
    run_dir = produce(args.channel, args.topic, args.rubric, args.hook, go=args.go)
    print(f"[ok] run → {run_dir}")


if __name__ == "__main__":
    main()
