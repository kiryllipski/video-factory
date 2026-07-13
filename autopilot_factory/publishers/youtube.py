#!/usr/bin/env python3
"""
publishers/youtube.py — автопостинг в YouTube Shorts через YouTube Data API v3.

Портировано 2026-07-10 из `../creative production scheme/autopilot_factory/publishers/youtube.py`
(рабочий механизм, которым реально публиковался @VitalLogic-nutriFlow — см. `learning/experiments.jsonl`
в исходном проекте) и адаптировано под конвенции этого репо:
  - файл видео по умолчанию `out.mp4` (не `final.mp4`, конвенция `engine.py`/ARCHITECTURE.md §1);
  - `categoryId` по умолчанию `27` (Education), не `22` (People & Blogs) — по находке
    `orchestration/research/51_youtube_channel_setup_checklist.md`: 22 душит discovery;
  - `defaultLanguage` параметризован флагом `--lang` (pl для vitallogic_bad_pl, en для остальных),
    не захардкожен на "pl".

МУЛЬТИКАНАЛЬНОСТЬ: под одной Gmail-учёткой может быть много YouTube-каналов
(brand accounts). OAuth-токен привязывается к КОНКРЕТНОМУ каналу, выбранному
на экране согласия. Поэтому храним отдельный токен на канал:
    autopilot_factory/tokens/<channel_label>.json
и выбираем канал флагом --channel <label>.

Документация:
  - Загрузка видео:  https://developers.google.com/youtube/v3/guides/uploading_a_video
  - videos.insert:   https://developers.google.com/youtube/v3/docs/videos/insert
  - OAuth desktop:   https://developers.google.com/youtube/v3/guides/auth/installed-apps

Шаги:
  1) Один раз авторизовать канал (откроется браузер, ВЫБЕРИ нужный канал/бренд-аккаунт):
       python3 autopilot_factory/publishers/youtube.py auth --channel biz_failures --client-secret client_secret.json
  2) Загрузить ролик (planowana публикация — private + publishAt):
       python3 autopilot_factory/publishers/youtube.py upload --channel vitallogic_bad_pl \
           --run autopilot_factory/runs/vitallogic_bad_pl/2026-07-10_slug --lang pl \
           --privacy private --publish-at 2026-07-11T06:00:00Z
"""
from __future__ import annotations
import os
import sys
import json
import shutil
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # autopilot_factory/
TOKENS_DIR = ROOT / "tokens"
sys.path.insert(0, str(HERE))
import prepublisher

# Внешнее хранилище iCloud — куда переносим готовые/загруженные ролики (освобождает диск Mac).
# Дублирует engine.DELIVERY_ROOT намеренно, чтобы не тянуть тяжёлый импорт engine (google-genai и др.).
DELIVERY_ROOT = Path(os.environ.get(
    "VIDEO_DELIVERY_ROOT",
    "/Users/kirillipski/Library/Mobile Documents/com~apple~CloudDocs/external storage/video/0.5",
))


def _archive_to_icloud(run: Path, channel: str):
    """После успешной загрузки переносим ВЕСЬ прогон (кадры/аудио/hf/json/mp4) в iCloud
    (`DELIVERY_ROOT/<channel>/<run.name>/`) — договорённость владельца 2026-07-10: загруженные видео
    не держим локально. Если прогон уже лежит в iCloud (переиспользованный пилот) — no-op."""
    dest_dir = DELIVERY_ROOT / channel / run.name
    if run.resolve() == dest_dir.resolve():
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    for item in list(run.iterdir()):
        target = dest_dir / item.name
        if target.exists():                       # перезаписываем (deliver() мог положить titled mp4)
            shutil.rmtree(target) if target.is_dir() else target.unlink()
        shutil.move(str(item), str(target))
    try:
        run.rmdir()
    except OSError:
        pass
    return dest_dir

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    # force-ssl нужен для videos.update (правка метаданных/раскрытия уже загруженных роликов).
    # ВНИМАНИЕ: старые токены выданы без него — чтобы update заработал, нужен ПОВТОРНЫЙ `auth`
    # (браузерный OAuth). insert (загрузка) работает и без него, по youtube.upload.
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# Дефолтный язык канала (для defaultLanguage/defaultAudioLanguage), если не передан --lang.
CHANNEL_LANG = {
    "vitallogic_bad_pl": "pl",
    "biz_failures": "en",
    "psychology": "en",
    "wealth_viz": "en",
}


def _require_libs():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow  # noqa
        from google.oauth2.credentials import Credentials       # noqa
        from googleapiclient.discovery import build             # noqa
    except ImportError:
        sys.exit("Нужны библиотеки: pip install --user "
                 "google-api-python-client google-auth-oauthlib google-auth-httplib2")


def _token_path(channel: str) -> Path:
    TOKENS_DIR.mkdir(exist_ok=True)
    return TOKENS_DIR / f"{channel}.json"


def _load_creds(channel: str):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    tp = _token_path(channel)
    if not tp.exists():
        sys.exit(f"Нет токена для канала '{channel}'. Сначала: youtube.py auth --channel {channel} --client-secret <file>")
    creds = Credentials.from_authorized_user_file(str(tp), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        tp.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _service(channel: str):
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=_load_creds(channel))


def cmd_auth(args):
    _require_libs()
    from google_auth_oauthlib.flow import InstalledAppFlow
    secret = Path(args.client_secret)
    if not secret.exists():
        sys.exit(f"client_secret не найден: {secret}")
    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    print("Открывается браузер. ВАЖНО: выбери именно нужный YouTube-канал/бренд-аккаунт.")
    creds = flow.run_local_server(port=0)
    _token_path(args.channel).write_text(creds.to_json(), encoding="utf-8")

    # покажем, на какой канал реально авторизовались
    from googleapiclient.discovery import build
    yt = build("youtube", "v3", credentials=creds)
    me = yt.channels().list(part="snippet", mine=True).execute()
    title = me["items"][0]["snippet"]["title"] if me.get("items") else "?"
    print(f"[ok] токен сохранён: {_token_path(args.channel)}")
    print(f"[ok] авторизован канал: «{title}» (label='{args.channel}')")


def cmd_whoami(args):
    """Не-деструктивная проверка: подтверждает, что токен канала валиден/рефрешится."""
    _require_libs()
    yt = _service(args.channel)
    me = yt.channels().list(part="snippet,statistics", mine=True).execute()
    if not me.get("items"):
        sys.exit(f"[whoami] токен валиден, но канал не найден для '{args.channel}'")
    item = me["items"][0]
    title = item["snippet"]["title"]
    subs = item.get("statistics", {}).get("subscriberCount", "?")
    print(f"[whoami] channel='{args.channel}' → «{title}» (подписчиков: {subs})")


COMMENT_QUEUE = HERE / "comment_queue.jsonl"


def _post_comment(yt, video_id: str, text: str) -> dict:
    """Постит владельческий комментарий под роликом (commentThreads.insert).
    Требует scope youtube.force-ssl — старые токены без него нужно re-auth'нуть.
    Пиннинг через Data API v3 НЕВОЗМОЖЕН (метода нет) — но на свежем ролике без
    комментариев владельческий коммент и так первый; при желании закрепить — вручную в Studio."""
    return yt.commentThreads().insert(
        part="snippet",
        body={"snippet": {"videoId": video_id,
                          "topLevelComment": {"snippet": {"textOriginal": text}}}},
    ).execute()


def _queue_comment(video_id: str, channel: str, publish_at: str | None, text: str):
    """Ставит комментарий в очередь (постить можно только после выхода ролика в public —
    на private/scheduled ролике комментарии недоступны). Обрабатывает `post-comments`."""
    import datetime
    with open(COMMENT_QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "video_id": video_id, "channel": channel, "publish_at": publish_at,
            "text": text, "queued_at": datetime.datetime.utcnow().isoformat() + "Z",
        }, ensure_ascii=False) + "\n")


def cmd_post_comments(args):
    """Проходит comment_queue.jsonl: для роликов, уже вышедших в public, постит
    владельческий комментарий-вопрос (growth_plan_2026-07-13, этап 3: цикл вовлечения).
    Запускать после каждого publishAt-слота (scheduled task / вручную)."""
    _require_libs()
    if not COMMENT_QUEUE.exists():
        print("[post-comments] очередь пуста (нет comment_queue.jsonl).")
        return
    entries = [json.loads(l) for l in COMMENT_QUEUE.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.channel:
        pending = [e for e in entries if e["channel"] == args.channel]
        others = [e for e in entries if e["channel"] != args.channel]
    else:
        pending, others = entries, []
    if not pending:
        print("[post-comments] нет комментариев в очереди для этого канала.")
        return
    services: dict[str, object] = {}
    remaining = list(others)
    posted = 0
    for e in pending:
        ch = e["channel"]
        yt = services.setdefault(ch, _service(ch))
        try:
            resp = yt.videos().list(part="status", id=e["video_id"]).execute()
            items = resp.get("items", [])
            status = items[0]["status"]["privacyStatus"] if items else "missing"
        except Exception as exc:
            print(f"  [post-comments] {e['video_id']}: не удалось проверить статус ({exc}); оставляю в очереди.")
            remaining.append(e)
            continue
        if status != "public":
            print(f"  [post-comments] {e['video_id']}: статус={status}, ещё не public — жду.")
            remaining.append(e)
            continue
        try:
            _post_comment(yt, e["video_id"], e["text"])
            posted += 1
            print(f"  [post-comments] ✓ {e['video_id']}: «{e['text'][:60]}…»"
                  if len(e['text']) > 60 else f"  [post-comments] ✓ {e['video_id']}: «{e['text']}»")
        except Exception as exc:
            msg = str(exc)
            if "insufficientPermissions" in msg or "forbidden" in msg.lower():
                print(f"  [post-comments] ✗ {e['video_id']}: нет прав — токен канала '{ch}' без "
                      f"scope youtube.force-ssl. Нужен повторный auth:\n"
                      f"    python3 autopilot_factory/publishers/youtube.py auth --channel {ch} "
                      f"--client-secret autopilot_factory/client_secret.json")
            else:
                print(f"  [post-comments] ✗ {e['video_id']}: {msg[:300]}")
            remaining.append(e)
    COMMENT_QUEUE.write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in remaining), encoding="utf-8")
    print(f"[post-comments] опубликовано: {posted}; осталось в очереди: {len(remaining)}.")


def cmd_upload(args):
    _require_libs()
    from googleapiclient.http import MediaFileUpload
    run = Path(args.run).resolve()
    video = Path(args.video) if args.video else (run / "out.mp4")
    pkg_path = run / "publish_package.json"
    if not video.exists():
        sys.exit(f"Видео не найдено: {video}")
    pkg = json.loads(pkg_path.read_text(encoding="utf-8")) if pkg_path.exists() else {}

    lang = args.lang or CHANNEL_LANG.get(args.channel, "en")

    try:
        report = prepublisher.inspect_run(run, video, privacy=args.privacy, lang=lang)
        prepublisher.print_report(report)
    except Exception as exc:
        print(f"[prepublisher] warning: проверка не сработала ({exc}); публикация продолжается.")

    title = (pkg.get("title") or run.name)[:100]
    description = pkg.get("description", "")
    tags = [h.lstrip("#") for h in pkg.get("hashtags", [])][:15]
    if "Shorts" not in tags:
        tags.append("Shorts")

    status = {
        "privacyStatus": args.privacy,             # private | unlisted | public
        "selfDeclaredMadeForKids": False,
        # Раскрытие AI: кадры (Nano Banana) фотореалистичны + голос синтетический (Gemini TTS) →
        # YouTube требует пометку «altered/synthetic content», а с мая 2026 авто-детектит и метит сам
        # (support.google.com/youtube/answer/14328491, revision_history: status.containsSyntheticMedia,
        # с 2024-10-30). Дефолт true для нашего пайплайна; отключить — флагом --no-synthetic.
        "containsSyntheticMedia": bool(getattr(args, "synthetic", True)),
    }
    # Плановая публикация: при publishAt YouTube требует privacyStatus=private; в заданный момент
    # (RFC3339, UTC) ролик автоматически становится public. Док: videos.insert status.publishAt.
    if getattr(args, "publish_at", None):
        status["privacyStatus"] = "private"
        status["publishAt"] = args.publish_at

    body = {
        "snippet": {
            "title": title,
            "description": description + ("\n\n#Shorts" if "#Shorts" not in description else ""),
            "tags": tags,
            "categoryId": args.category,   # 27=Education (дефолт), см. research/51 — 22 душит discovery
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": status,
    }

    sched = f" publishAt={args.publish_at}" if getattr(args, "publish_at", None) else ""
    print(f"[upload] канал='{args.channel}' lang={lang} category={args.category} privacy={status['privacyStatus']}{sched}\n  video: {video}\n  title: {title}")
    yt = _service(args.channel)
    media = MediaFileUpload(str(video), chunksize=-1, resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    try:
        while resp is None:
            status_chunk, resp = req.next_chunk()
            if status_chunk:
                print(f"  ... {int(status_chunk.progress()*100)}%")
    except Exception as exc:
        from googleapiclient.errors import HttpError
        is_quota = isinstance(exc, HttpError) and "uploadLimitExceeded" in str(exc)
        if not is_quota:
            raise
        pending = {
            "pending": True, "reason": "uploadLimitExceeded",
            "channel": args.channel, "privacy": args.privacy,
            "publish_at": getattr(args, "publish_at", None),
            "video": str(video), "detail": str(exc)[:500],
        }
        (run / "upload_pending.json").write_text(
            json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [upload] uploadLimitExceeded — суточный лимит канала. Ролик НЕ потерян, "
              f"помечен upload_pending=true ({run / 'upload_pending.json'}).")
        print(f"  [upload] дозалить позже: python3 autopilot_factory/publishers/youtube.py retry-pending --channel {args.channel}")
        sys.exit(2)
    vid = resp["id"]
    url = f"https://youtube.com/shorts/{vid}"
    result = {"video_id": vid, "url": url, "privacy": args.privacy,
              "channel_label": args.channel, "title": title}
    if getattr(args, "publish_at", None):
        result["publish_at"] = args.publish_at

    # Кастомная обложка (если <run>/thumbnail.jpg сгенерирован). Требует
    # ВЕРИФИЦИРОВАННОГО канала — иначе API вернёт ошибку; в этом случае не падаем,
    # ролик остаётся с авто-кадром, а статус пишем в результат.
    thumb_file = run / "thumbnail.jpg"
    result["thumbnail_set"] = False
    if thumb_file.exists():
        try:
            yt.thumbnails().set(
                videoId=vid,
                media_body=MediaFileUpload(str(thumb_file), mimetype="image/jpeg"),
            ).execute()
            result["thumbnail_set"] = True
            print(f"  [thumbnail] обложка установлена: {thumb_file.name}")
        except Exception as e:
            result["thumbnail_error"] = str(e)[:300]
            print(f"  [thumbnail] не удалось установить обложку (канал не верифицирован?): {e}")
    else:
        print("  [thumbnail] thumbnail.jpg не найден — пропускаю установку обложки")

    # v2 (growth_plan этап 3): комментарий-вопрос владельца из publish_package.pinned_comment.
    # Ролик public прямо сейчас → постим сразу; private/scheduled → в очередь (post-comments).
    pinned = (pkg.get("pinned_comment") or "").strip()
    result["pinned_comment"] = pinned
    if pinned:
        if status["privacyStatus"] == "public":
            try:
                _post_comment(yt, vid, pinned)
                result["comment_posted"] = True
                print(f"  [comment] владельческий комментарий опубликован: «{pinned[:60]}»")
            except Exception as e:
                result["comment_posted"] = False
                _queue_comment(vid, args.channel, None, pinned)
                print(f"  [comment] не удалось опубликовать сразу ({str(e)[:200]}) — "
                      f"поставлен в очередь comment_queue.jsonl (post-comments)")
        else:
            _queue_comment(vid, args.channel, getattr(args, "publish_at", None), pinned)
            result["comment_posted"] = False
            print(f"  [comment] ролик не public (publishAt) — комментарий в очереди; после слота: "
                  f"python3 autopilot_factory/publishers/youtube.py post-comments --channel {args.channel}")

    (run / "post_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    pending_marker = run / "upload_pending.json"
    if pending_marker.exists():
        pending_marker.unlink()

    # Версия пайплайна из run_meta.json (пишет build_media, v2+) — для сравнения v1/v2 в аналитике.
    pipeline_version = ""
    meta_path = run / "run_meta.json"
    if meta_path.exists():
        try:
            pipeline_version = json.loads(meta_path.read_text(encoding="utf-8")).get("pipeline_version", "")
        except Exception:
            pipeline_version = ""

    # Накопительный журнал публикаций (append-only) для будущего анализа.
    pub_log = ROOT / "publishers" / "publish_log.jsonl"
    with open(pub_log, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "run": run.name, "channel": args.channel, "video_id": vid, "url": url,
            "title": title, "published_at_or_scheduled": result.get("publish_at") or "now",
            "pipeline_version": pipeline_version,
            "title_template": pkg.get("title_template", ""),
        }, ensure_ascii=False) + "\n")
    print(f"[done] {url}\n[saved] {run / 'post_result.json'}")

    # Перенос загруженного прогона в iCloud (договорённость 2026-07-10). Отключить — --no-archive.
    if not getattr(args, "no_archive", False):
        try:
            moved = _archive_to_icloud(run, args.channel)
            print(f"[archived] прогон перемещён в iCloud → {moved}" if moved
                  else "[archived] прогон уже в iCloud — перенос не нужен")
        except Exception as e:
            print(f"[archive] warning: не удалось перенести в iCloud ({e}); локальная копия сохранена.")


def cmd_retry_pending(args):
    """Дозаливка роликов, упавших на uploadLimitExceeded (см. upload_pending.json в run_dir)."""
    runs_dir = ROOT / "runs"
    pending_files = sorted(runs_dir.glob("*/*/upload_pending.json"))
    if not pending_files:
        print("[retry-pending] нет роликов с upload_pending=true.")
        return
    print(f"[retry-pending] найдено {len(pending_files)} ролик(ов) на дозаливку.")
    for pf in pending_files:
        run_dir = pf.parent
        pending = json.loads(pf.read_text(encoding="utf-8"))
        if args.channel and pending.get("channel") != args.channel:
            continue
        print(f"\n---- дозаливаю {run_dir.name} ----")
        upload_args = argparse.Namespace(
            channel=pending["channel"], run=str(run_dir), video=None,
            privacy=pending.get("privacy", "private"), publish_at=pending.get("publish_at"),
            lang=None, category="27", synthetic=True, no_archive=False,
        )
        try:
            cmd_upload(upload_args)
        except SystemExit as exc:
            if exc.code == 2:
                print(f"  [retry-pending] всё ещё лимит — попробуй позже: {run_dir.name}")
            else:
                raise


def main():
    p = argparse.ArgumentParser(description="YouTube Shorts publisher (мультиканальный)")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("auth", help="авторизовать канал (один раз)")
    a.add_argument("--channel", required=True, help="метка канала, напр. vitallogic_bad_pl")
    a.add_argument("--client-secret", required=True, help="OAuth client_secret.json (Desktop app)")
    a.set_defaults(func=cmd_auth)

    w = sub.add_parser("whoami", help="проверить токен канала без публикации (read-only)")
    w.add_argument("--channel", required=True)
    w.set_defaults(func=cmd_whoami)

    u = sub.add_parser("upload", help="загрузить ролик")
    u.add_argument("--channel", required=True)
    u.add_argument("--run", required=True, help="папка запуска (с out.mp4 и publish_package.json)")
    u.add_argument("--video", default=None, help="путь к видео (по умолчанию <run>/out.mp4)")
    u.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    u.add_argument("--lang", default=None, help="pl | en (по умолчанию берётся из CHANNEL_LANG по --channel)")
    u.add_argument("--category", default="27", help="YouTube categoryId (27=Education, дефолт)")
    u.add_argument("--publish-at", dest="publish_at", default=None,
                   help="Запланировать авто-публикацию: RFC3339 UTC, напр. 2026-07-11T06:00:00Z "
                        "(ролик заливается private и сам станет public в этот момент)")
    u.add_argument("--no-synthetic", dest="synthetic", action="store_false",
                   help="НЕ помечать как AI/synthetic (по умолчанию помечаем — кадры и голос AI)")
    u.add_argument("--no-archive", dest="no_archive", action="store_true",
                   help="НЕ переносить прогон в iCloud после загрузки (по умолчанию переносим)")
    u.set_defaults(func=cmd_upload, synthetic=True, no_archive=False)

    r = sub.add_parser("retry-pending", help="дозалить ролики с upload_pending=true (лимит сброшен)")
    r.add_argument("--channel", default=None, help="ограничить одним каналом (по умолчанию — все)")
    r.set_defaults(func=cmd_retry_pending)

    c = sub.add_parser("post-comments",
                       help="опубликовать владельческие комментарии-вопросы из comment_queue.jsonl "
                            "для роликов, уже вышедших в public (v2, growth_plan этап 3)")
    c.add_argument("--channel", default=None, help="ограничить одним каналом (по умолчанию — все)")
    c.set_defaults(func=cmd_post_comments)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
