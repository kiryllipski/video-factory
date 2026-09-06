#!/usr/bin/env python3
"""
prepublisher.py — мягкая проверка перед публикацией.

Портировано 2026-07-10 из `../creative production scheme/autopilot_factory/prepublisher.py`
(механизм автопостинга VitalLogic) и адаптировано под мультиязычный пайплайн этого репо —
PL-специфичные проверки (wellness-комплаенс, дисклеймер, кириллица) теперь включаются только
при lang="pl", остальные каналы (biz_failures/psychology/wealth_viz, lang="en") их не видят.

Задача PrePublisher: заметить проблемы упаковки/артефактов и записать их в лог.
Обычные packaging warnings остаются мягкими. Для современных v8/v9 прогонов отсутствие или
провал release gate блокирует публикацию: финальный QA не может быть advisory после рендера.
"""
import json
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


DISCLAIMER_PL = "Materiał ma charakter edukacyjny i nie zastępuje porady lekarza."

FORBIDDEN_CLAIM_PATTERNS_PL = [
    r"\bleczy\b",
    r"\bwyleczy\b",
    r"\buzdrawia\b",
    r"\bgwarantuje\b",
    r"\bna pewno\b",
    r"\b100\s*%\b",
    r"\bchorob\w*\b",
    r"\bdepresj\w*\b",
    r"\bbezsenno\w*\b",
]

TOPIC_KEYWORD_STEMS_PL = [
    # витамины/минералы/добавки (ascii — _norm срезает диакритику: żelazo→zelazo, włosy→wlos)
    "magnez", "witamin", "cynk", "miedz", "zelazo", "ferrytyn", "wapn", "kolagen",
    "biotyn", "jod", "selen", "omega", "probiotyk", "kreatyn", "melatonin",
    "ashwagandh", "teanin", "kurkumin", "potas", "elektrolit",
    # симптомы/бытовые триггеры (searched как темы)
    "wlos", "paznokc", "wzdec", "skurcz", "przezieb", "zmeczen", "mgla", "skor",
    "kawa", "truskawk", "borowk", "herbat", "telefon", "ekran", "sen", "swiatlo",
    "slonce", "woda",
]


def _issue(severity, code, message, field=None, value=None):
    item = {
        "severity": severity,
        "code": code,
        "message": message,
    }
    if field:
        item["field"] = field
    if value is not None:
        item["value"] = value
    return item


def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception as exc:
        return {"_load_error": str(exc)}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def _probe_video(video_path):
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration",
                "-of", "json",
                str(video_path),
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        return None, [_issue("info", "ffprobe_missing", "ffprobe не найден: параметры видео не проверены.")]

    if proc.returncode != 0:
        return None, [_issue("warning", "ffprobe_failed", "ffprobe не смог прочитать видео.", value=proc.stderr.strip())]

    try:
        data = json.loads(proc.stdout)
        streams = data.get("streams") or []
        return (streams[0] if streams else None), []
    except Exception as exc:
        return None, [_issue("warning", "ffprobe_parse_failed", "Не удалось разобрать ffprobe JSON.", value=str(exc))]


def inspect_run(run_dir, video_path=None, privacy=None, lang=None):
    """Возвращает soft-report и пишет его в <run_dir>/pre_publish_log.json.

    lang: "pl" включает wellness-комплаенс проверки (дисклеймер, запрещённые claim'ы,
    topic-keyword в title) — актуально только для vitallogic_bad_pl. Для остальных
    каналов (en) эти проверки пропускаются, чтобы не давать ложных warnings.
    """
    run = Path(run_dir).resolve()
    video = Path(video_path).resolve() if video_path else (run / "out.mp4")
    issues = []

    pkg_path = run / "publish_package.json"
    pkg = _load_json(pkg_path)
    qa = _load_json(run / "qa.json")
    release = _load_json(run / "release_gate.json")
    run_meta = _load_json(run / "run_meta.json") or {}
    pipeline_version = str(run_meta.get("pipeline_version") or "")
    modern_release = pipeline_version.startswith(("8", "9"))

    if modern_release and release is None:
        issues.append(_issue(
            "error",
            "release_gate_missing",
            f"Для pipeline {pipeline_version} отсутствует release_gate.json.",
            "release_gate",
        ))
    elif isinstance(release, dict) and release.get("passed") is not True:
        failed_checks = [
            str(item.get("name") or "unknown")
            for item in release.get("checks", [])
            if item.get("passed") is not True
        ]
        issues.append(_issue(
            "error",
            "release_gate_failed",
            "Финальный release gate не пройден; upload/schedule запрещён.",
            "failed_checks",
            failed_checks,
        ))

    if not video.exists():
        issues.append(_issue("error", "video_missing", "Видео для публикации не найдено.", "video", str(video)))
    elif video.stat().st_size <= 0:
        issues.append(_issue("error", "video_empty", "Файл видео пустой.", "video", str(video)))
    else:
        stream, probe_issues = _probe_video(video)
        issues.extend(probe_issues)
        if stream:
            width = int(stream.get("width") or 0)
            height = int(stream.get("height") or 0)
            duration = float(stream.get("duration") or 0)
            if width and height and height <= width:
                issues.append(_issue("warning", "not_vertical", "Видео не выглядит вертикальным 9:16.", "video_size", f"{width}x{height}"))
            if duration and (duration < 8 or duration > 75):
                issues.append(_issue("warning", "duration_outside_shorts_range", "Длительность вне ожидаемого диапазона Shorts.", "duration_sec", round(duration, 2)))

    if pkg is None:
        issues.append(_issue("error", "publish_package_missing", "Нет publish_package.json. YouTube возьмёт fallback-данные."))
        pkg = {}
    elif "_load_error" in pkg:
        issues.append(_issue("error", "publish_package_invalid_json", "publish_package.json не читается как JSON.", value=pkg["_load_error"]))
        pkg = {}

    title = str(pkg.get("title") or "").strip()
    description = str(pkg.get("description") or "").strip()
    hashtags = pkg.get("hashtags") or []

    if not title:
        issues.append(_issue("error", "title_missing", "Нет title в publish_package.json.", "title"))
    if len(title) > 100:
        issues.append(_issue("warning", "title_too_long", "YouTube обрежет title до 100 символов.", "title", title))
    if "\n" in title or "\r" in title:
        issues.append(_issue("warning", "title_has_linebreaks", "В title есть переносы строк; лучше убрать перед public.", "title", title))
    if "#" in title:
        issues.append(_issue("warning", "title_has_hashtag", "Лучше держать title чистым: topic-keyword без #, hashtags — в description.", "title", title))

    if not description:
        issues.append(_issue("error", "description_missing", "Нет description в publish_package.json.", "description"))

    if not isinstance(hashtags, list):
        issues.append(_issue("error", "hashtags_not_list", "hashtags должен быть списком.", "hashtags", hashtags))
        hashtags = []
    normalized_tags = [str(tag).strip() for tag in hashtags if str(tag).strip()]
    if len(normalized_tags) < 3 or len(normalized_tags) > 6:
        issues.append(_issue("warning", "hashtags_count", "Ожидается 3-6 hashtags.", "hashtags_count", len(normalized_tags)))
    if "#Shorts" not in normalized_tags and "Shorts" not in [tag.lstrip("#") for tag in normalized_tags]:
        issues.append(_issue("warning", "shorts_hashtag_missing", "Не найден #Shorts в hashtags.", "hashtags", normalized_tags))

    if lang == "pl":
        if title and re.search(r"[А-Яа-яЁё]", title):
            issues.append(_issue("warning", "title_has_cyrillic", "В польском title найдена кириллица.", "title", title))
        if title and not any(stem in _norm(title) for stem in TOPIC_KEYWORD_STEMS_PL):
            issues.append(_issue(
                "warning",
                "title_missing_topic_keyword",
                "Title не содержит явный topic-keyword вроде magnez / witamina D / kawa / truskawki. Первые данные показывают, что такие title работают лучше.",
                "title",
                title,
            ))
        if description and DISCLAIMER_PL not in description:
            issues.append(_issue("warning", "disclaimer_missing", "В description не найден стандартный educational disclaimer.", "description"))
        if description and re.search(r"[А-Яа-яЁё]", description):
            issues.append(_issue("warning", "description_has_cyrillic", "В польском description найдена кириллица.", "description"))
        combined_copy = f"{title}\n{description}".lower()
        for pattern in FORBIDDEN_CLAIM_PATTERNS_PL:
            if re.search(pattern, combined_copy, flags=re.IGNORECASE):
                issues.append(_issue("warning", "risky_health_claim", "В упаковке найден потенциально рискованный health-claim.", "pattern", pattern))

    if isinstance(qa, dict) and not qa.get("approved", True):
        issues.append(_issue("warning", "creative_qa_not_approved", "Creative QA был не approved, публикация всё равно не блокируется.", "blocking_issues", qa.get("blocking_issues", [])))

    blocks_publication = any(item["severity"] == "error" for item in issues)
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "run_dir": str(run),
        "video": str(video),
        "privacy": privacy,
        "status": "issues_found" if issues else "clean",
        "blocks_publication": blocks_publication,
        "summary": {
            "errors": sum(1 for item in issues if item["severity"] == "error"),
            "warnings": sum(1 for item in issues if item["severity"] == "warning"),
            "info": sum(1 for item in issues if item["severity"] == "info"),
        },
        "issues": issues,
    }
    (run / "pre_publish_log.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def print_report(report):
    summary = report.get("summary", {})
    issues = report.get("issues", [])
    blocking = bool(report.get("blocks_publication"))
    print(
        "[prepublisher] "
        f"errors={summary.get('errors', 0)} "
        f"warnings={summary.get('warnings', 0)} "
        f"info={summary.get('info', 0)} "
        + ("(ПУБЛИКАЦИЯ ЗАБЛОКИРОВАНА)" if blocking else "(публикация не блокируется)")
    )
    for item in issues[:12]:
        print(f"  - {item['severity']}: {item['code']} — {item['message']}")
    if len(issues) > 12:
        print(f"  ... ещё {len(issues) - 12} issues см. pre_publish_log.json")
