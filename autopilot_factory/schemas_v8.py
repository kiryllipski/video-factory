#!/usr/bin/env python3
"""Canonical v8 contracts for evidence, editorial structure and media assembly."""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

import schemas_v8_base as V8Base


PIPELINE_VERSION = "8.0"

SourceType = Literal[
    "official_guideline",
    "regulation",
    "systematic_review",
    "meta_analysis",
    "clinical_trial",
    "primary_study",
    "official_database",
    "other",
]
ClaimVerdict = Literal["supported", "conditional", "rejected"]
RiskLevel = Literal["low", "medium", "high"]


class ResearchSource(BaseModel):
    id: str = Field(..., pattern=r"^SRC-[0-9]{2}$")
    title: str = Field(..., min_length=8, max_length=240)
    publisher: str = Field(..., min_length=2, max_length=120)
    url: str = Field(..., min_length=12, max_length=500)
    source_type: SourceType
    year: int = Field(..., ge=1900, le=2100)
    evidence_summary: str = Field(..., min_length=20, max_length=700)


class ResearchClaim(BaseModel):
    id: str = Field(..., pattern=r"^CLM-[0-9]{2}$")
    neutral_claim: str = Field(..., min_length=12, max_length=400)
    verdict: ClaimVerdict
    confidence: Literal["low", "medium", "high"]
    source_ids: List[str] = Field(..., min_length=1, max_length=5)
    allowed_wording: str = Field(..., min_length=8, max_length=400)
    forbidden_wording: List[str] = Field(default_factory=list, max_length=8)
    limitations: str = Field(..., min_length=4, max_length=500)
    risk_level: RiskLevel = "medium"
    display_source: bool = False


class ResearchPack(BaseModel):
    lang: Literal["pl", "ru"] = "pl"
    topic: str = Field(..., min_length=5, max_length=240)
    viewer_question: str = Field(..., min_length=8, max_length=240)
    recommended_angle: str = Field(..., min_length=12, max_length=400)
    evidence_summary: str = Field(..., min_length=30, max_length=1200)
    sources: List[ResearchSource] = Field(..., min_length=3, max_length=12)
    claims: List[ResearchClaim] = Field(..., min_length=4, max_length=12)
    unresolved_conflicts: List[str] = Field(default_factory=list, max_length=6)


class Beat(V8Base.Beat):
    claim_ids: List[str] = Field(default_factory=list, max_length=4)


class Overlay(V8Base.Overlay):
    claim_ids: List[str] = Field(default_factory=list, max_length=4)
    source_finding: str = Field(
        "", max_length=100,
        description=(
            "source: короткий зрительский вывод карточки исследования, 3–10 слов; "
            "title/publisher/year движок подставляет только из ResearchPack"
        ),
    )


class Script(V8Base.Script):
    lang: Literal["pl", "ru"] = "pl"
    beats: List[Beat] = Field(..., min_length=8, max_length=18)
    overlays: List[Overlay] = Field(default_factory=list, min_length=3, max_length=6)
    central_claim_id: str = Field(..., pattern=r"^CLM-[0-9]{2}$")
    poster_claim_ids: List[str] = Field(default_factory=list, max_length=3)
    payload_claim_ids: List[str] = Field(default_factory=list, min_length=1, max_length=4)
    payoff_claim_ids: List[str] = Field(default_factory=list, min_length=1, max_length=4)


class ComplianceVerdict(BaseModel):
    passed: bool
    fixes: List[str] = Field(default_factory=list, max_length=12)
    cleaned_script: Script


class FactCheckItem(BaseModel):
    claim_id: str
    passed: bool
    issue: str = ""
    required_change: str = ""


class FactReview(BaseModel):
    passed: bool
    checks: List[FactCheckItem] = Field(default_factory=list)
    unsupported_script_statements: List[str] = Field(default_factory=list, max_length=12)
    notes: List[str] = Field(default_factory=list, max_length=8)


class Frame(V8Base.Frame):
    claim_ids: List[str] = Field(default_factory=list, max_length=4)


class FramePlan(V8Base.FramePlan):
    frames: List[Frame] = Field(..., min_length=8, max_length=18)


class PublishPackage(V8Base.PublishPackage):
    description: str = Field(..., max_length=5000)
    distribution_lane: Literal["feed", "search", "hybrid"] = Field(
        "feed", description="Primary discovery lane used for the metadata hypothesis"
    )
    primary_query: str = Field(
        "", max_length=180, description="Actual viewer query for search/hybrid packaging"
    )
    secondary_queries: List[str] = Field(default_factory=list, max_length=8)
    metadata_hypothesis: str = Field(
        "", max_length=400, description="One falsifiable packaging hypothesis"
    )
    api_tags: List[str] = Field(
        default_factory=list, max_length=15,
        description="Small optional API tag set; distinct from visible hashtags"
    )
    source_urls: List[str] = Field(default_factory=list, max_length=8)


class ReleaseCheck(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class ReleaseReport(BaseModel):
    passed: bool
    checks: List[ReleaseCheck]
    content_revision: str


QAReport = V8Base.QAReport
QACheck = V8Base.QACheck

# The catalog is part of the v8 public contract.  Re-exporting it here keeps callers
# from reaching through an implementation module and makes the skill/checker v8-only.
Rubric = V8Base.Rubric
Format = V8Base.Format
CANONICAL_FORMATS = V8Base.CANONICAL_FORMATS
FORMAT_PRIORITY = V8Base.FORMAT_PRIORITY
FORMAT_BRIEFS = V8Base.FORMAT_BRIEFS
RUBRIC_META = V8Base.RUBRIC_META
ACTIVE_RUBRICS = V8Base.ACTIVE_RUBRICS
COMPLIANCE_STOPWORDS = V8Base.COMPLIANCE_STOPWORDS
rubric_formats = V8Base.rubric_formats


__all__ = [
    "PIPELINE_VERSION",
    "ResearchSource",
    "ResearchClaim",
    "ResearchPack",
    "Beat",
    "Overlay",
    "Script",
    "ComplianceVerdict",
    "FactCheckItem",
    "FactReview",
    "Frame",
    "FramePlan",
    "PublishPackage",
    "ReleaseCheck",
    "ReleaseReport",
    "QAReport",
    "QACheck",
    "Rubric",
    "Format",
    "CANONICAL_FORMATS",
    "FORMAT_PRIORITY",
    "FORMAT_BRIEFS",
    "RUBRIC_META",
    "ACTIVE_RUBRICS",
    "COMPLIANCE_STOPWORDS",
    "rubric_formats",
]
