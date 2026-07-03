#!/usr/bin/env python3
"""
schemas.py — контракты данных между стадиями runtime-конвейера (см. ARCHITECTURE.md §2).

Стадии общаются строго через эти Pydantic-модели: их передаём как `response_schema` в
`gemini_agent.run_structured(...)`, что гарантирует валидный JSON без парсинга текста.
Лимиты длины (retention) зашиты прямо в поля.

Статус: контракт-дизайн Фазы 0 (engine.py ещё не написан). Значения по умолчанию/лимиты —
из research/01 (retention), 04 (safe-зоны/пейсинг), 16/17 (контент/визуал).
"""
from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel, Field


# --- Стадия 1: сценарий ---------------------------------------------------------
class Beat(BaseModel):
    """Один смысловой бит ролика ≈ один план на таймлайне (1.5–2.5с)."""
    voiceover: str = Field(..., description="Текст озвучки бита (EN), короткими фразами")
    on_screen_text: str = Field("", description="Субтитр/оверлей: 2–4 слова, safe-зона")
    visual_cue: str = Field(..., description="Что показать в кадре — вход для visual_director")
    dur_s: float = Field(..., ge=0.8, le=4.0, description="Длительность бита в секундах")


class Script(BaseModel):
    lang: str = Field("en", description="Язык ролика")
    hook: str = Field(..., max_length=200, description="Хук первых 1–3 сек, без приветствий")
    beats: List[Beat] = Field(..., min_length=3, max_length=20)
    cta: str = Field(..., max_length=160, description="Призыв: save/follow/share")
    total_dur_s: float = Field(..., ge=15, le=90, description="Целевой хронометраж 30–50с оптимум")


# --- Стадия 2: комплаенс --------------------------------------------------------
class ComplianceVerdict(BaseModel):
    passed: bool
    fixes: List[str] = Field(default_factory=list, description="Что заменили и почему")
    cleaned_script: Script


# --- Стадия 3: план кадров ------------------------------------------------------
Motion = Literal["ken_burns_in", "ken_burns_out", "pan_left", "pan_right", "parallax", "static_hold"]


class Frame(BaseModel):
    prompt: str = Field(..., description="Промпт Nano Banana 2 (EN), позитивное описание чистоты")
    aspect: Literal["9:16"] = "9:16"
    ref_ids: List[str] = Field(default_factory=list, description="ID предыдущих кадров для консистентности (до 14)")
    motion: Motion = "ken_burns_in"
    start_s: float = Field(..., ge=0)
    dur_s: float = Field(..., ge=0.8, le=4.0)


class FramePlan(BaseModel):
    # общие на весь ролик — держат консистентность (research/17)
    grade: str = Field(..., description="Единый грейд/палитра ролика")
    light: str = Field(..., description="Единая схема света")
    lens: str = Field(..., description="Объектив/оптический язык (напр. '35mm', '85mm macro')")
    frames: List[Frame] = Field(..., min_length=3)


# --- Стадия 6: манифест сборки (вход hyperframes) -------------------------------
class CaptionStyle(BaseModel):
    words_on_screen: int = Field(3, ge=2, le=5, description="Слов на экране одновременно")
    karaoke: bool = True
    safe_zone: Literal["lower_third"] = "lower_third"


class AudioTrack(BaseModel):
    kind: Literal["voice", "bgm", "sfx"]
    path: str
    gain_db: float = 0.0


class BuildManifest(BaseModel):
    frame_plan: FramePlan
    audio: List[AudioTrack] = Field(default_factory=list)
    captions: CaptionStyle = Field(default_factory=CaptionStyle)
    disclaimer_overlay: str = Field("", description="Обязательная плашка ниши, если нужна (YMYL и т.п.)")
    fps: int = 30
    resolution: Literal["1080x1920"] = "1080x1920"


# --- Стадия 7: QA ---------------------------------------------------------------
class QACheck(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class QAReport(BaseModel):
    passed: bool
    checks: List[QACheck] = Field(..., description="hook_match, no_static_gt_3s, safe_zones, disclaimer, pacing")
    notes: List[str] = Field(default_factory=list)
    blame_stage: str = Field("", description="Куда вернуть при fail: scriptwriter|visual|assembly")


__all__ = [
    "Beat", "Script", "ComplianceVerdict", "Motion", "Frame", "FramePlan",
    "CaptionStyle", "AudioTrack", "BuildManifest", "QACheck", "QAReport",
]
