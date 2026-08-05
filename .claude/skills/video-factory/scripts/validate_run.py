#!/usr/bin/env python3
"""validate_run.py — валидирует артефакты прогона ДО любых трат на медиа.

Проверяет, что script.json / frame_plan.json (и, если есть, compliance.json) соответствуют
Pydantic-схемам из autopilot_factory/schemas.py, плюс несколько кросс-проверок, которых нет в схемах
(кадров = битов, порядок, суммарный хронометраж). Ничего не генерирует и не тратит бюджет.

    python3 scripts/validate_run.py <run_dir>

Код возврата 0 = всё зелёно; 1 = есть ошибки (перечислены).
"""
from __future__ import annotations
import re
import sys
import json
import argparse
from pathlib import Path

from _common import find_project_root, wire_paths

ROOT = find_project_root()
wire_paths(ROOT)
import schemas  # noqa: E402
from pydantic import ValidationError  # noqa: E402

# Стоп-слова комплаенса БАД/wellness PL/EU (research/02, studio_context §7) — запрещены ВЕЗДЕ:
# хук/озвучка/on_screen_text/CTA/постер. Ловим и словоформы (leczyć, chorobie, bólu, terapii…).
_PL_STOPWORDS = re.compile(
    # lecz\w+ (не голое «lecz» — это союз «но»), wyleczy/uleczy, zapobiega*, chorob*/chorób,
    # ból/bólu/bóle/boli/bolesny, terapia/terapii/terapeutyczny
    r"\b((wy|u)?lecz\w+|zapobiega\w*|chorob\w*|chorób|ból\w*|ból|bol[ei]\w*|terapi\w*|terapeut\w*)\b",
    re.IGNORECASE,
)


def _pl_stopword_hits(script) -> list[str]:
    """Сканирует все текстовые поля сценария на стоп-слова. Возвращает список 'поле: слово'."""
    hits = []
    fields = [("hook", script.hook), ("cta", script.cta),
              ("poster_text", getattr(script, "poster_text", "")),
              ("cta_plate", getattr(script, "cta_plate", ""))]
    for i, b in enumerate(script.beats):
        fields.append((f"beats[{i}].voiceover", b.voiceover))
        fields.append((f"beats[{i}].on_screen_text", b.on_screen_text))
    for name, text in fields:
        for m in _PL_STOPWORDS.finditer(text or ""):
            hits.append(f"{name}: «{m.group(0)}»")
    return hits


def _load(run_dir: Path, name: str) -> dict:
    p = run_dir / name
    if not p.exists():
        raise FileNotFoundError(name)
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Валидация прогона video-factory")
    ap.add_argument("run_dir")
    args = ap.parse_args()
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        print(f"[fail] нет папки прогона: {run_dir}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    # --- script.json (обязателен) ---
    script = None
    try:
        script = schemas.Script(**_load(run_dir, "script.json"))
        beats_total = sum(b.dur_s for b in script.beats)
        if abs(beats_total - script.total_dur_s) > max(4.0, 0.15 * script.total_dur_s):
            errors.append(f"сумма dur_s битов ({beats_total:.1f}с) далека от total_dur_s "
                          f"({script.total_dur_s:.1f}с) — расхождение >15%")
        # --- v2 (growth_plan_2026-07-13): постер + скорость хука ---
        poster = (getattr(script, "poster_text", "") or "").strip()
        # слова = токены с буквами/цифрами (звёздочки-акценты и голая пунктуация не в счёт)
        _words = lambda s: [w for w in s.replace("*", " ").split() if any(c.isalnum() for c in w)]
        poster_words = len(_words(poster))
        if not poster:
            warnings.append("poster_text пуст — постер-заголовок первого кадра возьмётся из "
                            "beats[0].on_screen_text (для новых прогонов пиши poster_text: 3–6 слов)")
        elif poster_words > 6:
            warnings.append(f"poster_text длиннее 6 слов ({poster_words}) — на постере "
                            f"первого кадра должен читаться за долю секунды")
        # --- v3 (factory_audit_2026-07-15): упаковка первых 2 секунд + финальная плашка ---
        if poster and poster_words > 4:
            warnings.append(f"v3: poster_text {poster_words} слов — таргет ≤4 (крупнее шрифт = "
                            f"читаемость в ленте); сожми до удара")
        if poster and "*" not in poster:
            warnings.append("v3: в poster_text нет акцент-слова (*słowo*) — выдели самое "
                            "цепляющее слово, сборка подсветит его жёлтым")
        cta_plate = (getattr(script, "cta_plate", "") or "").strip()
        if not cta_plate:
            warnings.append("v3: cta_plate пуст — финальная плашка-вопрос (петля к постеру, "
                            "толчок к комменту) не будет отрендерена")
        elif len(_words(cta_plate)) > 5:
            warnings.append(f"v3: cta_plate длиннее 5 слов — должен читаться мгновенно")
        if script.beats and script.beats[0].dur_s > 2.2:
            warnings.append(f"первый бит {script.beats[0].dur_s:.1f}с — v3: хук называет симптом "
                            f"за ≤1.5–2.2с; сократи voiceover первого бита")
        if not (22.0 <= script.total_dur_s <= 34.0):
            warnings.append(f"v3: total_dur_s {script.total_dur_s:.0f}с вне таргета 22–32с "
                            f"(пик completion Shorts 15–30с; edu допустим до ~34с при явном payoff)")
    except FileNotFoundError:
        errors.append("script.json не найден")
    except (ValidationError, json.JSONDecodeError) as e:
        errors.append(f"script.json не проходит схему Script: {e}")

    # --- compliance.json (опционален; если есть — берём cleaned_script для сверки с планом) ---
    effective_script = script
    if (run_dir / "compliance.json").exists():
        try:
            verdict = schemas.ComplianceVerdict(**_load(run_dir, "compliance.json"))
            effective_script = verdict.cleaned_script
        except (ValidationError, json.JSONDecodeError) as e:
            errors.append(f"compliance.json не проходит схему ComplianceVerdict: {e}")

    # --- frame_plan.json (обязателен) ---
    try:
        plan = schemas.FramePlan(**_load(run_dir, "frame_plan.json"))
        if effective_script is not None:
            nb, nf = len(effective_script.beats), len(plan.frames)
            if nb != nf:
                errors.append(f"кадров ({nf}) ≠ битов ({nb}) — нужен ровно один кадр на бит")
    except FileNotFoundError:
        errors.append("frame_plan.json не найден")
    except (ValidationError, json.JSONDecodeError) as e:
        errors.append(f"frame_plan.json не проходит схему FramePlan: {e}")

    # --- v2: стоп-слова комплаенса для PL-каналов (жёсткое правило studio_context §7) ---
    if effective_script is not None and effective_script.lang == "pl":
        hits = _pl_stopword_hits(effective_script)
        if hits:
            errors.append("PL стоп-слова комплаенса (leczy/zapobiega/choroba/ból/terapia) в тексте: "
                          + "; ".join(hits))

    if warnings:
        print("[warn] рекомендации (не блокируют):")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print("[fail] найдены проблемы:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"[ok] {run_dir.name}: script.json + frame_plan.json валидны, кадров = битов. Готово к build_media.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
