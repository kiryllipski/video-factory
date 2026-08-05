#!/usr/bin/env python3
"""
engine.py — оркестратор ОДНОГО ролика (runtime-конвейер). См. ARCHITECTURE.md §3.

СТАТУС: скелет Фазы 0 (дизайн, НЕ продакшен). Стадии 1–4 подключены к реальным раннерам;
стадии 5–6 (audio/assembly через hyperframes) — заглушки с TODO. Запуск требует явного флага
и не публикует ничего. Цель файла — зафиксировать проводку стадий и контрактов.

Проводка:
    тема → scriptwriter → compliance → visual_director → image_agent(Nano Banana 2)
         → [audio TODO] → [assembly hyperframes TODO] → qa
Каждая стадия пишет артефакт в runs/<channel>/<date>_<slug>/ и стоимость в cost.json (cost_tracker).
"""
from __future__ import annotations
import os
import sys
import json
import random
import shutil
import argparse
import datetime
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "orchestration"))  # gemini_agent, image_agent
sys.path.insert(0, str(Path(__file__).resolve().parent))  # schemas

# Готовые ролики доставляются сюда (внешнее хранилище iCloud, освобождает диск Mac).
# runs/<channel>/<slug>/ остаётся рабочей копией (script/frames/audio/hf/json) — не переносится.
DELIVERY_ROOT = Path(os.environ.get(
    "VIDEO_DELIVERY_ROOT",
    "/Users/kirillipski/Library/Mobile Documents/com~apple~CloudDocs/external storage/video/0.5",
))


_FS_UNSAFE = str.maketrans({c: " " for c in '/\\:*?"<>|\n\r\t'})


def _title_filename(run_dir: Path, fallback_stem: str) -> str:
    """Имя финального файла = заголовок ролика из publish_package.json (стадия 9), очищенный
    от небезопасных для файловой системы символов. Если пакета/заголовка нет — fallback на slug
    прогона. Польские буквы сохраняем (APFS/iCloud их держат). Требование владельца 2026-07-10:
    финальное видео называется по заголовку, а не безликим out.mp4."""
    title = ""
    pkg = run_dir / "publish_package.json"
    if pkg.exists():
        try:
            title = (json.loads(pkg.read_text(encoding="utf-8")).get("title") or "").strip()
        except Exception:
            title = ""
    stem = title.translate(_FS_UNSAFE) if title else fallback_stem
    stem = " ".join(stem.split()).strip(" .")   # схлопнуть пробелы, убрать хвостовые точки/пробелы
    stem = stem[:120].strip(" .")               # длина заголовка YouTube ≤100, оставим запас
    return (stem or fallback_stem) + ".mp4"


def deliver(run_dir: Path, channel: str, out_mp4: Path) -> Path:
    """Копирует финальный mp4 в DELIVERY_ROOT/<channel>/<run_dir.name>/, называя файл по заголовку
    ролика (publish_package.json). См. ARCHITECTURE.md §1 / §7."""
    dest_dir = DELIVERY_ROOT / channel / run_dir.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / _title_filename(run_dir, out_mp4.stem)
    shutil.copy2(out_mp4, dest)
    print(f"[delivered] {dest}")
    return dest

from gemini_agent import run_structured, run_agent           # noqa: E402
from image_agent import generate_image                       # noqa: E402
from audio_agent import generate_speech                       # noqa: E402
import schemas                                                # noqa: E402
import assembly                                               # noqa: E402

PROMPTS = Path(__file__).resolve().parent / "prompts"
CHANNELS = Path(__file__).resolve().parent / "channels"
LEARNING = Path(__file__).resolve().parent / "learning"

# Голос/подача/скорость озвучки по каналу (Gemini TTS).
# "tired"/"measured pace"/"calm" в style модель воспринимает буквально и говорит медленно —
# убраны из формулировок; speed — доп. ffmpeg atempo поверх сгенерированного WAV (см. audio_agent.py).
CHANNEL_VOICE = {
    "biz_failures": ("Charon", "wise, cynical baritone, sharp", 1.25),
    "psychology":   ("Kore",   "intriguing, insightful, energetic", 1.15),
    "wealth_viz":   ("Orus",   "confident, clear, authoritative", 1.15),
    "vitallogic_bad_pl": ("Aoede", "warm, caring, trustworthy, clear Polish articulation", 1.15),
}


def _role(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def _channel_ctx(channel: str) -> str:
    return (CHANNELS / channel / "studio_context.md").read_text(encoding="utf-8")


def _learnings_ctx(channel: str) -> str:
    """Закрытые гипотезы обучающего контура (learning_loop.py) — выводы, которые должны
    менять следующий сценарий, а не оседать декоративно в HYPOTHESES.md."""
    path = LEARNING / "learnings.json"
    if not path.exists():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = [e for e in data.get("entries", []) if e.get("channel", channel) == channel]
    if not entries:
        return ""
    lines = [f"- [{e['id']}] {e['insight']} → {e['how_to_apply']}" for e in entries]
    return "LEARNINGS (проверенные выводы прошлых роликов, применяй по умолчанию):\n" + "\n".join(lines)


# --- Стадия 1: сценарий ---------------------------------------------------------
def write_script(channel: str, topic: str, rubric: str, hook_formula: str) -> schemas.Script:
    ctx = _channel_ctx(channel)
    learnings = _learnings_ctx(channel)
    blocks = [f"STUDIO_CONTEXT:\n{ctx}"]
    if learnings:
        blocks.append(learnings)
    blocks.append(f"TOPIC: {topic}\nRUBRIC: {rubric}\nHOOK_FORMULA: {hook_formula}")
    user = "\n\n".join(blocks)
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
_NEGATIVE = ("NEGATIVE: over-saturated, deep-fried colors, 3d render, plastic skin, cartoon, "
             "mutated geometry, extra limbs, random text, watermark, logo, white border, "
             "photo frame, polaroid frame, paper margin, framed print, rounded photo corners, "
             "readable text, typography, captions, subtitles, labels, diagram annotations, "
             "infographic text, paragraphs, written words rendered in the image, text overlays — "
             "image must bleed to all four edges of the canvas and contain NO letters or words anywhere.")


def generate_frames(plan: schemas.FramePlan, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, fr in enumerate(plan.frames):
        # консистентность: подаём уже сгенерированные кадры как refs (до 14)
        refs = [str(p) for p in paths[-14:]] if fr.ref_ids else []
        style = f"{fr.prompt}\nGRADE: {plan.grade}. LIGHT: {plan.light}. LENS: {plan.lens}.\n{_NEGATIVE}"
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


def _node22_env() -> dict:
    """hyperframes CLI требует Node 20+ (util.styleText); системный default через nvm — v18.
    v2 (2026-07-13): хелпер переехал в assembly._node22_env (теперь и `hyperframes render`
    в сборке использует его, а не системный PATH); здесь — тонкий делегат для legacy-кода."""
    return assembly._node22_env()


def _transcribe_words(wav_path: Path, lang: str, offset: float, out_dir: Path) -> list[dict]:
    """⚠️ LEGACY, больше не вызывается из `synth_audio` (см. `_estimate_word_timestamps`, 2026-07-05).
    ASR-транскрипция гадает слова по звуку заново — для не-EN языков (PL) даёт неверные слова, не
    только сбои Node. Оставлено только для истории/воспроизводимости `_reassemble_fixed.py`.

    Пословные тайминги бита через `hyperframes transcribe` (whisper), сдвинутые на offset (сек)
    так, чтобы лечь в общую шкалу времени склеенной озвучки. --optional → тихо возвращает [], если
    whisper ДЕЙСТВИТЕЛЬНО недоступен (пайплайн продолжает работать на фолбэке on_screen_text).
    Настоящие сбои (например неверный Node) — печатаем предупреждение, а не проглатываем молча."""
    proc = subprocess.run(
        ["npx", "--yes", "hyperframes", "transcribe", str(wav_path),
         "--json", "--language", lang, "--dir", str(out_dir), "--optional"],
        capture_output=True, text=True, env=_node22_env(),
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        print(f"[WARN] hyperframes transcribe failed for {wav_path.name} "
              f"(rc={proc.returncode}) — falling back to keyword on_screen_text caption.\n"
              f"stderr: {proc.stderr.strip()[-500:]}", file=sys.stderr)
        return []
    try:
        meta = json.loads(proc.stdout)
        transcript_path = meta.get("transcriptPath")
        if not meta.get("ok") or not transcript_path:
            print(f"[WARN] hyperframes transcribe returned ok=false for {wav_path.name} — "
                  f"falling back to keyword on_screen_text caption.", file=sys.stderr)
            return []
        words = json.loads(Path(transcript_path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"[WARN] hyperframes transcribe output unparsable for {wav_path.name}: {e} — "
              f"falling back to keyword on_screen_text caption.", file=sys.stderr)
        return []
    return [{"text": w["text"], "start": round(w["start"] + offset, 3),
             "end": round(w["end"] + offset, 3)} for w in words]


def _estimate_word_timestamps(text: str, duration_sec: float, offset: float) -> list[dict]:
    """Оценивает пословные тайминги ПРОПОРЦИОНАЛЬНО ДЛИНЕ СЛОВА (символов) — без ASR/whisper.
    Портировано 2026-07-05 из `../creative production scheme/autopilot_factory/engine.py`
    (`get_word_timestamps`) взамен `_transcribe_words`.

    Почему не whisper: транскрипция заново РАСПОЗНАЁТ текст по звуку — но текст уже известен
    (это наш же `voiceover`), нужен только тайминг. Для не-EN языков (напр. PL) базовая whisper-
    модель `small.en` путает слова («Wapń z nabiału» → «Wapnis na biało», реальный кейс
    2026-07-05 на VitalLogic) — а `large-v3` (мультиязычная) падает с ошибкой выполнения на этой
    машине. Оценка по длине слова не идеальна (не слышит настоящие паузы TTS), но НИКОГДА не
    показывает неправильные слова — не ASR-задача, а просто раскладка уже известного текста по
    известной длительности. Языконезависимо, бесплатно, без внешних процессов/моделей."""
    words = text.split()
    if not words:
        return []
    char_counts = [max(len(w), 1) for w in words]
    total_chars = sum(char_counts)
    gap_fraction = 0.05
    gap = (duration_sec * gap_fraction) / max(len(words) - 1, 1)
    usable = duration_sec * (1 - gap_fraction)
    result, cursor = [], 0.0
    for word, chars in zip(words, char_counts):
        word_dur = usable * (chars / total_chars)
        result.append({"text": word, "start": round(offset + cursor, 3),
                        "end": round(offset + cursor + word_dur, 3)})
        cursor += word_dur + gap
    return result


def synth_audio(channel: str, script: schemas.Script, out_dir: Path):
    """Озвучивает каждый бит отдельно (Gemini TTS), обрезает тишину на стыках, оценивает
    пословные тайминги (без ASR, см. `_estimate_word_timestamps`) для караоке-субтитров,
    склеивает в voice.wav. Возвращает (voice_wav, per_beat_durations, per_beat_words)."""
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
        beat_words.append(_estimate_word_timestamps(beat.voiceover, d, cumulative))
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
def _channel_bgm(channel: str) -> Path | None:
    """v4 (владелец 2026-08-04): случайный трек из пула channels/<ch>/assets/bgm/ — один
    трек навсегда звучал одинаково на каждом ролике. Настроение пула держит бренд, конкретный
    файл внутри — ротируется. Нет файлов/канала → None (сборка без музыки, прежнее поведение)."""
    if not channel:
        return None
    bgm_dir = CHANNELS / channel / "assets" / "bgm"
    if not bgm_dir.is_dir():
        return None
    tracks = [p for p in sorted(bgm_dir.iterdir()) if p.suffix.lower() in (".wav", ".mp3", ".m4a", ".flac")]
    return random.choice(tracks) if tracks else None


def assemble(plan: schemas.FramePlan, script: schemas.Script, frames: list[Path],
             durations: list[float], beat_words: list[list[dict]], voice_wav: Path,
             out_mp4: Path, work_dir: Path, channel: str = "", skin: str = "photo") -> Path:
    # субтитры — пословные (whisper-тайминг), группами по CaptionStyle.words_on_screen;
    # если для бита распознавание не удалось — фолбэк на on_screen_text на весь бит.
    fallback_captions = [(b.on_screen_text or "") for b in script.beats]
    cap_style = schemas.CaptionStyle()
    motions = [f.motion for f in plan.frames]
    # v2: постер-заголовок первого кадра — poster_text сценария; для старых прогонов без
    # поля — фолбэк на on_screen_text первого бита (кадр-0 = «обложка» в ленте Shorts).
    headline = (getattr(script, "poster_text", "") or "").strip() or \
               (script.beats[0].on_screen_text or "").strip()
    # v3: финальная CTA-плашка (петля к постеру) + BGM-подложка канала.
    cta_text = (getattr(script, "cta_plate", "") or "").strip()
    # skin — типографический скин сборки (`photo` продакшен / `collage` эксперимент v5).
    return assembly.build_and_render(frames, beat_words, fallback_captions, durations, motions,
                                     cap_style, voice_wav, out_mp4, work_dir,
                                     headline=headline, cta_text=cta_text,
                                     bgm_wav=_channel_bgm(channel), skin=skin)


# --- Стадия 7: QA (advisory, gemini-2.5-flash, НЕ блокирует прогон) --------------
def qa(script: schemas.Script, plan: schemas.FramePlan) -> schemas.QAReport:
    user = f"SCRIPT_JSON:\n{script.model_dump_json()}\n\nFRAME_PLAN_JSON:\n{plan.model_dump_json()}"
    data = run_structured("flash", system=_role("qa"), user=user,
                          schema=schemas.QAReport, temperature=0.3)
    return schemas.QAReport(**data)


def produce(channel: str, topic: str, rubric: str, hook_formula: str, go: bool = False) -> Path:
    """Один ролик end-to-end. Без go=True выполняет только безопасные стадии (script/compliance/frameplan)."""
    slug = topic.lower().replace(" ", "-")[:40]
    run_dir = _ROOT / "autopilot_factory" / "runs" / channel / f"{datetime.date.today()}_{slug}"
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
    assemble(plan, script, frames, durations, beat_words, voice_wav, out_mp4, run_dir / "hf",
             channel=channel)  # стадия 6
    deliver(run_dir, channel, out_mp4)  # копия финала в DELIVERY_ROOT (iCloud)

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
