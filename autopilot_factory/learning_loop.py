#!/usr/bin/env python3
"""learning_loop.py — обучающий контур фабрики: гипотеза → метрика → вывод → следующий сценарий.

ПРИНЦИП: скрипт СОБИРАЕТ и СОЕДИНЯЕТ факты. Выводы делает Claude, читая `table`.
Не зашивай сюда аналитика — статистические пороги в коде устаревают молча, а Claude видит
контекст (что менялось в пайплайне, что происходило на канале) и рассуждает на нём.

Данные (append-only JSONL, git-friendly):
    learning/experiments.jsonl   — что за ролик и чем отличается от предыдущих (рычаги)
    learning/metrics.jsonl       — снапшоты метрик из YouTube Analytics API
    learning/studio_metrics.jsonl — ручные выгрузки Studio (Impressions / Stayed to watch)

Команды:
    register  --channel X --run <dir>      один прогон → experiments.jsonl
    backfill  --channel X                  вся история (архив iCloud + publish_log) → experiments.jsonl
    collect   --channel X                  YouTube Analytics API → metrics.jsonl (снапшот на сегодня)
    table     --channel X [--out f.md]     join experiments × metrics → таблица для анализа

Скоупы: `yt-analytics.readonly` уже выдан токену vitallogic_bad_pl — re-auth не нужен.
"""
from __future__ import annotations

import os
import sys
import json
import argparse
import datetime as _dt
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent          # autopilot_factory/
LEARNING = HERE / "learning"
PUBLISH_LOG = HERE / "publishers" / "publish_log.jsonl"
TOKENS_DIR = HERE / "tokens"

DELIVERY_ROOT = Path(os.environ.get(
    "VIDEO_DELIVERY_ROOT",
    "/Users/kirillipski/Library/Mobile Documents/com~apple~CloudDocs/external storage/video/0.5",
))


# ───────────────────────── утилиты ─────────────────────────

def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(p: Path) -> Optional[dict]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_jsonl(p: Path) -> List[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _append_jsonl(p: Path, rows: List[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _parse_iso(s: str) -> Optional[_dt.datetime]:
    if not s:
        return None
    try:
        return _dt.datetime.strptime(s.replace("+00:00", "Z"), "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=_dt.timezone.utc)
    except ValueError:
        return None


def _find_run_dir(channel: str, run: str) -> Optional[Path]:
    """Прогон живёт локально до загрузки, после — целиком в iCloud."""
    for cand in (HERE / "runs" / channel / run, DELIVERY_ROOT / channel / run):
        if cand.is_dir():
            return cand
    return None


# ───────────────────────── рычаги (levers) ─────────────────────────

def extract_levers(run_dir: Path) -> Dict[str, Any]:
    """Всё, что отличает этот ролик от других и потенциально влияет на результат.

    Читается механически из артефактов прогона — владельцу и Claude ничего не нужно
    вводить руками. Отсутствующий файл → просто пропущенные поля, не ошибка.
    """
    lv: Dict[str, Any] = {}

    script = _read_json(run_dir / "script.json") or {}
    if script:
        beats = script.get("beats") or []
        hook = (script.get("hook") or "").strip()
        lv.update({
            "lang": script.get("lang"),
            "hook": hook,
            "hook_words": len(hook.split()) if hook else None,
            "beats_count": len(beats) or None,
            "total_dur_s": script.get("total_dur_s"),
            "poster_text": (script.get("poster_text") or "").strip() or None,
            "cta_plate": (script.get("cta_plate") or "").strip() or None,
            "avg_beat_s": round(sum(b.get("dur_s", 0) for b in beats) / len(beats), 2) if beats else None,
        })

    fp = _read_json(run_dir / "frame_plan.json") or {}
    if fp:
        frames = fp.get("frames") or []
        motions = [f.get("motion") for f in frames if f.get("motion")]
        lv.update({
            "grade": fp.get("grade"),
            "light": fp.get("light"),
            "lens": fp.get("lens"),
            "frames_count": len(frames) or None,
            "motions_distinct": sorted(set(motions)) or None,
        })

    pkg = _read_json(run_dir / "publish_package.json") or {}
    if pkg:
        title = pkg.get("title") or ""
        lv.update({
            "title": title,
            "title_len": len(title) or None,
            "title_template": pkg.get("title_template") or None,
            "hashtags_count": len(pkg.get("hashtags") or []) or None,
            "has_pinned_comment": bool(pkg.get("pinned_comment")),
        })

    meta = _read_json(run_dir / "run_meta.json") or {}
    if meta:
        lv["pipeline_version"] = meta.get("pipeline_version")
        lv["built_at"] = meta.get("built_at")

    cost = _read_json(run_dir / "cost.json") or {}
    if cost:
        lv["cost_usd"] = round(cost.get("total_usd", 0), 4) or None

    qa = _read_json(run_dir / "qa.json") or {}
    if qa:
        lv["qa_passed"] = qa.get("passed")

    fqa = _read_json(run_dir / "frame_qa.json")
    if isinstance(fqa, dict):
        lv["frame_qa_retries"] = fqa.get("retries") or fqa.get("total_retries")

    return {k: v for k, v in lv.items() if v is not None}


def build_experiment(channel: str, run: str, run_dir: Path,
                     pub: Optional[dict] = None,
                     hypothesis: str = "") -> Dict[str, Any]:
    post = _read_json(run_dir / "post_result.json") or {}
    pub = pub or {}
    return {
        "run": run,
        "channel": channel,
        "video_id": post.get("video_id") or pub.get("video_id") or None,
        "published_at": post.get("publish_at") or pub.get("published_at_or_scheduled") or None,
        "registered_at": _now_iso(),
        "hypothesis": hypothesis or None,
        "levers": extract_levers(run_dir),
    }


# ───────────────────────── команды ─────────────────────────

def cmd_register(args) -> None:
    run_dir = Path(args.run) if args.run else None
    if run_dir and not run_dir.is_dir():
        run_dir = _find_run_dir(args.channel, args.run)
    if not run_dir or not run_dir.is_dir():
        sys.exit(f"Прогон не найден: {args.run}")

    run = run_dir.name
    path = LEARNING / "experiments.jsonl"
    known = {r.get("run") for r in _read_jsonl(path)}
    if run in known and not args.force:
        print(f"[skip] {run} уже зарегистрирован (--force чтобы перезаписать строкой поверх)")
        return

    exp = build_experiment(args.channel, run, run_dir, hypothesis=args.hypothesis or "")
    _append_jsonl(path, [exp])
    print(f"[ok] {run} → experiments.jsonl (video_id={exp['video_id']}, "
          f"рычагов: {len(exp['levers'])})")


def cmd_backfill(args) -> None:
    """Восстанавливает историю: publish_log.jsonl даёт что опубликовано, архив iCloud — чем."""
    path = LEARNING / "experiments.jsonl"
    # Пропускаем только те, что уже знают свой video_id. Прогон, зарегистрированный ДО загрузки
    # (`register` на готовом, но не опубликованном), имеет video_id=None — его нужно
    # перерегистрировать, когда он опубликуется, иначе он навсегда останется без метрик.
    known = {r.get("run") for r in _read_jsonl(path) if r.get("video_id")}

    pubs = [p for p in _read_jsonl(PUBLISH_LOG) if p.get("channel") == args.channel]
    by_run: Dict[str, dict] = {}
    for p in pubs:                      # последняя запись по прогону выигрывает
        if p.get("run"):
            by_run[p["run"]] = p

    rows, missing = [], []
    for run, pub in sorted(by_run.items()):
        if run in known:
            continue
        run_dir = _find_run_dir(args.channel, run)
        if not run_dir:
            missing.append(run)
            continue
        rows.append(build_experiment(args.channel, run, run_dir, pub=pub))

    if rows:
        _append_jsonl(path, rows)
    print(f"[ok] добавлено {len(rows)} экспериментов, пропущено (уже есть) "
          f"{len(by_run) - len(rows) - len(missing)}")
    if missing:
        print(f"[warn] прогон не найден ни локально, ни в архиве ({len(missing)}): "
              f"{', '.join(missing[:5])}{'…' if len(missing) > 5 else ''}")


def _analytics_service(channel: str):
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit("Нужны библиотеки: pip install --user "
                 "google-api-python-client google-auth-oauthlib google-auth-httplib2")
    tp = TOKENS_DIR / f"{channel}.json"
    if not tp.exists():
        sys.exit(f"Нет токена для канала '{channel}'")
    creds = Credentials.from_authorized_user_file(str(tp), scopes=None)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        tp.write_text(creds.to_json(), encoding="utf-8")
    return (build("youtubeAnalytics", "v2", credentials=creds),
            build("youtube", "v3", credentials=creds))


METRICS = ["views", "likes", "comments", "shares", "subscribersGained",
           "estimatedMinutesWatched", "averageViewDuration", "averageViewPercentage"]


def cmd_collect(args) -> None:
    yta, yt = _analytics_service(args.channel)

    exps = [e for e in _read_jsonl(LEARNING / "experiments.jsonl")
            if e.get("channel") == args.channel and e.get("video_id")]
    if not exps:
        sys.exit("Нет зарегистрированных экспериментов с video_id — сначала `backfill`")

    # только уже вышедшие: у запланированных метрик нет по определению
    now = _dt.datetime.now(_dt.timezone.utc)
    live = []
    for e in exps:
        pub = _parse_iso(e.get("published_at") or "")
        if pub and pub <= now:
            live.append((e["video_id"], pub))
    if not live:
        sys.exit("Ни один ролик ещё не вышел — метрики собирать не с чего")

    pub_by_id = {v: p for v, p in live}
    ids = list(pub_by_id)                       # dedupe: append-only даёт повторы по прогону
    start = min(pub_by_id.values()).strftime("%Y-%m-%d")
    end = now.strftime("%Y-%m-%d")

    rows: List[dict] = []
    snapshot = _now_iso()
    for i in range(0, len(ids), 200):          # filters ограничен по длине — режем пачками
        chunk = ids[i:i + 200]
        resp = yta.reports().query(
            ids="channel==MINE", startDate=start, endDate=end,
            metrics=",".join(METRICS), dimensions="video",
            filters="video==" + ",".join(chunk), maxResults=200,
        ).execute()
        cols = [h["name"] for h in resp.get("columnHeaders", [])]
        for row in resp.get("rows", []) or []:
            rec = dict(zip(cols, row))
            vid = rec.get("video")
            pub = pub_by_id.get(vid)
            hours_live = round((now - pub).total_seconds() / 3600, 1) if pub else None
            views = rec.get("views") or 0
            out = {
                "video_id": vid,
                "channel": args.channel,
                "snapshot_at": snapshot,
                "hours_live": hours_live,
                "views": views,
                "likes": rec.get("likes"),
                "comments": rec.get("comments"),
                "shares": rec.get("shares"),
                "subscribers_gained": rec.get("subscribersGained"),
                "watch_minutes": rec.get("estimatedMinutesWatched"),
                "avg_view_duration_s": rec.get("averageViewDuration"),
                "avg_view_pct": rec.get("averageViewPercentage"),
            }
            # сырые просмотры несравнимы у роликов разного возраста — нормируем
            if hours_live and hours_live > 0:
                out["views_per_day"] = round(views / (hours_live / 24), 2)
            rows.append(out)

    _append_jsonl(LEARNING / "metrics.jsonl", rows)
    print(f"[ok] снапшот {snapshot}: метрики по {len(rows)} роликам → metrics.jsonl")
    if len(rows) < len(ids):
        print(f"[warn] {len(ids) - len(rows)} роликов не вернули данных "
              f"(слишком свежие или приватные)")


def cmd_table(args) -> None:
    """Соединяет рычаги с последними метриками. Это вход для рассуждения Claude, не вывод."""
    # append-only: у прогона может быть несколько строк (перерегистрация после публикации,
    # --force). Берём последнюю по registered_at.
    by_run: Dict[str, dict] = {}
    for e in _read_jsonl(LEARNING / "experiments.jsonl"):
        if e.get("channel") != args.channel or not e.get("run"):
            continue
        prev = by_run.get(e["run"])
        if prev is None or (e.get("registered_at") or "") >= (prev.get("registered_at") or ""):
            by_run[e["run"]] = e
    exps = list(by_run.values())

    metrics = [m for m in _read_jsonl(LEARNING / "metrics.jsonl")
               if m.get("channel") == args.channel]

    latest: Dict[str, dict] = {}
    for m in metrics:                          # последний снапшот на ролик
        vid = m.get("video_id")
        if not vid:
            continue
        if vid not in latest or (m.get("snapshot_at") or "") > (latest[vid].get("snapshot_at") or ""):
            latest[vid] = m

    joined = []
    for e in exps:
        vid = e.get("video_id")
        m = latest.get(vid, {})
        lv = e.get("levers", {})
        joined.append({
            "run": e.get("run"),
            "published": (e.get("published_at") or "")[:10],
            "hours_live": m.get("hours_live"),
            "views": m.get("views"),
            "vpd": m.get("views_per_day"),
            "avg_pct": m.get("avg_view_pct"),
            "likes": m.get("likes"),
            "subs": m.get("subscribers_gained"),
            "template": lv.get("title_template"),
            "dur_s": lv.get("total_dur_s"),
            "beats": lv.get("beats_count"),
            "pipeline": lv.get("pipeline_version"),
            "cost": lv.get("cost_usd"),
            "hook": (lv.get("hook") or "")[:60],
        })
    joined.sort(key=lambda r: (r["vpd"] is None, -(r["vpd"] or 0)))

    cols = ["run", "published", "hours_live", "views", "vpd", "avg_pct", "likes", "subs",
            "template", "dur_s", "beats", "pipeline", "cost", "hook"]
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "|".join("---" for _ in cols) + "|"]
    for r in joined:
        lines.append("| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |")

    have = [r for r in joined if r["vpd"] is not None]
    header = (f"# Таблица экспериментов — {args.channel}\n\n"
              f"Собрано: {_now_iso()}. Всего роликов: {len(joined)}, с метриками: {len(have)}.\n"
              f"Сортировка по views_per_day (vpd) — сырые просмотры несравнимы у роликов "
              f"разного возраста.\n\n")
    text = header + "\n".join(lines) + "\n"

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[ok] → {args.out}")
    else:
        print(text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("register", help="зарегистрировать один прогон")
    p.add_argument("--channel", required=True)
    p.add_argument("--run", required=True, help="путь к прогону или его имя")
    p.add_argument("--hypothesis", default="", help="что этим роликом проверяем")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_register)

    p = sub.add_parser("backfill", help="восстановить историю из publish_log + архива")
    p.add_argument("--channel", required=True)
    p.set_defaults(func=cmd_backfill)

    p = sub.add_parser("collect", help="снять метрики через YouTube Analytics API")
    p.add_argument("--channel", required=True)
    p.set_defaults(func=cmd_collect)

    p = sub.add_parser("table", help="join рычагов и метрик для анализа")
    p.add_argument("--channel", required=True)
    p.add_argument("--out", default="")
    p.set_defaults(func=cmd_table)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
