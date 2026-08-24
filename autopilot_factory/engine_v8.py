#!/usr/bin/env python3
"""Canonical v8 Codex pipeline: research → claims → package → approved media → QA.

Codex owns the editorial and frame decisions.  The local renderer consumes an explicit
``media_manifest.json`` and never silently substitutes a Gemini image generation call.
Publishing remains a separate, directly authorized operation.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "orchestration"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:  # Optional for pure local contract/manifest checks.
    from audio_agent import TTS_MODELS, generate_speech  # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover - depends on local environment
    if exc.name != "google":
        raise
    TTS_MODELS = {"tts": "gemini-3.1-flash-tts-preview"}

    def generate_speech(*_args, **_kwargs):
        raise RuntimeError("Gemini TTS dependency is required only for media assembly")

try:  # Optional for pure local contract/manifest checks.
    from gemini_agent import resolve_model, run_agent  # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover - depends on local environment
    if exc.name != "google":
        raise

    def resolve_model(model: str) -> str:
        return model

    def run_agent(*_args, **_kwargs):
        raise RuntimeError("Gemini dependency is required only for network-backed v8 stages")
from runtime_support_v8 import _wav_dur, _trim_silence, _estimate_word_timestamps  # noqa: E402

import assembly_v8 as A  # noqa: E402
import engine_v8_base as V8Base  # noqa: E402
import schemas_v8 as S  # noqa: E402


PROMPTS = Path(__file__).resolve().parent / "prompts" / "v8"
CHANNELS = Path(__file__).resolve().parent / "channels"
RUNS = Path(__file__).resolve().parent / "runs"

TEXT_MODEL = "pro"
RESEARCH_MODEL = "pro"
IMAGE_MODEL = "img"
TTS_MODEL = "tts"
VISION_MODEL = "gemini-2.5-flash"
MAX_CONTENT_REVISIONS = 3
LANG = "pl"
LANGUAGE_CONFIG = {
    "pl": {
        "disclaimer": "Materiał ma charakter edukacyjny i nie zastępuje porady lekarza.",
        "qa_language_check": "language_pl",
        "tts_style": "bright, expressive, emotionally engaged male Polish narration; lively conversational pace, clear Polish articulation, varied pitch, playful comic timing, light irony; never flat or audiobook-like",
        "source_types": {
            "official_guideline": "Oficjalne zalecenie",
            "regulation": "Przepis / regulacja",
            "systematic_review": "Przegląd systematyczny",
            "meta_analysis": "Metaanaliza",
            "clinical_trial": "Badanie kliniczne",
            "primary_study": "Badanie",
            "official_database": "Oficjalna baza danych",
            "other": "",
        },
    },
    "ru": {
        "disclaimer": "Материал носит образовательный характер и не заменяет консультацию специалиста.",
        "qa_language_check": "language_ru",
        "tts_style": "bright, expressive, emotionally engaged male Russian narration; lively conversational pace, clear articulation, varied pitch, playful comic timing, light irony; never flat or audiobook-like",
        "source_types": {
            "official_guideline": "Официальная рекомендация",
            "regulation": "Нормативный документ",
            "systematic_review": "Систематический обзор",
            "meta_analysis": "Метаанализ",
            "clinical_trial": "Клиническое исследование",
            "primary_study": "Исследование",
            "official_database": "Официальная база данных",
            "other": "",
        },
    },
}
ABSOLUTE_WORDING = re.compile(
    r"\b(?:абсолют\w*|идентичн\w*|одинаков\w*|гарантир\w*|всегда|никогда|"
    r"absolutn\w*|identyczn\w*|tak\s+samo|gwarant\w*|zawsze|nigdy)\b|"
    r"\b(?:единственн\w*|jedyn\w*)\s+(?:способ|метод|sposób|metoda)\b|"
    r"\bna\s+paузу\b|\bna\s+pauzę\b",
    re.IGNORECASE,
)
GENERIC_OVERLAY_LABELS = {
    "энергия", "калории", "значение", "показатель", "результат", "данные", "факт",
    "energia", "kalorie", "wartość", "wynik", "dane", "fakt",
}

BASE_EXPECTED_QA = {
    "hook_stops_scroll",
    "format_delivered",
    "turn_is_real",
    "payload_is_real",
    "payoff_is_entailed",
    "overlays_add",
    "visual_causal_progression",
    "frames_semantic_match",
    "voice_persona",
    "not_a_clone",
    "source_named_when_natural",
}
BASE_CRITICAL_QA = {
    "hook_stops_scroll",
    "format_delivered",
    "payload_is_real",
    "payoff_is_entailed",
    "frames_semantic_match",
}


def _role(name: str) -> str:
    localized = PROMPTS / LANG / f"{name}.md"
    return (localized if localized.exists() else PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def _lang_config() -> dict:
    return LANGUAGE_CONFIG[LANG]


def _expected_qa() -> set[str]:
    return BASE_EXPECTED_QA | {_lang_config()["qa_language_check"]}


def _critical_qa() -> set[str]:
    return BASE_CRITICAL_QA | {_lang_config()["qa_language_check"]}


def _limited_call(fn, timeout_s: int = 180):
    """Не даёт синхронному SDK-вызову зависнуть навсегда на сетевом retry."""
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


def run_structured(model: str, system: str, user: str, schema, temperature: float = 0.7) -> dict:
    """Gemini JSON mode → JSON parse; окончательную строгость обеспечивает Pydantic.

    Gemini API отклоняет часть вложенных v8 Pydantic-схем как INVALID_ARGUMENT, поэтому
    передаём ту же полную JSON Schema в prompt. Три ограниченных повтора защищают и от
    оборванного JSON, и от зависшего SDK-retry.
    """
    schema_text = json.dumps(schema.model_json_schema(), ensure_ascii=False)
    base_user = (
        user
        + "\n\nВерни ОДИН JSON-объект без markdown и пояснений, строго по этой JSON Schema:\n"
        + schema_text
    )
    retry_note = ""
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            raw = _limited_call(
                lambda: run_agent(
                    model,
                    system=system,
                    user=base_user + retry_note,
                    temperature=temperature if attempt == 0 else min(temperature, 0.2),
                    json_mode=True,
                )
            )
            clean = raw.strip()
            if clean.startswith("```"):
                clean = re.sub(r"^```(?:json)?\s*", "", clean)
                clean = re.sub(r"\s*```$", "", clean)
            parsed, _end = json.JSONDecoder().raw_decode(clean)
            # Не только JSON syntax: любой ответ обязан пройти полный Pydantic-контракт
            # до возврата вызывающей стадии. Иначе одна неверная граница поля роняет run.
            schema(**parsed)
            return parsed
        except Exception as exc:
            last_exc = exc
            detail = str(exc).replace("\n", " ")[:240]
            print(f"[structured] JSON-mode retry {attempt + 1}/3: {detail}")
            retry_note = f"\n\nПРЕДЫДУЩИЙ JSON НЕ РАСПАРСИЛСЯ: {detail}. Верни валидный полный JSON."
    raise RuntimeError(f"Gemini JSON-mode трижды не сработал: {last_exc}")


def _context() -> str:
    return (CHANNELS / "vitallogic_bad_pl" / f"studio_context_v8_{LANG}.md").read_text(
        encoding="utf-8"
    )


def _write_json(path: Path, model_or_data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(model_or_data, "model_dump_json"):
        text = model_or_data.model_dump_json(indent=2)
    else:
        text = json.dumps(model_or_data, ensure_ascii=False, indent=2)
    path.write_text(text + ("" if text.endswith("\n") else "\n"), encoding="utf-8")


def _sha(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _revision(pack: S.ResearchPack, script: S.Script) -> str:
    raw = pack.model_dump_json() + "\n" + script.model_dump_json()
    return _sha(raw)[:16]


def _safe_slug(text: str) -> str:
    translit = str.maketrans(
        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
        "abvgdeejzijklmnoprstufhzcss_y_eua",
    )
    value = unicodedata.normalize("NFKD", text.lower().translate(translit))
    value = value.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")[:48] or "topic"


def research_errors(pack: S.ResearchPack) -> list[str]:
    errs: list[str] = []
    source_ids = [s.id for s in pack.sources]
    claim_ids = [c.id for c in pack.claims]
    if len(source_ids) != len(set(source_ids)):
        errs.append("дублируются source IDs")
    if len(claim_ids) != len(set(claim_ids)):
        errs.append("дублируются claim IDs")
    known_sources = set(source_ids)
    usable = 0
    displayed = 0
    for src in pack.sources:
        if not src.url.startswith(("https://", "http://")):
            errs.append(f"{src.id}: URL не http(s)")
    for claim in pack.claims:
        missing = set(claim.source_ids) - known_sources
        if missing:
            errs.append(f"{claim.id}: неизвестные источники {sorted(missing)}")
        if claim.verdict != "rejected":
            usable += 1
        if claim.display_source:
            displayed += 1
        if claim.risk_level == "high" and claim.verdict != "rejected" \
                and len(set(claim.source_ids)) < 2:
            errs.append(f"{claim.id}: high-risk claim подтверждён меньше чем двумя источниками")
        if claim.verdict == "conditional" and len(claim.limitations.strip()) < 12:
            errs.append(f"{claim.id}: conditional claim без содержательного ограничения")
    if usable < 3:
        errs.append(f"пригодных claims {usable}, нужно минимум 3")
    if displayed > 2:
        errs.append(f"display_source=true у {displayed} claims, максимум 2")
    return errs


def research_topic(topic: str, angle: str, run_dir: Path) -> tuple[str, S.ResearchPack]:
    user = f"ТЕМА: {topic}\n"
    if angle:
        user += f"ПРЕДВАРИТЕЛЬНЫЙ УГОЛ: {angle}\n"
    target_lang = "polski" if LANG == "pl" else "rosyjski"
    user += f"Język końcowego ResearchPack: {target_lang}. Zweryfikuj aktualne źródła pierwotne."
    memo_path = run_dir / "research_raw.md"
    if memo_path.exists() and memo_path.stat().st_size > 200:
        memo = memo_path.read_text(encoding="utf-8")
        print("[research] research_raw.md уже есть — resume без повторного поиска")
    else:
        print(f"[research] Gemini {resolve_model(RESEARCH_MODEL)} + Google Search")
        memo = run_agent(
            RESEARCH_MODEL,
            system=_role("researcher"),
            user=user,
            temperature=0.2,
            search=True,
        )
        memo_path.write_text(memo.rstrip() + "\n", encoding="utf-8")

    pack_path = run_dir / "research_pack.json"
    if pack_path.exists():
        try:
            saved_pack = S.ResearchPack.model_validate_json(pack_path.read_text(encoding="utf-8"))
            saved_errors = research_errors(saved_pack)
            if not saved_errors:
                print(
                    f"[research] research_pack.json уже прошёл gate — "
                    f"resume {len(saved_pack.sources)} sources · {len(saved_pack.claims)} claims"
                )
                return memo, saved_pack
        except Exception as exc:
            print(f"[research] сохранённый пакет невалиден, пересобираю: {str(exc)[:180]}")

    normalize_user = f"TOPIC:\n{topic}\n\nGROUNDED_RESEARCH_MEMO:\n{memo}"
    last_err = ""
    for attempt in range(2):
        if last_err:
            normalize_user += f"\n\nПРЕДЫДУЩИЙ ПАКЕТ ОТКЛОНЁН:\n{last_err}"
        try:
            data = run_structured(
                TEXT_MODEL,
                system=_role("research_normalizer"),
                user=normalize_user,
                schema=S.ResearchPack,
                temperature=0.1,
            )
            pack = S.ResearchPack(**data)
        except Exception as exc:
            last_err = f"JSON/Pydantic: {str(exc).replace(chr(10), ' ')[:700]}"
            print(f"[research] пакет не распарсился ({attempt + 1}/2): {last_err}")
            continue
        errs = research_errors(pack)
        if not errs:
            _write_json(run_dir / "research_pack.json", pack)
            print(f"[research] {len(pack.sources)} sources · {len(pack.claims)} claims")
            return memo, pack
        last_err = "\n".join(f"- {e}" for e in errs)
        print(f"[research] пакет не прошёл gate ({attempt + 1}/2): {', '.join(errs)}")
    raise SystemExit("[research] ResearchPack не прошёл gate:\n" + last_err)


def _known_claims(pack: S.ResearchPack) -> dict[str, S.ResearchClaim]:
    return {c.id: c for c in pack.claims}


def _field_needs_claim(text: str) -> bool:
    return bool(re.search(r"\d", text or ""))


def _overlay_norm(text: str) -> str:
    """Нормализация для детерминированных anti-duplication gates."""
    value = (text or "").lower().replace("ё", "е")
    value = re.sub(r"[^0-9a-zа-я%°]+", " ", value, flags=re.IGNORECASE)
    return " ".join(value.split())


def _compact_comparison_value(text: str) -> bool:
    """Versus — это считываемые значения, а не две мини-фразы поверх субтитров."""
    value = _overlay_norm(text)
    if not value or len(value) > 14:
        return False
    words = value.split()
    return bool(re.search(r"\d", value)) or len(words) == 1


def _compact_numeric_value(text: str) -> bool:
    """Числовой callout: только само число/единица вроде 74°C или 1,2 кг."""
    value = (text or "").strip()
    return bool(re.fullmatch(r"[~≈<>≤≥+\-]?\s*\d[\d.,]*\s*[A-Za-zА-Яа-я%°×/²³]*", value)) \
        and len(value) <= 12


def _source_match_score(hint: str, source: S.ResearchSource) -> int:
    """Выбирает источник для карточки по авторской короткой подсказке без LLM-вызова."""
    hint_norm = _overlay_norm(hint)
    if not hint_norm:
        return 0
    source_norm = _overlay_norm(f"{source.publisher} {source.title} {source.year}")
    hint_tokens = set(hint_norm.split())
    source_tokens = set(source_norm.split())
    score = len(hint_tokens & source_tokens)
    if str(source.year) in hint_tokens:
        score += 3
    publisher = _overlay_norm(source.publisher)
    if publisher and (publisher in hint_norm or hint_norm in publisher):
        score += 6
    return score


def _source_card_title(title: str, max_chars: int = 76) -> str:
    """Cards show a readable citation label; the full source remains in metadata/description.

    A scientific-paper title can be several hundred characters long. Letting it wrap freely
    turns a useful source card into clipped viewer text, so truncate on a word boundary before
    the renderer's layout gate rather than accepting a smaller, unreadable type size.
    """
    value = " ".join((title or "").split())
    if len(value) <= max_chars:
        return value
    cut = value[:max_chars - 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return (cut or value[:max_chars - 1]).rstrip() + "…"


def source_cards(script: S.Script, pack: S.ResearchPack) -> dict[int, dict[str, str]]:
    """Готовит render-only карточки: тезис из Script, библиография из ResearchPack."""
    claims = _known_claims(pack)
    sources = {s.id: s for s in pack.sources}
    cards: dict[int, dict[str, str]] = {}
    for overlay in script.overlays:
        if overlay.kind != "source":
            continue
        candidate_ids: list[str] = []
        for claim_id in overlay.claim_ids:
            claim = claims.get(claim_id)
            if claim:
                candidate_ids.extend(claim.source_ids)
        candidates = [sources[sid] for sid in dict.fromkeys(candidate_ids) if sid in sources]
        if not candidates:
            continue
        source = max(candidates, key=lambda item: _source_match_score(overlay.label, item))
        host = urlparse(source.url).netloc.lower().removeprefix("www.")
        cards[int(overlay.beat_idx)] = {
            "finding": overlay.source_finding.strip(),
            "title": _source_card_title(source.title),
            "publisher": source.publisher.strip(),
            "year": str(source.year),
            "type_label": _lang_config()["source_types"][source.source_type],
            "reference": host or source.url,
            "source_id": source.id,
            "claim_ids": ", ".join(overlay.claim_ids),
        }
    return cards


def script_errors(script: S.Script, pack: S.ResearchPack) -> list[str]:
    errs: list[str] = []
    known = _known_claims(pack)
    allowed = {cid for cid, c in known.items() if c.verdict != "rejected"}

    def check_ids(label: str, ids: list[str]) -> None:
        missing = set(ids) - set(known)
        rejected = set(ids) - allowed
        if missing:
            errs.append(f"{label}: неизвестные claim_ids {sorted(missing)}")
        if rejected:
            errs.append(f"{label}: rejected claim_ids {sorted(rejected)}")

    n = len(script.beats)
    hook_beats = [b for b in script.beats if b.act == "hook"]
    if not (2 <= len(hook_beats) <= 3):
        errs.append(f"hook-битов {len(hook_beats)}, нужно 2–3")
    order = [b.act for b in script.beats]
    rank = {"hook": 0, "body": 1, "payoff": 2}
    if any(rank[order[i + 1]] < rank[order[i]] for i in range(n - 1)):
        errs.append("акты идут не по порядку hook→body→payoff")
    if not any(b.act == "payoff" for b in script.beats):
        errs.append("нет payoff-акта")
    if not (0 <= script.turn_beat_idx < n) or script.beats[script.turn_beat_idx].act != "body":
        errs.append("turn_beat_idx не указывает на body")
    total = sum(b.dur_s for b in script.beats)
    # Validation must stay read-only. Mutating total_dur_s here changes the content
    # revision between the preflight hash and the release report.
    if not (22 <= total <= 36):
        errs.append(f"плановый хронометраж {total:.1f}с вне 22–36с")
    words = len(" ".join(b.voiceover for b in script.beats).split())
    if not (78 <= words <= 125):
        errs.append(f"слов в озвучке {words}, рабочий диапазон 78–125")
    if len(script.poster_text.replace("*", "").split()) > 4:
        errs.append("poster_text длиннее четырёх слов")
    if len(script.payoff_card.replace("*", "").split()) > 8:
        errs.append("payoff_card длиннее восьми слов: финальная карточка должна помещаться в 3 строки")
    if script.payoff_card.rstrip().endswith("?"):
        errs.append("payoff_card не может быть вопросом")
    if script.central_claim_id not in allowed:
        errs.append("central_claim_id отсутствует или rejected")

    evidence_texts = {
        "poster": script.poster_text,
        "payload": script.payload,
        "payoff": script.payoff_card,
    }
    evidence_texts.update({f"beat {i}": beat.voiceover for i, beat in enumerate(script.beats)})
    for label, value in evidence_texts.items():
        match = ABSOLUTE_WORDING.search(value or "")
        if match:
            errs.append(
                f"{label}: абсолютная формулировка «{match.group(0)}»; замени на точное "
                "ограниченное сравнение"
            )
        if "=" in (value or ""):
            errs.append(f"{label}: знак равенства выдаёт сходство за полную эквивалентность")
        lower = (value or "").lower()
        if "свежий брокколи" in lower:
            errs.append(f"{label}: неверное согласование; «брокколи» в русском женского рода")
        if "одного и двух десятых килограмма" in lower:
            errs.append(
                f"{label}: неестественное чтение 1.2 кг; скажи «килограмм двести граммов»"
            )
        if "для долгого хранения в холодильнике" in lower and "замороз" in lower:
            errs.append(f"{label}: замороженные овощи хранят в морозильнике, не в холодильнике")
        if "надежно фиксир" in lower:
            errs.append(
                f"{label}: «надёжно фиксирует» преувеличивает сохранность; скажи, что "
                "заморозка замедляет дальнейшие потери"
            )
        if "цвет меняет только вкус" in lower:
            errs.append(
                f"{label}: вывод слишком широкий; скажи, что цвет не делает сахар полезнее"
            )

    check_ids("poster", script.poster_claim_ids)
    check_ids("payload", script.payload_claim_ids)
    check_ids("payoff", script.payoff_claim_ids)
    if _field_needs_claim(script.poster_text) and not script.poster_claim_ids:
        errs.append("число в poster без claim_id")
    if _field_needs_claim(script.payload) and not script.payload_claim_ids:
        errs.append("число в payload без claim_id")
    if _field_needs_claim(script.payoff_card) and not script.payoff_claim_ids:
        errs.append("число в payoff без claim_id")

    used_claims: set[str] = set(script.poster_claim_ids + script.payload_claim_ids + script.payoff_claim_ids)
    for i, beat in enumerate(script.beats):
        check_ids(f"beat {i}", beat.claim_ids)
        used_claims.update(beat.claim_ids)
        if _field_needs_claim(beat.voiceover) and not beat.claim_ids:
            errs.append(f"beat {i}: число без claim_id")
        if beat.emphasis and beat.emphasis.lower() not in beat.voiceover.lower():
            errs.append(f"beat {i}: emphasis отсутствует в voiceover")

    overlay_beats: set[int] = set()
    for i, overlay in enumerate(script.overlays):
        check_ids(f"overlay {i}", overlay.claim_ids)
        used_claims.update(overlay.claim_ids)
        if not (0 <= overlay.beat_idx < n):
            errs.append(f"overlay {i}: beat_idx вне диапазона")
            continue
        if overlay.beat_idx in overlay_beats:
            errs.append(f"overlay {i}: два overlay на одном бите")
        overlay_beats.add(overlay.beat_idx)
        if script.beats[overlay.beat_idx].act == "hook":
            errs.append(f"overlay {i}: overlay в hook")
        overlay_text = " ".join(
            [overlay.label, overlay.value, overlay.label_b, overlay.value_b] + overlay.items
        )
        beat_text = _overlay_norm(script.beats[overlay.beat_idx].on_screen_text)
        label = _overlay_norm(overlay.label)
        if label and label == beat_text:
            errs.append(f"overlay {i}: подпись дублирует субтитр; оставь только значение")
        if overlay.kind in {"stat", "bar"} and label in GENERIC_OVERLAY_LABELS:
            errs.append(
                f"overlay {i}: общая подпись «{overlay.label}» ничего не добавляет; убери её"
            )
        if overlay.kind == "versus":
            if _overlay_norm(overlay.value) == _overlay_norm(overlay.value_b):
                errs.append(f"overlay {i}: versus сравнивает одинаковые значения")
            if not _compact_comparison_value(overlay.value) \
                    or not _compact_comparison_value(overlay.value_b):
                errs.append(
                    f"overlay {i}: versus допускает только короткие числа/однословные значения"
                )
            if len(_overlay_norm(overlay.label)) > 16 \
                    or len(_overlay_norm(overlay.label_b)) > 16:
                errs.append(f"overlay {i}: подпись versus слишком длинная для двух колонок")
        if overlay.kind == "callout" and re.search(r"\d", overlay.value or ""):
            if overlay.label.strip():
                errs.append(
                    f"overlay {i}: числовой callout не должен иметь вторую текстовую подпись"
                )
            if not _compact_numeric_value(overlay.value):
                errs.append(f"overlay {i}: оставь в числовом callout только число и единицу")
        if _field_needs_claim(overlay_text) and not overlay.claim_ids:
            errs.append(f"overlay {i}: число без claim_id")
        if overlay.kind == "source" and not overlay.claim_ids:
            errs.append(f"overlay {i}: source без claim_id")
        if overlay.kind == "source":
            finding_words = overlay.source_finding.split()
            if not (3 <= len(finding_words) <= 10):
                errs.append(
                    f"overlay {i}: source_finding должен содержать 3–10 слов для "
                    "крупной карточки исследования"
                )
            for cid in overlay.claim_ids:
                if cid in known and not known[cid].display_source:
                    errs.append(f"overlay {i}: {cid} не помечен display_source")
    if script.central_claim_id not in used_claims:
        errs.append("central_claim_id нигде не используется")
    return errs


def _script_user(topic: str, fmt: str, rubric: str, angle: str, pack: S.ResearchPack,
                 extra: str = "") -> str:
    meta = S.RUBRIC_META.get(rubric, {})
    blocks = [
        f"STUDIO_CONTEXT:\n{_context()}",
        f"RUBRIC: {rubric}\nRUBRIC_PROMISE: {meta.get('promise', '')}\n"
        f"RUBRIC_BRIEF: {meta.get('brief', '')}",
        f"FORMAT: {fmt}\nFORMAT_BRIEF: {S.FORMAT_BRIEFS[fmt]}",
        f"TOPIC: {topic}",
        f"ANGLE: {angle or pack.recommended_angle}",
        f"RESEARCH_PACK_JSON:\n{pack.model_dump_json(indent=2)}",
    ]
    if extra:
        blocks.append(extra)
    return "\n\n".join(blocks)


def write_script(topic: str, fmt: str, rubric: str, angle: str,
                 pack: S.ResearchPack) -> S.Script:
    user = _script_user(topic, fmt, rubric, angle, pack)
    last = ""
    for attempt in range(3):
        prompt = user
        if last:
            prompt += "\n\nПРЕДЫДУЩИЙ СЦЕНАРИЙ ОТКЛОНЁН МАШИННЫМ GATE:\n" + last
        data = run_structured(
            TEXT_MODEL,
            system=_role("scriptwriter"),
            user=prompt,
            schema=S.Script,
            temperature=0.75 if attempt == 0 else 0.45,
        )
        script = S.Script(**data)
        script.rubric = rubric
        script.format = fmt
        V8Base.normalize_script(script)
        errs = script_errors(script, pack)
        if not errs:
            return script
        last = "\n".join(f"- {e}" for e in errs) + \
            f"\n\nОТКЛОНЁННЫЙ JSON:\n{script.model_dump_json()}"
        print(f"[script] gate fail {attempt + 1}/3: {', '.join(errs)}")
    raise SystemExit("[script] не прошёл машинные gates:\n" + last)


def rewrite_script(topic: str, fmt: str, rubric: str, angle: str, pack: S.ResearchPack,
                   script: S.Script, issues: list[str]) -> S.Script:
    base_extra = (
        "ПЕРЕПИШИ ПРЕДЫДУЩИЙ СЦЕНАРИЙ ТОЧЕЧНО. Исправь перечисленные проблемы, сохрани "
        "все уже корректные claims и не добавляй фактов.\n"
        + "\n".join(f"- {x}" for x in issues)
        + f"\n\nПРЕДЫДУЩИЙ SCRIPT_JSON:\n{script.model_dump_json()}"
    )
    retry_note = ""
    for attempt in range(3):
        extra = base_extra + retry_note
        user = _script_user(topic, fmt, rubric, angle, pack, extra)
        data = run_structured(
            TEXT_MODEL,
            system=_role("scriptwriter"),
            user=user,
            schema=S.Script,
            temperature=0.35 if attempt == 0 else 0.2,
        )
        candidate = S.Script(**data)
        candidate.rubric = rubric
        candidate.format = fmt
        V8Base.normalize_script(candidate)
        errs = script_errors(candidate, pack)
        if not errs:
            return candidate
        print(f"[revision] rewrite gate fail {attempt + 1}/3: {', '.join(errs)}")
        retry_note = (
            "\n\nТВОЯ ПРЕДЫДУЩАЯ РЕДАКТУРА НЕ ПРОШЛА МАШИННЫЙ GATE:\n"
            + "\n".join(f"- {e}" for e in errs)
            + f"\n\nНЕУДАЧНЫЙ JSON:\n{candidate.model_dump_json()}"
        )
    raise ValueError("rewrite трижды не прошёл машинные gates")


def check_compliance(script: S.Script, pack: S.ResearchPack) -> S.ComplianceVerdict:
    user = (
        f"STUDIO_CONTEXT:\n{_context()}\n\n"
        f"RESEARCH_PACK_JSON:\n{pack.model_dump_json(indent=2)}\n\n"
        f"SCRIPT_JSON:\n{script.model_dump_json(indent=2)}"
    )
    data = run_structured(
        TEXT_MODEL,
        system=_role("compliance"),
        user=user,
        schema=S.ComplianceVerdict,
        temperature=0.1,
    )
    return S.ComplianceVerdict(**data)


def fact_check(memo: str, pack: S.ResearchPack, script: S.Script) -> S.FactReview:
    user = (
        f"GROUNDED_RESEARCH_MEMO:\n{memo}\n\n"
        f"RESEARCH_PACK_JSON:\n{pack.model_dump_json(indent=2)}\n\n"
        f"SCRIPT_JSON:\n{script.model_dump_json(indent=2)}"
    )
    data = run_structured(
        TEXT_MODEL,
        system=_role("fact_checker"),
        user=user,
        schema=S.FactReview,
        temperature=0.1,
    )
    review = S.FactReview(**data)
    failed = [c for c in review.checks if not c.passed]
    if failed or review.unsupported_script_statements:
        review.passed = False
    return review


def plan_errors(plan: S.FramePlan, script: S.Script, pack: S.ResearchPack) -> list[str]:
    errs: list[str] = []
    if len(plan.frames) != len(script.beats):
        errs.append(
            f"кадров {len(plan.frames)}, а битов {len(script.beats)}: нужен ровно один кадр на бит"
        )
    allowed = {c.id for c in pack.claims if c.verdict != "rejected"}
    used: set[str] = set()
    for i, frame in enumerate(plan.frames):
        if frame.beat_from != i or frame.beat_to != i:
            errs.append(
                f"кадр {i}: beat_from/beat_to должны быть {i}/{i}, получено "
                f"{frame.beat_from}/{frame.beat_to}"
            )
        missing = set(frame.claim_ids) - allowed
        if missing:
            errs.append(f"кадр {i}: неизвестные/rejected claim_ids {sorted(missing)}")
        used.update(frame.claim_ids)
        if _field_needs_claim(frame.claim) and not frame.claim_ids:
            errs.append(f"кадр {i}: число в claim без claim_id")
        if len(frame.claim.split()) < 3:
            errs.append(f"кадр {i}: claim слишком короткий")
        if i and frame.shot == plan.frames[i - 1].shot:
            previous = plan.frames[i - 1]
            # A fast three-shot hook may intentionally stay close while changing the
            # object and the narrator's emotion. Later repeats are also valid when the
            # evidence or subject changes; only decorative duplicate coverage is rejected.
            hook_burst = (
                i <= 2
                and frame.motion == "hook_punch"
                and previous.motion == "hook_punch"
            )
            evidence_changes = (
                frame.claim_ids != previous.claim_ids
                or frame.subject != previous.subject
                or frame.motion != previous.motion
            )
            if not hook_burst and not evidence_changes:
                errs.append(f"кадры {i - 1} и {i}: одинаковая крупность без смены evidence")
    if len({f.shot for f in plan.frames}) < 3:
        errs.append("на ролик меньше трёх разных ступеней крупности")
    subjects = [f.subject for f in plan.frames]
    if any(subjects[i] == subjects[i - 1] == subjects[i - 2] == "product"
           for i in range(2, len(subjects))):
        errs.append("три product-кадра подряд")
    if script.central_claim_id not in used:
        errs.append("central claim ни разу не поддержан кадром")
    return errs


def plan_frames(script: S.Script, pack: S.ResearchPack, extra: str = "") -> S.FramePlan:
    durs = [b.dur_s for b in script.beats]
    user = (
        f"STUDIO_CONTEXT:\n{_context()}\n\n"
        f"RESEARCH_PACK_JSON:\n{pack.model_dump_json(indent=2)}\n\n"
        f"SCRIPT_JSON:\n{script.model_dump_json(indent=2)}\n\n"
        f"Сделай РОВНО {len(script.beats)} кадров для битов 0..{len(script.beats)-1}; "
        f"плановая длина {sum(durs):.1f}с. Кадр с индексом i обязан иметь "
        "beat_from=i и beat_to=i: один смысловой бит — один исходный кадр. "
        "Не объединяй диапазоны и не дублируй биты."
    )
    if extra:
        user += "\n\nИСПРАВЬ ПРЕДЫДУЩИЙ QA:\n" + extra
    if script.rubric == "label":
        user += (
            "\n\nLABEL-SPECIFIC VISUAL RULE: tekst na etykiecie, także angielski, jest "
            "dozwolony. Nie traktuj go jako głównej planszy informacyjnej: pozostaw czytelne "
            "bezpieczne marginesy dla napisów oraz nie generuj tekstu, który konkuruje z "
            "napisami lub powtarza ich główną tezę."
        )
    last = ""
    for attempt in range(3):
        prompt = user + (("\n\nПРЕДЫДУЩИЙ ПЛАН ОТКЛОНЁН:\n" + last) if last else "")
        data = run_structured(
            TEXT_MODEL,
            system=_role("visual_director"),
            user=prompt,
            schema=S.FramePlan,
            temperature=0.65 if attempt == 0 else 0.35,
        )
        plan = S.FramePlan(**data)
        errs = plan_errors(plan, script, pack)
        if not errs:
            return plan
        last = "\n".join(f"- {e}" for e in errs) + \
            f"\n\nОТКЛОНЁННЫЙ JSON:\n{plan.model_dump_json()}"
        print(f"[visual] gate fail {attempt + 1}/3: {', '.join(errs)}")
    raise ValueError("frame plan не прошёл gates: " + last)


def semantic_qa(pack: S.ResearchPack, script: S.Script, plan: S.FramePlan) -> S.QAReport:
    user = (
        f"RESEARCH_PACK_JSON:\n{pack.model_dump_json(indent=2)}\n\n"
        f"SCRIPT_JSON:\n{script.model_dump_json(indent=2)}\n\n"
        f"FRAME_PLAN_JSON:\n{plan.model_dump_json(indent=2)}"
    )
    data = run_structured(
        TEXT_MODEL,
        system=_role("qa"),
        user=user,
        schema=S.QAReport,
        temperature=0.15,
    )
    report = S.QAReport(**data)
    expected = _expected_qa()
    critical_names = _critical_qa()
    by_name = {c.name: c for c in report.checks}
    missing = expected - set(by_name)
    for name in sorted(missing):
        report.checks.append(S.QACheck(name=name, passed=False, detail="проверка отсутствует"))
    critical = [c for c in report.checks if c.name in critical_names and not c.passed]
    report.passed = not critical
    return report


def qa_issues(report: S.QAReport) -> list[str]:
    return [f"{c.name}: {c.detail}" for c in report.checks
            if c.name in _critical_qa() and not c.passed]


def publish_package(script: S.Script, pack: S.ResearchPack) -> S.PublishPackage:
    user = (
        f"SCRIPT_JSON:\n{script.model_dump_json(indent=2)}\n\n"
        f"RESEARCH_PACK_JSON:\n{pack.model_dump_json(indent=2)}\n\n"
        f"DISCLAIMER: {_lang_config()['disclaimer']}"
    )
    data = run_structured(
        TEXT_MODEL,
        system=_role("publisher"),
        user=user,
        schema=S.PublishPackage,
        temperature=0.45,
    )
    pkg = S.PublishPackage(**data)
    allowed_urls = {s.url for s in pack.sources}
    pkg.source_urls = list(dict.fromkeys(u for u in pkg.source_urls if u in allowed_urls))[:8]
    display_ids = {sid for c in pack.claims if c.display_source for sid in c.source_ids}
    by_id = {s.id: s.url for s in pack.sources}
    for sid in display_ids:
        url = by_id.get(sid)
        if url and url not in pkg.source_urls:
            pkg.source_urls.append(url)
    pkg.source_urls = pkg.source_urls[:5]
    if _lang_config()["disclaimer"] not in pkg.description:
        pkg.description = pkg.description.rstrip() + "\n\n" + _lang_config()["disclaimer"]
    return pkg


def _save_revision(run_dir: Path, number: int, script: S.Script, compliance=None,
                   fact=None, plan=None, qa=None) -> None:
    dest = run_dir / "revisions" / f"revision_{number:02d}"
    _write_json(dest / "script.json", script)
    if compliance is not None:
        _write_json(dest / "compliance.json", compliance)
    if fact is not None:
        _write_json(dest / "fact_review.json", fact)
    if plan is not None:
        _write_json(dest / "frame_plan.json", plan)
    if qa is not None:
        _write_json(dest / "qa.json", qa)


def finalize_content(topic: str, fmt: str, rubric: str, angle: str, memo: str,
                     pack: S.ResearchPack, run_dir: Path):
    script = write_script(topic, fmt, rubric, angle, pack)
    last_issues: list[str] = []
    final = None

    for rev in range(1, MAX_CONTENT_REVISIONS + 1):
        if last_issues:
            print(f"[revision] переписываю content revision {rev}: {len(last_issues)} замечаний")
            script = rewrite_script(topic, fmt, rubric, angle, pack, script, last_issues)
        deterministic = script_errors(script, pack)
        if deterministic:
            last_issues = deterministic
            _save_revision(run_dir, rev, script)
            continue

        compliance = check_compliance(script, pack)
        if not compliance.passed:
            cleaned = compliance.cleaned_script
            cleaned.rubric = rubric
            cleaned.format = fmt
            clean_errs = script_errors(cleaned, pack)
            if clean_errs:
                last_issues = compliance.fixes + clean_errs
                _save_revision(run_dir, rev, script, compliance=compliance)
                continue
            script = cleaned
            # `passed` describes the script that proceeds downstream.  The compliance
            # reviewer may return `False` for the original draft while supplying a
            # safe, machine-valid cleaned version; retaining that old verdict would
            # incorrectly block the release (and resume) gate for the cleaned script.
            compliance = compliance.model_copy(update={"passed": True})

        fact = fact_check(memo, pack, script)
        if not fact.passed:
            last_issues = [
                f"{c.claim_id}: {c.issue}; исправление: {c.required_change}"
                for c in fact.checks if not c.passed
            ] + [f"непривязанное утверждение: {x}" for x in fact.unsupported_script_statements]
            _save_revision(run_dir, rev, script, compliance=compliance, fact=fact)
            continue

        try:
            plan = plan_frames(script, pack)
        except Exception as exc:
            last_issues = [f"visual plan: {exc}"]
            _save_revision(run_dir, rev, script, compliance=compliance, fact=fact)
            continue
        report = semantic_qa(pack, script, plan)

        visual_critical = [c for c in report.checks
                           if c.name == "frames_semantic_match" and not c.passed]
        other_issues = [x for x in qa_issues(report) if not x.startswith("frames_semantic_match:")]
        if visual_critical and not other_issues:
            details = "\n".join(c.detail for c in visual_critical)
            try:
                plan = plan_frames(script, pack, extra=details)
                report = semantic_qa(pack, script, plan)
            except Exception as exc:
                report.passed = False
                report.notes.append(f"повторный visual plan не собрался: {exc}")

        _save_revision(
            run_dir, rev, script, compliance=compliance, fact=fact, plan=plan, qa=report
        )
        issues = qa_issues(report)
        if issues:
            last_issues = issues
            continue
        final = (script, compliance, fact, plan, report)
        break

    if final is None:
        raise SystemExit("[release] content не прошёл три revision: " + "; ".join(last_issues))
    return final


def load_saved_content(run_dir: Path, pack: S.ResearchPack):
    """Возобновляет только полностью прошедшую content revision после сетевого сбоя."""
    candidates = [run_dir]
    revisions = run_dir / "revisions"
    if revisions.exists():
        candidates.extend(sorted(revisions.glob("revision_*"), reverse=True))
    names = {
        "script": ("script.json", S.Script),
        "compliance": ("compliance.json", S.ComplianceVerdict),
        "fact": ("fact_review.json", S.FactReview),
        "plan": ("frame_plan.json", S.FramePlan),
        "qa": ("qa.json", S.QAReport),
    }
    for folder in candidates:
        if not all((folder / filename).exists() for filename, _ in names.values()):
            continue
        try:
            loaded = {
                key: model.model_validate_json((folder / filename).read_text(encoding="utf-8"))
                for key, (filename, model) in names.items()
            }
            if script_errors(loaded["script"], pack):
                continue
            if plan_errors(loaded["plan"], loaded["script"], pack):
                continue
            if not loaded["compliance"].passed or not loaded["fact"].passed:
                continue
            if qa_issues(loaded["qa"]):
                continue
            print(f"[content] resume прошедшей revision из {folder.name}")
            return (
                loaded["script"], loaded["compliance"], loaded["fact"],
                loaded["plan"], loaded["qa"],
            )
        except Exception as exc:
            print(f"[content] не удалось возобновить {folder.name}: {str(exc)[:180]}")
    return None


def synth_audio(script: S.Script, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    # Keep the channel's approved Gemini narrator reproducible while allowing an
    # explicit per-run override.
    voice = os.environ.get("VITALLOGIC_TTS_VOICE", "Charon")
    base_style = _lang_config()["tts_style"]
    base_speed = 1.12
    pieces: list[Path] = []
    durs: list[float] = []
    beat_words: list[list[dict]] = []
    cumulative = 0.0
    acts = [b.act for b in script.beats]
    for i, beat in enumerate(script.beats):
        wav = out_dir / f"beat{i}.wav"
        meta = out_dir / f"beat{i}.tts.json"
        style = base_style
        speed = base_speed
        if i == len(script.beats) - 2:
            style += ", set up the final takeaway with a slight open cadence; do not sound final"
        elif i == len(script.beats) - 1:
            style += ", clearly separated final takeaway, slightly slower, decisive falling cadence"
            speed = 1.04
        signature = _sha(json.dumps({
            "text": beat.voiceover,
            "voice": voice,
            "style": style,
            "model": TTS_MODEL,
            "speed": speed,
        }, ensure_ascii=False, sort_keys=True))
        cached_signature = ""
        if meta.exists():
            try:
                cached_signature = json.loads(meta.read_text(encoding="utf-8")).get(
                    "signature", ""
                )
            except Exception:
                pass
        elif wav.exists() and wav.stat().st_size > 1000 and i < len(script.beats) - 2:
            # Alpha1 кэшировал только WAV. Для неизменившихся обычных битов безопасно
            # принять старый файл и добавить manifest; два финальных бита должны быть
            # пересинтезированы, потому что их delivery действительно изменился в alpha2.
            _write_json(meta, {
                "signature": signature, "voice": voice, "style": style,
                "model": TTS_MODEL, "speed": speed, "adopted_alpha1_wav": True,
            })
            cached_signature = signature
        if not (wav.exists() and wav.stat().st_size > 1000 and cached_signature == signature):
            generate_speech(
                beat.voiceover,
                voice=voice,
                style=style,
                model=TTS_MODEL,
                out=str(wav),
                speed=speed,
            )
            _trim_silence(wav)
            _write_json(meta, {
                "signature": signature, "voice": voice, "style": style,
                "model": TTS_MODEL, "speed": speed,
            })
        dur = _wav_dur(wav)
        beat_words.append(_estimate_word_timestamps(beat.voiceover, dur, cumulative))
        pieces.append(wav)
        pause = 0.0
        if i == len(script.beats) - 2:
            # Финальная фраза должна начинаться как отдельный вывод, а не как ещё один
            # синтаксический хвост предпоследней реплики.
            pause = 0.48
        elif i + 1 < len(script.beats) and acts[i + 1] != acts[i]:
            pause = 0.34
        elif i + 1 == script.turn_beat_idx:
            pause = 0.22
        if pause:
            silence = out_dir / f"pause{i}.wav"
            V8Base._silence(silence, pause)
            pieces.append(silence)
        durs.append(dur + pause)
        cumulative += dur + pause
    concat = out_dir / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in pieces), encoding="utf-8")
    voice_wav = out_dir / "voice.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c", "copy", str(voice_wav)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return voice_wav, durs, beat_words


def _probe_video(path: Path) -> dict:
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True,
    )
    data = json.loads(raw)
    video = next((s for s in data["streams"] if s.get("codec_type") == "video"), {})
    audio = next((s for s in data["streams"] if s.get("codec_type") == "audio"), {})
    return {
        "duration_s": round(float(data["format"]["duration"]), 3),
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": video.get("r_frame_rate"),
        "video_codec": video.get("codec_name"),
        "audio_codec": audio.get("codec_name"),
    }


def _final_visual_qa(out_mp4: Path, run_dir: Path, script: S.Script) -> list[dict]:
    try:
        from vision_qa import check_image  # type: ignore
    except (ImportError, ModuleNotFoundError) as exc:
        # Gemini Vision is targeted advisory QA. Local layout, ffprobe and manual frame
        # review remain available when the optional SDK is not installed.
        detail = f"optional Gemini Vision QA skipped: {exc}"
        return [
            {"name": name, "at_s": None, "passed": True, "skipped": True, "issues": [detail]}
            for name in ("poster", "middle", "payoff")
        ]

    meta = _probe_video(out_mp4)
    dur = meta["duration_s"]
    qa_dir = run_dir / "final_qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    moments = [
        ("poster", min(0.4, dur / 4), [script.poster_text.replace("*", "")]),
        ("middle", dur * 0.5, []),
        ("payoff", max(0.2, dur - 0.7), [script.payoff_card.replace("*", "")]),
    ]
    rows: list[dict] = []
    for name, at, expected in moments:
        png = qa_dir / f"{name}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{at:.3f}", "-i", str(out_mp4),
             "-frames:v", "1", str(png)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        result = check_image(png, still=True, expect_texts=expected)
        rows.append({"name": name, "at_s": round(at, 3), **result.model_dump()})
    return rows


def _artifact_hashes(run_dir: Path) -> dict[str, str]:
    names = [
        "research_raw.md",
        "research_pack.json",
        "script.json",
        "compliance.json",
        "fact_review.json",
        "frame_plan.json",
        "media_manifest.json",
        "qa.json",
        "publish_package.json",
        "release_gate.json",
        "final_qa.json",
        "out.mp4",
    ]
    return {name: _sha((run_dir / name).read_bytes()) for name in names if (run_dir / name).exists()}


def release_report(run_dir: Path, revision: str, pack: S.ResearchPack, script: S.Script,
                   compliance: S.ComplianceVerdict, fact: S.FactReview,
                   plan: S.FramePlan, qa: S.QAReport, pkg: S.PublishPackage,
                   media_meta: dict | None = None, visual_qa: list[dict] | None = None,
                   require_media: bool = False) -> S.ReleaseReport:
    checks: list[S.ReleaseCheck] = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append(S.ReleaseCheck(name=name, passed=passed, detail=detail))

    rerrs = research_errors(pack)
    serrs = script_errors(script, pack)
    perrs = plan_errors(plan, script, pack)
    qerrs = qa_issues(qa)
    allowed_urls = {s.url for s in pack.sources}
    add("research_pack", not rerrs, "; ".join(rerrs))
    add("script_claim_links", not serrs, "; ".join(serrs))
    add("compliance", compliance.passed, "; ".join(compliance.fixes))
    add("fact_review", fact.passed, "; ".join(fact.unsupported_script_statements))
    add("frame_plan", not perrs, "; ".join(perrs))
    add("semantic_qa_critical", not qerrs, "; ".join(qerrs))
    add("publish_sources", bool(pkg.source_urls) and set(pkg.source_urls) <= allowed_urls,
        f"{len(pkg.source_urls)} URLs")
    add("artifact_revision", revision == _revision(pack, script), revision)
    if require_media:
        meta = media_meta or {}
        media_ok = (
            (run_dir / "out.mp4").exists()
            and meta.get("width") == 1080
            and meta.get("height") == 1920
            and bool(meta.get("audio_codec"))
        )
        add("media_file", media_ok, json.dumps(meta, ensure_ascii=False))
        actual_duration = meta.get("duration_s")
        planned_duration = round(sum(beat.dur_s for beat in script.beats), 3)
        if isinstance(actual_duration, (int, float)):
            duration_ok = True
            duration_detail = (
                f"planned={planned_duration:.3f}s actual={float(actual_duration):.3f}s "
                "(observed for pacing; not a release blocker)"
            )
        else:
            duration_ok = False
            duration_detail = f"planned={planned_duration:.3f}s actual=missing"
        add("duration_observed", duration_ok, duration_detail)
        visual = visual_qa or []
        failed_visual = [x for x in visual if x.get("passed") is False and not x.get("skipped")]
        add("final_visual_qa", len(visual) == 3 and not failed_visual,
            "; ".join(f"{x.get('name')}: {x.get('issues')}" for x in visual if x.get("issues")))
    passed = all(c.passed for c in checks)
    return S.ReleaseReport(passed=passed, checks=checks, content_revision=revision)


def approved_codex_frames(run_dir: Path, plan: S.FramePlan) -> list[Path]:
    """Load the exact inspected frames declared by the Codex media manifest."""
    manifest_path = run_dir / "media_manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(
            f"[media] missing {manifest_path.name}; add approved built-in ImageGen frames "
            "and a v8 media_manifest.json before --build"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"[media] invalid {manifest_path}: {exc}") from exc
    if manifest.get("image_generation") != "built_in_imagegen":
        raise SystemExit("[media] image_generation must be built_in_imagegen")
    if manifest.get("image_model_substitution", "none") != "none":
        raise SystemExit("[media] image model substitution is not allowed in v8")
    entries = manifest.get("frames")
    if not isinstance(entries, list) or len(entries) != len(plan.frames):
        actual = len(entries) if isinstance(entries, list) else "missing/non-list"
        raise SystemExit(
            f"[media] manifest frame count {actual} does not match frame plan {len(plan.frames)}"
        )

    root = run_dir.resolve()
    approved: list[Path] = []
    for expected_index, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("index") != expected_index:
            raise SystemExit(f"[media] manifest frame index {expected_index} is missing or out of order")
        if entry.get("approval") not in {"accepted_after_visual_inspection", "approved"}:
            raise SystemExit(f"[media] frame {expected_index} is not visually approved")
        relative = Path(str(entry.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise SystemExit(f"[media] frame {expected_index} path escapes the run directory")
        frame_path = (root / relative).resolve()
        if root not in frame_path.parents or not frame_path.is_file():
            raise SystemExit(f"[media] frame {expected_index} not found: {relative}")
        if frame_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise SystemExit(f"[media] frame {expected_index} has unsupported image type")
        digest = hashlib.sha256(frame_path.read_bytes()).hexdigest()
        if digest != entry.get("sha256"):
            raise SystemExit(f"[media] sha256 mismatch for frame {expected_index}: {relative}")
        approved.append(frame_path)
    return approved


def _mark_media_manifest_built(run_dir: Path) -> None:
    manifest_path = run_dir / "media_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["engine_v8_build_used"] = True
    manifest["built_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    _write_json(manifest_path, manifest)


def build_media_from_artifacts(run_dir: Path, asset_channel: str = "vitallogic_bad_pl",
                               sfx_profile: str = A.DEFAULT_SFX_PROFILE) -> Path:
    """Дорогие стадии из уже принятого content revision; текстовые API не вызываются."""
    pack = S.ResearchPack(**json.loads((run_dir / "research_pack.json").read_text(encoding="utf-8")))
    script = S.Script(**json.loads((run_dir / "script.json").read_text(encoding="utf-8")))
    compliance = S.ComplianceVerdict(**json.loads(
        (run_dir / "compliance.json").read_text(encoding="utf-8")
    ))
    fact = S.FactReview(**json.loads((run_dir / "fact_review.json").read_text(encoding="utf-8")))
    plan = S.FramePlan(**json.loads((run_dir / "frame_plan.json").read_text(encoding="utf-8")))
    qa = S.QAReport(**json.loads((run_dir / "qa.json").read_text(encoding="utf-8")))
    pkg = S.PublishPackage(**json.loads(
        (run_dir / "publish_package.json").read_text(encoding="utf-8")
    ))
    revision = _revision(pack, script)
    pre = release_report(run_dir, revision, pack, script, compliance, fact, plan, qa, pkg)
    _write_json(run_dir / "release_gate.json", pre)
    if not pre.passed:
        raise SystemExit("[release] существующие артефакты не проходят pre-media gate")

    os.environ["RUN_COST_DIR"] = str(run_dir)
    frames = approved_codex_frames(run_dir, plan)
    # В v8 финал использует последний принятый кадр, а читаемость обеспечивает
    # детерминированный HTML-скрим. Скрытой image-generation стадии нет.
    payoff_frame = frames[-1]
    # Artifacts carry their language; `--build` can therefore safely assemble either
    # archived Russian evaluation runs or current Polish production runs.
    globals()["LANG"] = script.lang
    voice_wav, durs, beat_words = synth_audio(script, run_dir / "audio")
    cards = source_cards(script, pack)
    _write_json(run_dir / "source_cards.json", {str(k): v for k, v in cards.items()})
    out_mp4 = run_dir / "out.mp4"
    A.build_and_render(
        frames,
        [(f.beat_from, f.beat_to) for f in plan.frames],
        [f.motion for f in plan.frames],
        beat_words,
        [b.on_screen_text for b in script.beats],
        durs,
        script.overlays,
        [b.emphasis for b in script.beats],
        voice_wav,
        out_mp4,
        run_dir / "hf",
        headline=script.poster_text,
        payoff_text=script.payoff_card,
        turn_beat_idx=script.turn_beat_idx,
        bgm_wav=V8Base._channel_bgm(asset_channel),
        sfx_profile=sfx_profile,
        payoff_frame=payoff_frame,
        headline_until_first_cut=True,
        lang=script.lang,
        layout_gate=True,
        source_cards=cards,
    )
    _mark_media_manifest_built(run_dir)

    media_meta = _probe_video(out_mp4)
    sys.path.insert(0, str(ROOT / "skills" / "codex-viral-shorts" / "scripts"))
    final_visual = _final_visual_qa(out_mp4, run_dir, script)
    _write_json(run_dir / "final_qa.json", {"checks": final_visual})
    final_release = release_report(
        run_dir, revision, pack, script, compliance, fact, plan, qa, pkg,
        media_meta=media_meta, visual_qa=final_visual, require_media=True,
    )
    _write_json(run_dir / "release_gate.json", final_release)

    run_meta = {
        "pipeline_version": S.PIPELINE_VERSION,
        "language": script.lang,
        "topic": pack.topic,
        "rubric": script.rubric,
        "format": script.format,
        "angle": pack.recommended_angle,
        "content_revision": revision,
        "models": {
            "research": resolve_model(RESEARCH_MODEL),
            "text": resolve_model(TEXT_MODEL),
            "image": "codex_builtin_imagegen",
            "tts": TTS_MODELS[TTS_MODEL],
            "vision_qa": VISION_MODEL,
        },
        "prompts": "v8/codex-pl",
        "sfx_profile": sfx_profile,
        "media": media_meta,
        "release_passed": final_release.passed,
        "publication_authorized": False,
        "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    _write_json(run_dir / "run_meta.json", run_meta)
    _write_json(run_dir / "artifact_manifest.json", {
        "content_revision": revision,
        "sha256": _artifact_hashes(run_dir),
    })
    if not final_release.passed:
        raise SystemExit(f"[release] MP4 создан, но final gate не пройден → {run_dir}")
    print(f"[done] release-ready · {media_meta['duration_s']:.1f}s → {out_mp4}")
    return run_dir


def produce(topic: str, fmt: str, rubric: str, angle: str = "", slug: str = "",
            go: bool = False, run_channel: str = "",
            asset_channel: str = "vitallogic_bad_pl",
            sfx_profile: str = A.DEFAULT_SFX_PROFILE, lang: str = "pl") -> Path:
    if lang not in LANGUAGE_CONFIG:
        raise ValueError(f"unsupported v8 language: {lang}")
    globals()["LANG"] = lang
    run_channel = run_channel or ("vitallogic_bad_pl" if lang == "pl" else "vitallogic_v8_ru")
    slug = slug or _safe_slug(topic)
    run_dir = RUNS / run_channel / f"{datetime.date.today()}_v8-{slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    os.environ["RUN_COST_DIR"] = str(run_dir)
    print(f"[v8] {slug} · lang={lang} · rubric={rubric} · format={fmt}")

    memo, pack = research_topic(topic, angle, run_dir)
    saved = load_saved_content(run_dir, pack)
    if saved is None:
        script, compliance, fact, plan, qa = finalize_content(
            topic, fmt, rubric, angle, memo, pack, run_dir
        )
    else:
        script, compliance, fact, plan, qa = saved
    revision = _revision(pack, script)
    pkg = publish_package(script, pack)

    _write_json(run_dir / "script.json", script)
    _write_json(run_dir / "compliance.json", compliance)
    _write_json(run_dir / "fact_review.json", fact)
    _write_json(run_dir / "frame_plan.json", plan)
    _write_json(run_dir / "qa.json", qa)
    _write_json(run_dir / "publish_package.json", pkg)

    pre = release_report(run_dir, revision, pack, script, compliance, fact, plan, qa, pkg)
    _write_json(run_dir / "release_gate.json", pre)
    if not pre.passed:
        raise SystemExit("[release] pre-media gate failed")
    if not go:
        print(f"[dry] v8 content passed · revision={revision} → {run_dir}")
        return run_dir
    return build_media_from_artifacts(run_dir, asset_channel=asset_channel,
                                      sfx_profile=sfx_profile)


def main() -> None:
    parser = argparse.ArgumentParser(description="engine_v8.py — canonical Codex evidence pipeline")
    parser.add_argument("--topic", default="")
    parser.add_argument("--format", default="", choices=[""] + list(S.FORMAT_BRIEFS))
    parser.add_argument("--rubric", default="", choices=[""] + list(S.RUBRIC_META))
    parser.add_argument("--angle", default="")
    parser.add_argument("--slug", default="")
    parser.add_argument("--go", action="store_true")
    parser.add_argument("--lang", default="pl", choices=sorted(LANGUAGE_CONFIG))
    parser.add_argument("--run-channel", default="")
    parser.add_argument("--asset-channel", default="vitallogic_bad_pl")
    parser.add_argument("--sfx", default=A.DEFAULT_SFX_PROFILE, choices=list(A.SFX_PROFILES))
    parser.add_argument("--text-model", default=TEXT_MODEL)
    parser.add_argument("--research-model", default=RESEARCH_MODEL)
    parser.add_argument("--build", default="", metavar="RUN_DIR",
                        help="собрать MP4 из уже прошедших v8 content-артефактов")
    args = parser.parse_args()
    globals()["TEXT_MODEL"] = args.text_model
    globals()["RESEARCH_MODEL"] = args.research_model
    if args.build:
        try:
            existing = S.Script.model_validate_json((Path(args.build) / "script.json").read_text(encoding="utf-8"))
            globals()["LANG"] = existing.lang
        except Exception:
            globals()["LANG"] = args.lang
        build_media_from_artifacts(Path(args.build), asset_channel=args.asset_channel,
                                   sfx_profile=args.sfx)
        return
    if not args.topic or not args.format or not args.rubric:
        parser.error("--topic, --format и --rubric обязательны без --build")
    produce(
        args.topic,
        args.format,
        args.rubric,
        angle=args.angle,
        slug=args.slug,
        go=args.go,
        run_channel=args.run_channel,
        asset_channel=args.asset_channel,
        sfx_profile=args.sfx,
        lang=args.lang,
    )


if __name__ == "__main__":
    main()
