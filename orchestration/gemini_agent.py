#!/usr/bin/env python3
"""
gemini_agent.py — раннер Gemini-саб-агентов для оркестрации.

Claude (Opus) выступает оркестратором и делегирует отдельные задачи Gemini-моделям
через этот раннер. Используется двумя способами:

1. Как CLI (Claude вызывает через Bash):
     python3 orchestration/gemini_agent.py \
         --model pro \
         --system orchestration/roles/researcher.md \
         --task  "Собери best practices по hook'ам для short-form" \
         --search \
         --out   orchestration/research/hooks.md

2. Как библиотека (импортируется из autopilot_factory/ пайплайна):
     from gemini_agent import run_agent, run_structured
     text = run_agent("flash35", system="...", user="...", temperature=0.7)
     obj  = run_structured("pro", system="...", user="...", schema=MyPydanticModel)

Ключ берётся из GEMINI_API_KEY (.env в корне проекта имеет приоритет над окружением).

Документация:
  - google-genai SDK:        https://googleapis.github.io/python-genai/
  - Structured output:       https://ai.google.dev/gemini-api/docs/structured-output
  - Grounding / web search:  https://ai.google.dev/gemini-api/docs/google-search
  - Список моделей:          https://ai.google.dev/gemini-api/docs/models
"""
import os
import sys
import json
import time
import argparse
import datetime
from pathlib import Path

# --- .env loader (.env в корне проекта имеет приоритет над системным окружением) ---
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

from google import genai
from google.genai import types
import requests

# Учёт стоимости (необязателен: пишет в RUN_COST_DIR, если задан). Импорт мягкий —
# модуль лежит в autopilot_factory/, который пайплайн добавляет в sys.path.
try:
    import cost_tracker as _cost
except Exception:
    _cost = None

# --- Реестр моделей: дружелюбные алиасы -> реальные ID ---
# Проверено через models.list на этом ключе (2026-06-28).
MODELS = {
    # текст / рассуждения
    "lite":      "gemini-2.5-flash-lite",        # самый дешёвый, тривиальные задачи
    "flash":     "gemini-2.5-flash",             # дешёвый рабочий конь, структурный JSON
    "flash35":   "gemini-3.5-flash",             # сильнее flash, креативная генерация
    "pro":       "gemini-3.1-pro-preview",       # высокое рассуждение: судья/QA, арт-дирекшн
    # агентный / кодовый
    "antigravity": "antigravity-preview-05-2026",
    # глубокий ресёрч с веб-поиском (долгие запросы)
    "research":     "deep-research-preview-04-2026",
    "research_max": "deep-research-max-preview-04-2026",
    "research_pro": "deep-research-pro-preview-12-2025",
}

def resolve_model(name: str) -> str:
    return MODELS.get(name, name)  # позволяет передать и алиас, и полный ID

# Модели, доступные ТОЛЬКО через Interactions API (не через generateContent).
# Подтверждено живым вызовом 2026-07-01: generateContent -> 400 "This model only
# supports Interactions API". REST-эндпоинт /v1beta/interactions версия-независим
# от google-genai SDK (нам не нужен SDK>=2.3.0 с client.interactions — бьём REST напрямую).
DEEP_RESEARCH_ALIASES = {"research", "research_max", "research_pro"}
_INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"

_client = None
def client() -> "genai.Client":
    global _client
    if _client is None:
        if not os.environ.get("GEMINI_API_KEY"):
            raise SystemExit("GEMINI_API_KEY не найден (.env в корне проекта).")
        _client = genai.Client()
    return _client


def run_agent(model: str, system: str, user: str,
              temperature: float = 0.7, search: bool = False,
              json_mode: bool = False, thinking: bool = True) -> str:
    """Один вызов Gemini-саб-агента. Возвращает текст ответа."""
    cfg_kwargs = dict(temperature=temperature)
    if system:
        cfg_kwargs["system_instruction"] = system
    if search:
        cfg_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    if json_mode:
        cfg_kwargs["response_mime_type"] = "application/json"
    config = types.GenerateContentConfig(**cfg_kwargs)
    mid = resolve_model(model)
    resp = client().models.generate_content(
        model=mid, contents=user, config=config,
    )
    if _cost:
        _cost.record_tokens(mid, getattr(resp, "usage_metadata", None), step="run_agent")
    return resp.text or ""


def run_deep_research(model: str, query: str, system: str = "",
                       poll_interval: float = 20.0, timeout: float = 3300.0) -> str:
    """Глубокий ресёрч через Interactions API (research/research_max/research_pro).

    Асинхронно: create -> poll get до status=completed/failed. Может занимать минуты
    (документировано до 60 мин). system, если задан, склеивается в начало запроса —
    у Interactions API нет отдельного system_instruction на верхнем уровне.
    """
    mid = resolve_model(model)
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY не найден (.env в корне проекта).")
    full_input = f"{system}\n\n{query}" if system else query
    body = {"agent": mid, "input": full_input, "background": True, "store": True}
    resp = requests.post(_INTERACTIONS_URL, params={"key": key}, json=body, timeout=30)
    resp.raise_for_status()
    interaction_id = resp.json()["id"]

    t0 = time.time()
    data = None
    while time.time() - t0 < timeout:
        time.sleep(poll_interval)
        r = requests.get(f"{_INTERACTIONS_URL}/{interaction_id}", params={"key": key}, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("status") in ("completed", "failed"):
            break
    if data is None or data.get("status") != "completed":
        raise RuntimeError(f"deep research не завершился за {timeout}s (id={interaction_id}, "
                           f"status={data.get('status') if data else 'unknown'})")

    if _cost:
        usage = data.get("usage", {}) or {}
        # интерфейс record_tokens ждёт объект с атрибутами (google-genai usage_metadata) —
        # адаптируем словарь Interactions API через SimpleNamespace.
        import types as _pytypes
        ns = _pytypes.SimpleNamespace(
            prompt_token_count=usage.get("total_input_tokens", 0),
            candidates_token_count=usage.get("total_output_tokens", 0) + usage.get("total_thought_tokens", 0),
        )
        _cost.record_tokens(mid, ns, step="run_deep_research")

    # финальный текст — последний model_output шаг
    for step in reversed(data.get("steps", [])):
        if step.get("type") == "model_output":
            parts = [c.get("text", "") for c in step.get("content", []) if c.get("type") == "text"]
            return "\n".join(parts)
    return ""


def run_structured(model: str, system: str, user: str, schema,
                   temperature: float = 0.7) -> dict:
    """Структурированный вызов с Pydantic/ JSON-схемой. Возвращает распарсенный dict."""
    config = types.GenerateContentConfig(
        system_instruction=system or None,
        response_mime_type="application/json",
        response_schema=schema,
        temperature=temperature,
    )
    mid = resolve_model(model)
    resp = client().models.generate_content(
        model=mid, contents=user, config=config,
    )
    if _cost:
        _cost.record_tokens(mid, getattr(resp, "usage_metadata", None), step="run_structured")
    return json.loads(resp.text)


def _read_arg(value: str) -> str:
    """Если значение — путь к существующему файлу, читаем его; иначе берём как текст.

    Многострочный/длинный аргумент — это всегда инлайн-текст задачи, а не путь.
    Проверку файла оборачиваем в try, чтобы длинные строки не падали на is_file()
    (OSError: File name too long).
    """
    if value and "\n" not in value and len(value) < 4096:
        try:
            p = Path(value)
            if p.is_file():
                return p.read_text(encoding="utf-8")
        except OSError:
            pass
    return value or ""


def main():
    p = argparse.ArgumentParser(description="Раннер Gemini-саб-агентов для оркестрации")
    p.add_argument("--model", help="алиас (lite|flash|flash35|pro|research|...) или полный ID")
    p.add_argument("--system", default="", help="системный промпт: текст или путь к .md")
    p.add_argument("--task", help="задача: текст или путь к файлу")
    p.add_argument("--temp", type=float, default=0.7)
    p.add_argument("--search", action="store_true", help="включить grounding через Google Search")
    p.add_argument("--json", action="store_true", help="response_mime_type=application/json")
    p.add_argument("--out", default="", help="куда сохранить ответ (иначе stdout)")
    p.add_argument("--list-models", action="store_true")
    args = p.parse_args()

    if args.list_models:
        for alias, mid in MODELS.items():
            print(f"{alias:14s} -> {mid}")
        return

    if not args.model or not args.task:
        p.error("--model и --task обязательны (кроме режима --list-models)")

    system = _read_arg(args.system)
    task = _read_arg(args.task)

    t0 = time.time()
    if args.model in DEEP_RESEARCH_ALIASES:
        out = run_deep_research(args.model, task, system=system)
    else:
        out = run_agent(args.model, system, task,
                        temperature=args.temp, search=args.search, json_mode=args.json)
    dt = time.time() - t0

    header = (f"<!-- generated by gemini_agent | model={resolve_model(args.model)} "
              f"| search={args.search} | {datetime.datetime.now().isoformat(timespec='seconds')} "
              f"| {dt:.1f}s -->\n")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(header + out, encoding="utf-8")
        print(f"[ok] {resolve_model(args.model)} -> {args.out} ({dt:.1f}s, {len(out)} chars)")
    else:
        sys.stdout.write(out + "\n")
        sys.stderr.write(f"[ok] {resolve_model(args.model)} ({dt:.1f}s)\n")


if __name__ == "__main__":
    main()
