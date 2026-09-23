from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import DecisionState
from rivexis_api.version import DECISION_METHODOLOGY_VERSION

class DecisionRequest(BaseModel):
    engine_results: list[EngineResult]
    user_role: str = "Individual"
    risk_tolerance: str = "moderate"
    transaction_size: float | None = None
    position_size: float | None = None
    policy: dict[str, Any] = Field(default_factory=dict)

class RivexisDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision_methodology_version: str = DECISION_METHODOLOGY_VERSION
    decision: DecisionState
    overall_risk_score: float = Field(ge=0, le=100)
    decision_confidence: float = Field(ge=0, le=100)
    data_confidence: float = Field(ge=0, le=100)
    executive_summary: str
    critical_findings: list[str] = Field(default_factory=list)
    positive_findings: list[str] = Field(default_factory=list)
    risk_breakdown: dict[str, float] = Field(default_factory=dict)
    why: list[str] = Field(default_factory=list)
    what_could_go_wrong: list[str] = Field(default_factory=list)
    recommended_action: str
    safer_option: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    analysis_ids: list[str] = Field(default_factory=list)
    engine_versions: dict[str, str] = Field(default_factory=dict)
    engine_statuses: dict[str, str] = Field(default_factory=dict)
    analysis_framework_versions: dict[str, str] = Field(default_factory=dict)
    evidence_sources: list[str] = Field(default_factory=list)
    unresolved_conflict_count: int = 0
    evidence_count: int = 0
    demo: bool = False
