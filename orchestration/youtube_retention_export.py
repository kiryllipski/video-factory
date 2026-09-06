#!/usr/bin/env python3
"""Export YouTube retention curves for age-normalized strongest/weakest videos.

Read-only YouTube Analytics API export. Uses the latest local learning snapshot
to choose videos by views_per_day, then fetches the 100-point audience-retention
report one video at a time.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autopilot_factory.learning_loop import _analytics_service, _read_jsonl, _parse_iso


LEARNING = ROOT / "autopilot_factory" / "learning"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def latest_metrics(channel: str) -> dict[str, dict]:
    rows = [r for r in _read_jsonl(LEARNING / "metrics.jsonl")
            if r.get("channel") == channel and r.get("video_id")]
    latest: dict[str, dict] = {}
    for row in rows:
        vid = row["video_id"]
        if vid not in latest or row.get("snapshot_at", "") > latest[vid].get("snapshot_at", ""):
            latest[vid] = row
    return latest


def experiment_dates(channel: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in _read_jsonl(LEARNING / "experiments.jsonl"):
        if row.get("channel") == channel and row.get("video_id") and row.get("published_at"):
            out[row["video_id"]] = row["published_at"]
    return out


def metadata(yt, ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(ids), 50):
        resp = yt.videos().list(
            part="snippet,status,statistics,contentDetails",
            id=",".join(ids[i:i + 50]),
            maxResults=50,
        ).execute()
        for item in resp.get("items", []):
            out[item["id"]] = item
    return out


def fetch_curve(yta, video_id: str, published_at: str, end_date: str) -> tuple[list[dict], str | None]:
    pub = _parse_iso(published_at)
    start_date = (pub.date() if pub else dt.date.today()).isoformat()
    try:
        resp = yta.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            dimensions="elapsedVideoTimeRatio",
            metrics=("audienceWatchRatio,relativeRetentionPerformance,"
                     "startedWatching,stoppedWatching,totalSegmentImpressions"),
            filters=f"video=={video_id};audienceType==ORGANIC",
            maxResults=100,
        ).execute()
        headers = [h["name"] for h in resp.get("columnHeaders", [])]
        return [dict(zip(headers, row)) for row in (resp.get("rows") or [])], None
    except Exception as exc:  # keep the batch moving; record exact API error
        return [], f"{type(exc).__name__}: {exc}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="vitallogic_bad_pl")
    ap.add_argument("--n", type=int, default=25, help="number in each top/bottom cohort")
    ap.add_argument("--out", default="", help="output directory")
    args = ap.parse_args()

    latest = latest_metrics(args.channel)
    published = experiment_dates(args.channel)
    eligible = [r for r in latest.values() if r.get("views_per_day") is not None]
    eligible.sort(key=lambda r: (r.get("views_per_day") or 0, r.get("video_id")))
    bottom = eligible[:args.n]
    top = list(reversed(eligible[-args.n:]))
    selected = []
    seen = set()
    for cohort, rows in (("bottom", bottom), ("top", top)):
        for row in rows:
            vid = row["video_id"]
            if vid in seen:
                continue
            seen.add(vid)
            selected.append({"cohort": cohort, **row})

    yta, yt = _analytics_service(args.channel)
    meta = metadata(yt, [r["video_id"] for r in selected])
    end_date = dt.date.today().isoformat()
    stamp = now_iso()
    out_dir = Path(args.out) if args.out else LEARNING / "exports" / f"youtube_{dt.date.today().isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    curve_rows = []
    errors = []
    for idx, selected_row in enumerate(selected, 1):
        vid = selected_row["video_id"]
        item = meta.get(vid, {})
        pub = published.get(vid) or item.get("snippet", {}).get("publishedAt", "")
        curve, error = fetch_curve(yta, vid, pub, end_date)
        if error:
            errors.append({"video_id": vid, "cohort": selected_row["cohort"], "error": error})
        for point in curve:
            ratio = float(point.get("elapsedVideoTimeRatio") or 0)
            curve_rows.append({
                "video_id": vid,
                "title": item.get("snippet", {}).get("title", ""),
                "cohort": selected_row["cohort"],
                "published_at": pub,
                "views_per_day_snapshot": selected_row.get("views_per_day"),
                "elapsed_video_time_ratio": ratio,
                "elapsed_seconds": None,
                "audience_watch_ratio": point.get("audienceWatchRatio"),
                "relative_retention_performance": point.get("relativeRetentionPerformance"),
                "started_watching": point.get("startedWatching"),
                "stopped_watching": point.get("stoppedWatching"),
                "total_segment_impressions": point.get("totalSegmentImpressions"),
            })
        dur = item.get("contentDetails", {}).get("duration", "")
        summary_rows.append({
            "video_id": vid,
            "title": item.get("snippet", {}).get("title", ""),
            "cohort": selected_row["cohort"],
            "published_at": pub,
            "views_per_day_snapshot": selected_row.get("views_per_day"),
            "analytics_views_snapshot": selected_row.get("views"),
            "current_public_views": item.get("statistics", {}).get("viewCount"),
            "duration_iso8601": dur,
            "curve_points": len(curve),
            "error": error or "",
        })
        print(f"[{idx}/{len(selected)}] {vid}: {len(curve)} points" + (f"; {error}" if error else ""))

    def write_csv(path: Path, rows: list[dict]) -> None:
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(out_dir / "retention_curves.csv", curve_rows)
    write_csv(out_dir / "retention_summary.csv", summary_rows)
    (out_dir / "retention_errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "channel": args.channel,
        "exported_at": stamp,
        "selection": "latest local Analytics snapshot, sorted by views_per_day",
        "top_n": args.n,
        "selected_videos": len(selected),
        "curve_rows": len(curve_rows),
        "errors": len(errors),
        "source": "YouTube Analytics API v2, audienceType=ORGANIC",
        "files": ["retention_curves.csv", "retention_summary.csv", "retention_errors.json"],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] export: {out_dir}")
    print(f"[ok] videos={len(selected)} curve_points={len(curve_rows)} errors={len(errors)}")


if __name__ == "__main__":
    main()
