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
   Текстовые вызовы — единицы центов при бюджете ролика $3, где основная статья — картинки.

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
import signal
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "orchestration"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gemini_agent import run_agent, run_structured as _run_structured  # noqa: E402
from image_agent import generate_image as _generate_image       # noqa: E402
from audio_agent import generate_speech as _generate_speech    # noqa: E402
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
# Что считается конкретикой — зависит от рубрики (`RUBRIC_META[...]["payload_kind"]`).
#
# `substance` — число, единица или название формы вещества. Так было для ВСЕХ роликов до
# 2026-08-14, и это механически выдавливало канал обратно в дозировки: payload «переставь
# кофе на 40 минут позже» не содержит миллиграммов и не проходил гейт, поэтому сценарист
# всегда возвращался к банке с полки.
_CONCRETE_SUBSTANCE = re.compile(
    r"(\d)|(\bmg\b)|(\bmcg\b)|(\bµg\b)|(\bIU\b)|(glicynian|cytrynian|tlenek|jabłczan|"
    r"metylokobalamin|cyjanokobalamin|cholekalcyferol|chelat|liposomaln|monohydrat)",
    re.IGNORECASE)
# `action` — конкретное действие с условием, временем или порядком. Число тоже подходит:
# это ослабление требования, а не замена. Список глаголов/маркеров польский, потому что
# проверяем текст ролика, а не перевод.
_CONCRETE_ACTION = re.compile(
    r"(\d)"
    # действие: время/порядок
    r"|\b(przed|po|zanim|najpierw|potem|odczekaj|odstaw|przesuń|rozdziel|"
    # действие: что сделать с едой
    r"dodaj|zamień|zastąp|wyjmij|wyrzuć|ugotuj|zalej|podgrzej|schłodź|trzymaj|przechowuj|"
    r"połącz|łącz|nie łącz|nie pij|nie jedz|zjedz|wypij|posyp|skrop|"
    # действие: выбор (рейтинги и сравнения кончаются именно этим)
    r"wybierz|wybieraj|sięgnij|sięgaj|postaw na|unikaj|ogranicz|zrezygnuj|kupuj|nie kupuj|"
    r"szukaj|sprawdź|czytaj|"
    # мера и единица
    r"minut|godzin|dni|łyżk|szklank|porcj|garść|kromk|plaster)\b",
    re.IGNORECASE)

# Слова, которые выглядят как «данные», но не несут самостоятельного смысла. На скриншоте
# они создают вторую конкурирующую подпись рядом с числом (например, «энергия» над kcal).
_GENERIC_OVERLAY_LABELS = {
    "energia", "kalorie", "wartość", "wartosci", "wynik", "dane", "fakt", "poziom",
    "wskaźnik", "wskaznik", "rezultat", "informacja", "liczba",
}


def _overlay_norm(text: str) -> str:
    value = (text or "").lower()
    value = re.sub(r"[^0-9a-ząćęłńóśźż%°]+", " ", value, flags=re.IGNORECASE)
    return " ".join(value.split())


def _compact_comparison_value(text: str) -> bool:
    """Две колонки выдерживают число с единицей или одно слово, но не мини-абзацы."""
    value = _overlay_norm(text)
    if not value or len(value) > 14:
        return False
    return bool(re.search(r"\d", value)) or len(value.split()) == 1


def _compact_numeric_value(text: str) -> bool:
    """Числовой callout не должен превращаться во вторую реплику поверх субтитров."""
    value = (text or "").strip()
    return bool(re.fullmatch(r"[~≈<>≤≥+\-]?\s*\d[\d.,]*\s*[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż%°×/²³]*", value)) \
        and len(value) <= 14


def _payload_ok(payload: str, kind: str) -> bool:
    rx = _CONCRETE_SUBSTANCE if kind == "substance" else _CONCRETE_ACTION
    return bool(rx.search(payload))


def _role(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def _limited_call(fn, timeout_s: int = 180):
    """Не позволяет синхронному Gemini SDK retry блокировать всю производственную очередь."""
    previous = signal.getsignal(signal.SIGALRM)

    def _timeout(_signum, _frame):
        raise TimeoutError(f"Gemini call превысил {timeout_s}s")

    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(timeout_s)
    try:
        return fn()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def run_structured(*args, **kwargs):
    """v7 JSON-стадии получают тот же предел ожидания, что и research/vision вызовы."""
    return _limited_call(lambda: _run_structured(*args, **kwargs))


def generate_image(*args, **kwargs):
    """Один зависший image API retry не имеет права удерживать весь production run."""
    return _limited_call(lambda: _generate_image(*args, **kwargs))


def generate_speech(*args, **kwargs):
    """TTS подчиняется тем же границам времени, что текст, изображения и vision QA."""
    return _limited_call(lambda: _generate_speech(*args, **kwargs))


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
    formats, openers, ovkinds, rubrics, payloads = [], [], [], [], []
    for p in runs:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("format"):
            formats.append(d["format"])
        if d.get("rubric"):
            rubrics.append(d["rubric"])
        # Первое слово payload. Гейт конкретики (`_CONCRETE_ACTION`) — это ОТБОР, а отбор
        # по словарю однообразит: модель не видит списка, но получает отказы и сползает к
        # формуле «повелительный глагол + объект + время». Тем же лекарством, что и от
        # одинаковых хуков: показываем, чем payload начинался в прошлый раз.
        pw = (d.get("payload") or "").split()
        if pw:
            payloads.append(pw[0].strip(".,:;").lower())
        hook = (d.get("hook") or "").split()
        if hook:
            openers.append(hook[0].strip("?,.!").lower())
        ovkinds += [o.get("kind") for o in d.get("overlays", []) if o.get("kind")]
    if not (formats or openers):
        return "", []
    lines = ["STYLE_MEMORY — последние выпуски канала. НЕ ПОВТОРЯЙ это:"]
    if rubrics:
        lines.append(f"- рубрики последних выпусков (свежие первыми): {', '.join(rubrics)}")
    if formats:
        lines.append(f"- уже использованные форматы (свежие первыми): {', '.join(formats)}")
    if openers:
        lines.append(f"- первые слова хуков: {', '.join(dict.fromkeys(openers))}")
    if ovkinds:
        top = ", ".join(dict.fromkeys(ovkinds))
        lines.append(f"- типы оверлеев: {top} — возьми другие, где это уместно")
    if payloads:
        lines.append(f"- чем начинался payload: {', '.join(dict.fromkeys(payloads))} — "
                     f"конкретика обязательна, но форма фразы должна быть другой "
                     f"(не обязательно приказ: бывает цифра, правило выбора, срок, порядок)")
    return "\n".join(lines), formats


def recent_rubrics(channel: str, depth: int = 6) -> list[str]:
    runs = sorted((RUNS / channel).glob("*/script.json"), key=lambda p: p.stat().st_mtime,
                  reverse=True)[:depth]
    out = []
    for p in runs:
        try:
            r = json.loads(p.read_text(encoding="utf-8")).get("rubric")
        except Exception:
            continue
        if r:
            out.append(r)
    return out


def pick_rubric(channel: str, explicit: str = "") -> str:
    """Выбирает производственный контракт для уже найденной темы (см. `editorial_policy.md`).

    Серии разрешены: две подряд — норма (владелец 2026-08-14: «идти сериями по 2-3 ролика»),
    три подряд — уже монокультура, поэтому рубрика банится, если заняла 2 из последних 3
    выпусков. Внутри разрешённого пула fallback-выбор идёт по мягким весам `ACTIVE_RUBRICS`;
    это не ограничивает внешний поиск и не задаёт обязательный медиамикс."""
    if explicit:
        return explicit
    recent = recent_rubrics(channel, depth=3)
    pool = {r: w for r, w in S.ACTIVE_RUBRICS.items() if recent.count(r) < 2}
    if not pool:
        pool = dict(S.ACTIVE_RUBRICS)
    names, weights = list(pool), [pool[r] for r in pool]
    return random.choices(names, weights=weights, k=1)[0]


def pick_format(channel: str, explicit: str = "", rubric: str = "") -> str:
    """Формат не может повториться, пока не выйдут два других (ротация — п.1 research/61).
    Пул ограничен форматами, уместными в рубрике: `label_check` бессмысленен для кухонной
    химии, `anti_sell` — для привычек. `mistake` дополнительно ограничен: это шаблон,
    которым канал уже перекормлен."""
    if explicit:
        return explicit
    _, recent = style_memory(channel, depth=8)
    banned = set(recent[:2])
    allowed = S.rubric_formats(rubric) if rubric else list(S.FORMAT_BRIEFS)
    pool = [f for f in allowed if f not in banned]
    if "mistake" in pool and random.random() > 0.12:
        pool.remove("mistake")               # ≤~12% выпусков вместо прежних 100%
    return random.choice(pool or allowed or list(S.FORMAT_BRIEFS))


# --- стадия 1: сценарий ---------------------------------------------------------
_PAYLOAD_RULE = {
    "substance": ("payload обязан содержать ЧИСЛО (доза, процент, часы) или название формы "
                  "вещества — тема рубрики этого требует."),
    "action": ("payload обязан содержать КОНКРЕТНОЕ ДЕЙСТВИЕ с условием, временем или "
               "порядком («odczekaj 40 minut», «zjedz białko przed węglowodanami»), либо "
               "число. Действие должно быть выполнимо СЕГОДНЯ и БЕСПЛАТНО — зрителю не "
               "нужно ничего покупать."),
}


def _script_user(channel: str, topic: str, fmt: str, rubric: str = "label",
                 extra: str = "", angle: str = "", research_memo: str = "") -> str:
    mem, _ = style_memory(channel)
    meta = S.RUBRIC_META.get(rubric, {})
    blocks = [f"STUDIO_CONTEXT:\n{_channel_ctx(channel)}"]
    lr = _learnings_ctx(channel)
    if lr:
        blocks.append(lr)
    if mem:
        blocks.append(mem)
    blocks.append(
        f"RUBRIC: {rubric}\n"
        f"RUBRIC_PROMISE: {meta.get('promise', '')}\n"
        f"RUBRIC_BRIEF: {meta.get('brief', '')}\n"
        f"PAYLOAD_RULE: {_PAYLOAD_RULE.get(meta.get('payload_kind', 'substance'))}\n"
        f"COMPLIANCE_MODE: {meta.get('compliance', 'efsa')} "
        f"(запрещённые слова: {', '.join(S.COMPLIANCE_STOPWORDS[meta.get('compliance', 'efsa')])})")
    blocks.append(f"FORMAT: {fmt}\nFORMAT_BRIEF: {S.FORMAT_BRIEFS[fmt]}")
    blocks.append(f"TOPIC: {topic}")
    if angle:
        blocks.append(f"ANGLE (под каким углом раскрываем — это решение уже принято, "
                      f"не подменяй его): {angle}")
    if research_memo:
        blocks.append(
            "GROUNDED_RESEARCH_MEMO (Gemini Search; используй ТОЛЬКО эти источники и "
            "формулировки для фактов/чисел. Для overlay kind=source заполни все поля "
            "source_* строго из этого memo; если подходящей записи нет — не создавай source):\n"
            + research_memo
        )
    if extra:
        blocks.append(extra)
    return "\n\n".join(blocks)


def research_memo(topic: str, angle: str, run_dir: Path) -> str:
    """Короткий grounded-пакет для v7: не даёт source-карточке быть выдуманной сноской.

    Это не заменяет большой v8 ResearchPack, но делает один и тот же минимум обязательным
    для польского production-контура: источник, год, URL и ограничение вывода приходят из
    Gemini Search ДО сценария и сохраняются рядом с прогоном.
    """
    path = run_dir / "research_raw.md"
    if path.exists() and path.stat().st_size > 240:
        return path.read_text(encoding="utf-8")
    user = (
        f"TOPIC: {topic}\n"
        + (f"ANGLE: {angle}\n" if angle else "")
        + """Research this Polish YouTube Short using Google Search. Return a compact evidence memo
in Polish. Prefer official databases, systematic reviews, peer-reviewed papers and public-health
organizations. For every usable claim provide exactly: FINDING, TITLE, PUBLISHER, YEAR, URL,
and LIMITATION. Do not invent citations, do not use a source if you cannot give a working URL.
The memo is an internal source registry, not viewer copy."""
    )
    memo = _limited_call(lambda: run_agent(
        TEXT_MODEL,
        system=("You are a careful evidence researcher. Cite only sources you actually found; "
                "separate a measured value from interpretation."),
        user=user,
        temperature=0.1,
        search=True,
    ))
    path.write_text(memo.rstrip() + "\n", encoding="utf-8")
    return memo


def source_cards_from_script(sc: S.Script) -> dict[int, dict[str, str]]:
    """Передаёт в assembly только полностью описанные, traceable source-карточки."""
    cards: dict[int, dict[str, str]] = {}
    for overlay in sc.overlays:
        if overlay.kind != "source":
            continue
        if not all((overlay.source_finding, overlay.source_title, overlay.source_publisher,
                    overlay.source_year, overlay.source_reference)):
            continue
        cards[overlay.beat_idx] = {
            "finding": overlay.source_finding,
            "title": overlay.source_title,
            "publisher": overlay.source_publisher,
            "year": overlay.source_year,
            "type_label": "Badanie / źródło",
            "reference": overlay.source_reference,
            "reference_label": "Źródło",
        }
    return cards


def normalize_script(sc: S.Script) -> list[str]:
    """Чинит машинно-исправимые огрехи ДО валидации и возвращает список правок.

    Правило: нормализуем только то, где правильный ответ однозначен и не требует смысла.
    Всё остальное — гейт и переписывание моделью."""
    fixes: list[str] = []
    hook_idx = {i for i, b in enumerate(sc.beats) if b.act == "hook"}
    drop = [o for o in sc.overlays if o.beat_idx in hook_idx]
    if drop:
        sc.overlays = [o for o in sc.overlays if o.beat_idx not in hook_idx]
        fixes.append(f"снял {len(drop)} оверлей(ев) из акта hook — там работает poster_text")
    seen, uniq, dup = set(), [], 0
    for o in sc.overlays:
        if o.beat_idx in seen:
            dup += 1
            continue
        seen.add(o.beat_idx)
        uniq.append(o)
    if dup:
        sc.overlays = uniq
        fixes.append(f"снял {dup} лишний(х) оверлей(ев): на бите может быть только один")
    return fixes


# --- callout не пересказывает озвучку / list однороден и один на ролик (владелец
# 2026-08-15: в «źródła żelaza» два callout'а дословно повторяли то, что уже произносится и
# стоит в субтитрах, а list смешивал пункт-действие с пунктом-веществом) --------------------
_WORD_SPLIT = re.compile(r"[^\w]+", re.UNICODE)


def _significant_words(text: str) -> set[str]:
    """Слова длиннее 3 символов, нижний регистр, без пунктуации и звёздочек-акцентов."""
    return {w for w in _WORD_SPLIT.split(text.lower()) if len(w) > 3}


def _norm_list_text(text: str) -> str:
    """Для сравнения label с пунктами списка: убираем префикс +/-, пунктуацию, регистр."""
    t = text.strip()
    if t[:1] in "+-":
        t = t[1:].strip()
    return _WORD_SPLIT.sub(" ", t.lower()).strip()


def validate_script(sc: S.Script, recent_openers: tuple[str, ...] = ()) -> list[str]:
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
    # `percent` — только длина заливки. Без явного `value` шкала подписывается процентом, и
    # уровень ферритина 15 µg/l выходит на экран как «15%» (поймано на прогоне 2026-08-12).
    for o in sc.overlays:
        if o.kind == "bar" and not o.value.strip():
            errs.append(f"bar на бите {o.beat_idx}: нужен value с единицей измерения "
                        f"(«15 µg/l», «4%») — percent это только длина полоски")
        if o.kind in ("stat", "versus") and not o.value.strip():
            errs.append(f"{o.kind} на бите {o.beat_idx}: пустой value")
        label = _overlay_norm(o.label)
        if o.kind in {"stat", "bar"} and label in _GENERIC_OVERLAY_LABELS:
            errs.append(f"{o.kind} на бите {o.beat_idx}: общая подпись «{o.label}» ничего "
                        "не добавляет; оставь число без второго текста")
        if o.kind == "versus":
            if _overlay_norm(o.value) == _overlay_norm(o.value_b):
                errs.append(f"versus на бите {o.beat_idx}: сравнивает одинаковые значения")
            if _overlay_norm(o.label) == _overlay_norm(o.label_b):
                errs.append(f"versus на бите {o.beat_idx}: повторяет одинаковую подпись в "
                            "двух колонках; сравнение не считывается")
            if not _compact_comparison_value(o.value) or not _compact_comparison_value(o.value_b):
                errs.append(f"versus на бите {o.beat_idx}: в колонках допустимы только "
                            "короткие числа с единицей или однословные значения")
            if len(label) > 16 or len(_overlay_norm(o.label_b)) > 16:
                errs.append(f"versus на бите {o.beat_idx}: подписи слишком длинные для "
                            "двух колонок")
        if o.kind == "callout" and re.search(r"\d", o.value or ""):
            if o.label.strip():
                errs.append(f"callout на бите {o.beat_idx}: числовой callout не должен иметь "
                            "вторую текстовую подпись")
            if not _compact_numeric_value(o.value):
                errs.append(f"callout на бите {o.beat_idx}: оставь только число и единицу")
        if o.kind == "source":
            source_fields = (o.source_finding, o.source_title, o.source_publisher,
                             o.source_year, o.source_reference)
            if not all(x.strip() for x in source_fields):
                errs.append(f"source на бите {o.beat_idx}: нужны finding, title, publisher, "
                            "year и reference для карточки исследования")
            if not re.search(r"(?:https?://|[A-Za-z0-9-]+\.[A-Za-z]{2,})", o.source_reference):
                errs.append(f"source на бите {o.beat_idx}: reference должен быть URL или доменом")
            finding_words = o.source_finding.split()
            if o.source_finding and not 3 <= len(finding_words) <= 10:
                errs.append(f"source на бите {o.beat_idx}: finding должен содержать 3-10 слов")

    # callout — не пересказ озвучки и не больше одного на ролик. Числовые оверлеи
    # (stat/bar/versus/timeline/source/stamp) сюда не попадают — они показывают то, чего
    # в звуке нет, дублированием по определению не считаются.
    callouts = [o for o in sc.overlays if o.kind == "callout"]
    if len(callouts) > 1:
        errs.append(f"callout на ролике {len(callouts)}, разрешён только один")
    for o in callouts:
        if not (0 <= o.beat_idx < n):
            continue
        overlap = _significant_words(f"{o.label} {o.value}") & \
            _significant_words(sc.beats[o.beat_idx].voiceover)
        if overlap:
            errs.append(f"callout на бите {o.beat_idx} пересказывает озвучку "
                        f"(общие слова: {', '.join(sorted(overlap))}) — оверлей должен "
                        f"добавлять то, чего в звуке нет, а не повторять его")

    # list — один на ролик, только 3-4 однородных пункта, заголовок не дублирует пункт.
    # Однородность СМЫСЛА (не мешать действие с веществом) машина не проверяет — это судья
    # и сценарист; код держит только счётные правила.
    lists = [o for o in sc.overlays if o.kind == "list"]
    if len(lists) > 1:
        errs.append(f"list на ролике {len(lists)}, разрешён только один")
    for o in lists:
        if not (3 <= len(o.items) <= 4):
            errs.append(f"list на бите {o.beat_idx}: {len(o.items)} пункт(ов), нужно 3-4")
        if not o.label.strip():
            errs.append(f"list на бите {o.beat_idx}: пустой label — нужен заголовок списка")
        else:
            lbl = _norm_list_text(o.label)
            if any(_norm_list_text(it) == lbl for it in o.items):
                errs.append(f"list на бите {o.beat_idx}: label дублирует один из пунктов")

    low = sc.payload.lower()
    for v in _VAGUE_PL:
        if v in low:
            errs.append(f"payload содержит запрещённое обобщение «{v}»")
            break
    meta = S.RUBRIC_META.get(sc.rubric, {})
    kind = meta.get("payload_kind", "substance")
    if not _payload_ok(sc.payload, kind):
        errs.append("в payload нет конкретики: нужно " + (
            "число/доза/название формы вещества" if kind == "substance"
            else "действие с условием или временем (или число)"))

    # Стоп-слова зависят от режима комплаенса рубрики. Полный EFSA-набор — только там, где
    # речь о препаратах: запрет слова `ból` в ролике про кофе просто ломает живую речь.
    body = " ".join(b.voiceover for b in sc.beats).lower()
    for w in S.COMPLIANCE_STOPWORDS.get(meta.get("compliance", "efsa"), []):
        if re.search(rf"\b{w}", body):
            errs.append(f"стоп-слово комплаенса ({meta.get('compliance')}) в озвучке: «{w}»")

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

    # Самоповтор проверяем кодом, а не LLM-судьёй: на первом же прогоне 2026-08-12 судья
    # «нашёл» совпадения, которых в STYLE_MEMORY не было. Механическая проверка не врёт.
    first = (sc.hook.split() or [""])[0].strip("?,.!«»\"").lower()
    if first and first in recent_openers:
        errs.append(f"хук снова начинается со слова «{first}» — оно уже было в недавних выпусках")
    return errs


def _recent_openers(channel: str) -> tuple[str, ...]:
    runs = sorted((RUNS / channel).glob("*/script.json"), key=lambda p: p.stat().st_mtime,
                  reverse=True)[:8]
    out = []
    for p in runs:
        try:
            h = (json.loads(p.read_text(encoding="utf-8")).get("hook") or "").split()
        except Exception:
            continue
        if h:
            out.append(h[0].strip("?,.!«»\"").lower())
    return tuple(dict.fromkeys(out))


def write_script(channel: str, topic: str, fmt: str, rubric: str = "label",
                 angle: str = "", research: str = "") -> S.Script:
    user = _script_user(channel, topic, fmt, rubric, angle=angle, research_memo=research)
    openers = _recent_openers(channel)
    data = run_structured(TEXT_MODEL, system=_role("scriptwriter"), user=user,
                          schema=S.Script, temperature=0.95)
    sc, schema_errs = _parse_or_errs(S.Script, data, "сценарий")
    if sc is None:
        print(f"[script] {schema_errs[0]}")
        fix = ("ПРЕДЫДУЩАЯ ПОПЫТКА ОТКЛОНЕНА: " + schema_errs[0] +
               "\nСоблюдай ограничения длины полей из схемы.")
        data = run_structured(TEXT_MODEL, system=_role("scriptwriter"),
                              user=_script_user(channel, topic, fmt, rubric, fix, angle, research),
                              schema=S.Script, temperature=0.8)
        sc, schema_errs = _parse_or_errs(S.Script, data, "сценарий")
        if sc is None:
            raise SystemExit("[script] " + schema_errs[0])
    sc.rubric = rubric          # рубрику выбрал код, не модель — подменять её нельзя
    for note in normalize_script(sc):
        print(f"[script] нормализация: {note}")
    errs = validate_script(sc, openers)

    # Две попытки переписывания, не одна. Первая редакция гейтов (2026-08-14) давала один
    # шанс — и прогон «źródła żelaza» умер так: модель починила payload и на той же итерации
    # сломала соседнее правило. Попытка стоит ~$0.04 при потолке ролика $3, отказ прогона —
    # дороже. Больше двух не даём: если модель не сходится за два раза, дело в задании.
    for attempt in (1, 2):
        if not errs:
            break
        print(f"[script] гейты не пройдены ({len(errs)}), переписываю (попытка {attempt}/2):")
        for e in errs:
            print(f"         · {e}")
        fix = ("ПРЕДЫДУЩАЯ ПОПЫТКА ОТКЛОНЕНА машинной проверкой. Исправь ИМЕННО это,\n"
               "остальное не ломай — особенно то, что уже проходило:\n" +
               "\n".join(f"- {e}" for e in errs) +
               f"\n\nОТКЛОНЁННЫЙ ВАРИАНТ:\n{sc.model_dump_json()}")
        data = run_structured(TEXT_MODEL, system=_role("scriptwriter"),
                              user=_script_user(channel, topic, fmt, rubric, fix, angle, research),
                              schema=S.Script, temperature=0.8 if attempt == 1 else 0.6)
        sc = S.Script(**data)
        sc.rubric = rubric
        for note in normalize_script(sc):
            print(f"[script] нормализация: {note}")
        errs = validate_script(sc, openers)
    if errs:
        raise SystemExit("[script] сценарий не проходит гейты после двух переписываний:\n" +
                         "\n".join(f"  · {e}" for e in errs))
    return sc


# --- стадия 2: комплаенс --------------------------------------------------------
def check_compliance(channel: str, sc: S.Script) -> S.ComplianceVerdict:
    user = f"STUDIO_CONTEXT:\n{_channel_ctx(channel)}\n\nSCRIPT_JSON:\n{sc.model_dump_json()}"
    data = run_structured(TEXT_MODEL, system=_role("compliance"), user=user,
                          schema=S.ComplianceVerdict, temperature=0.2)
    return S.ComplianceVerdict(**data)


# --- стадия 3: план кадров ------------------------------------------------------
# Модель ТЕКСТОВЫХ стадий (сценарий, комплаенс, кадровый план, пакет публикации, судья).
# Была зашита как "pro" в восьми местах. Вынесена 2026-08-15, чтобы можно было сравнить
# качество текста на разных моделях без правки кода: `--text-model flash35`.
# Кадры, озвучка и пиксельный QA сюда не относятся — у них свои модели.
TEXT_MODEL = "pro"

MAX_FRAME_S = 3.0        # потолок времени одной картинки на экране (владелец 2026-08-13)
MIN_FRAMES = 9           # «9-15 кадров приемлемо» — там же


def validate_plan(plan: S.FramePlan, n_beats: int, beat_durs: list[float] | None = None
                  ) -> list[str]:
    errs: list[str] = []
    frames = plan.frames
    if len(frames) < MIN_FRAMES:
        errs.append(f"кадров {len(frames)}, нужно {MIN_FRAMES}-15 — картинка меняется слишком редко")
    # Гейт на «залипший» кадр. Без него диапазон битов ничем не ограничен сверху: в первой
    # партии v7 один кадр висел 8.4 с, а провалы без смены картинки доходили до 5.9 с
    # (docs/experiments/2026-08-13_v7_review.md). Правило про ≤2.5-3 с жило в research/01
    # и в промпте visual_director с v2 — и не исполнялось ни разу, пока не стало кодом.
    if beat_durs:
        for i, f in enumerate(frames):
            if not (0 <= f.beat_from <= f.beat_to < len(beat_durs)):
                continue
            d = sum(beat_durs[f.beat_from:f.beat_to + 1])
            # Кадр из ОДНОГО бита разбить нечем — кадры режутся только по границам битов,
            # а бит по контракту бывает до 3.5с. Требовать невыполнимое = зациклить гейт.
            if d > MAX_FRAME_S + 0.01 and f.beat_to > f.beat_from:
                errs.append(f"кадр {i}: висит {d:.1f}с (биты {f.beat_from}-{f.beat_to}), "
                            f"потолок {MAX_FRAME_S}с — разбей диапазон на два кадра")
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


def _parse_or_errs(model_cls, data, label: str):
    """Разбирает ответ модели по схеме. Нарушение схемы возвращается КАК ЗАМЕЧАНИЕ, а не
    падает исключением.

    Structured output гарантирует форму, но не ограничения полей: модель спокойно отдаёт
    `claim` длиннее 140 символов или `payload` длиннее 180, и pydantic роняет весь прогон.
    Поймано 2026-08-15 на `flash35` — ролик про железо умер на первом же ответе визуального
    директора, хотя у нас ровно для таких случаев есть петля переписывания. Дешёвые модели
    нарушают ограничения чаще, так что без этого сравнивать их с `pro` было бы нечестно:
    часть прогонов просто не доезжала бы до конца.
    """
    try:
        return model_cls(**data), []
    except Exception as e:
        detail = str(e).replace("\n", " ")[:400]
        return None, [f"{label}: ответ не проходит схему — {detail}"]


def plan_frames(channel: str, sc: S.Script) -> S.FramePlan:
    durs = [b.dur_s for b in sc.beats]
    total = sum(durs)
    # Нижняя граница числа кадров считается из хронометража, а не берётся из головы:
    # при потолке 3с на кадр 26-секундный ролик физически не покрывается девятью кадрами.
    lo = max(9, int(total / MAX_FRAME_S) + 1)
    user = (f"STUDIO_CONTEXT:\n{_channel_ctx(channel)}\n\n"
            f"SCRIPT_JSON:\n{sc.model_dump_json()}\n\n"
            f"Битов в сценарии: {len(sc.beats)} (индексы 0..{len(sc.beats)-1}), "
            f"хронометраж {total:.1f}с. Кадров сделай {lo}-15, они должны покрыть все биты "
            f"подряд. ЖЁСТКО: один кадр не держится на экране дольше {MAX_FRAME_S:.0f}с — "
            f"длинный бит или пара длинных битов разбивается на два кадра с разными планами.")
    data = run_structured(TEXT_MODEL, system=_role("visual_director"), user=user,
                          schema=S.FramePlan, temperature=0.75)
    plan, errs = _parse_or_errs(S.FramePlan, data, "кадровый план")
    if plan is not None:
        errs = validate_plan(plan, len(sc.beats), durs)
    if errs:
        print(f"[visual] гейты не пройдены ({len(errs)}), переписываю:")
        for e in errs:
            print(f"         · {e}")
        rejected = plan.model_dump_json() if plan is not None else json.dumps(data, ensure_ascii=False)
        fix = ("\n\nПРЕДЫДУЩИЙ ПЛАН ОТКЛОНЁН машинной проверкой. Исправь ИМЕННО это:\n" +
               "\n".join(f"- {e}" for e in errs) + f"\n\nОТКЛОНЁННЫЙ ПЛАН:\n{rejected}")
        data = run_structured(TEXT_MODEL, system=_role("visual_director"), user=user + fix,
                              schema=S.FramePlan, temperature=0.6)
        plan, errs2 = _parse_or_errs(S.FramePlan, data, "кадровый план")
        if plan is None:
            raise SystemExit("[visual] план не проходит схему и после переписывания:\n" +
                             "\n".join(f"  · {e}" for e in errs2))
        errs2 = validate_plan(plan, len(sc.beats), durs)
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
# Запрет на ЛЮБЫЕ буквы в кадре снят 2026-08-12 по замечанию владельца: модель, которой
# запрещены «labels», рисует банку с ОБОДРАННОЙ этикеткой — в нише про составы и дозировки
# это выглядит противоестественно, а этикетка здесь и есть предмет разговора. Теперь
# запрещены только элементы, которые спорят с нашей собственной графикой (плавающие титры,
# выноски, водяные знаки) и реальные торговые марки — по юридическим причинам. Короткие
# запланированные надписи на предмете и простой UI на экране разрешены, если это часть промпта.
_NEGATIVE = ("NEGATIVE: over-saturated, deep-fried colors, 3d render, plastic skin, cartoon, "
             "mutated geometry, extra limbs, watermark, channel logo, white border, "
             "photo frame, polaroid frame, paper margin, framed print, rounded photo corners, "
             "subtitle bars, caption overlays, floating text callouts, unplanned diagram annotations, "
             "dense infographic text, paragraphs of body copy, random fake lettering, "
             "real-world brand names or trademarks, "
             "worn or torn or peeling labels, scuffed scratched or chipped packaging, "
             "artificial distressing, grime, dust smears — "
             "objects are clean and intact; "
             "image must bleed to all four edges of the canvas. "
             "Printed packaging IS allowed and encouraged where the scene calls for it: a jar, "
             "bottle, blister or sachet may carry its own short readable label with generic wording "
             "(product name, ingredient, dosage, form). A phone, monitor or tablet may show a "
             "simple planned unbranded UI, icons, timer or chart. Keep embedded content short, "
             "crisp and incidental — it belongs to the object, never floats over the frame as an overlay.")


def _vision_check(path: Path, poster: bool):
    """Машинная проверка ПИКСЕЛЕЙ готового кадра (доли цента за вызов). Профиль `photo_v7`
    отличается от продакшенного: печатный текст на этикетке разрешён, зато отдельно
    проверяются осмысленность букв, целостность предмета и то, что объект не выселен за край
    — то есть ровно те три дефекта, которые всплыли на первой партии v7."""
    sys.path.insert(0, str(_ROOT / ".claude" / "skills" / "video-factory" / "scripts"))
    from vision_qa import check_image
    return _limited_call(lambda: check_image(path, poster=poster, profile="photo_v7"), 120)


def generate_frames(plan: S.FramePlan, out_dir: Path, qa_frames: bool = True) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    report: list[dict] = []
    # A run may contain an opt-in likeness reference supplied by the owner.  It is never
    # used implicitly: only prompts marked by the visual plan receive it, so object and
    # evidence frames cannot accidentally turn into portraits.
    character_refs = [
        path for suffix in (".png", ".jpg", ".jpeg", ".webp")
        for path in [out_dir.parent / f"character_reference{suffix}"]
        if path.is_file()
    ]
    for i, fr in enumerate(plan.frames):
        p = out_dir / f"frame_{i:02d}.png"
        if p.exists() and p.stat().st_size > 1000:
            # A previous run can have stopped after Vision QA rejected a frame but
            # before its replacement was written.  Re-check cached assets on resume
            # so a known bad frame cannot silently enter the final MP4.
            if qa_frames:
                try:
                    existing = _vision_check(p, poster=(i == 0))
                except Exception as e:
                    print(f"[frame-qa] resume-проверка пропущена для {p.name}: {e}")
                    existing = None
                if existing is not None and not existing.passed:
                    issues = "; ".join(existing.issues)[:200]
                    print(f"[frame-qa] {p.name} брак в resume: {issues}")
                    report.append({"frame": i, "attempt": "resume", "issues": existing.issues})
                else:
                    print(f"[frames] {p.name} уже есть — пропускаю (resume)")
                    paths.append(p)
                    continue
            else:
                print(f"[frames] {p.name} уже есть — пропускаю (resume)")
                paths.append(p)
                continue
        # лимит модели — 3 reference-изображения; раньше слали 14 и получали дрейф стиля
        uses_character_reference = "[[CHARACTER_REFERENCE]]" in fr.prompt
        prior_refs = [str(x) for x in paths[-3:]] if fr.ref_ids else []
        refs = ([str(character_refs[0])] if uses_character_reference and character_refs else []) \
            + prior_refs
        refs = refs[:3]  # Gemini image accepts at most three references in this pipeline.
        # Cartoon is normally negative for the documentary wellness preset, but
        # this channel also has an approved hand-drawn office/IT visual language.
        # Let an explicit 2D illustration brief win without weakening the other
        # geometry, watermark, text, and border safeguards.
        negative = _NEGATIVE
        if "2d hand-drawn" in fr.prompt.lower() or "2d illustrated" in fr.prompt.lower():
            negative = negative.replace("cartoon, ", "")
        frame_prompt = fr.prompt.replace("[[CHARACTER_REFERENCE]]", "").strip()
        if uses_character_reference and character_refs:
            frame_prompt += (
                "\nUse the attached character reference only for the visible person's facial "
                "likeness and natural features; keep the requested setting, pose, wardrobe, "
                "and documentary lighting."
            )
        prompt = (f"{frame_prompt}\nGRADE: {plan.grade}. LIGHT: {plan.light}. LENS: {plan.lens}.\n"
                  f"{negative}")
        generate_image("img", prompt, aspect_ratio="9:16", out=str(p), refs=refs)
        # Точечная перегенерация: бракуется и переснимается ОДИН кадр, а не весь ролик.
        for attempt in range(2 if qa_frames else 0):
            try:
                res = _vision_check(p, poster=(i == 0))
            except Exception as e:
                print(f"[frame-qa] пропущен для {p.name}: {e}")
                break
            if res.passed:
                break
            issues = "; ".join(res.issues)[:200]
            print(f"[frame-qa] {p.name} брак ({attempt + 1}/2): {issues}")
            report.append({"frame": i, "attempt": attempt + 1, "issues": res.issues})
            generate_image("img", prompt, aspect_ratio="9:16", out=str(p), refs=refs)
        paths.append(p)
    if report:
        (out_dir.parent / "frame_qa.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return paths


# Кадр под финальную карточку. До 2026-08-15 под payoff-карточкой лежал первый кадр ролика
# (frame0.png, решение 2026-08-12 — закрывало петлю «конец = начало»), но этот кадр не
# задумывался под крупный текст поверх. Отдельный кадр строится на основе последнего кадра
# плана (композиционно ближе всего к финалу ролика) с просьбой спокойной композиции: свободная
# середина под текст, ничего мелкого и пёстрого. Стиль/негатив — те же, что у остальных
# кадров, чтобы кадр не выпадал из ролика.
def generate_payoff_frame(plan: S.FramePlan, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "frame_payoff.png"
    if p.exists() and p.stat().st_size > 1000:
        print(f"[frames] {p.name} уже есть — пропускаю (resume)")
        return p
    last = plan.frames[-1]
    prompt = (f"{last.prompt}\n"
              f"PAYOFF CARD FRAME: calm, uncluttered composition built to carry a large text "
              f"card on top — keep the center of the frame open and simple, nothing small or "
              f"busy there, no clutter crowding the middle third.\n"
              f"GRADE: {plan.grade}. LIGHT: {plan.light}. LENS: {plan.lens}.\n"
              f"{_NEGATIVE}")
    generate_image("img", prompt, aspect_ratio="9:16", out=str(p))
    return p


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
    voice, base_style, base_speed = CHANNEL_VOICE.get(channel, ("Aoede", "", 1.15))
    pieces: list[Path] = []
    durs: list[float] = []
    beat_words: list[list[dict]] = []
    cumulative = 0.0
    acts = [b.act for b in sc.beats]

    for i, beat in enumerate(sc.beats):
        w = out_dir / f"beat{i}.wav"
        meta = out_dir / f"beat{i}.delivery.json"
        style, speed = base_style, base_speed
        if i == len(sc.beats) - 2:
            style = (base_style + "; leave a clear breath before the final conclusion").strip("; ")
        elif i == len(sc.beats) - 1:
            style = (base_style + "; decisive final takeaway, slightly slower, falling cadence").strip("; ")
            speed = min(base_speed, 1.04)
        signature = json.dumps({"text": beat.voiceover, "voice": voice, "style": style,
                                "speed": speed}, ensure_ascii=False, sort_keys=True)
        cached = ""
        if meta.exists():
            try:
                cached = json.loads(meta.read_text(encoding="utf-8")).get("signature", "")
            except Exception:
                pass
        if not (w.exists() and w.stat().st_size > 1000 and cached == signature):
            generate_speech(beat.voiceover, voice=voice, style=style, out=str(w), speed=speed)
            _trim_silence(w)
            meta.write_text(json.dumps({"signature": signature, "style": style, "speed": speed},
                                       ensure_ascii=False), encoding="utf-8")
        d = _wav_dur(w)
        beat_words.append(_estimate_word_timestamps(beat.voiceover, d, cumulative))
        pieces.append(w)

        # пауза ПОСЛЕ бита: на границе актов длиннее, перед поворотом — короткий вдох
        pause = 0.0
        if i == len(sc.beats) - 2:
            # Пользователь должен услышать, что начинается итог, а не ещё один кусок фразы.
            pause = 0.48
        elif i + 1 < len(sc.beats) and acts[i + 1] != acts[i]:
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
    data = run_structured(TEXT_MODEL, system=_role("qa"), user=user,
                          schema=S.QAReport, temperature=0.25)
    return S.QAReport(**data)


# Дисклеймер зависит от рубрики: приписка «Suplement diety» уместна там, где речь о добавках,
# и выглядит нелепо под роликом про кофе или про варку брокколи (поймано на первом прогоне
# рубрики day_body 2026-08-14). Образовательная часть обязательна везде.
DISCLAIMER_BASE = "Materiał ma charakter edukacyjny i nie zastępuje porady lekarza."
DISCLAIMER_SUPPLEMENT = DISCLAIMER_BASE + " Suplement diety."


def _disclaimer(rubric: str) -> str:
    mode = S.RUBRIC_META.get(rubric, {}).get("compliance", "efsa")
    return DISCLAIMER_SUPPLEMENT if mode == "efsa" else DISCLAIMER_BASE
# Потолок «короткого» описания без дисклеймера. Прежние описания v7 шли на 700-1100 символов;
# 450 — это две-три строки контекста плюс payload, то есть ровно то, что просит publisher.md.
SHORT_DESC_LIMIT = 450


def publish_package(channel: str, sc: S.Script) -> S.PublishPackage:
    """Стадия 8: заголовок/описание/хэштеги/закреплённый комментарий.

    Без этого пакета ролик физически нельзя залить: `publishers/youtube.py` читает
    `publish_package.json` и без него падает. В первой версии v7 стадии не было вовсе —
    ролики собирались, но оставались непубликуемыми."""
    user = (f"STUDIO_CONTEXT:\n{_channel_ctx(channel)}\n\n"
            f"SCRIPT_JSON:\n{sc.model_dump_json()}\n\n"
            f"DISCLAIMER (последней строкой описания, дословно): {_disclaimer(sc.rubric)}")
    data = run_structured(TEXT_MODEL, system=_role("publisher"), user=user,
                          schema=S.PublishPackage, temperature=0.7)
    pkg = S.PublishPackage(**data)
    # Дисклеймер — юридическое требование канала, не полагаемся на модель.
    disclaimer = _disclaimer(sc.rubric)
    if DISCLAIMER_BASE not in pkg.description:
        pkg.description = pkg.description.rstrip() + "\n\n" + disclaimer
    elif disclaimer == DISCLAIMER_BASE and DISCLAIMER_SUPPLEMENT in pkg.description:
        pkg.description = pkg.description.replace(DISCLAIMER_SUPPLEMENT, DISCLAIMER_BASE)
    # Метка описания должна следовать за ФАКТОМ, а не за намерением модели: иначе когорта
    # `short_context` наберётся из роликов с прежними простынями, и сравнить будет нечего.
    body_len = len(pkg.description.replace(DISCLAIMER_SUPPLEMENT, "")
                   .replace(DISCLAIMER_BASE, "").strip())
    if pkg.description_template == "short_context" and body_len > SHORT_DESC_LIMIT:
        print(f"[publish] описание {body_len} символов при лимите {SHORT_DESC_LIMIT} — "
              f"помечаю как long_seo, метка не должна врать")
        pkg.description_template = "long_seo"
    if not any(h.lower() == "#shorts" for h in pkg.hashtags):
        pkg.hashtags = (pkg.hashtags + ["#Shorts"])[:6]
    return pkg


def _channel_bgm(channel: str) -> Path | None:
    bgm_dir = CHANNELS / channel / "assets" / "bgm"
    if not bgm_dir.is_dir():
        return None
    tracks = [p for p in sorted(bgm_dir.iterdir())
              if p.suffix.lower() in (".wav", ".mp3", ".m4a", ".flac")]
    return random.choice(tracks) if tracks else None


# --- прогон ---------------------------------------------------------------------
def produce(channel: str, topic: str, fmt: str = "", slug: str = "", go: bool = False,
            sfx_profile: str = A.DEFAULT_SFX_PROFILE, rubric: str = "",
            angle: str = "") -> Path:
    # Тема уже выбрана редакцией/ресёрчем; здесь присваиваем контракт рубрики → формат.
    rubric = pick_rubric(channel, rubric)
    fmt = pick_format(channel, fmt, rubric)
    slug = slug or re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:40]
    run_dir = RUNS / channel / f"{datetime.date.today()}_{slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    os.environ["RUN_COST_DIR"] = str(run_dir)
    print(f"[v7] {slug} · рубрика={rubric} · формат={fmt}")

    research = research_memo(topic, angle, run_dir)
    sc = write_script(channel, topic, fmt, rubric, angle, research)
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
        pkg = publish_package(channel, sc)
        (run_dir / "publish_package.json").write_text(pkg.model_dump_json(indent=2),
                                                      encoding="utf-8")
        print(f"[publish] «{pkg.title}»")
    except Exception as e:
        print(f"[publish] пакет публикации не собрался: {e}")

    try:
        report = qa(channel, sc, plan)
        failed = [c.name for c in report.checks if not c.passed]
        # Судья видит то, чего не видит код: скатился ли сценарий обратно в старый шаблон,
        # настоящий ли поворот. Его вердикт возвращается сценаристу ОДИН раз и обязательно
        # до генерации кадров — переписать текст стоит центы, перегенерировать кадры $0.3.
        # Какие замечания судьи стоят одного переписывания сценария. Дополнено 2026-08-15:
        # `hook_stops_scroll` тут не было — то есть самая важная проверка (первая фраза
        # решает свайп) фиксировалась в отчёте и не чинилась. Поймано на ролике
        # «źródła żelaza»: судья увидел запрещённый общий вопрос о самочувствии
        # («Znowu brakuje ci sił?»), ролик собрался с ним и ушёл в готовые.
        soft = {"not_a_clone", "turn_is_real", "overlays_add", "visual_not_literal",
                "no_school_essay", "voice_persona", "payoff_card_is_conclusion",
                "hook_stops_scroll", "payload_is_real", "fits_rubric",
                "overlays_disciplined"}
        if set(failed) & soft:
            print(f"[qa] замечания судьи ({', '.join(failed)}) — переписываю сценарий один раз")
            notes = "\n".join(f"- {c.name}: {c.detail}" for c in report.checks if not c.passed)
            fix = ("СУДЬЯ ОТКЛОНИЛ ПРЕДЫДУЩИЙ ВАРИАНТ. Исправь ИМЕННО это:\n" + notes +
                   "\n\nОсобенно: если замечание про клон — смени УГОЛ ПОДАЧИ, а не слова.\n\n"
                   f"ОТКЛОНЁННЫЙ ВАРИАНТ:\n{sc.model_dump_json()}")
            # Сбой ИМЕННО этой попытки не должен уносить всю стадию QA: раньше исключение
            # ловил общий except ниже, и тогда терялся не только переписанный сценарий, но и
            # `qa.json` — прогон оставался вообще без отчёта судьи. Поймано 2026-08-13:
            # модель вернула payload длиннее 180 символов, pydantic упал, замечания судьи
            # (turn_is_real, overlays_add, not_a_clone) молча исчезли.
            try:
                data = run_structured(TEXT_MODEL, system=_role("scriptwriter"),
                                      user=_script_user(channel, topic, fmt, rubric,
                                                        fix, angle, research),
                                      schema=S.Script, temperature=0.9)
                cand = S.Script(**data)
                cand.rubric = rubric
            except Exception as e:
                print(f"[qa] переписать не удалось ({e}) — оставляю прежний вариант")
                cand = None
            if cand is not None and not validate_script(cand, _recent_openers(channel)):
                sc = cand
                (run_dir / "script.json").write_text(sc.model_dump_json(indent=2), encoding="utf-8")
                plan = plan_frames(channel, sc)
                (run_dir / "frame_plan.json").write_text(plan.model_dump_json(indent=2),
                                                         encoding="utf-8")
                report = qa(channel, sc, plan)
                failed = [c.name for c in report.checks if not c.passed]
            elif cand is not None:
                print("[qa] переписанный вариант не прошёл машинные гейты — оставляю прежний")
        (run_dir / "qa.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        print(f"[qa] passed={report.passed}" + (f" · осталось: {', '.join(failed)}" if failed else ""))
    except Exception as e:
        print(f"[qa] пропущен: {e}")

    if not go:
        print(f"[dry] сценарий/комплаенс/кадровый план готовы → {run_dir}")
        return run_dir

    frames = generate_frames(plan, run_dir / "frames")
    payoff_frame = generate_payoff_frame(plan, run_dir / "frames")
    voice_wav, durs, beat_words = synth_audio(channel, sc, run_dir / "audio")
    spans = [(f.beat_from, f.beat_to) for f in plan.frames]
    motions = [f.motion for f in plan.frames]
    out_mp4 = run_dir / "out.mp4"
    A.build_and_render(
        frames, spans, motions, beat_words,
        [b.on_screen_text for b in sc.beats], durs, sc.overlays,
        [b.emphasis for b in sc.beats], voice_wav, out_mp4, run_dir / "hf",
        headline=sc.poster_text, payoff_text=sc.payoff_card,
        turn_beat_idx=sc.turn_beat_idx, bgm_wav=_channel_bgm(channel),
        sfx_profile=sfx_profile, payoff_frame=payoff_frame,
        headline_until_first_cut=True, lang="pl", layout_gate=True,
        source_cards=source_cards_from_script(sc))

    (run_dir / "run_meta.json").write_text(json.dumps({
        "pipeline_version": S.PIPELINE_VERSION, "format": fmt, "rubric": rubric,
        "angle": angle, "sfx_profile": sfx_profile,
        "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] {out_mp4}")
    return run_dir


def build_from_artifacts(run_dir: Path, channel: str,
                         sfx_profile: str = A.DEFAULT_SFX_PROFILE) -> Path:
    """Достраивает прогон, у которого сценарий и план кадров УЖЕ написаны кем-то другим:
    кадры → финальный кадр → озвучка → сборка. Ни одной текстовой стадии.

    Заведено 2026-08-15 под сравнение авторства: тот же пайплайн, тот же визуал и звук, но
    текст написан не Gemini, а другим автором. Без этого режима сравнить было нельзя —
    `--go` всегда пишет сценарий заново, а `--rebuild` требует уже готовых кадров.
    Валидация обязательна: внешний сценарий проходит те же гейты, что и сгенерированный,
    иначе сравнение выродится в «у одного автора были правила, у другого нет»."""
    sc = S.Script(**json.loads((run_dir / "script.json").read_text(encoding="utf-8")))
    plan = S.FramePlan(**json.loads((run_dir / "frame_plan.json").read_text(encoding="utf-8")))
    for note in normalize_script(sc):
        print(f"[build] нормализация: {note}")
    errs = validate_script(sc) + validate_plan(plan, len(sc.beats), [b.dur_s for b in sc.beats])
    if errs:
        raise SystemExit("[build] внешние артефакты не проходят гейты:\n" +
                         "\n".join(f"  · {e}" for e in errs))
    (run_dir / "script.json").write_text(sc.model_dump_json(indent=2), encoding="utf-8")
    os.environ["RUN_COST_DIR"] = str(run_dir)
    generate_frames(plan, run_dir / "frames")
    generate_payoff_frame(plan, run_dir / "frames")
    return rebuild(run_dir, channel, sfx_profile=sfx_profile)


def rebuild(run_dir: Path, channel: str, sfx_profile: str = A.DEFAULT_SFX_PROFILE) -> Path:
    """Пересобирает ролик из уже сохранённых артефактов прогона (script/frame_plan/frames/audio),
    без единого обращения к API. Нужно, когда меняется только сборка — правка CSS, тайминга,
    звука. Раньше такой правки не существовало как операции: любое изменение рендера означало
    полный повторный прогон с повторной оплатой кадров."""
    sc = S.Script(**json.loads((run_dir / "script.json").read_text(encoding="utf-8")))
    plan = S.FramePlan(**json.loads((run_dir / "frame_plan.json").read_text(encoding="utf-8")))
    # glob по цифровому суффиксу намеренно (не "frame_*.png"): frame_payoff.png лежит в той же
    # папке и под общую маску тоже попал бы, задвоив/испортив список основных кадров.
    frames = sorted((run_dir / "frames").glob("frame_[0-9]*.png"))
    if len(frames) != len(plan.frames):
        raise SystemExit(f"[rebuild] кадров на диске {len(frames)}, в плане {len(plan.frames)}")
    # payoff-кадр — только с диска (rebuild без вызовов API): если его ещё нет, сборка ведёт
    # себя как раньше (payoff_frame=None), а не генерирует кадр за деньги.
    payoff_frame = run_dir / "frames" / "frame_payoff.png"
    payoff_frame = payoff_frame if payoff_frame.exists() else None
    voice_wav, durs, beat_words = synth_audio(channel, sc, run_dir / "audio")  # всё из кэша
    out_mp4 = run_dir / "out.mp4"
    A.build_and_render(
        frames, [(f.beat_from, f.beat_to) for f in plan.frames],
        [f.motion for f in plan.frames], beat_words,
        [b.on_screen_text for b in sc.beats], durs, sc.overlays,
        [b.emphasis for b in sc.beats], voice_wav, out_mp4, run_dir / "hf",
        headline=sc.poster_text, payoff_text=sc.payoff_card,
        turn_beat_idx=sc.turn_beat_idx, bgm_wav=_channel_bgm(channel),
        sfx_profile=sfx_profile, payoff_frame=payoff_frame,
        headline_until_first_cut=True, lang="pl", layout_gate=True,
        source_cards=source_cards_from_script(sc))
    print(f"[rebuilt] {out_mp4}")
    return out_mp4


def _label_png(dest: Path, text: str) -> Path:
    """Плашка-подпись для сравнительной катушки. Нужна только для внутреннего просмотра —
    в продакшен-ролик не попадает."""
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 40)
    except OSError:
        font = ImageFont.load_default()
    pad = 22
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    box = probe.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0] + pad * 2, box[3] - box[1] + pad * 2
    img = Image.new("RGBA", (w, h), (8, 12, 20, 205))
    ImageDraw.Draw(img).text((pad - box[0], pad - box[1]), text,
                             font=font, fill=(255, 255, 255, 255))
    img.save(dest)
    return dest


def remix(run_dir: Path, channel: str, profiles: list[str]) -> list[Path]:
    """Переозвучивает готовый ролик каждым из профилей и склеивает сравнительную «катушку»
    с подписью профиля в кадре. Видео не перерисовывается — берётся `hf/video.mp4`, меняется
    только звук, поэтому вариант стоит секунды и ноль обращений к API.

    Заведено по замечанию владельца 2026-08-12: плотность и характер SFX нельзя угадать
    из ресёрча, её надо выбрать ушами на реальном ролике."""
    hf = run_dir / "hf"
    events_path = hf / "sfx_events.json"
    if not events_path.exists():
        raise SystemExit(f"[remix] нет {events_path} — пересобери прогон (--rebuild)")
    meta = json.loads(events_path.read_text(encoding="utf-8"))
    events = [(float(t), k) for t, k in meta["events"]]
    voice = run_dir / "audio" / "voice.wav"
    bgm = _channel_bgm(channel)
    out_dir = run_dir / "sfx_variants"
    out_dir.mkdir(parents=True, exist_ok=True)

    made: list[Path] = []
    for prof in profiles:
        dst = out_dir / f"{prof}.mp4"
        A.mix(hf / "video.mp4", voice, dst, meta["total"], events, bgm, hf,
              meta["payoff_start"], profile=prof)
        n = len(A._sfx_plan(prof, events))
        print(f"[remix] {prof:9s} · {n:>2} звуковых событий → {dst.name}")
        made.append(dst)

    # сравнительная катушка: те же кадры, разный звук, подпись профиля в кадре
    reel = out_dir / "porownanie.mp4"
    labeled = []
    for prof, src in zip(profiles, made):
        lab = out_dir / f"_lab_{prof}.mp4"
        n = len(A._sfx_plan(prof, events))
        badge = _label_png(out_dir / f"_badge_{prof}.png",
                           f"{prof.upper()}  ·  {n} zvukov")
        # Подпись накладывается картинкой, а не фильтром drawtext: в локальной сборке ffmpeg
        # 8.1.1 фильтра drawtext нет вовсе (собран без libfreetype) — проверено 2026-08-12.
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-i", str(badge),
             "-filter_complex", "[0:v][1:v]overlay=x=(W-w)/2:y=96[v]",
             "-map", "[v]", "-map", "0:a",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", str(lab)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        labeled.append(lab)
        badge.unlink(missing_ok=True)
    lst = out_dir / "concat.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in labeled), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(reel)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for p in labeled:
        p.unlink(missing_ok=True)
    print(f"[remix] катушка сравнения → {reel}")
    return made + [reel]


def main():
    p = argparse.ArgumentParser(description="engine_v7.py — оркестратор ролика v7")
    p.add_argument("--channel", default="vitallogic_bad_pl")
    p.add_argument("--topic", default="")
    p.add_argument("--format", default="", help=f"один из: {', '.join(S.FORMAT_BRIEFS)}")
    p.add_argument("--rubric", default="",
                   help=f"рубрика (по умолчанию — ротация): {', '.join(S.ACTIVE_RUBRICS)}")
    p.add_argument("--angle", default="", help="угол подачи темы (из медиаплана/майнера)")
    p.add_argument("--slug", default="")
    p.add_argument("--go", action="store_true", help="запустить генерацию кадров/озвучки/сборку")
    p.add_argument("--rebuild", default="", metavar="RUN_DIR",
                   help="пересобрать ролик из артефактов прогона, без вызовов API")
    p.add_argument("--sfx", default=A.DEFAULT_SFX_PROFILE,
                   choices=list(A.SFX_PROFILES), help="звуковой профиль сборки")
    p.add_argument("--text-model", default=TEXT_MODEL, dest="text_model",
                   help="модель текстовых стадий: pro | flash35 | flash | lite")
    p.add_argument("--build", default="", metavar="RUN_DIR",
                   help="достроить прогон с УЖЕ написанными script.json/frame_plan.json: "
                        "кадры → озвучка → сборка (текстовые стадии пропускаются)")
    p.add_argument("--remix", default="", metavar="RUN_DIR",
                   help="переозвучить готовый ролик всеми профилями + катушка сравнения")
    a = p.parse_args()
    globals()["TEXT_MODEL"] = a.text_model
    if a.build:
        build_from_artifacts(Path(a.build), a.channel, sfx_profile=a.sfx)
        return
    if a.remix:
        remix(Path(a.remix), a.channel, list(A.SFX_PROFILES))
        return
    if a.rebuild:
        rebuild(Path(a.rebuild), a.channel, sfx_profile=a.sfx)
        return
    produce(a.channel, a.topic, a.format, a.slug, go=a.go, sfx_profile=a.sfx,
            rubric=a.rubric, angle=a.angle)


if __name__ == "__main__":
    main()
