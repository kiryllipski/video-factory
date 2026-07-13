#!/usr/bin/env python3
"""
analytics_report.py — еженедельный отчёт по CSV-экспорту YouTube Studio (v2, growth_plan §3/этап 5).

Вход: папка экспорта «Контент YYYY-MM-DD_YYYY-MM-DD <канал>» (внутри «Данные из таблицы.csv»)
или путь к самому CSV. Выход: markdown-отчёт (stdout или --out).

Что считает:
  - сводка: роликов / просмотров / медиана / среднее / доля топ-5;
  - корреляция views↔stayed-to-watch (диагноз «показы vs retention», см. growth_plan H1);
  - таблица по роликам: views, stayed%, avg%viewed, лайки%, подп./1k;
  - KPI-вердикты v2 (stayed ≥60%, лайки ≥5%, подп. ≥5/1k) — сколько роликов проходят;
  - доля шаблона «błąd» в заголовках (правило ротации: ≤30%);
  - если найден publish_log.jsonl — колонка версии пайплайна (v1/v2) и медианы по версиям.

    python3 orchestration/analytics_report.py "~/Downloads/Контент ... VitalLogic" \
        [--out orchestration/research/58_report.md]

Метод разбора и выводы недели 1 — orchestration/research/53_vitallogic_analytics_week1.md;
план роста — autopilot_factory/channels/vitallogic_bad_pl/growth_plan_2026-07-13.md.
"""
from __future__ import annotations
import csv
import json
import math
import argparse
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISH_LOG = ROOT / "autopilot_factory" / "publishers" / "publish_log.jsonl"

# KPI v2 на ролик (growth_plan этап 0, п.3)
KPI_STAYED = 60.0      # % оставшихся смотреть (свайп-тест)
KPI_LIKES_PCT = 5.0    # лайки / просмотры
KPI_SUBS_PER_1K = 5.0  # подписки на 1000 просмотров
TEMPLATE_BLAD_MAX_SHARE = 0.30  # «Ten błąd» ≤30% заголовков (ротация, этап 1 п.7)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_rows(csv_path: Path) -> list[dict]:
    rows = []
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cid = (row.get("Content") or "").strip()
            if not cid or cid == "Total":
                continue
            rows.append({
                "id": cid,
                "title": (row.get("Video title") or "").strip(),
                "published": (row.get("Video publish time") or "").strip(),
                "dur": _f(row.get("Duration")),
                "views": int(_f(row.get("Views")) or 0),
                "subs_gained": _f(row.get("Subscribers gained")) or 0.0,
                "likes": _f(row.get("Likes")) or 0.0,
                "shares": _f(row.get("Shares")) or 0.0,
                "engaged": _f(row.get("Engaged views")),
                "avg_viewed": _f(row.get("Average percentage viewed (%)")),
                "stayed": _f(row.get("Stayed to watch (%)")),
            })
    rows.sort(key=lambda r: -r["views"])
    return rows


def corr(pairs: list[tuple]) -> float:
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    if len(pairs) < 3:
        return float("nan")
    xs, ys = [a for a, _ in pairs], [b for _, b in pairs]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    cov = sum((a - mx) * (b - my) for a, b in pairs)
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return cov / den if den else float("nan")


def load_publish_log() -> dict:
    """video_id → {pipeline_version, title_template} из publish_log.jsonl (если ведётся)."""
    out = {}
    if PUBLISH_LOG.exists():
        for line in PUBLISH_LOG.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                out[e.get("video_id", "")] = {
                    "version": e.get("pipeline_version", "") or "1.x",
                    "template": e.get("title_template", ""),
                }
            except json.JSONDecodeError:
                continue
    return out


def build_report(rows: list[dict], source: str) -> str:
    views = [r["views"] for r in rows]
    total_v = sum(views)
    log = load_publish_log()
    lines = []
    lines.append(f"# Отчёт по каналу — {source}")
    lines.append("")
    med = statistics.median(views) if views else 0
    top5 = sum(sorted(views, reverse=True)[:5])
    lines.append(f"**Роликов:** {len(rows)} · **Просмотров:** {total_v} · "
                 f"**Медиана:** {med:.0f} · **Среднее:** {statistics.mean(views):.0f} · "
                 f"**Доля топ-5:** {top5 / total_v * 100:.0f}%" if total_v else "Нет просмотров.")
    c_stayed = corr([(r["views"], r["stayed"]) for r in rows])
    c_avg = corr([(r["views"], r["avg_viewed"]) for r in rows])
    lines.append("")
    lines.append(f"Корреляция views↔stayed: **{c_stayed:.2f}**; views↔avg%viewed: **{c_avg:.2f}**. "
                 + ("Близко к нулю → узкое место — ПОКАЗЫ (упаковка/темы), не retention (H1)."
                    if abs(c_stayed) < 0.35 else
                    "Заметная связь → retention начал влиять на дистрибуцию — рычаг сместился."))
    lines.append("")

    # KPI-вердикты
    n = len(rows) or 1
    ok_stayed = sum(1 for r in rows if (r["stayed"] or 0) >= KPI_STAYED)
    ok_likes = sum(1 for r in rows if r["views"] and r["likes"] / r["views"] * 100 >= KPI_LIKES_PCT)
    ok_subs = sum(1 for r in rows if r["views"] and r["subs_gained"] / r["views"] * 1000 >= KPI_SUBS_PER_1K)
    lines.append(f"## KPI v2 (growth_plan этап 0)")
    lines.append(f"- stayed ≥{KPI_STAYED:.0f}%: **{ok_stayed}/{len(rows)}**")
    lines.append(f"- лайки ≥{KPI_LIKES_PCT:.0f}%: **{ok_likes}/{len(rows)}**")
    lines.append(f"- подписки ≥{KPI_SUBS_PER_1K:.0f}/1k: **{ok_subs}/{len(rows)}**")
    lines.append("")

    # Ротация шаблона «błąd»
    blad = [r for r in rows if "błąd" in r["title"].lower() or "błędy" in r["title"].lower()]
    share = len(blad) / n
    lines.append(f"## Ротация заголовков")
    lines.append(f"Шаблон «błąd» в {len(blad)}/{len(rows)} заголовков (**{share * 100:.0f}%**) — "
                 + ("в норме (≤30%)." if share <= TEMPLATE_BLAD_MAX_SHARE
                    else f"ПРЕВЫШЕН лимит {TEMPLATE_BLAD_MAX_SHARE * 100:.0f}% — разнообразь шаблоны (этап 1 п.7)."))
    lines.append("")

    # Медианы по версии пайплайна (если у роликов есть журнал)
    if log:
        by_ver: dict[str, list[int]] = {}
        for r in rows:
            ver = log.get(r["id"], {}).get("version", "")
            if ver:
                by_ver.setdefault(ver, []).append(r["views"])
        if by_ver:
            lines.append("## Сравнение версий пайплайна")
            for ver, vs in sorted(by_ver.items()):
                lines.append(f"- v{ver}: {len(vs)} роликов, медиана {statistics.median(vs):.0f} просм.")
            lines.append("")

    # Таблица по роликам
    lines.append("## Ролики (по просмотрам)")
    lines.append("| Views | Stayed% | Avg% | Лайки% | Подп/1k | Vers | Заголовок |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        v = r["views"] or 0
        likes_pct = f"{r['likes'] / v * 100:.1f}" if v else "-"
        subs1k = f"{r['subs_gained'] / v * 1000:.1f}" if v else "-"
        stayed = f"{r['stayed']:.0f}" if r["stayed"] is not None else "-"
        avgv = f"{r['avg_viewed']:.0f}" if r["avg_viewed"] is not None else "-"
        ver = log.get(r["id"], {}).get("version", "") or "-"
        lines.append(f"| {v} | {stayed} | {avgv} | {likes_pct} | {subs1k} | {ver} | {r['title'][:70]} |")
    lines.append("")

    # Протокол аутлаера (этап 5 п.17)
    outliers = [r for r in rows if med and r["views"] >= 3 * med and r["views"] >= 300]
    lines.append("## Протокол аутлаера (≥3× медианы)")
    if outliers:
        for r in outliers:
            lines.append(f"- **{r['title'][:70]}** — {r['views']} просм. → в течение 2–3 дней "
                         f"выпустить 2–3 вариации темы (другая грань / часть 2 / ответ на комментарии).")
    else:
        lines.append("- Аутлаеров нет — продолжать по плану, наращивать долю массовых симптом-тем.")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Еженедельный отчёт по CSV-экспорту YouTube Studio")
    ap.add_argument("export", help="папка экспорта Studio или путь к «Данные из таблицы.csv»")
    ap.add_argument("--out", default=None, help="куда сохранить markdown (по умолчанию stdout)")
    args = ap.parse_args()
    p = Path(args.export).expanduser()
    csv_path = p if p.is_file() else p / "Данные из таблицы.csv"
    if not csv_path.exists():
        raise SystemExit(f"[analytics] не найден CSV: {csv_path}")
    rows = load_rows(csv_path)
    report = build_report(rows, source=p.name)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"[analytics] отчёт сохранён: {out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
