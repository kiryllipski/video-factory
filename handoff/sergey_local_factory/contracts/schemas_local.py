#!/usr/bin/env python3
"""
schemas_local.py — контракты данных между стадиями локального конвейера.

Стадии общаются строго через эти Pydantic-модели (не свободным текстом). Локальная LLM
(Ollama) вызывается с `format=json`; ответ валидируется соответствующей моделью, при
невалиде — один retry. Лимиты длины (retention) зашиты в поля. См. docs/ARCHITECTURE_LOCAL.md.

Зависимость: pydantic>=2  (`pip install pydantic`).
"""
from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# --- Стадия 1: сценарий ---------------------------------------------------------
class Beat(BaseModel):
    """Один смысловой бит ролика ≈ один план на таймлайне (1.5–2.5с)."""
    voiceover: str = Field(..., description="Текст озвучки бита (EN), короткими фразами")
    on_screen_text: str = Field("", description="Субтитр/оверлей: 2–4 слова, safe-зона")
    visual_cue: str = Field(..., description="Что показать в кадре — вход для visual_director")
    dur_s: float = Field(..., ge=0.8, le=4.0, description="Длительность бита, сек")


class Script(BaseModel):
    lang: str = Field("en", description="Язык ролика")
    hook: str = Field(..., max_length=200, description="Хук первых 1–3 сек, без приветствий")
    beats: List[Beat] = Field(..., min_length=3, max_length=24)
    cta: str = Field(..., max_length=160, description="Призыв: save/follow/share/квиз")
    total_dur_s: float = Field(..., ge=15, le=90, description="30–40с (YT) или 61–70с (TikTok CRP)")


# --- Стадия 2: комплаенс --------------------------------------------------------
class ComplianceVerdict(BaseModel):
    passed: bool
    fixes: List[str] = Field(default_factory=list, description="Что заменили и почему")
    cleaned_script: Script


# --- Стадия 3: план кадров ------------------------------------------------------
Motion = Literal["ken_burns_in", "ken_burns_out", "pan_left", "pan_right", "parallax", "static_hold"]


class Frame(BaseModel):
    prompt: str = Field(..., description="Промпт под выбранную модель (EN); структура — docs/IMAGE_PROMPTING.md")
    negative: str = Field("", description="Только для SDXL; для FLUX/Qwen/Z-Image оставлять пустым")
    aspect: Literal["9:16"] = "9:16"
    seed: Optional[int] = Field(None, description="Общий seed для консистентности статичных сцен")
    ref_ids: List[str] = Field(default_factory=list, description="ID предыдущих кадров (если повтор)")
    motion: Motion = "ken_burns_in"
    start_s: float = Field(..., ge=0)
    dur_s: float = Field(..., ge=0.8, le=4.0)


class FramePlan(BaseModel):
    # общие на весь ролик — держат консистентность
    grade: str = Field(..., description="Единый грейд/палитра ролика")
    light: str = Field(..., description="Единая схема света")
    lens: str = Field(..., description="Оптический язык (напр. '35mm', '85mm macro')")
    style_anchor: str = Field("", description="Якорная фраза стиля в начале каждого промпта")
    frames: List[Frame] = Field(..., min_length=3)


# --- Стадия 7: манифест сборки --------------------------------------------------
class CaptionStyle(BaseModel):
    words_on_screen: int = Field(3, ge=2, le=5)
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
    disclaimer_overlay: str = Field("", description="Обязательная плашка ниши (YMYL)")
    fps: int = 30


# --- Стадия 8: QA ---------------------------------------------------------------
class QAReport(BaseModel):
    passed: bool = Field(..., description="passed по техническим (блокирующим) флагам")
    technical: dict = Field(default_factory=dict, description="safe_zones/no_static/lufs/format/disclaimer -> bool")
    creative_notes: List[str] = Field(default_factory=list, description="Advisory-подсказки сценаристу/визуалу")


if __name__ == "__main__":
    # быстрая самопроверка контрактов: python contracts/schemas_local.py
    demo = Script(hook="They deleted the study.", beats=[
        Beat(voiceover="Scientists found something odd.", on_screen_text="something odd", visual_cue="lab macro", dur_s=2.0),
        Beat(voiceover="Then the data vanished.", on_screen_text="data vanished", visual_cue="empty folder", dur_s=2.0),
        Beat(voiceover="Here is what it showed.", on_screen_text="what it showed", visual_cue="graph rising", dur_s=2.0),
    ], cta="Save this before it's gone.", total_dur_s=36)
    print("schemas_local OK:", demo.model_dump_json(indent=2)[:120], "...")
