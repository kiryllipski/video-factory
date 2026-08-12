#!/usr/bin/env python3
"""
engine_v7.py — оркестратор одного ролика, версия 7.

Пять отличий от `engine.py` (v1-v6), в порядке влияния на результат:

1. **Формат вместо рубрики.** Ролик собирается по одному из 11 форматов (`schemas_v7.Format`),
   каждый со своей драматургией. Формат выбирается с учётом `style_memory` — повтор
   недавнего формата запрещён механически, а не пожеланием в промпте.

2. **Машинные гейты качества.** `validate_script` / `validate_plan` проверяют кодом то, что
   раньше было текстом в промпте и молча игнорировалось моделью: ритм, долю оверлеев,
   конкретику payload, ротацию крупности кадров, покрытие битов кадрами. Провал → одна
   попытка переписать с явным перечнем нарушений, потом отказ. Раньше QA был advisory
   и не блокировал ничего.

3. **Память стиля.** `style_memory()` собирает из прошлых прогонов форматы, первые слова
   хуков и типы оверлеев и отдаёт сценаристу как «этого не повторять». Раньше каждый прогон
   стартовал с чистого листа — и модель честно воспроизводила один и тот же шаблон.

4. **Модель уровня задачи.** Сценарий пишет `pro` (было `flash35`), судит `pro` (было `flash`).
   Текстовые вызовы — единицы центов при бюджете ролика $1, где 95% стоимости это картинки.

5. **Паузы в озвучке.** Между актами и перед payoff вставляется тишина. Раньше тишина
   срезалась в ноль на каждом стыке, и речь звучала как очередь.
"""
from __future__ import annotations
import os
import re
import sys
import json
import random
import shutil
import argparse
import datetime
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "orchestration"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gemini_agent import run_structured                        # noqa: E402
from image_agent import generate_image                         # noqa: E402
from audio_agent import generate_speech                        # noqa: E402
import schemas_v7 as S                                         # noqa: E402
import assembly_v7 as A                                        # noqa: E402
from engine import (deliver, _wav_dur, _trim_silence,          # noqa: E402
                    _estimate_word_timestamps, CHANNEL_VOICE)

PROMPTS = Path(__file__).resolve().parent / "prompts" / "v7"
CHANNELS = Path(__file__).resolve().parent / "channels"
LEARNING = Path(__file__).resolve().parent / "learning"
RUNS = Path(__file__).resolve().parent / "runs"

# Обобщения, которые убили предыдущую версию: сценарий из них состоял, зритель не уносил
# ничего. Проверяется по `payload` — там они запрещены безусловно.
_VAGUE_PL = [
    "niektóre badania", "badania są niejednoznaczne", "badania nie są jednoznaczne",
    "organizm decyduje", "wiele osób", "jest zdrowe", "jest korzystne", "wspiera organizm",
    "generalnie", "zazwyczaj pomaga", "może pomóc", "warto zadbać",
]
# Присутствие хотя бы одного — признак конкретики: число, единица измерения или форма вещества.
_CONCRETE = re.compile(
    r"(\d)|(\bmg\b)|(\bmcg\b)|(\bµg\b)|(\bIU\b)|(glicynian|cytrynian|tlenek|jabłczan|"
    r"metylokobalamin|cyjanokobalamin|cholekalcyferol|chelat|liposomaln|monohydrat)",
    re.IGNORECASE)


def _role(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def _channel_ctx(channel: str) -> str:
    """v7 читает свой конфиг канала. Старый `studio_context.md` остаётся у продакшен-пути v3
    и сюда не подаётся намеренно: его рубрики и формулы хуков — ровно то, что v7 ломает."""
    v7 = CHANNELS / channel / "studio_context_v7.md"
    path = v7 if v7.exists() else CHANNELS / channel / "studio_context.md"
    return path.read_text(encoding="utf-8")


def _learnings_ctx(channel: str) -> str:
    path = LEARNING / "learnings.json"
    if not path.exists():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = [e for e in data.get("entries", []) if e.get("channel", channel) == channel]
    if not entries:
        return ""
    lines = [f"- [{e['id']}] {e['insight']} → {e['how_to_apply']}" for e in entries]
    return "LEARNINGS (проверенные выводы прошлых роликов):\n" + "\n".join(lines)


# --- память стиля ---------------------------------------------------------------
def style_memory(channel: str, depth: int = 8) -> tuple[str, list[str]]:
    """Собирает из последних прогонов v7 то, что нельзя повторять. Возвращает (текст для
    промпта, список недавних форматов). Прогоны старых версий тоже учитываются — у них
    формата нет, но первое слово хука есть, и именно оно там всегда одно и то же."""
    runs = sorted((RUNS / channel).glob("*/script.json"), key=lambda p: p.stat().st_mtime,
                  reverse=True)[:depth]
    formats, openers, ovkinds = [], [], []
    for p in runs:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("format"):
            formats.append(d["format"])
        hook = (d.get("hook") or "").split()
        if hook:
            openers.append(hook[0].strip("?,.!").lower())
        ovkinds += [o.get("kind") for o in d.get("overlays", []) if o.get("kind")]
    if not (formats or openers):
        return "", []
    lines = ["STYLE_MEMORY — последние выпуски канала. НЕ ПОВТОРЯЙ это:"]
    if formats:
        lines.append(f"- уже использованные форматы (свежие первыми): {', '.join(formats)}")
    if openers:
        lines.append(f"- первые слова хуков: {', '.join(dict.fromkeys(openers))}")
    if ovkinds:
        top = ", ".join(dict.fromkeys(ovkinds))
        lines.append(f"- типы оверлеев: {top} — возьми другие, где это уместно")
    return "\n".join(lines), formats


def pick_format(channel: str, explicit: str = "") -> str:
    """Формат не может повториться, пока не выйдут два других (ротация — п.1 research/61).
    `mistake` дополнительно ограничен: это шаблон, которым канал уже перекормлен."""
    if explicit:
        return explicit
    _, recent = style_memory(channel, depth=8)
    banned = set(recent[:2])
    pool = [f for f in S.FORMAT_BRIEFS if f not in banned]
    if "mistake" in pool and random.random() > 0.12:
        pool.remove("mistake")               # ≤~12% выпусков вместо прежних 100%
    return random.choice(pool or list(S.FORMAT_BRIEFS))


# --- стадия 1: сценарий ---------------------------------------------------------
def _script_user(channel: str, topic: str, fmt: str, extra: str = "") -> str:
    mem, _ = style_memory(channel)
    blocks = [f"STUDIO_CONTEXT:\n{_channel_ctx(channel)}"]
    lr = _learnings_ctx(channel)
    if lr:
        blocks.append(lr)
    if mem:
        blocks.append(mem)
    blocks.append(f"FORMAT: {fmt}\nFORMAT_BRIEF: {S.FORMAT_BRIEFS[fmt]}")
    blocks.append(f"TOPIC: {topic}")
    if extra:
        blocks.append(extra)
    return "\n\n".join(blocks)


def validate_script(sc: S.Script) -> list[str]:
    """Машинные гейты сценария. Всё, что здесь проверяется, раньше было просьбой в промпте
    и молча не выполнялось — см. аудит §1.3 (0% битов короче 2с) и §2.2 (0 оверлеев)."""
    errs: list[str] = []
    n = len(sc.beats)

    hook_beats = [b for b in sc.beats if b.act == "hook"]
    if not (2 <= len(hook_beats) <= 3):
        errs.append(f"акт hook: нужно 2-3 бита, сейчас {len(hook_beats)}")
    if hook_beats and max(b.dur_s for b in hook_beats) > 1.7:
        errs.append("акт hook: биты должны быть 0.7-1.6с — сейчас есть длиннее 1.7с")
    if not any(b.dur_s <= 1.6 for b in sc.beats):
        errs.append("нет ни одного короткого бита (≤1.6с) — ритм снова ровный")

    if not any(b.act == "payoff" for b in sc.beats):
        errs.append("нет акта payoff")

    # порядок актов: hook → body → payoff, без чересполосицы
    order = [b.act for b in sc.beats]
    rank = {"hook": 0, "body": 1, "payoff": 2}
    if any(rank[order[i + 1]] < rank[order[i]] for i in range(len(order) - 1)):
        errs.append("акты идут не по порядку hook → body → payoff")

    if not (0 <= sc.turn_beat_idx < n):
        errs.append("turn_beat_idx вне диапазона битов")
    elif sc.beats[sc.turn_beat_idx].act != "body":
        errs.append("turn_beat_idx должен указывать на бит внутри акта body")

    covered = {o.beat_idx for o in sc.overlays}
    if any(not (0 <= i < n) for i in covered):
        errs.append("overlay ссылается на несуществующий бит")
    share = len(covered) / max(n, 1)
    if share < 0.35:
        errs.append(f"оверлеев на {share:.0%} битов, нужно ≥35% — информация должна быть на экране")
    if len(sc.overlays) != len(covered):
        errs.append("на одном бите больше одного оверлея")
    if any(o.beat_idx < len(sc.beats) and sc.beats[o.beat_idx].act == "hook"
           for o in sc.overlays):
        errs.append("в акте hook оверлеев быть не должно — там работает poster_text")

    low = sc.payload.lower()
    for v in _VAGUE_PL:
        if v in low:
            errs.append(f"payload содержит запрещённое обобщение «{v}»")
            break
    if not _CONCRETE.search(sc.payload):
        errs.append("в payload нет конкретики (числа/дозы/названия формы вещества)")

    body = " ".join(b.voiceover for b in sc.beats).lower()
    for w in ("leczy", "zapobiega", "choroba", "terapia"):
        if re.search(rf"\b{w}", body):
            errs.append(f"стоп-слово комплаенса в озвучке: «{w}»")

    if not sc.payoff_card.strip():
        errs.append("пустая payoff_card")
    elif sc.payoff_card.strip().endswith("?"):
        errs.append("payoff_card — вопрос; нужен вывод, а не вопрос")

    total = sum(b.dur_s for b in sc.beats)
    if not (18 <= total <= 45):
        errs.append(f"хронометраж {total:.1f}с вне диапазона 18-45с")

    poster_words = len(sc.poster_text.replace("*", "").split())
    if poster_words > 4:
        errs.append(f"poster_text из {poster_words} слов, нужно ≤4")
    return errs


def write_script(channel: str, topic: str, fmt: str) -> S.Script:
    user = _script_user(channel, topic, fmt)
    data = run_structured("pro", system=_role("scriptwriter"), user=user,
                          schema=S.Script, temperature=0.95)
    sc = S.Script(**data)
    errs = validate_script(sc)
    if errs:
        print(f"[script] гейты не пройдены ({len(errs)}), переписываю:")
        for e in errs:
            print(f"         · {e}")
        fix = ("ПРЕДЫДУЩАЯ ПОПЫТКА ОТКЛОНЕНА машинной проверкой. Исправь ИМЕННО это,\n"
               "остальное не ломай:\n" + "\n".join(f"- {e}" for e in errs) +
               f"\n\nОТКЛОНЁННЫЙ ВАРИАНТ:\n{sc.model_dump_json()}")
        data = run_structured("pro", system=_role("scriptwriter"),
                              user=_script_user(channel, topic, fmt, fix),
                              schema=S.Script, temperature=0.8)
        sc = S.Script(**data)
        errs2 = validate_script(sc)
        if errs2:
            raise SystemExit("[script] сценарий не проходит гейты и после переписывания:\n" +
                             "\n".join(f"  · {e}" for e in errs2))
    return sc


# --- стадия 2: комплаенс --------------------------------------------------------
def check_compliance(channel: str, sc: S.Script) -> S.ComplianceVerdict:
    user = f"STUDIO_CONTEXT:\n{_channel_ctx(channel)}\n\nSCRIPT_JSON:\n{sc.model_dump_json()}"
    data = run_structured("pro", system=_role("compliance"), user=user,
                          schema=S.ComplianceVerdict, temperature=0.2)
    return S.ComplianceVerdict(**data)


# --- стадия 3: план кадров ------------------------------------------------------
def validate_plan(plan: S.FramePlan, n_beats: int) -> list[str]:
    errs: list[str] = []
    frames = plan.frames
    if frames[0].beat_from != 0:
        errs.append("первый кадр не начинается с бита 0")
    if frames[-1].beat_to != n_beats - 1:
        errs.append(f"последний кадр заканчивается на бите {frames[-1].beat_to}, "
                    f"а битов {n_beats} — покрытие неполное")
    for i, f in enumerate(frames):
        if f.beat_to < f.beat_from:
            errs.append(f"кадр {i}: beat_to < beat_from")
        if i and f.beat_from != frames[i - 1].beat_to + 1:
            errs.append(f"кадр {i}: разрыв или наложение диапазонов битов")
        if len(f.claim.split()) < 3:
            errs.append(f"кадр {i}: claim слишком короткий, чтобы быть утверждением")
    for i in range(1, len(frames)):
        if frames[i].shot == frames[i - 1].shot:
            errs.append(f"кадры {i-1} и {i}: одинаковая крупность {frames[i].shot} подряд")
    if len({f.shot for f in frames}) < 3:
        errs.append("на ролик меньше трёх разных ступеней крупности")
    prod = [f.subject for f in frames]
    for i in range(2, len(prod)):
        if prod[i] == prod[i - 1] == prod[i - 2] == "product":
            errs.append(f"кадры {i-2}..{i}: три 'product' подряд")
            break
    return errs


def plan_frames(channel: str, sc: S.Script) -> S.FramePlan:
    user = (f"STUDIO_CONTEXT:\n{_channel_ctx(channel)}\n\n"
            f"SCRIPT_JSON:\n{sc.model_dump_json()}\n\n"
            f"Битов в сценарии: {len(sc.beats)} (индексы 0..{len(sc.beats)-1}). "
            f"Кадров сделай 6-10, они должны покрыть все биты подряд.")
    data = run_structured("pro", system=_role("visual_director"), user=user,
                          schema=S.FramePlan, temperature=0.75)
    plan = S.FramePlan(**data)
    errs = validate_plan(plan, len(sc.beats))
    if errs:
        print(f"[visual] гейты не пройдены ({len(errs)}), переписываю:")
        for e in errs:
            print(f"         · {e}")
        fix = ("\n\nПРЕДЫДУЩИЙ ПЛАН ОТКЛОНЁН машинной проверкой. Исправь ИМЕННО это:\n" +
               "\n".join(f"- {e}" for e in errs) + f"\n\nОТКЛОНЁННЫЙ ПЛАН:\n{plan.model_dump_json()}")
        data = run_structured("pro", system=_role("visual_director"), user=user + fix,
                              schema=S.FramePlan, temperature=0.6)
        plan = S.FramePlan(**data)
        errs2 = validate_plan(plan, len(sc.beats))
        if errs2:
            print("[visual] ВНИМАНИЕ: план всё ещё с замечаниями, чиню покрытие вручную:")
            for e in errs2:
                print(f"         · {e}")
            plan = _repair_coverage(plan, len(sc.beats))
    return plan


def _repair_coverage(plan: S.FramePlan, n_beats: int) -> S.FramePlan:
    """Последняя линия обороны: если модель дважды не смогла покрыть биты подряд —
    раскладываем диапазоны равномерно сами, сохраняя промпты и порядок кадров.
    Лучше ролик с чуть менее осмысленной нарезкой, чем упавший прогон."""
    frames = plan.frames
    k = len(frames)
    edges = [round(i * n_beats / k) for i in range(k)] + [n_beats]
    for i, f in enumerate(frames):
        f.beat_from = edges[i]
        f.beat_to = max(edges[i + 1] - 1, edges[i])
    return plan


# --- стадия 4: кадры ------------------------------------------------------------
_NEGATIVE = ("NEGATIVE: over-saturated, deep-fried colors, 3d render, plastic skin, cartoon, "
             "mutated geometry, extra limbs, random text, watermark, logo, white border, "
             "photo frame, polaroid frame, paper margin, framed print, rounded photo corners, "
             "readable text, typography, captions, subtitles, labels, diagram annotations, "
             "infographic text, paragraphs, written words rendered in the image, text overlays — "
             "image must bleed to all four edges of the canvas and contain NO letters or words anywhere.")


def generate_frames(plan: S.FramePlan, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, fr in enumerate(plan.frames):
        p = out_dir / f"frame_{i:02d}.png"
        if p.exists() and p.stat().st_size > 1000:
            print(f"[frames] {p.name} уже есть — пропускаю (resume)")
            paths.append(p)
            continue
        # лимит модели — 3 reference-изображения; раньше слали 14 и получали дрейф стиля
        refs = [str(x) for x in paths[-3:]] if fr.ref_ids else []
        prompt = (f"{fr.prompt}\nGRADE: {plan.grade}. LIGHT: {plan.light}. LENS: {plan.lens}.\n"
                  f"{_NEGATIVE}")
        generate_image("img", prompt, aspect_ratio="9:16", out=str(p), refs=refs)
        paths.append(p)
    return paths


# --- стадия 5: озвучка ----------------------------------------------------------
def _silence(path: Path, seconds: float) -> None:
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"anullsrc=r=24000:cl=mono", "-t", f"{seconds:.3f}",
                    "-c:a", "pcm_s16le", str(path)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def synth_audio(channel: str, sc: S.Script, out_dir: Path):
    """v7: между актами и перед payoff вставляется пауза. Раньше тишина срезалась в ноль
    на каждом стыке (`_trim_silence`), и биты склеивались встык — речь звучала как очередь
    (research/59 §6). Тишина учитывается в длительности бита, поэтому графика и субтитры
    остаются синхронными."""
    out_dir.mkdir(parents=True, exist_ok=True)
    voice, style, speed = CHANNEL_VOICE.get(channel, ("Aoede", "", 1.15))
    pieces: list[Path] = []
    durs: list[float] = []
    beat_words: list[list[dict]] = []
    cumulative = 0.0
    acts = [b.act for b in sc.beats]

    for i, beat in enumerate(sc.beats):
        w = out_dir / f"beat{i}.wav"
        if not (w.exists() and w.stat().st_size > 1000):
            generate_speech(beat.voiceover, voice=voice, style=style, out=str(w), speed=speed)
            _trim_silence(w)
        d = _wav_dur(w)
        beat_words.append(_estimate_word_timestamps(beat.voiceover, d, cumulative))
        pieces.append(w)

        # пауза ПОСЛЕ бита: на границе актов длиннее, перед поворотом — короткий вдох
        pause = 0.0
        if i + 1 < len(sc.beats) and acts[i + 1] != acts[i]:
            pause = 0.34
        elif i + 1 == sc.turn_beat_idx:
            pause = 0.22
        if pause:
            sp = out_dir / f"pause{i}.wav"
            _silence(sp, pause)
            pieces.append(sp)
        durs.append(d + pause)
        cumulative += d + pause

    lst = out_dir / "concat.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in pieces), encoding="utf-8")
    voice_wav = out_dir / "voice.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(voice_wav)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return voice_wav, durs, beat_words


# --- стадия 7: QA ---------------------------------------------------------------
def qa(channel: str, sc: S.Script, plan: S.FramePlan) -> S.QAReport:
    mem, _ = style_memory(channel)
    user = (f"{mem}\n\nSCRIPT_JSON:\n{sc.model_dump_json()}\n\n"
            f"FRAME_PLAN_JSON:\n{plan.model_dump_json()}")
    data = run_structured("pro", system=_role("qa"), user=user,
                          schema=S.QAReport, temperature=0.25)
    return S.QAReport(**data)


def _channel_bgm(channel: str) -> Path | None:
    bgm_dir = CHANNELS / channel / "assets" / "bgm"
    if not bgm_dir.is_dir():
        return None
    tracks = [p for p in sorted(bgm_dir.iterdir())
              if p.suffix.lower() in (".wav", ".mp3", ".m4a", ".flac")]
    return random.choice(tracks) if tracks else None


# --- прогон ---------------------------------------------------------------------
def produce(channel: str, topic: str, fmt: str = "", slug: str = "", go: bool = False) -> Path:
    fmt = pick_format(channel, fmt)
    slug = slug or re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:40]
    run_dir = RUNS / channel / f"{datetime.date.today()}_{slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    os.environ["RUN_COST_DIR"] = str(run_dir)
    print(f"[v7] {slug} · формат={fmt}")

    sc = write_script(channel, topic, fmt)
    (run_dir / "script.json").write_text(sc.model_dump_json(indent=2), encoding="utf-8")

    verdict = check_compliance(channel, sc)
    (run_dir / "compliance.json").write_text(verdict.model_dump_json(indent=2), encoding="utf-8")
    if not verdict.passed:
        cleaned = verdict.cleaned_script
        if validate_script(cleaned):
            print("[compliance] очищенный сценарий ломает гейты — оставляю исходный, "
                  "правки только в fixes")
        else:
            sc = cleaned
            (run_dir / "script.json").write_text(sc.model_dump_json(indent=2), encoding="utf-8")

    plan = plan_frames(channel, sc)
    (run_dir / "frame_plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    try:
        report = qa(channel, sc, plan)
        (run_dir / "qa.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        failed = [c.name for c in report.checks if not c.passed]
        print(f"[qa] passed={report.passed}" + (f" · провалено: {', '.join(failed)}" if failed else ""))
    except Exception as e:
        print(f"[qa] пропущен: {e}")

    if not go:
        print(f"[dry] сценарий/комплаенс/кадровый план готовы → {run_dir}")
        return run_dir

    frames = generate_frames(plan, run_dir / "frames")
    voice_wav, durs, beat_words = synth_audio(channel, sc, run_dir / "audio")
    spans = [(f.beat_from, f.beat_to) for f in plan.frames]
    motions = [f.motion for f in plan.frames]
    out_mp4 = run_dir / "out.mp4"
    A.build_and_render(
        frames, spans, motions, beat_words,
        [b.on_screen_text for b in sc.beats], durs, sc.overlays,
        [b.emphasis for b in sc.beats], voice_wav, out_mp4, run_dir / "hf",
        headline=sc.poster_text, payoff_text=sc.payoff_card,
        turn_beat_idx=sc.turn_beat_idx, bgm_wav=_channel_bgm(channel))

    (run_dir / "run_meta.json").write_text(json.dumps({
        "pipeline_version": S.PIPELINE_VERSION, "format": fmt,
        "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] {out_mp4}")
    return run_dir


def main():
    p = argparse.ArgumentParser(description="engine_v7.py — оркестратор ролика v7")
    p.add_argument("--channel", default="vitallogic_bad_pl")
    p.add_argument("--topic", required=True)
    p.add_argument("--format", default="", help=f"один из: {', '.join(S.FORMAT_BRIEFS)}")
    p.add_argument("--slug", default="")
    p.add_argument("--go", action="store_true", help="запустить генерацию кадров/озвучки/сборку")
    a = p.parse_args()
    produce(a.channel, a.topic, a.format, a.slug, go=a.go)


if __name__ == "__main__":
    main()
