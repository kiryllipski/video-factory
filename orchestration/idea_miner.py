#!/usr/bin/env python3
"""
idea_miner.py — майнер тем/идей для контент-фабрики.

Переводит поиск тем из ручного «тыкания в VidIQ» в детерминированный пайплайн:
    seed-ниша → расширение через YouTube autocomplete (бесплатно, без ключа)
              → поиск конкурентов в нише (YouTube Data API v3)
              → outlier-детект «залетевших» видео (V/S ratio)
              → (опц.) майнинг болей из комментов
              → (опц.) LLM-ранжирование в бэклог идей (Gemini через gemini_agent)

Обоснование метода — orchestration/research/55_content_ideation_tools.md:
LLM НЕ придумывает темы (галлюцинации), а ранжирует проверяемые сигналы спроса.
Лучший источник валидированных тем — outlier у мелких каналов: свежее видео с
V/S ratio (views/subscribers) > порога у канала с малой базой = алгоритм уже прогрел тему.

КЛЮЧИ (.env в корне проекта имеет приоритет над окружением):
  - GEMINI_API_KEY   — только для --rank (LLM-ранжирование). Autocomplete/outliers без него.
  - YOUTUBE_API_KEY  — для режимов outliers/full (YouTube Data API v3). Получить:
    https://console.cloud.google.com/ → включить "YouTube Data API v3" → создать API key.

КВОТЫ YouTube Data API v3 (10 000 юнитов/день по умолчанию):
  search.list = 100 юнитов/вызов (дорого!), videos.list / channels.list / playlistItems.list = 1 юнит,
  commentThreads.list = 1 юнит. Скрипт батчит id пачками по 50 и лимитирует число search.list.

CLI:
    # 1) только расширить семантику (бесплатно, без ключа):
    python3 orchestration/idea_miner.py --mode autocomplete --seed "business failures" --lang en

    # 2) полный прогон с outlier-детектом и ранжированием:
    python3 orchestration/idea_miner.py --channel biz_failures \\
        --seed "business failures" --seed "company collapse" --lang en \\
        --max-queries 5 --min-vs 3 --max-subs 50000 --max-age-days 60 \\
        --comments --rank --out orchestration/idea_backlog/biz_failures.json

Как библиотека:
    from idea_miner import autocomplete, mine_outliers, rank_ideas

Легальность: используется ТОЛЬКО официальный YouTube Data API (White-hat). HTML-скрейпинг
YouTube запрещён ToS. Autocomplete-эндпоинт неофициальный, но открытый (публичные подсказки).
"""
import os
import re
import sys
import json
import time
import argparse
import datetime as _dt
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request

# --- .env loader (.env проекта приоритетнее системного окружения), как в image_agent.py ---
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
def _load_env():
    env_path = _PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()
_load_env()

# gemini_agent — сосед по каталогу (для --rank)
sys.path.insert(0, str(Path(__file__).resolve().parent))

_ALPHABET_EN = "abcdefghijklmnopqrstuvwxyz"
_ALPHABET_RU = "абвгдежзиклмнопрстуфхцчшыэюя"
_ALPHABET_PL = "abcdefghijklmnoprstuwyz"


# ─────────────────────────── 1. AUTOCOMPLETE (расширение семантики) ───────────────────────────

def _suggest_once(query: str, lang: str, timeout: float = 8.0) -> list:
    """Один запрос к YouTube-autocomplete (client=firefox → JSON [query, [suggestions]])."""
    url = (
        "https://suggestqueries.google.com/complete/search"
        f"?client=firefox&ds=yt&hl={quote(lang)}&q={quote(query)}"
    )
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (idea_miner)"})
    try:
        with urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        return list(data[1]) if len(data) > 1 else []
    except Exception:
        return []


def autocomplete(seeds, lang: str = "en", depth: int = 1, pause: float = 0.2) -> list:
    """Рекурсивно расширяет seed-темы подсказками YouTube.

    depth=0 — только сами seeds; depth=1 — seeds + перебор "seed <буква>" (long-tail);
    depth=2 — ещё уровень по собранным подсказкам. Возвращает отсортированный dedup-список.
    """
    alphabet = {"en": _ALPHABET_EN, "ru": _ALPHABET_RU, "pl": _ALPHABET_PL}.get(lang, _ALPHABET_EN)
    seen = set()
    frontier = list(seeds)
    for s in seeds:
        for sug in _suggest_once(s, lang):
            seen.add(sug.lower())
        time.sleep(pause)
    for _level in range(depth):
        next_frontier = []
        for base in frontier:
            for ch in alphabet:
                q = f"{base} {ch}"
                for sug in _suggest_once(q, lang):
                    low = sug.lower()
                    if low not in seen:
                        seen.add(low)
                        next_frontier.append(sug)
                time.sleep(pause)
        frontier = next_frontier
        if not frontier:
            break
    return sorted(seen)


# ─────────────────────────── 2. YOUTUBE DATA API — outlier-детект ───────────────────────────

class _Quota:
    """Мягкий учёт израсходованных юнитов квоты (для отчёта)."""
    def __init__(self):
        self.units = 0
    def add(self, n):
        self.units += n


def youtube_service():
    """Строит клиент YouTube Data API v3. Требует YOUTUBE_API_KEY."""
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise SystemExit(
            "YOUTUBE_API_KEY не найден. Добавь строку YOUTUBE_API_KEY=... в .env в корне проекта.\n"
            "Ключ: https://console.cloud.google.com/ → включить 'YouTube Data API v3' → API key."
        )
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise SystemExit("Нужен пакет google-api-python-client: pip3 install google-api-python-client")
    return build("youtube", "v3", developerKey=key, cache_discovery=False)


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def find_channels(svc, query: str, lang: str, quota: "_Quota", max_channels: int = 10) -> list:
    """search.list (type=channel) — находит каналы в нише. Стоит 100 юнитов/вызов."""
    resp = svc.search().list(
        q=query, type="channel", part="snippet",
        maxResults=min(max_channels, 50), relevanceLanguage=lang, order="relevance",
    ).execute()
    quota.add(100)
    return [it["snippet"]["channelId"] for it in resp.get("items", [])]


def top_videos(svc, queries, lang: str, *, max_queries: int = 5, per_query: int = 15,
               published_after: str = None, min_views: int = 10000, quota: "_Quota" = None) -> list:
    """Самые просматриваемые ролики ниши (search.list type=video, order=viewCount).

    В отличие от outlier-детекта (мелкие каналы, VS-ratio) — вытаскивает ПРОВЕРЕННЫЕ темы/
    форматы независимо от размера канала: топ по абсолютным просмотрам. Лучший источник для
    «изучить подходы крупных игроков». 100 юнитов/запрос (search) + 1 юнит/50 id (videos).
    """
    quota = quota or _Quota()
    # YouTube ждёт RFC3339 (с временем и 'Z'); принимаем и голую дату YYYY-MM-DD
    if published_after and len(published_after.strip()) == 10:
        published_after = published_after.strip() + "T00:00:00Z"
    video_ids, chan_title = [], {}
    for q in list(queries)[:max_queries]:
        try:
            params = dict(q=q, type="video", part="snippet", order="viewCount",
                          maxResults=min(per_query, 50), relevanceLanguage=lang)
            if published_after:
                params["publishedAfter"] = published_after
            resp = svc.search().list(**params).execute()
            quota.add(100)
        except Exception as e:
            print(f"[top] пропуск запроса '{q}': {e}", file=sys.stderr)
            continue
        for it in resp.get("items", []):
            vid = it["id"]["videoId"]
            video_ids.append(vid)
            chan_title[vid] = it["snippet"].get("channelTitle", "")
    vids = videos_meta(svc, list(dict.fromkeys(video_ids)), quota)
    out = []
    seen = set()
    for v in vids:
        if v["views"] < min_views or v["video_id"] in seen:
            continue
        seen.add(v["video_id"])
        v["channel_title"] = chan_title.get(v["video_id"], "")
        out.append(v)
    out.sort(key=lambda x: x["views"], reverse=True)
    return out


def channels_meta(svc, channel_ids, quota: "_Quota") -> dict:
    """channels.list — статистика и uploads-плейлист. 1 юнит/вызов, батч до 50 id."""
    out = {}
    for batch in _chunks(list(dict.fromkeys(channel_ids)), 50):
        resp = svc.channels().list(
            id=",".join(batch), part="snippet,statistics,contentDetails",
        ).execute()
        quota.add(1)
        for it in resp.get("items", []):
            stats = it.get("statistics", {})
            out[it["id"]] = {
                "title": it["snippet"]["title"],
                "subscribers": int(stats.get("subscriberCount", 0)) if not stats.get("hiddenSubscriberCount") else None,
                "uploads_playlist": it["contentDetails"]["relatedPlaylists"].get("uploads"),
            }
    return out


def recent_video_ids(svc, uploads_playlist: str, quota: "_Quota", n: int = 20) -> list:
    """playlistItems.list — последние N видео канала. 1 юнит/вызов (50 id за раз)."""
    if not uploads_playlist:
        return []
    ids, token = [], None
    while len(ids) < n:
        try:
            resp = svc.playlistItems().list(
                playlistId=uploads_playlist, part="contentDetails",
                maxResults=min(50, n - len(ids)), pageToken=token,
            ).execute()
        except Exception:
            break  # 404 playlistNotFound / приватный канал — пропускаем, не роняем прогон
        quota.add(1)
        ids += [it["contentDetails"]["videoId"] for it in resp.get("items", [])]
        token = resp.get("nextPageToken")
        if not token:
            break
    return ids[:n]


def videos_meta(svc, video_ids, quota: "_Quota") -> list:
    """videos.list — просмотры/дата/теги. 1 юнит/вызов, батч до 50 id."""
    out = []
    for batch in _chunks(video_ids, 50):
        resp = svc.videos().list(
            id=",".join(batch), part="snippet,statistics",
        ).execute()
        quota.add(1)
        for it in resp.get("items", []):
            st = it.get("statistics", {})
            sn = it["snippet"]
            out.append({
                "video_id": it["id"],
                "title": sn.get("title", ""),
                "channel_id": sn.get("channelId", ""),
                "published_at": sn.get("publishedAt", ""),
                "views": int(st.get("viewCount", 0)) if st.get("viewCount") else 0,
                "tags": sn.get("tags", [])[:15],
                "url": f"https://youtube.com/watch?v={it['id']}",
            })
    return out


def top_comments(svc, video_id: str, quota: "_Quota", n: int = 30) -> list:
    """commentThreads.list — топ-комменты (боли/запросы аудитории). 1 юнит/вызов."""
    try:
        resp = svc.commentThreads().list(
            videoId=video_id, part="snippet", maxResults=min(n, 100),
            order="relevance", textFormat="plainText",
        ).execute()
        quota.add(1)
    except Exception:
        return []  # комменты выключены у видео
    out = []
    for it in resp.get("items", []):
        top = it["snippet"]["topLevelComment"]["snippet"]
        out.append({"text": top.get("textDisplay", "")[:400], "likes": top.get("likeCount", 0)})
    return out


def _age_days(published_at: str) -> float:
    try:
        dt = _dt.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        return (_dt.datetime.now(_dt.timezone.utc) - dt).total_seconds() / 86400.0
    except Exception:
        return 1e9


def mine_outliers(svc, queries, lang: str, *, max_queries: int = 5, channels_per_query: int = 10,
                  videos_per_channel: int = 20, min_vs: float = 3.0, min_subs: int = 1000,
                  max_subs: int = 50000, max_age_days: float = 60.0, min_views: int = 1000,
                  quota: "_Quota" = None) -> list:
    """Находит каналы по запросам и возвращает outlier-видео (V/S ratio > min_vs у свежих).

    Outlier = свежий (age < max_age_days), у канала с min_subs <= subs <= max_subs, где
    views/subscribers > min_vs → алгоритм уже прогрел тему. min_subs отсекает микроканалы/
    бренд-аккаунты (8–50 подписчиков), где VS-ratio раздут и не отражает реальный спрос.
    Отсортировано по vs_ratio.
    """
    quota = quota or _Quota()
    # 1) собрать каналы
    channel_ids = []
    for q in list(queries)[:max_queries]:
        try:
            channel_ids += find_channels(svc, q, lang, quota, channels_per_query)
        except Exception as e:
            print(f"[outliers] пропуск запроса '{q}': {e}", file=sys.stderr)
    channel_ids = list(dict.fromkeys(channel_ids))
    if not channel_ids:
        return []
    # 2) мета каналов (subs + uploads)
    meta = channels_meta(svc, channel_ids, quota)
    # 3) последние видео каждого канала
    all_video_ids = []
    for cid, m in meta.items():
        all_video_ids += recent_video_ids(svc, m["uploads_playlist"], quota, videos_per_channel)
    # 4) статистика видео батчами
    vids = videos_meta(svc, all_video_ids, quota)
    # 5) считаем outlier score
    outliers = []
    for v in vids:
        cm = meta.get(v["channel_id"])
        if not cm or not cm["subscribers"]:
            continue
        subs = cm["subscribers"]
        if subs <= 0 or subs < min_subs or subs > max_subs:
            continue
        if v["views"] < min_views:
            continue
        age = _age_days(v["published_at"])
        if age > max_age_days:
            continue
        vs = v["views"] / subs
        if vs < min_vs:
            continue
        outliers.append({
            **v,
            "channel_title": cm["title"],
            "subscribers": subs,
            "age_days": round(age, 1),
            "vs_ratio": round(vs, 2),
        })
    outliers.sort(key=lambda x: x["vs_ratio"], reverse=True)
    return outliers


# ─────────────────────────── 3. LLM-РАНЖИРОВАНИЕ (Gemini) ───────────────────────────

_RANK_SYSTEM = (
    "Ты — YouTube-продюсер контент-фабрики. Тебе дают ПРОВЕРЯЕМЫЕ сигналы спроса "
    "(top_videos — самые просматриваемые ролики ниши = проверенные темы/форматы; "
    "outlier-видео конкурентов с vs_ratio; autocomplete-запросы; боли из комментов). "
    "Сигналы могут быть на другом языке (напр. англ.) — изучи ПОДХОД/формат/угол и адаптируй "
    "к рынку и языку канала. Твоя задача — НЕ выдумывать темы, а синтезировать из сигналов "
    "бэклог идей под нишу канала. Каждая идея опирается на конкретный сигнал. Верни СТРОГО JSON."
)

_RANK_INSTRUCTION = (
    "Верни JSON-массив из {n} идей, отсортированный по убыванию потенциала. Каждый объект:\n"
    '{{"title": "кликабельный заголовок НА ЯЗЫКЕ КАНАЛА", "angle": "уникальный угол подачи", '
    '"format": "short|long", "rationale": "почему зайдёт — со ссылкой на сигнал", '
    '"borrowed_approach": "какой приём/формат крупного канала переиспользован (если из top_videos)", '
    '"source_signal": "top_video | outlier vs_ratio X.X | autocomplete | comment_pain", '
    '"score": 0-100}}\n'
    "Учитывай нишу, рубрики и ЯЗЫК канала (заголовки на языке канала). Под ретеншен "
    "(hook в первых словах), без кликбейта без покрытия."
)


def _clean_pains(pains: list, limit: int = 40) -> list:
    """Отсекает мусор из комментов: эмодзи-only, слишком короткие, благодарности."""
    junk = re.compile(r"^(thanks?|thank you|thx|nice|wow|great|super|dzięki|dziękuję|👍|🔥|❤|🎉)+",
                      re.IGNORECASE)
    out = []
    for p in pains:
        s = (p or "").strip()
        letters = sum(c.isalpha() for c in s)
        if letters < 15 or junk.match(s):
            continue
        out.append(s[:300])
        if len(out) >= limit:
            break
    return out


def rank_ideas(channel_ctx: str, outliers: list, suggestions: list, pains: list,
               top: list = None, n: int = 12, model: str = "pro") -> list:
    """Кластеризует сигналы в ранжированный бэклог идей через Gemini (json_mode)."""
    from gemini_agent import run_agent
    signals = {
        "top_videos": [
            {"title": t["title"], "views": t["views"], "channel": t.get("channel_title", "")}
            for t in (top or [])[:30]
        ],
        "outlier_videos": [
            {"title": o["title"], "vs_ratio": o["vs_ratio"], "age_days": o["age_days"],
             "channel": o["channel_title"], "subs": o["subscribers"]}
            for o in outliers[:30]
        ],
        "autocomplete_queries": suggestions[:100],
        "comment_pains": _clean_pains(pains, 40),
    }
    user = (
        f"КОНТЕКСТ КАНАЛА:\n{channel_ctx}\n\n"
        f"СИГНАЛЫ СПРОСА (JSON):\n{json.dumps(signals, ensure_ascii=False)}\n\n"
        + _RANK_INSTRUCTION.format(n=n)
    )
    raw = run_agent(model, _RANK_SYSTEM, user, temperature=0.6, json_mode=True)
    return _parse_json_array(raw)


def _parse_json_array(raw: str):
    """Терпимый парсер: снимает ```-обёртки, вытаскивает массив; при обрыве по лимиту
    токенов спасает все ЗАВЕРШЁННЫЕ объекты через посимвольный разбор баланса скобок."""
    txt = raw.strip()
    txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.MULTILINE).strip()
    try:
        data = json.loads(txt)
        return data if isinstance(data, list) else data.get("ideas", data)
    except Exception:
        pass
    # salvage: собираем целые {...}-объекты верхнего уровня (устойчиво к обрыву в конце)
    objs, depth, start, in_str, esc = [], 0, None, False, False
    for i, ch in enumerate(txt):
        if in_str:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': in_str = False
            continue
        if ch == '"': in_str = True
        elif ch == "{":
            if depth == 0: start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    objs.append(json.loads(txt[start:i + 1]))
                except Exception:
                    pass
                start = None
    if objs:
        return objs
    return [{"_parse_error": True, "raw": raw[:2000]}]


# ─────────────────────────── channel context ───────────────────────────

def _load_channel_ctx(channel: str) -> str:
    """Короткий контекст канала: редакционная политика + производственные рубрики.

    Канонический scope хранится в `editorial_policy.md`; v7-контекст добавляется как
    производственный слой. Старый `studio_context.md` намеренно не используется: там
    рубрики v1-v6 (Objaw→Błąd / Zła Para / Mit), от которых пайплайн ушёл ещё в v7."""
    base = _PROJECT_ROOT / "autopilot_factory" / "channels" / channel
    paths = [base / "editorial_policy.md", base / "studio_context_v7.md"]
    existing = [p for p in paths if p.exists()]
    if not existing:
        return f"(канал '{channel}' без studio_context.md)"
    chunks = []
    for p in existing:
        text = p.read_text(encoding="utf-8")
        # Для v7 берём начало до визуала/TTS; policy читаем целиком, поскольку там scope.
        if p.name != "editorial_policy.md":
            text = re.split(r"\n##\s+(?:[4-9]|1[0-9])\.", text)[0]
            text = text[:2200]
        else:
            # Оставляем место для производственных названий рубрик ниже; полный policy
            # сохраняется на диске и читается отдельно перед глубоким ресёрчем.
            text = text[:3600]
        chunks.append(text)
    chunks.append(
        "AVAILABLE PRODUCTION RUBRICS: plate, day_body, how_much, really_true, label, "
        "body_signals, at_shelf, kitchen_chem, movement, brain, performance, research_lab."
    )
    return "\n\n--- PRODUCTION CONTEXT ---\n\n".join(chunks)[:6200]


# ─────────────────────────── CLI ───────────────────────────

def main():
    p = argparse.ArgumentParser(description="Майнер тем/идей: autocomplete + YouTube outlier + LLM-ранжирование")
    p.add_argument("--mode", choices=["autocomplete", "outliers", "top", "full"], default="full",
                   help="autocomplete=только семантика (без ключа); outliers=+outlier-детект (мелкие каналы); "
                        "top=самые просматриваемые ролики ниши (крупные, изучить подходы); "
                        "full=outlier+ранжирование")
    p.add_argument("--top-per-query", type=int, default=15, help="[top] сколько топ-видео брать на запрос")
    p.add_argument("--published-after", help="[top] ISO-дата (YYYY-MM-DD), брать видео не старше (напр. 2025-01-01)")
    p.add_argument("--seed", action="append", default=[], help="seed-тема (повторяемо)")
    p.add_argument("--channel", help="имя канала (autopilot_factory/channels/<name>) — для контекста и тега")
    p.add_argument("--lang", default="en", help="язык подсказок/поиска (en/ru/pl)")
    p.add_argument("--depth", type=int, default=1, help="глубина autocomplete-рекурсии (0..2)")
    p.add_argument("--max-queries", type=int, default=5, help="сколько запросов уходит в search.list (по 100 юнитов)")
    p.add_argument("--channels-per-query", type=int, default=10)
    p.add_argument("--videos-per-channel", type=int, default=20)
    p.add_argument("--min-vs", type=float, default=3.0, help="порог V/S ratio для outlier")
    p.add_argument("--min-subs", type=int, default=1000, help="нижний порог подписчиков (отсекает микроканалы/бренд-спам)")
    p.add_argument("--max-subs", type=int, default=50000, help="верхний потолок подписчиков канала-конкурента")
    p.add_argument("--max-age-days", type=float, default=60.0)
    p.add_argument("--min-views", type=int, default=1000)
    p.add_argument("--comments", action="store_true", help="майнить топ-комменты у outlier-видео (боли)")
    p.add_argument("--rank", action="store_true", help="LLM-ранжирование сигналов в бэклог идей (нужен GEMINI_API_KEY)")
    p.add_argument("--rank-model", default="pro", help="модель Gemini для ранжирования (pro/flash35/...)")
    p.add_argument("--ideas", type=int, default=12, help="сколько идей вернуть при --rank")
    p.add_argument("--out", help="путь для JSON-результата (без --out → stdout)")
    args = p.parse_args()

    if not args.seed and not args.channel:
        p.error("нужен хотя бы один --seed (или --channel для контекста + свои --seed)")

    quota = _Quota()
    result = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "channel": args.channel, "lang": args.lang, "seeds": args.seed,
    }

    # 1) autocomplete — всегда (бесплатно)
    print(f"[autocomplete] расширяю {len(args.seed)} seed(ов), lang={args.lang}, depth={args.depth}…", file=sys.stderr)
    suggestions = autocomplete(args.seed, args.lang, depth=args.depth) if args.seed else []
    result["suggestions"] = suggestions
    print(f"[autocomplete] собрано подсказок: {len(suggestions)}", file=sys.stderr)

    outliers, top, pains = [], [], []
    if args.mode in ("outliers", "top", "full"):
        svc = youtube_service()
        # запросы: seeds + топ подсказок
        queries = list(dict.fromkeys(list(args.seed) + suggestions))
        n_q = min(args.max_queries, len(queries))

    if args.mode in ("outliers", "full"):
        print(f"[outliers] search.list по {n_q} запросам (~{n_q * 100} юнитов квоты)…", file=sys.stderr)
        outliers = mine_outliers(
            svc, queries, args.lang, max_queries=args.max_queries,
            channels_per_query=args.channels_per_query, videos_per_channel=args.videos_per_channel,
            min_vs=args.min_vs, min_subs=args.min_subs, max_subs=args.max_subs,
            max_age_days=args.max_age_days, min_views=args.min_views, quota=quota,
        )
        result["outliers"] = outliers
        print(f"[outliers] найдено outlier-видео: {len(outliers)}", file=sys.stderr)

    if args.mode == "top":
        print(f"[top] search.list (order=viewCount) по {n_q} запросам (~{n_q * 100} юнитов квоты)…", file=sys.stderr)
        top = top_videos(
            svc, queries, args.lang, max_queries=args.max_queries, per_query=args.top_per_query,
            published_after=args.published_after, min_views=args.min_views, quota=quota,
        )
        result["top_videos"] = top
        print(f"[top] собрано топ-видео: {len(top)}", file=sys.stderr)

    if args.comments:
        pool = (outliers or top)[:15]
        if pool:
            print(f"[comments] тяну комменты у топ-{len(pool)} видео…", file=sys.stderr)
            for v in pool:
                for c in top_comments(svc, v["video_id"], quota):
                    pains.append(c["text"])
            result["comment_pains"] = pains
            print(f"[comments] собрано комментов: {len(pains)}", file=sys.stderr)

    if args.mode in ("full", "top") and args.rank:
        ctx = _load_channel_ctx(args.channel) if args.channel else "(канал не задан)"
        print(f"[rank] ранжирую сигналы моделью {args.rank_model} → {args.ideas} идей…", file=sys.stderr)
        result["ideas"] = rank_ideas(ctx, outliers, suggestions, pains,
                                     top=top, n=args.ideas, model=args.rank_model)

    result["quota_units_spent"] = quota.units
    print(f"[quota] израсходовано юнитов YouTube API: {quota.units}", file=sys.stderr)

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(payload, encoding="utf-8")
        print(f"[out] сохранено → {args.out}", file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    main()
