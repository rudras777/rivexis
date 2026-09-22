from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from rivexis_api.models.enums import FreshnessStatus

class EvidenceRecord(BaseModel):
    evidence_id: str
    provider: str
    source_type: str = "demo"
    provider_endpoint: str | None = None
    provider_request_id: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    block_number: int | None = None
    chain_id: int | None = None
    asset_id: str | None = None
    protocol_id: str | None = None
    raw_reference: str | None = None
    normalized_value: Any = None
    calculation_version: str = "1.0.0"
    engine_version: str = "1.0.0"
    confidence: float = Field(default=0.0, ge=0, le=100)
    freshness: FreshnessStatus = FreshnessStatus.UNKNOWN
    license_classification: str = "internal-demo"

class SourceConflict(BaseModel):
    metric: str
    source_a: str
    value_a: Any
    source_b: str
    value_b: Any
    difference: float | None = None
    difference_percentage: float | None = None
    expected_tolerance: float | None = None
    severity: str = "moderate"
    resolution_method: str = "unresolved"
    resolved_value: Any = None
    resolution_confidence: float = Field(default=0, ge=0, le=100)
