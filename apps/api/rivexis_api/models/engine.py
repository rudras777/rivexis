from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field
from rivexis_api.models.enums import AnalysisStatus, EngineId, Severity
from rivexis_api.models.evidence import EvidenceRecord, SourceConflict

class EngineResult(BaseModel):
    engine_id: EngineId
    engine_version: str = "1.0.0"
    analysis_id: str = Field(default_factory=lambda: str(uuid4()))
    engine_run_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    block_reference: int | None = None
    status: AnalysisStatus = AnalysisStatus.COMPLETED
    risk_score: float = Field(default=0, ge=0, le=100)
    data_confidence: float = Field(default=0, ge=0, le=100)
    engine_confidence: float = Field(default=0, ge=0, le=100)
    severity: Severity = Severity.UNKNOWN
    summary: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    signals: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    hard_blockers: list[str] = Field(default_factory=list)
    mitigations: list[str] = Field(default_factory=list)
    safer_alternatives: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    provider_consensus: str = "UNAVAILABLE"
    provider_conflicts: list[SourceConflict] = Field(default_factory=list)
    data_freshness: dict[str, Any] = Field(default_factory=dict)
    missing_data: list[str] = Field(default_factory=list)
    provider_status: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    demo: bool = False
