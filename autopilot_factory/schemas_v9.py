#!/usr/bin/env python3
"""Retention-specific contracts layered over the stable v8 content package."""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field, model_validator


PIPELINE_VERSION = "9.0-retention"
MAX_V9_ACTUAL_DURATION_S = 35.0
DurationLane = Literal["core", "deep"]
CREATIVE_AXES = {
    "hook_family",
    "protagonist_mode",
    "story_engine",
    "proof_device",
    "environment",
    "edit_grammar",
    "payoff_device",
    "tts_delivery",
}


class CadencePlan(BaseModel):
    publications_today: int = Field(..., ge=1, le=4)
    slot_index: int = Field(..., ge=1, le=4)
    minimum_gap_hours: float = Field(4.0, ge=4.0, le=24.0)

    @model_validator(mode="after")
    def slot_must_exist(self):
        if self.slot_index > self.publications_today:
            raise ValueError("slot_index cannot exceed publications_today")
        return self


class CreativeFingerprint(BaseModel):
    hook_family: str = Field(..., min_length=3, max_length=80)
    protagonist_mode: str = Field(..., min_length=3, max_length=80)
    story_engine: str = Field(..., min_length=3, max_length=80)
    proof_device: str = Field(..., min_length=3, max_length=100)
    environment: str = Field(..., min_length=3, max_length=100)
    edit_grammar: str = Field(..., min_length=3, max_length=120)
    payoff_device: str = Field(..., min_length=3, max_length=100)
    tts_delivery: str = Field(..., min_length=3, max_length=100)
    compared_runs: List[str] = Field(..., min_length=8, max_length=20)
    changed_axes: List[str] = Field(..., min_length=3, max_length=8)

    @model_validator(mode="after")
    def require_real_comparison(self):
        if len(set(self.compared_runs)) < 8:
            raise ValueError("compared_runs must contain at least 8 distinct runs")
        distinct_axes = set(self.changed_axes)
        if len(distinct_axes) < 3:
            raise ValueError("changed_axes must contain at least 3 distinct axes")
        unknown = sorted(distinct_axes - CREATIVE_AXES)
        if unknown:
            raise ValueError("unknown changed_axes: " + ", ".join(unknown))
        return self


class RetentionPlan(BaseModel):
    version: Literal["9.0-retention"] = PIPELINE_VERSION
    duration_lane: DurationLane
    target_duration_s: float = Field(..., ge=18.0, le=35.0)
    first_proof_beat: int = Field(..., ge=0, le=17)
    turn_beat: int = Field(..., ge=0, le=17)
    payoff_beat: int = Field(..., ge=0, le=17)
    spoken_cta: bool = False
    cadence: CadencePlan
    creative_fingerprint: CreativeFingerprint

    @model_validator(mode="after")
    def validate_lane_and_order(self):
        if self.duration_lane == "core" and not 18.0 <= self.target_duration_s <= 24.0:
            raise ValueError("core target_duration_s must be 18-24 seconds")
        if self.duration_lane == "deep" and not 28.0 <= self.target_duration_s <= 35.0:
            raise ValueError("deep target_duration_s must be 28-35 seconds")
        if not self.first_proof_beat < self.turn_beat < self.payoff_beat:
            raise ValueError("beats must be ordered first_proof < turn < payoff")
        if self.spoken_cta:
            raise ValueError("spoken CTA is disabled during the retention sprint")
        return self


class TimingCheck(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class BeatTiming(BaseModel):
    beat_idx: int
    start_s: float
    end_s: float
    duration_s: float
    act: str


class RetentionTimingReport(BaseModel):
    version: Literal["9.0-retention"] = PIPELINE_VERSION
    passed: bool
    lane: DurationLane
    target_duration_s: float
    planned_duration_s: float
    actual_narration_s: float
    word_count: int
    first_proof_s: float
    turn_s: float
    payoff_s: float
    beats: List[BeatTiming]
    checks: List[TimingCheck]


__all__ = [
    "PIPELINE_VERSION",
    "MAX_V9_ACTUAL_DURATION_S",
    "DurationLane",
    "CadencePlan",
    "CreativeFingerprint",
    "RetentionPlan",
    "TimingCheck",
    "BeatTiming",
    "RetentionTimingReport",
]
