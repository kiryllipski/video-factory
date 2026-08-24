#!/usr/bin/env python3
"""dump_prompts.py — снапшот ВСЕХ промптов версии пайплайна в один читаемый файл.

Зачем: владелец должен иметь возможность сам открыть и прочитать, какими промптами собиралась
конкретная версия, не поднимая git-историю (поручение 2026-08-05). Снапшот собирается ИЗ КОДА —
константы импортируются, а не переписываются руками, поэтому файл не может разойтись с тем,
что реально ушло в модель.

Пишет `docs/prompt_versions/<версия>.md`.

    python3 scripts/dump_prompts.py 6.0-layers
    python3 scripts/dump_prompts.py --list       # какие версии умеет выгружать
"""
from __future__ import annotations
import argparse
import datetime
import importlib
from pathlib import Path

from _common import find_project_root, wire_paths

ROOT = find_project_root()
wire_paths(ROOT)

# версия → (модуль сборки, [(заголовок, путь к константе)])
_VERSIONS = {
    "3.0": ("build_media", [
        ("Негатив-блок кадра", "_NEGATIVE"),
    ]),
    "4.0-exp": ("build_media_v4exp", [
        ("Негатив-блок кадра", "_NEGATIVE"),
    ]),
    "5.0-collage": ("build_media_v5collage", [
        ("Инвариантный стилевой блок коллажа", "_COLLAGE_STYLE"),
        ("Технический хвост промпта кадра", "_COLLAGE_TECH"),
        ("Негатив-блок кадра", "_NEGATIVE"),
    ]),
    "6.0-layers": ("build_media_v6layers", [
        ("Стилевой блок стикер-листа", "_SHEET_STYLE"),
        ("Технический хвост листа", "_SHEET_TECH"),
        ("Негатив-блок листа", "_SHEET_NEGATIVE"),
    ]),
    # v7 живёт в autopilot_factory (полностью автономный прогон через engine_v7), а не в
    # скиллe: текстовые стадии пишут Gemini-роли из prompts/v7/, поэтому снапшот должен
    # брать и брифы форматов — они тоже уходят в модель как часть промпта.
    "7.0": ("engine_v7", [
        ("Негатив-блок кадра", "_NEGATIVE"),
        ("Запрещённые обобщения в payload", "_VAGUE_PL"),
    ]),
}

# Роли по версиям: v7 держит свои в подпапке, старые версии — в корне prompts/.
_ROLE_DIRS = {"7.0": "v7"}

# своды QA — общие для всех версий, но профиль зависит от стиля
_QA_BLOCKS = [
    ("frame-QA, профиль photo", "vision_qa", "_FRAME_RULES"),
    ("frame-QA, дополнение для кадра-0 (photo)", "vision_qa", "_POSTER_EXTRA"),
    ("frame-QA, профиль collage", "vision_qa", "_COLLAGE_FRAME_RULES"),
    ("frame-QA, дополнение для кадра-0 (collage)", "vision_qa", "_COLLAGE_POSTER_EXTRA"),
    ("video-QA готового стоп-кадра", "vision_qa", "_STILL_RULES"),
]


def _fence(text: str) -> str:
    return "```text\n" + str(text).strip() + "\n```"


def dump(version: str) -> Path:
    if version not in _VERSIONS:
        raise SystemExit(f"[dump_prompts] неизвестная версия «{version}». "
                         f"Известные: {', '.join(sorted(_VERSIONS))}")
    mod_name, consts = _VERSIONS[version]
    mod = importlib.import_module(mod_name)

    out = [f"# Промпты пайплайна {version}", "",
           f"> Снапшот собран {datetime.date.today()} скриптом "
           f"`.claude/skills/video-factory/scripts/dump_prompts.py` — текст взят из кода "
           f"(`{mod_name}.py`), не переписан руками.", "",
           "## Промпты сборки", ""]
    for title, attr in consts:
        out += [f"### {title}", "", _fence(getattr(mod, attr)), ""]

    out += ["## Своды машинного QA (vision)", ""]
    for title, qa_mod_name, attr in _QA_BLOCKS:
        qa_mod = importlib.import_module(qa_mod_name)
        val = getattr(qa_mod, attr, None)
        if val:
            out += [f"### {title}", "", _fence(val), ""]

    if version == "7.0":
        import schemas_v7 as _s7
        out += ["## Брифы форматов (уходят в промпт сценариста)", ""]
        for name, brief in _s7.FORMAT_BRIEFS.items():
            out += [f"### `{name}`", "", _fence(brief), ""]

    sub = _ROLE_DIRS.get(version, "")
    roles = ROOT / "autopilot_factory" / "prompts" / sub
    if roles.is_dir():
        out += [f"## Runtime-роли Gemini (`autopilot_factory/prompts/{sub or ''}`)", ""]
        for f in sorted(roles.glob("*.md")):
            out += [f"### {f.name}", "", _fence(f.read_text(encoding='utf-8')), ""]

    dest = ROOT / "docs" / "prompt_versions" / f"{version}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(out), encoding="utf-8")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description="Снапшот промптов версии пайплайна")
    ap.add_argument("version", nargs="?", help="напр. 6.0-layers")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true", help="выгрузить все известные версии")
    a = ap.parse_args()
    if a.list:
        for v, (m, _) in sorted(_VERSIONS.items()):
            print(f"{v:14s} ← {m}.py")
        return 0
    targets = sorted(_VERSIONS) if a.all else ([a.version] if a.version else [])
    if not targets:
        ap.error("укажи версию, или --all, или --list")
    for v in targets:
        print(f"[ok] {dump(v)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
