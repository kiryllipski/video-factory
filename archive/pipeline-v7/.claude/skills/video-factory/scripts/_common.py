#!/usr/bin/env python3
"""_common.py — общая проводка для скриптов навыка video-factory.

Находит корень проекта (по маркерам autopilot_factory/ + orchestration/), поднимаясь вверх
от расположения скрипта, и добавляет нужные каталоги в sys.path, чтобы можно было импортировать
schemas / engine / *_agent. Ключ Gemini раннеры сами читают из <root>/.env.
"""
from __future__ import annotations
import sys
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    p = (start or Path(__file__)).resolve()
    for cand in [p, *p.parents]:
        if (cand / "autopilot_factory").is_dir() and (cand / "orchestration").is_dir():
            return cand
    raise SystemExit("[video-factory] не найден корень проекта (autopilot_factory/ + orchestration/).")


def wire_paths(root: Path) -> None:
    for sub in ("orchestration", "autopilot_factory"):
        d = str(root / sub)
        if d not in sys.path:
            sys.path.insert(0, d)
